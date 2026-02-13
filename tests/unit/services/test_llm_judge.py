"""LlmJudge サービスのユニットテスト."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.models.article import Article
from src.models.interest_profile import InterestProfile, JudgmentCriterion
from src.services.llm_judge import LlmJudge


@pytest.fixture
def mock_interest_profile():
    """テスト用の関心プロファイルモック."""
    return InterestProfile(
        summary="Test engineer profile",
        high_interest=["AI/ML", "Cloud Infrastructure"],
        medium_interest=["Frontend"],
        low_priority=["Tutorials"],
        criteria={
            "act_now": JudgmentCriterion(
                label="ACT_NOW",
                description="Urgent articles",
                examples=["Security vulnerabilities"],
            ),
            "think": JudgmentCriterion(
                label="THINK", description="Design decisions", examples=["Architecture patterns"]
            ),
            "fyi": JudgmentCriterion(
                label="FYI", description="General info", examples=["New tools"]
            ),
            "ignore": JudgmentCriterion(
                label="IGNORE", description="Not interested", examples=["Beginner tutorials"]
            ),
        },
    )


@pytest.fixture
def sample_article():
    """テスト用の記事."""
    return Article(
        url="https://example.com/article",
        title="Test Article",
        published_at=datetime(2024, 1, 1, 0, 0, 0),
        source_name="Test Source",
        description="Test description",
        normalized_url="https://example.com/article",
        collected_at=datetime(2024, 1, 1, 0, 0, 0),
    )


def test_build_prompt_with_interest_profile(mock_interest_profile, sample_article):
    """プロンプトにInterestProfileの内容が含まれること."""
    # Arrange
    bedrock_client = MagicMock()
    llm_judge = LlmJudge(
        bedrock_client=bedrock_client,
        cache_repository=None,
        interest_profile=mock_interest_profile,
        model_id="test-model",
    )

    # Act
    prompt = llm_judge._build_prompt(sample_article)

    # Assert
    # InterestProfile.format_for_prompt()の出力が含まれること
    assert "Test engineer profile" in prompt
    assert "**強い関心を持つトピック**:" in prompt
    assert "- AI/ML" in prompt
    assert "- Cloud Infrastructure" in prompt
    assert "**中程度の関心を持つトピック**:" in prompt
    assert "- Frontend" in prompt
    assert "**低優先度のトピック**:" in prompt
    assert "- Tutorials" in prompt

    # InterestProfile.format_criteria_for_prompt()の出力が含まれること
    assert "**ACT_NOW**: Urgent articles" in prompt
    assert "Security vulnerabilities" in prompt
    assert "**THINK**: Design decisions" in prompt
    assert "Architecture patterns" in prompt
    assert "**FYI**: General info" in prompt
    assert "New tools" in prompt
    assert "**IGNORE**: Not interested" in prompt
    assert "Beginner tutorials" in prompt

    # 記事情報が含まれること
    assert "Test Article" in prompt
    assert "https://example.com/article" in prompt
    assert "Test description" in prompt
    assert "Test Source" in prompt

    # 出力形式の指定が含まれること
    assert "JSON形式" in prompt
    assert '"interest_label"' in prompt
    assert '"buzz_label"' in prompt
    assert '"confidence"' in prompt
    assert '"reason"' in prompt


def test_llm_judge_initialization_with_interest_profile(mock_interest_profile):
    """InterestProfileを受け取って初期化できること."""
    # Arrange
    bedrock_client = MagicMock()

    # Act
    llm_judge = LlmJudge(
        bedrock_client=bedrock_client,
        cache_repository=None,
        interest_profile=mock_interest_profile,
        model_id="test-model",
    )

    # Assert
    assert llm_judge._interest_profile == mock_interest_profile
    assert llm_judge._model_id == "test-model"
