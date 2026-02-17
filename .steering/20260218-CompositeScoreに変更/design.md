# 設計書: 最終選定のソートアルゴリズムをComposite Scoreに変更する

## GitHub Issue

https://github.com/k-negishi/ai-curated-newsletter/issues/43

## 概要

FinalSelectorのソートアルゴリズムを、InterestLabelの厳格階層から**Composite Score**（InterestLabel + 外部話題性の重み付き混合）に変更する。

## 現状の問題

1. InterestLabelが絶対的な壁となり、FYI+バズ大の記事がTHINK+バズ小に常に負ける
2. total_scoreにinterest_score（25%）が含まれるため、個人関心キーワード一致だけでスコアが底上げされる
3. 候補120件→15件選定の環境で、FYI+バズ小の記事が15件枠に残ってしまう

## 設計

### Composite Score アルゴリズム

```python
# InterestLabelをスコア化（0-100スケール）
LABEL_SCORE = {
    InterestLabel.ACT_NOW: 100,
    InterestLabel.THINK: 60,
    InterestLabel.FYI: 20,
    InterestLabel.IGNORE: 0,
}

# 混合比率
INTEREST_WEIGHT = 0.4   # InterestLabel 40%
BUZZ_WEIGHT = 0.6       # 外部話題性 60%

# BuzzScoreからinterest成分を除外し、0-100に正規化
external_buzz = total_score - interest_score × WEIGHT_INTEREST(0.25)
normalized_buzz = min(external_buzz / 0.75, 100.0)  # 理論最大75を100に正規化

# Composite Score
composite = INTEREST_WEIGHT × LABEL_SCORE[label] + BUZZ_WEIGHT × normalized_buzz
```

### ソートキーの変更

```python
# Before
key = (interest_priority, -total_score, -freshness, -confidence)

# After
key = (-composite, -freshness, -confidence)
```

### BuzzScore モデルの拡張

`BuzzScore` に `external_buzz` プロパティを追加:

```python
@property
def external_buzz(self) -> float:
    """interest成分を除外した外部話題性スコア（0-100正規化）."""
    raw = self.total_score - self.interest_score * 0.25
    return min(max(raw, 0.0) / 0.75, 100.0)
```

### パラメータ設計

| パラメータ | 値 | 根拠 |
|---|---|---|
| LABEL_SCORE[ACT_NOW] | 100 | 最高優先度 |
| LABEL_SCORE[THINK] | 60 | ACT_NOWの60%、FYIの3倍 |
| LABEL_SCORE[FYI] | 20 | 最低（IGNOREは除外済み） |
| α (INTEREST_WEIGHT) | 0.4 | ACT_NOW+バズ小が4位に留まるバランス |

### 期待される挙動（α=0.4）

| 記事例 | Label | composite | 順位 |
|---|---|---|---|
| アーキテクチャ実践ガイド（バズ大） | ACT_NOW | 84 | 1位 |
| Claude Code 3.0徹底解説（バズ大） | THINK | 72 | 2位 |
| TypeScript 6.0リリース（バズ大） | FYI | 61 | 3位 |
| ACT_NOW記事（バズ小） | ACT_NOW | 59 | 4位 |
| PostgreSQL実行計画（バズ中） | THINK | 56 | 5位 |
| THINK記事（バズ小） | THINK | 43 | 6位 |
| GitHub Actions作り方（バズ中） | FYI | 38 | 7位 |
| Claude Code git exclude（バズ小） | FYI | 24 | 8位→脱落 |

## 変更対象ファイル

| ファイル | 変更内容 |
|---|---|
| `src/models/buzz_score.py` | `external_buzz` プロパティ追加 |
| `src/services/final_selector.py` | Composite Scoreによるソートロジック |
| `tests/unit/models/test_buzz_score.py` | `external_buzz` プロパティのテスト追加 |
| `tests/unit/services/test_final_selector.py` | ソート順テストの修正・追加 |

## 変更しないもの

- IGNORE除外ロジック（ステップ1: そのまま）
- ドメイン偏り制御（ステップ3: そのまま）
- `FinalSelector.select()` の公開インタフェース（引数・戻り値は変更なし）
- `orchestrator.py` の呼び出し側

## TDDサイクル

1. **RED**: 失敗するテストを先に書く
2. **GREEN**: 最小限の実装でテストをパスさせる
3. **REFACTOR**: コード品質を向上させる
