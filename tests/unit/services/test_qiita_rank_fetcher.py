"""QiitaRankFetcherのユニットテスト."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

from src.services.qiita_rank_fetcher import QiitaRankFetcher


class TestQiitaRankFetcher:
    """QiitaRankFetcherクラスのテスト."""

    @pytest.mark.asyncio
    async def test_fetch_batch_success(self):
        """Qiita popular feed取得成功し、順位が正しくスコア化される."""
        fetcher = QiitaRankFetcher()

        urls = [
            "https://qiita.com/user1/items/item5",   # 5位 → 100点
            "https://qiita.com/user2/items/item15",  # 15位 → 70点
            "https://qiita.com/user3/items/item25",  # 25位 → 40点
            "https://qiita.com/user4/items/item35",  # 35位 → 20点
            "https://qiita.com/user5/items/item55",  # 55位 → 0点
        ]

        # モックレスポンス（Qiita popular feed）
        mock_response = MagicMock()
        mock_response.text = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry><link href="https://qiita.com/user/items/item1"/></entry>
  <entry><link href="https://qiita.com/user/items/item2"/></entry>
  <entry><link href="https://qiita.com/user/items/item3"/></entry>
  <entry><link href="https://qiita.com/user/items/item4"/></entry>
  <entry><link href="https://qiita.com/user1/items/item5"/></entry>
  <entry><link href="https://qiita.com/user/items/item6"/></entry>
  <entry><link href="https://qiita.com/user/items/item7"/></entry>
  <entry><link href="https://qiita.com/user/items/item8"/></entry>
  <entry><link href="https://qiita.com/user/items/item9"/></entry>
  <entry><link href="https://qiita.com/user/items/item10"/></entry>
  <entry><link href="https://qiita.com/user/items/item11"/></entry>
  <entry><link href="https://qiita.com/user/items/item12"/></entry>
  <entry><link href="https://qiita.com/user/items/item13"/></entry>
  <entry><link href="https://qiita.com/user/items/item14"/></entry>
  <entry><link href="https://qiita.com/user2/items/item15"/></entry>
  <entry><link href="https://qiita.com/user/items/item16"/></entry>
  <entry><link href="https://qiita.com/user/items/item17"/></entry>
  <entry><link href="https://qiita.com/user/items/item18"/></entry>
  <entry><link href="https://qiita.com/user/items/item19"/></entry>
  <entry><link href="https://qiita.com/user/items/item20"/></entry>
  <entry><link href="https://qiita.com/user/items/item21"/></entry>
  <entry><link href="https://qiita.com/user/items/item22"/></entry>
  <entry><link href="https://qiita.com/user/items/item23"/></entry>
  <entry><link href="https://qiita.com/user/items/item24"/></entry>
  <entry><link href="https://qiita.com/user3/items/item25"/></entry>
  <entry><link href="https://qiita.com/user/items/item26"/></entry>
  <entry><link href="https://qiita.com/user/items/item27"/></entry>
  <entry><link href="https://qiita.com/user/items/item28"/></entry>
  <entry><link href="https://qiita.com/user/items/item29"/></entry>
  <entry><link href="https://qiita.com/user/items/item30"/></entry>
  <entry><link href="https://qiita.com/user/items/item31"/></entry>
  <entry><link href="https://qiita.com/user/items/item32"/></entry>
  <entry><link href="https://qiita.com/user/items/item33"/></entry>
  <entry><link href="https://qiita.com/user/items/item34"/></entry>
  <entry><link href="https://qiita.com/user4/items/item35"/></entry>
  <entry><link href="https://qiita.com/user/items/item36"/></entry>
  <entry><link href="https://qiita.com/user/items/item37"/></entry>
  <entry><link href="https://qiita.com/user/items/item38"/></entry>
  <entry><link href="https://qiita.com/user/items/item39"/></entry>
  <entry><link href="https://qiita.com/user/items/item40"/></entry>
  <entry><link href="https://qiita.com/user/items/item41"/></entry>
  <entry><link href="https://qiita.com/user/items/item42"/></entry>
  <entry><link href="https://qiita.com/user/items/item43"/></entry>
  <entry><link href="https://qiita.com/user/items/item44"/></entry>
  <entry><link href="https://qiita.com/user/items/item45"/></entry>
  <entry><link href="https://qiita.com/user/items/item46"/></entry>
  <entry><link href="https://qiita.com/user/items/item47"/></entry>
  <entry><link href="https://qiita.com/user/items/item48"/></entry>
  <entry><link href="https://qiita.com/user/items/item49"/></entry>
  <entry><link href="https://qiita.com/user/items/item50"/></entry>
  <entry><link href="https://qiita.com/user/items/item51"/></entry>
  <entry><link href="https://qiita.com/user/items/item52"/></entry>
  <entry><link href="https://qiita.com/user/items/item53"/></entry>
  <entry><link href="https://qiita.com/user/items/item54"/></entry>
  <entry><link href="https://qiita.com/user5/items/item55"/></entry>
</feed>"""

        mock_policy = AsyncMock()
        mock_policy.fetch_with_policy = AsyncMock(return_value=mock_response)

        with patch.object(fetcher, "_policy", mock_policy):
            result = await fetcher.fetch_batch(urls)

        # スコアの検証
        # 5位: 100点（上位10件）
        # 15位: 70点（11-20件）
        # 25位: 40点（21-30件）
        # 35位: 20点（31-50件）
        # 55位: 0点（51件以降）
        assert result["https://qiita.com/user1/items/item5"] == 100.0
        assert result["https://qiita.com/user2/items/item15"] == 70.0
        assert result["https://qiita.com/user3/items/item25"] == 40.0
        assert result["https://qiita.com/user4/items/item35"] == 20.0
        assert result["https://qiita.com/user5/items/item55"] == 0.0

    @pytest.mark.asyncio
    async def test_score_calculation_ranks(self):
        """段階的スコア計算が正しい（上位10件=100, 11-20件=70, etc.）."""
        fetcher = QiitaRankFetcher()

        urls = [
            "https://qiita.com/user/items/rank1",
            "https://qiita.com/user/items/rank10",
            "https://qiita.com/user/items/rank11",
            "https://qiita.com/user/items/rank20",
            "https://qiita.com/user/items/rank21",
            "https://qiita.com/user/items/rank30",
            "https://qiita.com/user/items/rank31",
            "https://qiita.com/user/items/rank50",
            "https://qiita.com/user/items/rank51",
        ]

        # モックレスポンス
        mock_response = MagicMock()
        feed_entries = "\n".join([
            f'  <entry><link href="https://qiita.com/user/items/rank{i}"/></entry>'
            for i in range(1, 60)
        ])
        mock_response.text = f"""<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
{feed_entries}
</feed>"""

        mock_policy = AsyncMock()
        mock_policy.fetch_with_policy = AsyncMock(return_value=mock_response)

        with patch.object(fetcher, "_policy", mock_policy):
            result = await fetcher.fetch_batch(urls)

        # スコア境界値の検証
        assert result["https://qiita.com/user/items/rank1"] == 100.0   # 1位
        assert result["https://qiita.com/user/items/rank10"] == 100.0  # 10位
        assert result["https://qiita.com/user/items/rank11"] == 70.0   # 11位
        assert result["https://qiita.com/user/items/rank20"] == 70.0   # 20位
        assert result["https://qiita.com/user/items/rank21"] == 40.0   # 21位
        assert result["https://qiita.com/user/items/rank30"] == 40.0   # 30位
        assert result["https://qiita.com/user/items/rank31"] == 20.0   # 31位
        assert result["https://qiita.com/user/items/rank50"] == 20.0   # 50位
        assert result["https://qiita.com/user/items/rank51"] == 0.0    # 51位

    @pytest.mark.asyncio
    async def test_non_qiita_url_returns_zero(self):
        """Qiita以外のURLはスコア0が返される."""
        fetcher = QiitaRankFetcher()

        urls = [
            "https://example.com/article",
            "https://zenn.dev/user/articles/article",
        ]

        result = await fetcher.fetch_batch(urls)

        # Qiita以外のURLは全て0
        assert result["https://example.com/article"] == 0.0
        assert result["https://zenn.dev/user/articles/article"] == 0.0

    @pytest.mark.asyncio
    async def test_feed_fetch_failure(self):
        """feed取得失敗時、全てのスコアが0になる."""
        fetcher = QiitaRankFetcher()

        urls = ["https://qiita.com/user/items/item1"]

        # feed取得失敗をシミュレート
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

        # 失敗時は全て0
        assert result["https://qiita.com/user/items/item1"] == 0.0

    @pytest.mark.asyncio
    async def test_external_service_policy_applied(self):
        """ExternalServicePolicyが適用されていることを確認."""
        fetcher = QiitaRankFetcher()

        # _policyがExternalServicePolicyのインスタンスであることを確認
        from src.services.external_service_policy import ExternalServicePolicy
        assert isinstance(fetcher._policy, ExternalServicePolicy)

    @pytest.mark.asyncio
    async def test_empty_urls(self):
        """空のURLリストで空の辞書が返される."""
        fetcher = QiitaRankFetcher()

        result = await fetcher.fetch_batch([])

        assert result == {}

    @pytest.mark.asyncio
    async def test_url_normalization(self):
        """URLの正規化が正しく行われる."""
        fetcher = QiitaRankFetcher()

        # 異なる形式のURLだが、正規化後は同じ
        urls = [
            "https://qiita.com/user/items/item1/",  # 末尾スラッシュあり
            "https://qiita.com/user/items/item2",   # 末尾スラッシュなし
        ]

        # モックレスポンス（feed内のURLも末尾スラッシュなし）
        mock_response = MagicMock()
        mock_response.text = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry><link href="https://qiita.com/user/items/item1"/></entry>
  <entry><link href="https://qiita.com/user/items/item2"/></entry>
</feed>"""

        mock_policy = AsyncMock()
        mock_policy.fetch_with_policy = AsyncMock(return_value=mock_response)

        with patch.object(fetcher, "_policy", mock_policy):
            result = await fetcher.fetch_batch(urls)

        # 正規化により、両方マッチする
        assert result["https://qiita.com/user/items/item1/"] == 100.0
        assert result["https://qiita.com/user/items/item2"] == 100.0
