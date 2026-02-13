# 設計書

## アーキテクチャ概要

既存の実装はすでに完成しているため、新規の設計は不要。本タスクではローカル実行環境の整備に焦点を当てる。

```
ローカル開発環境
  ↓
SAM CLI (sam local invoke)
  ↓
Lambda Function (ローカル実行)
  ↓
- Collector → RSS/Atomフィード収集（実際にHTTPリクエスト）
- Normalizer → 正規化
- Deduplicator → 重複排除（AWS DynamoDB接続）
- BuzzScorer → Buzzスコア計算
- CandidateSelector → 候補選定
- LlmJudge → LLM判定（dry_runモードではスキップ or モック）
- FinalSelector → 最終選定
- Formatter → メール本文生成
- Notifier → メール送信（dry_runモードではスキップ）
```

## コンポーネント設計

### 1. イベントファイル（events/）

**責務**:
- Lambda関数に渡すイベントデータを定義
- dry_runモードと本番モードの切り替え

**実装の要点**:
- `events/dry_run.json`: `{"dry_run": true}` を設定
- `events/production.json`: `{"dry_run": false}` を設定
- README.mdに記載されている形式に従う

### 2. 依存関係管理

**責務**:
- Python依存関係が正しくインストールされていることを確認
- requirements.txtが最新の状態であることを確認

**実装の要点**:
- `uv pip install -e ".[dev]"` でインストール
- `requirements.txt` はすでに存在するため、内容確認のみ
- 不足している依存関係があれば追加

## データフロー

### ローカル実行（dry_runモード）
```
1. ユーザーが `sam local invoke` を実行
2. SAM CLIがLambda環境をローカルで起動
3. events/dry_run.json のイベントを読み込む
4. handler.lambda_handler() が実行される
5. Orchestrator.execute(run_id, executed_at, dry_run=True) が実行される
6. 各サービスが順次実行される（dry_runの場合、LLM判定やメール送信はスキップ）
7. 実行結果がJSON形式で返却される
8. ログがコンソールに出力される
```

## エラーハンドリング戦略

### 想定されるエラー

1. **依存関係のインストールエラー**
   - 対処: pyproject.tomlの依存関係を確認し、必要に応じて修正

2. **SAM CLIのビルドエラー**
   - 対処: template.yamlの構文エラーを確認
   - 対処: requirements.txtが正しく生成されているか確認

3. **Lambda実行時のインポートエラー**
   - 対処: src/配下のモジュールパスを確認
   - 対処: __init__.pyが適切に配置されているか確認

4. **AWS接続エラー（DynamoDB, Bedrock, SES）**
   - 対処: AWS認証情報が設定されているか確認（`aws configure`）
   - 対処: dry_runモードでは一部のAWS接続をスキップできるか確認

5. **RSS/Atomフィード取得エラー**
   - 対処: ネットワーク接続を確認
   - 対処: タイムアウト設定を確認

### エラーハンドリングパターン

- すべてのエラーは structlog でログ出力
- Lambda関数は500エラーを返すが、処理は継続可能な設計
- 各サービスで例外をキャッチし、適切なエラーメッセージを返す

## テスト戦略

### ローカル実行テスト
- `sam local invoke NewsletterFunction --event events/dry_run.json` を実行
- ログ出力を確認し、各ステップが正常に実行されているか確認
- エラーが発生した場合は原因を特定し、修正

### dry_runモードでの動作確認
- RSS/Atomフィードから記事を収集できるか
- 正規化、重複排除、Buzzスコア計算が正常に動作するか
- LLM判定がスキップされるか（またはモックで動作するか）
- 最終選定とフォーマットが正常に動作するか
- メール送信がスキップされるか

## 依存ライブラリ

新しいライブラリの追加は不要。既存の pyproject.toml に記載されている依存関係を使用。

```toml
[project]
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
    "pytest-cov>=4.1.0",
    "mypy>=1.8.0",
    "ruff>=0.2.0",
    "moto>=5.0.0",
    "boto3-stubs>=1.34.0",
]
```

## ディレクトリ構造

```
ai-curated-newsletter/
├── events/  （新規作成）
│   ├── dry_run.json  （新規作成）
│   └── production.json  （新規作成）
├── config/
│   └── sources.json  （既存）
├── src/  （既存）
├── tests/  （既存）
├── template.yaml  （既存）
├── pyproject.toml  （既存）
├── requirements.txt  （既存、確認のみ）
└── README.md  （既存、必要に応じて更新）
```

## 実装の順序

1. **events/ディレクトリとイベントファイルの作成**
   - `events/dry_run.json` 作成
   - `events/production.json` 作成

2. **依存関係のインストール確認**
   - `uv pip install -e ".[dev]"` 実行
   - エラーがないことを確認

3. **requirements.txtの確認**
   - 内容を確認し、必要に応じて再生成

4. **SAM CLIでのビルド**
   - `sam build` 実行
   - エラーがないことを確認

5. **ローカル実行テスト**
   - `sam local invoke NewsletterFunction --event events/dry_run.json` 実行
   - ログを確認し、正常に動作することを確認
   - エラーがあれば修正

6. **README.mdの確認と更新（必要に応じて）**
   - ローカル実行手順が正しいか確認
   - 不足情報があれば追記

## セキュリティ考慮事項

- AWS認証情報は環境変数または ~/.aws/credentials に設定
- メールアドレスなどの機密情報はログに出力しない（既にマスキング実装済み）
- dry_runモードでは実際のメール送信を行わない

## パフォーマンス考慮事項

- ローカル実行では処理時間の制約は緩い
- RSS/Atomフィードの取得に時間がかかる可能性があるため、タイムアウト設定を確認

## 将来の拡張性

- DynamoDB Localの導入（AWS接続なしでローカル完結）
- Localstackの導入（SES, Bedrockのモック）
- CI/CDパイプラインでのローカル実行テスト
