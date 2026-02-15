# Claude Python Toolkit

Pythonプロジェクト向けの Claude Code ワークフロー共通リポジトリ

## 概要

このリポジトリは、複数のPythonプロジェクトで共有する Claude Code のワークフロー（コマンド、スキル、エージェント）を提供します。Git Subtree + symlink を使用してプロジェクトに統合することで、以下の利点があります：

- **一貫性**: プロジェクト間で統一されたワークフローを維持
- **効率化**: ワークフロー改善を1箇所で行い、全プロジェクトに波及
- **迅速な立ち上げ**: 新規プロジェクトでの設定時間を大幅短縮
- **明確な分離**: 共通ファイルとプロジェクト固有ファイルがsymlinkで明確に区別

## アーキテクチャ

```
プロジェクト/
├── .claude-shared/              # git subtreeで共通リポを配置
│   ├── commands/                # 共通コマンド（実ファイル）
│   ├── skills/                  # 共通スキル（実ファイル）
│   └── agents/                  # 共通エージェント（実ファイル）
├── .claude/                     # Claude Codeが認識するディレクトリ
│   ├── commands/                # symlink（共通） + 実ファイル（プロジェクト固有）
│   ├── skills/                  # symlink（共通） + 実ファイル（プロジェクト固有）
│   ├── agents/                  # symlink（共通） + 実ファイル（プロジェクト固有）
│   └── settings.json            # プロジェクト固有設定
└── Makefile                     # Subtree + symlink管理
```

**ポイント:**
- `.claude-shared/` には共通リポジトリの実ファイルが配置される（git subtree）
- `.claude/` には共通リポジトリへの symlink と、プロジェクト固有ファイルが配置される
- Makefileの `claude-link` が自動的にsymlinkを作成（既存ファイルはスキップ）
- Git は symlink をサポートしているため、通常の Git 操作でコミット可能

## ディレクトリ構造

```
claude-python-toolkit/
├── README.md                     # このファイル
├── .gitignore                    # .idea/, __pycache__/ などを除外
├── Makefile.example              # Subtree + symlink操作用Makefileテンプレート
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
curl -O https://raw.githubusercontent.com/k-negishi/claude-python-toolkit/main/Makefile.example

# Makefile にリネーム
mv Makefile.example Makefile

# k-negishi を実際のGitHubユーザー名に置換（必要に応じて）
sed -i '' 's/k-negishi/your-github-username/g' Makefile
```

#### ステップ2: Subtree を追加

```bash
# Makefileを使用（推奨）
make claude-init

# または、直接コマンドを実行
# git subtree add --prefix=.claude-shared https://github.com/k-negishi/claude-python-toolkit.git main --squash
```

`make claude-init` は以下を自動実行します：
1. `.claude-shared/` に Subtree を追加
2. `.claude/` ディレクトリ構造を作成
3. symlink を自動作成

#### ステップ3: プロジェクト固有ファイルを追加

```bash
# 設定ファイルを作成
cp .claude-shared/settings.example.json .claude/settings.json
# ... 編集

# プロジェクト固有のスキルを作成（例）
mkdir -p .claude/skills/local-python-qa
cat > .claude/skills/local-python-qa/SKILL.md <<EOF
# Python品質チェックスキル
...
EOF
```

**重要**: プロジェクト固有ファイルは `.claude/` に直接配置してください。
- Makefileの `claude-link` は、既存ファイルをスキップするため、プロジェクト固有ファイルが優先されます
- ファイル名に特別なプレフィックスは不要です（symlink と実ファイルで自動的に区別されます）

#### ステップ4: コミット

```bash
git add .claude-shared/ .claude/ Makefile .gitignore
git commit -m "Integrate claude-python-toolkit via Git Subtree + symlink"
git push origin main
```

### 2. 共通リポジトリの更新を取得

```bash
# Makefileを使用（推奨）
make claude-update

# または、直接コマンドを実行
# git subtree pull --prefix=.claude-shared https://github.com/k-negishi/claude-python-toolkit.git main --squash
# make claude-link  # symlink を再作成
```

`make claude-update` は以下を自動実行します：
1. `.claude-shared/` の Subtree を更新
2. symlink を再作成（既存ファイルはスキップ）

### 3. ローカルの変更を共通リポジトリにプッシュ

共通ファイル（`.claude-shared/` 内）に改善を加えた場合、共通リポジトリにプッシュできます。

```bash
# 共通ファイルを編集
vim .claude-shared/commands/spec-plan.md

# 変更をコミット
git add .claude-shared/
git commit -m "Improve spec-plan command"

# 共通リポジトリにプッシュ
make claude-push

# または、直接コマンドを実行
# git subtree push --prefix=.claude-shared https://github.com/k-negishi/claude-python-toolkit.git main
```

**注意**: `.claude/` 内のsymlinkは、`.claude-shared/` の実ファイルを参照しているため、`.claude-shared/` を編集してください。

### 4. symlink の管理

```bash
# symlink を再作成（既存ファイルはスキップ）
make claude-link

# symlink を削除（実ファイルは保持）
make claude-clean

# Subtree の状態確認
make claude-status
```

## プロジェクト側の構成例

Subtree + symlink 統合後のプロジェクト側の構成:

```
your-project/
├── Makefile                      # Subtree + symlink管理
├── src/
├── .claude-shared/               # git subtree（共通リポジトリの実ファイル）
│   ├── commands/
│   ├── skills/
│   └── agents/
└── .claude/                      # Claude Code認識ディレクトリ
    ├── commands/
    │   ├── add-feature.md        # ← symlink（共通）
    │   ├── spec-plan.md          # ← symlink（共通）
    │   └── my-deploy.md          # ← 実ファイル（プロジェクト固有）
    ├── skills/
    │   ├── steering/             # ← symlink（共通）
    │   ├── python-pro/           # ← symlink（共通）
    │   └── local-python-qa/      # ← 実ディレクトリ（プロジェクト固有）
    ├── agents/
    │   └── doc-reviewer.md       # ← symlink（共通）
    └── settings.json             # ← 実ファイル（プロジェクト固有）
```

**symlink の確認:**

```bash
ls -la .claude/commands/
# lrwxr-xr-x  1 user  staff   47 Feb 15 18:03 add-feature.md -> ../../.claude-shared/commands/add-feature.md
# -rw-r--r--  1 user  staff  123 Feb 15 18:03 my-deploy.md
```

## 必須ファイル一覧

プロジェクト側で最低限必要なファイル:

- `Makefile` - Subtree + symlink操作用（Makefile.exampleから作成）
- `.claude/settings.json` - プロジェクト固有の設定
- `CLAUDE.md` - プロジェクト固有のドキュメント（CLAUDE.md.templateをベースに作成）
- `.gitignore` - `.claude-shared/.gitignore` を除外する設定

**.gitignore の例:**

```gitignore
# Claude Code - 共通リポジトリの.gitignoreは除外
.claude-shared/.gitignore
```

## トラブルシューティング

### Subtree追加時にコンフリクトが発生した場合

```bash
# --allow-unrelated-histories を追加
git subtree add --prefix=.claude-shared https://github.com/k-negishi/claude-python-toolkit.git main --squash --allow-unrelated-histories
```

### symlink が壊れている場合

```bash
# symlink を再作成
make claude-clean
make claude-link
```

### 既存の `.claude/` を新しいアーキテクチャに移行する場合

詳細は[移行ガイド](docs/migration-guide.md)を参照してください。

基本的な手順：
1. 既存の `.claude/` をバックアップ
2. プロジェクト固有ファイルを退避
3. `.claude/` を削除
4. 新しいSubtreeを `.claude-shared/` に追加
5. symlink を作成
6. プロジェクト固有ファイルを復元

## Makefileコマンド一覧

| コマンド | 説明 |
|---------|------|
| `make claude-init` | 初回セットアップ（Subtree追加 + symlink作成） |
| `make claude-update` | 共通リポジトリの更新を取得 + symlink再作成 |
| `make claude-push` | ローカルの変更を共通リポジトリにプッシュ |
| `make claude-link` | symlink を作成（既存ファイルはスキップ） |
| `make claude-clean` | symlink を削除（実ファイルは保持） |
| `make claude-status` | Subtree の状態確認 |

## 謝辞（参考元ライセンス情報）

以下のリポジトリのアイデア・構成・実装方針を参考にしています。

- https://github.com/GenerativeAgents/claude-code-book-chapter8
- https://github.com/Jeffallan/claude-skills

上記リポジトリはいずれも MIT License で公開されています。

