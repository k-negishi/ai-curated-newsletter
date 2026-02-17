"""CandidateSelectorサービスのユニットテスト."""

from datetime import datetime, timezone

from src.models.article import Article
from src.models.buzz_score import BuzzScore
from src.services.candidate_selector import CandidateSelector


class TestCandidateSelector:
    """CandidateSelectorクラスのテスト."""

    def test_default_max_candidates_is_100(self) -> None:
        """デフォルトのmax_candidatesが100であることを確認."""
        selector = CandidateSelector()
        assert selector._max_candidates == 100
