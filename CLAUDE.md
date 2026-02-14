# プロジェクトメモリ

## 技術スタック

- 開発環境: 
- Python
 

## スペック駆動開発の基本原則

### 基本フロー

1. **ドキュメント作成**: 永続ドキュメント(`docs/`)で「何を作るか」を定義
2. **作業計画**: ステアリングファイル(`.steering/`)で「今回何をするか」を計画
3. **実装**: tasklist.mdに従って実装し、進捗を随時更新
4. **検証**: テストと動作確認
5. **更新**: 必要に応じてドキュメント更新

### 重要なルール

#### ドキュメント作成時

**1ファイルずつ作成し、必ずユーザーの承認を得てから次に進む**

承認待ちの際は、明確に伝える:
```
「[ドキュメント名]の作成が完了しました。内容を確認してください。
承認いただけたら次のドキュメントに進みます。」
```

#### 実装前の確認

新しい実装を始める前に、必ず以下を確認:

1. CLAUDE.mdを読む
2. 関連する永続ドキュメント(`docs/`)を読む
3. Grepで既存の類似実装を検索
4. 既存パターンを理解してから実装開始

#### 品質チェック（必須）

**コード変更後は必ず以下のコマンドを実行すること:**

```bash
# 1. テスト実行
.venv/bin/pytest tests/ -v

# 2. リントチェック
.venv/bin/ruff check src/

# 3. コードフォーマット
.venv/bin/ruff format src/

# 4. 型チェック
.venv/bin/mypy src/
```

**全てのチェックがパスするまで実装は完了とみなさない。**

- ruff: `All checks passed!` を確認
- mypy: `Success: no issues found` を確認
- pytest: 今回の変更に関連するテストが全てパスすることを確認

#### ローカル実行（動作確認）

**Lambda関数をローカルで実行する方法:**

```bash
# 1. .envファイルが正しく設定されていることを確認
cat .env

# 2. Lambda関数を実行
# 方法A: シェルスクリプトで実行（最も簡単）
./run_local.sh  # 対話的にモードを選択

# 方法B: Pythonスクリプトで直接実行
.venv/bin/python test_lambda_local.py              # 本番モード
.venv/bin/python test_lambda_local.py --dry-run    # dry_runモード

# 方法C: SAM CLI（Docker環境による制約あり）
# sam build && sam local invoke NewsletterFunction --event events/production.json
# 注意: macOS環境ではDockerマウントエラーが発生する場合があります
```

**実行モード:**
- `test_lambda_local.py`: 本番モード（dry_run=false、メール送信あり）
- dry_runモードで実行したい場合は、スクリプト内の`event = {"dry_run": False}`を`True`に変更

**注意事項:**
- Bedrock（LLM）とSES（メール送信）は実際のAWSサービスにアクセスします
- AWS認証情報が必要（~/.aws/credentials）
- LLM判定は実行される（コストが発生: 約14円/30記事）
- SESで送信元メールアドレスが検証済みである必要があります

**実行結果の確認:**
- 実行完了後、`final_selected_count`が0でない場合は成功
- メールが送信先アドレスに届いていることを確認
- ThrottlingExceptionが一部発生しても、成功した記事で処理は継続されます

#### ステアリングファイル管理

作業ごとに `.steering/[YYYYMMDD]-[タスク名]/` を作成:

- `requirements.md`: 今回の要求内容
- `design.md`: 実装アプローチ
- `tasklist.md`: 具体的なタスクリスト

命名規則: `20250115-add-user-profile` 形式

#### ステアリングファイルの管理

**作業計画・実装・検証時は`steering`スキルを使用してください。**

- **作業計画時**: `Skill('steering')`でモード1(ステアリングファイル作成)
- **実装時**: `Skill('steering')`でモード2(実装とtasklist.md更新管理)
- **検証時**: `Skill('steering')`でモード3(振り返り)

詳細な手順と更新管理のルールはsteeringスキル内に定義されています。

## ディレクトリ構造

### 永続的ドキュメント(`docs/`)

アプリケーション全体の「何を作るか」「どう作るか」を定義:

#### 下書き・アイデア（`docs/ideas/`）
- 壁打ち・ブレインストーミングの成果物
- 技術調査メモ
- 自由形式（構造化は最小限）
- `/setup-project`実行時に自動的に読み込まれる

#### 正式版ドキュメント
- **product-requirements.md** - プロダクト要求定義書
- **functional-design.md** - 機能設計書
- **architecture.md** - 技術仕様書
- **repository-structure.md** - リポジトリ構造定義書
- **development-guidelines.md** - 開発ガイドライン
- **glossary.md** - ユビキタス言語定義

### 作業単位のドキュメント(`.steering/`)

特定の開発作業における「今回何をするか」を定義:

- `requirements.md`: 今回の作業の要求内容
- `design.md`: 変更内容の設計
- `tasklist.md`: タスクリスト

## 開発プロセス

### 初回セットアップ

1. このテンプレートを使用
2. `/setup-project` で永続的ドキュメント作成(対話的に6つ作成)
3. `/add-feature [機能]` で機能実装

### 日常的な使い方

**基本は普通に会話で依頼してください:**

```bash
# ドキュメントの編集
> PRDに新機能を追加してください
> architecture.mdのパフォーマンス要件を見直して
> glossary.mdに新しいドメイン用語を追加

# 機能追加(定型フローはコマンド)
> /add-feature ユーザープロフィールを編集  # 日本語、動詞で終わる
> /add-feature https://github.com/owner/repo/issues/123  # issue URLも指定可能

# 段階的な機能追加(計画と実装を分離)
> /plan ログイン機能を追加  # まず計画だけを立てたい場合
> /implement .steering/20260214-ログイン機能を追加/  # 既存の計画から実装

# 詳細レビュー(詳細なレポートが必要なとき)
> /review-docs docs/product-requirements.md
```

**コマンドの使い分け:**

- **`/add-feature`**: 計画から実装まで一気に完了させたい場合 (完全自動)
- **`/plan`**: まず計画だけを立てたい場合、要件を確認したい場合 (対話的)
- **`/implement`**: 既にステアリングファイルがあり、実装だけを行いたい場合 (TDDサイクル)

**ポイント**: スペック駆動開発の詳細を意識する必要はありません。Claude Codeが適切なスキルを判断してロードします。

## ドキュメント管理の原則

### 永続的ドキュメント(`docs/`)

- 基本設計を記述
- 頻繁に更新されない
- プロジェクト全体の「北極星」

### 作業単位のドキュメント(`.steering/`)

- 特定の作業に特化
- 作業ごとに新規作成
- 履歴として保持