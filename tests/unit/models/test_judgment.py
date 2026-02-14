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
        summary="Test summary",
        model_id="test-model",
        judged_at=judged_at,
        tags=["Python", "Testing"],
        published_at=published_at,
    )

    # Assert
    assert judgment.published_at == published_at
    assert judgment.url == "https://example.com/article"
    assert judgment.title == "Test Article"


def test_judgment_result_with_summary() -> None:
    """JudgmentResultにsummaryフィールドが正しく設定されることを検証."""
    # Arrange
    published_at = datetime(2026, 2, 15, 9, 0, 0, tzinfo=timezone.utc)
    judged_at = datetime(2026, 2, 15, 10, 0, 0, tzinfo=timezone.utc)
    test_summary = "PostgreSQLのインデックス戦略に関する実践的な記事。B-treeとGiSTインデックスの使い分け、パフォーマンスチューニング、実運用での注意点を解説。"

    # Act
    judgment = JudgmentResult(
        url="https://example.com/postgresql-index",
        title="PostgreSQL Index Strategies",
        description="This article discusses PostgreSQL indexing strategies...",
        interest_label=InterestLabel.THINK,
        buzz_label=BuzzLabel.MID,
        confidence=0.85,
        summary=test_summary,
        model_id="anthropic.claude-haiku-4-5-20251001-v1:0",
        judged_at=judged_at,
        tags=["PostgreSQL", "Performance"],
        published_at=published_at,
    )

    # Assert
    assert judgment.summary == test_summary
    assert len(judgment.summary) <= 300  # 最大300文字の制限を確認
    assert judgment.description != judgment.summary  # descriptionとsummaryは異なることを確認
