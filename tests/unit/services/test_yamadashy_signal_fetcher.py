"""YamadashySignalFetcherのユニットテスト."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

from src.services.yamadashy_signal_fetcher import YamadashySignalFetcher


class TestYamadashySignalFetcher:
    """YamadashySignalFetcherクラスのテスト."""

    @pytest.mark.asyncio
    async def test_fetch_signals_success_with_match(self):
        """yamadashy RSS取得成功時、掲載記事のシグナルが100になる."""
        fetcher = YamadashySignalFetcher()

        urls = [
            "https://example.com/article1",  # 掲載あり
            "https://example.com/article2",  # 掲載なし
        ]

        # モックレスポンス（RSS）
        mock_response = MagicMock()
        mock_response.text = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <item>
      <link>https://example.com/article1</link>
      <title>Article 1</title>
    </item>
  </channel>
</rss>"""

        mock_policy = AsyncMock()
        mock_policy.fetch_with_policy = AsyncMock(return_value=mock_response)

        with patch.object(fetcher, "_policy", mock_policy):
            result = await fetcher.fetch_signals(urls)

        # 掲載されている記事は100、されていない記事は0
        assert result["https://example.com/article1"] == 100
        assert result["https://example.com/article2"] == 0

    @pytest.mark.asyncio
    async def test_fetch_signals_no_match(self):
        """yamadashy RSSに掲載されていない記事のシグナルは0になる."""
        fetcher = YamadashySignalFetcher()

        urls = [
            "https://example.com/article1",
            "https://example.com/article2",
        ]

        # モックレスポンス（空のRSS）
        mock_response = MagicMock()
        mock_response.text = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
  </channel>
</rss>"""

        mock_policy = AsyncMock()
        mock_policy.fetch_with_policy = AsyncMock(return_value=mock_response)

        with patch.object(fetcher, "_policy", mock_policy):
            result = await fetcher.fetch_signals(urls)

        # 全て掲載されていないので0
        assert result["https://example.com/article1"] == 0
        assert result["https://example.com/article2"] == 0

    @pytest.mark.asyncio
    async def test_fetch_signals_rss_fetch_failure(self):
        """yamadashy RSS取得失敗時、全てのシグナルが0になる."""
        fetcher = YamadashySignalFetcher()

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
            result = await fetcher.fetch_signals(urls)

        # 失敗時は全て0
        assert result["https://example.com/article1"] == 0

    @pytest.mark.asyncio
    async def test_external_service_policy_applied(self):
        """ExternalServicePolicyが適用されていることを確認."""
        fetcher = YamadashySignalFetcher()

        # _policyがExternalServicePolicyのインスタンスであることを確認
        from src.services.external_service_policy import ExternalServicePolicy
        assert isinstance(fetcher._policy, ExternalServicePolicy)

    @pytest.mark.asyncio
    async def test_empty_urls(self):
        """空のURLリストで空の辞書が返される."""
        fetcher = YamadashySignalFetcher()

        result = await fetcher.fetch_signals([])

        assert result == {}

    @pytest.mark.asyncio
    async def test_url_normalization(self):
        """URLの正規化が正しく行われる."""
        fetcher = YamadashySignalFetcher()

        # 異なる形式のURLだが、正規化後は同じ
        urls = [
            "https://example.com/article1/",  # 末尾スラッシュあり
            "https://example.com/article2",   # 末尾スラッシュなし
        ]

        # モックレスポンス（RSS内のURLも末尾スラッシュなし）
        mock_response = MagicMock()
        mock_response.text = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <item>
      <link>https://example.com/article1</link>
      <title>Article 1</title>
    </item>
  </channel>
</rss>"""

        mock_policy = AsyncMock()
        mock_policy.fetch_with_policy = AsyncMock(return_value=mock_response)

        with patch.object(fetcher, "_policy", mock_policy):
            result = await fetcher.fetch_signals(urls)

        # 正規化により、article1はマッチする
        assert result["https://example.com/article1/"] == 100
        assert result["https://example.com/article2"] == 0
