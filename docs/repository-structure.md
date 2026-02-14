# リポジトリ構造定義書 (Repository Structure Document)

## プロジェクト構造

```
ai-curated-newsletter/
├── src/                      # ソースコード
│   ├── handler.py            # Lambda エントリーポイント
│   ├── orchestrator/         # オーケストレーションレイヤー
│   │   ├── __init__.py
│   │   └── orchestrator.py   # 全体フロー制御
│   ├── services/             # サービスレイヤー（ビジネスロジック）
│   │   ├── __init__.py
│   │   ├── collector.py      # RSS/Atom収集
│   │   ├── normalizer.py     # 正規化
│   │   ├── deduplicator.py   # 重複排除
│   │   ├── buzz_scorer.py    # Buzzスコア計算
│   │   ├── candidate_selector.py  # 候補選定
│   │   ├── llm_judge.py      # LLM判定
│   │   ├── final_selector.py # 最終選定
│   │   ├── formatter.py      # メール本文生成
│   │   └── notifier.py       # メール送信
│   ├── repositories/         # データレイヤー（データ永続化）
│   │   ├── __init__.py
│   │   ├── cache_repository.py    # 判定キャッシュ（DynamoDB）
│   │   ├── history_repository.py  # 実行履歴（DynamoDB）
│   │   └── source_master.py       # 収集元マスタ（S3/設定ファイル）
│   ├── models/               # データモデル（dataclass）
│   │   ├── __init__.py
│   │   ├── article.py        # 記事エンティティ
│   │   ├── judgment.py       # 判定結果エンティティ
│   │   ├── buzz_score.py     # Buzzスコアエンティティ
│   │   ├── execution_summary.py   # 実行サマリ
│   │   └── source_config.py  # 収集元設定
│   └── shared/               # 共通ユーティリティ
│       ├── __init__.py
│       ├── utils/            # 汎用ユーティリティ
│       │   ├── __init__.py
│       │   ├── url_normalizer.py  # URL正規化
│       │   └── date_utils.py      # 日時ユーティリティ
│       ├── logging/          # ログ設定
│       │   ├── __init__.py
│       │   └── logger.py     # structlog設定
│       └── exceptions/       # カスタム例外
│           ├── __init__.py
│           ├── collection_error.py
│           ├── llm_error.py
│           └── notification_error.py
├── tests/                    # テストコード
│   ├── __init__.py
│   ├── unit/                 # ユニットテスト
│   │   ├── __init__.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── test_normalizer.py
│   │   │   ├── test_buzz_scorer.py
│   │   │   └── test_final_selector.py
│   │   ├── repositories/
│   │   │   ├── __init__.py
│   │   │   ├── test_cache_repository.py
│   │   │   └── test_history_repository.py
│   │   └── shared/
│   │       ├── __init__.py
│   │       └── utils/
│   │           ├── __init__.py
│   │           └── test_url_normalizer.py
│   ├── integration/          # 統合テスト
│   │   ├── __init__.py
│   │   ├── test_collection_flow.py       # 収集→正規化→重複排除
│   │   ├── test_judgment_flow.py         # LLM判定→キャッシュ保存
│   │   └── test_notification_flow.py     # 最終選定→フォーマット→通知
│   └── e2e/                  # E2Eテスト
│       ├── __init__.py
│       ├── test_normal_flow.py           # 正常系フロー
│       └── test_error_handling_flow.py   # 異常系フロー
├── config/                   # 設定ファイル
│   └── sources.yaml          # 収集元マスタ（Phase 1）
├── docs/                     # プロジェクトドキュメント
│   ├── product-requirements.md
│   ├── functional-design.md
│   ├── architecture.md
│   ├── repository-structure.md  # 本ドキュメント
│   ├── development-guidelines.md
│   ├── glossary.md
│   └── ideas/                # アイデア・下書き
│       └── initial-request.md
├── .claude/                  # Claude Code設定
│   ├── CLAUDE.md             # プロジェクト固有指示
│   └── skills/               # カスタムスキル
├── .steering/                # ステアリングファイル（作業管理）
│   └── [YYYYMMDD]-[task]/    # 作業単位のディレクトリ
│       ├── requirements.md
│       ├── design.md
│       └── tasklist.md
├── template.yaml             # AWS SAM テンプレート
├── pyproject.toml            # Python依存関係定義（uv）
├── requirements.txt          # Lambda デプロイ用（uv pip compile生成）
├── .gitignore
├── README.md
└── LICENSE
```

## ディレクトリ詳細

### src/ (ソースコードディレクトリ)

#### handler.py (Lambda エントリーポイント)

**役割**: AWS Lambda のエントリーポイント。イベント受信、Orchestrator呼び出し、レスポンス返却

**配置ファイル**:
- `handler.py`: Lambda ハンドラー関数 `lambda_handler(event, context)`

**依存関係**:
- 依存可能: `orchestrator/`, `shared/`
- 依存禁止: `services/`, `repositories/`（Orchestrator経由でのみアクセス）

**例**:
```python
# src/handler.py
import structlog
from orchestrator.orchestrator import Orchestrator

logger = structlog.get_logger()

def lambda_handler(event: dict, context: Any) -> dict:
    """Lambda ハンドラー関数.

    Args:
        event: Lambda イベント
        context: Lambda コンテキスト

    Returns:
        レスポンス辞書
    """
    logger.info("lambda_invoked", event=event)

    # Orchestrator初期化・実行
    orchestrator = Orchestrator()
    result = orchestrator.execute(event)

    return {
        "statusCode": 200 if result.success else 500,
        "body": {"run_id": result.run_id}
    }
```

#### orchestrator/ (オーケストレーションレイヤー)

**役割**: 全体フローの制御、各サービスの呼び出し順序管理、エラーハンドリング

**配置ファイル**:
- `orchestrator.py`: Orchestrator クラス

**命名規則**:
- クラス名: `Orchestrator`
- ファイル名: `orchestrator.py`

**依存関係**:
- 依存可能: `services/`, `repositories/`, `models/`, `shared/`
- 依存禁止: なし（最上位レイヤー）

**例**:
```python
# src/orchestrator/orchestrator.py
from dataclasses import dataclass
from services.collector import Collector
from services.normalizer import Normalizer
from models.article import Article

@dataclass
class OrchestratorResult:
    """Orchestrator実行結果."""
    run_id: str
    success: bool
    summary: ExecutionSummary

class Orchestrator:
    """全体フロー制御."""

    def execute(self, event: dict) -> OrchestratorResult:
        """ニュースレター実行フローを実行する."""
        # ステップ1: 収集
        articles = self.collector.collect()

        # ステップ2: 正規化
        normalized = self.normalizer.normalize(articles)

        # ... 以降のステップ
```

#### services/ (サービスレイヤー)

**役割**: ビジネスロジックの実装（収集、正規化、判定、通知等）

**配置ファイル**:
- `collector.py`: RSS/Atom収集
- `normalizer.py`: 記事情報の正規化
- `deduplicator.py`: 重複排除
- `buzz_scorer.py`: 話題性スコア計算（非LLM）
- `candidate_selector.py`: LLM判定候補の選定
- `llm_judge.py`: LLM判定
- `final_selector.py`: 最終選定（最大15件）
- `formatter.py`: メール本文生成
- `notifier.py`: メール送信（SES）

**命名規則**:
- クラス名: PascalCase（例: `RssCollector`, `LlmJudge`）
- ファイル名: snake_case（例: `llm_judge.py`）

**依存関係**:
- 依存可能: `repositories/`, `models/`, `shared/`
- 依存禁止: `orchestrator/`（上位レイヤーへの依存禁止）

**例**:
```python
# src/services/normalizer.py
from typing import List
from models.article import Article
from shared.utils.url_normalizer import normalize_url

class Normalizer:
    """記事情報の正規化."""

    def normalize(self, articles: List[Article]) -> List[Article]:
        """記事リストを正規化する.

        Args:
            articles: 正規化前の記事リスト

        Returns:
            正規化された記事リスト
        """
        normalized = []
        for article in articles:
            article.url = normalize_url(article.url)
            # ... その他の正規化処理
            normalized.append(article)
        return normalized
```

#### repositories/ (データレイヤー)

**役割**: データの永続化と取得（DynamoDB、S3、設定ファイル）

**配置ファイル**:
- `cache_repository.py`: 判定キャッシュの読み書き（DynamoDB）
- `history_repository.py`: 実行履歴の保存（DynamoDB）
- `source_master.py`: 収集元マスタの読み込み（S3/設定ファイル）

**命名規則**:
- クラス名: `[Entity]Repository`（例: `CacheRepository`）
- ファイル名: `[entity]_repository.py`（例: `cache_repository.py`）

**依存関係**:
- 依存可能: `models/`, `shared/`
- 依存禁止: `services/`, `orchestrator/`

**例**:
```python
# src/repositories/cache_repository.py
from typing import Optional
import boto3
from models.judgment import JudgmentResult

class CacheRepository:
    """判定キャッシュリポジトリ."""

    def __init__(self, dynamodb_client: Any, table_name: str) -> None:
        """リポジトリを初期化する.

        Args:
            dynamodb_client: DynamoDB クライアント
            table_name: テーブル名
        """
        self.dynamodb = dynamodb_client
        self.table_name = table_name

    def get(self, url: str) -> Optional[JudgmentResult]:
        """キャッシュから判定結果を取得する."""
        # DynamoDB GetItem
        ...

    def put(self, judgment: JudgmentResult) -> None:
        """判定結果をキャッシュに保存する."""
        # DynamoDB PutItem
        ...
```

#### models/ (データモデル)

**役割**: ドメインエンティティの定義（dataclass）

**配置ファイル**:
- `article.py`: 記事エンティティ
- `judgment.py`: 判定結果エンティティ
- `buzz_score.py`: Buzzスコアエンティティ
- `execution_summary.py`: 実行サマリ
- `source_config.py`: 収集元設定

**命名規則**:
- クラス名: PascalCase（例: `Article`, `JudgmentResult`）
- ファイル名: snake_case（例: `article.py`, `judgment.py`）

**依存関係**:
- 依存可能: なし（他のレイヤーに依存しない）
- 依存禁止: すべて

**例**:
```python
# src/models/article.py
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Article:
    """記事エンティティ.

    Attributes:
        url: 正規化されたURL（一意キー）
        title: 記事タイトル
        published_at: 公開日時（UTC）
        source_name: ソース名
        description: 記事の概要（最大800文字）
        normalized_url: 正規化前の元URL
        collected_at: 収集日時（UTC）
    """
    url: str
    title: str
    published_at: datetime
    source_name: str
    description: str
    normalized_url: str
    collected_at: datetime
```

#### shared/ (共通ユーティリティ)

**役割**: 複数のレイヤーで使用される共通機能

**配置ファイル**:
- `utils/`: 汎用ユーティリティ関数
  - `url_normalizer.py`: URL正規化
  - `date_utils.py`: 日時ユーティリティ
- `logging/`: ログ設定
  - `logger.py`: structlog設定
- `exceptions/`: カスタム例外
  - `collection_error.py`: 収集エラー
  - `llm_error.py`: LLM判定エラー
  - `notification_error.py`: 通知エラー

**命名規則**:
- 関数ファイル: snake_case + 動詞（例: `normalize_url.py`）
- 例外クラス: PascalCase + Error（例: `CollectionError`）

**依存関係**:
- 依存可能: 標準ライブラリ、外部ライブラリのみ
- 依存禁止: `orchestrator/`, `services/`, `repositories/`, `models/`

**例**:
```python
# src/shared/utils/url_normalizer.py
from urllib.parse import urlparse, urlunparse

def normalize_url(url: str) -> str:
    """URLを正規化する.

    - クエリパラメータ除去（utm_*等）
    - スキーム統一（https）
    - トレーリングスラッシュ除去

    Args:
        url: 正規化前URL

    Returns:
        正規化されたURL
    """
    parsed = urlparse(url)
    # 正規化処理
    return urlunparse(parsed)
```

### tests/ (テストディレクトリ)

#### unit/

**役割**: 単一コンポーネントのユニットテスト（モック使用）

**構造**:
```
tests/unit/
├── __init__.py
├── services/
│   ├── __init__.py
│   ├── test_normalizer.py
│   ├── test_buzz_scorer.py
│   └── test_final_selector.py
├── repositories/
│   ├── __init__.py
│   ├── test_cache_repository.py
│   └── test_history_repository.py
└── shared/
    └── utils/
        └── test_url_normalizer.py
```

**命名規則**:
- パターン: `test_[テスト対象ファイル名].py`
- 例: `buzz_scorer.py` → `test_buzz_scorer.py`

**例**:
```python
# tests/unit/services/test_buzz_scorer.py
import pytest
from datetime import datetime, timezone, timedelta
from services.buzz_scorer import BuzzScorer

def test_calculate_recency_score():
    """鮮度スコア計算のテスト."""
    scorer = BuzzScorer()

    # 本日公開: 100点
    now = datetime.now(timezone.utc)
    assert scorer.calculate_recency_score(now) == 100.0

    # 3日前: 70点
    three_days_ago = now - timedelta(days=3)
    assert scorer.calculate_recency_score(three_days_ago) == 70.0
```

#### integration/

**役割**: 複数コンポーネントの統合テスト（moto使用）

**構造**:
```
tests/integration/
├── __init__.py
├── test_collection_flow.py       # 収集→正規化→重複排除
├── test_judgment_flow.py         # LLM判定→キャッシュ保存
└── test_notification_flow.py     # 最終選定→フォーマット→通知
```

**例**:
```python
# tests/integration/test_judgment_flow.py
import pytest
from moto import mock_dynamodb
import boto3
from services.llm_judge import LlmJudge
from repositories.cache_repository import CacheRepository

@mock_dynamodb
def test_llm_judgment_with_cache():
    """LLM判定結果のキャッシュ保存統合テスト."""
    # DynamoDBテーブル作成（motoモック）
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
    table = dynamodb.create_table(...)

    # テスト実行
    cache_repo = CacheRepository(dynamodb, "test-cache")
    llm_judge = LlmJudge(bedrock_client_mock, cache_repo)

    result = llm_judge.judge(article)
    assert result.interest_label == "ACT_NOW"

    # キャッシュ確認
    cached = cache_repo.get(article.url)
    assert cached.interest_label == result.interest_label
```

#### e2e/

**役割**: 全体フローのE2Eテスト（AWS SAM CLI使用）

**構造**:
```
tests/e2e/
├── __init__.py
├── test_normal_flow.py           # 正常系フロー
└── test_error_handling_flow.py   # 異常系フロー
```

### config/ (設定ファイルディレクトリ)

**配置ファイル**:
- `sources.yaml`: 収集元マスタ（Phase 1）

**Phase 2での拡張**:
- DynamoDBテーブルに移行

**例**:
```json
{
  "sources": [
    {
      "source_id": "hacker_news",
      "name": "Hacker News",
      "feed_url": "https://news.ycombinator.com/rss",
      "feed_type": "rss",
      "priority": "high",
      "timeout_seconds": 10,
      "retry_count": 2,
      "enabled": true
    }
  ]
}
```

### docs/ (ドキュメントディレクトリ)

**配置ドキュメント**:
- `product-requirements.md`: プロダクト要求定義書（PRD）
- `functional-design.md`: 機能設計書
- `architecture.md`: アーキテクチャ設計書
- `repository-structure.md`: リポジトリ構造定義書（本ドキュメント）
- `development-guidelines.md`: 開発ガイドライン
- `glossary.md`: 用語集
- `ideas/`: アイデア・下書き
  - `initial-request.md`: 初期要求仕様

### .steering/ (ステアリングファイル)

**役割**: 特定の開発作業における「今回何をするか」を定義

**構造**:
```
.steering/
└── [YYYYMMDD]-[task-name]/
    ├── requirements.md      # 今回の作業の要求内容
    ├── design.md            # 変更内容の設計
    └── tasklist.md          # タスクリスト
```

**命名規則**: `20250115-add-notification-feature` 形式

**管理方針**:
- 作業ごとに新規作成
- 履歴として保持（削除しない）
- `.gitignore` で除外（個人的な作業管理）

### .claude/ (Claude Code設定)

**役割**: Claude Code設定とカスタマイズ

**構造**:
```
.claude/
├── CLAUDE.md                # プロジェクト固有指示
└── skills/                  # カスタムスキル
    ├── prd-writing/
    ├── functional-design/
    ├── architecture-design/
    ├── repository-structure/
    ├── development-guidelines/
    └── glossary-creation/
```

## ファイル配置規則

### ソースファイル

| ファイル種別 | 配置先 | 命名規則 | 例 |
|------------|--------|---------|-----|
| Lambda ハンドラー | `src/` | `handler.py` | `handler.py` |
| Orchestrator | `src/orchestrator/` | `orchestrator.py` | `orchestrator.py` |
| サービスクラス | `src/services/` | `[service]_[entity].py` | `llm_judge.py`, `buzz_scorer.py` |
| リポジトリクラス | `src/repositories/` | `[entity]_repository.py` | `cache_repository.py` |
| モデルクラス | `src/models/` | `[entity].py` | `article.py`, `judgment.py` |
| ユーティリティ関数 | `src/shared/utils/` | `[function].py` | `url_normalizer.py` |
| 例外クラス | `src/shared/exceptions/` | `[error_type]_error.py` | `collection_error.py` |

### テストファイル

| テスト種別 | 配置先 | 命名規則 | 例 |
|-----------|--------|---------|-----|
| ユニットテスト | `tests/unit/` | `test_[対象].py` | `test_buzz_scorer.py` |
| 統合テスト | `tests/integration/` | `test_[機能]_flow.py` | `test_judgment_flow.py` |
| E2Eテスト | `tests/e2e/` | `test_[シナリオ]_flow.py` | `test_normal_flow.py` |

### 設定ファイル

| ファイル種別 | 配置先 | 命名規則 |
|------------|--------|---------|
| 依存関係定義 | プロジェクトルート | `pyproject.toml` |
| Lambda デプロイ用 | プロジェクトルート | `requirements.txt` |
| AWS SAM テンプレート | プロジェクトルート | `template.yaml` |
| 収集元マスタ | `config/` | `sources.yaml` |
| Git除外設定 | プロジェクトルート | `.gitignore` |

## 命名規則

### ディレクトリ名

- **レイヤーディレクトリ**: 複数形、snake_case
  - 例: `services/`, `repositories/`, `models/`
- **機能ディレクトリ**: 単数形、snake_case
  - 例: `orchestrator/`, `shared/`

### ファイル名

- **クラスファイル**: snake_case
  - 例: `llm_judge.py`, `cache_repository.py`
- **関数ファイル**: snake_case + 動詞
  - 例: `normalize_url.py`, `format_date.py`
- **モデルファイル**: snake_case（エンティティ名）
  - 例: `article.py`, `judgment.py`

### クラス名・関数名

- **クラス名**: PascalCase
  - 例: `LlmJudge`, `CacheRepository`, `Article`
- **関数名**: snake_case
  - 例: `normalize_url()`, `calculate_recency_score()`
- **定数名**: UPPER_SNAKE_CASE
  - 例: `MAX_ARTICLES = 15`, `DEFAULT_TIMEOUT = 10`

### テストファイル名

- パターン: `test_[テスト対象].py`
- 例: `test_llm_judge.py`, `test_cache_repository.py`

## 依存関係のルール

### レイヤー間の依存

```
handler.py
    ↓ (OK)
orchestrator/
    ↓ (OK)
services/
    ↓ (OK)
repositories/
    ↓ (OK)
models/ + shared/
```

**許可される依存**:
- `handler.py` → `orchestrator/`, `shared/`
- `orchestrator/` → `services/`, `repositories/`, `models/`, `shared/`
- `services/` → `repositories/`, `models/`, `shared/`
- `repositories/` → `models/`, `shared/`
- `models/` → なし（他のレイヤーに依存しない）
- `shared/` → 標準ライブラリ、外部ライブラリのみ

**禁止される依存**:
- `repositories/` → `services/` (❌)
- `services/` → `orchestrator/` (❌)
- `models/` → 任意のレイヤー (❌)

### モジュール間の依存

**循環依存の禁止**:
```python
# ❌ 悪い例: 循環依存
# services/task_service.py
from .user_service import UserService

# services/user_service.py
from .task_service import TaskService  # 循環依存
```

**解決策: Protocolを使った抽象化**:
```python
# models/protocols.py
from typing import Protocol

class ITaskService(Protocol):
    """タスクサービスのインターフェース."""
    def create_task(self, title: str) -> None: ...

# services/user_service.py
from models.protocols import ITaskService

class UserService:
    def __init__(self, task_service: ITaskService) -> None:
        self.task_service = task_service
```

## スケーリング戦略

### Phase 1 → Phase 2 移行（Step Functions化）

**Phase 1: 単一Lambda構成**
```
src/
├── handler.py              # 単一エントリーポイント
├── orchestrator/
│   └── orchestrator.py     # 全ステップを順次実行
├── services/               # 各サービス
└── repositories/           # 各リポジトリ
```

**Phase 2: Step Functions構成**
```
src/
├── handlers/               # 複数のLambda ハンドラー
│   ├── __init__.py
│   ├── collect_and_prepare.py   # Lambda 1
│   ├── judge_articles.py        # Lambda 2
│   └── select_and_notify.py     # Lambda 3
├── services/               # 各サービス（変更なし）
└── repositories/           # 各リポジトリ（変更なし）
```

**移行手順**:
1. `orchestrator.py` の各ステップを独立したLambdaハンドラーに分割
2. S3バケット作成（Lambda間データ受け渡し用）
3. Step Functions State Machine定義
4. EventBridge をStep Functions実行に変更

### ファイル分割の目安

**ファイル分割の推奨**:
- 1ファイル: 300行以下を推奨
- 300-500行: リファクタリングを検討
- 500行以上: 分割を強く推奨

**分割方法**:
```python
# 悪い例: 1ファイルに全機能（800行）
# services/llm_judge.py

# 良い例: 責務ごとに分割
# services/llm_judge/
# ├── __init__.py
# ├── judge.py              # 判定ロジック（200行）
# ├── prompt_builder.py     # プロンプト生成（150行）
# └── output_parser.py      # 出力パース（100行）
```

## 除外設定

### .gitignore

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# 仮想環境
.venv/
venv/
ENV/
env/

# テスト・カバレッジ
.pytest_cache/
.coverage
htmlcov/
.tox/

# 型チェック・リンター
.mypy_cache/
.ruff_cache/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# ログ
*.log

# AWS SAM
.aws-sam/
samconfig.toml

# ステアリングファイル（個人的な作業管理）
.steering/

# 環境変数
.env
.env.local

# 一時ファイル
*.tmp
*.bak
```

### .ruffignore

```
__pycache__/
.venv/
dist/
build/
.steering/
.pytest_cache/
.mypy_cache/
.ruff_cache/
```

## デプロイ成果物

### Lambda デプロイパッケージ

**生成方法（uv）:**
```bash
# 依存関係のコンパイル
uv pip compile pyproject.toml -o requirements.txt

# AWS SAM ビルド
sam build
```

**成果物構造**:
```
.aws-sam/build/NewsletterFunction/
├── src/                    # ソースコード
│   ├── handler.py
│   ├── orchestrator/
│   ├── services/
│   ├── repositories/
│   ├── models/
│   └── shared/
├── boto3/                  # 依存ライブラリ
├── feedparser/
├── httpx/
├── structlog/
├── pydantic/
└── ... (その他の依存)
```

## ドキュメント配置

### プロジェクトルート

- `README.md`: プロジェクト概要、セットアップ手順
- `LICENSE`: ライセンス

### docs/ ディレクトリ

- `product-requirements.md`: プロダクト要求定義書（PRD）
- `functional-design.md`: 機能設計書
- `architecture.md`: アーキテクチャ設計書
- `repository-structure.md`: リポジトリ構造定義書（本ドキュメント）
- `development-guidelines.md`: 開発ガイドライン
- `glossary.md`: 用語集
- `ideas/`: アイデア・下書き

## 開発ワークフロー

### 初回セットアップ

```bash
# リポジトリクローン
git clone <repository-url>
cd ai-curated-newsletter

# 依存関係のインストール（uv）
uv pip install -e ".[dev]"

# AWS SAM CLI確認
sam --version

# テスト実行
pytest

# 型チェック
mypy src/

# リンター・フォーマッター
ruff check src/
ruff format src/
```

### 日常的な開発

```bash
# 機能追加時
# 1. ブランチ作成
git checkout -b feature/add-xxx

# 2. コード実装
# src/services/xxx.py を作成

# 3. テスト実装
# tests/unit/services/test_xxx.py を作成

# 4. テスト実行
pytest tests/unit/services/test_xxx.py

# 5. 型チェック・リンター
mypy src/
ruff check src/

# 6. コミット
git add .
git commit -m "add: xxx機能を追加"

# 7. プッシュ
git push origin feature/add-xxx
```

### デプロイ

```bash
# ローカルテスト
sam local invoke NewsletterFunction --event events/test_event.json

# ビルド
sam build

# デプロイ
sam deploy --guided
```
