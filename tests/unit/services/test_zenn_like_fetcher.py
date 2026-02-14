"""ZennLikeFetcherのユニットテスト（ランキングAPI版）."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

from src.services.zenn_like_fetcher import ZennLikeFetcher


class TestZennLikeFetcher:
    """ZennLikeFetcherクラスのテスト（ランキングAPI版）."""

    @pytest.mark.asyncio
    async def test_fetch_batch_success(self):
        """Zenn週間ランキングAPIから記事を取得し、スコアが計算される."""
        fetcher = ZennLikeFetcher()

        urls = [
            "https://zenn.dev/user1/articles/ranking1",  # ランキング1位
            "https://zenn.dev/user2/articles/ranking15",  # ランキング15位
            "https://zenn.dev/user3/articles/ranking35",  # ランキング35位
            "https://zenn.dev/user4/articles/not-in-ranking",  # ランキング圏外
        ]

        # モックレスポンス（ページ1: 1-30件）
        # 実際の順序通りに配置
        articles_page1 = [{"path": f"/user1/articles/ranking1"}]  # 1位
        for i in range(2, 15):
            articles_page1.append({"path": f"/user_other/articles/other{i}"})
        articles_page1.append({"path": "/user2/articles/ranking15"})  # 15位
        for i in range(16, 31):
            articles_page1.append({"path": f"/user_other/articles/other{i}"})

        mock_response_page1 = MagicMock()
        mock_response_page1.json = MagicMock(return_value={
            "articles": articles_page1,
            "next_page": 2,
        })

        # モックレスポンス（ページ2: 31-60件）
        articles_page2 = [{"path": "/user_other/articles/other31"}]  # 31位
        for i in range(32, 35):
            articles_page2.append({"path": f"/user_other/articles/other{i}"})
        articles_page2.append({"path": "/user3/articles/ranking35"})  # 35位
        for i in range(36, 61):
            articles_page2.append({"path": f"/user_other/articles/other{i}"})

        mock_response_page2 = MagicMock()
        mock_response_page2.json = MagicMock(return_value={
            "articles": articles_page2,
            "next_page": None,  # テストを簡略化するため、ここで終了
        })

        mock_policy = AsyncMock()
        mock_policy.fetch_with_policy = AsyncMock(
            side_effect=[
                mock_response_page1,
                mock_response_page2,
            ]
        )

        with patch.object(fetcher, "_policy", mock_policy):
            result = await fetcher.fetch_batch(urls)

        # スコア検証
        assert len(result) == 4
        assert result["https://zenn.dev/user1/articles/ranking1"] == 100.0  # 1位
        assert result["https://zenn.dev/user2/articles/ranking15"] == 80.0  # 15位
        assert result["https://zenn.dev/user3/articles/ranking35"] == 60.0  # 35位
        assert result["https://zenn.dev/user4/articles/not-in-ranking"] == 0.0  # 圏外

    @pytest.mark.asyncio
    async def test_pagination(self):
        """ページネーションが正しく動作する（100件まで取得）."""
        fetcher = ZennLikeFetcher()

        # ページ1のみを取得
        mock_response = MagicMock()
        mock_response.json = MagicMock(return_value={
            "articles": [
                {"path": "/user1/articles/article1"},
            ],
            "next_page": None,
        })

        mock_policy = AsyncMock()
        mock_policy.fetch_with_policy = AsyncMock(return_value=mock_response)

        with patch.object(fetcher, "_policy", mock_policy):
            await fetcher.fetch_batch(["https://zenn.dev/user1/articles/article1"])

        # APIが1回だけ呼ばれることを確認
        assert mock_policy.fetch_with_policy.call_count == 1

        # APIのURLを確認
        call_args = mock_policy.fetch_with_policy.call_args
        api_url = call_args[0][0]
        assert "https://zenn.dev/api/articles?order=weekly" in api_url

    @pytest.mark.asyncio
    async def test_score_calculation_by_rank(self):
        """ランキング順位に基づくスコア計算が正しい."""
        fetcher = ZennLikeFetcher()

        urls = [
            "https://zenn.dev/user/articles/rank1",   # 1位: 100点
            "https://zenn.dev/user/articles/rank10",  # 10位: 100点
            "https://zenn.dev/user/articles/rank11",  # 11位: 80点
            "https://zenn.dev/user/articles/rank30",  # 30位: 80点
            "https://zenn.dev/user/articles/rank31",  # 31位: 60点
            "https://zenn.dev/user/articles/rank50",  # 50位: 60点
            "https://zenn.dev/user/articles/rank51",  # 51位: 40点
            "https://zenn.dev/user/articles/rank100", # 100位: 40点
        ]

        # モックレスポンス（実際の順序通りに配置）
        articles = []
        # 1位
        articles.append({"path": "/user/articles/rank1"})
        # 2-9位（ダミー）
        for i in range(2, 10):
            articles.append({"path": f"/user/articles/dummy{i}"})
        # 10位
        articles.append({"path": "/user/articles/rank10"})
        # 11位
        articles.append({"path": "/user/articles/rank11"})
        # 12-29位（ダミー）
        for i in range(12, 30):
            articles.append({"path": f"/user/articles/dummy{i}"})
        # 30位
        articles.append({"path": "/user/articles/rank30"})
        # 31位
        articles.append({"path": "/user/articles/rank31"})
        # 32-49位（ダミー）
        for i in range(32, 50):
            articles.append({"path": f"/user/articles/dummy{i}"})
        # 50位
        articles.append({"path": "/user/articles/rank50"})
        # 51位
        articles.append({"path": "/user/articles/rank51"})
        # 52-99位（ダミー）
        for i in range(52, 100):
            articles.append({"path": f"/user/articles/dummy{i}"})
        # 100位
        articles.append({"path": "/user/articles/rank100"})

        mock_response = MagicMock()
        mock_response.json = MagicMock(return_value={
            "articles": articles,
            "next_page": None,
        })

        mock_policy = AsyncMock()
        mock_policy.fetch_with_policy = AsyncMock(return_value=mock_response)

        with patch.object(fetcher, "_policy", mock_policy):
            result = await fetcher.fetch_batch(urls)

        # スコア検証
        assert result["https://zenn.dev/user/articles/rank1"] == 100.0
        assert result["https://zenn.dev/user/articles/rank10"] == 100.0
        assert result["https://zenn.dev/user/articles/rank11"] == 80.0
        assert result["https://zenn.dev/user/articles/rank30"] == 80.0
        assert result["https://zenn.dev/user/articles/rank31"] == 60.0
        assert result["https://zenn.dev/user/articles/rank50"] == 60.0
        assert result["https://zenn.dev/user/articles/rank51"] == 40.0
        assert result["https://zenn.dev/user/articles/rank100"] == 40.0

    @pytest.mark.asyncio
    async def test_non_zenn_url_returns_zero(self):
        """Zenn以外のURLはスコア0が返される."""
        fetcher = ZennLikeFetcher()

        urls = [
            "https://example.com/article",
            "https://qiita.com/user/items/article",
        ]

        # ランキング取得は実行されるが、結果に影響しない
        mock_response = MagicMock()
        mock_response.json = MagicMock(return_value={
            "articles": [],
            "next_page": None,
        })

        mock_policy = AsyncMock()
        mock_policy.fetch_with_policy = AsyncMock(return_value=mock_response)

        with patch.object(fetcher, "_policy", mock_policy):
            result = await fetcher.fetch_batch(urls)

        # Zenn以外のURLは全て0
        assert result["https://example.com/article"] == 0.0
        assert result["https://qiita.com/user/items/article"] == 0.0

    @pytest.mark.asyncio
    async def test_api_failure_returns_zero(self):
        """API失敗時にスコア0が返される."""
        fetcher = ZennLikeFetcher()

        urls = ["https://zenn.dev/user/articles/article1"]

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

        # 失敗時は0
        assert result["https://zenn.dev/user/articles/article1"] == 0.0

    @pytest.mark.asyncio
    async def test_external_service_policy_applied(self):
        """ExternalServicePolicyが適用されていることを確認."""
        fetcher = ZennLikeFetcher()

        # _policyがExternalServicePolicyのインスタンスであることを確認
        from src.services.external_service_policy import ExternalServicePolicy
        assert isinstance(fetcher._policy, ExternalServicePolicy)

    @pytest.mark.asyncio
    async def test_empty_urls(self):
        """空のURLリストで空の辞書が返される."""
        fetcher = ZennLikeFetcher()

        result = await fetcher.fetch_batch([])

        assert result == {}

    @pytest.mark.asyncio
    async def test_max_pages_limit(self):
        """最大4ページ（100件程度）まで取得する."""
        fetcher = ZennLikeFetcher()

        # 無限にページがあるレスポンスを返す
        mock_response = MagicMock()
        mock_response.json = MagicMock(return_value={
            "articles": [{"path": f"/user/articles/article{i}"} for i in range(30)],
            "next_page": 999,  # 常に次のページがある
        })

        mock_policy = AsyncMock()
        mock_policy.fetch_with_policy = AsyncMock(return_value=mock_response)

        with patch.object(fetcher, "_policy", mock_policy):
            await fetcher.fetch_batch(["https://zenn.dev/user/articles/test"])

        # 最大4回（4ページ）まで呼ばれることを確認
        assert mock_policy.fetch_with_policy.call_count == 4
