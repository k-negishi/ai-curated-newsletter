"""通知エラー例外モジュール."""


class NotificationError(Exception):
    """通知エラー.

    メール送信（SES）に失敗した場合に発生する.
    このエラーは致命的で、実行を中断する.
    """
