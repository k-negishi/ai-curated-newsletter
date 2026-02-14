"""判定フローの統合テスト."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock

import pytest

from src.models.article import Article
from src.models.interest_profile import InterestProfile, JudgmentCriterion
from src.models.judgment import BuzzLabel, InterestLabel, JudgmentResult
from src.repositories.cache_repository import CacheRepository
from src.services.llm_judge import LlmJudge


@pytest.fixture
def mock_cache_repository() -> CacheRepository:
    """モックのCacheRepositoryを返す."""
    mock_cache = Mock(spec=CacheRepository)
    mock_cache.get = Mock(return_value=None)  # 初回はキャッシュなし
    mock_cache.put = Mock()  # 保存は成功する前提
    mock_cache.exists = Mock(return_value=False)
    return mock_cache


@pytest.fixture
def mock_interest_profile() -> InterestProfile:
    """テスト用のInterestProfileを返す."""
    criteria = {
        "act_now": JudgmentCriterion(
            label="ACT_NOW", description="今すぐ読むべき記事", examples=[]
        ),
        "think": JudgmentCriterion(label="THINK", description="設計判断に役立つ記事", examples=[]),
        "fyi": JudgmentCriterion(label="FYI", description="知っておくとよい記事", examples=[]),
        "ignore": JudgmentCriterion(label="IGNORE", description="関心外の記事", examples=[]),
    }
    return InterestProfile(
        summary="テストプロファイル",
        max_interest=[],
        high_interest=["AI/ML"],
        medium_interest=[],
        low_interest=[],
        ignore_interest=[],
        criteria=criteria,
    )


@pytest.fixture
def sample_articles() -> list[Article]:
    """サンプル記事のリストを返す."""
    return [
        Article(
            url="https://example.com/article1",
            title="Important Tech News",
            published_at=datetime.now(timezone.utc),
            source_name="Test Source",
            description="This is an important article",
            normalized_url="https://example.com/article1",
            collected_at=datetime.now(timezone.utc),
        ),
        Article(
            url="https://example.com/article2",
            title="Interesting Tutorial",
            published_at=datetime.now(timezone.utc),
            source_name="Test Source",
            description="A useful tutorial",
            normalized_url="https://example.com/article2",
            collected_at=datetime.now(timezone.utc),
        ),
    ]


@pytest.mark.asyncio
async def test_judgment_flow_success(
    mock_cache_repository: CacheRepository,
    mock_interest_profile: InterestProfile,
    sample_articles: list[Article],
) -> None:
    """判定フローが正常に動作することを確認."""
    # Bedrockクライアントをモック
    mock_bedrock = Mock()

    # 最初の記事は ACT_NOW、2番目は THINK と判定
    response1_body = Mock()
    response1_body.read.return_value = (
        b'{"content": [{"text": "{\\"interest_label\\": \\"ACT_NOW\\", '
        b'\\"buzz_label\\": \\"HIGH\\", \\"confidence\\": 0.9, '
        b'\\"summary\\": \\"Important news\\"}"}]}'
    )
    response2_body = Mock()
    response2_body.read.return_value = (
        b'{"content": [{"text": "{\\"interest_label\\": \\"THINK\\", '
        b'\\"buzz_label\\": \\"MID\\", \\"confidence\\": 0.8, '
        b'\\"summary\\": \\"Useful tutorial\\"}"}]}'
    )
    mock_bedrock.invoke_model.side_effect = [
        {"body": response1_body},
        {"body": response2_body},
    ]

    llm_judge = LlmJudge(
        bedrock_client=mock_bedrock,
        cache_repository=mock_cache_repository,
        interest_profile=mock_interest_profile,
        model_id="test-model",
        concurrency_limit=5,
    )

    # 初回判定
    result = await llm_judge.judge_batch(sample_articles)

    assert len(result.judgments) == 2
    assert result.judgments[0].interest_label == InterestLabel.ACT_NOW
    assert result.judgments[1].interest_label == InterestLabel.THINK
    assert result.failed_count == 0

    # Bedrock が2回呼び出されることを確認
    assert mock_bedrock.invoke_model.call_count == 2

    # キャッシュに2件保存されることを確認
    assert mock_cache_repository.put.call_count == 2


@pytest.mark.asyncio
async def test_judgment_flow_error_handling(
    mock_cache_repository: CacheRepository,
    mock_interest_profile: InterestProfile,
    sample_articles: list[Article],
) -> None:
    """判定エラーが適切にハンドリングされることを確認."""
    # Bedrockクライアントをモック（エラーを返す）
    mock_bedrock = Mock()
    mock_bedrock.invoke_model.side_effect = Exception("Bedrock API error")

    llm_judge = LlmJudge(
        bedrock_client=mock_bedrock,
        cache_repository=mock_cache_repository,
        interest_profile=mock_interest_profile,
        model_id="test-model",
        concurrency_limit=5,
    )

    # エラーが発生してもクラッシュしない
    result = await llm_judge.judge_batch(sample_articles)

    # 判定失敗が記録されている
    assert result.failed_count == 2
    # 判定失敗時はIGNOREラベルが設定される
    assert len(result.judgments) == 2
    assert all(j.interest_label == InterestLabel.IGNORE for j in result.judgments)
