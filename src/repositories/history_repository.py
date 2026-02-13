"""実行履歴リポジトリモジュール."""

from datetime import timedelta
from typing import Any

from botocore.exceptions import ClientError

from src.models.execution_summary import ExecutionSummary
from src.shared.logging.logger import get_logger

logger = get_logger(__name__)


class HistoryRepository:
    """実行履歴リポジトリ.

    DynamoDBに実行履歴（ExecutionSummary）を保存する.
    TTL付きで90日後に自動削除される.

    Attributes:
        _table: DynamoDBテーブルリソース
        _table_name: テーブル名
        _dry_run: ドライランモード（true の場合、履歴保存をスキップ）
    """

    def __init__(self, dynamodb_resource: Any, table_name: str, dry_run: bool = False) -> None:
        """リポジトリを初期化する.

        Args:
            dynamodb_resource: DynamoDBリソース（boto3.resource('dynamodb')）
            table_name: テーブル名
            dry_run: ドライランモード（デフォルト: False）
        """
        self._dynamodb = dynamodb_resource
        self._table_name = table_name
        self._table = dynamodb_resource.Table(table_name)
        self._dry_run = dry_run

    def _generate_pk(self, year: int, week: int) -> str:
        """年・週番号からパーティションキーを生成する.

        Args:
            year: 年（4桁）
            week: 週番号（1-53）

        Returns:
            パーティションキー（RUN#<YYYYWW>形式）
        """
        return f"RUN#{year:04d}{week:02d}"

    def _generate_sk(self, executed_at_iso: str) -> str:
        """実行日時からソートキーを生成する.

        Args:
            executed_at_iso: 実行日時（ISO 8601形式文字列）

        Returns:
            ソートキー（SUMMARY#<timestamp>形式）
        """
        return f"SUMMARY#{executed_at_iso}"

    def _calculate_ttl(self, summary: ExecutionSummary) -> int:
        """TTLを計算する（実行日時 + 90日）.

        Args:
            summary: 実行サマリ

        Returns:
            TTL（Unixタイムスタンプ）
        """
        ttl_date = summary.executed_at + timedelta(days=90)
        return int(ttl_date.timestamp())

    def save(self, summary: ExecutionSummary) -> None:
        """実行サマリをDynamoDBに保存する.

        dry_run=true の場合、履歴保存をスキップします。

        Args:
            summary: 実行サマリ

        Raises:
            ClientError: DynamoDB操作に失敗した場合
        """
        # dry_run=true の場合、履歴保存をスキップ
        if self._dry_run:
            logger.info(
                "history_save_skipped",
                run_id=summary.run_id,
                reason="dry_run_mode_enabled",
            )
            return

        # 年・週番号を計算（ISO 8601 week date）
        iso_calendar = summary.executed_at.isocalendar()
        year = iso_calendar[0]
        week = iso_calendar[1]

        pk = self._generate_pk(year, week)
        sk = self._generate_sk(summary.executed_at.isoformat())
        ttl = self._calculate_ttl(summary)

        try:
            self._table.put_item(
                Item={
                    "PK": pk,
                    "SK": sk,
                    "run_id": summary.run_id,
                    "executed_at": summary.executed_at.isoformat(),
                    "collected_count": summary.collected_count,
                    "deduped_count": summary.deduped_count,
                    "llm_judged_count": summary.llm_judged_count,
                    "cache_hit_count": summary.cache_hit_count,
                    "final_selected_count": summary.final_selected_count,
                    "notification_sent": summary.notification_sent,
                    "execution_time_seconds": summary.execution_time_seconds,
                    "estimated_cost_usd": summary.estimated_cost_usd,
                    "ttl": ttl,
                }
            )
            logger.debug(
                "history_save_success",
                run_id=summary.run_id,
                year=year,
                week=week,
            )

        except ClientError as e:
            logger.error("history_save_error", run_id=summary.run_id, error=str(e))
            raise

    def get_by_week(self, year: int, week: int) -> list[ExecutionSummary]:
        """指定週の実行履歴を取得する.

        Args:
            year: 年（4桁）
            week: 週番号（1-53）

        Returns:
            実行サマリのリスト（古い順）
        """
        pk = self._generate_pk(year, week)

        try:
            response = self._table.query(
                KeyConditionExpression="PK = :pk",
                ExpressionAttributeValues={":pk": pk},
            )

            items = response.get("Items", [])

            # DynamoDBアイテムからExecutionSummaryに変換
            from datetime import datetime

            summaries: list[ExecutionSummary] = []
            for item in items:
                summary = ExecutionSummary(
                    run_id=item["run_id"],
                    executed_at=datetime.fromisoformat(item["executed_at"]),
                    collected_count=int(item["collected_count"]),
                    deduped_count=int(item["deduped_count"]),
                    llm_judged_count=int(item["llm_judged_count"]),
                    cache_hit_count=int(item["cache_hit_count"]),
                    final_selected_count=int(item["final_selected_count"]),
                    notification_sent=bool(item["notification_sent"]),
                    execution_time_seconds=float(item["execution_time_seconds"]),
                    estimated_cost_usd=float(item["estimated_cost_usd"]),
                )
                summaries.append(summary)

            logger.debug("history_get_by_week_success", year=year, week=week, count=len(summaries))
            return summaries

        except ClientError as e:
            logger.error("history_get_by_week_error", year=year, week=week, error=str(e))
            return []
