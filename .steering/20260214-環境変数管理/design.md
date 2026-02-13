# 設計書

## アーキテクチャ概要

```
┌─────────────────────────────────────────────────────────┐
│ 環境変数管理戦略                                         │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ ローカル開発環境:                                       │
│  .env → python-dotenv → os.environ → アプリケーション │
│                                                         │
│ 本番環境 (AWS Lambda):                                  │
│  .env.prod を SSM Parameter Store に登録               │
│  Lambda起動時に SSM から読み込み → アプリケーション   │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## コンポーネント設計

### 1. 設定管理モジュール（`src/shared/config.py`）

**責務**:
- 環境変数の一元管理
- ローカル .env ファイルの読み込み
- SSM Parameter Store からの設定取得
- デフォルト値の提供

**実装の要点**:
```python
from dataclasses import dataclass
from typing import Optional
import os
from dotenv import load_dotenv
import boto3

@dataclass
class AppConfig:
    """アプリケーション設定."""
    environment: str  # "local" / "production"
    log_level: str
    dry_run: bool
    dynamodb_cache_table: str
    dynamodb_history_table: str
    bedrock_model_id: str
    bedrock_max_parallel: int
    llm_candidate_max: int
    final_select_max: int
    final_select_max_per_domain: int

def load_config() -> AppConfig:
    """環境に応じた設定を読み込む.

    ローカル開発時は .env から読み込み
    Lambda環境時は SSM Parameter Store から読み込み
    """
    # .env ファイル読み込み（ローカルのみ）
    load_dotenv(".env")

    environment = os.getenv("ENVIRONMENT", "local")

    if environment == "local":
        # ローカル開発: 環境変数から直接取得
        return AppConfig(
            environment="local",
            log_level=os.getenv("LOG_LEVEL", "DEBUG"),
            dry_run=os.getenv("DRY_RUN", "false").lower() == "true",
            # ... その他の設定
        )
    else:
        # 本番環境: SSM Parameter Store から取得
        ssm = boto3.client("ssm")
        params = ssm.get_parameters_by_path(
            Path="/ai-curated-newsletter/",
            Recursive=True,
            WithDecryption=True
        )
        # ... SSM からの読み込みロジック
```

### 2. 環境変数の定義

**ローカル開発環境（`.env`）**:
```bash
ENVIRONMENT=local
LOG_LEVEL=DEBUG
DRY_RUN=false
DYNAMODB_CACHE_TABLE=ai-curated-newsletter-cache
DYNAMODB_HISTORY_TABLE=ai-curated-newsletter-history
BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0
BEDROCK_MAX_PARALLEL=5
LLM_CANDIDATE_MAX=150
FINAL_SELECT_MAX=12
FINAL_SELECT_MAX_PER_DOMAIN=4
```

**本番環境（SSM Parameter Store）**:
```
/ai-curated-newsletter/environment = "production"
/ai-curated-newsletter/log_level = "INFO"
/ai-curated-newsletter/dry_run = "false"
/ai-curated-newsletter/dynamodb_cache_table = "ai-curated-newsletter-cache"
... (同様)
```

### 3. dry_run モード実装

**定義**:
- `DRY_RUN=true` または `dry_run=true` イベントパラメータで有効化
- 以下の処理をスキップ:
  - メール送信（`Notifier.send()` が何もしない）
  - 実行履歴保存（`HistoryRepository.put()` が何もしない）
- 以下は実行:
  - RSS/Atom収集
  - LLM判定（コスト見積もり用）
  - DynamoDB キャッシュ保存（判定結果は永続化）

**実装例**:
```python
class Notifier:
    def __init__(self, dry_run: bool):
        self.dry_run = dry_run

    def send(self, articles: List[Article]) -> bool:
        """メール送信."""
        if self.dry_run:
            logger.info("dry_run=true のためメール送信をスキップ")
            return True

        # 実際のメール送信
        ...
```

## ディレクトリ構造

```
.env                                # ローカル開発用環境変数（.gitignore）
.env.example                        # テンプレート（リポジトリに含める）
.env.local                          # ローカルのAWS認証情報（.gitignore）
.steering/20250214-環境変数管理/
└── requirements.md
└── design.md
└── tasklist.md
src/
├── shared/
│   ├── config.py                  # 設定管理モジュール（新規）
│   ├── logging/
│   ├── exceptions/
│   └── utils/
├── services/
├── repositories/
└── models/
```

## 実装の順序

1. **設定管理モジュール作成** (`src/shared/config.py`)
   - AppConfig dataclass 定義
   - load_config() 関数実装
   - ローカル .env 読み込み対応
   - SSM Parameter Store 読み込み対応（Lambda環境想定）

2. **環境変数テンプレート作成**
   - `.env.example` 作成
   - `.gitignore` に `.env` および `.env.local` 追加

3. **既存コードの設定適用**
   - `src/handler.py` で load_config() を呼び出し
   - Orchestrator, Service層 で config を使用するよう更新

4. **dry_run モード実装**
   - Notifier に dry_run フラグを追加
   - HistoryRepository に dry_run フラグを追加

5. **ローカル実行確認**
   - `sam local invoke` でテスト
   - 環境変数が正しく読み込まれることを確認

6. **テスト実装**
   - `tests/unit/shared/test_config.py` - config読み込みテスト
   - `tests/integration/test_dry_run_mode.py` - dry_run モード統合テスト

## エラーハンドリング戦略

### SSM Parameter Store読み込み失敗時
- エラーログ出力
- アプリケーション起動失敗（Lambda関数がエラーで終了）
- 理由: 設定なしでは実行できないため、フェイルファーストが正しい

### 環境変数不足時
- デフォルト値を使用する（可能な範囲で）
- 必須項目不足時はエラー発生

## セキュリティ考慮事項

- メールアドレス等の機密情報は Secrets Manager で管理
- SSM Parameter Store で KMS暗号化を有効化
- ローカル開発時も .env に機密情報を含めない（テスト用ダミー値のみ）
- ログ出力時は機密情報をマスキング（既存のガイドラインに準拠）

## パフォーマンス考慮事項

- SSM Parameter Store読み込みは Lambda 起動時に1回のみ（キャッシュ）
- DynamoDB等のテーブル名は環境変数から参照（ハードコード禁止）

## テスト戦略

### ユニットテスト
- `test_load_config_local`: .env ファイルから正しく読み込まれることを確認
- `test_load_config_production`: 環境変数から正しく読み込まれることを確認
- `test_dry_run_notifier_skip`: dry_run=true でメール送信がスキップされることを確認
- `test_dry_run_cache_saved`: dry_run=true でキャッシュは保存されることを確認

### 統合テスト
- ローカル .env → アプリケーション全体で正しく使用されることを確認
- dry_run=true で Notifier, HistoryRepository がスキップされることを確認

## 依存ライブラリ

```python
{
  "new": {
    "python-dotenv": ">=1.0.0"  # .env ファイル読み込み
  },
  "existing": {
    "boto3": ">=1.34.0",  # SSM Parameter Store アクセス
    "pydantic": ">=2.6.0"  # 設定バリデーション（オプション）
  }
}
```
