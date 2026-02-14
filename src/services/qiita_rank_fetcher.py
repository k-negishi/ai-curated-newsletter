"""QiitaRankFetcherモジュール."""

from urllib.parse import urlparse

import feedparser  # type: ignore[import-untyped]
import httpx

from src.services.external_service_policy import ExternalServicePolicy
from src.shared.logging.logger import get_logger
from src.shared.utils.url_normalizer import normalize_url

logger = get_logger(__name__)


class QiitaRankFetcher:
    """Qiita popular feed順位取得サービス.

    Qiita popular feedから順位を取得し、段階的スコアに変換する。
    Qiita以外のURLはスコア0として扱う。

    Attributes:
        _policy: 外部サービス利用ポリシー
        _feed_url: Qiita popular feedのURL
    """

    DEFAULT_FEED_URL = "https://qiita.com/popular-items/feed"
    QIITA_DOMAIN = "qiita.com"

    def __init__(
        self,
        policy: ExternalServicePolicy | None = None,
        feed_url: str = DEFAULT_FEED_URL,
    ) -> None:
        """QiitaRankFetcherを初期化する.

        Args:
            policy: 外部サービス利用ポリシー（デフォルト: 新規作成）
            feed_url: Qiita popular feedのURL（デフォルト: 公式URL）
        """
        self._policy = policy if policy is not None else ExternalServicePolicy()
        self._feed_url = feed_url

    async def fetch_batch(self, urls: list[str]) -> dict[str, float]:
        """Qiita popular feed内の順位を取得し、スコア化する.

        Args:
            urls: 記事URLリスト（Qiita以外は欠損扱い）

        Returns:
            URLをキーとするスコア（0-100）の辞書
        """
        if not urls:
            return {}

        logger.info("qiita_fetch_batch_start", url_count=len(urls))

        # Qiita URLとそれ以外を分離
        qiita_urls = []
        non_qiita_urls = []

        for url in urls:
            if self._is_qiita_url(url):
                qiita_urls.append(url)
            else:
                non_qiita_urls.append(url)

        logger.debug(
            "qiita_url_classification",
            qiita_url_count=len(qiita_urls),
            non_qiita_url_count=len(non_qiita_urls),
        )

        # Qiita popular feedを取得
        try:
            feed_ranks = await self._fetch_feed_ranks()
        except Exception as e:
            logger.error("qiita_feed_fetch_failed", error=str(e))
            # 失敗時は全て0
            return dict.fromkeys(urls, 0.0)

        # 各URLの順位を取得
        ranks: dict[str, int | None] = {}

        for url in qiita_urls:
            normalized_url = normalize_url(url)
            rank = feed_ranks.get(normalized_url)
            ranks[url] = rank

        # Qiita以外のURLはランクなし（スコア0）
        for url in non_qiita_urls:
            ranks[url] = None

        # スコア計算
        scores = self._calculate_scores(ranks)

        matched_count = sum(1 for r in ranks.values() if r is not None)

        logger.info(
            "qiita_fetch_batch_complete",
            url_count=len(urls),
            qiita_url_count=len(qiita_urls),
            matched_count=matched_count,
        )

        return scores

    def _is_qiita_url(self, url: str) -> bool:
        """URLがQiitaのURLかどうか判定する.

        Args:
            url: 記事URL

        Returns:
            Qiita URLの場合True
        """
        parsed = urlparse(url)
        return parsed.netloc == self.QIITA_DOMAIN

    async def _fetch_feed_ranks(self) -> dict[str, int]:
        """Qiita popular feedを取得し、URLと順位のマッピングを返す.

        Returns:
            正規化URLをキーとする順位（1始まり）の辞書

        Raises:
            httpx.HTTPError: feed取得が失敗した場合
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await self._policy.fetch_with_policy(self._feed_url, client)

                # feedparserでfeedをパース
                feed = feedparser.parse(response.text)

                # 各エントリーのlinkと順位をマッピング
                ranks = {}
                for rank, entry in enumerate(feed.entries, start=1):
                    if hasattr(entry, "link"):
                        normalized_url = normalize_url(entry.link)
                        ranks[normalized_url] = rank

                logger.debug("qiita_feed_parsed", entry_count=len(ranks))

                return ranks

        except httpx.HTTPError as e:
            logger.error("qiita_feed_fetch_error", error=str(e))
            raise

    def _calculate_scores(self, ranks: dict[str, int | None]) -> dict[str, float]:
        """順位からスコアを計算する.

        スコア計算式（段階的）:
        - 上位10件: 100点
        - 11-20件: 70点
        - 21-30件: 40点
        - 31-50件: 20点
        - 51件以降: 0点
        - ランク圏外（None）: 0点

        Args:
            ranks: URLをキーとする順位（None=圏外）の辞書

        Returns:
            URLをキーとするスコア（0-100）の辞書
        """
        scores = {}
        for url, rank in ranks.items():
            if rank is None:
                score = 0.0
            elif rank <= 10:
                score = 100.0
            elif rank <= 20:
                score = 70.0
            elif rank <= 30:
                score = 40.0
            elif rank <= 50:
                score = 20.0
            else:
                score = 0.0

            scores[url] = score

        return scores
