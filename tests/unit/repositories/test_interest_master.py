"""InterestMaster リポジトリのユニットテスト."""

import tempfile
from pathlib import Path

import pytest
import yaml

from src.repositories.interest_master import InterestMaster


def test_get_profile_success():
    """正常にInterestProfileが返され、各フィールドが正しく読み込まれること."""
    # Arrange
    test_data = {
        "profile": {
            "summary": "Test summary",
            "high_interest": ["AI/ML", "Cloud"],
            "medium_interest": ["Frontend"],
            "low_priority": ["Tutorials"],
        },
        "criteria": {
            "act_now": {
                "label": "ACT_NOW",
                "description": "Urgent",
                "examples": ["Security alerts"],
            },
            "think": {"label": "THINK", "description": "Design", "examples": ["Patterns"]},
        },
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(test_data, f)
        temp_path = f.name

    try:
        master = InterestMaster(temp_path)

        # Act
        profile = master.get_profile()

        # Assert
        assert profile.summary == "Test summary"
        assert profile.high_interest == ["AI/ML", "Cloud"]
        assert profile.medium_interest == ["Frontend"]
        assert profile.low_priority == ["Tutorials"]
        assert "act_now" in profile.criteria
        assert profile.criteria["act_now"].label == "ACT_NOW"
        assert profile.criteria["act_now"].description == "Urgent"
        assert profile.criteria["act_now"].examples == ["Security alerts"]
        assert "think" in profile.criteria
    finally:
        Path(temp_path).unlink()


def test_get_profile_caching():
    """2回目の呼び出しでキャッシュが使われること（ファイル読み込みが1回のみ）."""
    # Arrange
    test_data = {
        "profile": {
            "summary": "Test",
            "high_interest": [],
            "medium_interest": [],
            "low_priority": [],
        },
        "criteria": {},
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(test_data, f)
        temp_path = f.name

    try:
        master = InterestMaster(temp_path)

        # Act
        profile1 = master.get_profile()
        profile2 = master.get_profile()

        # Assert
        assert profile1 is profile2  # 同じインスタンスが返されること
    finally:
        Path(temp_path).unlink()


def test_get_profile_file_not_found():
    """ファイルが存在しない場合にFileNotFoundErrorが発生すること."""
    # Arrange
    master = InterestMaster("/nonexistent/path/interests.yaml")

    # Act & Assert
    with pytest.raises(FileNotFoundError):
        master.get_profile()


def test_get_profile_invalid_yaml():
    """YAML解析エラーの場合にValueErrorが発生すること."""
    # Arrange
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write("invalid: yaml: content:\n  - [unclosed")
        temp_path = f.name

    try:
        master = InterestMaster(temp_path)

        # Act & Assert
        with pytest.raises(ValueError, match="Failed to parse interests.yaml"):
            master.get_profile()
    finally:
        Path(temp_path).unlink()


def test_get_profile_missing_profile_key():
    """'profile'キーがない場合にValueErrorが発生すること."""
    # Arrange
    test_data = {"criteria": {}}

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(test_data, f)
        temp_path = f.name

    try:
        master = InterestMaster(temp_path)

        # Act & Assert
        with pytest.raises(ValueError, match="Missing 'profile' key"):
            master.get_profile()
    finally:
        Path(temp_path).unlink()


def test_get_profile_missing_criteria_key():
    """'criteria'キーがない場合にValueErrorが発生すること."""
    # Arrange
    test_data = {
        "profile": {
            "summary": "Test",
            "high_interest": [],
            "medium_interest": [],
            "low_priority": [],
        }
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(test_data, f)
        temp_path = f.name

    try:
        master = InterestMaster(temp_path)

        # Act & Assert
        with pytest.raises(ValueError, match="Missing 'criteria' key"):
            master.get_profile()
    finally:
        Path(temp_path).unlink()
