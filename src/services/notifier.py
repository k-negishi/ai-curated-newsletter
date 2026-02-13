"""メール通知サービスモジュール."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from src.shared.exceptions.notification_error import NotificationError
from src.shared.logging.logger import get_logger, mask_email
from src.shared.utils.date_utils import now_utc

logger = get_logger(__name__)


@dataclass
class NotificationResult:
    """通知結果.

    Attributes:
        message_id: SESメッセージID
        sent_at: 送信日時（UTC）
    """

    message_id: str
    sent_at: datetime


class Notifier:
    """メール通知サービス.

    AWS SESを使用してメールを送信する.

    Attributes:
        _ses_client: SESクライアント
        _from_email: 送信元メールアドレス
        _to_email: 送信先メールアドレス
        _dry_run: ドライランモード（true の場合メール送信をスキップ）
    """

    def __init__(
        self, ses_client: Any, from_email: str, to_email: str, dry_run: bool = False
    ) -> None:
        """通知サービスを初期化する.

        Args:
            ses_client: SESクライアント（boto3.client('ses')）
            from_email: 送信元メールアドレス
            to_email: 送信先メールアドレス
            dry_run: ドライランモード（デフォルト: False）
        """
        self._ses_client = ses_client
        self._from_email = from_email
        self._to_email = to_email
        self._dry_run = dry_run

    def send(self, subject: str, body: str) -> NotificationResult:
        """メールを送信する.

        dry_run=true の場合、メール送信をスキップします。

        Args:
            subject: メール件名
            body: メール本文（プレーンテキスト）

        Returns:
            通知結果

        Raises:
            NotificationError: メール送信に失敗した場合
        """
        logger.info(
            "notification_start",
            from_email=mask_email(self._from_email),
            to_email=mask_email(self._to_email),
            subject=subject,
            dry_run=self._dry_run,
        )

        # dry_run=true の場合、メール送信をスキップ
        if self._dry_run:
            logger.info(
                "notification_skipped",
                reason="dry_run_mode_enabled",
                to_email=mask_email(self._to_email),
            )
            return NotificationResult(message_id="dry-run", sent_at=now_utc())

        try:
            # SES send_email
            response = self._ses_client.send_email(
                Source=self._from_email,
                Destination={"ToAddresses": [self._to_email]},
                Message={
                    "Subject": {"Data": subject, "Charset": "UTF-8"},
                    "Body": {"Text": {"Data": body, "Charset": "UTF-8"}},
                },
            )

            message_id = response["MessageId"]
            sent_at = now_utc()

            logger.info(
                "notification_success",
                message_id=message_id,
                to_email=mask_email(self._to_email),
            )

            return NotificationResult(message_id=message_id, sent_at=sent_at)

        except Exception as e:
            logger.error(
                "notification_failed",
                to_email=mask_email(self._to_email),
                error=str(e),
            )
            raise NotificationError(f"Failed to send email: {e}") from e
