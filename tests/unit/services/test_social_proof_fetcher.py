"""SocialProofFetcherのユニットテスト."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

from src.services.social_proof_fetcher import SocialProofFetcher


class TestSocialProofFetcher:
    """SocialProofFetcherクラスのテスト."""

    @pytest.mark.asyncio
    async def test_fetch_single_batch_success(self):
        """_fetch_single_batch: 正常レスポンスでURLごとの件数を返す."""
        fetcher = SocialProofFetcher(timeout=5)
        urls = ["https://example1.com", "https://example2.com"]

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.raise_for_status = MagicMock()
            mock_response.json = MagicMock(
                return_value={
                    "https://example1.com": 42,
                    "https://example2.com": 10,
                }
            )

            mock_get = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value.get = mock_get

            counts = await fetcher._fetch_single_batch(urls)

            assert counts == {
                "https://example1.com": 42,
                "https://example2.com": 10,
            }
            called_url = mock_get.call_args.args[0]
            assert "count/entries" in called_url
            assert "url=https%3A%2F%2Fexample1.com" in called_url
            assert "url=https%3A%2F%2Fexample2.com" in called_url

    @pytest.mark.asyncio
    async def test_fetch_single_batch_http_error(self):
        """_fetch_single_batch: HTTPエラー時は例外を送出する."""
        fetcher = SocialProofFetcher(timeout=5)

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=httpx.HTTPStatusError(
                    "Error", request=MagicMock(), response=MagicMock()
                )
            )

            with pytest.raises(httpx.HTTPError):
                await fetcher._fetch_single_batch(["https://example.com"])

    @pytest.mark.asyncio
    async def test_fetch_batch_success_under_50(self):
        """fetch_batch: 50件以下は1バッチで取得される."""
        fetcher = SocialProofFetcher(timeout=5, concurrency_limit=3)
        urls = [
            "https://example1.com",
            "https://example2.com",
            "https://example3.com",
        ]

        with patch.object(fetcher, "_fetch_single_batch") as mock_fetch_batch:
            mock_fetch_batch.return_value = {
                "https://example1.com": 10,
                "https://example2.com": 20,
                "https://example3.com": 30,
            }

            result = await fetcher.fetch_batch(urls)

            assert result == {
                "https://example1.com": 10,
                "https://example2.com": 20,
                "https://example3.com": 30,
            }
            assert mock_fetch_batch.call_count == 1

    @pytest.mark.asyncio
    async def test_fetch_batch_over_50_urls(self):
        """fetch_batch: 50件超過時は分割される."""
        fetcher = SocialProofFetcher(timeout=5, concurrency_limit=2)
        urls = [f"https://example.com/article{i}" for i in range(79)]

        first_batch_result = {url: i for i, url in enumerate(urls[:50])}
        second_batch_result = {url: i for i, url in enumerate(urls[50:], start=50)}
        with patch.object(fetcher, "_fetch_single_batch") as mock_fetch_batch:
            mock_fetch_batch.side_effect = [first_batch_result, second_batch_result]

            result = await fetcher.fetch_batch(urls)

            assert len(result) == 79
            assert mock_fetch_batch.call_count == 2

    @pytest.mark.asyncio
    async def test_fetch_batch_partial_failure(self):
        """fetch_batch: 一部バッチ失敗時も他バッチを返す."""
        fetcher = SocialProofFetcher(timeout=5, concurrency_limit=2)
        urls = [f"https://example.com/article{i}" for i in range(60)]

        success_batch = {url: i for i, url in enumerate(urls[:50])}

        with patch.object(fetcher, "_fetch_single_batch") as mock_fetch_batch:
            mock_fetch_batch.side_effect = [success_batch, Exception("Error")]

            result = await fetcher.fetch_batch(urls)

            assert result == success_batch
            assert mock_fetch_batch.call_count == 2

    @pytest.mark.asyncio
    async def test_fetch_batch_empty_urls(self):
        """fetch_batch: 空のURLリストで空の辞書が返される."""
        fetcher = SocialProofFetcher(timeout=5)

        result = await fetcher.fetch_batch([])

        assert result == {}
