"""dry_run モードの統合テスト."""

from unittest.mock import Mock
from datetime import datetime

import pytest

from src.repositories.history_repository import HistoryRepository
from src.services.notifier import Notifier
from src.models.execution_summary import ExecutionSummary


@pytest.fixture
def mock_ses_client():
    """モックのSESクライアントを返す."""
    mock_ses = Mock()
    mock_ses.send_email.return_value = {"MessageId": "test-message-id"}
    return mock_ses


@pytest.fixture
def mock_dynamodb_resource():
    """モックのDynamoDBリソースを返す."""
    mock_db = Mock()
    mock_table = Mock()
    mock_db.Table.return_value = mock_table
    return mock_db


def test_dry_run_notifier_skip(mock_ses_client) -> None:
    """dry_run=true の場合、Notifier.send() がメール送信をスキップすることを確認."""
    notifier = Notifier(
        ses_client=mock_ses_client,
        from_email="sender@example.com",
        to_email="recipient@example.com",
        dry_run=True,
    )

    result = notifier.send(subject="Test", body="Test body")

    # 結果が返される（ただし message_id は "dry-run"）
    assert result.message_id == "dry-run"
    assert result.sent_at is not None

    # SES send_email は呼ばれない
    assert mock_ses_client.send_email.call_count == 0


def test_dry_run_notifier_not_skip(mock_ses_client) -> None:
    """dry_run=false の場合、Notifier.send() が正常に動作することを確認."""
    notifier = Notifier(
        ses_client=mock_ses_client,
        from_email="sender@example.com",
        to_email="recipient@example.com",
        dry_run=False,
    )

    result = notifier.send(subject="Test", body="Test body")

    # 結果が返される
    assert result.message_id == "test-message-id"
    assert result.sent_at is not None

    # SES send_email が呼ばれる
    assert mock_ses_client.send_email.call_count == 1


def test_dry_run_history_skip(mock_dynamodb_resource) -> None:
    """dry_run=true の場合、HistoryRepository.save() が履歴保存をスキップすることを確認."""
    repository = HistoryRepository(
        dynamodb_resource=mock_dynamodb_resource,
        table_name="test-history",
        dry_run=True,
    )

    summary = ExecutionSummary(
        run_id="test-run-id",
        executed_at=datetime.now(),
        collected_count=10,
        deduped_count=8,
        llm_judged_count=6,
        cache_hit_count=2,
        final_selected_count=4,
        notification_sent=False,
        execution_time_seconds=5.0,
        estimated_cost_usd=0.06,
    )

    repository.save(summary)

    # DynamoDB put_item は呼ばれない
    mock_table = mock_dynamodb_resource.Table.return_value
    assert mock_table.put_item.call_count == 0


def test_dry_run_history_not_skip(mock_dynamodb_resource) -> None:
    """dry_run=false の場合、HistoryRepository.save() が正常に動作することを確認."""
    repository = HistoryRepository(
        dynamodb_resource=mock_dynamodb_resource,
        table_name="test-history",
        dry_run=False,
    )

    summary = ExecutionSummary(
        run_id="test-run-id",
        executed_at=datetime.now(),
        collected_count=10,
        deduped_count=8,
        llm_judged_count=6,
        cache_hit_count=2,
        final_selected_count=4,
        notification_sent=False,
        execution_time_seconds=5.0,
        estimated_cost_usd=0.06,
    )

    repository.save(summary)

    # DynamoDB put_item が呼ばれる
    mock_table = mock_dynamodb_resource.Table.return_value
    assert mock_table.put_item.call_count == 1


def test_dry_run_default_false(mock_ses_client) -> None:
    """dry_run デフォルト値が False であることを確認."""
    notifier = Notifier(
        ses_client=mock_ses_client,
        from_email="sender@example.com",
        to_email="recipient@example.com",
    )

    assert notifier._dry_run is False

    result = notifier.send(subject="Test", body="Test body")

    # デフォルトが False なので、SES send_email が呼ばれる
    assert mock_ses_client.send_email.call_count == 1


def test_dry_run_history_default_false(mock_dynamodb_resource) -> None:
    """HistoryRepository dry_run デフォルト値が False であることを確認."""
    repository = HistoryRepository(
        dynamodb_resource=mock_dynamodb_resource,
        table_name="test-history",
    )

    assert repository._dry_run is False

    summary = ExecutionSummary(
        run_id="test-run-id",
        executed_at=datetime.now(),
        collected_count=10,
        deduped_count=8,
        llm_judged_count=6,
        cache_hit_count=2,
        final_selected_count=4,
        notification_sent=False,
        execution_time_seconds=5.0,
        estimated_cost_usd=0.06,
    )

    repository.save(summary)

    # デフォルトが False なので、DynamoDB put_item が呼ばれる
    mock_table = mock_dynamodb_resource.Table.return_value
    assert mock_table.put_item.call_count == 1
