"""通知フローの統合テスト."""

from unittest.mock import Mock

import pytest

from src.services.formatter import Formatter
from src.services.notifier import Notifier
from src.shared.exceptions.notification_error import NotificationError


@pytest.fixture
def mock_ses_client():
    """モックのSESクライアントを返す."""
    mock_ses = Mock()
    mock_ses.send_email.return_value = {"MessageId": "test-message-id"}
    return mock_ses


@pytest.mark.asyncio
async def test_notification_flow_success(mock_ses_client) -> None:
    """通知フローが正常に動作することを確認."""
    notifier = Notifier(
        ses_client=mock_ses_client,
        from_email="sender@example.com",
        to_email=["recipient@example.com"],
    )

    subject = "Test Newsletter"
    body = "This is a test newsletter body."

    result = notifier.send(subject=subject, body=body)

    # 結果検証
    assert result.message_id == "test-message-id"
    assert result.sent_at is not None

    # SES send_email が1回呼ばれることを確認
    assert mock_ses_client.send_email.call_count == 1

    # 呼び出し引数の検証（個別送信のため単一アドレスで送信される）
    call_args = mock_ses_client.send_email.call_args[1]
    assert call_args["Source"] == "sender@example.com"
    assert call_args["Destination"]["ToAddresses"] == ["recipient@example.com"]
    assert call_args["Message"]["Subject"]["Data"] == subject
    assert call_args["Message"]["Body"]["Text"]["Data"] == body


@pytest.mark.asyncio
async def test_notification_flow_multiple_recipients(mock_ses_client) -> None:
    """複数アドレスへの配信が個別送信で動作することを確認."""
    notifier = Notifier(
        ses_client=mock_ses_client,
        from_email="sender@example.com",
        to_email=["a@example.com", "b@example.com"],
    )

    result = notifier.send(subject="Multi-recipient Test", body="body text")

    assert result.message_id == "test-message-id"

    # 各アドレスに個別送信されることを確認
    assert mock_ses_client.send_email.call_count == 2
    calls = mock_ses_client.send_email.call_args_list
    assert calls[0][1]["Destination"]["ToAddresses"] == ["a@example.com"]
    assert calls[1][1]["Destination"]["ToAddresses"] == ["b@example.com"]


@pytest.mark.asyncio
async def test_notification_flow_partial_failure() -> None:
    """1件失敗しても他のアドレスへの送信が継続されることを確認."""
    mock_ses_client = Mock()
    mock_ses_client.send_email.side_effect = [
        {"MessageId": "msg-success"},
        Exception("MessageRejected: Email address is not verified"),
    ]

    notifier = Notifier(
        ses_client=mock_ses_client,
        from_email="sender@example.com",
        to_email=["verified@example.com", "unverified@example.com"],
    )

    # 1件成功しているので NotificationError は発生しない
    result = notifier.send(subject="Test", body="body text")

    assert result.message_id == "msg-success"
    # 両アドレスに send_email が試みられたことを確認
    assert mock_ses_client.send_email.call_count == 2


@pytest.mark.asyncio
async def test_notification_flow_all_fail() -> None:
    """全件失敗した場合に NotificationError が発生することを確認."""
    mock_ses_client = Mock()
    mock_ses_client.send_email.side_effect = Exception("MessageRejected")

    notifier = Notifier(
        ses_client=mock_ses_client,
        from_email="sender@example.com",
        to_email=["a@example.com", "b@example.com"],
    )

    with pytest.raises(NotificationError, match="Failed to send email to all recipients"):
        notifier.send(subject="Test", body="body text")

    # 両アドレスとも試みたことを確認
    assert mock_ses_client.send_email.call_count == 2


@pytest.mark.asyncio
async def test_notification_flow_error_handling(mock_ses_client) -> None:
    """通知エラーが適切にハンドリングされることを確認."""
    # SESエラーをシミュレート
    mock_ses_client.send_email.side_effect = Exception("SES API error")

    notifier = Notifier(
        ses_client=mock_ses_client,
        from_email="sender@example.com",
        to_email=["recipient@example.com"],
    )

    subject = "Test Newsletter"
    body = "This is a test newsletter body."

    # エラーが発生した場合、NotificationErrorが発生することを確認
    with pytest.raises(Exception) as exc_info:
        notifier.send(subject=subject, body=body)

    assert "SES API error" in str(exc_info.value)


@pytest.mark.asyncio
async def test_notification_flow_with_html_body(mock_ses_client) -> None:
    """HTML本文が指定された場合、SESペイロードにHtmlパートが含まれることを確認."""
    notifier = Notifier(
        ses_client=mock_ses_client,
        from_email="sender@example.com",
        to_email=["recipient@example.com"],
    )

    result = notifier.send(
        subject="Test Newsletter",
        body="This is a test newsletter body.",
        html_body="<html><body><p>This is html.</p></body></html>",
    )

    assert result.message_id == "test-message-id"

    call_args = mock_ses_client.send_email.call_args[1]
    assert call_args["Message"]["Body"]["Text"]["Data"] == "This is a test newsletter body."
    assert call_args["Message"]["Body"]["Html"]["Data"] == (
        "<html><body><p>This is html.</p></body></html>"
    )
