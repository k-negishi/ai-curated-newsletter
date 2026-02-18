# タスクリスト

## 🚨 タスク完全完了の原則

**このファイルの全タスクが完了するまで作業を継続すること**

### 必須ルール
- **全てのタスクを`[x]`にすること**
- 「時間の都合により別タスクとして実施予定」は禁止
- 「実装が複雑すぎるため後回し」は禁止
- 未完了タスク（`[ ]`）を残したまま作業を終了しない

### 実装可能なタスクのみを計画
- 計画段階で「実装可能なタスク」のみをリストアップ
- 「将来やるかもしれないタスク」は含めない
- 「検討中のタスク」は含めない

### タスクスキップが許可される唯一のケース
以下の技術的理由に該当する場合のみスキップ可能:
- 実装方針の変更により、機能自体が不要になった
- アーキテクチャ変更により、別の実装方法に置き換わった
- 依存関係の変更により、タスクが実行不可能になった

スキップ時は必ず理由を明記:
```markdown
- [x] ~~タスク名~~（実装方針変更により不要: 具体的な技術的理由）
```

### タスクが大きすぎる場合
- タスクを小さなサブタスクに分割
- 分割したサブタスクをこのファイルに追加
- サブタスクを1つずつ完了させる

---

## フェーズ1: OIDC設定（AWS側）

**実施済み（2026-02-19）**: AWS CLIで実施完了。

### 1-1. GitHub OIDCプロバイダーの作成

- [x] OIDCプロバイダー確認（2023年11月に作成済みのものを再利用: `token.actions.githubusercontent.com` / `sts.amazonaws.com`）

### 1-2. IAMロールの作成

- [x] `aws iam create-role` でロール `GitHubActionsDeployRole` を作成（ARN: `arn:aws:iam::${{ secrets.AWS_ACCOUNT_ID }}:role/GitHubActionsDeployRole`）

### 1-3. 信頼ポリシーの設定

- [x] 信頼ポリシーをロール作成時に同時設定（mainブランチ限定: `repo:k-negishi/ai-curated-newsletter:ref:refs/heads/main`）

### 1-4. 権限ポリシーの設定

- [x] `AWSCloudFormationFullAccess` をアタッチ
- [x] `IAMFullAccess` をアタッチ（個人開発のため許容）
- [x] `AWSLambda_FullAccess` をアタッチ
- [x] `AmazonDynamoDBFullAccess` をアタッチ
- [x] `AmazonEventBridgeFullAccess` をアタッチ

### 1-5. ロールARNの取得

- [x] ARN確認済み: `arn:aws:iam::${{ secrets.AWS_ACCOUNT_ID }}:role/GitHubActionsDeployRole`

---

## フェーズ2: CIワークフロー作成

### 2-1. ディレクトリとファイルの作成

- [x] `.github/workflows/` ディレクトリを作成（存在しない場合）
- [x] `.github/workflows/ci.yml` ファイルを作成

### 2-2. ci.yml の基本構造を作成

- [x] ワークフロー名: `CI` を設定
- [x] トリガー: `pull_request` on `main` を設定
- [x] ジョブ名: `test` を作成
- [x] ランナー: `ubuntu-latest` を指定

### 2-3. コードチェックアウトステップを追加

- [x] `actions/checkout@v4` を使用してコードをチェックアウト

### 2-4. Python 3.14環境セットアップステップを追加

- [x] `actions/setup-python@v5` を使用
- [x] `python-version: '3.14'` を指定

### 2-5. uv インストールステップを追加

- [x] `astral-sh/setup-uv@v5` を使用してuvをインストール

### 2-6. 依存関係インストールステップを追加

- [x] `uv pip install -e ".[dev]"` を実行

### 2-7. ruff check ステップを追加

- [x] `uv run ruff check src/` を実行
- [x] 失敗時にワークフローを停止

### 2-8. ruff format --check ステップを追加

- [x] `uv run ruff format --check src/` を実行
- [x] 失敗時にワークフローを停止

### 2-9. mypy ステップを追加

- [x] `uv run mypy src/` を実行
- [x] 失敗時にワークフローを停止

### 2-10. pytest ステップを追加

- [x] `uv run pytest tests/ -v` を実行
- [x] カバレッジ90%チェック（`--cov-fail-under=90`）
- [x] 失敗時にワークフローを停止

---

## フェーズ3: CIワークフローのテスト

### 3-1. 新しいブランチを作成

- [x] `git checkout -b ci/add-github-actions-workflows` でブランチ作成（ci.yml + cd.yml を同時にPR）

### 3-2. ci.yml と cd.yml をコミット

- [x] `git add .github/workflows/ci.yml .github/workflows/cd.yml`
- [x] `git commit -m "ci: GitHub Actions CI/CDワークフローを追加"`
- [x] `git push origin ci/add-github-actions-workflows`

### 3-3. PRを作成

- [x] GitHub上でPRを作成

### 3-4. ワークフローの実行を確認

- [ ] GitHub Actionsタブでワークフローが自動的にトリガーされることを確認
- [ ] ruff check が成功することを確認
- [ ] ruff format --check が成功することを確認
- [ ] mypy が成功することを確認
- [ ] pytest が成功することを確認（カバレッジ90%）

### 3-5. ワークフロー成功後にPRをマージ

- [ ] すべてのテストが通ったことを確認
- [ ] PRをmainブランチにマージ
- [ ] ブランチを削除

---

## フェーズ4: CDワークフロー作成

**実施済み（2026-02-19）**: `.github/workflows/cd.yml` を作成済み。

### 4-1. 新しいブランチを作成

- [x] ~~`git checkout -b test/cd-workflow` でブランチ作成~~（実装方針変更により不要: フェーズ3と合わせてPR管理するため）

### 4-2. cd.yml ファイルを作成

- [x] `.github/workflows/cd.yml` ファイルを作成

### 4-3. cd.yml の基本構造を作成

- [x] ワークフロー名: `CD` を設定
- [x] トリガー: `push` on `main` を設定

### 4-4. testジョブを作成

- [x] ジョブ名: `test` を作成
- [x] ランナー: `ubuntu-latest` を指定
- [x] CIワークフローと同じテストステップを追加（コードチェックアウト / Python 3.14 / uv / 依存関係 / ruff check / ruff format --check / mypy / pytest）

### 4-5. deployジョブを作成

- [x] ジョブ名: `deploy` を作成（`needs: test`）
- [x] `permissions`: `id-token: write` / `contents: read` を設定

### 4-6. deployジョブのコードチェックアウトステップを追加

- [x] `actions/checkout@v4` を使用

### 4-7. OIDC認証ステップを追加

- [x] `aws-actions/configure-aws-credentials@v4` を使用（`role-to-assume: arn:aws:iam::${{ secrets.AWS_ACCOUNT_ID }}:role/GitHubActionsDeployRole`）

### 4-8. Python 3.14環境セットアップステップを追加

- [x] `actions/setup-python@v5` / `python-version: '3.14'`

### 4-9. AWS SAM CLIインストールステップを追加

- [x] `aws-actions/setup-sam@v2` を使用

### 4-10. SAM buildステップを追加

- [x] `sam build` を実行

### 4-11. SAM deployステップを追加

- [x] `sam deploy --no-confirm-changeset --no-fail-on-empty-changeset` を実行

---

## フェーズ5: CDワークフローのテスト

### 5-1. cd.yml をコミット

- [ ] `git add .github/workflows/cd.yml`
- [ ] `git commit -m "add: CDワークフローを追加"`
- [ ] `git push origin test/cd-workflow`

### 5-2. PRを作成

- [ ] GitHub上でPRを作成
- [ ] PRのタイトル: `add: CDワークフローを追加`

### 5-3. CIワークフローの実行を確認

- [ ] GitHub Actionsタブでci.ymlが自動的にトリガーされることを確認
- [ ] すべてのテストが通ることを確認

### 5-4. PRをmainにマージ

- [ ] PRをmainブランチにマージ
- [ ] ブランチを削除

### 5-5. CDワークフローの実行を確認

- [ ] mainマージ後、GitHub Actionsタブでcd.ymlが自動的にトリガーされることを確認
- [ ] testジョブが成功することを確認
- [ ] deployジョブが実行されることを確認（testジョブ成功後）
- [ ] OIDC認証が成功することを確認
- [ ] sam build が成功することを確認
- [ ] sam deploy が成功することを確認

### 5-6. デプロイ結果の確認

- [ ] AWSマネジメントコンソールにログイン
- [ ] CloudFormationスタックが更新されていることを確認
- [ ] Lambda関数が最新のコードで更新されていることを確認
- [ ] DynamoDBテーブルに変更がないことを確認（今回は変更なし）

---

## フェーズ6: ドキュメント更新

### 6-1. README.mdにCI/CD使用方法を追記

- [ ] README.mdを開く
- [ ] 「CI/CD」セクションを追加
- [ ] CIワークフローの説明を追加（PR作成時に自動テスト）
- [ ] CDワークフローの説明を追加（mainマージ時に自動デプロイ）
- [ ] OIDC設定手順へのリンクを追加（design.mdを参照）

### 6-2. README.mdの変更をコミット

- [ ] 新しいブランチを作成: `git checkout -b docs/update-ci-cd`
- [ ] `git add README.md`
- [ ] `git commit -m "docs: CI/CD使用方法を追記"`
- [ ] `git push origin docs/update-ci-cd`
- [ ] PRを作成してマージ

---

## フェーズ7: 品質チェックと最終確認

### 7-1. すべてのワークフローが正常に動作することを確認

- [ ] GitHub Actionsタブで最近の実行履歴を確認
- [ ] ci.yml が過去のPRで正常に動作していることを確認
- [ ] cd.yml が過去のmainマージで正常に動作していることを確認

### 7-2. エラーハンドリングのテスト

- [ ] 意図的にテストを失敗させるPRを作成
  - [ ] ruff checkエラーを発生させる（例: 未使用のimport）
  - [ ] CIワークフローが失敗することを確認
  - [ ] PRマージがブロックされることを確認
- [ ] PRをクローズ（マージしない）

### 7-3. CI/CDドキュメントの確認

- [ ] README.mdのCI/CDセクションが正確であることを確認
- [ ] design.mdのOIDC設定手順が正確であることを確認

---

## 実装後の振り返り

### 実装完了日
{YYYY-MM-DD}

### 計画と実績の差分

**計画と異なった点**:
- （実装後に記入）

**新たに必要になったタスク**:
- （実装中に追加したタスクがあれば記入）

**技術的理由でスキップしたタスク**（該当する場合のみ）:
- （該当なし）

### 学んだこと

**技術的な学び**:
- GitHub ActionsのOIDC認証の仕組み
- AWS SAM CLIのCI/CD統合
- GitHub Actionsワークフローの設計パターン

**プロセス上の改善点**:
- ステアリングファイルによる計画の有効性
- 段階的な実装とテスト（CI → CD）の重要性

### 次回への改善提案

**計画フェーズでの改善点**:
- OIDC設定手順を事前にドキュメント化することで、実装がスムーズになった

**実装フェーズでの改善点**:
- GitHub Actionsのテストを段階的に行うことで、問題の早期発見ができた

**ワークフロー全体での改善点**:
- 将来的には、依存関係キャッシュやSAMビルドキャッシュを追加してパフォーマンスを改善
