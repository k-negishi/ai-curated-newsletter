"""LlmJudgeサービスのユニットテスト."""

import json
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from botocore.exceptions import ClientError

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
        max_interest=["セキュリティ"],
        high_interest=["AI/ML", "クラウドインフラ", "アーキテクチャ設計"],
        medium_interest=["データベース技術", "フロントエンド技術"],
        low_interest=["初心者向けチュートリアル"],
        ignore_interest=["広告記事"],
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

    # Assert - 低関心トピックが含まれることを確認
    assert "**低関心のトピック**:" in prompt
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
        '"summary":"important",'
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
        '"summary":"useful"'
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


def test_llm_judge_initialization_with_inference_profile_arn(
    mock_interest_profile: InterestProfile,
) -> None:
    """LlmJudgeがinference_profile_arnを正しく保持することを確認."""
    # Arrange
    mock_bedrock = MagicMock()
    test_arn = "arn:aws:bedrock:ap-northeast-1::inference-profile/test-profile"

    # Act
    llm_judge = LlmJudge(
        bedrock_client=mock_bedrock,
        cache_repository=None,
        interest_profile=mock_interest_profile,
        model_id="test-model",
        inference_profile_arn=test_arn,
    )

    # Assert
    assert llm_judge._inference_profile_arn == test_arn
    assert llm_judge._model_id == "test-model"


def test_llm_judge_initialization_without_inference_profile_arn(
    mock_interest_profile: InterestProfile,
) -> None:
    """inference_profile_arnが未設定の場合、空文字列がデフォルトとして保持されることを確認."""
    # Arrange
    mock_bedrock = MagicMock()

    # Act
    llm_judge = LlmJudge(
        bedrock_client=mock_bedrock,
        cache_repository=None,
        interest_profile=mock_interest_profile,
        model_id="test-model",
    )

    # Assert
    assert llm_judge._inference_profile_arn == ""
    assert llm_judge._model_id == "test-model"


# ThrottlingException リトライテスト


@pytest.mark.asyncio
async def test_judge_single_retries_on_throttling_exception(
    mock_interest_profile: InterestProfile, sample_article: Article
) -> None:
    """ThrottlingException 発生時にリトライされることを確認."""
    # Arrange
    mock_bedrock = MagicMock()

    # 最初の2回はThrottlingExceptionを発生させ、3回目は成功
    mock_bedrock.invoke_model.side_effect = [
        ClientError(
            {'Error': {'Code': 'ThrottlingException', 'Message': 'Too many requests'}},
            'InvokeModel'
        ),
        ClientError(
            {'Error': {'Code': 'ThrottlingException', 'Message': 'Too many requests'}},
            'InvokeModel'
        ),
        {
            'body': MagicMock(
                read=lambda: b'{"content":[{"text":"{\\"interest_label\\":\\"ACT_NOW\\",\\"buzz_label\\":\\"HIGH\\",\\"confidence\\":0.9,\\"summary\\":\\"test\\",\\"tags\\":[]}"}]}'
            )
        },
    ]

    llm_judge = LlmJudge(
        bedrock_client=mock_bedrock,
        cache_repository=None,
        interest_profile=mock_interest_profile,
        model_id="test-model",
        max_retries=3,
    )

    # Act
    with patch('asyncio.sleep', new_callable=AsyncMock):  # sleep をモック化して高速化
        result = await llm_judge._judge_single(sample_article)

    # Assert
    assert result is not None
    assert result.interest_label.value == "ACT_NOW"
    assert mock_bedrock.invoke_model.call_count == 3  # 2回リトライ + 1回成功


@pytest.mark.asyncio
async def test_judge_single_raises_exception_after_max_retries(
    mock_interest_profile: InterestProfile, sample_article: Article
) -> None:
    """最大リトライ回数到達時に例外が raise されることを確認."""
    # Arrange
    mock_bedrock = MagicMock()

    # 全てのリトライでThrottlingExceptionを発生
    mock_bedrock.invoke_model.side_effect = ClientError(
        {'Error': {'Code': 'ThrottlingException', 'Message': 'Too many requests'}},
        'InvokeModel'
    )

    llm_judge = LlmJudge(
        bedrock_client=mock_bedrock,
        cache_repository=None,
        interest_profile=mock_interest_profile,
        model_id="test-model",
        max_retries=2,
    )

    # Act & Assert
    with patch('asyncio.sleep', new_callable=AsyncMock):
        with pytest.raises(ClientError) as exc_info:
            await llm_judge._judge_single(sample_article)

        assert exc_info.value.response['Error']['Code'] == 'ThrottlingException'
        # max_retries=2 なので、3回実行される（初回 + 2回リトライ）
        assert mock_bedrock.invoke_model.call_count == 3


@pytest.mark.asyncio
async def test_judge_single_retries_on_service_unavailable_exception(
    mock_interest_profile: InterestProfile, sample_article: Article
) -> None:
    """ServiceUnavailableException もリトライされることを確認."""
    # Arrange
    mock_bedrock = MagicMock()

    # 最初はServiceUnavailableException、2回目は成功
    mock_bedrock.invoke_model.side_effect = [
        ClientError(
            {'Error': {'Code': 'ServiceUnavailableException', 'Message': 'Service unavailable'}},
            'InvokeModel'
        ),
        {
            'body': MagicMock(
                read=lambda: b'{"content":[{"text":"{\\"interest_label\\":\\"THINK\\",\\"buzz_label\\":\\"MID\\",\\"confidence\\":0.8,\\"summary\\":\\"test\\",\\"tags\\":[]}"}]}'
            )
        },
    ]

    llm_judge = LlmJudge(
        bedrock_client=mock_bedrock,
        cache_repository=None,
        interest_profile=mock_interest_profile,
        model_id="test-model",
        max_retries=3,
    )

    # Act
    with patch('asyncio.sleep', new_callable=AsyncMock):
        result = await llm_judge._judge_single(sample_article)

    # Assert
    assert result is not None
    assert result.interest_label.value == "THINK"
    assert mock_bedrock.invoke_model.call_count == 2  # 1回リトライ + 1回成功


@pytest.mark.asyncio
async def test_judge_single_does_not_retry_on_validation_exception(
    mock_interest_profile: InterestProfile, sample_article: Article
) -> None:
    """ValidationException はリトライされないことを確認."""
    # Arrange
    mock_bedrock = MagicMock()

    # ValidationException を発生
    mock_bedrock.invoke_model.side_effect = ClientError(
        {'Error': {'Code': 'ValidationException', 'Message': 'Invalid request'}},
        'InvokeModel'
    )

    llm_judge = LlmJudge(
        bedrock_client=mock_bedrock,
        cache_repository=None,
        interest_profile=mock_interest_profile,
        model_id="test-model",
        max_retries=3,
    )

    # Act & Assert
    with pytest.raises(ClientError) as exc_info:
        await llm_judge._judge_single(sample_article)

    assert exc_info.value.response['Error']['Code'] == 'ValidationException'
    # リトライされないので、1回のみ実行
    assert mock_bedrock.invoke_model.call_count == 1


# 指数バックオフ + ジッター テスト


def test_calculate_backoff_exponential_growth(
    mock_interest_profile: InterestProfile,
) -> None:
    """指数バックオフの計算が正しいことを確認."""
    # Arrange
    llm_judge = LlmJudge(
        bedrock_client=MagicMock(),
        cache_repository=None,
        interest_profile=mock_interest_profile,
        model_id="test-model",
    )

    base_delay = 2.0
    max_backoff = 20.0

    # Act & Assert
    for attempt in range(5):
        delay = llm_judge._calculate_backoff(attempt, base_delay, max_backoff)

        # 期待される基本遅延（ジッター前）
        expected_base = min(base_delay * (2 ** attempt), max_backoff)

        # ジッターは最大50%なので、expected_base <= delay <= expected_base * 1.5
        assert expected_base <= delay <= expected_base * 1.5, (
            f"attempt={attempt}: expected {expected_base} <= {delay} <= {expected_base * 1.5}"
        )


def test_calculate_backoff_respects_max_backoff(
    mock_interest_profile: InterestProfile,
) -> None:
    """最大バックオフ時間を超えないことを確認."""
    # Arrange
    llm_judge = LlmJudge(
        bedrock_client=MagicMock(),
        cache_repository=None,
        interest_profile=mock_interest_profile,
        model_id="test-model",
    )

    base_delay = 2.0
    max_backoff = 20.0

    # Act
    # attempt=10 で指数的に増えても max_backoff を超えない
    delay = llm_judge._calculate_backoff(10, base_delay, max_backoff)

    # Assert
    # max_backoff * 1.5 (ジッター込み) を超えない
    assert delay <= max_backoff * 1.5


def test_calculate_backoff_jitter_range(
    mock_interest_profile: InterestProfile,
) -> None:
    """ジッターが適切な範囲内であることを確認."""
    # Arrange
    llm_judge = LlmJudge(
        bedrock_client=MagicMock(),
        cache_repository=None,
        interest_profile=mock_interest_profile,
        model_id="test-model",
    )

    base_delay = 2.0
    max_backoff = 20.0
    attempt = 0

    # Act
    # 複数回実行してジッターの範囲を確認
    delays = [llm_judge._calculate_backoff(attempt, base_delay, max_backoff) for _ in range(100)]

    # Assert
    # 全ての遅延が base_delay 以上、base_delay * 1.5 以下
    for delay in delays:
        assert base_delay <= delay <= base_delay * 1.5


# 設定値適用のテスト


def test_llm_judge_stores_retry_config_parameters(
    mock_interest_profile: InterestProfile,
) -> None:
    """コンストラクタで設定値が正しく保持されることを確認."""
    # Arrange
    mock_bedrock = MagicMock()
    request_interval = 3.0
    retry_base_delay = 2.5
    max_backoff = 30.0

    # Act
    llm_judge = LlmJudge(
        bedrock_client=mock_bedrock,
        cache_repository=None,
        interest_profile=mock_interest_profile,
        model_id="test-model",
        request_interval=request_interval,
        retry_base_delay=retry_base_delay,
        max_backoff=max_backoff,
    )

    # Assert
    assert llm_judge._request_interval == request_interval
    assert llm_judge._retry_base_delay == retry_base_delay
    assert llm_judge._max_backoff == max_backoff


@pytest.mark.asyncio
async def test_judge_single_uses_custom_backoff_config(
    mock_interest_profile: InterestProfile, sample_article: Article
) -> None:
    """リトライ時にカスタム設定値が使用されることを確認."""
    # Arrange
    mock_bedrock = MagicMock()
    retry_base_delay = 3.0
    max_backoff = 15.0

    # 2回失敗してから成功
    mock_bedrock.invoke_model.side_effect = [
        ClientError(
            {'Error': {'Code': 'ThrottlingException', 'Message': 'Too many requests'}},
            'InvokeModel'
        ),
        ClientError(
            {'Error': {'Code': 'ThrottlingException', 'Message': 'Too many requests'}},
            'InvokeModel'
        ),
        {
            "body": MagicMock(
                read=MagicMock(
                    return_value=json.dumps({
                        "content": [{
                            "text": json.dumps({
                                "interest_label": "ACT_NOW",
                                "buzz_label": "HIGH",
                                "confidence": 0.9,
                                "summary": "テスト理由",
                                "tags": ["Test"]
                            })
                        }]
                    }).encode()
                )
            )
        },
    ]

    llm_judge = LlmJudge(
        bedrock_client=mock_bedrock,
        cache_repository=None,
        interest_profile=mock_interest_profile,
        model_id="test-model",
        max_retries=3,
        retry_base_delay=retry_base_delay,
        max_backoff=max_backoff,
    )

    # Act & Assert
    # _calculate_backoff が正しいパラメータで呼ばれることを確認
    with patch.object(
        llm_judge, '_calculate_backoff', wraps=llm_judge._calculate_backoff
    ) as mock_calculate:
        with patch('asyncio.sleep', new_callable=AsyncMock):
            result = await llm_judge._judge_single(sample_article)

        # リトライ時に _calculate_backoff が呼ばれることを確認
        assert mock_calculate.call_count == 2  # 2回リトライ

        # 1回目のリトライ: attempt=0
        mock_calculate.assert_any_call(
            attempt=0,
            base_delay=retry_base_delay,
            max_backoff=max_backoff,
        )

        # 2回目のリトライ: attempt=1
        mock_calculate.assert_any_call(
            attempt=1,
            base_delay=retry_base_delay,
            max_backoff=max_backoff,
        )

    assert result is not None
    assert result.interest_label.value == "ACT_NOW"
# Phase 4: 並列リクエスト間隔のテスト


@pytest.mark.asyncio
async def test_judge_batch_applies_request_interval(
    mock_interest_profile: InterestProfile, sample_article: Article
) -> None:
    """judge_batch がリクエスト前に間隔を挿入することを確認."""
    # Arrange
    mock_bedrock = MagicMock()
    request_interval = 0.5

    # 成功レスポンス（リトライが発生しないように正しい形式）
    mock_bedrock.invoke_model.return_value = {
        "body": MagicMock(
            read=MagicMock(
                return_value=json.dumps({
                    "content": [{
                        "text": json.dumps({
                            "interest_label": "ACT_NOW",
                            "buzz_label": "HIGH",
                            "confidence": 0.9,
                            "reason": "テスト理由",
                            "tags": ["Test"]
                        })
                    }]
                }).encode()
            )
        )
    }

    llm_judge = LlmJudge(
        bedrock_client=mock_bedrock,
        cache_repository=None,
        interest_profile=mock_interest_profile,
        model_id="test-model",
        request_interval=request_interval,
        max_retries=0,  # リトライを無効化してテストを簡略化
    )

    # 2つの記事でテスト
    articles = [sample_article, sample_article]

    # Act
    with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
        result = await llm_judge.judge_batch(articles)

        # Assert
        # リクエスト間隔が実装されたので、asyncio.sleep が request_interval で呼ばれる
        # 2つの記事があるので、2回呼ばれる
        assert mock_sleep.call_count == 2
        mock_sleep.assert_any_call(request_interval)

    # 判定は失敗するが、フォールバック判定が返される
    assert len(result.judgments) == 2
