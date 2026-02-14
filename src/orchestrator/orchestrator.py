"""オーケストレーターモジュール."""

import time
from dataclasses import asdict, dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

from src.models.execution_summary import ExecutionSummary
from src.repositories.cache_repository import CacheRepository
from src.repositories.history_repository import HistoryRepository
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
from src.shared.logging.logger import get_logger
from src.shared.utils.bedrock_cost_estimator import estimate_bedrock_cost_usd

logger = get_logger(__name__)


@dataclass
class OrchestratorOutput:
    """オーケストレーター実行結果.

    Attributes:
        summary: 実行サマリ
        notification_sent: 通知送信成功フラグ
    """

    summary: ExecutionSummary
    notification_sent: bool


class Orchestrator:
    """オーケストレーター.

    ニュースレター生成の全体フローを制御する.

    8ステップ:
    1. 収集・正規化
    2. 重複排除
    3. Buzzスコア計算
    4. 候補選定
    5. LLM判定
    6. 最終選定
    7. フォーマット・通知
    8. 履歴保存

    Attributes:
        _source_master: 収集元マスタ
        _cache_repository: キャッシュリポジトリ
        _history_repository: 履歴リポジトリ
        _collector: 収集サービス
        _normalizer: 正規化サービス
        _deduplicator: 重複排除サービス
        _buzz_scorer: Buzzスコア計算サービス
        _candidate_selector: 候補選定サービス
        _llm_judge: LLM判定サービス
        _final_selector: 最終選定サービス
        _formatter: フォーマットサービス
        _notifier: 通知サービス
    """

    def __init__(
        self,
        source_master: SourceMaster,
        cache_repository: CacheRepository | None,
        history_repository: HistoryRepository | None,
        collector: Collector,
        normalizer: Normalizer,
        deduplicator: Deduplicator,
        buzz_scorer: BuzzScorer,
        candidate_selector: CandidateSelector,
        llm_judge: LlmJudge,
        final_selector: FinalSelector,
        formatter: Formatter,
        notifier: Notifier,
    ) -> None:
        """オーケストレーターを初期化する.

        Args:
            source_master: 収集元マスタ
            cache_repository: キャッシュリポジトリ
            history_repository: 履歴リポジトリ
            collector: 収集サービス
            normalizer: 正規化サービス
            deduplicator: 重複排除サービス
            buzz_scorer: Buzzスコア計算サービス
            candidate_selector: 候補選定サービス
            llm_judge: LLM判定サービス
            final_selector: 最終選定サービス
            formatter: フォーマットサービス
            notifier: 通知サービス
        """
        self._source_master = source_master
        self._cache_repository = cache_repository
        self._history_repository = history_repository
        self._collector = collector
        self._normalizer = normalizer
        self._deduplicator = deduplicator
        self._buzz_scorer = buzz_scorer
        self._candidate_selector = candidate_selector
        self._llm_judge = llm_judge
        self._final_selector = final_selector
        self._formatter = formatter
        self._notifier = notifier

    async def execute(
        self, run_id: str, executed_at: datetime, dry_run: bool = False
    ) -> OrchestratorOutput:
        """ニュースレター生成フローを実行する.

        Args:
            run_id: 実行ID（UUID）
            executed_at: 実行日時（UTC）
            dry_run: dry_runモード（通知をスキップ）

        Returns:
            実行結果

        Raises:
            Exception: 致命的エラーが発生した場合
        """
        start_time = time.time()

        logger.info("orchestrator_start", run_id=run_id, dry_run=dry_run)

        # 統計情報の初期化
        collected_count = 0
        deduped_count = 0
        llm_judged_count = 0
        cache_hit_count = 0
        final_selected_count = 0
        notification_sent = False

        try:
            # Step 1: 収集・正規化
            collection_result = await self._collector.collect()
            collected_count = len(collection_result.articles)
            logger.info(
                "step1_collect_complete",
                collected_count=collected_count,
                error_count=len(collection_result.errors),
            )

            normalized_articles = self._normalizer.normalize(collection_result.articles)
            logger.info("step1_complete", normalized_count=len(normalized_articles))

            # Step 2: 重複排除
            dedup_result = self._deduplicator.deduplicate(normalized_articles)
            deduped_count = len(dedup_result.unique_articles)
            cache_hit_count = dedup_result.cached_count
            logger.info(
                "step2_complete",
                unique_count=deduped_count,
                duplicate_count=dedup_result.duplicate_count,
                cached_count=cache_hit_count,
            )

            # Step 3: Buzzスコア計算
            buzz_scores = await self._buzz_scorer.calculate_scores(dedup_result.unique_articles)
            logger.info("step3_complete", score_count=len(buzz_scores))

            # Step 4: 候補選定
            selection_result = self._candidate_selector.select(
                dedup_result.unique_articles, buzz_scores
            )
            logger.info("step4_complete", candidate_count=len(selection_result.candidates))

            # Step 5: LLM判定
            judgment_result = await self._llm_judge.judge_batch(selection_result.candidates)
            llm_judged_count = len(judgment_result.judgments)
            logger.info(
                "step5_complete",
                judged_count=llm_judged_count,
                failed_count=judgment_result.failed_count,
            )

            # Step 6: 最終選定
            final_result = self._final_selector.select(judgment_result.judgments)
            final_selected_count = len(final_result.selected_articles)
            logger.info("step6_complete", selected_count=final_selected_count)

            # Step 7: フォーマット・通知
            logger.info("step7_start", step="format_and_notify")

            if final_selected_count == 0:
                logger.warning("no_articles_to_notify")
                # 記事がない場合でも履歴は保存
            else:
                # メール本文生成
                mail_body = self._formatter.format(
                    selected_articles=final_result.selected_articles,
                    collected_count=collected_count,
                    judged_count=llm_judged_count,
                    executed_at=executed_at,
                )
                mail_html_body = self._formatter.format_html(
                    selected_articles=final_result.selected_articles,
                    collected_count=collected_count,
                    judged_count=llm_judged_count,
                    executed_at=executed_at,
                )

                if dry_run:
                    logger.info("dry_run_mode", message="Showing formatted output")
                    # dry_runモードでもフォーマット結果を表示
                    print("\n" + "=" * 80)
                    print("📧 フォーマット結果（dry_runモード、メール送信なし）")
                    print("=" * 80)
                    print(mail_body)
                    print("=" * 80 + "\n")
                    logger.info("step7_complete", notification_sent=notification_sent)
                else:
                    # メール送信
                    subject = self._build_newsletter_subject(executed_at)
                    notification_result = self._notifier.send(
                        subject=subject, body=mail_body, html_body=mail_html_body
                    )
                    notification_sent = True
                    logger.info(
                        "step7_complete",
                        message_id=notification_result.message_id,
                        notification_sent=notification_sent,
                    )

            # Step 8: 履歴保存
            logger.info("step8_start", step="save_history")
            execution_time = time.time() - start_time

            # コスト推定（トークン単価ベース）
            estimated_cost = estimate_bedrock_cost_usd(llm_judged_count)

            summary = ExecutionSummary(
                run_id=run_id,
                executed_at=executed_at,
                collected_count=collected_count,
                deduped_count=deduped_count,
                llm_judged_count=llm_judged_count,
                cache_hit_count=cache_hit_count,
                final_selected_count=final_selected_count,
                notification_sent=notification_sent,
                execution_time_seconds=execution_time,
                estimated_cost_usd=estimated_cost,
            )

            # TODO(MVP): DynamoDB未セットアップのため一時的にコメントアウト
            # self._history_repository.save(summary)
            # MVPフェーズではログ出力のみ（DynamoDB未使用）
            logger.info("execution_summary", **asdict(summary))
            logger.info("step8_complete", run_id=run_id)

            logger.info(
                "orchestrator_complete",
                run_id=run_id,
                execution_time_seconds=execution_time,
            )

            return OrchestratorOutput(summary=summary, notification_sent=notification_sent)

        except Exception as e:
            logger.error(
                "orchestrator_failed",
                run_id=run_id,
                error=str(e),
            )
            raise

    @classmethod
    def _build_newsletter_subject(cls, executed_at: datetime) -> str:
        """ニュースレター件名を生成する."""
        jst_date = executed_at.astimezone(cls._TOKYO_TZ)
        return f"Techニュースレター - {jst_date.year}年{jst_date.month}月{jst_date.day}日"

    _TOKYO_TZ = ZoneInfo("Asia/Tokyo")
