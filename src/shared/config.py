"""アプリケーション設定管理モジュール."""

import os
from dataclasses import dataclass

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from dotenv import load_dotenv

from src.shared.logging.logger import get_logger

logger = get_logger(__name__)


@dataclass
class AppConfig:
    """アプリケーション設定.

    環境変数、.env ファイル、AWS SSM Parameter Store から読み込まれた
    アプリケーション全体で使用される設定を保持します。

    Attributes:
        environment: 実行環境 ("local" または "production")
        log_level: ログレベル ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")
        dry_run: ドライラン mode フラグ
        dynamodb_cache_table: DynamoDB キャッシュテーブル名
        dynamodb_history_table: DynamoDB 履歴テーブル名
        bedrock_model_id: Bedrock モデルID
        bedrock_region: Bedrock リージョン
        bedrock_max_parallel: Bedrock 並列実行数
        llm_candidate_max: LLM 候補記事数上限
        final_select_max: 最終選抜記事数上限
        final_select_max_per_domain: ドメイン当たりの最終選抜記事数上限
        sources_config_path: RSS/Atom ソース設定ファイルパス
        from_email: 送信元メールアドレス
        to_email: 送信先メールアドレス
    """

    environment: str
    log_level: str
    dry_run: bool
    dynamodb_cache_table: str
    dynamodb_history_table: str
    bedrock_model_id: str
    bedrock_region: str
    bedrock_max_parallel: int
    llm_candidate_max: int
    final_select_max: int
    final_select_max_per_domain: int
    sources_config_path: str
    from_email: str
    to_email: str


def load_config() -> AppConfig:
    """環境に応じた設定を読み込む.

    実行環境によって読み込み元が異なります：
    - ローカル開発（environment=local）: .env ファイルから読み込み
    - Lambda環境（environment=production）: AWS SSM Parameter Store から読み込み

    Returns:
        AppConfig: アプリケーション設定

    Raises:
        ValueError: 必須設定が見つからない場合
        ClientError: SSM Parameter Store 読み込み失敗時（Lambda環境）
    """
    # .env ファイル読み込み（ローカル開発時のみ効果があります）
    load_dotenv(".env")

    environment = os.getenv("ENVIRONMENT", "local")

    if environment == "local":
        return _load_config_local()
    else:
        return _load_config_from_ssm()


def _load_config_local() -> AppConfig:
    """ローカル開発環境から設定を読み込む.

    .env ファイルおよび環境変数から設定を読み込みます。
    環境変数が優先度が高く、次に .env ファイル、最後にデフォルト値が使用されます。

    Returns:
        AppConfig: ローカル開発環境の設定

    Raises:
        ValueError: 必須設定が見つからない場合
    """
    logger.info("loading_config_from_local_env")

    try:
        config = AppConfig(
            environment="local",
            log_level=os.getenv("LOG_LEVEL", "DEBUG"),
            dry_run=os.getenv("DRY_RUN", "false").lower() == "true",
            dynamodb_cache_table=os.getenv("DYNAMODB_CACHE_TABLE", "ai-curated-newsletter-cache"),
            dynamodb_history_table=os.getenv(
                "DYNAMODB_HISTORY_TABLE", "ai-curated-newsletter-history"
            ),
            bedrock_model_id=os.getenv("BEDROCK_MODEL_ID"),
            bedrock_region=os.getenv("BEDROCK_REGION", "ap-northeast-1"),
            bedrock_max_parallel=int(os.getenv("BEDROCK_MAX_PARALLEL", "5")),
            llm_candidate_max=int(os.getenv("LLM_CANDIDATE_MAX", "150")),
            final_select_max=int(os.getenv("FINAL_SELECT_MAX", "12")),
            final_select_max_per_domain=int(os.getenv("FINAL_SELECT_MAX_PER_DOMAIN", "4")),
            sources_config_path=os.getenv("SOURCES_CONFIG_PATH", "config/sources.yaml"),
            from_email=os.getenv("FROM_EMAIL", "noreply@example.com"),
            to_email=os.getenv("TO_EMAIL", "recipient@example.com"),
        )
        logger.info("config_loaded_successfully", environment="local")
        return config

    except (ValueError, TypeError) as e:
        logger.error("config_load_failed", error=str(e))
        raise ValueError(f"Failed to load configuration: {e}") from e


def _load_config_from_ssm() -> AppConfig:
    """AWS SSM Parameter Store から設定を読み込む.

    Lambda環境での本番運用を想定しています。
    SSM Parameter Store から `/ai-curated-newsletter/` 配下のパラメータを取得します。

    Returns:
        AppConfig: SSM から読み込んだ本番環境の設定

    Raises:
        ClientError: SSM Parameter Store へのアクセス失敗時
        ValueError: 必須パラメータが見つからない場合
    """
    logger.info("loading_config_from_ssm_parameter_store")

    try:
        ssm = boto3.client("ssm", region_name=os.getenv("AWS_REGION", "ap-northeast-1"))

        # SSM Parameter Store からパラメータを取得
        params = ssm.get_parameters_by_path(
            Path="/ai-curated-newsletter/",
            Recursive=True,
            WithDecryption=True,
        )

        # パラメータを辞書に変換
        param_dict = {
            param["Name"].replace("/ai-curated-newsletter/", ""): param["Value"]
            for param in params.get("Parameters", [])
        }

        logger.info("ssm_parameters_loaded", count=len(param_dict))

        # 必須パラメータが揃っているか確認
        required_params = [
            "log_level",
            "dynamodb_cache_table",
            "dynamodb_history_table",
            "bedrock_model_id",
            "bedrock_max_parallel",
            "llm_candidate_max",
            "final_select_max",
            "final_select_max_per_domain",
            "sources_config_path",
            "from_email",
            "to_email",
        ]

        missing_params = [p for p in required_params if p not in param_dict]
        if missing_params:
            logger.error("missing_ssm_parameters", missing=missing_params)
            raise ValueError(f"Missing required SSM parameters: {', '.join(missing_params)}")

        config = AppConfig(
            environment="production",
            log_level=param_dict["log_level"],
            dry_run=param_dict.get("dry_run", "false").lower() == "true",
            dynamodb_cache_table=param_dict["dynamodb_cache_table"],
            dynamodb_history_table=param_dict["dynamodb_history_table"],
            bedrock_model_id=param_dict["bedrock_model_id"],
            bedrock_max_parallel=int(param_dict["bedrock_max_parallel"]),
            llm_candidate_max=int(param_dict["llm_candidate_max"]),
            final_select_max=int(param_dict["final_select_max"]),
            final_select_max_per_domain=int(param_dict["final_select_max_per_domain"]),
            sources_config_path=param_dict["sources_config_path"],
            from_email=param_dict["from_email"],
            to_email=param_dict["to_email"],
        )

        logger.info("config_loaded_successfully", environment="production")
        return config

    except (ClientError, BotoCoreError) as e:
        logger.error("ssm_parameter_store_error", error=str(e))
        raise ClientError(
            {"Error": {"Code": "SSMError", "Message": str(e)}}, "GetParametersByPath"
        ) from e
    except (ValueError, TypeError) as e:
        logger.error("config_parse_error", error=str(e))
        raise ValueError(f"Failed to parse configuration from SSM: {e}") from e
