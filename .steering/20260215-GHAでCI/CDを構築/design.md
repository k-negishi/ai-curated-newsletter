# 設計書

## アーキテクチャ概要

GitHub Actionsで2つのワークフローを構築し、CI（継続的インテグレーション）とCD（継続的デプロイ）を実現します。

```
GitHub Repository
├── .github/workflows/
│   ├── ci.yml          # PR作成時のCI（テスト自動実行）
│   └── cd.yml          # mainマージ時のCI+CD（テスト + デプロイ）
```

### ワークフローのトリガー

| ワークフロー | トリガー | 実行内容 |
|------------|---------|---------|
| **ci.yml** | PR作成・更新（`pull_request`） | ruff check/format, mypy, pytest |
| **cd.yml** | mainブランチへのpush（`push` on `main`） | CI（上記テスト）+ CD（SAMデプロイ）|

### AWS認証方式

OIDC（OpenID Connect）を使用し、一時的な認証トークンでAWSに認証します。

```
GitHub Actions
    ↓ OIDC認証（一時トークン取得）
AWS IAM Role
    ↓ AssumeRoleWithWebIdentity
一時的なAWS認証情報（有効期限15分〜1時間）
    ↓ SAM CLI実行
AWS Lambda/DynamoDB等へデプロイ
```

**メリット**:
- アクセスキーをGitHubシークレットに保存不要
- 一時的な認証トークン（有効期限付き）でセキュア
- IAMロールによる権限管理（最小権限の原則）

## コンポーネント設計

### 1. CIワークフロー（ci.yml）

**責務**:
- PR作成・更新時に自動的にテストを実行
- コード品質を保証し、PRマージ前に問題を検出

**実装の要点**:
- Python 3.14環境をセットアップ
- 依存関係を `pyproject.toml` からインストール（`uv`を使用）
- ruff check, ruff format --check, mypy, pytest を順次実行
- いずれかのステップが失敗した場合、ワークフロー全体を失敗させる

**ワークフロー構造**:
```yaml
name: CI

on:
  pull_request:
    branches:
      - main

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
      - name: Set up Python 3.14
      - name: Install uv
      - name: Install dependencies
      - name: Run ruff check
      - name: Run ruff format --check
      - name: Run mypy
      - name: Run pytest
```

### 2. CDワークフロー（cd.yml）

**責務**:
- mainブランチマージ時に自動的にテストとデプロイを実行
- production環境への確実なデプロイを保証

**実装の要点**:
- CI（テスト）を最初に実行し、成功した場合のみデプロイに進む
- OIDC認証を使用してAWSに認証
- AWS SAM CLIで `sam build` と `sam deploy` を実行
- デプロイパラメータは `template.yaml` と `samconfig.toml` から取得

**ワークフロー構造**:
```yaml
name: CD

on:
  push:
    branches:
      - main

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
      - name: Set up Python 3.14
      - name: Install uv
      - name: Install dependencies
      - name: Run ruff check
      - name: Run ruff format --check
      - name: Run mypy
      - name: Run pytest

  deploy:
    needs: test  # testジョブが成功した場合のみ実行
    runs-on: ubuntu-latest
    permissions:
      id-token: write  # OIDC用
      contents: read
    steps:
      - name: Checkout code
      - name: Configure AWS credentials (OIDC)
      - name: Set up Python 3.14
      - name: Install AWS SAM CLI
      - name: SAM build
      - name: SAM deploy
```

### 3. OIDC設定（AWS IAMロール）

**責務**:
- GitHub Actionsに対してAWSリソースへのアクセス権限を付与
- 一時的な認証トークンを発行し、セキュアな認証を実現

**実装の要点**:
- **IAMロール名**: `GitHubActionsDeployRole`（またはプロジェクト固有の名前）
- **信頼ポリシー**: GitHub ActionsからのAssumeRoleを許可
- **権限ポリシー**: SAMデプロイに必要な最小権限を付与

**IAMロール作成手順**（ステップバイステップ）:

#### ステップ1: GitHub OIDCプロバイダーの作成

AWS IAMコンソールで、GitHub用のOIDCプロバイダーを作成します。

1. **AWSマネジメントコンソール** → **IAM** → **IDプロバイダー** → **プロバイダーを追加**
2. **プロバイダーのタイプ**: OpenID Connect
3. **プロバイダーのURL**: `https://token.actions.githubusercontent.com`
4. **対象者（Audience）**: `sts.amazonaws.com`
5. **作成**をクリック

#### ステップ2: IAMロールの作成

1. **AWSマネジメントコンソール** → **IAM** → **ロール** → **ロールを作成**
2. **信頼されたエンティティタイプ**: ウェブアイデンティティ
3. **アイデンティティプロバイダー**: `token.actions.githubusercontent.com`
4. **Audience**: `sts.amazonaws.com`
5. **GitHub組織**: `k-negishi`（リポジトリオーナー名）
6. **GitHubリポジトリ**: `ai-curated-newsletter`
7. **GitHubブランチ**: `main`（mainブランチからのみデプロイ可能）

#### ステップ3: 信頼ポリシーの設定

以下のJSON形式の信頼ポリシーを設定します:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::{AWS_ACCOUNT_ID}:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "token.actions.githubusercontent.com:sub": "repo:k-negishi/ai-curated-newsletter:ref:refs/heads/main"
        }
      }
    }
  ]
}
```

**重要**: `{AWS_ACCOUNT_ID}` を実際のAWSアカウントIDに置き換えてください。

#### ステップ4: 権限ポリシーの設定

SAMデプロイに必要な権限を付与します。以下のマネージドポリシーをアタッチ:

- `AWSCloudFormationFullAccess`: CloudFormationスタック管理
- `IAMFullAccess`: Lambda実行ロール作成
- `AWSLambda_FullAccess`: Lambda関数管理
- `AmazonDynamoDBFullAccess`: DynamoDBテーブル管理
- `AmazonEventBridgeFullAccess`: EventBridgeルール管理

**注意**: 本番環境では、最小権限の原則に従い、より厳密なカスタムポリシーを作成することを推奨します。

#### ステップ5: ロールARNの取得

作成したIAMロールのARNを取得し、GitHub Actionsワークフローで使用します。

例: `arn:aws:iam::123456789012:role/GitHubActionsDeployRole`

#### ステップ6: GitHub Actionsワークフローでの使用

`cd.yml` のdeployジョブで、以下のようにOIDC認証を設定します:

```yaml
- name: Configure AWS credentials
  uses: aws-actions/configure-aws-credentials@v4
  with:
    role-to-assume: arn:aws:iam::123456789012:role/GitHubActionsDeployRole
    aws-region: ap-northeast-1
```

## データフロー

### CI（PR作成時）

```
PR作成/更新
    ↓
GitHub Actions: ci.ymlトリガー
    ↓
Python 3.14環境セットアップ
    ↓
依存関係インストール（uv pip install）
    ↓
ruff check実行
    ↓ 成功
ruff format --check実行
    ↓ 成功
mypy実行
    ↓ 成功
pytest実行（カバレッジ90%チェック）
    ↓ 成功
ワークフロー成功（PRマージ可能）
```

### CD（mainマージ時）

```
mainブランチへのpush
    ↓
GitHub Actions: cd.ymlトリガー
    ↓
[testジョブ]
Python 3.14環境セットアップ
    ↓
依存関係インストール（uv pip install）
    ↓
ruff check, ruff format, mypy, pytest実行
    ↓ すべて成功
[deployジョブ]
OIDC認証（一時トークン取得）
    ↓
AWS認証情報設定
    ↓
AWS SAM CLIインストール
    ↓
sam build実行（依存関係をビルド）
    ↓ 成功
sam deploy実行（CloudFormationスタック更新）
    ↓ 成功
ワークフロー成功（デプロイ完了）
```

## エラーハンドリング戦略

### CIワークフローのエラーハンドリング

- **テスト失敗時**: ワークフローを失敗させ、PRマージをブロック
- **依存関係インストール失敗時**: ワークフローを失敗させ、エラーログを出力
- **Python環境セットアップ失敗時**: ワークフローを失敗させる

### CDワークフローのエラーハンドリング

- **テスト失敗時**: deployジョブを実行せず、ワークフローを失敗
- **OIDC認証失敗時**: デプロイを中止し、エラーログを出力
- **sam build失敗時**: デプロイを中止し、ビルドエラーを出力
- **sam deploy失敗時**: デプロイを中止し、CloudFormationエラーを出力

**リトライ戦略**:
- 現時点ではリトライなし（失敗時は手動で再実行）
- 将来的にはネットワークエラー等の一時的なエラーに対してリトライを追加

## テスト戦略

### ワークフローのテスト方法

#### CIワークフロー（ci.yml）のテスト

1. **新しいブランチを作成**:
   ```bash
   git checkout -b test/ci-workflow
   ```

2. **ci.ymlを作成してpush**:
   ```bash
   git add .github/workflows/ci.yml
   git commit -m "add: CIワークフローを追加"
   git push origin test/ci-workflow
   ```

3. **PRを作成**:
   - GitHub上でPRを作成
   - GitHub Actionsが自動的にトリガーされることを確認

4. **ワークフローの実行を確認**:
   - GitHub Actionsタブでワークフローのログを確認
   - ruff check, ruff format --check, mypy, pytest がすべて成功することを確認

#### CDワークフロー（cd.yml）のテスト

1. **CIワークフローのPRをマージ**:
   - ci.ymlのPRをmainにマージ
   - **この時点ではcd.ymlがまだ存在しないため、CDワークフローは実行されない**

2. **新しいブランチを作成してcd.ymlを追加**:
   ```bash
   git checkout -b test/cd-workflow
   git add .github/workflows/cd.yml
   git commit -m "add: CDワークフローを追加"
   git push origin test/cd-workflow
   ```

3. **PRを作成してCIワークフローが成功することを確認**

4. **PRをmainにマージ**:
   - mainマージ後、GitHub Actionsが自動的にトリガーされることを確認

5. **ワークフローの実行を確認**:
   - GitHub ActionsタブでワークフローのログをGitHub Actionsタブでワークフローのログを確認
   - testジョブが成功することを確認
   - deployジョブが実行され、sam build と sam deploy が成功することを確認
   - AWSコンソールでLambda関数が更新されていることを確認

## 依存ライブラリ

新しく追加するライブラリはありません。GitHub Actionsの標準機能とAWS SAM CLIのみを使用します。

## ディレクトリ構造

```
ai-curated-newsletter/
├── .github/
│   └── workflows/
│       ├── ci.yml          # 新規作成
│       └── cd.yml          # 新規作成
├── src/
├── tests/
├── pyproject.toml
├── template.yaml           # 既存（変更なし）
└── README.md               # 更新（CI/CD使用方法を追記）
```

## 実装の順序

### フェーズ1: OIDC設定（AWS側）

1. GitHub OIDCプロバイダーをAWS IAMに追加
2. IAMロール `GitHubActionsDeployRole` を作成
3. 信頼ポリシーを設定（GitHub Actionsからの認証を許可）
4. 権限ポリシーを設定（SAMデプロイに必要な権限を付与）
5. ロールARNを取得

### フェーズ2: CIワークフロー作成

1. `.github/workflows/ci.yml` を作成
2. Python 3.14環境セットアップステップを追加
3. 依存関係インストールステップを追加（uvを使用）
4. ruff check ステップを追加
5. ruff format --check ステップを追加
6. mypy ステップを追加
7. pytest ステップを追加（カバレッジ90%チェック）

### フェーズ3: CDワークフロー作成

1. `.github/workflows/cd.yml` を作成
2. testジョブを追加（CIと同じテストを実行）
3. deployジョブを追加（testジョブ成功後に実行）
4. OIDC認証ステップを追加
5. AWS SAM CLIインストールステップを追加
6. sam build ステップを追加
7. sam deploy ステップを追加

### フェーズ4: テストと検証

1. CIワークフローのテスト（PRで確認）
2. CDワークフローのテスト（mainマージで確認）
3. デプロイ結果の確認（AWSコンソールで確認）

### フェーズ5: ドキュメント更新

1. README.mdにCI/CD使用方法を追記
2. 振り返りを記録

## セキュリティ考慮事項

### OIDC認証

- **アクセスキー不要**: GitHubシークレットにアクセスキーを保存しない
- **一時的な認証**: 認証トークンは有効期限付き（15分〜1時間）
- **最小権限**: IAMロールで必要最小限の権限のみ付与

### シークレット管理

- **GitHubシークレット**: OIDC認証ではシークレット不要
- **環境変数**: デプロイパラメータ（メールアドレス等）は `template.yaml` と `samconfig.toml` から取得

### 権限管理

- **IAMロール**: SAMデプロイに必要な権限のみ付与
- **ブランチ制限**: mainブランチからのみデプロイ可能に制限

## パフォーマンス考慮事項

### ワークフロー実行時間

- **CIワークフロー**: 約3〜5分（依存関係インストール + テスト）
- **CDワークフロー**: 約10〜15分（CI + SAMビルド + デプロイ）

### キャッシュ戦略

将来的に、以下のキャッシュを検討:

- **依存関係キャッシュ**: `uv` の依存関係をキャッシュしてインストール時間を短縮
- **SAMビルドキャッシュ**: `.aws-sam/build/` をキャッシュしてビルド時間を短縮

現時点では、実装の複雑さを避けるためキャッシュは使用しません。

## 将来の拡張性

### Phase 2以降の拡張候補

- **staging環境へのデプロイ**: developブランチマージ時にstaging環境へデプロイ
- **手動承認**: production環境へのデプロイ前に手動承認ステップを追加
- **通知機能**: Slack通知（デプロイ成功/失敗を通知）
- **ロールバック機能**: デプロイ失敗時の自動ロールバック
- **パフォーマンステスト**: デプロイ後にsmoke testを実行
- **複数リージョンデプロイ**: 複数AWSリージョンへの同時デプロイ
