# 設計書

## アーキテクチャ概要

```
┌─────────────────────────────────────────────────────────────┐
│ AWS リソース構成図（本番環境）                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ EventBridge Schedule                                        │
│     │                                                       │
│     ↓                                                       │
│ Lambda Function (NewsletterFunction)                        │
│     │                                                       │
│     ├─→ Bedrock (Claude 3.5 Sonnet)                        │
│     ├─→ DynamoDB Cache Table                               │
│     ├─→ DynamoDB History Table                             │
│     ├─→ SES (Email Send)                                   │
│     └─→ Secrets Manager (Credentials)                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## AWS リソース構成

### 1. DynamoDB テーブル設計

#### テーブル1: キャッシュテーブル

```
テーブル名: ai-curated-newsletter-cache
PK: URL#<sha256(url)>
SK: JUDGMENT#v1
課金モード: オンデマンド
PITR: 有効（35日間保存）

属性例:
{
  "url": "https://example.com/article",
  "interest_label": "ACT_NOW",
  "buzz_label": "HIGH",
  "confidence": 0.85,
  "reason": "PostgreSQL インデックス戦略",
  "model_id": "anthropic.claude-3-5-sonnet-20241022-v2:0",
  "judged_at": "2025-01-15T10:30:00Z",
  "title": "PostgreSQL Index Strategies",
  "source_name": "Hacker News"
}
```

#### テーブル2: 履歴テーブル

```
テーブル名: ai-curated-newsletter-history
PK: RUN#<YYYYWW> (例: RUN#202503)
SK: SUMMARY#<timestamp>
課金モード: オンデマンド
TTL: ttl 属性（90日）

属性例:
{
  "run_id": "550e8400-e29b-41d4-a716-446655440000",
  "executed_at": "2025-01-15T09:00:00Z",
  "collected_count": 342,
  "deduped_count": 280,
  "llm_judged_count": 120,
  "cache_hit_count": 160,
  "final_selected_count": 10,
  "notification_sent": true,
  "execution_time_seconds": 385.5,
  "estimated_cost_usd": 0.42,
  "ttl": 1739559600  # Unix timestamp (90日後)
}
```

### 2. SES 設定

**SES Sending Limit（サンドボックスモード）**:
- 本番環境から脱出するために AWS Support に申請
- または自動でクォーター引き上げ申請

**検証済みメールアドレス**:
- 送信元: `from_address` (例: `newsletter@example.com`)
- 送信先: `to_address` (個人の通知先メール)

### 3. Bedrock 設定

**モデル**: Claude 3.5 Sonnet
- モデル ID: `anthropic.claude-3-5-sonnet-20241022-v2:0`
- リージョン: `us-east-1`（重要）
- 推論 API アクセス確認

**使用方法**:
```python
bedrock = boto3.client("bedrock-runtime", region_name="us-east-1")
response = bedrock.invoke_model(
    modelId="anthropic.claude-3-5-sonnet-20241022-v2:0",
    body=json.dumps({...}),
    contentType="application/json"
)
```

### 4. Secrets Manager 設定

**シークレット**: `/ai-curated-newsletter/email`

```json
{
  "from_address": "newsletter@example.com",
  "to_address": "user@example.com"
}
```

### 5. EventBridge スケジュール

**ルール名**: `ai-curated-newsletter-schedule`

**スケジュール式**:
```
cron(0 9 * * TUE,FRI *)  # 火曜・金曜 09:00 UTC
```

**ターゲット**: NewsletterFunction Lambda

**入力**:
```json
{
  "command": "run_newsletter",
  "dry_run": false
}
```

### 6. IAM ロール・ポリシー

**ロール名**: `NewsletterLambdaExecutionRole`

**アタッチポリシー**:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DynamoDBAccess",
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:BatchGetItem",
        "dynamodb:Query"
      ],
      "Resource": [
        "arn:aws:dynamodb:us-east-1:ACCOUNT_ID:table/ai-curated-newsletter-cache",
        "arn:aws:dynamodb:us-east-1:ACCOUNT_ID:table/ai-curated-newsletter-history"
      ]
    },
    {
      "Sid": "BedrockAccess",
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel"
      ],
      "Resource": "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-5-sonnet-*"
    },
    {
      "Sid": "SESAccess",
      "Effect": "Allow",
      "Action": [
        "ses:SendEmail"
      ],
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "ses:FromAddress": "newsletter@example.com"
        }
      }
    },
    {
      "Sid": "SecretsManagerAccess",
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue"
      ],
      "Resource": "arn:aws:secretsmanager:us-east-1:ACCOUNT_ID:secret:/ai-curated-newsletter/email*"
    },
    {
      "Sid": "CloudWatchLogs",
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:us-east-1:ACCOUNT_ID:log-group:/aws/lambda/NewsletterFunction:*"
    }
  ]
}
```

## 実装の順序

1. **DynamoDB テーブル作成**
   - キャッシュテーブル
   - 履歴テーブル（TTL設定）
   - PITR 有効化

2. **SES セットアップ**
   - メールアドレス検証
   - サンドボックスモード解除申請

3. **Secrets Manager に機密情報保存**
   - メールアドレス登録

4. **IAM ロール・ポリシー作成**
   - 最小権限ポリシー設定

5. **EventBridge スケジュール設定**
   - スケジュールルール作成
   - Lambda をターゲット登録

6. **ローカル確認**
   - `sam local invoke` で動作確認
   - AWS 認証情報設定確認

## コスト見積もり

| サービス | 推定コスト | 根拠 |
|---------|-----------|------|
| DynamoDB | $0.50 | オンデマンド（読み書き + ストレージ） |
| Bedrock | $4.00 | 週2回 × 120件 × Claude 3.5 Sonnet料金 |
| SES | $0.01 | 週2回 × $0.10/1000通 |
| Lambda | $1.00 | 週2回 × 10分 × 1GB |
| Secrets Manager | $0.40 | 1シークレット × $0.40/月 |
| CloudWatch Logs | $0.50 | ログ保存（5GB/月） |
| EventBridge | $0.00 | 無料枠内（月100万イベント） |
| **合計** | **$6.41** | **余裕あり（$10以内）** |

## セキュリティ考慮事項

- **最小権限**: IAM ポリシーで必要な操作のみ許可
- **暗号化**: DynamoDB, Secrets Manager で自動暗号化
- **ログマスキング**: メールアドレスは structlog でマスキング
- **API キー**: ハードコード禁止、Secrets Manager で管理

## テスト戦略

### ユニットテスト
- DynamoDB モック（moto）を使用
- Bedrock モック
- SES モック

### 統合テスト
- moto で DynamoDB/SES をモック
- 実際の Bedrock 呼び出し（テスト用プロンプト）
- 実行時間計測

### E2E テスト
- `sam local invoke` でローカル実行
- dry_run=true で確認
- 実際の AWS リソースへのアクセス確認

## 依存ライブラリ

追加なし（既存の boto3 で対応）

## 将来の拡張性

### Phase 2 への想定
- Lambda レイヤー化（複数 Lambda に分割）
- Step Functions による処理分割
- CloudFront/API Gateway 追加
- X（Twitter）、GitHub Trending などのソース追加
