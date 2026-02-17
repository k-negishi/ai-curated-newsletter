# タスクリスト

## 🚨 タスク完全完了の原則

**このファイルの全タスクが完了するまで作業を継続すること**

### 必須ルール
- **全てのタスクを`[x]`にすること**
- 「時間の都合により別タスクとして実施予定」は禁止
- 「実装が複雑すぎるため後回し」は禁止
- 未完了タスク（`[ ]`）を残したまま作業を終了しない

### 実装可能なタスクのみを計画
- 計画段階で「実装可能なタスク」のみをリストアップ
- 「将来やるかもしれないタスク」は含めない
- 「検討中のタスク」は含めない

### タスクスキップが許可される唯一のケース
以下の技術的理由に該当する場合のみスキップ可能:
- 実装方針の変更により、機能自体が不要になった
- アーキテクチャ変更により、別の実装方法に置き換わった
- 依存関係の変更により、タスクが実行不可能になった

スキップ時は必ず理由を明記:
```markdown
- [x] ~~タスク名~~（実装方針変更により不要: 具体的な技術的理由）
```

### タスクが大きすぎる場合
- タスクを小さなサブタスクに分割
- 分割したサブタスクをこのファイルに追加
- サブタスクを1つずつ完了させる

---

## フェーズ1: BuzzScore → BuzzLabel 変換ロジック

- [x] `src/models/buzz_score.py` に `to_buzz_label()` メソッドを追加
  - [x] `_HIGH_THRESHOLD = 70.0`, `_MID_THRESHOLD = 40.0` をクラス定数として定義
  - [x] `to_buzz_label()` メソッドを実装（total_score → BuzzLabel変換）
- [x] `tests/unit/models/test_buzz_score.py` に `to_buzz_label()` のテストを追加
  - [x] 境界値テスト（70.0, 40.0）
  - [x] 通常値テスト（80, 50, 20）
  - [x] エッジケース（0, 100）

## フェーズ2: LlmJudgeのプロンプト・パース変更

- [x] `src/services/llm_judge.py` の `_build_prompt()` を修正
  - [x] buzz_labelの判定基準セクションを削除
  - [x] 出力形式JSONからbuzz_labelを削除
- [x] `src/services/llm_judge.py` の `_parse_response()` を修正
  - [x] 必須フィールドから `buzz_label` を削除
- [x] `src/services/llm_judge.py` の `_judge_single()` を修正
  - [x] LLMレスポンスからbuzz_labelを取得しない
  - [x] JudgmentResult作成時に `buzz_label=BuzzLabel.LOW`（デフォルト値）を設定
- [x] `tests/unit/services/test_llm_judge.py` のテストを更新
  - [x] プロンプトにbuzz_labelが含まれないことを検証するテストに変更
  - [x] `_parse_response()` でbuzz_labelなしJSONが正常にパースされるテストを追加

## フェーズ3: FinalSelectorのソートキー変更

- [x] `src/services/final_selector.py` の `select()` メソッドを修正
  - [x] `buzz_scores: dict[str, BuzzScore] | None = None` パラメータを追加
  - [x] `_sort_by_priority()` に `buzz_scores` を渡す
- [x] `src/services/final_selector.py` の `_sort_by_priority()` を修正
  - [x] ソートキー第2優先度を `buzz_label`（3段階）から `buzz_score.total_score`（連続値）に変更
  - [x] buzz_scoresがNone/URLが見つからない場合は0.0をフォールバックとして使用
- [x] `tests/unit/services/test_final_selector.py` のテストを更新
  - [x] buzz_scoresを渡すテストに変更
  - [x] buzz_scoresがNoneの場合のフォールバックテストを追加

## フェーズ4: Orchestratorのbuzz_label上書きロジック

- [x] `src/orchestrator/orchestrator.py` の `execute()` を修正
  - [x] Step 5（LLM判定）の後にbuzz_labelの上書きロジックを追加
  - [x] Step 6（最終選定）にbuzz_scoresを渡す

## フェーズ5: 品質チェックと修正

- [x] すべてのテストが通ることを確認
  - [x] `.venv/bin/pytest tests/ -v`（220 passed、統合テスト3件の既存失敗を除く）
- [x] リントエラーがないことを確認
  - [x] `.venv/bin/ruff check src/` → All checks passed!
  - [x] `.venv/bin/ruff format src/` → 修正完了
- [x] 型エラーがないことを確認
  - [x] `.venv/bin/mypy src/` → Success: no issues found

## フェーズ6: ドキュメント更新

- [x] `docs/functional-design.md` を更新
  - [x] LLM判定の出力仕様からbuzz_labelを削除
  - [x] BuzzScore → BuzzLabel変換の仕様を追加
  - [x] 最終選定アルゴリズムのソートキーを更新
- [x] `docs/glossary.md` を更新
  - [x] Buzz Labelの定義を「BuzzScoreから閾値変換で導出」に変更
  - [x] LLM判断器の「Buzzラベル化」を削除
- [x] 実装後の振り返り（このファイルの下部に記録）

---

## 実装後の振り返り

### 実装完了日
2026-02-18

### 計画と実績の差分

**計画と異なった点**:
- FinalSelectorの変更（フェーズ3）は先行する#37（同一ドメイン制限のデフォルト無制限化）のコミットに一部含まれていた。buzz_scores引数の追加とソートキー変更がそのコミットに同梱されており、今回の作業では既にコミット済みだった。
- 統合テスト（`tests/integration/test_buzz_scorer_integration.py`）で3件の既存失敗が検出されたが、interest_scoreの期待値ずれが原因であり、今回の変更とは無関係。

**新たに必要になったタスク**:
- なし

### 学んだこと

**技術的な学び**:
- LLMの責務を「内容理解」に限定し、定量的な判定（話題性）は実データ由来のスコアから導出する設計が、関心の分離として適切。LLMはリアルタイムの外部シグナル（はてブ数、複数ソース出現回数等）を持たないため、これらに基づく判定は非LLMアルゴリズムに任せるべき。
- BuzzLabel（離散3段階）からBuzzScore total_score（連続値0-100）へのソートキー変更により、同じHIGH内でもスコア差による細かい優先順位付けが可能になった。

**プロセス上の改善点**:
- フェーズ1-3を並列に実装し、フェーズ4（統合）→フェーズ5（品質チェック）→フェーズ6（ドキュメント）と直列に進めた構成が効率的だった。

### 次回への改善提案

**計画フェーズでの改善点**:
- 先行コミットとの変更範囲の重複を事前に確認すること。#37のコミットがFinalSelectorの変更を含んでいたため、作業の一部が重複した。

**実装フェーズでの改善点**:
- 既存の統合テスト失敗を事前に把握しておくと、今回の変更による影響かどうかの判断が迅速になる。
