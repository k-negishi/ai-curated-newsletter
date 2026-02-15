"""メール本文フォーマットサービスモジュール."""

import html
from datetime import datetime
from zoneinfo import ZoneInfo

from src.models.judgment import InterestLabel, JudgmentResult
from src.shared.logging.logger import get_logger

logger = get_logger(__name__)


class Formatter:
    """メール本文フォーマットサービス.

    最終選定された記事をプレーンテキスト形式・HTML形式で整形する.
    """

    _TOKYO_TZ = ZoneInfo("Asia/Tokyo")
    # Gmail署名誤判定を避けるため、'=' や '-' の代わりに '─' を使用
    _SECTION_SEPARATOR = "─" * 40
    _ITEM_SEPARATOR = "─" * 40

    def format(
        self,
        selected_articles: list[JudgmentResult],
        collected_count: int,
        judged_count: int,
        executed_at: datetime,
    ) -> str:
        """メール本文（プレーンテキスト）を生成する."""
        logger.info("formatting_start", article_count=len(selected_articles))

        act_now_articles = [
            a for a in selected_articles if a.interest_label == InterestLabel.ACT_NOW
        ]
        think_articles = [a for a in selected_articles if a.interest_label == InterestLabel.THINK]
        fyi_articles = [a for a in selected_articles if a.interest_label == InterestLabel.FYI]

        jst_executed_at = self._to_jst(executed_at)
        body_parts: list[str] = []
        body_parts.append(self._SECTION_SEPARATOR)
        body_parts.append("Techニュースレター")
        body_parts.append(self._SECTION_SEPARATOR)
        body_parts.append("")
        body_parts.append("【実行サマリ】")
        body_parts.append(f"実行日時: {jst_executed_at.strftime('%Y-%m-%d %H:%M:%S')}")
        body_parts.append(f"収集件数: {collected_count} 件")
        body_parts.append(f"LLM判定件数: {judged_count} 件")
        body_parts.append(f"最終通知件数: {len(selected_articles)} 件")
        body_parts.append("")

        article_index = 1
        article_index = self._append_text_section(
            body_parts=body_parts,
            title=f"🚀 ACT_NOW ({len(act_now_articles)}件)",
            subtitle="今すぐ読むべき重要な記事",
            articles=act_now_articles,
            start_index=article_index,
        )
        article_index = self._append_text_section(
            body_parts=body_parts,
            title=f"💡 THINK ({len(think_articles)}件)",
            subtitle="技術判断に役立つ記事",
            articles=think_articles,
            start_index=article_index,
        )
        self._append_text_section(
            body_parts=body_parts,
            title=f"📌 FYI ({len(fyi_articles)}件)",
            subtitle="知っておくとよい記事",
            articles=fyi_articles,
            start_index=article_index,
        )

        body_parts.append(self._SECTION_SEPARATOR)
        body_parts.append(f"生成日時: {jst_executed_at.strftime('%Y-%m-%d %H:%M:%S')}")
        body_parts.append("")
        body_parts.append("Generated with Claude Code")
        body_parts.append(self._SECTION_SEPARATOR)

        body = "\n".join(body_parts)
        logger.info("formatting_complete", body_length=len(body))
        return body

    def format_html(
        self,
        selected_articles: list[JudgmentResult],
        collected_count: int,
        judged_count: int,
        executed_at: datetime,
    ) -> str:
        """メール本文（HTML）を生成する."""
        act_now_articles = [
            a for a in selected_articles if a.interest_label == InterestLabel.ACT_NOW
        ]
        think_articles = [a for a in selected_articles if a.interest_label == InterestLabel.THINK]
        fyi_articles = [a for a in selected_articles if a.interest_label == InterestLabel.FYI]

        jst_executed_at = self._to_jst(executed_at)
        html_parts: list[str] = [
            "<html><body>",
            "<h1>Techニュースレター</h1>",
            "<h2>実行サマリ</h2>",
            f"<p>実行日時: {jst_executed_at.strftime('%Y-%m-%d %H:%M:%S')}</p>",
            f"<p>収集件数: {collected_count} 件</p>",
            f"<p>LLM判定件数: {judged_count} 件</p>",
            f"<p>最終通知件数: {len(selected_articles)} 件</p>",
        ]

        article_index = 1
        article_index = self._append_html_section(
            html_parts=html_parts,
            title=f"🚀 ACT_NOW ({len(act_now_articles)}件)",
            subtitle="今すぐ読むべき重要な記事",
            articles=act_now_articles,
            start_index=article_index,
        )
        article_index = self._append_html_section(
            html_parts=html_parts,
            title=f"💡 THINK ({len(think_articles)}件)",
            subtitle="技術判断に役立つ記事",
            articles=think_articles,
            start_index=article_index,
        )
        self._append_html_section(
            html_parts=html_parts,
            title=f"📌 FYI ({len(fyi_articles)}件)",
            subtitle="知っておくとよい記事",
            articles=fyi_articles,
            start_index=article_index,
        )

        html_parts.extend(
            [
                "<hr/>",
                f"<p>生成日時: {jst_executed_at.strftime('%Y-%m-%d %H:%M:%S')}</p>",
                "<br/>",
                "<p>Generated with Claude Code</p>",
                "</body></html>",
            ]
        )
        return "".join(html_parts)

    def _append_text_section(
        self,
        body_parts: list[str],
        title: str,
        subtitle: str,
        articles: list[JudgmentResult],
        start_index: int,
    ) -> int:
        if not articles:
            return start_index

        body_parts.append(self._SECTION_SEPARATOR)
        body_parts.append(title)
        body_parts.append(subtitle)
        body_parts.append(self._SECTION_SEPARATOR)
        body_parts.append("")

        index = start_index
        for article in articles:
            body_parts.extend(self._format_article(index, article))
            body_parts.append("")
            index += 1
        return index

    def _append_html_section(
        self,
        html_parts: list[str],
        title: str,
        subtitle: str,
        articles: list[JudgmentResult],
        start_index: int,
    ) -> int:
        if not articles:
            return start_index

        html_parts.append(f"<h2>{self._escape_non_url_html_text(title)}</h2>")
        html_parts.append(f"<p>{self._escape_non_url_html_text(subtitle)}</p>")
        html_parts.append("<br/>")

        index = start_index
        for i, article in enumerate(articles):
            tag_text = self._format_tags(article.tags)
            safe_title = self._escape_non_url_html_text(article.title)
            safe_summary = self._escape_non_url_html_text(article.summary)
            safe_tag_text = self._escape_non_url_html_text(tag_text)
            safe_url = html.escape(article.url, quote=True)

            published_date = self._format_published_date(article.published_at)
            safe_published_date = self._escape_non_url_html_text(published_date)

            html_parts.append(
                f"[{index}] {safe_title}<br/>"
                f"Tag: {safe_tag_text}<br/>"
                f"公開日: {safe_published_date}<br/>"
                f'URL: <a href="{safe_url}" target="_blank" rel="noopener noreferrer">'
                f"{safe_url}</a><br/>"
                f"Buzz: {article.buzz_label.value}<br/>"
                f"概要: {safe_summary}"
            )

            # 最後の記事以外は記事間に空白行を追加
            if i < len(articles) - 1:
                html_parts.append("<br/><br/>")

            index += 1

        return index

    def _format_article(self, index: int, article: JudgmentResult) -> list[str]:
        return [
            f"[{index}] {article.title}",
            f"Tag: {self._format_tags(article.tags)}",
            f"公開日: {self._format_published_date(article.published_at)}",
            f"URL: {article.url}",
            f"Buzz: {article.buzz_label.value}",
            f"概要: {article.summary}",
            self._ITEM_SEPARATOR,
        ]

    def _to_jst(self, dt: datetime) -> datetime:
        return dt.astimezone(self._TOKYO_TZ)

    def _format_published_date(self, published_at: datetime) -> str:
        """公開日をYYYY-MM-DD形式でフォーマットする.

        Args:
            published_at: 公開日時（UTC）

        Returns:
            YYYY-MM-DD形式の文字列（JST）
        """
        jst_date = self._to_jst(published_at)
        return jst_date.strftime("%Y-%m-%d")

    def _format_tags(self, tags: list[str]) -> str:
        if not tags:
            return "-"
        return ", ".join(tags)

    def _escape_non_url_html_text(self, value: str) -> str:
        return html.escape(value)
