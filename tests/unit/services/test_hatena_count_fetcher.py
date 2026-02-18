"""HatenaCountFetcherのユニットテスト."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

from src.services.social_proof.hatena_count_fetcher import HatenaCountFetcher


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

        # 区間マッピングによるスコア検証
        # 100件: 80.0
        # 50件: 65.0
        # 10件: 12.0
        assert len(result) == 3
        assert result["https://example1.com/article1"] == 80.0
        assert result["https://example2.com/article2"] == 65.0
        assert result["https://example3.com/article3"] == 12.0

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
    async def test_score_calculation_interval_mapping(self):
        """区間マッピングスコア計算が正しいことを確認."""
        fetcher = HatenaCountFetcher()

        urls = [
            "https://example.com/zero",
            "https://example.com/one",
            "https://example.com/five",
            "https://example.com/fifteen",
            "https://example.com/thirty",
            "https://example.com/fifty",
            "https://example.com/hundred",
            "https://example.com/two_hundred",
            "https://example.com/five_hundred",
        ]

        mock_response = MagicMock()
        mock_response.json = MagicMock(return_value={
            "https://example.com/zero": 0,
            "https://example.com/one": 1,
            "https://example.com/five": 5,
            "https://example.com/fifteen": 15,
            "https://example.com/thirty": 30,
            "https://example.com/fifty": 50,
            "https://example.com/hundred": 100,
            "https://example.com/two_hundred": 200,
            "https://example.com/five_hundred": 500,
        })

        mock_policy = AsyncMock()
        mock_policy.fetch_with_policy = AsyncMock(return_value=mock_response)

        with patch.object(fetcher, "_policy", mock_policy):
            result = await fetcher.fetch_batch(urls)

        # 区間マッピング検証
        assert result["https://example.com/zero"] == 0.0        # 0件: 0点
        assert result["https://example.com/one"] == 5.0          # 1件: 5点
        assert result["https://example.com/five"] == 12.0        # 5件: 12点
        assert result["https://example.com/fifteen"] == 25.0     # 15件: 25点
        assert result["https://example.com/thirty"] == 50.0      # 30件: 50点
        assert result["https://example.com/fifty"] == 65.0       # 50件: 65点
        assert result["https://example.com/hundred"] == 80.0     # 100件: 80点
        assert result["https://example.com/two_hundred"] == 92.0 # 200件: 92点
        assert result["https://example.com/five_hundred"] == 100.0  # 500件: 100点

    @pytest.mark.asyncio
    async def test_score_calculation_boundary_values(self):
        """区間マッピングの境界値テスト."""
        fetcher = HatenaCountFetcher()

        urls = [
            "https://example.com/four",
            "https://example.com/fourteen",
            "https://example.com/twenty_nine",
            "https://example.com/forty_nine",
            "https://example.com/ninety_nine",
            "https://example.com/one_ninety_nine",
            "https://example.com/four_ninety_nine",
        ]

        mock_response = MagicMock()
        mock_response.json = MagicMock(return_value={
            "https://example.com/four": 4,            # 1〜4の上限
            "https://example.com/fourteen": 14,        # 5〜14の上限
            "https://example.com/twenty_nine": 29,     # 15〜29の上限
            "https://example.com/forty_nine": 49,      # 30〜49の上限
            "https://example.com/ninety_nine": 99,     # 50〜99の上限
            "https://example.com/one_ninety_nine": 199, # 100〜199の上限
            "https://example.com/four_ninety_nine": 499, # 200〜499の上限
        })

        mock_policy = AsyncMock()
        mock_policy.fetch_with_policy = AsyncMock(return_value=mock_response)

        with patch.object(fetcher, "_policy", mock_policy):
            result = await fetcher.fetch_batch(urls)

        # 各区間の上限値でも同じスコアが返されること
        assert result["https://example.com/four"] == 5.0           # 1〜4件: 5点
        assert result["https://example.com/fourteen"] == 12.0      # 5〜14件: 12点
        assert result["https://example.com/twenty_nine"] == 25.0   # 15〜29件: 25点
        assert result["https://example.com/forty_nine"] == 50.0    # 30〜49件: 50点
        assert result["https://example.com/ninety_nine"] == 65.0   # 50〜99件: 65点
        assert result["https://example.com/one_ninety_nine"] == 80.0   # 100〜199件: 80点
        assert result["https://example.com/four_ninety_nine"] == 92.0  # 200〜499件: 92点

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
        from src.services.social_proof.external_service_policy import (
            ExternalServicePolicy,
        )
        assert isinstance(fetcher._policy, ExternalServicePolicy)

    @pytest.mark.asyncio
    async def test_empty_urls(self):
        """空のURLリストで空の辞書が返される."""
        fetcher = HatenaCountFetcher()

        result = await fetcher.fetch_batch([])

        assert result == {}
