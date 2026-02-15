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

## 【最重要】初手: バックアップ作成

**すべての作業を開始する前に、必ずバックアップを作成してください。**

- [x] `.claude`ディレクトリのバックアップを作成
  ```bash
  cp -r .claude .claude.backup
  ```
- [x] Git履歴のバックアップを作成
  ```bash
  git log --oneline --all > .git-history-backup.txt
  ```
- [x] 現在のブランチとコミットIDを記録
  ```bash
  git branch --show-current > .git-current-state.txt
  git rev-parse HEAD >> .git-current-state.txt
  ```
- [x] プロジェクト全体のバックアップ（推奨）
  ```bash
  cd /Users/Kei/Development/projects
  tar -czf ai-curated-newsletter-backup-$(date +%Y%m%d-%H%M%S).tar.gz ai-curated-newsletter/
  ```
- [x] バックアップの確認
  ```bash
  ls -la .claude.backup/
  ls -la .git-history-backup.txt
  ls -la .git-current-state.txt
  ls -la ../ai-curated-newsletter-backup-*.tar.gz
  ```

---

## フェーズ1: 共通リポジトリ作成（4時間）

### 1-1. GitHubで新規リポジトリ作成

- [x] GitHubにログインして新規リポジトリを作成
  - リポジトリ名: `claude-python-toolkit`
  - 公開設定: Public
  - 初期化: README.md, .gitignore (Python)

### 1-2. ローカルにcloneして基本構造を作成

- [x] リポジトリをローカルにclone
  ```bash
  cd ~/Development/projects
  git clone https://github.com/k-negishi/claude-python-toolkit.git
  cd claude-python-toolkit
  ```
- [x] 基本ディレクトリ構造を作成
  ```bash
  mkdir -p commands skills agents
  ```
  

### 1-3. 共通ファイルを移行

**Commands（6個）**:
- [x] `add-feature.md`をコピー
- [x] `plan.md`を`spec-plan.md`にリネームしてコピー
- [x] `review-docs.md`をコピー
- [x] `commit-push-close.md`をコピー
- [x] `research-plan.md`をコピー
- [x] `setup-project.md`をコピー

**Skills（10スキル、計23ファイル）**:
- [x] `steering/`ディレクトリをコピー
- [x] `prd-writing/`ディレクトリをコピー
- [x] `functional-design/`ディレクトリをコピー
- [x] `architecture-design/`ディレクトリをコピー
- [x] `repository-structure/`ディレクトリをコピー
- [x] `glossary-creation/`ディレクトリをコピー
- [x] `git-commit/`ディレクトリをコピー
- [x] `close-issue/`ディレクトリをコピー
- [x] `feedback-response/`ディレクトリをコピー
- [x] `python-pro/`ディレクトリをコピー（共通化）

**Agents（2個）**:
- [x] `doc-reviewer.md`をコピー
- [x] `implementation-validator.md`から共通部分を抽出してコピー

**設定ファイル**:
- [x] `settings.example.json`をテンプレートとして作成
  - 現在の`.claude/settings.json`からプロジェクト固有部分を除外
- [x] `CLAUDE.md.template`を作成
  - 現在の`CLAUDE.md`からスペック駆動開発の基本原則を抽出
- [x] `Makefile.example`を作成
  - Subtree操作コマンド（claude-init, claude-update, claude-push, claude-status）を定義

### 1-4. `.gitignore`設定

- [x] 共通リポジトリの`.gitignore`に`local-*`を追加
  ```bash
  echo "" >> .gitignore
  echo "# プロジェクト固有ファイルを除外" >> .gitignore
  echo "local-*" >> .gitignore
  ```

### 1-5. `local-`ファイルが存在しないことを確認

- [x] 共通リポジトリに`local-`ファイルが存在しないことを確認
  ```bash
  find . -name "local-*" | wc -l
  # 出力が 0 であること
  ```

### 1-6. README.md作成

- [x] README.mdに以下を記述
  - 使用方法（Subtree追加、更新、プッシュ）
  - ディレクトリ構造
  - 命名規則の説明（`local-`プレフィックス）
  - 必須ファイルの一覧

### 1-7. Git commit & push

- [x] git addでファイルを追加
  ```bash
  git add .
  ```
- [x] git commitでコミット
  ```bash
  git commit -m "Initial commit: Setup shared workflow repository"
  ```
- [x] git pushでプッシュ
  ```bash
  git push origin main
  ```

---

## フェーズ2: 現プロジェクトでの統合（3時間）

### 2-1. Makefile.exampleからMakefileを作成

**注意**: この時点ではまだSubtreeを追加していないため、共通リポジトリから直接ダウンロードするか、手動で作成します。

- [x] 共通リポジトリの`Makefile.example`をダウンロード
  ```bash
  curl -O https://raw.githubusercontent.com/YOUR_USERNAME/claude-python-toolkit/main/Makefile.example
  ```
- [x] `Makefile.example`を`Makefile`にコピー
  ```bash
  cp Makefile.example Makefile
  ```
- [x] `YOUR_USERNAME`を実際のGitHubユーザー名に置換
  ```bash
  sed -i '' 's/YOUR_USERNAME/actual-username/g' Makefile
  ```
- [x] `Makefile.example`を削除
  ```bash
  rm Makefile.example
  ```

### 2-2. 既存`.claude`をGitから削除

- [ ] `.claude`をGitから削除（ワーキングツリーには残す）
  ```bash
  git rm -r --cached .claude
  ```
- [ ] コミット
  ```bash
  git commit -m "Remove .claude directory before Subtree integration"
  ```

### 2-3. Subtree追加

- [ ] `make claude-init`を実行
  ```bash
  make claude-init
  ```
- [ ] Subtree追加が成功したことを確認
  ```bash
  make claude-status
  ```

### 2-4. プロジェクト固有ファイルを配置

**`local-python-qa`スキル作成**:
- [x] `.claude/skills/local-python-qa/`ディレクトリを作成
  ```bash
  mkdir -p .claude/skills/local-python-qa
  ```
- [x] `SKILL.md`を作成
  - ステップ0: 実装前の品質チェック（mypy, ruff）
  - ステップ4: 自動テストと品質チェック（pytest, ruff, mypy）
  - `/implement`から`Skill('local-python-qa')`で読み込まれる内容

**設定ファイル配置**:
- [x] `.claude/settings.local.json`をコピー
  - 既存の`settings.json`から必要な部分をコピー

**CLAUDE.md更新**:
- [ ] プロジェクトルートの`CLAUDE.md`をプロジェクト固有部分のみに更新
  - 技術スタック（Python）
  - 品質チェック（pytest, ruff, mypy）
  - ローカル実行（Lambda関数）

### 2-5. Subtree統合をコミット&プッシュ

**注意**: プロジェクト側（ai-curated-newsletter）では`.gitignore`を更新しない。`local-`ファイルも通常通りcommit可能。共通リポジトリ側の`.gitignore`は既にフェーズ1で設定済み。

- [ ] git addでファイルを追加
  ```bash
  git add .
  ```
- [ ] git commitでコミット
  ```bash
  git commit -m "Integrate claude-python-toolkit via Git Subtree"
  ```
- [ ] git pushでプッシュ
  ```bash
  git push origin main
  ```

---

## フェーズ3: 検証とドキュメント整備（2時間）

### 3-1. 機能テスト

- [ ] `/spec-plan`コマンドの動作確認
  - Claude Codeで`/spec-plan テスト機能`を実行
  - ステアリングファイルが正しく作成されることを確認
- [ ] `/implement`コマンドの動作確認
  - 作成したステアリングファイルで`/implement`を実行
  - TDDサイクルが正しく実行されることを確認
- [ ] 品質チェックの動作確認
  ```bash
  .venv/bin/pytest tests/ -v
  .venv/bin/ruff check src/
  .venv/bin/mypy src/
  ```

### 3-2. Subtree操作テスト

**更新テスト（`make claude-update`）**:
- [ ] 共通リポジトリで小さな変更を加える
  ```bash
  cd ~/Development/projects/claude-python-toolkit
  echo "# テスト変更" >> README.md
  git add README.md
  git commit -m "Test: Add test change to README"
  git push origin main
  ```
- [ ] プロジェクト側で更新を取得
  ```bash
  cd ~/Development/projects/ai-curated-newsletter
  make claude-update
  ```
- [ ] 変更が反映されていることを確認
  ```bash
  cat .claude/README.md | grep "テスト変更"
  ```

**プッシュテスト（`make claude-push`）**:
- [ ] プロジェクト側で共通ファイルに小さな変更を加える
  ```bash
  echo "# プロジェクト側からの変更" >> .claude/README.md
  git add .claude/README.md
  git commit -m "Test: Modify shared file from project"
  ```
- [ ] 共通リポジトリにプッシュ
  ```bash
  make claude-push
  ```
- [ ] 共通リポジトリで変更が反映されていることを確認
  ```bash
  cd ~/Development/projects/claude-python-toolkit
  git pull origin main
  cat README.md | grep "プロジェクト側からの変更"
  ```

### 3-3. ドキュメント更新

**プロジェクトREADME.md更新**:
- [ ] プロジェクトのREADME.mdに以下を追記
  - Subtreeの使い方
  - Makefileコマンドの説明（`make claude-init`, `make claude-update`, `make claude-push`, `make claude-status`）
  - プロジェクト固有ファイルの説明（`local-`プレフィックス）

**共通リポジトリREADME.md更新**:
- [ ] 共通リポジトリのREADME.mdに以下を追加
  - 実際の使用例
  - Subtree追加のコマンド例
  - トラブルシューティング

### 3-4. 最終確認

- [ ] 共通リポジトリに`local-`ファイルが存在しないことを確認
  ```bash
  cd ~/Development/projects/claude-python-toolkit
  find . -name "local-*" | wc -l
  # 出力が 0 であること
  ```
- [ ] プロジェクト側で必要なファイルが揃っていることを確認
  ```bash
  cd ~/Development/projects/ai-curated-newsletter
  ls .claude/commands/spec-plan.md
  ls .claude/skills/steering/SKILL.md
  ls .claude/skills/local-python-qa/SKILL.md
  ls .claude/settings.local.json
  ```
- [ ] 全てのMakefileコマンドが動作することを確認
  ```bash
  make claude-status
  ```

---

## 実装後の振り返り

### 実装完了日
{YYYY-MM-DD}

### 計画と実績の差分

**計画と異なった点**:
- {計画時には想定していなかった技術的な変更点}
- {実装方針の変更とその理由}

**新たに必要になったタスク**:
- {実装中に追加したタスク}
- {なぜ追加が必要だったか}

**技術的理由でスキップしたタスク**（該当する場合のみ）:
- {タスク名}
  - スキップ理由: {具体的な技術的理由}
  - 代替実装: {何に置き換わったか}

**⚠️ 注意**: 「時間の都合」「難しい」などの理由でスキップしたタスクはここに記載しないこと。全タスク完了が原則。

### 学んだこと

**技術的な学び**:
- {Git Subtreeの使い方}
- {共通化と個別化のバランス}
- {命名規則の重要性}

**プロセス上の改善点**:
- {段階的な移行の効果}
- {バックアップの重要性}
- {テストと検証の重要性}

**コスト・パフォーマンスの成果**（該当する場合）:
- {新規プロジェクト立ち上げ時間の短縮}
- {ワークフロー改善の効率化}

### 次回への改善提案

**計画フェーズでの改善点**:
- {ファイル分類の基準を明確化}
- {リスク管理の充実}

**実装フェーズでの改善点**:
- {バックアップ手順の自動化}
- {テスト手順の標準化}

**ワークフロー全体での改善点**:
- {CI/CDでの自動Subtree更新}
- {バージョン管理の導入}
- {他プロジェクトへの展開}
