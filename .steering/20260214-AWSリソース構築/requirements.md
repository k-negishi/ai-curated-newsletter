# 要求内容

## 概要

AI Curated Newsletter が稼働するために必要な AWS リソースをすべて構築する。キャッシュ・履歴保存・LLM連携・メール送信などのインフラを整備し、本番環境で動作可能な状態にする。

## 背景

現在、AWS リソースが未構築の状態で、ローカル開発のみが可能。本番環境での運用に必要な以下のリソースを構築する必要がある：

- **DynamoDB**: 判定キャッシュ・実行履歴保存
- **SES**: メール送信（本番環境）
- **Bedrock**: Claude 3.5 Sonnet による LLM判定
- **Route53**: カスタムドメイン管理（必要に応じて）
- **Secrets Manager**: メールアドレスなど機密情報管理
- **EventBridge**: 週2-3回のスケジュール実行
- **IAM ロール**: Lambda の最小権限設定

## 実装対象の機能

### 1. DynamoDB テーブル構築

#### キャッシュテーブル（`ai-curated-newsletter-cache`）
- 判定結果をキャッシュ
- PK: `URL#<sha256(url)>`、SK: `JUDGMENT#v1`
- TTL: なし（永続保存）
- 課金モード: オンデマンド

#### 履歴テーブル（`ai-curated-newsletter-history`）
- 実行履歴を保存
- PK: `RUN#<YYYYWW>`、SK: `SUMMARY#<timestamp>`
- TTL: 90日（自動削除）
- 課金モード: オンデマンド

### 2. SES 設定

- メール送信元アドレスを検証済みに設定
- 本番環境から脱出（サンドボックスモード解除）
- 送信先メールアドレスも検証（初期段階）

### 3. Bedrock リソース確認

- Claude 3.5 Sonnet が利用可能か確認（us-east-1）
- モデル ID: `anthropic.claude-3-5-sonnet-20241022-v2:0`
- 推論 API アクセス権限確認

### 4. Secrets Manager 設定

- メール送信元アドレスを保存
- 送信先アドレスを保存
- 自動ローテーション設定（将来対応）

### 5. EventBridge スケジュール

- 週2回実行（例: 火曜・金曜 09:00 UTC）
- Lambda との連携設定

### 6. IAM ロール・ポリシー

- Lambda 実行ロール作成
- 最小権限ポリシー設定（DynamoDB, Bedrock, SES, Secrets Manager アクセス）

## 受け入れ条件

### DynamoDB
- [ ] キャッシュテーブルが作成されており、書き込み・読み込みが可能
- [ ] 履歴テーブルが作成されており、TTL が設定されている
- [ ] オンデマンド課金モードが有効
- [ ] Point-in-Time Recovery が有効（バックアップ）

### SES
- [ ] 送信元メールアドレスが検証済み（緑のチェック表示）
- [ ] 本番環境から脱出している（サンドボックスモード解除）
- [ ] テストメール送信が成功する

### Bedrock
- [ ] Claude 3.5 Sonnet へのアクセスが確認できる
- [ ] Lambda から Bedrock API を呼び出し可能

### Secrets Manager
- [ ] メール関連の機密情報が保存されている
- [ ] Lambda から シークレット値を取得可能

### EventBridge
- [ ] スケジュール実行ルールが作成されている
- [ ] Lambda をターゲットとして登録されている

### IAM ロール
- [ ] DynamoDB（GetItem, PutItem, BatchGetItem, Query）アクセス許可
- [ ] Bedrock（InvokeModel）アクセス許可
- [ ] SES（SendEmail）アクセス許可
- [ ] Secrets Manager（GetSecretValue）アクセス許可

### ローカル確認
- [ ] `sam local invoke` でドライラン（dry_run=true）が実行できる
- [ ] AWS 認証情報が正しく設定されている

## 成功指標

- すべての AWS リソースが構築されている
- Lambda が本番環境で正常に実行される
- コスト見積もりが月 $10 以内（PRD 要件）
- セキュリティベストプラクティスに準拠している

## スコープ外

以下はこのフェーズでは実装しません:

- **Route53 カスタムドメイン**: 不要（通知メールのみ）
- **CloudFront / API Gateway**: 不要（Lambda 単体で十分）
- **VPC 設定**: 不要（パブリック API のみ使用）
- **Lambda レイヤー化**: Phase 2 で検討
- **CI/CD パイプライン**: Phase 2 で実装
- **マルチリージョン対応**: Phase 2 で検討

## 参照ドキュメント

- `docs/architecture.md` - テクノロジースタック、AWS リソース設計
- `docs/product-requirements.md` - コスト要件（月 $10 以内）
- `docs/development-guidelines.md` - デプロイメント手順
