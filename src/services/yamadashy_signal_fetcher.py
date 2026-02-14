"""YamadashySignalFetcherモジュール."""

import feedparser  # type: ignore[import-untyped]
import httpx

from src.services.external_service_policy import ExternalServicePolicy
from src.shared.logging.logger import get_logger
from src.shared.utils.url_normalizer import normalize_url

logger = get_logger(__name__)


class YamadashySignalFetcher:
    """yamadashy掲載シグナル取得サービス.

    yamadashy RSSフィードを取得し、記事URLが掲載されているか判定する。
    掲載されている場合はシグナル100、されていない場合は0を返す。

    Attributes:
        _policy: 外部サービス利用ポリシー
        _rss_url: yamadashy RSSのURL
    """

    DEFAULT_RSS_URL = "https://yamadashy.github.io/tech-blog-rss-feed/feeds/rss.xml"

    def __init__(
        self,
        policy: ExternalServicePolicy | None = None,
        rss_url: str = DEFAULT_RSS_URL,
    ) -> None:
        """YamadashySignalFetcherを初期化する.

        Args:
            policy: 外部サービス利用ポリシー（デフォルト: 新規作成）
            rss_url: yamadashy RSSのURL（デフォルト: 公式URL）
        """
        self._policy = policy if policy is not None else ExternalServicePolicy()
        self._rss_url = rss_url

    async def fetch_signals(self, urls: list[str]) -> dict[str, int]:
        """yamadashy掲載シグナルを取得する.

        Args:
            urls: 記事URLリスト

        Returns:
            URLをキーとするシグナル（100 or 0）の辞書
        """
        if not urls:
            return {}

        logger.info("yamadashy_fetch_signals_start", url_count=len(urls))

        # RSSを取得
        try:
            feed_urls = await self._fetch_rss_urls()
        except Exception as e:
            logger.error("yamadashy_rss_fetch_failed", error=str(e))
            # 失敗時は全て0
            return dict.fromkeys(urls, 0)

        # 正規化されたRSS URLのセットを作成
        normalized_feed_urls = {normalize_url(url) for url in feed_urls}

        logger.debug(
            "yamadashy_feed_urls_fetched",
            feed_url_count=len(normalized_feed_urls),
        )

        # 各URLについて掲載判定
        signals = {}
        for url in urls:
            normalized_url = normalize_url(url)
            signal = 100 if normalized_url in normalized_feed_urls else 0
            signals[url] = signal

        matched_count = sum(1 for s in signals.values() if s == 100)

        logger.info(
            "yamadashy_fetch_signals_complete",
            url_count=len(urls),
            matched_count=matched_count,
        )

        return signals

    async def _fetch_rss_urls(self) -> list[str]:
        """yamadashy RSSを取得し、URLリストを返す.

        Returns:
            RSS内のURLリスト

        Raises:
            httpx.HTTPError: RSS取得が失敗した場合
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await self._policy.fetch_with_policy(self._rss_url, client)

                # feedparserでRSSをパース
                feed = feedparser.parse(response.text)

                # 各エントリーのlinkを抽出
                urls = [entry.link for entry in feed.entries if hasattr(entry, "link")]

                logger.debug("yamadashy_rss_parsed", entry_count=len(urls))

                return urls

        except httpx.HTTPError as e:
            logger.error("yamadashy_rss_fetch_error", error=str(e))
            raise
