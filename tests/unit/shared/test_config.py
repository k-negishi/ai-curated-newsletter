"""アプリケーション設定のテスト."""

import os
from unittest.mock import Mock, patch

import pytest

from src.shared.config import AppConfig, _load_config_from_ssm, _load_config_local, load_config


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
            "BEDROCK_MODEL_ID": "anthropic.claude-haiku-4-5-20251001-v1:0",
            "BEDROCK_MAX_PARALLEL": "5",
            "LLM_CANDIDATE_MAX": "150",
            "FINAL_SELECT_MAX": "15",
            "FINAL_SELECT_MAX_PER_DOMAIN": "0",
            "SOURCES_CONFIG_PATH": "config/sources.yaml",
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
        assert config.bedrock_model_id == "anthropic.claude-haiku-4-5-20251001-v1:0"
        assert config.bedrock_inference_profile_arn == ""
        assert config.bedrock_max_parallel == 5
        assert config.llm_candidate_max == 150
        assert config.final_select_max == 15
        assert config.final_select_max_per_domain == 0
        assert config.sources_config_path == "config/sources.yaml"
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
        "BEDROCK_INFERENCE_PROFILE_ARN": "arn:aws:bedrock:ap-northeast-1::inference-profile/custom-profile",
        "BEDROCK_MAX_PARALLEL": "10",
        "LLM_CANDIDATE_MAX": "200",
        "FINAL_SELECT_MAX": "20",
        "FINAL_SELECT_MAX_PER_DOMAIN": "5",
        "SOURCES_CONFIG_PATH": "custom/sources.yaml",
        "FROM_EMAIL": "custom-from@example.com",
        "TO_EMAIL": "custom-to@example.com",
    }

    with patch.dict(os.environ, env_vars, clear=False):
        config = _load_config_local()

        assert config.log_level == "INFO"
        assert config.dry_run is True
        assert config.dynamodb_cache_table == "custom-cache"
        assert config.bedrock_inference_profile_arn == "arn:aws:bedrock:ap-northeast-1::inference-profile/custom-profile"
        assert config.bedrock_max_parallel == 10
        assert config.llm_candidate_max == 200
        assert config.final_select_max == 20
        assert config.final_select_max_per_domain == 5
        assert config.sources_config_path == "custom/sources.yaml"
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
        bedrock_inference_profile_arn="",
        bedrock_region="ap-northeast-1",
        bedrock_max_parallel=5,
        bedrock_request_interval=2.5,
        bedrock_retry_base_delay=2.0,
        bedrock_max_backoff=20.0,
        bedrock_max_retries=4,
        llm_candidate_max=150,
        final_select_max=15,
        final_select_max_per_domain=4,
        sources_config_path="sources.yaml",
        from_email="from@example.com",
        to_email="to@example.com",
    )

    assert config.environment == "local"
    assert config.log_level == "DEBUG"
    assert config.dry_run is False
    assert config.bedrock_inference_profile_arn == ""
    assert config.bedrock_request_interval == 2.5
    assert config.bedrock_retry_base_delay == 2.0
    assert config.bedrock_max_backoff == 20.0
    assert config.bedrock_max_retries == 4


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


def test_load_config_from_ssm_dotenv_parameter() -> None:
    """SSM の dotenv 1パラメータから production 設定を復元できることを確認."""
    dotenv_content = """LOG_LEVEL=INFO
DRY_RUN=true
DYNAMODB_CACHE_TABLE=prod-cache
DYNAMODB_HISTORY_TABLE=prod-history
BEDROCK_MODEL_ID=anthropic.claude-haiku-4-5-20251001-v1:0
BEDROCK_MAX_PARALLEL=8
LLM_CANDIDATE_MAX=180
FINAL_SELECT_MAX=15
FINAL_SELECT_MAX_PER_DOMAIN=5
SOURCES_CONFIG_PATH=config/sources.yaml
FROM_EMAIL=prod-from@example.com
TO_EMAIL=prod-to@example.com
"""
    mock_ssm = Mock()
    mock_ssm.get_parameter.return_value = {"Parameter": {"Value": dotenv_content}}

    with patch("src.shared.config.boto3.client", return_value=mock_ssm):
        with patch.dict(
            os.environ,
            {
                "AWS_REGION": "ap-northeast-1",
                "SSM_DOTENV_PARAMETER": "/ai-curated-newsletter/dotenv",
            },
            clear=False,
        ):
            config = _load_config_from_ssm()

    assert config.environment == "production"
    assert config.log_level == "INFO"
    assert config.dry_run is True
    assert config.dynamodb_cache_table == "prod-cache"
    assert config.dynamodb_history_table == "prod-history"
    assert config.bedrock_model_id == "anthropic.claude-haiku-4-5-20251001-v1:0"
    # BEDROCK_REGION が dotenv 内にない場合、AWS_REGION をフォールバックとして使う
    assert config.bedrock_region == "ap-northeast-1"
    assert config.bedrock_max_parallel == 8
    assert config.llm_candidate_max == 180
    assert config.final_select_max == 15
    assert config.final_select_max_per_domain == 5
    assert config.sources_config_path == "config/sources.yaml"
    assert config.from_email == "prod-from@example.com"
    assert config.to_email == "prod-to@example.com"
    mock_ssm.get_parameter.assert_called_once_with(
        Name="/ai-curated-newsletter/dotenv",
        WithDecryption=True,
    )


def test_load_config_from_ssm_dotenv_parameter_missing_required() -> None:
    """dotenv 内の必須値が欠けると ValueError になることを確認."""
    dotenv_content = """LOG_LEVEL=INFO
DYNAMODB_CACHE_TABLE=prod-cache
DYNAMODB_HISTORY_TABLE=prod-history
BEDROCK_MODEL_ID=anthropic.claude-haiku-4-5-20251001-v1:0
BEDROCK_MAX_PARALLEL=8
LLM_CANDIDATE_MAX=180
FINAL_SELECT_MAX=15
FINAL_SELECT_MAX_PER_DOMAIN=5
SOURCES_CONFIG_PATH=config/sources.yaml
FROM_EMAIL=prod-from@example.com
"""
    mock_ssm = Mock()
    mock_ssm.get_parameter.return_value = {"Parameter": {"Value": dotenv_content}}

    with patch("src.shared.config.boto3.client", return_value=mock_ssm):
        with pytest.raises(ValueError, match="TO_EMAIL"):
            _load_config_from_ssm()
