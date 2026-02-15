# 開発ガイドライン (Development Guidelines)

## 基本原則

### 1. 個人開発の原則（TooMuch回避）

本プロジェクトは個人開発プロジェクトです。以下の原則を守ってください：

- **複雑さの最小化**: 必要最小限の機能のみ実装する
- **コストの最小化**: 月額$10以内を厳守
- **運用負荷の最小化**: 手動運用が必要な機能は避ける

**判断基準**:
> これは本当に通知する価値があるか？

### 2. 具体例の重要性

- コードレビュー、設計説明では必ず具体例を示す
- 「こうすべき」だけでなく「なぜそうすべきか」を説明する

### 3. Single Responsibility Principle (SRP)

- 1つのクラス・関数は1つの責務のみを持つ
- 変更理由が2つ以上ある場合は分割を検討

---

## コーディング規約

### Python 3.14 規約

#### 命名規則

| 対象 | 規則 | 例 |
|------|------|-----|
| モジュール・パッケージ | snake_case | `llm_judge.py`, `url_normalizer.py` |
| クラス | PascalCase | `LlmJudge`, `CacheRepository` |
| 関数・メソッド | snake_case | `normalize_url()`, `calculate_buzz_score()` |
| 変数 | snake_case | `article_list`, `total_score` |
| 定数 | UPPER_SNAKE_CASE | `MAX_ARTICLES = 15`, `DEFAULT_TIMEOUT = 10` |
| プライベートメンバ | _leading_underscore | `_internal_method()`, `_cache` |

**理由**:
- PEP 8 準拠（Python標準スタイルガイド）
- コード可読性の向上

#### 型ヒント（必須）

すべての関数・メソッドに型ヒントを付ける：

```python
# ✅ 良い例
from typing import List, Optional
from datetime import datetime

def normalize_url(url: str) -> str:
    """URLを正規化する."""
    ...

def calculate_recency_score(published_at: datetime) -> float:
    """鮮度スコアを計算する."""
    ...

def get_cached_judgment(url: str) -> Optional[JudgmentResult]:
    """キャッシュから判定結果を取得する."""
    ...

# ❌ 悪い例（型ヒントなし）
def normalize_url(url):
    ...
```

**理由**:
- mypy による静的型チェックが可能
- IDE の補完・エラー検出が向上
- 関数の仕様が明確になる

#### docstring規約（Googleスタイル）

すべての public 関数・クラスに docstring を記述：

```python
def calculate_buzz_score(
    source_count: int,
    published_at: datetime,
    domain_diversity: float
) -> float:
    """記事のBuzzスコアを計算する.

    Args:
        source_count: 複数ソース出現数（1以上）
        published_at: 公開日時（UTC）
        domain_diversity: ドメイン多様性（0.0-1.0）

    Returns:
        Buzzスコア（0-100）

    Raises:
        ValueError: source_countが0以下の場合

    Examples:
        >>> calculate_buzz_score(3, datetime.now(timezone.utc), 0.8)
        75.5
    """
    if source_count <= 0:
        raise ValueError("source_count must be positive")

    # スコア計算ロジック
    ...
```

**docstringの構成**:
1. 1行目: 簡潔な説明（ピリオドで終わる）
2. `Args`: 引数の説明
3. `Returns`: 戻り値の説明
4. `Raises`: 発生する例外
5. `Examples`: 使用例（オプション）

#### dataclass の使用

データクラスは `@dataclass` デコレーターを使用：

```python
from dataclasses import dataclass
from datetime import datetime
from typing import Literal

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

@dataclass
class JudgmentResult:
    """LLM判定結果.

    Attributes:
        url: 記事URL
        interest_label: 関心度ラベル
        buzz_label: 話題性ラベル
        confidence: 信頼度（0.0-1.0）
        reason: 判定理由（最大200文字）
        model_id: 使用したモデルID
        judged_at: 判定日時（UTC）
    """
    url: str
    interest_label: Literal["ACT_NOW", "THINK", "FYI", "IGNORE"]
    buzz_label: Literal["HIGH", "MID", "LOW"]
    confidence: float
    reason: str
    model_id: str
    judged_at: datetime
```

**理由**:
- ボイラープレートコードの削減
- `__init__`, `__repr__`, `__eq__` の自動生成
- 型ヒントとの統合

#### エラーハンドリング

**例外の定義**:

```python
# src/shared/exceptions/collection_error.py
class CollectionError(Exception):
    """RSS/Atom収集時のエラー."""

    def __init__(self, source_name: str, original_error: Exception) -> None:
        """エラーを初期化する.

        Args:
            source_name: 収集元名
            original_error: 元の例外
        """
        self.source_name = source_name
        self.original_error = original_error
        super().__init__(f"Failed to collect from {source_name}: {original_error}")

# src/shared/exceptions/llm_error.py
class LlmError(Exception):
    """LLM判定時のエラー."""
    pass

class LlmJsonParseError(LlmError):
    """LLM出力のJSON解析エラー."""
    pass

class LlmTimeoutError(LlmError):
    """LLMタイムアウトエラー."""
    pass
```

**例外のハンドリング**:

```python
import structlog

logger = structlog.get_logger()

def collect_from_source(source: SourceConfig) -> List[Article]:
    """収集元から記事を収集する.

    Args:
        source: 収集元設定

    Returns:
        収集した記事リスト

    Raises:
        CollectionError: 収集失敗時
    """
    try:
        response = httpx.get(source.feed_url, timeout=source.timeout_seconds)
        response.raise_for_status()
        # フィード解析
        ...
    except httpx.HTTPError as e:
        logger.error(
            "collection_failed",
            source_name=source.name,
            error=str(e)
        )
        raise CollectionError(source.name, e)
```

**原則**:
- カスタム例外を定義する（`CollectionError`, `LlmError` など）
- 例外には必要な情報を含める（`source_name`, `original_error` など）
- ログを残してから例外を再送出またはカスタム例外に変換

#### ログ出力（structlog）

**ログ初期化**:

```python
# src/shared/logging/logger.py
import structlog
import logging
import sys

def setup_logger(log_level: str = "INFO") -> None:
    """structlogを初期化する.

    Args:
        log_level: ログレベル（DEBUG, INFO, WARNING, ERROR）
    """
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper())
    )

    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
```

**ログ出力**:

```python
import structlog

logger = structlog.get_logger()

# 構造化ログ（JSON形式）
logger.info(
    "orchestrator_started",
    run_id=run_id,
    dry_run=dry_run
)

logger.info(
    "collection_completed",
    run_id=run_id,
    collected_count=len(articles),
    source_count=len(sources)
)

logger.error(
    "llm_judgment_failed",
    run_id=run_id,
    article_url=article.url,
    error=str(e)
)
```

**機密情報のマスキング**:

```python
def mask_email(email: str) -> str:
    """メールアドレスをマスクする.

    Args:
        email: メールアドレス

    Returns:
        マスクされたメールアドレス

    Examples:
        >>> mask_email("user@example.com")
        "us***@example.com"
    """
    local, domain = email.split("@")
    return f"{local[:2]}***@{domain}"

logger.info(
    "notification_sent",
    run_id=run_id,
    to_address=mask_email(to_address),  # マスキング必須
    article_count=len(articles)
)
```

---

## テストコード規約

### テスト構成

```
tests/
├── unit/                 # ユニットテスト（モック使用）
│   ├── services/
│   ├── repositories/
│   └── shared/
├── integration/          # 統合テスト（moto使用）
│   ├── test_collection_flow.py
│   ├── test_judgment_flow.py
│   └── test_notification_flow.py
└── e2e/                  # E2Eテスト（AWS SAM CLI）
    ├── test_normal_flow.py
    └── test_error_handling_flow.py
```

### ユニットテスト

**フレームワーク**: pytest

**命名規則**:
- ファイル名: `test_[対象].py`
- 関数名: `test_[テスト内容]`

**例**:

```python
# tests/unit/services/test_buzz_scorer.py
import pytest
from datetime import datetime, timezone, timedelta
from services.buzz_scorer import BuzzScorer

def test_calculate_recency_score_today():
    """本日公開の記事は100点を返す."""
    scorer = BuzzScorer()
    now = datetime.now(timezone.utc)
    assert scorer.calculate_recency_score(now) == 100.0

def test_calculate_recency_score_three_days_ago():
    """3日前の記事は70点を返す."""
    scorer = BuzzScorer()
    three_days_ago = datetime.now(timezone.utc) - timedelta(days=3)
    assert scorer.calculate_recency_score(three_days_ago) == 70.0

def test_calculate_recency_score_old_article():
    """10日以上前の記事は0点を返す."""
    scorer = BuzzScorer()
    old = datetime.now(timezone.utc) - timedelta(days=15)
    assert scorer.calculate_recency_score(old) == 0.0

@pytest.mark.parametrize("source_count,expected", [
    (1, 20),
    (3, 60),
    (5, 100),
])
def test_calculate_source_count_score(source_count, expected):
    """ソース数スコア計算のパラメータ化テスト."""
    scorer = BuzzScorer()
    assert scorer.calculate_source_count_score(source_count) == expected
```

### 統合テスト（moto使用）

**フレームワーク**: pytest + moto

**例**:

```python
# tests/integration/test_judgment_flow.py
import pytest
from moto import mock_dynamodb
import boto3
from services.llm_judge import LlmJudge
from repositories.cache_repository import CacheRepository
from models.article import Article
from datetime import datetime, timezone

@mock_dynamodb
def test_llm_judgment_with_cache():
    """LLM判定結果がキャッシュに保存されることを確認する."""
    # DynamoDBテーブル作成（motoモック）
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
    cache_repo = CacheRepository(dynamodb, "test-cache")
    llm_judge = LlmJudge(bedrock_client_mock, cache_repo)

    article = Article(
        url="https://example.com/article",
        title="Test Article",
        published_at=datetime.now(timezone.utc),
        source_name="Test Source",
        description="Test description",
        normalized_url="https://example.com/article",
        collected_at=datetime.now(timezone.utc)
    )

    result = llm_judge.judge(article)

    # 判定結果を検証
    assert result.interest_label in ["ACT_NOW", "THINK", "FYI", "IGNORE"]
    assert result.buzz_label in ["HIGH", "MID", "LOW"]

    # キャッシュ確認
    cached = cache_repo.get(article.url)
    assert cached is not None
    assert cached.interest_label == result.interest_label
```

### E2Eテスト（AWS SAM CLI）

**実行方法**:

```bash
# ローカルLambda実行
sam local invoke NewsletterFunction \
  --event events/test_event.json \
  --env-vars env.json
```

**テストイベント例**:

```json
{
  "command": "run_newsletter",
  "dry_run": true
}
```

### テストカバレッジ目標

| レイヤー | カバレッジ目標 |
|---------|--------------|
| services/ | 90%以上 |
| repositories/ | 90%以上 |
| models/ | 90%以上 |
| shared/ | 90%以上 |

**カバレッジ計測**:

```bash
# カバレッジ測定
pytest --cov=src --cov-report=html

# カバレッジレポート確認
open htmlcov/index.html
```

---

## 依存関係管理

### uv の使用

本プロジェクトでは **uv**（Rust製の超高速パッケージマネージャー）を使用します。

**インストール**:

```bash
# uvのインストール（macOS/Linux）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 依存関係のインストール
uv pip install -e .

# 開発依存関係のインストール
uv pip install -e ".[dev]"
```

**依存関係の追加**:

```bash
# pyproject.toml に直接追加
[project]
dependencies = [
    "boto3>=1.34.0",
    "feedparser>=6.0.0",
    # 新しい依存を追加
]

# requirements.txt 再生成
uv pip compile pyproject.toml -o requirements.txt

# インストール
uv pip sync requirements.txt
```

**依存関係の更新**:

```bash
# 依存関係を最新に更新
uv pip compile --upgrade pyproject.toml -o requirements.txt

# インストール
uv pip sync requirements.txt
```

**pyproject.toml の構造**:

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

---

## 品質管理ツール

### mypy（静的型チェック）

**設定ファイル（pyproject.toml）**:

```toml
[tool.mypy]
python_version = "3.14"
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_any_generics = true
```

**実行方法**:

```bash
# 全ファイルを型チェック
mypy src/

# 特定ファイルのみ
mypy src/services/llm_judge.py
```

### ruff（リンター・フォーマッター）

**設定ファイル（ruff.toml）**:

ruff設定は `ruff.toml` に独立して管理されています。段階的にルールを導入し、各ルールの目的を日本語コメントで明記しています。

主要なルール:
- **フェーズ1（基本）**: E, W, F, I, B, C4, UP
- **フェーズ2（セキュリティ・非同期）**: S, ASYNC, C90, T20, SIM
- **フェーズ3（テスト品質・命名規則）**: PT, RET, PIE, N, PLE, PLW, PLR0911-0913, PLR2004, RUF
- **フェーズ4（型チェック・docstring）**: TCH, D, LOG

詳細は `ruff.toml` を参照してください。

**実行方法**:

```bash
# リント実行
ruff check src/

# 自動修正
ruff check --fix src/

# フォーマット
ruff format src/
```

---

## Git運用ルール

### ブランチ戦略（簡略版Git Flow）

個人開発のため、Git Flowを簡略化して使用：

```
main (本番環境)
  └─ feature/* (機能開発)
  └─ fix/* (バグ修正)
```

**ブランチ命名規則**:
- 機能追加: `feature/[機能名]`（例: `feature/add-llm-judge`）
- バグ修正: `fix/[修正内容]`（例: `fix/url-normalization-bug`）

**運用ルール**:
1. `main` から `feature/*` または `fix/*` をブランチ
2. 実装 → テスト → コミット
3. `main` にマージ（fast-forward推奨）
4. ブランチ削除

### コミットメッセージ規約

**フォーマット（Conventional Commits準拠）**:

```
<type>: <subject>

<body>

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

**type（必須）**:
- `add`: 新機能追加
- `update`: 既存機能の改善
- `fix`: バグ修正
- `refactor`: リファクタリング
- `test`: テスト追加・修正
- `docs`: ドキュメント更新
- `chore`: ビルド・ツール設定等

**subject（必須）**:
- 50文字以内
- 命令形（例: "add", "fix", "update"）
- 小文字で始める

**body（オプション）**:
- 詳細な説明
- 変更理由、影響範囲

**例**:

```
add: LLM判定機能を実装

Bedrock Claude 3.5 Sonnetを使用して記事の判定を行う機能を追加。
- LlmJudgeクラスの実装
- プロンプト生成ロジック
- JSON出力のバリデーション

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

```
fix: URL正規化のクエリパラメータ除去バグを修正

utm_* パラメータが除去されない問題を修正。

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

### プルリクエスト（個人開発のため省略可）

個人開発のため、プルリクエストは必須ではありません。

必要に応じて以下のテンプレートを使用：

```markdown
## 概要
[変更内容の簡潔な説明]

## 変更内容
- [変更1]
- [変更2]

## テスト
- [ ] ユニットテスト実行
- [ ] 統合テスト実行
- [ ] 型チェック（mypy）実行
- [ ] リンター（ruff）実行

## チェックリスト
- [ ] docstringを記述した
- [ ] 型ヒントを付けた
- [ ] テストを追加した
```

---

## 開発環境セットアップ

### 初回セットアップ

```bash
# 1. リポジトリクローン
git clone <repository-url>
cd ai-curated-newsletter

# 2. uv のインストール
curl -LsSf https://astral.sh/uv/install.sh | sh

# 3. 依存関係のインストール
uv pip install -e ".[dev]"

# 4. AWS SAM CLI のインストール（macOS）
brew install aws-sam-cli

# 5. AWS認証設定
aws configure

# 6. 動作確認
pytest
mypy src/
ruff check src/
```

### 日常的な開発フロー

```bash
# 1. ブランチ作成
git checkout -b feature/add-xxx

# 2. コード実装
# src/services/xxx.py を作成

# 3. テスト実装
# tests/unit/services/test_xxx.py を作成

# 4. テスト実行
pytest tests/unit/services/test_xxx.py -v

# 5. 型チェック
mypy src/

# 6. リンター・フォーマッター
ruff check src/
ruff format src/

# 7. コミット
git add .
git commit -m "add: xxx機能を追加"

# 8. mainにマージ
git checkout main
git merge feature/add-xxx --ff-only
git branch -d feature/add-xxx

# 9. プッシュ
git push origin main
```

---

## デプロイフロー

### ローカルテスト

```bash
# テストイベント作成
cat <<EOF > events/test_event.json
{
  "command": "run_newsletter",
  "dry_run": true
}
EOF

# ローカルLambda実行
sam local invoke NewsletterFunction \
  --event events/test_event.json \
  --env-vars env.json
```

### デプロイ

```bash
# 1. 依存関係のコンパイル
uv pip compile pyproject.toml -o requirements.txt

# 2. テスト実行
pytest
mypy src/
ruff check src/

# 3. ビルド
sam build

# 4. デプロイ（初回）
sam deploy --guided

# 5. デプロイ（2回目以降）
sam deploy
```

---

## コードレビュー（個人開発のため参考）

個人開発のため、コードレビューは必須ではありませんが、以下の観点でセルフレビューを推奨：

### レビュー観点

1. **機能性**
   - 要件を満たしているか
   - エッジケースを考慮しているか

2. **コード品質**
   - 型ヒントは付いているか
   - docstringは記述されているか
   - SRPを守っているか

3. **テスト**
   - テストカバレッジは90%以上か
   - エッジケースをテストしているか

4. **パフォーマンス**
   - 不要なループはないか
   - DynamoDB BatchGetItemを使用しているか

5. **セキュリティ**
   - 機密情報をログに出力していないか
   - 入力バリデーションは実装されているか

---

## トラブルシューティング

### よくある問題

#### 1. uv で依存関係がインストールできない

```bash
# キャッシュクリア
uv cache clean

# 再インストール
uv pip install -e ".[dev]"
```

#### 2. mypy でエラーが出る

```python
# boto3-stubs をインストール
uv pip install boto3-stubs[dynamodb,bedrock-runtime,ses,secretsmanager]
```

#### 3. moto でDynamoDBテーブルが作成できない

```python
# リージョンを明示的に指定
dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
```

---

## まとめ

本ガイドラインは以下を定義しました：

1. **基本原則**: TooMuch回避、具体例の重要性、SRP
2. **コーディング規約**: 命名規則、型ヒント、docstring、エラーハンドリング
3. **テスト規約**: ユニット・統合・E2Eテスト、カバレッジ目標
4. **依存関係管理**: uv の使用方法
5. **品質管理**: mypy, ruff の設定
6. **Git運用**: 簡略版Git Flow、コミットメッセージ規約
7. **開発環境**: セットアップ手順、開発フロー

このガイドラインに従って開発することで、高品質で保守しやすいコードベースを維持できます。
