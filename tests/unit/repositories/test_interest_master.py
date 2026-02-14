"""InterestMasterリポジトリのユニットテスト."""

import pytest
from pathlib import Path
import tempfile
import yaml

from src.repositories.interest_master import InterestMaster
from src.models.interest_profile import InterestProfile


@pytest.fixture
def temp_interests_yaml():
    """一時的なinterests.yamlファイルを作成するフィクスチャ（5段階版）."""
    yaml_content = {
        "profile": {
            "summary": "テストサマリ",
            "max_interest": ["AI Coding"],
            "high_interest": ["AI/ML", "クラウド"],
            "medium_interest": ["データベース"],
            "low_interest": ["チュートリアル"],
            "ignore_interest": ["Ruby"],
        },
        "criteria": {
            "act_now": {
                "label": "ACT_NOW",
                "description": "今すぐ読むべき",
                "examples": ["例1", "例2"],
            },
            "think": {"label": "THINK", "description": "設計判断に役立つ", "examples": []},
        },
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(yaml_content, f, allow_unicode=True)
        temp_path = f.name

    yield temp_path

    # クリーンアップ
    Path(temp_path).unlink()


def test_get_profile_success(temp_interests_yaml: str) -> None:
    """正常にInterestProfileが取得できることを確認（5段階版）."""
    # Arrange
    master = InterestMaster(temp_interests_yaml)

    # Act
    profile = master.get_profile()

    # Assert
    assert isinstance(profile, InterestProfile)
    assert profile.summary == "テストサマリ"
    assert profile.max_interest == ["AI Coding"]
    assert profile.high_interest == ["AI/ML", "クラウド"]
    assert profile.medium_interest == ["データベース"]
    assert profile.low_interest == ["チュートリアル"]
    assert profile.ignore_interest == ["Ruby"]
    assert "act_now" in profile.criteria
    assert profile.criteria["act_now"].label == "ACT_NOW"
    assert profile.criteria["act_now"].description == "今すぐ読むべき"
    assert profile.criteria["act_now"].examples == ["例1", "例2"]
    assert "think" in profile.criteria


def test_get_profile_caching(temp_interests_yaml: str) -> None:
    """2回目の呼び出しでキャッシュが使われることを確認."""
    # Arrange
    master = InterestMaster(temp_interests_yaml)

    # Act
    profile1 = master.get_profile()
    profile2 = master.get_profile()

    # Assert - 同じインスタンスが返されること
    assert profile1 is profile2


def test_get_profile_file_not_found() -> None:
    """ファイルが存在しない場合にFileNotFoundErrorが発生することを確認."""
    # Arrange
    master = InterestMaster("/path/to/nonexistent/file.yaml")

    # Act & Assert
    with pytest.raises(FileNotFoundError) as exc_info:
        master.get_profile()

    assert "Interest config file not found" in str(exc_info.value)


def test_get_profile_invalid_yaml() -> None:
    """YAML解析エラーの場合にValueErrorが発生することを確認."""
    # Arrange - 不正なYAMLファイルを作成
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write("invalid: yaml: content: [")
        temp_path = f.name

    try:
        master = InterestMaster(temp_path)

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            master.get_profile()

        assert "Failed to parse interests.yaml" in str(exc_info.value)
    finally:
        # クリーンアップ
        Path(temp_path).unlink()


def test_get_profile_missing_profile_key() -> None:
    """'profile'キーがない場合にValueErrorが発生することを確認."""
    # Arrange - profileキーがないYAML
    yaml_content = {
        "criteria": {
            "act_now": {"label": "ACT_NOW", "description": "テスト", "examples": []}
        }
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(yaml_content, f)
        temp_path = f.name

    try:
        master = InterestMaster(temp_path)

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            master.get_profile()

        assert "Missing 'profile' key in interests.yaml" in str(exc_info.value)
    finally:
        # クリーンアップ
        Path(temp_path).unlink()


def test_get_profile_missing_criteria_key() -> None:
    """'criteria'キーがない場合にValueErrorが発生することを確認."""
    # Arrange - criteriaキーがないYAML
    yaml_content = {
        "profile": {
            "summary": "テスト",
            "max_interest": [],
            "high_interest": [],
            "medium_interest": [],
            "low_interest": [],
            "ignore_interest": [],
        }
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(yaml_content, f)
        temp_path = f.name

    try:
        master = InterestMaster(temp_path)

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            master.get_profile()

        assert "Missing 'criteria' key in interests.yaml" in str(exc_info.value)
    finally:
        # クリーンアップ
        Path(temp_path).unlink()
