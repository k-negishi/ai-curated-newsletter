"""外部サービス利用ポリシーモジュール."""

import asyncio
import random
import time
from urllib.parse import urlparse

import httpx

from src.shared.logging.logger import get_logger

logger = get_logger(__name__)


class ExternalServicePolicy:
    """外部サービス利用ポリシー.

    外部APIへのリクエストに対して以下のポリシーを適用する:
    - 同一ドメイン同時接続制限
    - 全体同時接続制限
    - リクエスト間隔（jitter）
    - タイムアウト
    - リトライ戦略（429 / 5xx のみ）

    Attributes:
        _domain_concurrency: 同一ドメイン同時接続数
        _total_concurrency: 全体同時接続数
        _jitter_range: リクエスト間隔のjitter範囲（秒）
        _timeout: タイムアウト（秒）
        _retry_delays: リトライ間隔リスト（秒）
        _total_semaphore: 全体同時接続制限用のセマフォ
        _domain_semaphores: ドメインごとの同時接続制限用セマフォ
        _last_request_time: 最後のリクエスト時刻
    """

    def __init__(
        self,
        domain_concurrency: int = 1,
        total_concurrency: int = 3,
        jitter_range: tuple[float, float] = (3.0, 6.0),
        timeout: int = 5,
        retry_delays: list[float] | None = None,
    ) -> None:
        """外部サービス利用ポリシーを初期化する.

        Args:
            domain_concurrency: 同一ドメイン同時接続数（デフォルト: 1）
            total_concurrency: 全体同時接続数（デフォルト: 3）
            jitter_range: リクエスト間隔のjitter範囲（秒、デフォルト: 3.0〜6.0）
            timeout: タイムアウト（秒、デフォルト: 5）
            retry_delays: リトライ間隔リスト（秒、デフォルト: [2.0, 4.0, 8.0]）
        """
        self._domain_concurrency = domain_concurrency
        self._total_concurrency = total_concurrency
        self._jitter_range = jitter_range
        self._timeout = timeout
        self._retry_delays = retry_delays if retry_delays is not None else [2.0, 4.0, 8.0]

        # 同時接続制限用のセマフォ
        self._total_semaphore = asyncio.Semaphore(total_concurrency)
        self._domain_semaphores: dict[str, asyncio.Semaphore] = {}

        # jitter管理用
        self._last_request_time: float | None = None
        self._request_lock = asyncio.Lock()

    def _get_domain_semaphore(self, url: str) -> asyncio.Semaphore:
        """URLのドメインに対応するセマフォを取得する.

        Args:
            url: リクエストURL

        Returns:
            ドメインごとのセマフォ
        """
        domain = urlparse(url).netloc

        if domain not in self._domain_semaphores:
            self._domain_semaphores[domain] = asyncio.Semaphore(self._domain_concurrency)

        return self._domain_semaphores[domain]

    async def _apply_jitter(self) -> None:
        """リクエスト間隔のjitterを適用する.

        前回のリクエストから指定された時間（jitter_range）が経過していない場合、待機する。
        """
        async with self._request_lock:
            if self._last_request_time is not None:
                elapsed = time.time() - self._last_request_time
                jitter = random.uniform(*self._jitter_range)

                if elapsed < jitter:
                    wait_time = jitter - elapsed
                    logger.debug("applying_jitter", wait_time=wait_time)
                    await asyncio.sleep(wait_time)

            self._last_request_time = time.time()

    async def fetch_with_policy(self, url: str, client: httpx.AsyncClient) -> httpx.Response:
        """外部サービス利用ポリシーを適用してHTTPリクエストを実行する.

        Args:
            url: リクエストURL
            client: httpxクライアント

        Returns:
            HTTPレスポンス

        Raises:
            httpx.HTTPError: リトライ後も失敗した場合
        """
        domain_semaphore = self._get_domain_semaphore(url)

        # 同時接続制限とjitterを適用
        async with self._total_semaphore, domain_semaphore:
            await self._apply_jitter()

            # リトライロジック（初回 + retry_delays回数分リトライ）
            max_attempts = len(self._retry_delays) + 1
            for attempt in range(max_attempts):
                # リトライ時は待機
                if attempt > 0:
                    delay = self._retry_delays[attempt - 1]
                    logger.info("retrying_request", url=url, attempt=attempt, delay=delay)
                    await asyncio.sleep(delay)

                try:
                    response = await client.get(url, timeout=self._timeout)
                    response.raise_for_status()
                    return response

                except httpx.HTTPStatusError as e:
                    status_code = e.response.status_code
                    is_last_attempt = attempt >= len(self._retry_delays)

                    # 429 / 5xx のみリトライ対象
                    if status_code == 429 or 500 <= status_code < 600:
                        logger.warning(
                            "http_error_retryable",
                            url=url,
                            status_code=status_code,
                            attempt=attempt,
                        )

                        # 最後のリトライでもエラーの場合は例外を再送出
                        if is_last_attempt:
                            raise
                    else:
                        # 429 / 5xx 以外はリトライしない
                        logger.warning(
                            "http_error_not_retryable",
                            url=url,
                            status_code=status_code,
                        )
                        raise

                except httpx.TimeoutException:
                    is_last_attempt = attempt >= len(self._retry_delays)
                    logger.warning("request_timeout", url=url, attempt=attempt)

                    # タイムアウトもリトライ対象
                    if is_last_attempt:
                        raise

            # ここには到達しないが、型チェッカーのために必要
            raise RuntimeError("Unexpected code path")
