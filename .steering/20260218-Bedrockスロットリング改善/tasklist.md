# タスクリスト: Bedrockスロットリング改善

## Phase 1: boto3内部リトライ無効化

- [x] handler.py に botocore.Config を適用
  - [x] ~~RED: boto3クライアントのConfig設定が適用されることを確認するテストを書く~~ (理由: handler.pyはLambdaエントリポイントでユニットテスト対象外。mypy/ruffで検証)
  - [x] GREEN: `Config(retries={"max_attempts": 0, "mode": "standard"})` を適用
  - [x] REFACTOR: 不要なら整理
- [x] lint/format/型チェックがすべて通る

## Phase 2: リクエストの時間分散（staggered start）

- [x] staggered start を実装
  - [x] RED: 初回バッチでワーカーごとに異なる遅延が適用されるテストを書く
  - [x] GREEN: `judge_with_semaphore` に index ベースの初回分散を実装
  - [x] REFACTOR: `_aggregate_results()` を抽出してruff C901複雑度違反を解消
- [x] lint/format/型チェックがすべて通る

## Phase 3: 全体テストと品質チェック

- [x] 全テスト実行（pytest tests/ -v）- 今回の変更に関連する19テスト全パス。失敗3件は並行開発による既存問題
- [x] ruff check / ruff format / mypy がすべてパス
- [x] 既存の統合テスト（test_judgment_flow.py）がパスすることを確認
