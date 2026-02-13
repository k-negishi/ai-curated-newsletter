"""InterestProfile モデルのユニットテスト."""

import pytest

from src.models.interest_profile import InterestProfile, JudgmentCriterion


def test_interest_profile_initialization():
    """各フィールドが正しく初期化されること."""
    # Arrange
    summary = "Test summary"
    high_interest = ["AI/ML", "Cloud"]
    medium_interest = ["Frontend"]
    low_priority = ["Tutorials"]
    criteria = {
        "act_now": JudgmentCriterion(
            label="ACT_NOW", description="Urgent", examples=["Security alerts"]
        )
    }

    # Act
    profile = InterestProfile(
        summary=summary,
        high_interest=high_interest,
        medium_interest=medium_interest,
        low_priority=low_priority,
        criteria=criteria,
    )

    # Assert
    assert profile.summary == summary
    assert profile.high_interest == high_interest
    assert profile.medium_interest == medium_interest
    assert profile.low_priority == low_priority
    assert profile.criteria == criteria


def test_format_for_prompt():
    """summaryと各リストが整形されること."""
    # Arrange
    profile = InterestProfile(
        summary="Test summary",
        high_interest=["AI/ML", "Cloud"],
        medium_interest=["Frontend"],
        low_priority=["Tutorials"],
        criteria={},
    )

    # Act
    result = profile.format_for_prompt()

    # Assert
    assert "Test summary" in result
    assert "**強い関心を持つトピック**:" in result
    assert "- AI/ML" in result
    assert "- Cloud" in result
    assert "**中程度の関心を持つトピック**:" in result
    assert "- Frontend" in result
    assert "**低優先度のトピック**:" in result
    assert "- Tutorials" in result


def test_format_for_prompt_with_empty_lists():
    """空リストの場合に適切にスキップされること."""
    # Arrange
    profile = InterestProfile(
        summary="Test summary",
        high_interest=[],
        medium_interest=["Frontend"],
        low_priority=[],
        criteria={},
    )

    # Act
    result = profile.format_for_prompt()

    # Assert
    assert "Test summary" in result
    assert "**強い関心を持つトピック**:" not in result  # 空リストはスキップ
    assert "**中程度の関心を持つトピック**:" in result
    assert "- Frontend" in result
    assert "**低優先度のトピック**:" not in result  # 空リストはスキップ


def test_format_criteria_for_prompt():
    """全てのcriteriaが整形され、examplesが含まれること."""
    # Arrange
    criteria = {
        "act_now": JudgmentCriterion(
            label="ACT_NOW",
            description="Urgent articles",
            examples=["Security alerts", "Breaking changes"],
        ),
        "think": JudgmentCriterion(
            label="THINK",
            description="Architecture decisions",
            examples=["Design patterns"],
        ),
        "fyi": JudgmentCriterion(
            label="FYI", description="General info", examples=["Tutorials"]
        ),
        "ignore": JudgmentCriterion(label="IGNORE", description="Not interested", examples=[]),
    }
    profile = InterestProfile(
        summary="Test", high_interest=[], medium_interest=[], low_priority=[], criteria=criteria
    )

    # Act
    result = profile.format_criteria_for_prompt()

    # Assert
    assert "**ACT_NOW**: Urgent articles" in result
    assert "Security alerts" in result
    assert "Breaking changes" in result
    assert "**THINK**: Architecture decisions" in result
    assert "Design patterns" in result
    assert "**FYI**: General info" in result
    assert "Tutorials" in result
    assert "**IGNORE**: Not interested" in result
