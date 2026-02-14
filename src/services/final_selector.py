"""最終選定サービスモジュール."""

from collections import Counter
from dataclasses import dataclass
from urllib.parse import urlparse

from src.models.judgment import InterestLabel, JudgmentResult
from src.shared.logging.logger import get_logger

logger = get_logger(__name__)


@dataclass
class FinalSelectionResult:
    """最終選定結果.

    Attributes:
        selected_articles: 最終選定された記事のリスト（最大15件）
    """

    selected_articles: list[JudgmentResult]


class FinalSelector:
    """最終選定サービス.

    Interest Labelによる優先順位付けとドメイン偏り制御を行い、
    最終的に通知する記事を選定する.

    Attributes:
        _max_articles: 最大選定件数
        _max_per_domain: 同一ドメインの最大件数
    """

    def __init__(self, max_articles: int = 15, max_per_domain: int = 4) -> None:
        """最終選定サービスを初期化する.

        Args:
            max_articles: 最大選定件数（デフォルト: 15）
            max_per_domain: 同一ドメインの最大件数（デフォルト: 4）
        """
        self._max_articles = max_articles
        self._max_per_domain = max_per_domain

    def select(self, judgments: list[JudgmentResult]) -> FinalSelectionResult:
        """最終選定を行う.

        優先順位:
        1. Interest Label: ACT_NOW > THINK > FYI > IGNORE（IGNOREは除外）
        2. Buzz Label: HIGH > MID > LOW
        3. 鮮度: judged_at降順
        4. Confidence: 信頼度降順

        ドメイン偏り制御:
        - 同一ドメインは最大4件まで

        Args:
            judgments: LLM判定結果のリスト

        Returns:
            最終選定結果（最大15件）
        """
        logger.info(
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

        # ステップ2: 優先順位付けでソート
        sorted_judgments = self._sort_by_priority(non_ignore_judgments)

        # ステップ3: ドメイン偏り制御しながら選定
        selected = self._select_with_domain_control(sorted_judgments)

        logger.info(
            "final_selection_complete",
            input_count=len(judgments),
            output_count=len(selected),
        )

        return FinalSelectionResult(selected_articles=selected)

    def _sort_by_priority(self, judgments: list[JudgmentResult]) -> list[JudgmentResult]:
        """優先順位に基づいてソートする.

        Args:
            judgments: 判定結果のリスト

        Returns:
            ソート済み判定結果のリスト
        """
        # Interest Labelの優先度マップ
        interest_priority = {
            InterestLabel.ACT_NOW: 0,
            InterestLabel.THINK: 1,
            InterestLabel.FYI: 2,
            InterestLabel.IGNORE: 3,  # 既に除外されているはずだが念のため
        }

        # Buzz Labelの優先度マップ
        from src.models.judgment import BuzzLabel

        buzz_priority = {
            BuzzLabel.HIGH: 0,
            BuzzLabel.MID: 1,
            BuzzLabel.LOW: 2,
        }

        return sorted(
            judgments,
            key=lambda j: (
                interest_priority.get(j.interest_label, 999),
                buzz_priority.get(j.buzz_label, 999),
                -j.judged_at.timestamp(),  # 鮮度降順
                -j.confidence,  # 信頼度降順
            ),
        )

    def _select_with_domain_control(
        self, sorted_judgments: list[JudgmentResult]
    ) -> list[JudgmentResult]:
        """ドメイン偏り制御しながら選定する.

        Args:
            sorted_judgments: ソート済み判定結果のリスト

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

            # 同一ドメインの件数チェック
            if domain_counts[domain] >= self._max_per_domain:
                logger.debug(
                    "domain_limit_reached",
                    url=judgment.url,
                    domain=domain,
                    count=domain_counts[domain],
                )
                continue

            # 選定に追加
            selected.append(judgment)
            domain_counts[domain] += 1

            logger.debug(
                "article_selected",
                url=judgment.url,
                interest_label=judgment.interest_label.value,
                buzz_label=judgment.buzz_label.value,
                domain=domain,
                domain_count=domain_counts[domain],
            )

        return selected
