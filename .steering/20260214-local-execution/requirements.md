# 要求内容

## 概要

既存の実装をローカル環境で実行可能にし、動作確認ができる状態にする。

## 背景

現在、src/配下に主要な実装コードは完成しているが、ローカル環境での動作確認に必要なファイルやドキュメントが不足している。Issue #2「とりあえずローカルで稼働させる」を解決するため、以下を整備する必要がある：

- Lambda実行用のイベントファイルが存在しない
- ローカル実行の具体的な手順が不明確
- 依存関係のインストール状況が未確認
- 実際にSAM CLIでローカル実行できるかが未検証

## 実装対象の機能

### 1. イベントファイルの作成
- `events/`ディレクトリを作成
- `events/dry_run.json`: dry_runモードで実行するためのイベントファイル
- `events/production.json`: 本番モードで実行するためのイベントファイル

### 2. ローカル実行環境の整備
- 依存関係のインストール確認（uv経由）
- requirements.txtの生成確認
- 環境変数の設定方法の明確化

### 3. ローカル実行テスト
- SAM CLIでのビルド実行
- dry_runモードでのローカル実行
- エラーがあれば修正

### 4. ドキュメント更新（必要に応じて）
- README.mdのローカル実行手順の確認と更新

## 受け入れ条件

### イベントファイルの作成
- [ ] `events/dry_run.json`が存在し、dry_run=trueが設定されている
- [ ] `events/production.json`が存在し、dry_run=falseが設定されている
- [ ] イベントファイルのJSON形式が正しい

### ローカル実行環境の整備
- [ ] `uv pip install -e ".[dev]"`が成功する
- [ ] `requirements.txt`が存在し、依存関係が正しく記述されている
- [ ] 環境変数の設定方法が明確である

### ローカル実行テスト
- [ ] `sam build`が成功する
- [ ] `sam local invoke NewsletterFunction --event events/dry_run.json`が実行できる
- [ ] 実行時にエラーが発生しない（または発生したエラーを修正済み）
- [ ] dry_runモードでログが出力され、処理の流れが確認できる

### ドキュメント更新
- [ ] README.mdのローカル実行手順が正しい（実際に実行して確認）
- [ ] 不足している情報があれば追記する

## 成功指標

- ローカル環境でSAM CLIを使ってLambda関数を実行できる
- dry_runモードで記事収集〜LLM判定（モック）〜通知（スキップ）の流れが確認できる
- エラーが発生せず、正常に完了する
- 他の開発者がREADME.mdを見てローカル実行できる

## スコープ外

以下はこのフェーズでは実装しません:

- 実際のAWS環境へのデプロイ
- DynamoDB LocalやLocalstackの導入（実際のAWSリソースを使用）
- 本番モードでの実行（dry_runモードのみ）
- 実際のBedrockへの接続（dry_runモードではBedrockを呼び出さないため）
- SESでの実際のメール送信（dry_runモードでは送信しない）

## 参照ドキュメント

- `docs/product-requirements.md` - プロダクト要求定義書
- `docs/architecture.md` - アーキテクチャ設計書
- `docs/repository-structure.md` - リポジトリ構造定義書
- `docs/development-guidelines.md` - 開発ガイドライン
- `README.md` - セットアップ手順
