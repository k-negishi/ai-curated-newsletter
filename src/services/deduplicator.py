"""重複排除サービスモジュール."""

from dataclasses import dataclass

from src.models.article import Article
from src.repositories.cache_repository import CacheRepository
from src.shared.logging.logger import get_logger

logger = get_logger(__name__)


@dataclass
class DeduplicationResult:
    """重複排除結果.

    Attributes:
        unique_articles: 重複排除後の記事リスト
        duplicate_count: 重複件数（同一URL）
        cached_count: キャッシュヒット件数（既に判定済み）
    """

    unique_articles: list[Article]
    duplicate_count: int
    cached_count: int


class Deduplicator:
    """重複排除サービス.

    URL完全一致による重複排除と、キャッシュ済み記事の除外を行う.

    Attributes:
        _cache_repository: キャッシュリポジトリ
    """

    def __init__(self, cache_repository: CacheRepository | None) -> None:
        """重複排除サービスを初期化する.

        Args:
            cache_repository: キャッシュリポジトリ（Noneの場合はキャッシュチェックをスキップ）
        """
        self._cache_repository = cache_repository

    def deduplicate(self, articles: list[Article]) -> DeduplicationResult:
        """記事リストから重複を排除する.

        1. normalized_url で重複チェック（先に出現した記事を優先）
        2. キャッシュ済み記事を除外（既にLLM判定済み）

        Args:
            articles: 正規化済み記事のリスト

        Returns:
            重複排除結果
        """
        logger.debug("deduplication_start", article_count=len(articles))

        # ステップ1: URL重複排除（normalized_url で判定）
        seen_urls: set[str] = set()
        url_unique_articles: list[Article] = []
        duplicate_count = 0

        for article in articles:
            if article.normalized_url in seen_urls:
                duplicate_count += 1
                logger.debug(
                    "duplicate_article_found",
                    url=article.url,
                    normalized_url=article.normalized_url,
                )
                continue

            seen_urls.add(article.normalized_url)
            url_unique_articles.append(article)

        logger.debug(
            "url_deduplication_complete",
            unique_count=len(url_unique_articles),
            duplicate_count=duplicate_count,
        )

        # ステップ2: キャッシュ済み記事の除外
        # 一括でキャッシュ存在チェック
        urls_to_check = [article.url for article in url_unique_articles]
        if self._cache_repository is not None:
            cache_results = self._cache_repository.batch_exists(urls_to_check)
        else:
            logger.debug(
                "cache_check_skipped", message="CacheRepository is None, skipping cache check"
            )
            cache_results = {}  # 空辞書: 全記事がキャッシュヒットしていないとみなす

        final_articles: list[Article] = []
        cached_count = 0

        for article in url_unique_articles:
            if cache_results.get(article.url, False):
                cached_count += 1
                logger.debug(
                    "cached_article_found",
                    url=article.url,
                )
                continue

            final_articles.append(article)

        logger.info(
            "deduplication_complete",
            input_count=len(articles),
            output_count=len(final_articles),
            duplicate_count=duplicate_count,
            cached_count=cached_count,
        )

        return DeduplicationResult(
            unique_articles=final_articles,
            duplicate_count=duplicate_count,
            cached_count=cached_count,
        )
