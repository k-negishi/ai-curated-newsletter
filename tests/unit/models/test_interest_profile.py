"""InterestProfileモデルのユニットテスト."""

import pytest

from src.models.interest_profile import InterestProfile, JudgmentCriterion


def test_interest_profile_initialization() -> None:
    """InterestProfileの初期化テスト（5段階版）."""
    # Arrange
    criteria = {
        "act_now": JudgmentCriterion(
            label="ACT_NOW", description="今すぐ読むべき", examples=["例1", "例2"]
        )
    }

    # Act
    profile = InterestProfile(
        summary="テストプロファイル",
        max_interest=[],
        high_interest=["AI/ML", "クラウド"],
        medium_interest=["フロントエンド"],
        low_interest=["初心者向け"],
        ignore_interest=[],
        criteria=criteria,
    )

    # Assert
    assert profile.summary == "テストプロファイル"
    assert profile.max_interest == []
    assert profile.high_interest == ["AI/ML", "クラウド"]
    assert profile.medium_interest == ["フロントエンド"]
    assert profile.low_interest == ["初心者向け"]
    assert profile.ignore_interest == []
    assert "act_now" in profile.criteria


def test_format_for_prompt() -> None:
    """format_for_prompt()メソッドのテスト（5段階版）."""
    # Arrange
    profile = InterestProfile(
        summary="プリンシパルエンジニアとして活動",
        max_interest=[],
        high_interest=["AI/ML", "クラウドインフラ"],
        medium_interest=["データベース"],
        low_interest=["チュートリアル"],
        ignore_interest=[],
        criteria={},
    )

    # Act
    result = profile.format_for_prompt()

    # Assert
    assert "プリンシパルエンジニアとして活動" in result
    assert "**強い関心を持つトピック**:" in result
    assert "- AI/ML" in result
    assert "- クラウドインフラ" in result
    assert "**中程度の関心を持つトピック**:" in result
    assert "- データベース" in result
    assert "**低関心のトピック**:" in result
    assert "- チュートリアル" in result


def test_format_for_prompt_with_empty_lists() -> None:
    """空リストの場合のformat_for_prompt()テスト（5段階版）."""
    # Arrange
    profile = InterestProfile(
        summary="サマリのみ",
        max_interest=[],
        high_interest=[],
        medium_interest=[],
        low_interest=[],
        ignore_interest=[],
        criteria={},
    )

    # Act
    result = profile.format_for_prompt()

    # Assert
    assert result == "サマリのみ"
    assert "**最高関心を持つトピック**:" not in result
    assert "**強い関心を持つトピック**:" not in result
    assert "**中程度の関心を持つトピック**:" not in result
    assert "**低関心のトピック**:" not in result
    assert "**関心外のトピック**:" not in result


def test_format_criteria_for_prompt() -> None:
    """format_criteria_for_prompt()メソッドのテスト."""
    # Arrange
    criteria = {
        "act_now": JudgmentCriterion(
            label="ACT_NOW",
            description="今すぐ読むべき記事",
            examples=["セキュリティ脆弱性", "重要な技術変更"],
        ),
        "think": JudgmentCriterion(
            label="THINK", description="設計判断に役立つ記事", examples=["アーキテクチャパターン"]
        ),
        "fyi": JudgmentCriterion(label="FYI", description="知っておくとよい記事", examples=[]),
        "ignore": JudgmentCriterion(label="IGNORE", description="関心外の記事", examples=[]),
    }

    profile = InterestProfile(
        summary="テスト",
        max_interest=[],
        high_interest=[],
        medium_interest=[],
        low_interest=[],
        ignore_interest=[],
        criteria=criteria,
    )

    # Act
    result = profile.format_criteria_for_prompt()

    # Assert
    assert "- **ACT_NOW**: 今すぐ読むべき記事" in result
    assert "- セキュリティ脆弱性" in result
    assert "- 重要な技術変更" in result
    assert "- **THINK**: 設計判断に役立つ記事" in result
    assert "- アーキテクチャパターン" in result
    assert "- **FYI**: 知っておくとよい記事" in result
    assert "- **IGNORE**: 関心外の記事" in result

    # 順序確認（act_now → think → fyi → ignore）
    lines = result.split("\n")
    act_now_index = next(i for i, line in enumerate(lines) if "ACT_NOW" in line)
    think_index = next(i for i, line in enumerate(lines) if "THINK" in line)
    fyi_index = next(i for i, line in enumerate(lines) if "FYI" in line)
    ignore_index = next(i for i, line in enumerate(lines) if "IGNORE" in line)

    assert act_now_index < think_index < fyi_index < ignore_index


def test_interest_profile_initialization_5_levels() -> None:
    """InterestProfileの5段階フィールド初期化テスト."""
    # Arrange
    criteria = {
        "act_now": JudgmentCriterion(
            label="ACT_NOW", description="今すぐ読むべき", examples=["例1"]
        )
    }

    # Act
    profile = InterestProfile(
        summary="5段階テスト",
        max_interest=["AI Coding"],
        high_interest=["AI/ML", "クラウド"],
        medium_interest=["フロントエンド"],
        low_interest=["チュートリアル"],
        ignore_interest=["Ruby", "PHP"],
        criteria=criteria,
    )

    # Assert
    assert profile.summary == "5段階テスト"
    assert profile.max_interest == ["AI Coding"]
    assert profile.high_interest == ["AI/ML", "クラウド"]
    assert profile.medium_interest == ["フロントエンド"]
    assert profile.low_interest == ["チュートリアル"]
    assert profile.ignore_interest == ["Ruby", "PHP"]
    assert "act_now" in profile.criteria


def test_format_for_prompt_5_levels() -> None:
    """format_for_prompt()メソッドの5段階対応テスト."""
    # Arrange
    profile = InterestProfile(
        summary="5段階プロファイル",
        max_interest=["AI Coding"],
        high_interest=["アーキテクチャ設計"],
        medium_interest=["API設計"],
        low_interest=["基礎文法"],
        ignore_interest=["Ruby"],
        criteria={},
    )

    # Act
    result = profile.format_for_prompt()

    # Assert
    assert "5段階プロファイル" in result
    assert "**最高関心を持つトピック**:" in result
    assert "- AI Coding" in result
    assert "**強い関心を持つトピック**:" in result
    assert "- アーキテクチャ設計" in result
    assert "**中程度の関心を持つトピック**:" in result
    assert "- API設計" in result
    assert "**低関心のトピック**:" in result
    assert "- 基礎文法" in result
    assert "**関心外のトピック**:" in result
    assert "- Ruby" in result


