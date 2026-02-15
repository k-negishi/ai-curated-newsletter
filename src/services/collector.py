"""記事収集サービスモジュール."""

import asyncio
from dataclasses import dataclass
from datetime import datetime

import feedparser  # type: ignore[import-untyped]
import httpx

from src.models.article import Article
from src.models.source_config import SourceConfig
from src.repositories.source_master import SourceMaster
from src.shared.exceptions.collection_error import SourceCollectionError
from src.shared.logging.logger import get_logger
from src.shared.utils.date_utils import now_utc, struct_time_to_datetime
from src.shared.utils.url_normalizer import normalize_url

logger = get_logger(__name__)


@dataclass
class CollectionResult:
    """収集結果.

    Attributes:
        articles: 収集された記事のリスト
        errors: 収集エラー（source_id -> エラーメッセージ）
    """

    articles: list[Article]
    errors: dict[str, str]


class Collector:
    """記事収集サービス.

    複数のRSS/Atomフィードから記事を並列収集する.

    Attributes:
        _source_master: 収集元マスタ
    """

    def __init__(self, source_master: SourceMaster) -> None:
        """収集サービスを初期化する.

        Args:
            source_master: 収集元マスタ
        """
        self._source_master = source_master

    async def collect(self) -> CollectionResult:
        """全有効ソースから記事を収集する.

        複数ソースから並列収集を行い、ソース単位のエラーは継続する.

        Returns:
            収集結果（記事リストとエラー情報）
        """
        sources = self._source_master.get_enabled_sources()
        logger.info("collection_start", source_count=len(sources))

        # 並列収集
        tasks = [self._collect_from_source(source) for source in sources]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 結果を集約
        all_articles: list[Article] = []
        errors: dict[str, str] = {}

        for source, result in zip(sources, results, strict=True):
            if isinstance(result, Exception):
                error_msg = str(result)
                errors[source.source_id] = error_msg
                logger.warning(
                    "source_collection_failed",
                    source_id=source.source_id,
                    error=error_msg,
                )
            elif isinstance(result, list):
                all_articles.extend(result)
                logger.debug(
                    "source_collection_success",
                    source_id=source.source_id,
                    article_count=len(result),
                )

        logger.info(
            "collection_complete",
            total_articles=len(all_articles),
            failed_sources=len(errors),
        )

        return CollectionResult(articles=all_articles, errors=errors)

    async def _collect_from_source(self, source: SourceConfig) -> list[Article]:
        """単一ソースから記事を収集する.

        Args:
            source: 収集元設定

        Returns:
            記事のリスト

        Raises:
            SourceCollectionError: 収集に失敗した場合
        """
        logger.debug("source_collection_start", source_id=source.source_id)

        try:
            # HTTP リクエスト（リトライ付き）
            async with httpx.AsyncClient(timeout=source.timeout_seconds) as client:
                for attempt in range(source.retry_count + 1):
                    try:
                        response = await client.get(str(source.feed_url))
                        response.raise_for_status()
                        feed_content = response.text
                        break
                    except (httpx.HTTPError, httpx.TimeoutException) as e:
                        if attempt == source.retry_count:
                            raise SourceCollectionError(
                                f"HTTP request failed after {source.retry_count + 1} attempts: {e}"
                            ) from e
                        logger.debug(
                            "source_collection_retry",
                            source_id=source.source_id,
                            attempt=attempt + 1,
                            error=str(e),
                        )
                        await asyncio.sleep(1.0 * (attempt + 1))  # 指数バックオフ

            # フィード解析
            feed = feedparser.parse(feed_content)

            if feed.bozo:
                raise SourceCollectionError(f"Feed parsing error: {feed.bozo_exception}")

            # 記事エントリを Article に変換
            articles: list[Article] = []
            collected_at = now_utc()

            for entry in feed.entries:
                try:
                    # 必須フィールドのチェック
                    if not hasattr(entry, "link") or not entry.link:
                        logger.debug(
                            "entry_missing_link",
                            source_id=source.source_id,
                            title=getattr(entry, "title", "N/A"),
                        )
                        continue

                    # URL正規化
                    url = entry.link
                    normalized_url = normalize_url(url)

                    # タイトル取得
                    title = getattr(entry, "title", "No Title")

                    # 公開日時取得
                    published_at = self._parse_published_date(entry)

                    # 概要取得
                    description = self._extract_description(entry)

                    article = Article(
                        url=url,
                        title=title,
                        published_at=published_at,
                        source_name=source.name,
                        description=description,
                        normalized_url=normalized_url,
                        collected_at=collected_at,
                    )

                    articles.append(article)

                except Exception as e:
                    logger.debug(
                        "entry_parse_error",
                        source_id=source.source_id,
                        entry_link=getattr(entry, "link", "N/A"),
                        error=str(e),
                    )
                    continue

            logger.debug(
                "source_collection_complete",
                source_id=source.source_id,
                article_count=len(articles),
            )

            return articles

        except SourceCollectionError:
            raise
        except Exception as e:
            raise SourceCollectionError(f"Unexpected error: {e}") from e

    def _parse_published_date(self, entry: feedparser.FeedParserDict) -> datetime:
        """フィードエントリから公開日時を解析する.

        Args:
            entry: フィードエントリ

        Returns:
            公開日時（UTC）
        """
        # published または updated を試行
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            return struct_time_to_datetime(entry.published_parsed)
        if hasattr(entry, "updated_parsed") and entry.updated_parsed:
            return struct_time_to_datetime(entry.updated_parsed)
        # 日時情報がない場合は現在時刻を使用
        return now_utc()

    def _extract_description(self, entry: feedparser.FeedParserDict) -> str:
        """フィードエントリから概要を抽出する.

        Args:
            entry: フィードエントリ

        Returns:
            概要（最大500文字）
        """
        # summary または description を試行
        description = ""

        if hasattr(entry, "summary") and entry.summary:
            description = entry.summary
        elif hasattr(entry, "description") and entry.description:
            description = entry.description
        elif hasattr(entry, "content") and entry.content and len(entry.content) > 0:
            # content は通常リストなので最初の要素を取得
            description = entry.content[0].get("value", "")

        # HTML タグを除去（簡易版）
        import re

        description = re.sub(r"<[^>]+>", "", description)

        # 前後空白除去と長さ制限
        description = description.strip()[:500]

        return description or "No description"
