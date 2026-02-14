"""SocialProof取得サービスモジュール."""

import asyncio
from urllib.parse import urlencode

import httpx

from src.shared.logging.logger import get_logger

logger = get_logger(__name__)


class SocialProofFetcher:
    """SocialProof（外部反応）取得サービス.

    はてなブックマーク数を取得する.

    Attributes:
        _timeout: タイムアウト（秒）
        _concurrency_limit: 並列度制限
        _batch_size: はてなAPIの最大URL指定数
    """

    HATENA_BATCH_API_URL = "https://bookmark.hatenaapis.com/count/entries"
    DEFAULT_BATCH_SIZE = 50

    def __init__(
        self,
        timeout: int = 5,
        concurrency_limit: int = 10,
        batch_size: int = DEFAULT_BATCH_SIZE,
    ) -> None:
        """SocialProof取得サービスを初期化する.

        Args:
            timeout: タイムアウト（秒、デフォルト: 5）
            concurrency_limit: 並列度制限（デフォルト: 10）
            batch_size: はてなAPIに一度に渡すURL数（デフォルト: 50）
        """
        self._timeout = timeout
        self._concurrency_limit = concurrency_limit
        self._batch_size = batch_size

    async def fetch_batch(self, urls: list[str]) -> dict[str, int]:
        """複数URLのはてブ数を一括取得する.

        Args:
            urls: URLリスト

        Returns:
            URLをキーとするはてブ数の辞書
        """
        if not urls:
            return {}

        logger.info("social_proof_fetch_start", url_count=len(urls))

        batches = self._split_batches(urls)
        logger.debug("social_proof_batch_split", batch_count=len(batches))

        semaphore = asyncio.Semaphore(self._concurrency_limit)

        async def fetch_with_semaphore(batch_urls: list[str]) -> dict[str, int]:
            async with semaphore:
                return await self._fetch_single_batch(batch_urls)

        tasks = [fetch_with_semaphore(batch) for batch in batches]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 結果を集約
        counts: dict[str, int] = {}
        failed_batch_count = 0

        for result in results:
            if isinstance(result, Exception):
                logger.warning("social_proof_batch_fetch_failed", error=str(result))
                failed_batch_count += 1
            elif isinstance(result, dict):
                counts.update(result)

        logger.info(
            "social_proof_fetch_complete",
            total_count=len(urls),
            success_count=len(counts),
            failed_batch_count=failed_batch_count,
        )

        return counts

    def _split_batches(self, urls: list[str]) -> list[list[str]]:
        """URLリストをバッチサイズごとに分割する."""
        return [urls[i : i + self._batch_size] for i in range(0, len(urls), self._batch_size)]

    async def _fetch_single_batch(self, urls: list[str]) -> dict[str, int]:
        """単一バッチのはてブ数を取得する.

        Args:
            urls: 記事URLリスト（最大50件）

        Returns:
            URLをキーとするはてブ数の辞書
        """
        try:
            params = [("url", url) for url in urls]
            query = urlencode(params)
            api_url = f"{self.HATENA_BATCH_API_URL}?{query}"

            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.get(api_url)
                response.raise_for_status()

                raw_counts = response.json()
                if not isinstance(raw_counts, dict):
                    raise ValueError("Hatena API response must be dict")

                counts: dict[str, int] = {}
                for url, value in raw_counts.items():
                    try:
                        counts[url] = int(value)
                    except (TypeError, ValueError):
                        logger.warning(
                            "hatena_batch_count_parse_failed",
                            url=url,
                            value=value,
                        )
                        counts[url] = 0

                logger.debug(
                    "hatena_batch_fetch_success",
                    batch_size=len(urls),
                    result_count=len(counts),
                )

                return counts

        except (httpx.HTTPError, ValueError) as e:
            logger.warning("hatena_batch_fetch_failed", error=str(e), batch_size=len(urls))
            raise
