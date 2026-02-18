"""記事正規化サービスモジュール."""

import html
from dataclasses import replace

from src.models.article import Article
from src.shared.logging.logger import get_logger
from src.shared.utils.date_utils import to_utc
from src.shared.utils.url_normalizer import normalize_url

logger = get_logger(__name__)


class Normalizer:
    """記事正規化サービス.

    収集した記事を統一フォーマットに正規化する.
    URL、日時、タイトル、概要を整形する.
    """

    def normalize(self, articles: list[Article]) -> list[Article]:
        """記事リストを正規化する.

        Args:
            articles: 収集した記事のリスト

        Returns:
            正規化された記事のリスト
        """
        logger.debug("normalization_start", article_count=len(articles))

        normalized_articles: list[Article] = []

        for article in articles:
            try:
                # URL正規化（normalized_urlを更新）
                normalized_url = normalize_url(article.url)

                # タイトル正規化
                normalized_title = self._normalize_title(article.title)

                # 概要正規化
                normalized_description = self._normalize_description(article.description)

                # 日時正規化（UTC統一）
                normalized_published_at = to_utc(article.published_at)
                normalized_collected_at = to_utc(article.collected_at)

                # 正規化された記事を作成
                normalized_article = replace(
                    article,
                    normalized_url=normalized_url,
                    title=normalized_title,
                    description=normalized_description,
                    published_at=normalized_published_at,
                    collected_at=normalized_collected_at,
                )

                normalized_articles.append(normalized_article)

            except Exception as e:
                logger.warning(
                    "article_normalization_failed",
                    url=article.url,
                    error=str(e),
                )
                continue

        logger.info(
            "normalization_complete",
            input_count=len(articles),
            output_count=len(normalized_articles),
        )

        return normalized_articles

    def _normalize_title(self, title: str) -> str:
        """タイトルを正規化する.

        HTML実体参照をデコードし、前後の空白を除去する.

        Args:
            title: タイトル

        Returns:
            正規化されたタイトル
        """
        # HTML実体参照をデコード（例: &amp; → &, &lt; → <）
        decoded_title = html.unescape(title)

        # 前後空白除去
        normalized_title = decoded_title.strip()

        # 空の場合はデフォルト値
        return normalized_title if normalized_title else "No Title"

    def _normalize_description(self, description: str) -> str:
        """概要を正規化する.

        HTML実体参照をデコードし、最大800文字に制限する.

        Args:
            description: 概要

        Returns:
            正規化された概要（最大800文字）
        """
        # HTML実体参照をデコード
        decoded_description = html.unescape(description)

        # 前後空白除去
        trimmed_description = decoded_description.strip()

        # 最大800文字に制限
        normalized_description = trimmed_description[:800]

        # 空の場合はデフォルト値
        return normalized_description if normalized_description else "No description"
