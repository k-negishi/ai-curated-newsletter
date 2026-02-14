"""LlmJudgeサービスのユニットテスト."""

import pytest
from unittest.mock import MagicMock

from src.models.article import Article
from src.models.interest_profile import InterestProfile, JudgmentCriterion
from src.services.llm_judge import LlmJudge


@pytest.fixture
def mock_interest_profile() -> InterestProfile:
    """テスト用のInterestProfileモック."""
    criteria = {
        "act_now": JudgmentCriterion(
            label="ACT_NOW",
            description="今すぐ読むべき記事（緊急性・重要性が高い）",
            examples=["セキュリティ脆弱性", "重要な技術変更"],
        ),
        "think": JudgmentCriterion(
            label="THINK",
            description="設計判断に役立つ記事（アーキテクチャ・技術選定に有用）",
            examples=["アーキテクチャパターン"],
        ),
        "fyi": JudgmentCriterion(
            label="FYI", description="知っておくとよい記事（一般的な技術情報）", examples=[]
        ),
        "ignore": JudgmentCriterion(
            label="IGNORE", description="関心外の記事（上記に該当しない）", examples=[]
        ),
    }

    return InterestProfile(
        summary="プリンシパルエンジニアとして、技術的な深さと実践的な価値を重視します。",
        high_interest=["AI/ML", "クラウドインフラ", "アーキテクチャ設計"],
        medium_interest=["データベース技術", "フロントエンド技術"],
        low_priority=["初心者向けチュートリアル"],
        criteria=criteria,
    )


@pytest.fixture
def sample_article() -> Article:
    """テスト用の記事."""
    from datetime import datetime, timezone

    return Article(
        url="https://example.com/article1",
        title="テスト記事タイトル",
        description="テスト記事の説明文",
        source_name="テストソース",
        published_at=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        normalized_url="https://example.com/article1",
        collected_at=datetime(2024, 1, 1, 13, 0, 0, tzinfo=timezone.utc),
    )


def test_build_prompt_with_interest_profile(
    mock_interest_profile: InterestProfile, sample_article: Article
) -> None:
    """プロンプトにInterestProfileの内容が含まれることを確認."""
    # Arrange
    mock_bedrock = MagicMock()
    llm_judge = LlmJudge(
        bedrock_client=mock_bedrock,
        cache_repository=None,
        interest_profile=mock_interest_profile,
        model_id="test-model",
    )

    # Act
    prompt = llm_judge._build_prompt(sample_article)

    # Assert - プロファイル情報が含まれることを確認
    assert "プリンシパルエンジニアとして、技術的な深さと実践的な価値を重視します。" in prompt
    assert "**強い関心を持つトピック**:" in prompt
    assert "- AI/ML" in prompt
    assert "- クラウドインフラ" in prompt
    assert "- アーキテクチャ設計" in prompt

    # Assert - 中程度の関心トピックが含まれることを確認
    assert "**中程度の関心を持つトピック**:" in prompt
    assert "- データベース技術" in prompt
    assert "- フロントエンド技術" in prompt

    # Assert - 低優先度トピックが含まれることを確認
    assert "**低優先度のトピック**:" in prompt
    assert "- 初心者向けチュートリアル" in prompt

    # Assert - 判定基準が含まれることを確認
    assert "- **ACT_NOW**: 今すぐ読むべき記事（緊急性・重要性が高い）" in prompt
    assert "- セキュリティ脆弱性" in prompt
    assert "- **THINK**: 設計判断に役立つ記事（アーキテクチャ・技術選定に有用）" in prompt
    assert "- **FYI**: 知っておくとよい記事（一般的な技術情報）" in prompt
    assert "- **IGNORE**: 関心外の記事（上記に該当しない）" in prompt

    # Assert - 記事情報が含まれることを確認
    assert "テスト記事タイトル" in prompt
    assert "https://example.com/article1" in prompt
    assert "テスト記事の説明文" in prompt
    assert "テストソース" in prompt


def test_build_prompt_structure(
    mock_interest_profile: InterestProfile, sample_article: Article
) -> None:
    """プロンプトの構造が正しいことを確認."""
    # Arrange
    mock_bedrock = MagicMock()
    llm_judge = LlmJudge(
        bedrock_client=mock_bedrock,
        cache_repository=None,
        interest_profile=mock_interest_profile,
        model_id="test-model",
    )

    # Act
    prompt = llm_judge._build_prompt(sample_article)

    # Assert - セクションが存在することを確認
    assert "# 関心プロファイル" in prompt
    assert "# 記事情報" in prompt
    assert "# 判定基準" in prompt
    assert "**interest_label**（関心度）:" in prompt
    assert "**buzz_label**（話題性）:" in prompt
    assert "# 出力形式" in prompt
    assert "JSON形式で以下のキーを含めて出力してください:" in prompt


def test_llm_judge_initialization_with_interest_profile(
    mock_interest_profile: InterestProfile,
) -> None:
    """LlmJudgeがInterestProfileを正しく保持することを確認."""
    # Arrange
    mock_bedrock = MagicMock()

    # Act
    llm_judge = LlmJudge(
        bedrock_client=mock_bedrock,
        cache_repository=None,
        interest_profile=mock_interest_profile,
        model_id="test-model",
        max_retries=3,
        concurrency_limit=10,
    )

    # Assert
    assert llm_judge._interest_profile is mock_interest_profile
    assert llm_judge._model_id == "test-model"
    assert llm_judge._max_retries == 3
    assert llm_judge._concurrency_limit == 10


def test_parse_response_includes_tags_when_present(
    mock_interest_profile: InterestProfile, sample_article: Article
) -> None:
    """レスポンスにtagsがある場合、配列として取り出せることを確認."""
    llm_judge = LlmJudge(
        bedrock_client=MagicMock(),
        cache_repository=None,
        interest_profile=mock_interest_profile,
        model_id="test-model",
    )

    response = (
        '{'
        '"interest_label":"ACT_NOW",'
        '"buzz_label":"HIGH",'
        '"confidence":0.9,'
        '"reason":"important",'
        '"tags":["Kotlin","Claude"]'
        '}'
    )
    parsed = llm_judge._parse_response(response)

    assert parsed["tags"] == ["Kotlin", "Claude"]


def test_parse_response_uses_empty_tags_when_missing(
    mock_interest_profile: InterestProfile, sample_article: Article
) -> None:
    """レスポンスにtagsがない場合、空配列になることを確認."""
    llm_judge = LlmJudge(
        bedrock_client=MagicMock(),
        cache_repository=None,
        interest_profile=mock_interest_profile,
        model_id="test-model",
    )

    response = (
        '{'
        '"interest_label":"THINK",'
        '"buzz_label":"MID",'
        '"confidence":0.8,'
        '"reason":"useful"'
        '}'
    )
    parsed = llm_judge._parse_response(response)

    assert parsed["tags"] == []


def test_create_fallback_judgment_includes_published_at(
    mock_interest_profile: InterestProfile, sample_article: Article
) -> None:
    """フォールバック判定結果にpublished_atが含まれることを確認."""
    llm_judge = LlmJudge(
        bedrock_client=MagicMock(),
        cache_repository=None,
        interest_profile=mock_interest_profile,
        model_id="test-model",
    )

    fallback = llm_judge._create_fallback_judgment(sample_article)

    assert fallback.published_at == sample_article.published_at
    assert fallback.interest_label.value == "IGNORE"
    assert fallback.buzz_label.value == "LOW"
