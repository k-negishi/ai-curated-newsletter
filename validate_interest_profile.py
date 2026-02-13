#!/usr/bin/env python3
"""興味プロファイルの実装を検証するスクリプト.

このスクリプトは開発環境がセットアップされていない場合に、
基本的な実装が正しく動作するかを確認するために使用します。
"""

import sys
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent))


def validate_yaml_structure():
    """config/interests.yamlの構造を検証する."""
    print("=== YAML構造の検証 ===")
    try:
        import yaml

        with open("config/interests.yaml") as f:
            data = yaml.safe_load(f)

        # 必須キーの存在確認
        assert "profile" in data, "Missing 'profile' key"
        assert "criteria" in data, "Missing 'criteria' key"

        profile = data["profile"]
        assert "summary" in profile, "Missing 'summary' in profile"
        assert "high_interest" in profile, "Missing 'high_interest' in profile"
        assert "medium_interest" in profile, "Missing 'medium_interest' in profile"
        assert "low_priority" in profile, "Missing 'low_priority' in profile"

        # criteria の検証
        for key in ["act_now", "think", "fyi", "ignore"]:
            assert key in data["criteria"], f"Missing '{key}' in criteria"
            criterion = data["criteria"][key]
            assert "label" in criterion, f"Missing 'label' in {key}"
            assert "description" in criterion, f"Missing 'description' in {key}"
            assert "examples" in criterion, f"Missing 'examples' in {key}"

        print("✓ YAML構造は正しく定義されています")
        return True

    except Exception as e:
        print(f"✗ YAML検証エラー: {e}")
        return False


def validate_interest_profile_model():
    """InterestProfileモデルの基本動作を検証する."""
    print("\n=== InterestProfileモデルの検証 ===")
    try:
        from src.models.interest_profile import InterestProfile, JudgmentCriterion

        # テストデータ
        criteria = {
            "act_now": JudgmentCriterion(
                label="ACT_NOW", description="Urgent", examples=["Security"]
            )
        }
        profile = InterestProfile(
            summary="Test summary",
            high_interest=["AI/ML", "Cloud"],
            medium_interest=["Frontend"],
            low_priority=["Tutorials"],
            criteria=criteria,
        )

        # format_for_prompt のテスト
        prompt_text = profile.format_for_prompt()
        assert "Test summary" in prompt_text
        assert "AI/ML" in prompt_text
        assert "Cloud" in prompt_text

        # format_criteria_for_prompt のテスト
        criteria_text = profile.format_criteria_for_prompt()
        assert "ACT_NOW" in criteria_text
        assert "Urgent" in criteria_text

        print("✓ InterestProfileモデルは正しく動作しています")
        return True

    except Exception as e:
        print(f"✗ InterestProfileモデル検証エラー: {e}")
        import traceback

        traceback.print_exc()
        return False


def validate_interest_master():
    """InterestMasterの基本動作を検証する."""
    print("\n=== InterestMasterの検証 ===")
    try:
        from src.repositories.interest_master import InterestMaster

        # 実際のconfig/interests.yamlを読み込む
        master = InterestMaster("config/interests.yaml")
        profile = master.get_profile()

        assert profile.summary != ""
        assert len(profile.high_interest) > 0
        assert len(profile.medium_interest) > 0
        assert len(profile.low_priority) > 0
        assert "act_now" in profile.criteria
        assert "think" in profile.criteria
        assert "fyi" in profile.criteria
        assert "ignore" in profile.criteria

        print(f"✓ InterestMasterは正しく動作しています")
        print(f"  - high_interest: {len(profile.high_interest)}件")
        print(f"  - medium_interest: {len(profile.medium_interest)}件")
        print(f"  - low_priority: {len(profile.low_priority)}件")
        print(f"  - criteria: {len(profile.criteria)}件")
        return True

    except Exception as e:
        print(f"✗ InterestMaster検証エラー: {e}")
        import traceback

        traceback.print_exc()
        return False


def validate_integration():
    """統合動作を検証する."""
    print("\n=== 統合動作の検証 ===")
    try:
        from datetime import datetime

        from src.models.article import Article
        from src.repositories.interest_master import InterestMaster

        # InterestMasterからプロファイルを読み込む
        master = InterestMaster("config/interests.yaml")
        profile = master.get_profile()

        # サンプル記事を作成
        sample_article = Article(
            url="https://example.com/test",
            title="Test Article About AI",
            published_at=datetime(2024, 1, 1, 0, 0, 0),
            source_name="Test Source",
            description="This is a test article about artificial intelligence",
            normalized_url="https://example.com/test",
            collected_at=datetime(2024, 1, 1, 0, 0, 0),
        )

        # プロンプト生成のシミュレーション（LlmJudgeの_build_promptロジック）
        profile_text = profile.format_for_prompt()
        criteria_text = profile.format_criteria_for_prompt()

        prompt = f"""以下の記事について、関心度と話題性を判定してください。

# 関心プロファイル
{profile_text}

# 記事情報
- タイトル: {sample_article.title}
- URL: {sample_article.url}
- 概要: {sample_article.description}
- ソース: {sample_article.source_name}

# 判定基準
**interest_label**（関心度）:
{criteria_text}
"""

        # プロンプトの内容を確認
        assert "プリンシパルエンジニア" in prompt or len(profile_text) > 0
        assert "ACT_NOW" in prompt
        assert "THINK" in prompt
        assert "FYI" in prompt
        assert "IGNORE" in prompt
        assert "Test Article About AI" in prompt

        print("✓ 統合動作は正しく機能しています")
        print(f"  - プロンプト長: {len(prompt)}文字")
        return True

    except Exception as e:
        print(f"✗ 統合動作検証エラー: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """全ての検証を実行する."""
    print("興味プロファイル実装の検証を開始します...\n")

    results = []
    results.append(validate_yaml_structure())
    results.append(validate_interest_profile_model())
    results.append(validate_interest_master())
    results.append(validate_integration())

    print("\n" + "=" * 50)
    if all(results):
        print("✓ すべての検証に成功しました！")
        print("実装は正しく動作する準備ができています。")
        return 0
    else:
        print("✗ 一部の検証に失敗しました。")
        print("エラーメッセージを確認して修正してください。")
        return 1


if __name__ == "__main__":
    sys.exit(main())
