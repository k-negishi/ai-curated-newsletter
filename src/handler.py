"""Lambda ハンドラーモジュール."""

import asyncio
import json
import uuid
from typing import Any

import boto3

from src.orchestrator.orchestrator import Orchestrator
from src.repositories.interest_master import InterestMaster
from src.repositories.source_master import SourceMaster
from src.services.buzz_scorer import BuzzScorer
from src.services.candidate_selector import CandidateSelector
from src.services.collector import Collector
from src.services.deduplicator import Deduplicator
from src.services.final_selector import FinalSelector
from src.services.formatter import Formatter
from src.services.llm_judge import LlmJudge
from src.services.normalizer import Normalizer
from src.services.notifier import Notifier
from src.shared.config import load_config
from src.shared.logging.logger import configure_logging, get_logger
from src.shared.utils.date_utils import now_utc


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Lambda エントリポイント.

    Args:
        event: Lambda イベント
        context: Lambda コンテキスト

    Returns:
        Lambda レスポンス
    """
    # run_id生成
    run_id = str(uuid.uuid4())

    # ログ設定
    configure_logging(run_id=run_id)
    logger = get_logger(__name__)

    logger.info("lambda_handler_start", run_id=run_id)

    try:
        # 設定読み込み
        config = load_config()
        logger.info("config_loaded", environment=config.environment)

        # ログレベル設定（config から取得）
        configure_logging(log_level=config.log_level, run_id=run_id)

        # イベント解析と dry_run フラグ決定
        # イベント内の dry_run フラグが設定されていれば優先、なければ環境変数から取得
        dry_run = event.get("dry_run", config.dry_run)
        logger.info("event_parsed", dry_run=dry_run)

        # AWS クライアント初期化
        # TODO(MVP): DynamoDB未セットアップのため一時的にコメントアウト
        # Phase 2で有効化: 以下の2行を復元
        # dynamodb = boto3.resource("dynamodb")
        # cache_repository = CacheRepository(dynamodb, config.dynamodb_cache_table)
        # history_repository = HistoryRepository(dynamodb, config.dynamodb_history_table)
        bedrock_runtime = boto3.client("bedrock-runtime", region_name=config.bedrock_region)
        ses = boto3.client("ses")

        # リポジトリ初期化
        source_master = SourceMaster(config.sources_config_path)
        interest_master = InterestMaster("config/interests.yaml")
        interest_profile = interest_master.get_profile()
        cache_repository = None  # MVPフェーズではキャッシュ機能を無効化
        history_repository = None  # MVPフェーズでは履歴保存機能を無効化

        # サービス初期化
        collector = Collector(source_master)
        normalizer = Normalizer()
        deduplicator = Deduplicator(cache_repository)
        buzz_scorer = BuzzScorer()
        candidate_selector = CandidateSelector(max_candidates=config.llm_candidate_max)
        llm_judge = LlmJudge(
            bedrock_client=bedrock_runtime,
            cache_repository=cache_repository,
            interest_profile=interest_profile,
            model_id=config.bedrock_model_id,
        )
        final_selector = FinalSelector(
            max_articles=config.final_select_max,
            max_per_domain=config.final_select_max_per_domain,
        )
        formatter = Formatter()
        notifier = Notifier(
            ses, from_email=config.from_email, to_email=config.to_email, dry_run=dry_run
        )

        # Orchestrator初期化
        orchestrator = Orchestrator(
            source_master=source_master,
            cache_repository=cache_repository,
            history_repository=history_repository,
            collector=collector,
            normalizer=normalizer,
            deduplicator=deduplicator,
            buzz_scorer=buzz_scorer,
            candidate_selector=candidate_selector,
            llm_judge=llm_judge,
            final_selector=final_selector,
            formatter=formatter,
            notifier=notifier,
        )

        # Orchestrator実行
        executed_at = now_utc()
        result = asyncio.run(orchestrator.execute(run_id, executed_at, dry_run))

        # レスポンス返却
        logger.info("lambda_handler_success", run_id=run_id)

        return {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "message": "Newsletter generation completed",
                    "run_id": run_id,
                    "collected_count": result.summary.collected_count,
                    "final_selected_count": result.summary.final_selected_count,
                    "notification_sent": result.notification_sent,
                }
            ),
        }

    except Exception as e:
        logger.error("lambda_handler_failed", run_id=run_id, error=str(e))

        return {
            "statusCode": 500,
            "body": json.dumps(
                {
                    "message": "Newsletter generation failed",
                    "run_id": run_id,
                    "error": str(e),
                }
            ),
        }
