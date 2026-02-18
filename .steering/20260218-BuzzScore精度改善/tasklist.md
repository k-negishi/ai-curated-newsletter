# BuzzScore精度改善 タスクリスト

GitHub Issue: https://github.com/k-negishi/ai-curated-newsletter/issues/44

---

## Task 1: BuzzScoreモデルから recency_score を削除

**対象**: `src/models/buzz_score.py`, `tests/unit/models/test_buzz_score.py`

他の変更の前提となるため最初に実施。

- [x] RED: `recency_score` なしでBuzzScoreを生成するテストを書く
- [x] GREEN: `BuzzScore` dataclassから `recency_score` フィールドを削除、docstring更新
- [x] REFACTOR: テスト内の全BuzzScore生成箇所（約12箇所）から `recency_score` を削除
- [x] `external_buzz` プロパティのテストが引き続きパスすることを確認
- [x] lint/format/型チェックがすべて通る

---

## Task 2: BuzzScorerからRecency廃止＋重み再配分

**対象**: `src/services/buzz_scorer.py`, `tests/unit/services/test_buzz_scorer.py`

- [x] RED: 新しい重み（SP=0.55, Interest=0.35, Authority=0.10）でのtotal_scoreテストを書く
- [x] GREEN: `_calculate_recency_score` 削除、`WEIGHT_RECENCY` 削除、重み再配分、`_calculate_total_score` を3引数化
- [x] REFACTOR: Recencyテスト3件を削除、`test_calculate_total_score` を新しい重みで更新
- [x] `calculate_scores()` のBuzzScore生成から `recency_score` を削除
- [x] lint/format/型チェックがすべて通る

---

## Task 3: FinalSelector・統合テストの recency_score 参照を修正

**対象**: `src/services/final_selector.py`, `tests/unit/services/test_final_selector.py`, `tests/integration/test_buzz_scorer_integration.py`

- [x] `_ZERO_BUZZ_SCORE` から `recency_score` を削除
- [x] `test_final_selector.py` の `_make_buzz_score` ヘルパーから `recency_score` を削除
- [x] 統合テスト: `recency_score` アサーション削除、total_score計算式を3要素に更新（4箇所）
- [x] 全テストがパスすることを確認
- [x] lint/format/型チェックがすべて通る

---

## Task 4: はてブスコアを区間マッピング方式に変更

**対象**: `src/services/social_proof/hatena_count_fetcher.py`, `tests/unit/services/test_hatena_count_fetcher.py`

- [x] RED: 区間マッピングの期待値でテストを書く（0件→0, 1件→5, 30件→50, 100件→80, 500件→100）
- [x] GREEN: `_calculate_scores()` を区間マッピングテーブルに変更、`math` import削除、`HATENA_SCORE_TABLE` 定数追加
- [x] REFACTOR: `test_fetch_batch_success_under_50` のアサーション値を更新（100件→80, 50件→65, 10件→12）
- [x] lint/format/型チェックがすべて通る

---

## Task 5: SP計算を適用重み正規化に変更

**対象**: `src/services/social_proof/multi_source_social_proof_fetcher.py`, `tests/unit/services/test_multi_source_social_proof_fetcher.py`

- [x] RED: ドメイン別の正規化テストを書く（Zenn URL→/0.85、Qiita URL→/0.65、外部URL→/0.50）
- [x] GREEN: `_calculate_integrated_scores()` にドメイン判定と適用重み正規化を実装
- [x] REFACTOR: 既存テストの期待値を更新（example.com は外部ブログ扱い→/0.50）
- [x] `test_score_zero_treated_as_data` のQiita URLテストの期待値を更新
- [x] lint/format/型チェックがすべて通る

---

## Task 6: 全体結合テスト

- [x] `pytest tests/ -v` で全テストがパスすることを確認（236 passed, 1 failed は今回の変更と無関係の未コミットテスト）
- [x] `ruff check src/` でエラーなし
- [x] `ruff format src/` でフォーマット済み
- [x] `mypy src/` で型エラーなし

---

## 申し送り事項

- **実装完了日**: 2026-02-18
- **計画と実績の差分**: 計画通り6タスクで完了。Task 4, 5 はマルチエージェントで並列実行
- **external_buzz プロパティ**: 計算式 `(total - interest×0.35) / 0.65` は変更なし。totalからrecencyが消えたことで、純粋に SP+Authority のみを反映するようになった
- **BuzzLabel 閾値**: HIGH≥70, MID≥40 を維持。新しい重みでも妥当な分布になることを実データで事前検証済み
- **1件の既存テスト失敗**: `test_llm_judge.py::test_judge_batch_logs_total_token_usage` は今回の変更と無関係（別タスクの未コミットコード由来）
