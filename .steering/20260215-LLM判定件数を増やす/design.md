# 設計書

## アーキテクチャ概要

既存アーキテクチャを維持しつつ、以下のみを変更する。

- `src/shared/utils/bedrock_cost_estimator.py`（新規）
- `src/orchestrator/orchestrator.py`（コスト算出呼び出し差し替え）
- `.env`（実効候補件数）
- `README.md`（運用上の推奨値追記）
- `tests/unit/shared/utils/test_bedrock_cost_estimator.py`（新規）

## 設計方針

1. 推定コストは「件数×固定単価」ではなく、入力/出力トークンと単価から算出する
2. 設定値変更（30->120）と算出ロジック変更を同時に入れ、意思決定と実装を一致させる
3. モデル単価・トークン前提は関数引数で上書き可能にし、将来の価格改定に追従しやすくする

## 詳細設計

### 1. Bedrockコスト推定ユーティリティ

新規: `src/shared/utils/bedrock_cost_estimator.py`

提供関数:

- `estimate_bedrock_cost_usd(article_count, avg_input_tokens=900, avg_output_tokens=140, input_cost_per_million=6.0, output_cost_per_million=30.0) -> float`
  - 式:
    - `input_cost = article_count * avg_input_tokens * input_cost_per_million / 1_000_000`
    - `output_cost = article_count * avg_output_tokens * output_cost_per_million / 1_000_000`
    - `total = input_cost + output_cost`
  - `article_count` が負値なら `ValueError`

### 2. Orchestrator統合

- `src/orchestrator/orchestrator.py`
  - 既存の仮置き式 `llm_judged_count * 0.01` を削除
  - `estimate_bedrock_cost_usd(llm_judged_count)` を使用

### 3. 実効設定変更

- `.env`
  - `LLM_CANDIDATE_MAX=30` を `120` に変更

### 4. README追記

- `README.md` に以下を明記
  - `LLM_CANDIDATE_MAX` の運用推奨値: 120（最大150）
  - コスト算出前提（900 in / 140 out, Sonnet v2料金）

## TDDサイクル

1. RED
- 先に `tests/unit/shared/utils/test_bedrock_cost_estimator.py` を追加し、未実装で失敗を確認

2. GREEN
- `src/shared/utils/bedrock_cost_estimator.py` を実装
- `orchestrator.py` へ統合し、対象テストをパスさせる

3. REFACTOR
- README整合を更新
- 追加したテスト + 関連テストを再実行して回帰なしを確認
