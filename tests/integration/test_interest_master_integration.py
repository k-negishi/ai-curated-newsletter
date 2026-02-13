"""InterestMaster 統合テスト."""

from datetime import datetime
from unittest.mock import MagicMock

from src.models.article import Article
from src.repositories.interest_master import InterestMaster
from src.services.llm_judge import LlmJudge


def test_load_real_interests_yaml():
    """実際のconfig/interests.yamlを読み込めること."""
    # Arrange
    master = InterestMaster("config/interests.yaml")

    # Act
    profile = master.get_profile()

    # Assert
    assert profile is not None
    assert profile.summary != ""
    assert len(profile.high_interest) > 0
    assert len(profile.medium_interest) > 0
    assert len(profile.low_priority) > 0
    assert "act_now" in profile.criteria
    assert "think" in profile.criteria
    assert "fyi" in profile.criteria
    assert "ignore" in profile.criteria
    assert profile.criteria["act_now"].label == "ACT_NOW"
    assert profile.criteria["think"].label == "THINK"
    assert profile.criteria["fyi"].label == "FYI"
    assert profile.criteria["ignore"].label == "IGNORE"


def test_interest_master_to_llm_judge_integration():
    """InterestMaster → LlmJudge のDI連携が動作すること."""
    # Arrange
    interest_master = InterestMaster("config/interests.yaml")
    interest_profile = interest_master.get_profile()
    bedrock_client = MagicMock()

    llm_judge = LlmJudge(
        bedrock_client=bedrock_client,
        cache_repository=None,
        interest_profile=interest_profile,
        model_id="test-model",
    )

    sample_article = Article(
        url="https://example.com/test",
        title="Test Article",
        published_at=datetime(2024, 1, 1, 0, 0, 0),
        source_name="Test Source",
        description="Test description",
        normalized_url="https://example.com/test",
        collected_at=datetime(2024, 1, 1, 0, 0, 0),
    )

    # Act
    prompt = llm_judge._build_prompt(sample_article)

    # Assert
    # プロンプト生成が正常に動作すること
    assert prompt is not None
    assert len(prompt) > 0
    # 関心プロファイルの内容が含まれていること
    assert "プリンシパルエンジニア" in prompt or "Test Article" in prompt
    # 判定基準が含まれていること
    assert "ACT_NOW" in prompt
    assert "THINK" in prompt
    assert "FYI" in prompt
    assert "IGNORE" in prompt
    # 記事情報が含まれていること
    assert "Test Article" in prompt
    assert "https://example.com/test" in prompt
