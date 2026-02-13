# 要求内容

## 概要

Lambda環境を本番・ローカル開発で安全に管理するため、環境変数を .env ファイルとAWS SSM Parameter Storeで管理する基盤を構築する。

## 背景

現在、環境変数がハードコードまたは不安定な方式で管理されている。以下の課題がある：
- ローカル開発時に環境変数の設定が煩雑
- 本番環境での機密情報管理が不安全（ハードコード禁止）
- AWS Secrets ManagerまたはSSM Parameter Storeとの連携が未実装
- サンドボックスモード（dry_run）のサポートが明確でない

## 実装対象の機能

### 1. ローカル開発用 .env ファイル管理
- プロジェクトルートに `.env` ファイルを用意（Gitから除外）
- ローカル実行時に自動的に読み込まれる
- 開発者が環境変数を簡単に設定できる

### 2. 本番環境用 AWS SSM Parameter Store管理
- AWS Lambda環境変数から SSM Parameter Storeにアクセス
- 起動時に SSM から環境設定を取得
- Secrets Managerで機密情報（メールアドレス等）を管理

### 3. dry_run モード対応
- `DRY_RUN=true` 環境変数でドライランモードを制御
- dry_runモード時はメール送信をスキップ
- LLM判定は実行（コスト確認用）
- DynamoDB書き込みはスキップ（履歴記録なし）

### 4. 設定の一元管理
- 環境固有の設定（本番 vs ローカル）を分離
- 設定ファイル変更時の再起動不要（可能な限り）

## 受け入れ条件

### .env ファイル管理
- [ ] .env ファイルのテンプレート（.env.example）をリポジトリに追加
- [ ] .gitignore に `.env` を追加（Gitから除外）
- [ ] `.env.local` にはローカルのAWS認証情報を記述（`.gitignore`から除外）

### SSM Parameter Store連携
- [ ] Lambda起動時に SSM Parameter Storeから設定を取得可能
- [ ] 取得に失敗した場合のエラーハンドリングが実装されている
- [ ] 設定変更後、Lambda再デプロイで反映される

### dry_run モード
- [ ] dry_run=true の場合、メール送信がスキップされる
- [ ] dry_run=true でも LLM判定は実行される（テスト用）
- [ ] dry_run=true でも DynamoDB キャッシュには書き込まれる（判定結果は永続化）
- [ ] dry_run=true でも 実行履歴には記録されない（HistoryTable には書き込まない）

### ローカル実行確認
- [ ] `sam local invoke` でローカルLambdaが正常に実行される
- [ ] 環境変数が正しく読み込まれることを確認
- [ ] .env から正しく設定が読み込まれることを確認

## 成功指標

- 環境変数がコード内にハードコードされていない
- ローカル開発環境で簡単に設定できる（.env ファイルのみ）
- 本番環境で機密情報が安全に管理されている
- dry_run モードが正常に動作している

## スコープ外

以下はこのフェーズでは実装しません:

- Secrets Manager の自動ローテーション
- マルチリージョン対応
- デプロイパイプライン自動化（CI/CD）
- 環境変数の暗号化（SSM は既に暗号化対応）

## 参照ドキュメント

- `docs/product-requirements.md` - プロダクト要求定義書
- `docs/architecture.md` - アーキテクチャ設計書
- `docs/development-guidelines.md` - 開発ガイドライン
