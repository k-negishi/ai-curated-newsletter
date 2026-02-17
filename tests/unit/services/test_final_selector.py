"""FinalSelectorサービスのユニットテスト."""

from datetime import datetime, timezone

import pytest

from src.models.buzz_score import BuzzScore
from src.models.judgment import BuzzLabel, InterestLabel, JudgmentResult
from src.services.final_selector import FinalSelector


def _make_buzz_score(url: str, total_score: float) -> BuzzScore:
    """テスト用のBuzzScoreを生成するヘルパー."""
    return BuzzScore(
        url=url,
        recency_score=0.0,
        consensus_score=0.0,
        social_proof_score=0.0,
        interest_score=0.0,
        authority_score=0.0,
        source_count=0,
        social_proof_count=0,
        total_score=total_score,
    )


class TestFinalSelector:
    """FinalSelectorクラスのテスト."""

    @pytest.fixture
    def final_selector(self) -> FinalSelector:
        """FinalSelectorインスタンスを返す."""
        return FinalSelector(max_articles=15, max_per_domain=4)

    def create_judgment(
        self,
        url: str,
        interest_label: InterestLabel,
        buzz_label: BuzzLabel,
        confidence: float = 0.9,
        title: str = "Test Article",
        description: str = "Test description",
    ) -> JudgmentResult:
        """JudgmentResultを生成するヘルパー."""
        return JudgmentResult(
            url=url,
            title=title,
            description=description,
            interest_label=interest_label,
            buzz_label=buzz_label,
            confidence=confidence,
            summary="Test reason",
            model_id="test-model",
            judged_at=datetime.now(timezone.utc),
            published_at=datetime(2026, 2, 13, 12, 0, 0, tzinfo=timezone.utc),
            tags=[],
        )

    def test_filters_ignore_label(self, final_selector: FinalSelector) -> None:
        """IGNOREラベルの記事が除外されることを確認."""
        judgments = [
            self.create_judgment(
                "https://example.com/1", InterestLabel.ACT_NOW, BuzzLabel.HIGH
            ),
            self.create_judgment("https://example.com/2", InterestLabel.IGNORE, BuzzLabel.HIGH),
        ]

        result = final_selector.select(judgments)

        assert len(result.selected_articles) == 1
        assert result.selected_articles[0].url == "https://example.com/1"

    def test_prioritizes_by_interest_label(self, final_selector: FinalSelector) -> None:
        """Interest Labelによる優先順位付けが正しいことを確認."""
        judgments = [
            self.create_judgment("https://example.com/fyi", InterestLabel.FYI, BuzzLabel.HIGH),
            self.create_judgment(
                "https://example.com/act_now", InterestLabel.ACT_NOW, BuzzLabel.LOW
            ),
            self.create_judgment("https://example.com/think", InterestLabel.THINK, BuzzLabel.MID),
        ]

        result = final_selector.select(judgments)

        # ACT_NOW > THINK > FYI の順
        assert result.selected_articles[0].url == "https://example.com/act_now"
        assert result.selected_articles[1].url == "https://example.com/think"
        assert result.selected_articles[2].url == "https://example.com/fyi"

    def test_respects_max_articles(self, final_selector: FinalSelector) -> None:
        """最大件数が守られることを確認."""
        # 異なるドメインから20件の記事を生成（ドメイン偏り制御を回避）
        judgments = [
            self.create_judgment(
                f"https://example{i}.com/article", InterestLabel.ACT_NOW, BuzzLabel.HIGH
            )
            for i in range(20)
        ]

        result = final_selector.select(judgments)

        # 最大15件に制限される
        assert len(result.selected_articles) == 15

    def test_respects_max_per_domain(self, final_selector: FinalSelector) -> None:
        """同一ドメインの最大件数が守られることを確認."""
        # 同一ドメインから10件の記事
        judgments = [
            self.create_judgment(
                f"https://example.com/article{i}", InterestLabel.ACT_NOW, BuzzLabel.HIGH
            )
            for i in range(10)
        ]

        result = final_selector.select(judgments)

        # 同一ドメインは最大4件
        assert len(result.selected_articles) == 4

    def test_handles_multiple_domains(self, final_selector: FinalSelector) -> None:
        """複数ドメインから適切に選定されることを確認."""
        judgments = [
            # example.com から 5件
            *[
                self.create_judgment(
                    f"https://example.com/article{i}", InterestLabel.ACT_NOW, BuzzLabel.HIGH
                )
                for i in range(5)
            ],
            # another.com から 5件
            *[
                self.create_judgment(
                    f"https://another.com/article{i}", InterestLabel.ACT_NOW, BuzzLabel.HIGH
                )
                for i in range(5)
            ],
        ]

        result = final_selector.select(judgments)

        # 各ドメイン最大4件 → 合計8件
        assert len(result.selected_articles) == 8

        # ドメイン別にカウント
        example_count = sum(1 for a in result.selected_articles if "example.com" in a.url)
        another_count = sum(1 for a in result.selected_articles if "another.com" in a.url)

        assert example_count == 4
        assert another_count == 4

    def test_empty_input(self, final_selector: FinalSelector) -> None:
        """空の入力を処理できることを確認."""
        result = final_selector.select([])
        assert len(result.selected_articles) == 0

    def test_no_domain_limit_when_max_per_domain_is_zero(self) -> None:
        """max_per_domain=0 の場合、ドメイン制限なしで全記事が選定されることを確認."""
        selector = FinalSelector(max_articles=15, max_per_domain=0)
        # 同一ドメインから10件の記事
        judgments = [
            self.create_judgment(
                f"https://example.com/article{i}", InterestLabel.ACT_NOW, BuzzLabel.HIGH
            )
            for i in range(10)
        ]

        result = selector.select(judgments)

        # ドメイン制限なし → 全10件が選定される
        assert len(result.selected_articles) == 10

    def test_default_constructor_has_no_domain_limit(self) -> None:
        """デフォルトコンストラクタではドメイン制限なしであることを確認."""
        selector = FinalSelector()
        # 同一ドメインから10件の記事
        judgments = [
            self.create_judgment(
                f"https://example.com/article{i}", InterestLabel.ACT_NOW, BuzzLabel.HIGH
            )
            for i in range(10)
        ]

        result = selector.select(judgments)

        # デフォルトはドメイン制限なし → 全10件が選定される
        assert len(result.selected_articles) == 10

    def test_default_max_articles_is_15(self) -> None:
        """デフォルト最大件数が15件であることを確認."""
        selector = FinalSelector()
        judgments = [
            self.create_judgment(
                f"https://default{i}.com/article", InterestLabel.ACT_NOW, BuzzLabel.HIGH
            )
            for i in range(20)
        ]

        result = selector.select(judgments)

        assert len(result.selected_articles) == 15

    def test_select_without_buzz_scores(self, final_selector: FinalSelector) -> None:
        """buzz_scoresがNoneでも正常に動作することを確認."""
        judgments = [
            self.create_judgment(
                "https://example.com/1", InterestLabel.ACT_NOW, BuzzLabel.LOW
            ),
            self.create_judgment(
                "https://example2.com/2", InterestLabel.THINK, BuzzLabel.LOW
            ),
        ]

        result = final_selector.select(judgments)  # buzz_scores=None

        assert len(result.selected_articles) == 2
        # Interest Label順でソートされる
        assert result.selected_articles[0].url == "https://example.com/1"
        assert result.selected_articles[1].url == "https://example2.com/2"

    def test_sorts_by_buzz_score_within_same_interest(
        self, final_selector: FinalSelector
    ) -> None:
        """同一Interest Label内でbuzz_scoreの高い記事が優先されることを確認."""
        judgments = [
            self.create_judgment(
                "https://example1.com/low", InterestLabel.ACT_NOW, BuzzLabel.LOW
            ),
            self.create_judgment(
                "https://example2.com/high", InterestLabel.ACT_NOW, BuzzLabel.LOW
            ),
            self.create_judgment(
                "https://example3.com/mid", InterestLabel.ACT_NOW, BuzzLabel.LOW
            ),
        ]

        buzz_scores = {
            "https://example1.com/low": _make_buzz_score("https://example1.com/low", 20.0),
            "https://example2.com/high": _make_buzz_score("https://example2.com/high", 80.0),
            "https://example3.com/mid": _make_buzz_score("https://example3.com/mid", 50.0),
        }

        result = final_selector.select(judgments, buzz_scores=buzz_scores)

        # buzz_scoreの高い順: high(80) > mid(50) > low(20)
        assert result.selected_articles[0].url == "https://example2.com/high"
        assert result.selected_articles[1].url == "https://example3.com/mid"
        assert result.selected_articles[2].url == "https://example1.com/low"

    def test_missing_buzz_score_falls_back_to_zero(
        self, final_selector: FinalSelector
    ) -> None:
        """buzz_scoresに存在しないURLは0.0として扱われることを確認."""
        judgments = [
            self.create_judgment(
                "https://example1.com/no-score", InterestLabel.ACT_NOW, BuzzLabel.LOW
            ),
            self.create_judgment(
                "https://example2.com/has-score", InterestLabel.ACT_NOW, BuzzLabel.LOW
            ),
        ]

        buzz_scores = {
            "https://example2.com/has-score": _make_buzz_score(
                "https://example2.com/has-score", 50.0
            ),
            # example1.com/no-score はbuzz_scoresに存在しない → 0.0扱い
        }

        result = final_selector.select(judgments, buzz_scores=buzz_scores)

        # スコアがある方が優先される
        assert result.selected_articles[0].url == "https://example2.com/has-score"
        assert result.selected_articles[1].url == "https://example1.com/no-score"
