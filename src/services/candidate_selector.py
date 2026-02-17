"""候補選定サービスモジュール."""

from dataclasses import dataclass

from src.models.article import Article
from src.models.buzz_score import BuzzScore
from src.shared.logging.logger import get_logger

logger = get_logger(__name__)


@dataclass
class SelectionResult:
    """候補選定結果.

    Attributes:
        candidates: 選定された候補記事のリスト
        total_score_dict: Buzzスコア辞書（normalized_url -> total_score）
    """

    candidates: list[Article]
    total_score_dict: dict[str, float]


class CandidateSelector:
    """候補選定サービス.

    Buzzスコアと鮮度に基づいて、LLM判定候補を選定する.

    Attributes:
        _max_candidates: 最大候補数
    """

    def __init__(self, max_candidates: int = 100) -> None:
        """候補選定サービスを初期化する.

        Args:
            max_candidates: 最大候補数（デフォルト: 100）
        """
        self._max_candidates = max_candidates

    def select(self, articles: list[Article], scores: dict[str, BuzzScore]) -> SelectionResult:
        """Buzzスコアに基づいて候補記事を選定する.

        ソート順:
        1. Buzzスコア降順
        2. 鮮度降順（公開日時の新しい順）

        Args:
            articles: 重複排除済み記事のリスト
            scores: Buzzスコア辞書（normalized_url -> BuzzScore）

        Returns:
            選定結果（上位max_candidates件）
        """
        logger.info(
            "candidate_selection_start",
            article_count=len(articles),
            max_candidates=self._max_candidates,
        )

        # スコアがない記事は除外
        articles_with_score = [article for article in articles if article.normalized_url in scores]

        # Buzzスコア降順 → 鮮度降順でソート
        sorted_articles = sorted(
            articles_with_score,
            key=lambda a: (
                -scores[a.normalized_url].total_score,
                -a.published_at.timestamp(),
            ),
        )

        # 上位max_candidates件を選定
        candidates = sorted_articles[: self._max_candidates]

        # total_score辞書を作成（後続処理で使用）
        total_score_dict: dict[str, float] = {
            article.normalized_url: scores[article.normalized_url].total_score
            for article in candidates
        }

        logger.info(
            "candidate_selection_complete",
            input_count=len(articles),
            output_count=len(candidates),
        )

        return SelectionResult(
            candidates=candidates,
            total_score_dict=total_score_dict,
        )
