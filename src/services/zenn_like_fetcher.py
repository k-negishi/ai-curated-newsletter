"""ZennLikeFetcherモジュール（ランキングAPI版）."""

from urllib.parse import urlparse

import httpx

from src.services.external_service_policy import ExternalServicePolicy
from src.shared.logging.logger import get_logger

logger = get_logger(__name__)


class ZennLikeFetcher:
    """Zenn週間ランキング取得サービス.

    Zenn週間ランキングAPIから記事リストを取得し、ランキング順位に基づくスコアを計算する。
    Zenn以外のURLはスコア0として扱う。

    Attributes:
        _policy: 外部サービス利用ポリシー
    """

    ZENN_API_BASE_URL = "https://zenn.dev/api/articles"
    ZENN_DOMAIN = "zenn.dev"
    MAX_PAGES = 4  # 最大4ページ（100件程度）まで取得

    def __init__(
        self,
        policy: ExternalServicePolicy | None = None,
    ) -> None:
        """ZennLikeFetcherを初期化する.

        Args:
            policy: 外部サービス利用ポリシー（デフォルト: 新規作成）
        """
        self._policy = policy if policy is not None else ExternalServicePolicy()

    async def fetch_batch(self, urls: list[str]) -> dict[str, float]:
        """Zenn週間ランキングを取得し、スコア化する.

        Args:
            urls: 記事URLリスト（Zenn以外は欠損扱い）

        Returns:
            URLをキーとするスコア（0-100）の辞書
        """
        if not urls:
            return {}

        logger.info("zenn_fetch_batch_start", url_count=len(urls))

        # Zenn URLとそれ以外を分離
        zenn_urls = []
        non_zenn_urls = []

        for url in urls:
            if self._is_zenn_url(url):
                zenn_urls.append(url)
            else:
                non_zenn_urls.append(url)

        logger.debug(
            "zenn_url_classification",
            zenn_url_count=len(zenn_urls),
            non_zenn_url_count=len(non_zenn_urls),
        )

        # Zenn週間ランキングを取得
        try:
            ranking_map = await self._fetch_ranking()
        except Exception as e:
            logger.error("zenn_ranking_fetch_failed", error=str(e))
            ranking_map = {}

        # スコア計算
        scores = {}

        for url in urls:
            # Zenn URLの場合、ランキング内の順位を確認
            if url in ranking_map:
                rank = ranking_map[url]
                score = self._calculate_score_by_rank(rank)
                scores[url] = score
            else:
                # Zenn以外のURLまたはランキング圏外
                scores[url] = 0.0

        logger.info(
            "zenn_fetch_batch_complete",
            url_count=len(urls),
            zenn_url_count=len(zenn_urls),
            success_count=len(scores),
        )

        return scores

    def _is_zenn_url(self, url: str) -> bool:
        """URLがZennのURLかどうか判定する.

        Args:
            url: 記事URL

        Returns:
            Zenn URLの場合True
        """
        parsed = urlparse(url)
        return parsed.netloc == self.ZENN_DOMAIN

    async def _fetch_ranking(self) -> dict[str, int]:
        """Zenn週間ランキングを取得する（ページネーション対応）.

        Returns:
            URL -> ランキング順位の辞書（1-100位程度）

        Raises:
            httpx.HTTPError: API呼び出しが失敗した場合
        """
        ranking_map: dict[str, int] = {}
        current_rank = 1
        current_page = 1

        try:
            async with httpx.AsyncClient() as client:
                while current_page <= self.MAX_PAGES:
                    # ページネーションURL構築
                    api_url = self._build_api_url(current_page)

                    logger.debug("zenn_ranking_fetch_page", page=current_page, url=api_url)

                    # API呼び出し
                    response = await self._policy.fetch_with_policy(api_url, client)
                    data: dict[str, list[dict[str, str]] | int | None] = response.json()

                    # 記事リストを取得
                    articles: list[dict[str, str]] = data.get("articles", [])  # type: ignore[assignment]

                    if not articles:
                        logger.debug("zenn_ranking_no_more_articles", page=current_page)
                        break

                    # ランキングマップに追加
                    current_rank = self._add_articles_to_ranking(
                        ranking_map, articles, current_rank
                    )

                    # 次のページがあるか確認
                    next_page = data.get("next_page")
                    if next_page is None:
                        logger.debug("zenn_ranking_no_next_page", page=current_page)
                        break

                    current_page += 1

            logger.info("zenn_ranking_fetch_complete", total_articles=len(ranking_map))

        except httpx.HTTPError as e:
            logger.error("zenn_ranking_api_error", error=str(e))
            raise

        return ranking_map

    def _build_api_url(self, page: int) -> str:
        """Zenn週間ランキングAPIのURLを構築する.

        Args:
            page: ページ番号（1始まり）

        Returns:
            API URL
        """
        if page == 1:
            return f"{self.ZENN_API_BASE_URL}?order=weekly"
        else:
            return f"{self.ZENN_API_BASE_URL}?order=weekly&page={page}"

    def _add_articles_to_ranking(
        self, ranking_map: dict[str, int], articles: list[dict[str, str]], start_rank: int
    ) -> int:
        """記事リストをランキングマップに追加する.

        Args:
            ranking_map: ランキングマップ（更新される）
            articles: 記事リスト
            start_rank: 開始ランキング順位

        Returns:
            次の順位
        """
        current_rank = start_rank

        for article in articles:
            path = article.get("path", "")
            if path:
                # pathを完全URLに変換
                full_url = f"https://zenn.dev{path}"
                ranking_map[full_url] = current_rank
                current_rank += 1

        return current_rank

    def _calculate_score_by_rank(self, rank: int) -> float:
        """ランキング順位に基づくスコアを計算する.

        Args:
            rank: ランキング順位（1位、2位...）

        Returns:
            スコア（0-100）
        """
        if 1 <= rank <= 10:
            return 100.0
        elif 11 <= rank <= 30:
            return 80.0
        elif 31 <= rank <= 50:
            return 60.0
        elif 51 <= rank <= 100:
            return 40.0
        else:
            return 0.0
