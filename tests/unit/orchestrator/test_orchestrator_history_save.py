"""Orchestrator の履歴保存ロジックのユニットテスト."""

import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock, patch

import pytest

from src.orchestrator.orchestrator import Orchestrator


def _build_orchestrator(
    history_repository: Mock | None = None,
) -> Orchestrator:
    """テスト用の Orchestrator を構築する.

    各サービスはモックで置き換え、最小限のパイプラインが動作するようにする.
    """
    source_master = Mock()
    cache_repository = None

    collector = Mock()
    collected_article = Mock()
    collected_article.url = "https://example.com/article"
    collection_result = Mock()
    collection_result.articles = [collected_article]
    collection_result.errors = []
    collector.collect = AsyncMock(return_value=collection_result)

    normalizer = Mock()
    normalizer.normalize.return_value = [collected_article]

    dedup_result = Mock()
    dedup_result.unique_articles = [collected_article]
    dedup_result.duplicate_count = 0
    dedup_result.cached_count = 0
    deduplicator = Mock()
    deduplicator.deduplicate.return_value = dedup_result

    buzz_score = Mock()
    buzz_score.to_buzz_label.return_value = "high"
    buzz_scorer = Mock()
    buzz_scorer.calculate_scores = AsyncMock(
        return_value={"https://example.com/article": buzz_score}
    )

    selection_result = Mock()
    selection_result.candidates = [collected_article]
    candidate_selector = Mock()
    candidate_selector.select.return_value = selection_result

    judgment = Mock()
    judgment.url = "https://example.com/article"
    judgment.buzz_label = None
    judgment_batch_result = Mock()
    judgment_batch_result.judgments = [judgment]
    judgment_batch_result.failed_count = 0
    llm_judge = Mock()
    llm_judge.judge_batch = AsyncMock(return_value=judgment_batch_result)

    final_result = Mock()
    final_result.selected_articles = [judgment]
    final_selector = Mock()
    final_selector.select.return_value = final_result

    formatter = Mock()
    formatter.format.return_value = "plain text body"
    formatter.format_html.return_value = "<p>html body</p>"

    notifier = Mock()
    notification_result = Mock()
    notification_result.message_id = "msg-001"
    notifier.send.return_value = notification_result

    return Orchestrator(
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


def test_history_saved_when_repository_provided() -> None:
    """history_repository が設定されている場合、save() が呼ばれることを確認."""
    mock_history_repo = Mock()
    orchestrator = _build_orchestrator(history_repository=mock_history_repo)

    executed_at = datetime(2026, 2, 24, 10, 0, 0, tzinfo=timezone.utc)
    result = asyncio.run(orchestrator.execute("run-001", executed_at, dry_run=False))

    mock_history_repo.save.assert_called_once()
    saved_summary = mock_history_repo.save.call_args[0][0]
    assert saved_summary.run_id == "run-001"
    assert result.notification_sent is True


def test_history_skipped_when_repository_is_none() -> None:
    """history_repository が None の場合、エラーなく実行が完了することを確認."""
    orchestrator = _build_orchestrator(history_repository=None)

    executed_at = datetime(2026, 2, 24, 10, 0, 0, tzinfo=timezone.utc)
    result = asyncio.run(orchestrator.execute("run-002", executed_at, dry_run=False))

    # エラーなく完了し、結果が返される
    assert result.summary.run_id == "run-002"
    assert result.notification_sent is True
