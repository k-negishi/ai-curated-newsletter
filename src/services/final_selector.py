"""最終選定サービスモジュール."""

from collections import Counter
from dataclasses import dataclass
from typing import ClassVar
from urllib.parse import urlparse

from src.models.buzz_score import BuzzScore
from src.models.judgment import InterestLabel, JudgmentResult
from src.shared.logging.logger import get_logger

logger = get_logger(__name__)

# BuzzScoreが見つからない場合のフォールバック用ゼロスコア
_ZERO_BUZZ_SCORE = BuzzScore(
    url="",
    social_proof_score=0.0,
    interest_score=0.0,
    authority_score=0.0,
    social_proof_count=0,
    total_score=0.0,
)


@dataclass
class FinalSelectionResult:
    """最終選定結果.

    Attributes:
        selected_articles: 最終選定された記事のリスト（最大15件）
    """

    selected_articles: list[JudgmentResult]


class FinalSelector:
    """最終選定サービス.

    Composite Score（InterestLabel + 外部話題性の重み付き混合）と
    ドメイン偏り制御を行い、最終的に通知する記事を選定する.

    Composite Score = α × LABEL_SCORE[label] + (1-α) × normalized_external_buzz

    Attributes:
        _max_articles: 最大選定件数
        _max_per_domain: 同一ドメインの最大件数
    """

    # InterestLabelをスコア化（0-100スケール）
    LABEL_SCORE: ClassVar[dict[InterestLabel, float]] = {
        InterestLabel.ACT_NOW: 100.0,
        InterestLabel.THINK: 60.0,
        InterestLabel.FYI: 20.0,
        InterestLabel.IGNORE: 0.0,
    }

    # 混合比率: InterestLabel 40%, 外部話題性 60%
    INTEREST_WEIGHT: ClassVar[float] = 0.4
    BUZZ_WEIGHT: ClassVar[float] = 0.6

    def __init__(self, max_articles: int = 15, max_per_domain: int = 0) -> None:
        """最終選定サービスを初期化する.

        Args:
            max_articles: 最大選定件数（デフォルト: 15）
            max_per_domain: 同一ドメインの最大件数（デフォルト: 0=制限なし）
        """
        self._max_articles = max_articles
        self._max_per_domain = max_per_domain

    def select(
        self,
        judgments: list[JudgmentResult],
        buzz_scores: dict[str, BuzzScore] | None = None,
    ) -> FinalSelectionResult:
        """最終選定を行う.

        Composite Scoreで統合的にソートし、ドメイン偏り制御を適用する.

        優先順位:
        1. Composite Score降順（InterestLabel×α + external_buzz×(1-α)）
        2. 鮮度: judged_at降順
        3. Confidence: 信頼度降順

        Args:
            judgments: LLM判定結果のリスト
            buzz_scores: URL→BuzzScoreのマッピング（Noneの場合は全記事0.0扱い）

        Returns:
            最終選定結果（最大15件）
        """
        logger.debug(
            "final_selection_start",
            judgment_count=len(judgments),
            max_articles=self._max_articles,
        )

        # ステップ1: IGNORE除外
        non_ignore_judgments = [j for j in judgments if j.interest_label != InterestLabel.IGNORE]

        logger.debug(
            "ignore_filtered",
            input_count=len(judgments),
            output_count=len(non_ignore_judgments),
        )

        # ステップ2: Composite Scoreでソート
        sorted_judgments = self._sort_by_priority(non_ignore_judgments, buzz_scores)

        # ステップ2.5: 候補ランキングをログ出力
        self._log_candidates(sorted_judgments, buzz_scores)

        # ステップ3: ドメイン偏り制御しながら選定
        selected = self._select_with_domain_control(sorted_judgments, buzz_scores)

        logger.info(
            "final_selection_complete",
            input_count=len(judgments),
            output_count=len(selected),
        )

        return FinalSelectionResult(selected_articles=selected)

    def _calculate_composite_score(
        self, interest_label: InterestLabel, buzz_score: BuzzScore
    ) -> float:
        """Composite Scoreを計算する.

        composite = α × LABEL_SCORE[label] + (1-α) × normalized_external_buzz

        Args:
            interest_label: LLM判定によるInterestLabel
            buzz_score: BuzzScore（external_buzzプロパティを使用）

        Returns:
            Composite Score（0-100）
        """
        label_score = self.LABEL_SCORE.get(interest_label, 0.0)
        return self.INTEREST_WEIGHT * label_score + self.BUZZ_WEIGHT * buzz_score.external_buzz

    def _sort_by_priority(
        self,
        judgments: list[JudgmentResult],
        buzz_scores: dict[str, BuzzScore] | None = None,
    ) -> list[JudgmentResult]:
        """Composite Scoreに基づいてソートする.

        Args:
            judgments: 判定結果のリスト
            buzz_scores: URL→BuzzScoreのマッピング

        Returns:
            ソート済み判定結果のリスト
        """
        return sorted(
            judgments,
            key=lambda j: (
                -self._calculate_composite_score(
                    j.interest_label,
                    (buzz_scores or {}).get(j.url, _ZERO_BUZZ_SCORE),
                ),
                -j.judged_at.timestamp(),
                -j.confidence,
            ),
        )

    def _log_candidates(
        self,
        sorted_judgments: list[JudgmentResult],
        buzz_scores: dict[str, BuzzScore] | None = None,
    ) -> None:
        """候補ランキングをログ出力する."""
        for rank, j in enumerate(sorted_judgments, start=1):
            bs = (buzz_scores or {}).get(j.url, _ZERO_BUZZ_SCORE)
            composite = self._calculate_composite_score(j.interest_label, bs)
            logger.debug(
                "final_candidate",
                rank=rank,
                title=j.title,
                url=j.url,
                composite_score=round(composite, 1),
                interest_label=j.interest_label.value,
                buzz_label=j.buzz_label.value,
                external_buzz=round(bs.external_buzz, 1),
                total_score=round(bs.total_score, 1),
                social_proof_score=round(bs.social_proof_score, 1),
            )

    def _select_with_domain_control(
        self,
        sorted_judgments: list[JudgmentResult],
        buzz_scores: dict[str, BuzzScore] | None = None,
    ) -> list[JudgmentResult]:
        """ドメイン偏り制御しながら選定する.

        Args:
            sorted_judgments: ソート済み判定結果のリスト
            buzz_scores: URL→BuzzScoreのマッピング

        Returns:
            選定された判定結果のリスト（最大max_articles件）
        """
        selected: list[JudgmentResult] = []
        domain_counts: Counter[str] = Counter()

        for judgment in sorted_judgments:
            # 最大件数に達したら終了
            if len(selected) >= self._max_articles:
                break

            # ドメイン取得
            domain = urlparse(judgment.url).netloc

            # 同一ドメインの件数チェック（0 = 制限なし）
            if self._max_per_domain > 0 and domain_counts[domain] >= self._max_per_domain:
                logger.debug(
                    "domain_limit_reached",
                    url=judgment.url,
                    domain=domain,
                    count=domain_counts[domain],
                )
                continue

            # 選定に追加
            bs = (buzz_scores or {}).get(judgment.url, _ZERO_BUZZ_SCORE)
            composite = self._calculate_composite_score(judgment.interest_label, bs)
            selected.append(judgment)
            domain_counts[domain] += 1

            logger.debug(
                "article_selected",
                rank=len(selected),
                title=judgment.title,
                url=judgment.url,
                composite_score=round(composite, 1),
                interest_label=judgment.interest_label.value,
                buzz_label=judgment.buzz_label.value,
                external_buzz=round(bs.external_buzz, 1),
                total_score=round(bs.total_score, 1),
                social_proof_score=round(bs.social_proof_score, 1),
            )

        return selected
