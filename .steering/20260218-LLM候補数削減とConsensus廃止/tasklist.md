# LLM候補数削減とConsensus廃止 タスクリスト

## GitHub Issue
https://github.com/k-negishi/ai-curated-newsletter/issues/42

## 概要
LLM候補数を150→100に削減し、BuzzScoreからConsensus要素を廃止する。

## 実装方針
- Kent Beck の TDD (Test-Driven Development) で実装する
- RED → GREEN → REFACTOR のサイクルを遵守

## タスクリスト

### Phase 1: BuzzScore モデルから Consensus を削除
- [x] `src/models/buzz_score.py` から `consensus_score`, `source_count` を削除
  - [x] RED: consensus_score/source_count なしでBuzzScoreが生成できるテスト
  - [x] GREEN: フィールド削除
  - [x] REFACTOR: 不要なimport等の整理
- [x] `tests/unit/models/test_buzz_score.py` を修正
  - [x] 全BuzzScoreコンストラクタからconsensus_score/source_count削除
- [x] lint/format/型チェックがすべて通る

### Phase 2: BuzzScorer から Consensus 計算を削除
- [x] `src/services/buzz_scorer.py` を修正
  - [x] RED: 新しい重み配分(0.45/0.35/0.15/0.05)でtotal_scoreが正しく計算されるテスト
  - [x] GREEN: `_calculate_consensus_score` 削除、`WEIGHT_CONSENSUS` 削除、重み更新、`calculate_scores` 修正
  - [x] REFACTOR: url_counts（Counter）が不要になれば削除
- [x] `tests/unit/services/test_buzz_scorer.py` を修正
  - [x] consensus関連テスト2件を削除
  - [x] `test_calculate_total_score` の期待値を再計算
  - [x] `test_calculate_scores` からconsensus関連アサーション削除
- [x] `tests/integration/test_buzz_scorer_integration.py` を修正
  - [x] 全テストのtotal_score期待値を再計算
  - [x] consensus_score関連アサーション削除
- [x] lint/format/型チェックがすべて通る

### Phase 3: テストヘルパーの修正
- [x] `tests/unit/services/test_final_selector.py` の `_make_buzz_score` を修正
  - [x] consensus_score/source_count 削除（linterが自動修正済み）
- [x] lint/format/型チェックがすべて通る

### Phase 4: LLM候補数を100に変更
- [x] `src/services/candidate_selector.py` のデフォルトを150→100に変更
  - [x] RED: max_candidates=100がデフォルトであることのテスト
  - [x] GREEN: デフォルト値変更
- [x] `src/shared/config.py` の `LLM_CANDIDATE_MAX` デフォルト "150"→"100"
- [x] lint/format/型チェックがすべて通る

### Phase 5: 品質チェック
- [x] `pytest tests/ -v` — 232 passed, coverage 90.44%
- [x] `ruff check src/` — All checks passed
- [x] `ruff format src/` — フォーマット確認（social_proof_fetcher.pyは並行作業の影響で差分あり、本issueスコープ外）
- [x] `mypy src/` — Success: no issues found in 46 source files

## 申し送り事項
- `config/interests.yaml` が別作業で変更されており、統合テストの `interest_score` 期待値が 85→80 に変化（high_interest一致=80で正しい値）
- 統合テストの `total_score` 期待値は、ハードコードではなく計算式ベースの `pytest.approx` に変更し、interests.yaml変更に強い形にした
- `social_proof_fetcher.py` に並行作業による変更あり（Python 2構文 `except TypeError, ValueError:` → 正しくは `except (TypeError, ValueError):`）。git上は正しい構文だが、ワーキングツリーが並行作業で上書きされている
