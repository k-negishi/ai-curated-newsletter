# 要求内容

## 概要

DynamoDBに関する処理を一時的にコメントアウトし、アプリケーションをDynamoDB依存なしで動作可能にする。

## 背景

現在、アプリケーションはDynamoDBを使用して以下を実装している:
- 判定キャッシュ（CacheRepository）: LLM判定結果の永続化・重複排除
- 実行履歴（HistoryRepository）: 実行サマリの保存

しかし、以下の理由により、一時的にDynamoDB処理を無効化する必要がある:
1. MVP開発の初期段階で、まずコアロジック（収集・判定・通知）の動作確認を優先
2. DynamoDBのセットアップ・コスト管理を後回しにして、開発スピードを上げる
3. ローカル環境での動作確認を容易にする（DynamoDB Localのセットアップ不要）

## 実装対象の機能

### 1. CacheRepository処理のコメントアウト
- CacheRepositoryへの依存を削除または無効化
- キャッシュチェック処理をスキップし、全記事をLLM判定対象とする
- 判定結果のキャッシュ保存をスキップ

### 2. HistoryRepository処理のコメントアウト
- HistoryRepositoryへの依存を削除または無効化
- 実行履歴の保存処理をスキップ（ログのみで記録）

### 3. DynamoDB初期化のコメントアウト
- handler.pyでのDynamoDBリソース初期化をコメントアウト
- 環境変数（CACHE_TABLE_NAME, HISTORY_TABLE_NAME）の参照を無効化

## 受け入れ条件

### CacheRepository処理のコメントアウト
- [ ] Deduplicatorでのキャッシュチェックがスキップされる
- [ ] LlmJudgeでのキャッシュ保存がスキップされる
- [ ] DynamoDB呼び出しがゼロになる（boto3のDynamoDB APIが呼ばれない）
- [ ] アプリケーションが正常に起動・実行できる

### HistoryRepository処理のコメントアウト
- [ ] Orchestratorでの履歴保存がスキップされる
- [ ] DynamoDB呼び出しがゼロになる
- [ ] 実行サマリがログに出力される（代替手段）

### DynamoDB初期化のコメントアウト
- [ ] handler.pyでDynamoDBリソースが初期化されない
- [ ] CacheRepository/HistoryRepositoryのインスタンス化がスキップされる
- [ ] 環境変数エラーが発生しない

## 成功指標

- DynamoDB関連のコードが全てコメントアウトされている
- アプリケーションがDynamoDB接続なしで正常に動作する
- テストが全てパスする（DynamoDB依存のテストはスキップ）
- ログに「DynamoDBスキップ」の旨が記録される

## スコープ外

以下はこのフェーズでは実装しません:

- DynamoDB関連コードの完全削除（コメントアウトのみ）
- 代替のキャッシュ実装（インメモリキャッシュ等）
- 実行履歴の代替保存先（ファイル出力等）
- テストコードの大幅な書き換え（DynamoDB依存テストはスキップのみ）

## 参照ドキュメント

- `docs/product-requirements.md` - プロダクト要求定義書
- `docs/functional-design.md` - 機能設計書
- `docs/architecture.md` - アーキテクチャ設計書
- `docs/repository-structure.md` - リポジトリ構造定義書
- GitHub Issue #8: https://github.com/k-negishi/ai-curated-newsletter/issues/8
