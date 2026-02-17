# タスクリスト: 最終選定のソートアルゴリズムをComposite Scoreに変更する

## GitHub Issue
https://github.com/k-negishi/ai-curated-newsletter/issues/43

## 実装方針
- Kent Beck の TDD (Test-Driven Development) で実装する
- RED → GREEN → REFACTOR のサイクルを遵守

---

## タスク

### 1. BuzzScore に external_buzz プロパティを追加
- [x] RED: `test_buzz_score.py` に `external_buzz` プロパティのテストを追加
  - interest成分除外・0-100正規化の確認
  - 境界値テスト（total_score=0, interest_score=0, 最大値）
- [x] GREEN: `buzz_score.py` に `external_buzz` プロパティを実装
- [x] REFACTOR: コードを改善（シンプルな1行プロパティのため変更なし）
- [x] lint/format/型チェックがすべて通る

### 2. FinalSelector の Composite Score ソートを実装
- [x] RED: `test_final_selector.py` にComposite Scoreソートのテストを追加
  - InterestLabel違い×Buzz Score違いの組み合わせで順位確認
  - FYI+バズ大 が THINK+バズ小 を上回るケース
  - ACT_NOW+バズ小 が中位に留まるケース
  - buzz_scores=None の場合のフォールバック
- [x] GREEN: `final_selector.py` の `_sort_by_priority` を Composite Score に変更
  - LABEL_SCORE, INTEREST_WEIGHT, BUZZ_WEIGHT を定数として定義
  - external_buzz を使った composite score 計算
  - ソートキーを (-composite, -freshness, -confidence) に変更
- [x] REFACTOR: コードを改善（_calculate_composite_scoreを独立メソッドに分離済み）
- [x] lint/format/型チェックがすべて通る

### 3. 既存テストの修正
- [x] `test_prioritizes_by_interest_label` — 厳格階層前提のテストを Composite Score 前提に修正
- [x] `test_sorts_by_buzz_score_within_same_interest` — buzz_scores=Noneまたはinterest_score=0のケースは挙動が同一のため修正不要
- [x] その他のテストが壊れていないか確認（全16テストパス）
- [x] lint/format/型チェックがすべて通る

### 4. 全体検証
- [x] `pytest tests/ -v` で全テストパス（232 passed, coverage 90.44%）
- [x] `ruff check src/` でエラーなし
- [x] `ruff format src/` でフォーマット済み
- [x] `mypy src/` で型エラーなし

---

## 申し送り事項

### 実装完了サマリ
- **Composite Score 算出**: `α(0.4) × LABEL_SCORE[label] + (1-α)(0.6) × external_buzz`
- **external_buzz**: `(total_score - interest_score × 0.35) / 0.65`（0-100正規化）
- **ソートキー**: `(-composite, -freshness, -confidence)`
- 既存テストは Composite Score 前提で全て互換。追加修正なし

### 既存バグの修正（本Issue外）
- `social_proof_fetcher.py:120`: Python 2構文 `except TypeError, ValueError:` → `except (TypeError, ValueError):` に修正
  - ruff format 0.15.0 が括弧を外すバグあり → `# fmt: skip` で回避
- `test_buzz_scorer.py` / `test_buzz_scorer_integration.py`: 別PRで削除済みの `consensus_score`/`source_count` フィールドへの参照が残存していたため修正
  - 統合テストの重み計算も旧5要素→現4要素に更新
