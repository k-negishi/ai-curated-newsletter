# 設計書

## アーキテクチャ概要（パターンB）

Git Subtreeを使用して、`.claude`ディレクトリを共通リポジトリ（`claude-python-toolkit`）として分離し、複数のPythonプロジェクト間で共有する。

**パターンB: `.claude/`がSubtree、プロジェクト固有ファイルも`.claude/`内に混在**

### 共通リポジトリ (claude-python-toolkit)

```
claude-python-toolkit/
├── commands/          # 6個のコマンド
├── skills/            # 10スキル（共通のみ）
├── agents/            # 2エージェント
├── settings.example.json
├── CLAUDE.md.template
├── Makefile.example   # Subtree操作のテンプレート
├── .gitignore         # local-*を除外（重要）
└── README.md
```

### プロジェクト側の構造

```
プロジェクトルート/
├── .claude/                          ← Subtreeで共通リポジトリを配置
│   ├── commands/                     ← 共通ファイル（Subtreeで管理）
│   │   ├── add-feature.md
│   │   ├── spec-plan.md
│   │   ├── review-docs.md
│   │   ├── commit-push-close.md
│   │   ├── research-plan.md
│   │   └── setup-project.md
│   ├── skills/                       ← 共通+個別が混在
│   │   ├── steering/                 ← 共通ファイル
│   │   ├── prd-writing/              ← 共通ファイル
│   │   ├── functional-design/        ← 共通ファイル
│   │   ├── architecture-design/      ← 共通ファイル
│   │   ├── repository-structure/     ← 共通ファイル
│   │   ├── glossary-creation/        ← 共通ファイル
│   │   ├── git-commit/               ← 共通ファイル
│   │   ├── close-issue/              ← 共通ファイル
│   │   ├── feedback-response/        ← 共通ファイル
│   │   ├── python-pro/               ← 共通ファイル
│   │   └── local-python-qa/          ← プロジェクト固有（混在OK）
│   ├── agents/                       ← 共通ファイル
│   │   ├── doc-reviewer.md
│   │   └── implementation-validator.md
│   ├── settings.example.json         ← 共通ファイル
│   ├── settings.local.json           ← プロジェクト固有（混在OK）
│   ├── CLAUDE.md.template            ← 共通ファイル
│   └── Makefile.example              ← 共通ファイル
├── CLAUDE.md                         ← プロジェクト固有（ルート）
└── Makefile                          ← プロジェクト固有（ルート）
```

### パターンBのメリット

- **シンプル**: `.claude/`がそのままSubtree
- **柔軟**: 共通ファイルと個別ファイルを同じディレクトリ内で管理できる
- **Claude Code互換**: `CLAUDE.md`と`Makefile`がルートにあり、Claude Codeが認識しやすい

### パターンBの運用ルール

**重要なポイント**:
1. **.claude/内に共通ファイルと個別ファイルが混在する** - これは正常な動作
2. **プロジェクト固有ファイルには必ず`local-`プレフィックスを付ける**
3. **共通リポジトリの`.gitignore`で`local-*`を除外** - Subtree pushで個別ファイルが送られても無視される
4. **Subtree pull時、個別ファイルは上書きされない** - 共通リポジトリに存在しないため安全

## ファイル分類戦略

### 共通化するファイル（約25ファイル）

#### Commands（6個）
- `add-feature.md` → 変更なし
- `plan.md` → **`spec-plan.md`にリネーム**
- `review-docs.md` → 変更なし
- `commit-push-close.md` → 変更なし
- `research-plan.md` → 変更なし
- `setup-project.md` → 変更なし

#### Skills（10スキル、計23ファイル）
- `steering/` → 変更なし
- `prd-writing/` → 変更なし
- `functional-design/` → 変更なし
- `architecture-design/` → 変更なし
- `repository-structure/` → 変更なし
- `glossary-creation/` → 変更なし
- `git-commit/` → 変更なし
- `close-issue/` → 変更なし
- `feedback-response/` → 変更なし
- **`python-pro/` → 共通化（全Pythonプロジェクトで共有）**

#### Agents（2個）
- `doc-reviewer.md` → 変更なし
- `implementation-validator.md` → **一部を`local-implementation-validator.md`に分離**

#### 設定
- `settings.example.json` → テンプレートとして作成
- `CLAUDE.md.template` → スペック駆動開発の基本原則を抽出
- `Makefile.example` → Subtree操作コマンドのテンプレート

### プロジェクト固有ファイル（local-プレフィックス）

#### Skills
- **`local-python-qa/`**: Python品質チェックスキル（新規作成）
  - ステップ0: 実装前の品質チェック（mypy, ruff）
  - ステップ4: 自動テストと品質チェック（pytest, ruff, mypy）
  - `/implement`から`Skill('local-python-qa')`で読み込まれる

#### 設定
- `settings.local.json`: プロジェクト固有の設定
- (プロジェクトルート) `CLAUDE.md`: プロジェクト固有部分のみ（Python/AWS/Lambda実行方法）

### 内容分割が必要なファイル

#### 1. implement.md

**共通部分（共通リポジトリ）**:
- TDD基本フロー（RED → GREEN → REFACTOR）
- 実装手順の一般的な説明
- タスクリスト管理の基本

**個別部分（プロジェクト側: `local-python-qa`スキル）**:
- Python品質チェック（pytest, ruff, mypy）
- Python固有の実装パターン
- `/implement`から`Skill('local-python-qa')`で読み込む

#### 2. CLAUDE.md

**共通部分（`CLAUDE.md.template`）**:
- スペック駆動開発の基本原則
- ドキュメント管理の原則
- ステアリングファイル管理

**個別部分（プロジェクトの`CLAUDE.md`）**:
- 技術スタック（Python）
- 品質チェック（pytest, ruff, mypy）
- ローカル実行（Lambda関数）

#### 3. implementation-validator.md

**共通部分（共通リポジトリ）**:
- コーディング規約検証
- エラーハンドリング検証
- セキュリティ検証

**個別部分（`local-implementation-validator.md`）**:
- Python特化の検証（型ヒント、dataclass等）
- Python固有のパターン検証

## Subtree操作フロー

### Subtree追加（初回のみ）

```bash
git subtree add --prefix=.claude https://github.com/YOUR_USERNAME/claude-python-toolkit.git main --squash
```

### Subtree更新（共通リポジトリから取得）

```bash
git subtree pull --prefix=.claude https://github.com/YOUR_USERNAME/claude-python-toolkit.git main --squash
```

### Subtreeプッシュ（ローカル変更を共通リポジトリへ）

```bash
git subtree push --prefix=.claude https://github.com/YOUR_USERNAME/claude-python-toolkit.git main
```

### Subtree状態確認

```bash
git log --grep="git-subtree-dir: .claude" --oneline
```

## Makefile設計

### 共通リポジトリ（Makefile.example）

共通リポジトリに`Makefile.example`として以下を配置:

```makefile
.PHONY: claude-init claude-update claude-push claude-status

CLAUDE_REPO_URL := https://github.com/YOUR_USERNAME/claude-python-toolkit.git
CLAUDE_PREFIX := .claude

claude-init:
	@echo "Adding claude-python-toolkit as a subtree..."
	git subtree add --prefix=$(CLAUDE_PREFIX) $(CLAUDE_REPO_URL) main --squash

claude-update:
	@echo "Updating claude-python-toolkit from remote..."
	git subtree pull --prefix=$(CLAUDE_PREFIX) $(CLAUDE_REPO_URL) main --squash

claude-push:
	@echo "Pushing changes to claude-python-toolkit..."
	git subtree push --prefix=$(CLAUDE_PREFIX) $(CLAUDE_REPO_URL) main

claude-status:
	@echo "Checking subtree status..."
	git log --grep="git-subtree-dir: $(CLAUDE_PREFIX)" --oneline | head -5
```

### プロジェクト側（Makefile）

プロジェクト側では、`Makefile.example`をコピーして`YOUR_USERNAME`を実際のGitHubユーザー名に置換:

```bash
cp .claude/Makefile.example Makefile
sed -i '' 's/YOUR_USERNAME/actual-username/g' Makefile
```

## 命名規則

### 共通リポジトリ

**禁止**: `local-`プレフィックスのファイル

**理由**: プロジェクト固有ファイルと区別するため

### プロジェクト側

**必須**: プロジェクト固有ファイルには`local-`プレフィックスを付ける

**例**:
- `local-python-qa/`
- `local-implementation-validator.md`
- `settings.local.json`

## .gitignore設計

### プロジェクト側（ai-curated-newsletter）

プロジェクト側では、`.gitignore`に`local-*`を**追加しない**。

**理由**:
- プロジェクト固有の設定やスキル（`local-python-qa/`、`settings.local.json`等）は、プロジェクトのGit履歴として保存すべき
- `local-`ファイルも通常通りcommit可能

### 共通リポジトリ側（claude-python-toolkit）

共通リポジトリの`.gitignore`に以下を追加:

```gitignore
# プロジェクト固有ファイルを除外
local-*
```

**理由**:
- 共通リポジトリには`local-`ファイルを含めない
- 万が一Subtree pushで`local-`ファイルが送られても、`.gitignore`で無視される

## リスク管理と対策

### リスク1: Subtree追加時のコンフリクト

**対策**:
- バックアップを必ず作成（`.claude.backup`）
- `--allow-unrelated-histories`フラグを使用
- 段階的に統合（一気にやらない）

**バックアップ手順**:
```bash
cp -r .claude .claude.backup
git log --oneline --all > .git-history-backup.txt
git branch --show-current > .git-current-state.txt
git rev-parse HEAD >> .git-current-state.txt
cd ..
tar -czf ai-curated-newsletter-backup-$(date +%Y%m%d-%H%M%S).tar.gz ai-curated-newsletter/
```

### リスク2: プロジェクト固有ファイルの誤共有

**対策**:
- `.gitignore`で`local-*`を除外
- 共通リポジトリに`local-`ファイルが存在しないことを定期確認
- 命名規則を厳守

**確認コマンド**:
```bash
# 共通リポジトリでlocal-ファイルがないことを確認
find . -name "local-*" | wc -l
# 出力が 0 であること
```

### リスク3: Subtree更新時のマージコンフリクト

**対策**:
- 手動マージを前提に、conflictが発生したら慎重に解決
- `git status`で確認後、エディタで手動マージ
- 重要な変更はPRベースのフローに変更（共通リポジトリ側）

## 検証方法

### End-to-End検証

#### 1. 共通リポジトリの確認

```bash
cd ~/Development/projects/claude-python-toolkit

# local- ファイルが存在しないことを確認
find . -name "local-*" | wc -l
# 出力が 0 であること

# 必須ファイルの存在確認
ls commands/add-feature.md
ls commands/spec-plan.md
ls commands/implement.md
ls skills/steering/SKILL.md
ls agents/doc-reviewer.md
ls settings.example.json
ls CLAUDE.md.template
```

#### 2. プロジェクト側の確認

```bash
cd ~/Development/projects/ai-curated-newsletter

# Subtreeが正しく追加されていることを確認
make claude-status

# プロジェクト固有ファイルの存在確認
ls .claude/skills/local-python-qa/SKILL.md
ls .claude/settings.local.json

# 共通ファイルの存在確認
ls .claude/commands/spec-plan.md
ls .claude/skills/steering/SKILL.md
ls .claude/skills/python-pro/SKILL.md
```

#### 3. 動作確認

Claude Codeで以下を実行:
1. `/spec-plan`コマンドが動作するか（旧`/plan`）
2. `/implement`コマンドが動作するか
3. `Skill('steering')`が正しく読み込まれるか

品質チェックが動作するか:
```bash
.venv/bin/pytest tests/ -v
.venv/bin/ruff check src/
.venv/bin/mypy src/
```

#### 4. Subtree操作の確認

```bash
# 共通リポジトリで小さな変更を加える
cd ~/Development/projects/claude-python-toolkit
echo "# テスト変更" >> README.md
git add README.md
git commit -m "Test: Add test change to README"
git push origin main

# プロジェクト側で更新を取得
cd ~/Development/projects/ai-curated-newsletter
make claude-update

# 変更が反映されていることを確認
cat .claude/README.md | grep "テスト変更"
```

## 実装の順序

### フェーズ1: 共通リポジトリ作成（4時間）

1. GitHubで新規リポジトリ作成
2. 基本構造作成（commands, skills, agents）
3. 共通ファイル移行
4. README.md作成
5. Git commit & push

### フェーズ2: 現プロジェクトでの統合（3時間）

1. Makefile作成
2. 既存`.claude`をGitから削除
3. Subtree追加
4. プロジェクト固有ファイル配置
5. `.gitignore`更新
6. Git commit & push

### フェーズ3: 検証とドキュメント整備（2時間）

1. 機能テスト
2. Subtree操作テスト
3. ドキュメント更新
4. （オプション）他プロジェクトでの試験導入

## パフォーマンス考慮事項

- Subtree操作はGit履歴を含むため、初回追加時は数秒かかる
- 更新時は`--squash`オプションを使用し、履歴を圧縮
- 大規模な変更時はブランチを作成してマージ

## セキュリティ考慮事項

- 共通リポジトリはPublicだが、機密情報は含まない
- プロジェクト固有の機密情報は`settings.local.json`に保存
- `.gitignore`でプロジェクト固有ファイルを除外

## 将来の拡張性

- Phase 2: CI/CDでの自動Subtree更新
- Phase 2: 共通リポジトリのバージョン管理（タグ付け）
- Phase 2: 他言語プロジェクト（TypeScript, Go）への展開
