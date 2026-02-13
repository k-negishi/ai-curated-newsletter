"""判定キャッシュリポジトリモジュール."""

import hashlib
from typing import Any

from botocore.exceptions import ClientError

from src.models.judgment import JudgmentResult
from src.shared.logging.logger import get_logger

logger = get_logger(__name__)


class CacheRepository:
    """判定キャッシュリポジトリ.

    DynamoDBに判定結果をキャッシュし、再判定を防ぐ.

    Attributes:
        _table: DynamoDBテーブルリソース
        _table_name: テーブル名
    """

    def __init__(self, dynamodb_resource: Any, table_name: str) -> None:
        """リポジトリを初期化する.

        Args:
            dynamodb_resource: DynamoDBリソース（boto3.resource('dynamodb')）
            table_name: テーブル名
        """
        self._dynamodb = dynamodb_resource
        self._table_name = table_name
        self._table = dynamodb_resource.Table(table_name)

    def _generate_pk(self, url: str) -> str:
        """URLからパーティションキーを生成する.

        Args:
            url: 記事URL

        Returns:
            パーティションキー（URL#<sha256>形式）
        """
        url_hash = hashlib.sha256(url.encode()).hexdigest()[:16]
        return f"URL#{url_hash}"

    def _generate_sk(self) -> str:
        """ソートキーを生成する.

        Returns:
            ソートキー（JUDGMENT#v1固定）
        """
        return "JUDGMENT#v1"

    def get(self, url: str) -> JudgmentResult | None:
        """キャッシュから判定結果を取得する.

        Args:
            url: 記事URL

        Returns:
            判定結果（存在しない場合None）
        """
        try:
            response = self._table.get_item(
                Key={
                    "PK": self._generate_pk(url),
                    "SK": self._generate_sk(),
                }
            )

            if "Item" not in response:
                return None

            item = response["Item"]
            # DynamoDBアイテムからJudgmentResultに変換
            from datetime import datetime

            from src.models.judgment import BuzzLabel, InterestLabel

            return JudgmentResult(
                url=item["url"],
                title=item.get("title", "No Title"),  # 欠損値の場合は"No Title"
                description=item.get("description", ""),  # 欠損値の場合は空文字列
                interest_label=InterestLabel(item["interest_label"]),
                buzz_label=BuzzLabel(item["buzz_label"]),
                confidence=float(item["confidence"]),
                reason=item["reason"],
                model_id=item["model_id"],
                judged_at=datetime.fromisoformat(item["judged_at"]),
            )

        except ClientError as e:
            logger.error("cache_get_error", url=url, error=str(e))
            return None

    def put(self, judgment: JudgmentResult) -> None:
        """判定結果をキャッシュに保存する.

        注: dry_run=true の場合でも、キャッシュは保存されます。
        これにより、テスト実行でも判定結果が永続化され、次回以降の
        テスト実行でキャッシュが活用されます。

        Args:
            judgment: 判定結果
        """
        try:
            self._table.put_item(
                Item={
                    "PK": self._generate_pk(judgment.url),
                    "SK": self._generate_sk(),
                    "url": judgment.url,
                    "title": judgment.title,
                    "description": judgment.description,
                    "interest_label": judgment.interest_label.value,
                    "buzz_label": judgment.buzz_label.value,
                    "confidence": judgment.confidence,
                    "reason": judgment.reason,
                    "model_id": judgment.model_id,
                    "judged_at": judgment.judged_at.isoformat(),
                }
            )
            logger.debug("cache_put_success", url=judgment.url)

        except ClientError as e:
            logger.error("cache_put_error", url=judgment.url, error=str(e))
            raise

    def exists(self, url: str) -> bool:
        """URLが既に判定済みか確認する.

        Args:
            url: 記事URL

        Returns:
            判定済みの場合True
        """
        return self.get(url) is not None

    def batch_exists(self, urls: list[str]) -> dict[str, bool]:
        """複数URLの判定済み状態を一括確認する.

        Args:
            urls: URLリスト

        Returns:
            URLをキーとする判定済みフラグの辞書
        """
        if not urls:
            return {}

        result: dict[str, bool] = {}

        # DynamoDB BatchGetItemは最大100件まで
        batch_size = 100
        for i in range(0, len(urls), batch_size):
            batch_urls = urls[i : i + batch_size]

            # リクエストキーを構築
            keys = [{"PK": self._generate_pk(url), "SK": self._generate_sk()} for url in batch_urls]

            try:
                response = self._dynamodb.batch_get_item(
                    RequestItems={
                        self._table_name: {
                            "Keys": keys,
                        }
                    }
                )

                # 存在するURLを取得
                existing_urls = {
                    item["url"] for item in response.get("Responses", {}).get(self._table_name, [])
                }

                # 結果を構築
                for url in batch_urls:
                    result[url] = url in existing_urls

            except ClientError as e:
                logger.error("cache_batch_exists_error", batch_size=len(batch_urls), error=str(e))
                # エラー時は全てFalseとして扱う（安全側に倒す）
                for url in batch_urls:
                    result[url] = False

        return result
