"""JudgmentResultモデルのユニットテスト."""

from datetime import datetime, timezone

import pytest

from src.models.judgment import BuzzLabel, InterestLabel, JudgmentResult


def test_judgment_result_includes_published_at() -> None:
    """JudgmentResultにpublished_atフィールドが含まれることを検証."""
    # Arrange
    published_at = datetime(2026, 2, 13, 12, 0, 0, tzinfo=timezone.utc)
    judged_at = datetime(2026, 2, 15, 10, 0, 0, tzinfo=timezone.utc)

    # Act
    judgment = JudgmentResult(
        url="https://example.com/article",
        title="Test Article",
        description="This is a test article",
        interest_label=InterestLabel.ACT_NOW,
        buzz_label=BuzzLabel.HIGH,
        confidence=0.9,
        reason="Test reason",
        model_id="test-model",
        judged_at=judged_at,
        tags=["Python", "Testing"],
        published_at=published_at,
    )

    # Assert
    assert judgment.published_at == published_at
    assert judgment.url == "https://example.com/article"
    assert judgment.title == "Test Article"
