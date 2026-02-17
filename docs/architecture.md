# 技術仕様書 (Architecture Design Document)

## テクノロジースタック

### 言語・ランタイム

| 技術 | バージョン | 選定理由 |
|------|-----------|----------|
| Python | 3.14+ | AWS Lambda標準サポート、型ヒント・dataclass・match式など最新機能が利用可能、豊富なライブラリエコシステム |

### AWSサービス

| サービス | 用途 | 選定理由 |
|---------|------|----------|
| AWS Lambda | 実行環境 | サーバーレス、低コスト（実行時のみ課金）、自動スケール、週2-3回の定期実行に最適、15分のタイムアウト（現状の処理時間6-10分に対応可能） |
| AWS EventBridge | スケジューラ | cron形式のスケジュール実行、Lambdaとのネイティブ連携、柔軟な実行頻度設定（週2-3回、曜日・時間指定） |
| Amazon DynamoDB | データストア | サーバーレス、オンデマンドモード（使用量に応じた自動スケール）、低レイテンシ、キャッシュ・履歴保存に最適、月$5以内のコスト目標に対応 |
| AWS Bedrock | LLMサービス | Claude Haiku 4.5へのマネージドアクセス、JSON出力の信頼性、AWSアカウント内で完結（セキュリティ）、従量課金（月$1以内の目標に対応、83%コスト削減） |
| Amazon SES | メール送信 | 低コスト（$0.10/1000通）、高い到達率、HTMLメール対応、バウンス・苦情管理 |
| Amazon S3 | 一時データ保存 | 将来のStep Functions化時のデータ受け渡しに使用（Phase 2）、設定ファイル保存 |
| AWS Secrets Manager | 認証情報管理 | メールアドレス、通知先アドレスの安全な保存、自動ローテーション対応 |

### フレームワーク・ライブラリ

| 技術 | バージョン | 用途 | 選定理由 |
|------|-----------|------|----------|
| boto3 | 1.34+ | AWS SDK | AWS公式SDK、Lambda環境にプリインストール、DynamoDB/Bedrock/SES/Secrets Managerの操作 |
| feedparser | 6.0+ | RSS/Atom解析 | Python標準的なフィードパーサー、広範なフォーマット対応、安定性高い |
| httpx | 0.27+ | HTTPクライアント | async/await対応、タイムアウト・リトライ機能、接続プール管理 |
| structlog | 24.1+ | 構造化ログ | JSON形式ログ出力、CloudWatch Logs連携、run_id単位の追跡に最適 |
| pydantic | 2.6+ | データバリデーション | dataclassとの統合、型安全なバリデーション、JSON schema生成 |

### 開発ツール

| 技術 | バージョン | 用途 | 選定理由 |
|------|-----------|------|----------|
| uv | 0.1+ | 依存関係管理 | Rust製の超高速パッケージマネージャー、pip/pip-tools互換、pyproject.toml対応、依存解決が10-100倍高速（Astral社、ruffと同じ開発元） |
| mypy | 1.8+ | 静的型チェック | 型ヒントの検証、バグの早期発見、IDEサポート向上 |
| pytest | 8.0+ | テストフレームワーク | Python標準的なテストツール、豊富なプラグイン、モック機能 |
| pytest-asyncio | 0.23+ | 非同期テスト | async/awaitのテストサポート |
| ruff | 0.2+ | リンター/フォーマッター | Rust製の高速ツール、Flake8・Black・isort等を統合、設定が簡潔 |
| AWS SAM CLI | 1.110+ | Lambdaローカル実行 | ローカル環境でのテスト、デプロイ自動化 |

## アーキテクチャパターン

### Phase 1（MVP）: 単一Lambda構成

```
┌─────────────────────────────────────────────────────────┐
│ EventBridge Scheduler (週2-3回)                          │
└────────────────────┬────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────┐
│ Lambda Function (Python 3.14)                           │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ Handler                                             │ │
│ └────────┬────────────────────────────────────────────┘ │
│          ↓                                               │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ Orchestrator                                        │ │
│ │  ├─ Step 1: Collect & Normalize                    │ │
│ │  ├─ Step 2: Deduplicate                            │ │
│ │  ├─ Step 3: Calculate Buzz Score                   │ │
│ │  ├─ Step 4: Select Candidates                      │ │
│ │  ├─ Step 5: LLM Judge (最大150件)                  │ │
│ │  ├─ Step 6: Final Select (最大15件)                │ │
│ │  ├─ Step 7: Format & Notify                        │ │
│ │  └─ Step 8: Save History                           │ │
│ └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
         │              │              │
         ↓              ↓              ↓
    ┌────────┐    ┌─────────┐    ┌──────┐
    │DynamoDB│    │ Bedrock │    │ SES  │
    └────────┘    └─────────┘    └──────┘
```

**特徴:**
- シンプルな構成（個人開発の原則に準拠）
- 単一Lambdaで全処理を実行
- 現状の処理時間（6-10分）は15分制限内に収まる
- コスト最小（Lambda実行時間の課金のみ）

### Phase 2（将来）: Step Functions構成

将来的に処理時間が伸びた場合、Step Functions化に移行可能な設計：

```
┌─────────────────────────────────────────────────────────┐
│ EventBridge Scheduler (週2-3回)                          │
└────────────────────┬────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────┐
│ Step Functions State Machine                            │
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │ Lambda 1: CollectAndPrepare                    │    │
│  │  - RSS/Atom収集                                │    │
│  │  - 正規化・重複排除                            │    │
│  │  - Buzzスコア計算・候補選定                    │    │
│  │  - S3に候補リスト保存                          │    │
│  └────────────────┬───────────────────────────────┘    │
│                   ↓ (S3経由)                             │
│  ┌────────────────────────────────────────────────┐    │
│  │ Lambda 2: JudgeArticles                        │    │
│  │  - S3から候補リスト読み込み                    │    │
│  │  - LLM判定（並列処理）                         │    │
│  │  - DynamoDBキャッシュ保存                      │    │
│  │  - S3に判定結果保存                            │    │
│  └────────────────┬───────────────────────────────┘    │
│                   ↓ (S3経由)                             │
│  ┌────────────────────────────────────────────────┐    │
│  │ Lambda 3: SelectAndNotify                      │    │
│  │  - S3から判定結果読み込み                      │    │
│  │  - 最終選定・フォーマット                      │    │
│  │  - メール送信・履歴保存                        │    │
│  └────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

**移行トリガー:**
- 実行時間が12分を超える場合
- 収集元が大幅に増える場合
- LLM判定対象を150件以上に拡大する場合

**移行コスト:**
- Step Functions: 月24遷移 × $0.000025 = $0.0006
- S3: 一時データ保存（月$0.01未満）
- 合計: ほぼ無視できる追加コスト

### レイヤードアーキテクチャ（コンポーネント設計）

```
┌─────────────────────────────────────────────────────────┐
│ Orchestration Layer                                     │
│  - Orchestrator: 全体フロー制御                          │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────┴────────────────────────────────────┐
│ Service Layer（ビジネスロジック）                       │
│  - Collector: RSS/Atom収集                              │
│  - Normalizer: 正規化                                   │
│  - Deduplicator: 重複排除                               │
│  - BuzzScorer: 話題性スコア計算                         │
│  - CandidateSelector: 候補選定                          │
│  - LlmJudge: LLM判定                                    │
│  - FinalSelector: 最終選定                              │
│  - Formatter: メール本文生成                            │
│  - Notifier: メール送信                                 │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────┴────────────────────────────────────┐
│ Data Layer（データ永続化）                               │
│  - CacheRepository: 判定キャッシュ（DynamoDB）          │
│  - HistoryRepository: 実行履歴（DynamoDB）              │
│  - SourceMaster: 収集元マスタ（設定ファイル）            │
└─────────────────────────────────────────────────────────┘
```

**レイヤー分離の原則:**
- Orchestration → Service → Data（一方向の依存）
- Service層はData層のみに依存
- Data層は外部依存なし（DynamoDB/S3へのアクセスのみ）

## データ永続化戦略

### DynamoDB テーブル設計

#### テーブル1: 判定キャッシュ

| 項目 | 説明 |
|------|------|
| **テーブル名** | `ai-curated-newsletter-cache` |
| **課金モード** | オンデマンド（使用量に応じた自動スケール） |
| **PK** | `URL#<sha256(url)>` |
| **SK** | `JUDGMENT#v1` |

**属性:**
```python
{
  "url": "https://example.com/article",
  "interest_label": "ACT_NOW",
  "buzz_label": "HIGH",
  "confidence": 0.85,
  "reason": "PostgreSQLのインデックス戦略について実践的な知見",
  "model_id": "anthropic.claude-haiku-4-5-20251001-v1:0",
  "judged_at": "2025-01-15T10:30:00Z",
  "title": "PostgreSQL Index Strategies",
  "source_name": "Hacker News"
}
```

**TTL:** なし（永続的にキャッシュ、再判定禁止の原則）

**推定コスト:**
- 週2回実行 × 120件判定 = 月960件書き込み
- 月960件 × $1.25/百万 = $0.0012
- 読み込み（重複チェック）: 週2回 × 400件 = 月3200件 × $0.25/百万 = $0.0008
- 合計: **月$0.002**

#### テーブル2: 実行履歴

| 項目 | 説明 |
|------|------|
| **テーブル名** | `ai-curated-newsletter-history` |
| **課金モード** | オンデマンド |
| **PK** | `RUN#<YYYYWW>` (例: `RUN#202503`) |
| **SK** | `SUMMARY#<timestamp>` |

**属性:**
```python
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
  "estimated_cost_usd": 0.42
}
```

**TTL:** 90日（古い履歴は自動削除）

**推定コスト:**
- 週2回実行 = 月8件書き込み × $1.25/百万 = $0.00001
- 合計: **月$0.00001**

### S3 バケット設計（Phase 2用）

| バケット | 用途 | ライフサイクル |
|---------|------|--------------|
| `ai-curated-newsletter-temp` | Lambda間データ受け渡し | 1日後に自動削除 |
| `ai-curated-newsletter-config` | 収集元マスタ設定 | 永続保存 |

**Phase 1では未使用**（Phase 2移行時に作成）

### バックアップ戦略

**DynamoDB Point-in-Time Recovery (PITR):**
- 有効化: Yes
- 保存期間: 35日間
- 追加コスト: ストレージサイズに応じて（推定月$0.20）

**目的:**
- 誤削除・障害時の復旧
- 判定キャッシュの保護（再判定禁止の原則）

## パフォーマンス要件

### レスポンスタイム目標

| 処理 | 目標時間 | 測定環境 | 備考 |
|------|---------|---------|------|
| RSS/Atom収集（全ソース） | 30秒以内 | Lambda 1024MB | 並列収集、各ソース10秒タイムアウト |
| 正規化・重複排除 | 10秒以内 | Lambda 1024MB | DynamoDB BatchGetItem使用 |
| Buzzスコア計算 | 5秒以内 | Lambda 1024MB | 純粋な計算処理 |
| LLM判定（120件） | 5分以内 | Lambda 1024MB | 並列5件ずつ、24バッチ |
| 最終選定・フォーマット・通知 | 30秒以内 | Lambda 1024MB | SES送信含む |
| **全体実行時間** | **10分以内（目標）** | Lambda 1024MB | **15分制限の67%** |

### Lambda設定

| 設定項目 | 値 | 理由 |
|---------|---|------|
| メモリ | 1024MB | コスト効率とパフォーマンスのバランス（2048MBでは過剰、512MBでは不足） |
| タイムアウト | 15分（900秒） | 最大値を設定（実際は10分目標） |
| 同時実行数 | 1 | 週2-3回の定期実行のため、同時実行は不要 |
| 環境変数 | 以下を設定 | |

**環境変数:**
```bash
ENVIRONMENT=production
LOG_LEVEL=INFO
DYNAMODB_CACHE_TABLE=ai-curated-newsletter-cache
DYNAMODB_HISTORY_TABLE=ai-curated-newsletter-history
SOURCE_CONFIG_S3_BUCKET=ai-curated-newsletter-config
SOURCE_CONFIG_S3_KEY=sources.yaml
BEDROCK_MODEL_ID=anthropic.claude-haiku-4-5-20251001-v1:0
BEDROCK_MAX_PARALLEL=5
LLM_CANDIDATE_MAX=150
FINAL_SELECT_MAX=15
FINAL_SELECT_MAX_PER_DOMAIN=0  # 0=制限なし、正の整数で制限を有効化
```

### リソース使用量

| リソース | 予想使用量 | 上限 | 理由 |
|---------|-----------|------|------|
| メモリ | 600-800MB | 1024MB | フィード解析、JSON処理、LLM応答の一時保存 |
| CPU | 60-80% | 100% | LLM API待機時間が多いため、CPU使用率は低め |
| ネットワーク | 20-30MB | 無制限 | RSS/Atom取得（数MB）、Bedrock API（数MB） |

## セキュリティアーキテクチャ

### データ保護

**機密情報管理:**
```
AWS Secrets Manager:
- secret/ai-curated-newsletter/email
  - to_address: 通知先メールアドレス
  - from_address: 送信元メールアドレス（SES検証済み）
```

**DynamoDBアクセス制御:**
- Lambda実行ロールに最小権限付与
- 許可操作: `GetItem`, `PutItem`, `BatchGetItem`, `Query`（2テーブルのみ）
- 拒否操作: `Scan`, `DeleteTable`, `UpdateTable`

**Bedrockアクセス制御:**
- 許可操作: `InvokeModel`（Claude Haiku 4.5のみ）
- リージョン制限: `us-east-1`のみ

### 入力検証

**収集元マスタのバリデーション:**
```python
from enum import Enum
from pydantic import BaseModel, HttpUrl, Field


class FeedType(str, Enum):
    """フィード種別."""
    RSS = "rss"
    ATOM = "atom"


class Priority(str, Enum):
    """優先度."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class SourceConfig(BaseModel):
    """収集元設定（バリデーション付き）."""
    source_id: str = Field(min_length=1, max_length=50, pattern="^[a-z0-9_]+$")
    name: str = Field(min_length=1, max_length=100)
    feed_url: HttpUrl  # URLフォーマット検証
    feed_type: FeedType
    priority: Priority
    timeout_seconds: int = Field(ge=5, le=30)  # 5-30秒
    retry_count: int = Field(ge=0, le=5)  # 0-5回
    enabled: bool
```

**LLM出力のバリデーション:**
```python
from enum import Enum
from pydantic import BaseModel, Field


class InterestLabel(str, Enum):
    """関心度ラベル."""
    ACT_NOW = "ACT_NOW"
    THINK = "THINK"
    FYI = "FYI"
    IGNORE = "IGNORE"


class BuzzLabel(str, Enum):
    """話題性ラベル."""
    HIGH = "HIGH"
    MID = "MID"
    LOW = "LOW"


class JudgmentOutput(BaseModel):
    """LLM判定出力（バリデーション付き）."""
    interest_label: InterestLabel
    buzz_label: BuzzLabel
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str = Field(min_length=1, max_length=200)
```

### ログマスキング

**機密情報のマスキング:**
```python
import structlog

# メールアドレスをマスク
def mask_email(email: str) -> str:
    """メールアドレスをマスクする."""
    local, domain = email.split("@")
    return f"{local[:2]}***@{domain}"

logger.info(
    "notification_sent",
    to_address=mask_email(to_address),  # "us***@example.com"
    article_count=10
)
```

## スケーラビリティ設計

### データ増加への対応

**想定データ量:**
- 判定キャッシュ: 年間5,000件 × 5年 = 25,000件（約10MB）
- 実行履歴: 年間100件 × 5年 = 500件（約1MB）

**パフォーマンス劣化対策:**
- DynamoDBオンデマンドモード（自動スケール）
- BatchGetItemによる一括取得（最大100件/リクエスト）
- GSI不要（単純なPK/SK検索のみ）

**アーカイブ戦略:**
- 実行履歴はTTL 90日で自動削除
- 判定キャッシュは永続保存（再判定禁止の原則）
- 5年後に25,000件でも性能問題なし

### 収集元の拡張性

**Phase 1（MVP）:**
- 収集元マスタ: S3上のJSON設定ファイル（`sources.yaml`）
- 手動編集 → S3アップロード → Lambda再起動

**Phase 2（拡張）:**
- 収集元マスタ: DynamoDBテーブル
- 管理UI/CLIで動的に追加・削除
- Lambda再起動不要

### 機能拡張の方向性

**Phase 2以降の拡張候補:**
1. **Step Functions化**: 処理時間が伸びた場合（前述）
2. **フィードバック機能**: 通知記事の評価収集（PRD Phase 2参照）
3. **近似重複排除**: Embedding + ベクトル検索（コスト要検証）
4. **マルチユーザー対応**: DynamoDBにuser_id追加（スコープ外）

## テスト戦略

### ユニットテスト

**フレームワーク:** pytest + pytest-asyncio

**対象コンポーネント:**
- Normalizer: URL正規化、日時変換
- BuzzScorer: スコア計算ロジック
- FinalSelector: 選定ロジック、ドメイン偏り制御
- Formatter: メール本文生成

**カバレッジ目標:** 90%以上

**モック対象:**
- DynamoDB（boto3.dynamodb.Table）
- Bedrock（boto3.bedrock_runtime）
- SES（boto3.ses）

**実装例:**
```python
import pytest
from datetime import datetime, timezone
from buzz_scorer import BuzzScorer

def test_calculate_recency_score():
    """鮮度スコア計算のテスト."""
    scorer = BuzzScorer()

    # 本日公開: 100点
    now = datetime.now(timezone.utc)
    assert scorer.calculate_recency_score(now) == 100.0

    # 3日前: 70点
    three_days_ago = now - timedelta(days=3)
    assert scorer.calculate_recency_score(three_days_ago) == 70.0

    # 10日以上前: 0点
    old = now - timedelta(days=15)
    assert scorer.calculate_recency_score(old) == 0.0
```

### 統合テスト

**方法:** moto（AWSサービスのモック）

**対象フロー:**
- 収集 → 正規化 → 重複排除（DynamoDB連携）
- LLM判定 → キャッシュ保存（DynamoDB連携）
- 最終選定 → フォーマット → 通知（SESモック）

**実装例:**
```python
import pytest
from moto import mock_dynamodb, mock_ses
import boto3

@mock_dynamodb
def test_cache_repository():
    """キャッシュリポジトリの統合テスト."""
    # DynamoDBテーブル作成（motoでモック）
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
    table = dynamodb.create_table(
        TableName="test-cache",
        KeySchema=[
            {"AttributeName": "PK", "KeyType": "HASH"},
            {"AttributeName": "SK", "KeyType": "RANGE"}
        ],
        AttributeDefinitions=[
            {"AttributeName": "PK", "AttributeType": "S"},
            {"AttributeName": "SK", "AttributeType": "S"}
        ],
        BillingMode="PAY_PER_REQUEST"
    )

    # テスト実行
    repo = CacheRepository(dynamodb, "test-cache")
    judgment = JudgmentResult(...)
    repo.put(judgment)

    result = repo.get(judgment.url)
    assert result.interest_label == judgment.interest_label

@mock_ses
def test_notifier():
    """通知機能の統合テスト."""
    ses = boto3.client("ses", region_name="us-east-1")
    # SES検証済みメールアドレスを追加（motoモック用）
    ses.verify_email_identity(EmailAddress="test@example.com")

    notifier = Notifier(ses)
    result = notifier.send(NotificationInput(...))
    assert result.success is True
```

### E2Eテスト

**ツール:** AWS SAM CLI（ローカルLambda実行）

**シナリオ:**
1. **正常系（dry_run=true）:**
   - 全ソース収集成功
   - LLM判定成功（モック使用）
   - 通知スキップ（dry_run）
   - 実行履歴保存確認

2. **異常系:**
   - 一部ソース収集失敗 → 他ソース継続
   - LLM判定失敗 → IGNORE扱い
   - 通知失敗 → エラーログ確認

**実行方法:**
```bash
# ローカル実行
sam local invoke NewsletterFunction \
  --event events/test_event.json \
  --env-vars env.json

# DynamoDB Local連携
docker-compose up dynamodb-local
sam local invoke --docker-network sam-network
```

### パフォーマンステスト

**目標:**
- 全体実行時間: 10分以内
- メモリ使用量: 1024MB以内

**測定方法:**
```python
import time
import structlog

logger = structlog.get_logger()

def measure_execution_time(func):
    """実行時間を測定するデコレーター."""
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        logger.info(
            "execution_time",
            function=func.__name__,
            elapsed_seconds=elapsed
        )
        return result
    return wrapper
```

## 技術的制約

### 環境要件

| 項目 | 要件 |
|------|------|
| AWSリージョン | ap-northeast-1（Bedrock Claude Haiku 4.5利用可能） |
| Lambda ランタイム | Python 3.14 |
| Lambda メモリ | 1024MB |
| Lambda タイムアウト | 15分 |
| DynamoDB | オンデマンドモード |
| SES | 本番環境から移行（サンドボックス解除済み） |

### パフォーマンス制約

| 項目 | 制約 | 理由 |
|------|------|------|
| Lambda実行時間 | 15分以内 | AWS Lambda最大タイムアウト |
| LLM判定対象 | 最大150件 | コスト制約（月$4）、処理時間制約（5分以内） |
| 最終通知件数 | 最大15件 | 出力最小主義の原則（PRD絶対制約） |
| Bedrock並列度 | 5件 | レート制限・安定性のバランス |
| RSS/Atomタイムアウト | 10秒/ソース | 全体実行時間への影響を最小化 |

### セキュリティ制約

| 項目 | 制約 |
|------|------|
| 機密情報管理 | AWS Secrets Manager必須（ハードコード禁止） |
| ログ出力 | メールアドレスのマスキング必須 |
| IAMロール | 最小権限の原則（必要な操作のみ許可） |
| VPC | 不要（パブリックAPIのみ使用） |

### コスト制約

**月額上限:** $10（PRD絶対制約）

**内訳:**
| サービス | 推定コスト | 根拠 |
|---------|-----------|------|
| Lambda | $1.00 | 週2回 × 10分 × $0.0000166667/GB秒 × 1GB |
| DynamoDB | $0.50 | オンデマンド（読み書き + ストレージ） |
| Bedrock | $0.70 | 週2回 × 120件 × Claude Haiku 4.5料金（input $1.00/1M, output $5.00/1M） |
| SES | $0.01 | 週2回 × $0.10/1000通 |
| Secrets Manager | $0.40 | 1シークレット × $0.40/月 |
| S3 | $0.10 | 設定ファイル保存（Phase 2で一時データ追加） |
| EventBridge | $0.00 | 無料枠内（月100万イベント） |
| CloudWatch Logs | $0.50 | ログ保存（5GB/月） |
| **合計** | **$3.21** | **大幅削減（$10以内、従来比$3.30削減）** |

## 依存関係管理

### バージョン管理方針

**pyproject.toml:**
```toml
[project]
name = "ai-curated-newsletter"
version = "0.1.0"
requires-python = ">=3.14"
dependencies = [
    "boto3>=1.34.0",
    "feedparser>=6.0.0",
    "httpx>=0.27.0",
    "structlog>=24.1.0",
    "pydantic>=2.6.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "mypy>=1.8.0",
    "ruff>=0.2.0",
    "moto>=5.0.0",
    "boto3-stubs>=1.34.0",
]
```

**依存関係管理コマンド（uv）:**
```bash
# 依存関係のインストール
uv pip install -e .

# 開発依存関係のインストール
uv pip install -e ".[dev]"

# requirements.txt 生成（Lambda デプロイ用）
uv pip compile pyproject.toml -o requirements.txt

# 依存関係の更新
uv pip compile --upgrade pyproject.toml -o requirements.txt
uv pip sync requirements.txt
```

**方針:**
- `>=` で最低バージョンを指定（柔軟性とセキュリティパッチ対応）
- boto3は頻繁に更新されるため最低バージョンのみ指定
- requirements.txt で厳密なバージョン固定（再現性）
- 月次で依存関係を更新（`uv pip compile --upgrade`）
- uvの超高速依存解決（Rust製、Poetry比10-100倍高速）

### Lambda レイヤー構成

**レイヤー1: 依存ライブラリ**
- feedparser
- httpx
- structlog
- pydantic

**レイヤー2: boto3（オプション）**
- Lambda環境にプリインストールされているが、バージョン固定のため含める

**サイズ制約:**
- 合計50MB以内（ZIP圧縮後）
- 超過する場合はDocker Lambdaを検討

## デプロイ戦略

### Infrastructure as Code

**ツール:** AWS SAM (Serverless Application Model)

**template.yaml 概要:**
```yaml
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31

Globals:
  Function:
    Runtime: python3.14
    MemorySize: 1024
    Timeout: 900
    Environment:
      Variables:
        ENVIRONMENT: production
        LOG_LEVEL: INFO

Resources:
  NewsletterFunction:
    Type: AWS::Serverless::Function
    Properties:
      Handler: src.handler.lambda_handler
      Policies:
        - DynamoDBCrudPolicy:
            TableName: !Ref CacheTable
        - DynamoDBCrudPolicy:
            TableName: !Ref HistoryTable
        - Statement:
            - Effect: Allow
              Action: bedrock:InvokeModel
              Resource: !Sub arn:aws:bedrock:${AWS::Region}::foundation-model/anthropic.claude-haiku-4-5-*
        - SESCrudPolicy:
            IdentityName: !Ref SenderEmail
        - AWSSecretsManagerGetSecretValuePolicy:
            SecretArn: !Ref EmailSecret
      Events:
        Schedule:
          Type: Schedule
          Properties:
            Schedule: cron(0 9 * * TUE,FRI *)  # 火曜・金曜 09:00 UTC

  CacheTable:
    Type: AWS::DynamoDB::Table
    Properties:
      TableName: ai-curated-newsletter-cache
      BillingMode: PAY_PER_REQUEST
      AttributeDefinitions:
        - AttributeName: PK
          AttributeType: S
        - AttributeName: SK
          AttributeType: S
      KeySchema:
        - AttributeName: PK
          KeyType: HASH
        - AttributeName: SK
          KeyType: RANGE
      PointInTimeRecoverySpecification:
        PointInTimeRecoveryEnabled: true

  HistoryTable:
    Type: AWS::DynamoDB::Table
    Properties:
      TableName: ai-curated-newsletter-history
      BillingMode: PAY_PER_REQUEST
      AttributeDefinitions:
        - AttributeName: PK
          AttributeType: S
        - AttributeName: SK
          AttributeType: S
      KeySchema:
        - AttributeName: PK
          KeyType: HASH
        - AttributeName: SK
          KeyType: RANGE
      TimeToLiveSpecification:
        Enabled: true
        AttributeName: ttl
```

### CI/CD パイプライン（Phase 2）

**Phase 1:** 手動デプロイ
```bash
# 依存関係のインストール
uv pip install -e ".[dev]"

# テスト
pytest
mypy src/

# Lambda デプロイ用requirements.txt生成
uv pip compile pyproject.toml -o requirements.txt

# デプロイ
sam build
sam deploy --guided
```

**Phase 2:** GitHub Actions
- プルリクエスト: テスト実行
- mainブランチマージ: 自動デプロイ

## モニタリング・アラート

### CloudWatch Logs

**ログ構造:**
```json
{
  "timestamp": "2025-01-15T09:00:00.000Z",
  "level": "info",
  "event": "orchestrator_started",
  "run_id": "550e8400-e29b-41d4-a716-446655440000",
  "dry_run": false
}
```

**保存期間:** 30日

### CloudWatch Metrics

**カスタムメトリクス:**
- `CollectedArticleCount`: 収集件数
- `LlmJudgedCount`: LLM判定件数
- `FinalSelectedCount`: 最終選定件数
- `ExecutionTimeSeconds`: 実行時間
- `EstimatedCostUSD`: 推定コスト

### アラート設定（Phase 2）

**SNS トピック:** `ai-curated-newsletter-alerts`

**アラート条件:**
1. Lambda実行失敗
2. 実行時間が12分を超える
3. 最終選定件数が0件（3回連続）

## 将来の拡張パス

### Step Functions化への移行手順

1. **準備:**
   - S3バケット作成（`ai-curated-newsletter-temp`）
   - Orchestratorを3つのLambdaに分割

2. **Lambda分割:**
   ```
   Lambda 1: collect_and_prepare.py
   Lambda 2: judge_articles.py
   Lambda 3: select_and_notify.py
   ```

3. **State Machine定義:**
   ```yaml
   StartAt: CollectAndPrepare
   States:
     CollectAndPrepare:
       Type: Task
       Resource: !GetAtt Lambda1.Arn
       Next: JudgeArticles

     JudgeArticles:
       Type: Task
       Resource: !GetAtt Lambda2.Arn
       Next: SelectAndNotify

     SelectAndNotify:
       Type: Task
       Resource: !GetAtt Lambda3.Arn
       End: true
   ```

4. **EventBridge変更:**
   - Lambda直接実行 → Step Functions実行

5. **テスト・デプロイ:**
   - dry_runモードで動作確認
   - 本番環境デプロイ

### コスト影響

**追加コスト:**
- Step Functions: 月$0.0006
- S3: 月$0.01

**合計:** 月$3.22（大幅削減、依然として$10以内）
