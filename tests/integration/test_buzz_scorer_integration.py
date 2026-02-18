"""BuzzScorerの統合テスト."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock

import pytest

from src.models.article import Article
from src.repositories.interest_master import InterestMaster
from src.repositories.source_master import SourceMaster
from src.services.buzz_scorer import BuzzScorer
from src.services.social_proof.multi_source_social_proof_fetcher import (
    MultiSourceSocialProofFetcher,
)


class TestBuzzScorerIntegration:
    """BuzzScorerの統合テスト（3要素版）."""

    @pytest.fixture
    def interest_profile(self):
        """実際のInterestProfile（config/interests.yaml）を読み込む."""
        interest_master = InterestMaster("config/interests.yaml")
        return interest_master.get_profile()

    @pytest.fixture
    def source_master(self):
        """実際のSourceMaster（config/sources.yaml）を読み込む."""
        return SourceMaster("config/sources.yaml")

    @pytest.fixture
    def social_proof_fetcher(self):
        """MultiSourceSocialProofFetcherのモックを返す."""
        mock_fetcher = Mock(spec=MultiSourceSocialProofFetcher)
        mock_fetcher.fetch_batch = AsyncMock(return_value={})
        return mock_fetcher

    @pytest.fixture
    def buzz_scorer(self, interest_profile, source_master, social_proof_fetcher):
        """BuzzScorerインスタンスを返す."""
        return BuzzScorer(interest_profile, source_master, social_proof_fetcher)

    @pytest.mark.asyncio
    async def test_buzz_scorer_with_real_dependencies(
        self, buzz_scorer, social_proof_fetcher
    ):
        """実際のInterestProfile、SourceMasterを使用して3要素が正しく計算されること."""
        # テスト記事（Zenn、AI Coding関連、新しい記事）
        article = Article(
            url="https://zenn.dev/example/articles/ai-coding-test",
            title="Claudeによるコーディング支援の実践",
            published_at=datetime.now(timezone.utc),
            source_name="Zenn（トレンド）",  # Authority: MEDIUM (50点)
            description="Claudeとプロンプトエンジニアリングについての記事",
            normalized_url="https://zenn.dev/example/articles/ai-coding-test",
            collected_at=datetime.now(timezone.utc),
        )

        # MultiSourceSocialProofFetcherのモック設定（4指標統合スコア: 25）
        social_proof_fetcher.fetch_batch.return_value = {
            "https://zenn.dev/example/articles/ai-coding-test": 25.0,
        }

        scores = await buzz_scorer.calculate_scores([article])

        assert len(scores) == 1
        buzz_score = scores[article.normalized_url]

        # 各要素スコアが正しく計算されていることを確認
        assert buzz_score.social_proof_score == 25.0  # 4指標統合スコア
        assert buzz_score.interest_score == 80.0  # AI Coding（high_interest一致）
        assert buzz_score.authority_score == 50.0  # Zenn（MEDIUM）

        # 総合スコアが正しく計算されていることを確認（3要素版）
        # (25 * 0.55) + (interest * 0.35) + (50 * 0.10)
        expected = (25 * 0.55) + (buzz_score.interest_score * 0.35) + (50 * 0.10)
        assert buzz_score.total_score == pytest.approx(expected, abs=0.01)

    @pytest.mark.asyncio
    async def test_no_single_element_dominates(self, buzz_scorer, social_proof_fetcher):
        """単一要素が支配しないことを検証."""
        # ケース1: SocialProofが低い記事
        article1 = Article(
            url="https://example.com/new-but-boring",
            title="Unrelated topic",
            published_at=datetime.now(timezone.utc),
            source_name="Qiita（トレンド）",  # Authority: 50点
            description="Some other topic",
            normalized_url="https://example.com/new-but-boring",
            collected_at=datetime.now(timezone.utc),
        )

        # MultiSourceSocialProofFetcherのモック設定（統合スコア: 0）
        social_proof_fetcher.fetch_batch.return_value = {
            "https://example.com/new-but-boring": 0.0,
        }

        scores = await buzz_scorer.calculate_scores([article1])
        buzz_score1 = scores[article1.normalized_url]

        # SocialProof 0点の場合、総合スコアは100点にならない（3要素版）
        # (0 * 0.55) + (interest * 0.35) + (50 * 0.10)
        expected1 = (0 * 0.55) + (buzz_score1.interest_score * 0.35) + (50 * 0.10)
        assert buzz_score1.total_score < 100.0
        assert buzz_score1.total_score == pytest.approx(expected1, abs=0.01)

        # ケース2: SocialProofのみ高い記事
        article2 = Article(
            url="https://example.com/old-but-popular",
            title="Old popular article",
            published_at=datetime.now(timezone.utc),
            source_name="Qiita（トレンド）",  # Authority: 50点
            description="Unrelated content",
            normalized_url="https://example.com/old-but-popular",
            collected_at=datetime.now(timezone.utc),
        )

        # MultiSourceSocialProofFetcherのモック設定（統合スコア: 100）
        social_proof_fetcher.fetch_batch.return_value = {
            "https://example.com/old-but-popular": 100.0,
        }

        scores = await buzz_scorer.calculate_scores([article2])
        buzz_score2 = scores[article2.normalized_url]

        # SocialProof 100点でも、総合スコアは100点にならない（3要素版）
        # (100 * 0.55) + (interest * 0.35) + (50 * 0.10)
        expected2 = (100 * 0.55) + (buzz_score2.interest_score * 0.35) + (50 * 0.10)
        assert buzz_score2.total_score < 100.0
        assert buzz_score2.total_score == pytest.approx(expected2, abs=0.01)

    @pytest.mark.asyncio
    async def test_no_missing_important_articles(self, buzz_scorer, social_proof_fetcher):
        """取りこぼし防止のシナリオ検証."""
        # ケース1: 公式ブログ（Authority高）が低SocialProofでも一定スコア維持
        article_official = Article(
            url="https://qiita.com/official-blog",
            title="公式アナウンス",
            published_at=datetime.now(timezone.utc),
            source_name="Qiita（トレンド）",  # Authority: MEDIUM (50点)
            description="Important announcement",
            normalized_url="https://qiita.com/official-blog",
            collected_at=datetime.now(timezone.utc),
        )

        # ケース2: Interest一致記事が同条件で優先
        article_interest = Article(
            url="https://zenn.dev/ai-article",
            title="PostgreSQLのパフォーマンスチューニング",
            published_at=datetime.now(timezone.utc),
            source_name="Zenn（トレンド）",  # Authority: 50点
            description="インデックス設計と実行計画について",
            normalized_url="https://zenn.dev/ai-article",
            collected_at=datetime.now(timezone.utc),
        )

        article_no_interest = Article(
            url="https://zenn.dev/other-article",
            title="無関係な記事",
            published_at=datetime.now(timezone.utc),
            source_name="Zenn（トレンド）",  # Authority: 50点
            description="Unrelated topic",
            normalized_url="https://zenn.dev/other-article",
            collected_at=datetime.now(timezone.utc),
        )

        # ケース3: 話題記事（SocialProof高）が興味外でも一定スコア維持
        article_popular = Article(
            url="https://qiita.com/popular-article",
            title="バズっている記事",
            published_at=datetime.now(timezone.utc),
            source_name="Qiita（トレンド）",  # Authority: 50点
            description="Unrelated but popular",
            normalized_url="https://qiita.com/popular-article",
            collected_at=datetime.now(timezone.utc),
        )

        # MultiSourceSocialProofFetcherのモック設定（4指標統合スコア）
        social_proof_fetcher.fetch_batch.return_value = {
            "https://qiita.com/official-blog": 5.0,  # 低統合スコア
            "https://zenn.dev/ai-article": 5.0,  # 低統合スコア
            "https://zenn.dev/other-article": 5.0,  # 低統合スコア
            "https://qiita.com/popular-article": 100.0,  # 高統合スコア
        }

        articles = [article_official, article_interest, article_no_interest, article_popular]
        scores = await buzz_scorer.calculate_scores(articles)

        # ケース1検証: 公式記事が低SocialProofでも一定スコアを維持（3要素版）
        official_score = scores[article_official.normalized_url]
        # (5 * 0.55) + (interest * 0.35) + (50 * 0.10)
        expected_official = (
            (5 * 0.55)
            + (official_score.interest_score * 0.35)
            + (50 * 0.10)
        )
        assert official_score.total_score == pytest.approx(expected_official, abs=0.01)

        # ケース2検証: Interest一致記事が同条件（同じSocialProof）で優先（3要素版）
        interest_score_result = scores[article_interest.normalized_url]
        no_interest_score = scores[article_no_interest.normalized_url]
        # Interest一致記事のほうが高スコア
        assert interest_score_result.total_score > no_interest_score.total_score

        # ケース3検証: 話題記事が興味外でも一定スコアを維持（3要素版）
        popular_score = scores[article_popular.normalized_url]
        # (100 * 0.55) + (interest * 0.35) + (50 * 0.10)
        expected_popular = (
            (100 * 0.55)
            + (popular_score.interest_score * 0.35)
            + (50 * 0.10)
        )
        assert popular_score.total_score >= 60.0  # 一定スコアを維持
        assert popular_score.total_score == pytest.approx(expected_popular, abs=0.01)
