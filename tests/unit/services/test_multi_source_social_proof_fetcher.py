"""MultiSourceSocialProofFetcherのユニットテスト."""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, patch

from src.services.multi_source_social_proof_fetcher import MultiSourceSocialProofFetcher
from src.models.article import Article


def create_test_article(url: str) -> Article:
    """テスト用の記事を作成する."""
    return Article(
        url=url,
        title="Test Article",
        published_at=datetime(2025, 1, 1, 0, 0, 0),
        source_name="test",
        description="test description",
        normalized_url=url,
        collected_at=datetime(2025, 1, 1, 0, 0, 0),
    )


class TestMultiSourceSocialProofFetcher:
    """MultiSourceSocialProofFetcherクラスのテスト."""

    @pytest.mark.asyncio
    async def test_fetch_batch_all_signals_success(self):
        """4指標すべて取得成功時の統合スコア計算."""
        fetcher = MultiSourceSocialProofFetcher()

        articles = [create_test_article("https://example.com/article1")]

        # モック: 各Fetcherが正常にスコアを返す
        # Y=100, H=50, Z=60, Q=70
        mock_yamadashy = AsyncMock()
        mock_yamadashy.fetch_signals = AsyncMock(
            return_value={"https://example.com/article1": 100}
        )

        mock_hatena = AsyncMock()
        mock_hatena.fetch_batch = AsyncMock(
            return_value={"https://example.com/article1": 50.0}
        )

        mock_zenn = AsyncMock()
        mock_zenn.fetch_batch = AsyncMock(
            return_value={"https://example.com/article1": 60.0}
        )

        mock_qiita = AsyncMock()
        mock_qiita.fetch_batch = AsyncMock(
            return_value={"https://example.com/article1": 70.0}
        )

        with patch.object(fetcher, "_yamadashy_fetcher", mock_yamadashy), \
             patch.object(fetcher, "_hatena_fetcher", mock_hatena), \
             patch.object(fetcher, "_zenn_fetcher", mock_zenn), \
             patch.object(fetcher, "_qiita_fetcher", mock_qiita):

            result = await fetcher.fetch_batch(articles)

        # 統合スコア: S = (0.20*100 + 0.45*50 + 0.25*60 + 0.10*70) / (0.20+0.45+0.25+0.10)
        # S = (20 + 22.5 + 15 + 7) / 1.0 = 64.5
        assert len(result) == 1
        assert 64.0 <= result["https://example.com/article1"] <= 65.0

    @pytest.mark.asyncio
    async def test_fetch_batch_one_signal_missing(self):
        """1指標欠損時の統合スコア計算（分母から除外）."""
        fetcher = MultiSourceSocialProofFetcher()

        articles = [create_test_article("https://example.com/article1")]

        # モック: Zennのみ欠損（スコア0）
        # Y=100, H=50, Z=0（欠損）, Q=70
        mock_yamadashy = AsyncMock()
        mock_yamadashy.fetch_signals = AsyncMock(
            return_value={"https://example.com/article1": 100}
        )

        mock_hatena = AsyncMock()
        mock_hatena.fetch_batch = AsyncMock(
            return_value={"https://example.com/article1": 50.0}
        )

        mock_zenn = AsyncMock()
        mock_zenn.fetch_batch = AsyncMock(
            return_value={"https://example.com/article1": 0.0}  # 欠損
        )

        mock_qiita = AsyncMock()
        mock_qiita.fetch_batch = AsyncMock(
            return_value={"https://example.com/article1": 70.0}
        )

        with patch.object(fetcher, "_yamadashy_fetcher", mock_yamadashy), \
             patch.object(fetcher, "_hatena_fetcher", mock_hatena), \
             patch.object(fetcher, "_zenn_fetcher", mock_zenn), \
             patch.object(fetcher, "_qiita_fetcher", mock_qiita):

            result = await fetcher.fetch_batch(articles)

        # 統合スコア（Zenn除外）: S = (0.20*100 + 0.45*50 + 0.10*70) / (0.20+0.45+0.10)
        # S = (20 + 22.5 + 7) / 0.75 = 66.0
        assert len(result) == 1
        assert 65.0 <= result["https://example.com/article1"] <= 67.0

    @pytest.mark.asyncio
    async def test_fetch_batch_all_signals_missing(self):
        """全指標欠損時のデフォルトスコア（S=40）."""
        fetcher = MultiSourceSocialProofFetcher()

        articles = [create_test_article("https://example.com/article1")]

        # モック: 全て欠損（スコア0）
        mock_yamadashy = AsyncMock()
        mock_yamadashy.fetch_signals = AsyncMock(
            return_value={"https://example.com/article1": 0}
        )

        mock_hatena = AsyncMock()
        mock_hatena.fetch_batch = AsyncMock(
            return_value={"https://example.com/article1": 0.0}
        )

        mock_zenn = AsyncMock()
        mock_zenn.fetch_batch = AsyncMock(
            return_value={"https://example.com/article1": 0.0}
        )

        mock_qiita = AsyncMock()
        mock_qiita.fetch_batch = AsyncMock(
            return_value={"https://example.com/article1": 0.0}
        )

        with patch.object(fetcher, "_yamadashy_fetcher", mock_yamadashy), \
             patch.object(fetcher, "_hatena_fetcher", mock_hatena), \
             patch.object(fetcher, "_zenn_fetcher", mock_zenn), \
             patch.object(fetcher, "_qiita_fetcher", mock_qiita):

            result = await fetcher.fetch_batch(articles)

        # デフォルトスコア: S=40
        assert len(result) == 1
        assert result["https://example.com/article1"] == 40.0

    @pytest.mark.asyncio
    async def test_weight_distribution(self):
        """重み配分の検証（Y=0.20, H=0.45, Z=0.25, Q=0.10）."""
        fetcher = MultiSourceSocialProofFetcher()

        articles = [create_test_article("https://example.com/article1")]

        # モック: 全て100点
        mock_yamadashy = AsyncMock()
        mock_yamadashy.fetch_signals = AsyncMock(
            return_value={"https://example.com/article1": 100}
        )

        mock_hatena = AsyncMock()
        mock_hatena.fetch_batch = AsyncMock(
            return_value={"https://example.com/article1": 100.0}
        )

        mock_zenn = AsyncMock()
        mock_zenn.fetch_batch = AsyncMock(
            return_value={"https://example.com/article1": 100.0}
        )

        mock_qiita = AsyncMock()
        mock_qiita.fetch_batch = AsyncMock(
            return_value={"https://example.com/article1": 100.0}
        )

        with patch.object(fetcher, "_yamadashy_fetcher", mock_yamadashy), \
             patch.object(fetcher, "_hatena_fetcher", mock_hatena), \
             patch.object(fetcher, "_zenn_fetcher", mock_zenn), \
             patch.object(fetcher, "_qiita_fetcher", mock_qiita):

            result = await fetcher.fetch_batch(articles)

        # 全て100点の場合、統合スコアも100点
        assert result["https://example.com/article1"] == 100.0

    @pytest.mark.asyncio
    async def test_empty_articles(self):
        """空の記事リストで空の辞書が返される."""
        fetcher = MultiSourceSocialProofFetcher()

        result = await fetcher.fetch_batch([])

        assert result == {}
