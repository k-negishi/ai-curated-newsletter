"""構造化ログ設定モジュール."""

import logging
import sys
from typing import Any

import structlog
import structlog.contextvars


def mask_email(email: str) -> str:
    """メールアドレスをマスクする.

    Args:
        email: マスク対象のメールアドレス

    Returns:
        マスクされたメールアドレス（例: "us***@example.com"）

    Examples:
        >>> mask_email("user@example.com")
        'us***@example.com'
        >>> mask_email("a@b.com")
        'a***@b.com'
    """
    if "@" not in email:
        return "***"

    local, domain = email.split("@", 1)
    masked_local = local[0] + "***" if len(local) <= 2 else local[:2] + "***"
    return f"{masked_local}@{domain}"


def configure_logging(log_level: str = "INFO", run_id: str | None = None) -> None:
    """構造化ログを設定する.

    Args:
        log_level: ログレベル（DEBUG, INFO, WARNING, ERROR, CRITICAL）
        run_id: 実行ID（ログコンテキストに含める）

    Examples:
        >>> configure_logging(log_level="INFO", run_id="550e8400-e29b-41d4")
    """
    # 標準ロギングの設定
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper()),
    )

    # structlogプロセッサーの設定
    processors: list[Any] = [
        # コンテキスト変数をマージ
        structlog.contextvars.merge_contextvars,
        # イベント辞書をマージ
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        # タイムスタンプ追加
        structlog.processors.TimeStamper(fmt="iso"),
        # スタック情報追加（エラー時）
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        # JSON形式で出力
        structlog.processors.JSONRenderer(),
    ]

    # structlogの設定
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # run_idをコンテキストにバインド
    if run_id:
        structlog.contextvars.bind_contextvars(run_id=run_id)


def get_logger(name: str | None = None) -> Any:
    """構造化ロガーを取得する.

    Args:
        name: ロガー名（省略時はルートロガー）

    Returns:
        structlogロガー

    Examples:
        >>> logger = get_logger(__name__)
        >>> logger.info("test_event", key="value")
    """
    return structlog.get_logger(name)
