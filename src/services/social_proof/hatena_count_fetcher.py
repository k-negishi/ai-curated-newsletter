"""HatenaCountFetcherモジュール."""

import asyncio
import time
from typing import ClassVar
from urllib.parse import urlencode

import httpx

from src.services.social_proof.external_service_policy import ExternalServicePolicy
from src.shared.logging.logger import get_logger

logger = get_logger(__name__)


class HatenaCountFetcher:
    """はてなブックマーク数取得サービス.

    複数URLのはてなブックマーク数を一括取得し、スコア化する。
    /count/entries APIを使用し、50件ごとにバッチ処理を行う。

    Attributes:
        _policy: 外部サービス利用ポリシー
        _batch_size: 一括取得の最大件数（デフォルト: 50）
    """

    HATENA_BATCH_API_URL = "https://bookmark.hatenaapis.com/count/entries"
    DEFAULT_BATCH_SIZE = 50

    HATENA_SCORE_TABLE: ClassVar[list[tuple[int, float]]] = [
        (500, 100.0),  # 500件以上: 大事件
        (200, 92.0),  # 200〜499件: 大バズ
        (100, 80.0),  # 100〜199件: バズ
        (50, 65.0),  # 50〜99件: 話題
        (30, 50.0),  # 30〜49件: 良記事
        (15, 25.0),  # 15〜29件: 注目され始め
        (5, 12.0),  # 5〜14件: わずかに注目
        (1, 5.0),  # 1〜4件: ほぼノイズ
    ]

    def __init__(
        self,
        policy: ExternalServicePolicy | None = None,
        batch_size: int = DEFAULT_BATCH_SIZE,
    ) -> None:
        """HatenaCountFetcherを初期化する.

        Args:
            policy: 外部サービス利用ポリシー（デフォルト: 新規作成）
            batch_size: 一括取得の最大件数（デフォルト: 50）
        """
        self._policy = policy if policy is not None else ExternalServicePolicy()
        self._batch_size = batch_size

    async def fetch_batch(self, urls: list[str]) -> dict[str, float]:
        """複数URLのはてなブックマーク数を一括取得し、スコア化する.

        Args:
            urls: 記事URLリスト

        Returns:
            URLをキーとするスコア（0-100）の辞書
        """
        if not urls:
            return {}

        start_time = time.time()
        logger.debug("hatena_fetch_batch_start", url_count=len(urls))

        # 50件ごとに分割
        batches = [urls[i : i + self._batch_size] for i in range(0, len(urls), self._batch_size)]

        logger.debug("hatena_batch_split", batch_count=len(batches))

        # 各バッチを並列で取得
        tasks = [self._fetch_single_batch(batch) for batch in batches]
        batch_results = await asyncio.gather(*tasks, return_exceptions=True)

        # 結果を統合
        all_counts: dict[str, int] = {}
        for result in batch_results:
            if isinstance(result, Exception):
                logger.warning("hatena_batch_fetch_failed", error=str(result))
            elif isinstance(result, dict):
                all_counts.update(result)

        # スコア計算
        scores = self._calculate_scores(all_counts)

        elapsed = time.time() - start_time
        logger.info(
            "hatena_fetch_batch_complete",
            url_count=len(urls),
            success_count=len(scores),
            elapsed_seconds=round(elapsed, 2),
        )

        return scores

    async def _fetch_single_batch(self, urls: list[str]) -> dict[str, int]:
        """単一バッチのはてなブックマーク数を取得する.

        Args:
            urls: 記事URLリスト（最大50件）

        Returns:
            URLをキーとするブックマーク数の辞書

        Raises:
            httpx.HTTPError: API呼び出しが失敗した場合
        """
        try:
            # クエリパラメータを構築（url=url1&url=url2&...）
            params = [("url", url) for url in urls]
            query_string = urlencode(params)
            api_url = f"{self.HATENA_BATCH_API_URL}?{query_string}"

            async with httpx.AsyncClient() as client:
                response = await self._policy.fetch_with_policy(api_url, client)

                # JSONレスポンスをパース
                counts: dict[str, int] = response.json()

                logger.debug(
                    "hatena_batch_fetch_success",
                    batch_size=len(urls),
                    result_count=len(counts),
                )

                return counts

        except httpx.HTTPError as e:
            logger.error(
                "hatena_batch_fetch_error",
                batch_size=len(urls),
                error=str(e),
            )
            raise

    def _calculate_scores(self, counts: dict[str, int]) -> dict[str, float]:
        """ブックマーク数からスコアを計算する（区間マッピング方式）.

        HATENA_SCORE_TABLEを降順に走査し、最初にマッチした閾値のスコアを返す。
        - 500件以上: 100点（大事件）
        - 200〜499件: 92点（大バズ）
        - 100〜199件: 80点（バズ）
        - 50〜99件: 65点（話題）
        - 30〜49件: 50点（良記事）
        - 15〜29件: 25点（注目され始め）
        - 5〜14件: 12点（わずかに注目）
        - 1〜4件: 5点（ほぼノイズ）
        - 0件: 0点

        Args:
            counts: URLをキーとするブックマーク数の辞書

        Returns:
            URLをキーとするスコア（0-100）の辞書
        """
        scores = {}
        for url, count in counts.items():
            score = 0.0
            for threshold, mapped_score in self.HATENA_SCORE_TABLE:
                if count >= threshold:
                    score = mapped_score
                    break
            scores[url] = score

        return scores
