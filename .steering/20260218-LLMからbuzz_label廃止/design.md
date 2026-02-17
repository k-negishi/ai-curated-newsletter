# 設計書

## アーキテクチャ概要

既存のレイヤードアーキテクチャを維持しつつ、LLMの責務からbuzz_label判定を分離する。BuzzLabelはBuzzScoreから機械的に導出する。

```
変更前:
  BuzzScorer → total_score（候補選定用）
  LlmJudge  → buzz_label（最終選定・メール表示用）  ← LLMが推測

変更後:
  BuzzScorer → total_score → buzz_label（全用途で使用）  ← 実データから導出
  LlmJudge  → interest_label, summary, tags のみ        ← 内容理解に集中
```

## コンポーネント設計

### 1. BuzzScore → BuzzLabel 変換（models/buzz_score.py）

**責務**:
- `total_score`から`BuzzLabel`への閾値変換

**実装の要点**:
- `BuzzScore`モデルにメソッド`to_buzz_label()`を追加
- 閾値はクラス定数として定義（将来の調整を容易に）
- modelsレイヤーに配置（BuzzScoreとBuzzLabelは両方modelsの概念）

```python
# src/models/buzz_score.py に追加
from src.models.judgment import BuzzLabel

_HIGH_THRESHOLD: ClassVar[float] = 70.0
_MID_THRESHOLD: ClassVar[float] = 40.0

def to_buzz_label(self) -> BuzzLabel:
    if self.total_score >= self._HIGH_THRESHOLD:
        return BuzzLabel.HIGH
    if self.total_score >= self._MID_THRESHOLD:
        return BuzzLabel.MID
    return BuzzLabel.LOW
```

### 2. LlmJudge（services/llm_judge.py）

**変更内容**:
- `_build_prompt()`: buzz_labelの指示セクション・出力形式を削除
- `_parse_response()`: `buzz_label`を必須フィールドから除外
- `_judge_single()`: `buzz_label`をLLMレスポンスから取得しない。一時的にデフォルト値`BuzzLabel.LOW`を設定
- `_create_fallback_judgment()`: 変更なし（`BuzzLabel.LOW`のまま）

**実装の要点**:
- LLMレスポンスにbuzz_labelが含まれていても無視する（後方互換）
- JudgmentResultにはまだbuzz_labelフィールドが必要（後のステップで上書き）

### 3. Orchestrator（orchestrator/orchestrator.py）

**変更内容**:
- Step 5（LLM判定）の後に、buzz_scoresを使ってJudgmentResultのbuzz_labelを上書き

**実装の要点**:
- Step 3で計算済みのbuzz_scoresとStep 5のjudgment結果を組み合わせる
- buzz_scores辞書（URL → BuzzScore）をキーにして対応するBuzzLabelを設定

```python
# Step 5.5: BuzzScoreからBuzzLabelを設定
for judgment in judgment_result.judgments:
    buzz_score = buzz_scores.get(judgment.url)
    if buzz_score is not None:
        judgment.buzz_label = buzz_score.to_buzz_label()
```

### 4. FinalSelector（services/final_selector.py）

**変更内容**:
- ソートキーの第2優先度を`buzz_label`（3段階）から`buzz_score`（連続値）に変更
- buzz_scoresをselectメソッドの引数に追加

**実装の要点**:
- `select(judgments, buzz_scores)`のシグネチャ変更
- buzz_scoresがない場合のフォールバック（0.0）

```python
def select(
    self,
    judgments: list[JudgmentResult],
    buzz_scores: dict[str, BuzzScore] | None = None,
) -> FinalSelectionResult:
```

ソートキーの変更:
```python
# 変更前
buzz_priority = {BuzzLabel.HIGH: 0, BuzzLabel.MID: 1, BuzzLabel.LOW: 2}
key = (..., buzz_priority.get(j.buzz_label, 999), ...)

# 変更後
key = (..., -(buzz_scores or {}).get(j.url, _ZERO_BUZZ_SCORE).total_score, ...)
```

### 5. CacheRepository（repositories/cache_repository.py）

**変更内容**: なし

**理由**:
- `buzz_label`は引き続きJudgmentResultに存在するため、保存・読み込みロジックは変更不要
- 既存キャッシュデータも正常に読み込める

### 6. Formatter（services/formatter.py）

**変更内容**: なし

**理由**:
- JudgmentResultの`buzz_label`フィールドは存続するため、メール表示はそのまま動作

## データフロー

### 変更後のフロー
```
1. Collector → 記事収集
2. Normalizer → 正規化
3. Deduplicator → 重複排除
4. BuzzScorer → buzz_scores辞書（URL → BuzzScore）
5. CandidateSelector → 候補選定（buzz_scores使用）
6. LlmJudge → judgments（buzz_label=LOWのダミー値）
7. Orchestrator → judgmentsのbuzz_labelをbuzz_scoresから上書き
8. FinalSelector → 最終選定（buzz_scoresのtotal_scoreでソート）
9. Formatter → メール本文（buzz_label表示）
10. Notifier → メール送信
```

## エラーハンドリング戦略

### buzz_scoresにURLが存在しない場合
- FinalSelectorでbuzz_scoresが`None`またはURLが見つからない場合、`total_score=0.0`として扱う
- Orchestratorでbuzz_scoresに該当URLがない場合、`BuzzLabel.LOW`を設定

### 既存キャッシュとの互換性
- 既存のキャッシュデータにはLLM由来のbuzz_labelが保存されている
- 読み込み時はそのまま使用する（BuzzScoreからの再導出は行わない）
- 新規判定分のみBuzzScoreベースのbuzz_labelが設定される

## テスト戦略

### ユニットテスト

**新規テスト**:
- `tests/unit/models/test_buzz_score.py`: `to_buzz_label()`のテスト
  - total_score=80 → HIGH
  - total_score=70 → HIGH（境界値）
  - total_score=69.9 → MID
  - total_score=50 → MID
  - total_score=40 → MID（境界値）
  - total_score=39.9 → LOW
  - total_score=0 → LOW

**更新テスト**:
- `tests/unit/services/test_llm_judge.py`:
  - プロンプトにbuzz_labelが含まれないことを検証
  - `_parse_response()`でbuzz_labelなしのJSONをパースできることを検証
- `tests/unit/services/test_final_selector.py`:
  - buzz_scoresを使ったソートの検証
  - buzz_scoresがNone/空の場合のフォールバック検証

### 統合テスト
- Orchestratorの全体フローでbuzz_labelがBuzzScoreから正しく設定されることを検証

## 依存ライブラリ

新しいライブラリの追加なし。

## ディレクトリ構造

```
変更対象ファイル:
src/
├── models/
│   └── buzz_score.py          # to_buzz_label() メソッド追加
├── services/
│   ├── llm_judge.py           # プロンプト・パース変更
│   └── final_selector.py      # ソートキー変更、buzz_scores引数追加
├── orchestrator/
│   └── orchestrator.py        # buzz_label上書きロジック追加

tests/
├── unit/
│   ├── models/
│   │   └── test_buzz_score.py # to_buzz_label()テスト追加
│   ├── services/
│   │   ├── test_llm_judge.py  # プロンプト・パーステスト更新
│   │   └── test_final_selector.py # ソートテスト更新

docs/
├── functional-design.md       # LLM判定仕様の更新
└── glossary.md                # Buzz Label定義の更新
```

## 実装の順序

1. `BuzzScore.to_buzz_label()` メソッド追加 + テスト
2. `LlmJudge` のプロンプト・パース変更 + テスト更新
3. `FinalSelector` のソートキー変更 + テスト更新
4. `Orchestrator` のbuzz_label上書きロジック追加
5. 品質チェック（pytest, ruff, mypy）
6. ドキュメント更新

## セキュリティ考慮事項

- セキュリティに影響する変更なし

## パフォーマンス考慮事項

- LLMプロンプトのトークン数削減（buzz_label指示の分だけ減少）
- FinalSelectorのソートにBuzzScore辞書のルックアップが追加されるが、最大15件のため影響は無視できる

## 将来の拡張性

- 閾値（HIGH ≥ 70, MID ≥ 40）はBuzzScoreのクラス定数として定義しており、運用データに基づく調整が容易
- BuzzScore計算アルゴリズムの改善がそのままBuzz Label精度の向上につながる
