"""アプリケーション設定のテスト."""

import os
from unittest.mock import patch

import pytest

from src.shared.config import AppConfig, load_config, _load_config_local


def test_load_config_local_defaults() -> None:
    """ローカル環境でデフォルト値が使用されることを確認."""
    # NOTE: .env ファイルが存在する場合、load_dotenv により環境変数が設定される
    # そのため、テストではすべての環境変数をクリアしてから検証する
    with patch.dict(
        os.environ,
        {
            "ENVIRONMENT": "local",
            "LOG_LEVEL": "DEBUG",
            "DRY_RUN": "false",
            "DYNAMODB_CACHE_TABLE": "ai-curated-newsletter-cache",
            "DYNAMODB_HISTORY_TABLE": "ai-curated-newsletter-history",
            "BEDROCK_MODEL_ID": "anthropic.claude-3-5-sonnet-20241022-v2:0",
            "BEDROCK_MAX_PARALLEL": "5",
            "LLM_CANDIDATE_MAX": "150",
            "FINAL_SELECT_MAX": "12",
            "FINAL_SELECT_MAX_PER_DOMAIN": "4",
            "SOURCES_CONFIG_PATH": "config/sources.json",
            "FROM_EMAIL": "noreply@example.com",
            "TO_EMAIL": "recipient@example.com",
        },
        clear=True,
    ):
        config = _load_config_local()

        assert config.environment == "local"
        assert config.log_level == "DEBUG"
        assert config.dry_run is False
        assert config.dynamodb_cache_table == "ai-curated-newsletter-cache"
        assert config.dynamodb_history_table == "ai-curated-newsletter-history"
        assert config.bedrock_model_id == "anthropic.claude-3-5-sonnet-20241022-v2:0"
        assert config.bedrock_max_parallel == 5
        assert config.llm_candidate_max == 150
        assert config.final_select_max == 12
        assert config.final_select_max_per_domain == 4
        assert config.sources_config_path == "config/sources.json"
        assert config.from_email == "noreply@example.com"
        assert config.to_email == "recipient@example.com"


def test_load_config_local_with_env_vars() -> None:
    """環境変数でオーバーライドされることを確認."""
    env_vars = {
        "ENVIRONMENT": "local",
        "LOG_LEVEL": "INFO",
        "DRY_RUN": "true",
        "DYNAMODB_CACHE_TABLE": "custom-cache",
        "DYNAMODB_HISTORY_TABLE": "custom-history",
        "BEDROCK_MODEL_ID": "custom-model",
        "BEDROCK_MAX_PARALLEL": "10",
        "LLM_CANDIDATE_MAX": "200",
        "FINAL_SELECT_MAX": "20",
        "FINAL_SELECT_MAX_PER_DOMAIN": "5",
        "SOURCES_CONFIG_PATH": "custom/sources.json",
        "FROM_EMAIL": "custom-from@example.com",
        "TO_EMAIL": "custom-to@example.com",
    }

    with patch.dict(os.environ, env_vars, clear=False):
        config = _load_config_local()

        assert config.log_level == "INFO"
        assert config.dry_run is True
        assert config.dynamodb_cache_table == "custom-cache"
        assert config.bedrock_max_parallel == 10
        assert config.llm_candidate_max == 200
        assert config.final_select_max == 20
        assert config.final_select_max_per_domain == 5
        assert config.sources_config_path == "custom/sources.json"
        assert config.from_email == "custom-from@example.com"
        assert config.to_email == "custom-to@example.com"


def test_load_config_local_dry_run_variations() -> None:
    """dry_run フラグのバリエーション処理を確認."""
    test_cases = [
        ("true", True),
        ("True", True),
        ("TRUE", True),
        ("false", False),
        ("False", False),
        ("FALSE", False),
        ("", False),
        ("invalid", False),
    ]

    for dry_run_value, expected in test_cases:
        with patch.dict(os.environ, {"ENVIRONMENT": "local", "DRY_RUN": dry_run_value}, clear=False):
            config = _load_config_local()
            assert config.dry_run is expected, f"Failed for DRY_RUN={dry_run_value}"


def test_app_config_dataclass() -> None:
    """AppConfig dataclass が正しく動作することを確認."""
    config = AppConfig(
        environment="local",
        log_level="DEBUG",
        dry_run=False,
        dynamodb_cache_table="cache",
        dynamodb_history_table="history",
        bedrock_model_id="model-id",
        bedrock_max_parallel=5,
        llm_candidate_max=150,
        final_select_max=12,
        final_select_max_per_domain=4,
        sources_config_path="sources.json",
        from_email="from@example.com",
        to_email="to@example.com",
    )

    assert config.environment == "local"
    assert config.log_level == "DEBUG"
    assert config.dry_run is False


def test_load_config_local_integer_parsing() -> None:
    """整数値が正しくパースされることを確認."""
    env_vars = {
        "ENVIRONMENT": "local",
        "BEDROCK_MAX_PARALLEL": "25",
        "LLM_CANDIDATE_MAX": "300",
        "FINAL_SELECT_MAX": "25",
        "FINAL_SELECT_MAX_PER_DOMAIN": "8",
    }

    with patch.dict(os.environ, env_vars, clear=False):
        config = _load_config_local()

        assert isinstance(config.bedrock_max_parallel, int)
        assert isinstance(config.llm_candidate_max, int)
        assert isinstance(config.final_select_max, int)
        assert isinstance(config.final_select_max_per_domain, int)

        assert config.bedrock_max_parallel == 25
        assert config.llm_candidate_max == 300
        assert config.final_select_max == 25
        assert config.final_select_max_per_domain == 8


def test_load_config_local_invalid_integer() -> None:
    """無効な整数値でエラーが発生することを確認."""
    env_vars = {
        "ENVIRONMENT": "local",
        "BEDROCK_MAX_PARALLEL": "invalid",
    }

    with patch.dict(os.environ, env_vars, clear=False):
        with pytest.raises(ValueError):
            _load_config_local()


def test_load_config_environment_detection() -> None:
    """環境検出が正しく動作することを確認."""
    # local 環境
    with patch.dict(os.environ, {"ENVIRONMENT": "local"}, clear=False):
        config = load_config()
        assert config.environment == "local"

    # デフォルト（ENVIRONMENT未設定 -> local と判定）
    with patch.dict(os.environ, {}, clear=True):
        # ENVIRONMENT がない場合は "local" がデフォルト
        config = load_config()
        assert config.environment == "local"
