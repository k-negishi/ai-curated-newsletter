"""HatenaCountFetcherのユニットテスト."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

from src.services.hatena_count_fetcher import HatenaCountFetcher


class TestHatenaCountFetcher:
    """HatenaCountFetcherクラスのテスト."""

    @pytest.mark.asyncio
    async def test_fetch_batch_success_under_50(self):
        """/count/entries API呼び出しが成功する（50件以下）."""
        fetcher = HatenaCountFetcher()

        urls = [
            "https://example1.com/article1",
            "https://example2.com/article2",
            "https://example3.com/article3",
        ]

        # モックレスポンス: {"url1": 100, "url2": 50, "url3": 10}
        mock_response = MagicMock()
        mock_response.json = MagicMock(return_value={
            "https://example1.com/article1": 100,
            "https://example2.com/article2": 50,
            "https://example3.com/article3": 10,
        })

        mock_policy = AsyncMock()
        mock_policy.fetch_with_policy = AsyncMock(return_value=mock_response)

        with patch.object(fetcher, "_policy", mock_policy):
            result = await fetcher.fetch_batch(urls)

        # スコア計算の検証
        # 100件: log10(101) * 25 = 50.11
        # 50件: log10(51) * 25 = 42.48
        # 10件: log10(11) * 25 = 25.98
        assert len(result) == 3
        assert 49.0 <= result["https://example1.com/article1"] <= 51.0
        assert 41.0 <= result["https://example2.com/article2"] <= 43.0
        assert 25.0 <= result["https://example3.com/article3"] <= 27.0

    @pytest.mark.asyncio
    async def test_fetch_batch_over_50_urls(self):
        """50件超過時に分割処理される."""
        fetcher = HatenaCountFetcher()

        # 79件のURL（50件 + 29件に分割される）
        urls = [f"https://example.com/article{i}" for i in range(79)]

        # モックレスポンス
        mock_response = MagicMock()
        mock_response.json = MagicMock(return_value={url: i for i, url in enumerate(urls)})

        mock_policy = AsyncMock()
        mock_policy.fetch_with_policy = AsyncMock(return_value=mock_response)

        with patch.object(fetcher, "_policy", mock_policy):
            result = await fetcher.fetch_batch(urls)

        # 2回APIが呼ばれる（50件 + 29件）
        assert mock_policy.fetch_with_policy.call_count == 2

        # 全URLのスコアが返される
        assert len(result) == 79

    @pytest.mark.asyncio
    async def test_score_calculation_log_transform(self):
        """log変換スコア計算が正しい（0件→0, 100件→50, 1000件→75, 10000件→100）."""
        fetcher = HatenaCountFetcher()

        urls = [
            "https://example.com/zero",
            "https://example.com/hundred",
            "https://example.com/thousand",
            "https://example.com/ten_thousand",
        ]

        # モックレスポンス
        mock_response = MagicMock()
        mock_response.json = MagicMock(return_value={
            "https://example.com/zero": 0,
            "https://example.com/hundred": 100,
            "https://example.com/thousand": 1000,
            "https://example.com/ten_thousand": 10000,
        })

        mock_policy = AsyncMock()
        mock_policy.fetch_with_policy = AsyncMock(return_value=mock_response)

        with patch.object(fetcher, "_policy", mock_policy):
            result = await fetcher.fetch_batch(urls)

        # 0件: log10(1) * 25 = 0
        # 100件: log10(101) * 25 = 50.11
        # 1000件: log10(1001) * 25 = 75.00
        # 10000件: min(100, log10(10001) * 25) = 100
        assert result["https://example.com/zero"] == 0.0
        assert 49.0 <= result["https://example.com/hundred"] <= 51.0
        assert 74.0 <= result["https://example.com/thousand"] <= 76.0
        assert result["https://example.com/ten_thousand"] == 100.0

    @pytest.mark.asyncio
    async def test_api_failure_returns_empty_dict(self):
        """API失敗時に空の辞書が返される."""
        fetcher = HatenaCountFetcher()

        urls = ["https://example.com/article1"]

        # API失敗をシミュレート
        mock_policy = AsyncMock()
        mock_policy.fetch_with_policy = AsyncMock(
            side_effect=httpx.HTTPStatusError(
                "Internal Server Error",
                request=MagicMock(),
                response=MagicMock(status_code=500),
            )
        )

        with patch.object(fetcher, "_policy", mock_policy):
            result = await fetcher.fetch_batch(urls)

        # 失敗時は空の辞書が返される
        assert result == {}

    @pytest.mark.asyncio
    async def test_external_service_policy_applied(self):
        """ExternalServicePolicyが適用されていることを確認."""
        fetcher = HatenaCountFetcher()

        # _policyがExternalServicePolicyのインスタンスであることを確認
        from src.services.external_service_policy import ExternalServicePolicy
        assert isinstance(fetcher._policy, ExternalServicePolicy)

    @pytest.mark.asyncio
    async def test_empty_urls(self):
        """空のURLリストで空の辞書が返される."""
        fetcher = HatenaCountFetcher()

        result = await fetcher.fetch_batch([])

        assert result == {}
