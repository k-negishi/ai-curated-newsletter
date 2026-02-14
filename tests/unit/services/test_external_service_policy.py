"""ExternalServicePolicyのユニットテスト."""

import asyncio
import pytest
import time
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

from src.services.external_service_policy import ExternalServicePolicy


class TestExternalServicePolicy:
    """ExternalServicePolicyクラスのテスト."""

    @pytest.mark.asyncio
    async def test_same_domain_concurrency_limit(self):
        """同一ドメイン同時接続制限が1接続に制限される."""
        policy = ExternalServicePolicy(
            domain_concurrency=1,
            total_concurrency=3,
            jitter_range=(0.0, 0.0),  # jitterを無効化
        )

        # 同一ドメインに対する並列リクエスト
        urls = [
            "https://example.com/page1",
            "https://example.com/page2",
            "https://example.com/page3",
        ]

        # リクエストの開始時刻を記録
        start_times = []

        async def mock_request(url: str, timeout: int):
            start_times.append(time.time())
            await asyncio.sleep(0.1)  # 100ms待機
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.raise_for_status = MagicMock()
            return mock_response

        # httpx.AsyncClient全体をモック化
        mock_client = AsyncMock()
        mock_client.get = mock_request

        tasks = [policy.fetch_with_policy(url, mock_client) for url in urls]
        await asyncio.gather(*tasks)

        # 同時接続制限が1なので、リクエストは直列に実行されるべき
        # 2つ目のリクエストは1つ目の完了後に開始される（100ms以上の差）
        assert len(start_times) == 3
        assert start_times[1] - start_times[0] >= 0.09  # 100ms - 誤差

    @pytest.mark.asyncio
    async def test_total_concurrency_limit(self):
        """全体同時接続制限が3接続に制限される."""
        policy = ExternalServicePolicy(
            domain_concurrency=3,
            total_concurrency=3,
            jitter_range=(0.0, 0.0),  # jitterを無効化
        )

        # 異なるドメインに対する並列リクエスト（4つ）
        urls = [
            "https://domain1.com/page",
            "https://domain2.com/page",
            "https://domain3.com/page",
            "https://domain4.com/page",
        ]

        # リクエストの開始時刻を記録
        start_times = []

        async def mock_request(url: str, timeout: int):
            start_times.append(time.time())
            await asyncio.sleep(0.1)  # 100ms待機
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.raise_for_status = MagicMock()
            return mock_response

        mock_client = AsyncMock()
        mock_client.get = mock_request

        tasks = [policy.fetch_with_policy(url, mock_client) for url in urls]
        await asyncio.gather(*tasks)

        # 全体同時接続制限が3なので、4つ目のリクエストは3つ目の完了後に開始
        assert len(start_times) == 4
        # 最初の3つはほぼ同時に開始
        assert start_times[2] - start_times[0] < 0.05
        # 4つ目は最初の3つの完了後に開始（100ms以上後）
        assert start_times[3] - start_times[0] >= 0.09

    @pytest.mark.asyncio
    async def test_jitter_between_requests(self):
        """リクエスト間隔が3〜6秒のjitterで制御される."""
        policy = ExternalServicePolicy(jitter_range=(0.1, 0.2))  # テスト用に短縮

        urls = [
            "https://example.com/page1",
            "https://example.com/page2",
        ]

        request_times = []

        async def mock_request(url: str, timeout: int):
            request_times.append(time.time())
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.raise_for_status = MagicMock()
            return mock_response

        mock_client = AsyncMock()
        mock_client.get = mock_request

        # 直列に実行
        for url in urls:
            await policy.fetch_with_policy(url, mock_client)

        # 2つ目のリクエストは1つ目から0.1〜0.2秒後に開始
        interval = request_times[1] - request_times[0]
        assert 0.09 <= interval <= 0.25  # 誤差を考慮

    @pytest.mark.asyncio
    async def test_timeout_setting(self):
        """タイムアウトが5秒に設定される."""
        policy = ExternalServicePolicy(
            timeout=5,
            jitter_range=(0.0, 0.0),  # jitterを無効化
        )

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(
            side_effect=httpx.TimeoutException("Timeout")
        )

        with pytest.raises(httpx.TimeoutException):
            await policy.fetch_with_policy("https://example.com", mock_client)

    @pytest.mark.asyncio
    async def test_retry_strategy_429(self):
        """429エラー時にリトライ戦略（2s→4s→8s）が適用される."""
        policy = ExternalServicePolicy(
            retry_delays=[0.1, 0.2, 0.4],  # テスト用に短縮
            jitter_range=(0.0, 0.0),  # jitterを無効化
        )

        call_count = 0
        retry_times = []

        async def mock_request(url: str, timeout: int):
            nonlocal call_count
            retry_times.append(time.time())
            call_count += 1

            if call_count < 4:
                # 最初の3回は429エラー
                mock_response = MagicMock()
                mock_response.status_code = 429
                raise httpx.HTTPStatusError(
                    "Too Many Requests",
                    request=MagicMock(),
                    response=mock_response
                )
            else:
                # 4回目は成功
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.raise_for_status = MagicMock()
                return mock_response

        mock_client = AsyncMock()
        mock_client.get = mock_request

        result = await policy.fetch_with_policy("https://example.com", mock_client)

        # 4回リクエストが実行される（初回 + 3回リトライ）
        assert call_count == 4
        assert result.status_code == 200

        # リトライ間隔の確認（0.1s, 0.2s, 0.4s）
        assert retry_times[1] - retry_times[0] >= 0.09  # 0.1s
        assert retry_times[2] - retry_times[1] >= 0.19  # 0.2s
        assert retry_times[3] - retry_times[2] >= 0.39  # 0.4s

    @pytest.mark.asyncio
    async def test_retry_strategy_5xx(self):
        """5xxエラー時にリトライされる."""
        policy = ExternalServicePolicy(
            retry_delays=[0.1, 0.2],  # 2回リトライ
            jitter_range=(0.0, 0.0),  # jitterを無効化
        )

        call_count = 0

        async def mock_request(url: str, timeout: int):
            nonlocal call_count
            call_count += 1

            if call_count < 3:
                # 最初の2回は500エラー
                mock_response = MagicMock()
                mock_response.status_code = 500
                raise httpx.HTTPStatusError(
                    "Internal Server Error",
                    request=MagicMock(),
                    response=mock_response
                )
            else:
                # 3回目は成功
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.raise_for_status = MagicMock()
                return mock_response

        mock_client = AsyncMock()
        mock_client.get = mock_request

        result = await policy.fetch_with_policy("https://example.com", mock_client)

        assert call_count == 3
        assert result.status_code == 200

    @pytest.mark.asyncio
    async def test_no_retry_for_4xx_except_429(self):
        """429以外の4xxエラー時にリトライされない."""
        policy = ExternalServicePolicy(
            retry_delays=[0.1, 0.2, 0.4],
            jitter_range=(0.0, 0.0),  # jitterを無効化
        )

        call_count = 0

        async def mock_request(url: str, timeout: int):
            nonlocal call_count
            call_count += 1

            # 404エラー
            mock_response = MagicMock()
            mock_response.status_code = 404
            raise httpx.HTTPStatusError(
                "Not Found",
                request=MagicMock(),
                response=mock_response
            )

        mock_client = AsyncMock()
        mock_client.get = mock_request

        with pytest.raises(httpx.HTTPStatusError):
            await policy.fetch_with_policy("https://example.com", mock_client)

        # リトライされず、1回だけ実行される
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self):
        """最大リトライ回数を超えた場合にエラーが発生する."""
        policy = ExternalServicePolicy(
            retry_delays=[0.1, 0.2],  # 2回リトライ
            jitter_range=(0.0, 0.0),  # jitterを無効化
        )

        call_count = 0

        async def mock_request(url: str, timeout: int):
            nonlocal call_count
            call_count += 1

            # 常に429エラー
            mock_response = MagicMock()
            mock_response.status_code = 429
            raise httpx.HTTPStatusError(
                "Too Many Requests",
                request=MagicMock(),
                response=mock_response
            )

        mock_client = AsyncMock()
        mock_client.get = mock_request

        with pytest.raises(httpx.HTTPStatusError):
            await policy.fetch_with_policy("https://example.com", mock_client)

        # 初回 + 2回リトライ = 3回実行される
        assert call_count == 3
