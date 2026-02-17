"""BuzzScoreモデルのユニットテスト."""

import pytest

from src.models.buzz_score import BuzzScore
from src.models.judgment import BuzzLabel


class TestBuzzScore:
    """BuzzScoreクラスのテスト."""

    def test_buzz_score_instance_creation(self):
        """BuzzScoreインスタンスが正しく生成されることを確認."""
        buzz_score = BuzzScore(
            url="https://example.com/article",
            recency_score=100.0,
            consensus_score=60.0,
            social_proof_score=50.0,
            interest_score=80.0,
            authority_score=100.0,
            source_count=3,
            social_proof_count=25,
            total_score=77.0,
        )

        assert buzz_score.url == "https://example.com/article"
        assert buzz_score.recency_score == 100.0
        assert buzz_score.consensus_score == 60.0
        assert buzz_score.social_proof_score == 50.0
        assert buzz_score.interest_score == 80.0
        assert buzz_score.authority_score == 100.0
        assert buzz_score.source_count == 3
        assert buzz_score.social_proof_count == 25
        assert buzz_score.total_score == 77.0

    def test_buzz_score_field_types(self):
        """BuzzScoreの各フィールドの型が正しいことを確認."""
        buzz_score = BuzzScore(
            url="https://example.com/article",
            recency_score=90.5,
            consensus_score=40.0,
            social_proof_score=20.0,
            interest_score=60.0,
            authority_score=50.0,
            source_count=2,
            social_proof_count=5,
            total_score=52.1,
        )

        assert isinstance(buzz_score.url, str)
        assert isinstance(buzz_score.recency_score, float)
        assert isinstance(buzz_score.consensus_score, float)
        assert isinstance(buzz_score.social_proof_score, float)
        assert isinstance(buzz_score.interest_score, float)
        assert isinstance(buzz_score.authority_score, float)
        assert isinstance(buzz_score.source_count, int)
        assert isinstance(buzz_score.social_proof_count, int)
        assert isinstance(buzz_score.total_score, float)

    def test_buzz_score_zero_values(self):
        """BuzzScoreが0値でも正しく動作することを確認."""
        buzz_score = BuzzScore(
            url="https://example.com/old-article",
            recency_score=0.0,
            consensus_score=0.0,
            social_proof_score=0.0,
            interest_score=40.0,  # デフォルト値
            authority_score=0.0,
            source_count=1,
            social_proof_count=0,
            total_score=10.0,  # interest_score * 0.25
        )

        assert buzz_score.recency_score == 0.0
        assert buzz_score.consensus_score == 0.0
        assert buzz_score.social_proof_score == 0.0
        assert buzz_score.interest_score == 40.0
        assert buzz_score.authority_score == 0.0
        assert buzz_score.source_count == 1
        assert buzz_score.social_proof_count == 0
        assert buzz_score.total_score == 10.0

    def test_buzz_score_max_values(self):
        """BuzzScoreが最大値でも正しく動作することを確認."""
        buzz_score = BuzzScore(
            url="https://example.com/hot-article",
            recency_score=100.0,
            consensus_score=100.0,
            social_proof_score=100.0,
            interest_score=100.0,
            authority_score=100.0,
            source_count=5,
            social_proof_count=150,
            total_score=100.0,
        )

        assert buzz_score.recency_score == 100.0
        assert buzz_score.consensus_score == 100.0
        assert buzz_score.social_proof_score == 100.0
        assert buzz_score.interest_score == 100.0
        assert buzz_score.authority_score == 100.0
        assert buzz_score.source_count == 5
        assert buzz_score.social_proof_count == 150
        assert buzz_score.total_score == 100.0


class TestToBuzzLabel:
    """to_buzz_label()メソッドのテスト."""

    def _make_buzz_score(self, total_score: float) -> BuzzScore:
        """テスト用BuzzScoreを生成するヘルパー."""
        return BuzzScore(
            url="https://example.com/article",
            recency_score=0.0,
            consensus_score=0.0,
            social_proof_score=0.0,
            interest_score=0.0,
            authority_score=0.0,
            source_count=1,
            social_proof_count=0,
            total_score=total_score,
        )

    def test_to_buzz_label_high(self):
        """HIGH: total_score=80 の場合HIGHを返す."""
        buzz_score = self._make_buzz_score(80)
        assert buzz_score.to_buzz_label() == BuzzLabel.HIGH

    def test_to_buzz_label_high_boundary(self):
        """HIGH境界値: total_score=70.0 の場合HIGHを返す."""
        buzz_score = self._make_buzz_score(70.0)
        assert buzz_score.to_buzz_label() == BuzzLabel.HIGH

    def test_to_buzz_label_mid(self):
        """MID: total_score=50 の場合MIDを返す."""
        buzz_score = self._make_buzz_score(50)
        assert buzz_score.to_buzz_label() == BuzzLabel.MID

    def test_to_buzz_label_mid_boundary(self):
        """MID境界値: total_score=40.0 の場合MIDを返す."""
        buzz_score = self._make_buzz_score(40.0)
        assert buzz_score.to_buzz_label() == BuzzLabel.MID

    def test_to_buzz_label_low(self):
        """LOW: total_score=20 の場合LOWを返す."""
        buzz_score = self._make_buzz_score(20)
        assert buzz_score.to_buzz_label() == BuzzLabel.LOW

    def test_to_buzz_label_low_boundary(self):
        """LOW境界値: total_score=39.9 の場合LOWを返す."""
        buzz_score = self._make_buzz_score(39.9)
        assert buzz_score.to_buzz_label() == BuzzLabel.LOW

    def test_to_buzz_label_edge_zero(self):
        """エッジケース: total_score=0 の場合LOWを返す."""
        buzz_score = self._make_buzz_score(0)
        assert buzz_score.to_buzz_label() == BuzzLabel.LOW

    def test_to_buzz_label_edge_max(self):
        """エッジケース: total_score=100 の場合HIGHを返す."""
        buzz_score = self._make_buzz_score(100)
        assert buzz_score.to_buzz_label() == BuzzLabel.HIGH
