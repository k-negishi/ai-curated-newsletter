"""通知フローの統合テスト."""

from unittest.mock import Mock

import pytest

from src.services.formatter import Formatter
from src.services.notifier import Notifier


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
        to_email="recipient@example.com",
    )

    subject = "Test Newsletter"
    body = "This is a test newsletter body."

    result = notifier.send(subject=subject, body=body)

    # 結果検証
    assert result.message_id == "test-message-id"
    assert result.sent_at is not None

    # SES send_email が呼ばれることを確認
    assert mock_ses_client.send_email.call_count == 1

    # 呼び出し引数の検証
    call_args = mock_ses_client.send_email.call_args[1]
    assert call_args["Source"] == "sender@example.com"
    assert call_args["Destination"]["ToAddresses"] == ["recipient@example.com"]
    assert call_args["Message"]["Subject"]["Data"] == subject
    assert call_args["Message"]["Body"]["Text"]["Data"] == body


@pytest.mark.asyncio
async def test_notification_flow_error_handling(mock_ses_client) -> None:
    """通知エラーが適切にハンドリングされることを確認."""
    # SESエラーをシミュレート
    mock_ses_client.send_email.side_effect = Exception("SES API error")

    notifier = Notifier(
        ses_client=mock_ses_client,
        from_email="sender@example.com",
        to_email="recipient@example.com",
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
        to_email="recipient@example.com",
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
