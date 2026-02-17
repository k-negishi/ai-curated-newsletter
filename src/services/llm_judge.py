"""LLM判定サービスモジュール."""

import asyncio
import json
import random
from dataclasses import dataclass
from typing import Any

from botocore.exceptions import ClientError

from src.models.article import Article
from src.models.interest_profile import InterestProfile
from src.models.judgment import BuzzLabel, InterestLabel, JudgmentResult
from src.repositories.cache_repository import CacheRepository
from src.shared.exceptions.llm_error import LlmJsonParseError
from src.shared.logging.logger import get_logger
from src.shared.utils.date_utils import now_utc

logger = get_logger(__name__)


@dataclass
class JudgmentBatchResult:
    """LLM一括判定結果.

    Attributes:
        judgments: 判定結果のリスト
        failed_count: 判定失敗件数
    """

    judgments: list[JudgmentResult]
    failed_count: int


class LlmJudge:
    """LLM判定サービス.

    AWS Bedrockを使用して記事の関心度と話題性を判定する.

    Attributes:
        _bedrock_client: Bedrock Runtimeクライアント
        _cache_repository: キャッシュリポジトリ
        _interest_profile: 関心プロファイル
        _model_id: 使用するLLMモデルID
        _inference_profile_arn: インファレンスプロファイルARN (オプション)
        _max_retries: 最大リトライ回数
        _concurrency_limit: 並列度制限
        _request_interval: 並列リクエスト間隔（秒）
        _retry_base_delay: リトライの基本遅延時間（秒）
        _max_backoff: 最大バックオフ時間（秒）
    """

    def __init__(
        self,
        bedrock_client: Any,
        cache_repository: CacheRepository | None,
        interest_profile: InterestProfile,
        model_id: str,
        inference_profile_arn: str = "",
        max_retries: int = 2,
        concurrency_limit: int = 5,
        request_interval: float = 0.0,
        retry_base_delay: float = 2.0,
        max_backoff: float = 20.0,
    ) -> None:
        """LLM判定サービスを初期化する.

        Args:
            bedrock_client: Bedrock Runtimeクライアント（boto3.client('bedrock-runtime')）
            cache_repository: キャッシュリポジトリ
            interest_profile: 関心プロファイル
            model_id: 使用するLLMモデルID
            inference_profile_arn: インファレンスプロファイルARN（デフォルト: ""）
            max_retries: 最大リトライ回数（デフォルト: 2）
            concurrency_limit: 並列度制限（デフォルト: 5）
            request_interval: 並列リクエスト間隔（秒、デフォルト: 0.0、Phase4で使用）
            retry_base_delay: リトライの基本遅延時間（秒、デフォルト: 2.0）
            max_backoff: 最大バックオフ時間（秒、デフォルト: 20.0）
        """
        self._bedrock_client = bedrock_client
        self._cache_repository = cache_repository
        self._interest_profile = interest_profile
        self._model_id = model_id
        self._inference_profile_arn = inference_profile_arn
        self._max_retries = max_retries
        self._concurrency_limit = concurrency_limit
        self._request_interval = request_interval
        self._retry_base_delay = retry_base_delay
        self._max_backoff = max_backoff

    async def judge_batch(self, articles: list[Article]) -> JudgmentBatchResult:
        """記事リストを一括判定する.

        並列度を制限しながら、複数記事を同時に判定する.

        Args:
            articles: 判定対象記事のリスト

        Returns:
            一括判定結果
        """
        logger.info("llm_judgment_start", article_count=len(articles))

        # 並列度制限（Semaphore）
        semaphore = asyncio.Semaphore(self._concurrency_limit)

        async def judge_with_semaphore(article: Article) -> JudgmentResult | None:
            async with semaphore:
                if self._request_interval > 0:
                    await asyncio.sleep(self._request_interval)
                return await self._judge_single(article)

        # 並列実行
        tasks = [judge_with_semaphore(article) for article in articles]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 結果を集約
        judgments: list[JudgmentResult] = []
        failed_count = 0

        for article, result in zip(articles, results, strict=True):
            if isinstance(result, Exception):
                logger.warning(
                    "llm_judgment_failed",
                    url=article.url,
                    error=str(result),
                )
                failed_count += 1
                # 失敗時はIGNORE扱い
                fallback_judgment = self._create_fallback_judgment(article)
                judgments.append(fallback_judgment)
            elif result is None:
                logger.warning("llm_judgment_none", url=article.url)
                failed_count += 1
                fallback_judgment = self._create_fallback_judgment(article)
                judgments.append(fallback_judgment)
            elif isinstance(result, JudgmentResult):
                judgments.append(result)
                # キャッシュに保存
                if self._cache_repository is not None:
                    try:
                        self._cache_repository.put(result)
                    except Exception as e:
                        logger.error(
                            "cache_put_failed",
                            url=article.url,
                            error=str(e),
                        )
                else:
                    logger.debug(
                        "cache_put_skipped", url=article.url, message="CacheRepository is None"
                    )

        logger.info(
            "llm_judgment_complete",
            total_count=len(articles),
            success_count=len(judgments) - failed_count,
            failed_count=failed_count,
        )

        return JudgmentBatchResult(judgments=judgments, failed_count=failed_count)

    async def _judge_single(self, article: Article) -> JudgmentResult:
        """単一記事を判定する（リトライ付き）.

        ThrottlingException や ServiceUnavailableException が発生した場合、
        最大 max_retries 回までリトライします。

        Args:
            article: 判定対象記事

        Returns:
            判定結果

        Raises:
            LlmJsonParseError: JSON解析に失敗した場合（リトライ後）
            ClientError: Bedrock API エラー（リトライ対象外 or 最大リトライ到達）
        """
        for attempt in range(self._max_retries + 1):
            try:
                # プロンプト生成
                prompt = self._build_prompt(article)

                # Bedrock呼び出し
                # ARNが設定されていればそれを使用、未設定ならmodel_idを使用
                model_identifier = (
                    self._inference_profile_arn if self._inference_profile_arn else self._model_id
                )
                response = await asyncio.to_thread(
                    self._bedrock_client.invoke_model,
                    modelId=model_identifier,
                    body=json.dumps(
                        {
                            "anthropic_version": "bedrock-2023-05-31",
                            "max_tokens": 1000,
                            "messages": [{"role": "user", "content": prompt}],
                        }
                    ),
                )

                # レスポンス解析
                response_body = json.loads(response["body"].read())
                content = response_body["content"][0]["text"]

                # JSON解析
                judgment_data = self._parse_response(content)

                # JudgmentResult作成
                judgment = JudgmentResult(
                    url=article.url,
                    title=article.title,
                    description=article.description,
                    interest_label=InterestLabel(judgment_data["interest_label"]),
                    buzz_label=BuzzLabel.LOW,  # BuzzScoreから後で上書きされる
                    confidence=float(judgment_data["confidence"]),
                    summary=judgment_data["summary"][:300],  # 最大300文字
                    model_id=self._model_id,
                    judged_at=now_utc(),
                    published_at=article.published_at,
                    tags=self._extract_tags(judgment_data),
                )

                logger.debug(
                    "llm_judgment_success",
                    url=article.url,
                    interest_label=judgment.interest_label.value,
                )

                return judgment

            except LlmJsonParseError as e:
                if attempt < self._max_retries:
                    logger.warning(
                        "llm_judgment_retry",
                        url=article.url,
                        attempt=attempt + 1,
                        error=str(e),
                    )
                    await asyncio.sleep(1.0 * (attempt + 1))  # 指数バックオフ
                    continue
                logger.error(
                    "llm_judgment_json_parse_failed",
                    url=article.url,
                    error=str(e),
                )
                raise

            except ClientError as e:
                # Bedrock API エラー（ThrottlingException, ServiceUnavailableException など）
                error_code = e.response.get("Error", {}).get("Code", "")

                # リトライ対象のエラーか判定
                # ThrottlingException: レート制限超過（429相当）
                # ServiceUnavailableException: サービス利用不可（5xx相当）
                is_retryable = error_code in ["ThrottlingException", "ServiceUnavailableException"]

                if is_retryable and attempt < self._max_retries:
                    # 指数バックオフ + ジッター計算
                    backoff_delay = self._calculate_backoff(
                        attempt=attempt,
                        base_delay=self._retry_base_delay,
                        max_backoff=self._max_backoff,
                    )
                    logger.warning(
                        "llm_judgment_retry_throttling",
                        url=article.url,
                        attempt=attempt + 1,
                        error_code=error_code,
                        backoff_delay=backoff_delay,
                        error=str(e),
                    )
                    await asyncio.sleep(backoff_delay)
                    continue
                # リトライ対象外（ValidationException, AccessDeniedException など）
                # または最大リトライ回数に到達
                logger.error(
                    "llm_judgment_client_error",
                    url=article.url,
                    error_code=error_code,
                    error=str(e),
                )
                raise

            except Exception as e:
                logger.error(
                    "llm_judgment_unexpected_error",
                    url=article.url,
                    error=str(e),
                )
                raise

        # ここには到達しないはずだが、型チェックのため
        raise LlmJsonParseError("Max retries exceeded")

    @staticmethod
    def _calculate_backoff(attempt: int, base_delay: float, max_backoff: float) -> float:
        """指数バックオフ + ジッターを計算する.

        Args:
            attempt: リトライ回数（0始まり）
            base_delay: 基本遅延時間（秒）
            max_backoff: 最大バックオフ時間（秒）

        Returns:
            計算されたバックオフ時間（秒）
        """
        delay: float = min(base_delay * (2**attempt), max_backoff)
        jitter: float = random.uniform(0, delay * 0.5)  # 最大50%のジッター
        return delay + jitter

    def _build_prompt(self, article: Article) -> str:
        """判定プロンプトを生成する.

        Args:
            article: 判定対象記事

        Returns:
            プロンプト文字列
        """
        # InterestProfileから動的に生成
        profile_text = self._interest_profile.format_for_prompt()
        criteria_text = self._interest_profile.format_criteria_for_prompt()

        return f"""以下の記事について、関心度を判定してください。

# 関心プロファイル
{profile_text}

# 記事情報
- タイトル: {article.title}
- URL: {article.url}
- 概要: {article.description}
- ソース: {article.source_name}

# 判定基準
**interest_label**（関心度）:
{criteria_text}

**confidence**（信頼度）: 0.0-1.0の範囲で判定の確信度を示す
**summary**（要約）: 記事の内容を簡潔に要約（最大300文字、メール表示用）
**tags**（タグ）: 記事内容を表す技術キーワードを1-3個（例: "Kotlin", "Claude", "AWS"）

# 出力形式
JSON形式で以下のキーを含めて出力してください:
{{
  "interest_label": "ACT_NOW" | "THINK" | "FYI" | "IGNORE",
  "confidence": 0.85,
  "summary": "記事の内容を簡潔に要約",
  "tags": ["Kotlin", "Claude"]
}}

JSON以外は出力しないでください。"""

    def _parse_response(self, response_text: str) -> dict[str, Any]:
        """LLMレスポンスからJSON判定結果を解析する.

        Args:
            response_text: LLMの出力テキスト

        Returns:
            判定結果の辞書

        Raises:
            LlmJsonParseError: JSON解析に失敗した場合
        """
        try:
            # JSON部分を抽出（マークダウンコードブロックを除去）
            json_text = response_text.strip()
            if json_text.startswith("```json"):
                json_text = json_text[7:]  # "```json\n" を除去
            if json_text.startswith("```"):
                json_text = json_text[3:]  # "```" を除去
            if json_text.endswith("```"):
                json_text = json_text[:-3]  # "```" を除去
            json_text = json_text.strip()

            # JSON解析
            data: dict[str, Any] = json.loads(json_text)

            # 必須フィールドの検証
            required_fields = ["interest_label", "confidence", "summary"]
            for field in required_fields:
                if field not in data:
                    raise LlmJsonParseError(f"Missing required field: {field}")

            data["tags"] = self._extract_tags(data)
            return data

        except json.JSONDecodeError as e:
            raise LlmJsonParseError(f"JSON decode error: {e}") from e
        except Exception as e:
            raise LlmJsonParseError(f"Unexpected parse error: {e}") from e

    def _create_fallback_judgment(self, article: Article) -> JudgmentResult:
        """判定失敗時のフォールバック判定結果を作成する.

        Args:
            article: 記事

        Returns:
            IGNORE扱いの判定結果
        """
        return JudgmentResult(
            url=article.url,
            title=article.title,
            description=article.description,
            interest_label=InterestLabel.IGNORE,
            buzz_label=BuzzLabel.LOW,
            confidence=0.0,
            summary="LLM judgment failed",
            model_id=self._model_id,
            judged_at=now_utc(),
            published_at=article.published_at,
            tags=[],
        )

    def _extract_tags(self, judgment_data: dict[str, Any]) -> list[str]:
        """LLMレスポンスからタグ配列を取り出して正規化する."""
        raw_tags = judgment_data.get("tags", [])
        if not isinstance(raw_tags, list):
            return []

        normalized: list[str] = []
        for tag in raw_tags:
            if not isinstance(tag, str):
                continue
            clean_tag = tag.strip()
            if not clean_tag:
                continue
            normalized.append(clean_tag[:30])
            if len(normalized) >= 5:
                break
        return normalized
