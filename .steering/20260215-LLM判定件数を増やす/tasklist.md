# タスクリスト

## フェーズ1: RED（失敗テストを先に作る）

- [x] コスト算出ユーティリティのテストを追加
  - [x] `tests/unit/shared/utils/test_bedrock_cost_estimator.py` を作成
  - [x] 30/60/90/120/150件のコスト期待値テストを追加
  - [x] 負値入力で `ValueError` になるテストを追加
- [x] RED確認: 追加したテストを実行し、失敗を確認

## フェーズ2: GREEN（最小実装でテストを通す）

- [x] `src/shared/utils/bedrock_cost_estimator.py` を実装
- [x] `src/orchestrator/orchestrator.py` のコスト算出を差し替え
- [x] GREEN確認: 追加テストがパスすることを確認

## フェーズ3: REFACTOR（設定・ドキュメント整合）

- [x] `.env` の `LLM_CANDIDATE_MAX` を `30 -> 120` に更新
- [x] `README.md` に推奨値とコスト前提を追記
- [x] 回帰確認として関連テストを再実行
  - [x] `.venv/bin/pytest tests/unit/shared/utils/test_bedrock_cost_estimator.py -v`
- [x] 品質チェックを実行
  - [x] `.venv/bin/ruff check src/`
  - [x] `.venv/bin/ruff format src/`
  - [x] `.venv/bin/mypy src/`

## 実装後の振り返り

- [x] 実装完了日を記録
- [x] 計画と実績の差分を記録
- [x] 学んだことと次回への改善を記録

### 実装完了日
2026-02-15

### 計画と実績の差分
- issue本文で求められていたコスト算出の根拠をコード化するため、`src/shared/utils/bedrock_cost_estimator.py` を新規追加した
- 品質ゲートは計画上の最小対象（新規テスト）に加え、`pytest tests/ -v` 全件も実行して回帰がないことを確認した

### 学んだこと
- 「件数の変更」だけでなく「算出根拠をコード化」すると、運用判断（120/150の選択）が再現可能になる
- Orchestratorの集計値は、仮置き係数よりもトークン単価ベースへ寄せることで説明責任が取りやすい

### 次回への改善提案
- 価格改定に備えて、モデル単価を設定ファイル化し、実行環境ごとに差し替え可能にする
- 実トークン使用量（CloudWatch Logs）を収集し、平均900/140トークン前提を実測で定期更新する
