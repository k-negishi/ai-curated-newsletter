# AI Curated Newsletter

技術ニュース/テックブログを収集し、LLM で判定して「読む価値のある記事」を厳選してメール通知する AWS Lambda ベースのシステムです。

## Claude Code による仕様駆動開発(SDD)

このプロジェクトでは、Claude Code による AI駆動の仕様駆動開発（SDD）を採用しています。  
プロジェクトの要件定義、機能設計、アーキテクチャ設計、リポジトリ構成、開発ガイドラインなどはすべて AI と対話しながらドキュメント化され、コード実装もほぼすべてを AI によって生成しています。  

skills などの .claude ファイルは、自前の共通リポジトリ（https://github.com/k-negishi/claude-python-toolkit ）で管理されたスキルやエージェントを活用しつつ、プロジェクト固有の要件に合わせたカスタマイズも行っています。

### アーキテクチャ

```
プロジェクト/
├── .claude-shared/              # git subtreeで共通リポを配置
│   ├── commands/                # 共通コマンド
│   ├── skills/                  # 共通スキル
│   └── agents/                  # 共通エージェント
├── .claude/                     # Claude Codeが認識するディレクトリ
│   ├── commands/                # symlink（共通） + 実ファイル（プロジェクト固有）
│   ├── skills/                  # symlink（共通） + 実ファイル（プロジェクト固有）
│   ├── agents/                  # symlink（共通） + 実ファイル（プロジェクト固有）
│   └── settings.json            # プロジェクト固有設定
└── Makefile                     # Subtree + symlink管理
```

**ポイント:**
- `.claude-shared/` には共通リポジトリの実ファイルが配置される（git subtree）
- `.claude/` には共通リポジトリへの symlink と、プロジェクト固有ファイル（`settings.json`, `local-python-qa/` など）が配置される
- Git は symlink をサポートしているため、通常の Git 操作でコミット可能

## 現在の実装ステータス（MVP）

- 収集、正規化、重複排除、Buzz スコアリング、LLM 判定、最終選定、メール通知まで実装済み
- `dry_run` モード対応（メール送信をスキップ）
- DynamoDB のキャッシュ/履歴保存用コードは存在するが、`src/handler.py` では現在無効化（`None` 注入）されている
- ローカル実行のみで、SAM デプロイは未実施

## 主要機能

- 複数 RSS/Atom フィードの並列収集
- URL 正規化と重複排除
- Buzz スコア + 鮮度による LLM 判定候補（最大 100 件）選定
- AWS Bedrock（Claude 4.5 Haiku）による記事内容の判定
- 最終選定（任意の件数、15件を想定）
- AWS SES によるメール通知

## 技術スタック

- Python 3.14
- AWS Lambda / EventBridge / Bedrock / SES / DynamoDB
- AWS SAM
- pytest / mypy / ruff

## 処理フロー

```text
EventBridge (火・金 09:00 UTC)
  -> Lambda (src.handler.lambda_handler)
  -> Collector -> Normalizer -> Deduplicator -> BuzzScorer
  -> CandidateSelector (max 100)
  -> LlmJudge (Bedrock)
  -> FinalSelector (max 15, max_per_domain 0=制限なし)
  -> Formatter -> Notifier (SES)
```

## 判定ラベル

- `ACT_NOW`: 今すぐ読むべき
- `THINK`: 設計・技術判断に有益
- `FYI`: 情報として把握推奨
- `IGNORE`: 通知不要

## セットアップ

### 前提条件

- Python 3.14+
- `uv`
- AWS 認証情報（`aws configure` など）
- （SAM ローカル実行/デプロイ時のみ）AWS SAM CLI

### 依存関係インストール

```bash
uv venv .venv
source .venv/bin/activate
uv pip install -e ".[dev]"
```

### 環境変数

`.env.example` をコピーして `.env` を作成し、必要に応じて編集してください。

LLM 判定候補件数の運用目安:

- `LLM_CANDIDATE_MAX=120`（推奨）
- 実装上の上限は 100（`CandidateSelector`）
- コスト試算の前提（目安）:
  - Claude Haiku 4.5 単価: input `$1/1M`、output `$5/1M`
  - 1記事あたり平均トークン: input `900`、output `140`
  - 120件実行時の推定: 約 `$0.19/回`（週2回運用で約 `$1.55/月`）

Bedrock リトライ設定（ThrottlingException 対策）:

- `BEDROCK_MAX_PARALLEL=2`: 並列実行数（デフォルト: 5 → 推奨: 2）
- `BEDROCK_REQUEST_INTERVAL=2.5`: 並列リクエスト間隔（秒、デフォルト: 2.5）
- `BEDROCK_RETRY_BASE_DELAY=2.0`: リトライ基本遅延時間（秒、デフォルト: 2.0）
- `BEDROCK_MAX_BACKOFF=20.0`: 最大バックオフ時間（秒、デフォルト: 20.0）
- `BEDROCK_MAX_RETRIES=4`: 最大リトライ回数（デフォルト: 4）

リトライ機能の詳細:
- ThrottlingException と ServiceUnavailableException を自動リトライ
- 指数バックオフ + ジッター（最大50%）を使用して、リトライ間隔を分散
- Lambda タイムアウト（900秒 = 15分）内で完了するように調整

## ローカル実行

### 推奨: Python スクリプトで直接実行

```bash
# 本番モード（メール送信あり）
.venv/bin/python test_lambda_local.py
```
```bash
# dry_run モード（メール送信なし、LLM判定は実行）
.venv/bin/python test_lambda_local.py --dry-run
```

### 補助スクリプト（対話式）

```bash
./run_local.sh
```

### SAM ローカル実行

```bash
sam build
sam local invoke NewsletterFunction --event events/dry_run.json
sam local invoke NewsletterFunction --event events/production.json
```

### 運用コマンド

```bash
# 共通リポジトリの更新を取得
make claude-update

# symlinkだけ再構築
make claude-link

# 現状確認
make claude-status

# 共通symlinkを一時削除（実ファイルは保持）
make claude-clean

# ローカルの変更を共通リポジトリにプッシュ
make claude-push
```

### プロジェクト固有ファイルの管理

通常の Git 操作で管理できます：

```bash
# プロジェクト固有ファイルを編集
vim .claude/settings.json
vim .claude/skills/local-python-qa/SKILL.md

# 通常通りコミット
git add .claude/settings.json .claude/skills/local-python-qa/
git commit -m "Update project-specific configs"
git push
```

**注意:** symlink は透過的に扱われるため、共通ファイルとプロジェクト固有ファイルを意識する必要はありません。

## テスト・品質チェック

**注**: ruffの設定は `ruff.toml` に記載されています。

```bash
# 1. テスト実行
.venv/bin/pytest tests/ -v

# 2. Ruff違反の確認と修正
.venv/bin/ruff check src/              # エラー確認
.venv/bin/ruff check src/ --fix        # 自動修正（エラーがある場合）
.venv/bin/ruff format src/             # コードフォーマット

# 3. 型チェック
.venv/bin/mypy src/
```

### Ruff違反の修正手順

1. **エラー確認**: `ruff check src/` でエラーを確認
2. **自動修正**: `ruff check src/ --fix` で自動修正可能なエラーを修正
3. **手動修正**: 残りのエラーを優先度順に修正（セキュリティ > 複雑度 > スタイル）
4. **再確認**: `ruff check src/` で `All checks passed!` を確認
5. **フォーマット**: `ruff format src/` でコードスタイルを統一
6. **テスト再実行**: `.venv/bin/pytest tests/ -v` でテストが壊れていないか確認

## デプロイ（AWS SAM）

### `.env` を SSM に同期してデプロイ（推奨）

```bash
chmod +x scripts/sam-deploy.sh
./scripts/sam-deploy.sh
```

このスクリプトは以下を自動で実行します。

- `.env` を読み込む
- `.env` 全文を `/ai-curated-newsletter/dotenv` として SecureString 登録（上書き）
- `sam build`
- `sam deploy`

#### スクリプト設定のまとめ

- `ENV_FILE`: 読み込む環境ファイル（デフォルト: `.env`）
- `SSM_DOTENV_PARAMETER`: SSM パラメータ名（デフォルト: `/ai-curated-newsletter/dotenv`）
- `AWS_REGION`: 利用リージョン（デフォルト: `ap-northeast-1`）
- `STACK_NAME`: デプロイ対象スタック名（デフォルト: `ai-curated-newsletter`）
- `SAM_CONFIG_FILE`: SAM 設定ファイル（デフォルト: `samconfig.toml` があれば利用）
- `SAM_CONFIG_ENV`: SAM 設定の環境名（デフォルト: `default`）
- `SAM_S3_BUCKET`: デプロイアーティファクト保存先バケット名（未指定時は `--resolve-s3` を自動利用）

#### 実行フローのまとめ

1. `.env` を読み込み、環境変数として展開
2. `.env` 全文を SSM Parameter Store (`SecureString`) に1件登録
3. `sam build` を実行
4. `sam deploy` を実行（`FromEmail` / `ToEmail` をパラメータで注入、S3 設定が無ければ `--resolve-s3` を自動付与）

### 初回

```bash
sam build
sam deploy --guided
```

`template.yaml` のパラメータ:

- `FromEmail`
- `ToEmail`

### 2回目以降

```bash
sam build
sam deploy
```

### デプロイ後確認

```bash
aws lambda invoke \
  --function-name ai-curated-newsletter \
  --payload '{"dry_run": true}' \
  response.json
cat response.json
```

## 運用メモ

- EventBridge スケジュール（`template.yaml`）
  - 火曜 09:00 UTC
  - 金曜 09:00 UTC
- SES サンドボックス中は送信元/送信先ともに検証済みメールアドレスが必要
- `dry_run=true` でも Bedrock 判定は実行されるため、LLM コストは発生する

## 参考ドキュメント

- `docs/product-requirements.md`
- `docs/functional-design.md`
- `docs/architecture.md`
- `docs/repository-structure.md`
- `docs/development-guidelines.md`
- `docs/glossary.md`

## 謝辞（参考元ライセンス情報）

以下のリポジトリのアイデア・構成・実装方針を参考にしています。

- https://github.com/GenerativeAgents/claude-code-book-chapter8
- https://github.com/Jeffallan/claude-skills

上記リポジトリはいずれも MIT License で公開されています。  
