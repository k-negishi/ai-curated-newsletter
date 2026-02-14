"""InterestMasterの統合テスト."""

import pytest
from pathlib import Path
from unittest.mock import MagicMock

from src.repositories.interest_master import InterestMaster
from src.models.interest_profile import InterestProfile
from src.models.article import Article
from src.services.llm_judge import LlmJudge


def test_load_real_interests_yaml() -> None:
    """実際のconfig/interests.yamlを読み込めることを確認."""
    # Arrange
    config_path = Path(__file__).parent.parent.parent / "config" / "interests.yaml"
    master = InterestMaster(config_path)

    # Act
    profile = master.get_profile()

    # Assert
    assert isinstance(profile, InterestProfile)
    assert profile.summary  # サマリが空でないこと
    assert len(profile.high_interest) > 0  # 高関心トピックが存在すること
    assert "act_now" in profile.criteria
    assert "think" in profile.criteria
    assert "fyi" in profile.criteria
    assert "ignore" in profile.criteria

    # 各criteriaが正しく読み込まれていることを確認
    assert profile.criteria["act_now"].label == "ACT_NOW"
    assert profile.criteria["think"].label == "THINK"
    assert profile.criteria["fyi"].label == "FYI"
    assert profile.criteria["ignore"].label == "IGNORE"


def test_interest_master_to_llm_judge_integration() -> None:
    """InterestMaster → LlmJudge のDI連携が動作することを確認."""
    # Arrange
    config_path = Path(__file__).parent.parent.parent / "config" / "interests.yaml"
    interest_master = InterestMaster(config_path)
    interest_profile = interest_master.get_profile()

    mock_bedrock = MagicMock()
    llm_judge = LlmJudge(
        bedrock_client=mock_bedrock,
        cache_repository=None,
        interest_profile=interest_profile,
        model_id="test-model",
    )

    from datetime import datetime, timezone

    sample_article = Article(
        url="https://example.com/test",
        title="統合テスト記事",
        description="統合テストの説明",
        source_name="テストソース",
        published_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        normalized_url="https://example.com/test",
        collected_at=datetime(2024, 1, 1, 13, 0, 0, tzinfo=timezone.utc),
    )

    # Act
    prompt = llm_judge._build_prompt(sample_article)

    # Assert - 実際のYAMLから読み込んだプロファイル情報がプロンプトに含まれることを確認
    assert len(prompt) > 0
    assert "# 関心プロファイル" in prompt
    assert "# 記事情報" in prompt
    assert "# 判定基準" in prompt

    # プロファイルの内容が動的に生成されていることを確認
    # （具体的な内容はinterests.yamlの内容に依存するため、存在確認のみ）
    profile_text = interest_profile.format_for_prompt()
    assert profile_text in prompt

    criteria_text = interest_profile.format_criteria_for_prompt()
    assert criteria_text in prompt


def test_interest_profile_format_output() -> None:
    """InterestProfileの整形出力が正しいことを確認."""
    # Arrange
    config_path = Path(__file__).parent.parent.parent / "config" / "interests.yaml"
    interest_master = InterestMaster(config_path)
    interest_profile = interest_master.get_profile()

    # Act
    profile_text = interest_profile.format_for_prompt()
    criteria_text = interest_profile.format_criteria_for_prompt()

    # Assert - プロファイル整形出力の検証
    assert len(profile_text) > 0
    if interest_profile.max_interest:
        assert "**最高関心を持つトピック**:" in profile_text
    if interest_profile.high_interest:
        assert "**強い関心を持つトピック**:" in profile_text
    if interest_profile.medium_interest:
        assert "**中程度の関心を持つトピック**:" in profile_text
    if interest_profile.low_interest:
        assert "**低関心のトピック**:" in profile_text
    if interest_profile.ignore_interest:
        assert "**関心外のトピック**:" in profile_text

    # Assert - 判定基準整形出力の検証
    assert len(criteria_text) > 0
    assert "ACT_NOW" in criteria_text
    assert "THINK" in criteria_text
    assert "FYI" in criteria_text
    assert "IGNORE" in criteria_text
