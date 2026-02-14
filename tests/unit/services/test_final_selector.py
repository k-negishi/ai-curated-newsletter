"""FinalSelectorサービスのユニットテスト."""

from datetime import datetime, timezone

import pytest

from src.models.judgment import BuzzLabel, InterestLabel, JudgmentResult
from src.services.final_selector import FinalSelector


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
