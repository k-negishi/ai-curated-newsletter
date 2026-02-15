# Claude Python Toolkit

Pythonプロジェクト向けの Claude Code ワークフロー共通リポジトリ

## 概要

このリポジトリは、複数のPythonプロジェクトで共有する Claude Code のワークフロー（コマンド、スキル、エージェント）を提供します。Git Subtree を使用してプロジェクトに統合することで、以下の利点があります：

- **一貫性**: プロジェクト間で統一されたワークフローを維持
- **効率化**: ワークフロー改善を1箇所で行い、全プロジェクトに波及
- **迅速な立ち上げ**: 新規プロジェクトでの設定時間を大幅短縮

## ディレクトリ構造

```
claude-python-toolkit/
├── README.md                     # このファイル
├── .gitignore                    # local-* ファイルを除外
├── Makefile.example              # Subtree操作用Makefileテンプレート
├── commands/                     # Claude Codeコマンド定義
│   ├── add-feature.md
│   ├── spec-plan.md              # ステアリングファイル作成
│   ├── review-docs.md
│   ├── commit-push-close.md
│   ├── research-plan.md
│   └── setup-project.md
├── skills/                       # Claude Codeスキル定義
│   ├── steering/                 # ステアリングファイル管理
│   ├── prd-writing/              # PRD作成
│   ├── functional-design/        # 機能設計
│   ├── architecture-design/      # アーキテクチャ設計
│   ├── repository-structure/     # リポジトリ構造定義
│   ├── glossary-creation/        # 用語集作成
│   ├── git-commit/               # Gitコミット支援
│   ├── close-issue/              # Issue クローズ
│   ├── feedback-response/        # フィードバック対応
│   └── python-pro/               # Python開発ベストプラクティス
├── agents/                       # Claude Code エージェント定義
│   ├── doc-reviewer.md           # ドキュメントレビュー
│   └── implementation-validator.md  # 実装検証
├── settings.example.json         # Claude Code設定テンプレート
└── CLAUDE.md.template            # プロジェクトCLAUDE.mdテンプレート
```

## 使用方法

### 1. 初回セットアップ

#### ステップ1: Makefile を作成

```bash
# プロジェクトルートで実行
cd your-project

# Makefile.example をダウンロード
curl -O https://raw.githubusercontent.com/YOUR_USERNAME/claude-python-toolkit/main/Makefile.example

# Makefile にコピー
cp Makefile.example Makefile

# YOUR_USERNAME を実際のGitHubユーザー名に置換
sed -i '' 's/YOUR_USERNAME/your-github-username/g' Makefile

# Makefile.example を削除
rm Makefile.example
```

#### ステップ2: 既存の `.claude` を削除（既にある場合）

```bash
# Gitから削除（ワーキングツリーには残す）
git rm -r --cached .claude

# コミット
git commit -m "Remove .claude directory before Subtree integration"
```

#### ステップ3: Subtree を追加

```bash
# Makefileを使用（推奨）
make claude-init

# または、直接コマンドを実行
# git subtree add --prefix=.claude https://github.com/YOUR_USERNAME/claude-python-toolkit.git main --squash
```

#### ステップ4: プロジェクト固有ファイルを追加

プロジェクト固有のファイルは、必ず `local-` プレフィックスを付けて `.claude/` 内に配置してください。

```bash
# 例: プロジェクト固有のスキルを作成
mkdir -p .claude/skills/local-python-qa
# ... SKILL.md を作成

# 例: プロジェクト固有の設定を作成
cp .claude/settings.example.json .claude/settings.local.json
# ... 編集
```

#### ステップ5: コミット

```bash
git add .
git commit -m "Integrate claude-python-toolkit via Git Subtree"
git push origin main
```

### 2. 共通リポジトリの更新を取得

```bash
# Makefileを使用（推奨）
make claude-update

# または、直接コマンドを実行
# git subtree pull --prefix=.claude https://github.com/YOUR_USERNAME/claude-python-toolkit.git main --squash
```

### 3. ローカルの変更を共通リポジトリにプッシュ

共通ファイルに改善を加えた場合、共通リポジトリにプッシュできます。

```bash
# Makefileを使用（推奨）
make claude-push

# または、直接コマンドを実行
# git subtree push --prefix=.claude https://github.com/YOUR_USERNAME/claude-python-toolkit.git main
```

**注意**: `local-*` ファイルは共通リポジトリの `.gitignore` で除外されているため、プッシュされません。

### 4. Subtree の状態確認

```bash
make claude-status
```

## 命名規則

### `local-` プレフィックス

プロジェクト固有のファイルには、必ず `local-` プレフィックスを付けてください。

**例:**
- `local-python-qa/` - プロジェクト固有の品質チェックスキル
- `settings.local.json` - プロジェクト固有の設定
- `local-deployment.md` - プロジェクト固有のデプロイ手順

**理由:**
- 共通リポジトリの `.gitignore` で `local-*` を除外しているため、プッシュ時に共通リポジトリに混入しない
- 共通ファイルとプロジェクト固有ファイルが明確に区別できる

## プロジェクト側の構成例

Subtree統合後のプロジェクト側の `.claude/` ディレクトリ:

```
your-project/
├── Makefile                      # Makefile.exampleから作成
├── src/
└── .claude/                      # git subtreeで管理
    ├── commands/
    │   ├── add-feature.md        # ← 共通（subtree由来）
    │   ├── spec-plan.md          # ← 共通（subtree由来）
    │   └── local-deploy.md       # ← プロジェクト固有
    ├── skills/
    │   ├── steering/             # ← 共通（subtree由来）
    │   ├── python-pro/           # ← 共通（subtree由来）
    │   └── local-python-qa/      # ← プロジェクト固有
    ├── agents/
    │   └── doc-reviewer.md       # ← 共通（subtree由来）
    ├── settings.example.json     # ← 共通（subtree由来）
    ├── settings.local.json       # ← プロジェクト固有
    └── CLAUDE.md.template        # ← 共通（subtree由来）
```

## 必須ファイル一覧

プロジェクト側で最低限必要なファイル:

- `Makefile` - Subtree操作用（Makefile.exampleから作成）
- `.claude/settings.local.json` - プロジェクト固有の設定
- `CLAUDE.md` - プロジェクト固有のドキュメント（CLAUDE.md.templateをベースに作成）

## トラブルシューティング

### Subtree追加時にコンフリクトが発生した場合

```bash
# --allow-unrelated-histories を追加
git subtree add --prefix=.claude https://github.com/YOUR_USERNAME/claude-python-toolkit.git main --squash --allow-unrelated-histories
```

### 誤って `local-*` ファイルを共通リポジトリにプッシュしてしまった場合

```bash
# 共通リポジトリ側で削除
cd ~/path/to/claude-python-toolkit
git rm -r local-*
git commit -m "Remove accidentally pushed local-* files"
git push origin main

# プロジェクト側で更新を取得
cd ~/path/to/your-project
make claude-update
```

## 謝辞（参考元ライセンス情報）

以下のリポジトリのアイデア・構成・実装方針を参考にしています。

- https://github.com/GenerativeAgents/claude-code-book-chapter8
- https://github.com/Jeffallan/claude-skills

上記リポジトリはいずれも MIT License で公開されています。  
# テスト変更
# プロジェクト側からの変更
