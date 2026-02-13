# AI Curated Newsletter

技術ニュース/テックブログを自動収集し、LLMで判定して本当に読む価値のある記事だけをメールで通知するシステム。

## Features

- 📰 複数のRSS/Atomフィードから技術記事を自動収集
- 🤖 AWS Bedrock（Claude 3.5 Sonnet）による記事の自動判定
- 📧 週2〜3回、最大12件に厳選してメール通知
- 🚫 重複記事の自動排除とURL単位のキャッシュ
- 📊 Buzzスコアによる記事の優先順位付け
- ⚡ サーバーレスアーキテクチャで運用コスト最小化

## Tech Stack

- **Language**: Python 3.12
- **Infrastructure**: AWS Lambda, EventBridge, DynamoDB, SES
- **LLM**: AWS Bedrock (Claude 3.5 Sonnet)
- **Framework**: AWS SAM
- **Testing**: pytest, moto
- **Linting**: mypy, ruff

## Architecture

```
EventBridge (週2-3回)
    ↓
Lambda Function
    ↓
Collector → Normalizer → Deduplicator → BuzzScorer
    ↓
CandidateSelector (150件に絞る)
    ↓
LLM Judge (Bedrock) + Cache (DynamoDB)
    ↓
FinalSelector (12件に絞る) → Formatter → Notifier (SES)
    ↓
History (DynamoDB)
```

### LLM判定ラベル

記事は以下のラベルで分類されます：

- **ACT_NOW**: 今すぐ読むべき重要な記事
- **THINK**: じっくり考えるべき記事
- **FYI**: 参考情報として知っておくと良い記事
- **IGNORE**: 通知不要

## セットアップ手順

### 前提条件

- Python 3.12以上
- [uv](https://github.com/astral-sh/uv) (Python package installer)
- [AWS SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html)
- AWS認証情報が設定されていること（`aws configure`）

### 依存関係のインストール

```bash
# uvのインストール（Macの場合）
brew install uv

# プロジェクトの依存関係をインストール
uv pip install -e .

# 開発依存関係もインストール（テスト、Lintツール）
uv pip install -e ".[dev]"
```

### 環境変数の設定

以下の環境変数を設定してください：

```bash
export CACHE_TABLE_NAME=ai-curated-newsletter-cache
export HISTORY_TABLE_NAME=ai-curated-newsletter-history
export FROM_EMAIL=your-verified-email@example.com
export TO_EMAIL=your-email@example.com
export BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0
export AWS_REGION=us-east-1
```

## ローカル実行方法

### SAM CLIでのローカル実行

```bash
# ビルド
sam build

# ローカル実行（dry_runモード）
sam local invoke NewsletterFunction --event events/dry_run.json

# ローカル実行（本番モード）
sam local invoke NewsletterFunction --event events/production.json
```

### イベントファイルの例

`events/dry_run.json`:
```json
{
  "dry_run": true
}
```

`events/production.json`:
```json
{
  "dry_run": false
}
```

### ユニットテストの実行

```bash
# 全テスト実行
pytest tests/

# カバレッジ付き実行
pytest --cov=src tests/

# 特定のテストファイルのみ実行
pytest tests/unit/services/test_final_selector.py
```

### 品質チェック

```bash
# 型チェック
mypy src/

# Lintチェック
ruff check src/

# フォーマット
ruff format src/
```

## デプロイ方法

### 初回デプロイ

```bash
# ビルド
sam build

# デプロイ（ガイド付き）
sam deploy --guided
```

ガイド付きデプロイでは、以下を入力します：
- Stack Name: `ai-curated-newsletter`
- AWS Region: `us-east-1`（または任意のリージョン）
- Parameter FromEmail: 送信元メールアドレス（SESで認証済みのもの）
- Parameter ToEmail: 送信先メールアドレス
- Parameter BedrockModelId: `anthropic.claude-3-5-sonnet-20241022-v2:0`
- Confirm changes before deploy: `Y`
- Allow SAM CLI IAM role creation: `Y`
- Save arguments to configuration file: `Y`

### 2回目以降のデプロイ

```bash
# ビルド
sam build

# デプロイ（設定ファイルを使用）
sam deploy
```

### デプロイ後の確認

```bash
# Lambda関数の手動実行（dry_runモード）
aws lambda invoke \
  --function-name ai-curated-newsletter-NewsletterFunction-XXXXX \
  --payload '{"dry_run": true}' \
  --region us-east-1 \
  response.json

# レスポンス確認
cat response.json
```

### スケジュール設定の確認

デプロイ後、EventBridgeスケジュールが自動的に作成されます：
- 毎週火曜日 09:00 UTC（18:00 JST）
- 毎週金曜日 09:00 UTC（18:00 JST）

スケジュールを変更する場合は、`template.yaml`の`ScheduleExpression`を編集してください。

### SESメールアドレスの認証

初回デプロイ後、SESでメールアドレスを認証する必要があります：

```bash
# 送信元メールアドレスの認証
aws ses verify-email-identity --email-address your-verified-email@example.com

# 送信先メールアドレスの認証（SESサンドボックスモードの場合）
aws ses verify-email-identity --email-address your-email@example.com
```

認証メールが送信されるので、リンクをクリックして認証を完了してください。

### SESサンドボックスモードの解除（本番環境）

本番環境では、SESサンドボックスモードを解除する必要があります：
1. AWS ConsoleでSESダッシュボードを開く
2. 「Request production access」をクリック
3. 申請フォームを記入して送信
4. AWS審査後、本番モードに移行

## 謝辞（参考元ライセンス情報）

本プロジェクトは、以下のリポジトリのアイデア・構成・実装方針を参考にしています。

- https://github.com/GenerativeAgents/claude-code-book-chapter8
- https://github.com/Jeffallan/claude-skills

上記リポジトリはいずれも MIT License で公開されています。  
