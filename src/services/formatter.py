"""メール本文フォーマットサービスモジュール."""

from datetime import datetime

from src.models.judgment import InterestLabel, JudgmentResult
from src.shared.logging.logger import get_logger

logger = get_logger(__name__)


class Formatter:
    """メール本文フォーマットサービス.

    最終選定された記事をプレーンテキスト形式のメール本文に整形する.
    """

    def format(
        self,
        selected_articles: list[JudgmentResult],
        collected_count: int,
        judged_count: int,
        executed_at: datetime,
    ) -> str:
        """メール本文を生成する.

        Args:
            selected_articles: 最終選定された記事のリスト
            collected_count: 収集件数
            judged_count: LLM判定件数
            executed_at: 実行日時

        Returns:
            プレーンテキスト形式のメール本文
        """
        logger.info("formatting_start", article_count=len(selected_articles))

        # セクション別に分類
        act_now_articles = [
            a for a in selected_articles if a.interest_label == InterestLabel.ACT_NOW
        ]
        think_articles = [a for a in selected_articles if a.interest_label == InterestLabel.THINK]
        fyi_articles = [a for a in selected_articles if a.interest_label == InterestLabel.FYI]

        # メール本文を構築
        body_parts = []

        # ヘッダー
        body_parts.append("=" * 80)
        body_parts.append("AI Curated Newsletter")
        body_parts.append("=" * 80)
        body_parts.append("")

        # サマリ統計
        body_parts.append("【実行サマリ】")
        body_parts.append(f"実行日時: {executed_at.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        body_parts.append(f"収集件数: {collected_count} 件")
        body_parts.append(f"LLM判定件数: {judged_count} 件")
        body_parts.append(f"最終通知件数: {len(selected_articles)} 件")
        body_parts.append("")

        # ACT_NOW セクション
        if act_now_articles:
            body_parts.append("=" * 80)
            body_parts.append(f"🚀 ACT_NOW ({len(act_now_articles)}件)")
            body_parts.append("今すぐ読むべき重要な記事")
            body_parts.append("=" * 80)
            body_parts.append("")
            for i, article in enumerate(act_now_articles, 1):
                body_parts.extend(self._format_article(i, article))
                body_parts.append("")

        # THINK セクション
        if think_articles:
            body_parts.append("=" * 80)
            body_parts.append(f"💡 THINK ({len(think_articles)}件)")
            body_parts.append("設計判断に役立つ記事")
            body_parts.append("=" * 80)
            body_parts.append("")
            for i, article in enumerate(think_articles, 1):
                body_parts.extend(self._format_article(i, article))
                body_parts.append("")

        # FYI セクション
        if fyi_articles:
            body_parts.append("=" * 80)
            body_parts.append(f"📌 FYI ({len(fyi_articles)}件)")
            body_parts.append("知っておくとよい記事")
            body_parts.append("=" * 80)
            body_parts.append("")
            for i, article in enumerate(fyi_articles, 1):
                body_parts.extend(self._format_article(i, article))
                body_parts.append("")

        # フッター
        body_parts.append("=" * 80)
        body_parts.append("🤖 Generated with Claude Code")
        body_parts.append("=" * 80)

        body = "\n".join(body_parts)

        logger.info("formatting_complete", body_length=len(body))

        return body

    def _format_article(self, index: int, article: JudgmentResult) -> list[str]:
        """単一記事をフォーマットする.

        Args:
            index: 記事番号
            article: 判定結果

        Returns:
            フォーマット済みテキストの行リスト
        """
        lines = []
        lines.append(f"[{index}] {article.title}")
        lines.append(f"URL: {article.url}")
        lines.append(f"Buzz: {article.buzz_label.value}")
        lines.append(f"概要: {article.description}")
        lines.append("-" * 80)
        return lines
