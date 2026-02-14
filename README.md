# AI Curated Newsletter

技術ニュース/テックブログを収集し、LLM で判定して「読む価値のある記事」を厳選してメール通知する AWS Lambda ベースのシステムです。

## 現在の実装ステータス（MVP）

- 収集、正規化、重複排除、Buzz スコアリング、LLM 判定、最終選定、メール通知まで実装済み
- `dry_run` モード対応（メール送信をスキップ）
- DynamoDB のキャッシュ/履歴保存用コードは存在するが、`src/handler.py` では現在無効化（`None` 注入）されている
- ローカル実行のみで、SAM デプロイは未実施

## 主要機能

- 複数 RSS/Atom フィードの並列収集
- URL 正規化と重複排除
- Buzz スコア + 鮮度による LLM 判定候補（最大 150 件）選定
- AWS Bedrock（Claude 3.5 Sonnet）での記事判定
- 最終選定（任意の件数、15件を想定）
- AWS SES によるメール通知

## 技術スタック

- Python 3.12
- AWS Lambda / EventBridge / Bedrock / SES / DynamoDB
- AWS SAM
- pytest / mypy / ruff

## 処理フロー

```text
EventBridge (火・金 09:00 UTC)
  -> Lambda (src.handler.lambda_handler)
  -> Collector -> Normalizer -> Deduplicator -> BuzzScorer
  -> CandidateSelector (max 150)
  -> LlmJudge (Bedrock)
  -> FinalSelector (max 15, max_per_domain 4)
  -> Formatter -> Notifier (SES)
```

## 判定ラベル

- `ACT_NOW`: 今すぐ読むべき
- `THINK`: 設計・技術判断に有益
- `FYI`: 情報として把握推奨
- `IGNORE`: 通知不要

## セットアップ

### 前提条件

- Python 3.12+
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

```bash
cp .env.example .env
```

LLM 判定候補件数の運用目安:

- `LLM_CANDIDATE_MAX=120`（推奨）
- 実装上の上限は 150（`CandidateSelector`）
- コスト試算の前提（目安）:
  - Claude 3.5 Sonnet v2 単価: input `$6/1M`、output `$30/1M`
  - 1記事あたり平均トークン: input `900`、output `140`
  - 120件実行時の推定: 約 `$1.15/回`（週2回運用で約 `$9.22/月`）

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

## テスト・品質チェック

```bash
.venv/bin/pytest tests/ -v
.venv/bin/ruff check src/
.venv/bin/ruff format src/
.venv/bin/mypy src/
```

## デプロイ（AWS SAM）

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
