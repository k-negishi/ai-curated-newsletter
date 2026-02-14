"""実行サマリエンティティモジュール."""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class ExecutionSummary:
    """実行履歴サマリ.

    ニュースレター実行の統計情報を表す.

    Attributes:
        run_id: 実行ID（UUID）
        executed_at: 実行日時（UTC）
        collected_count: 収集件数
        deduped_count: 重複排除後件数
        llm_judged_count: LLM判定件数
        cache_hit_count: キャッシュヒット件数
        final_selected_count: 最終選定件数（0-15）
        notification_sent: 通知送信成功フラグ
        execution_time_seconds: 実行時間（秒）
        estimated_cost_usd: 推定コスト（USD）
    """

    run_id: str
    executed_at: datetime
    collected_count: int
    deduped_count: int
    llm_judged_count: int
    cache_hit_count: int
    final_selected_count: int
    notification_sent: bool
    execution_time_seconds: float
    estimated_cost_usd: float
