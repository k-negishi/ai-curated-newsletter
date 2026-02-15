# ロールバックプラン

## 概要

Subtree統合後に問題が発生した場合に、元の状態に安全に戻すための手順を定義します。

---

## 前提条件

ロールバックを実行する前に、以下が完了していることを確認してください:

- [ ] バックアップが作成されている（`.claude.backup/`）
- [ ] Git履歴のバックアップが作成されている（`.git-history-backup.txt`）
- [ ] 現在のブランチとコミットIDが記録されている（`.git-current-state.txt`）
- [ ] プロジェクト全体のバックアップが作成されている（`.tar.gz`）

---

## ロールバックシナリオ

### シナリオ1: Subtree追加直後に問題が発生（フェーズ2完了時点）

**症状**:
- Subtree追加後にコンフリクトが解決できない
- `.claude/`ディレクトリの内容が壊れた
- Git履歴が意図しない状態になった

**ロールバック手順**:

#### ステップ1: 現在の状態を確認

```bash
# 現在のブランチとコミットIDを確認
git branch --show-current
git rev-parse HEAD

# Subtree統合前のコミットIDを確認
cat .git-current-state.txt
```

#### ステップ2: Subtree統合のコミットを取り消す

```bash
# Subtree統合のコミットを特定
git log --grep="Integrate claude-python-toolkit" --oneline

# コミットIDを確認（例: abc1234）
# Subtree統合前の状態に戻す
git reset --hard <Subtree統合前のコミットID>
```

**注意**: `git reset --hard`は作業ディレクトリの変更も破棄します。未コミットの変更がある場合は事前にstashしてください。

#### ステップ3: `.claude/`をバックアップから復元

```bash
# 現在の.claudeを削除
rm -rf .claude

# バックアップから復元
cp -r .claude.backup .claude

# 復元を確認
ls -la .claude/
```

#### ステップ4: Gitにステージング

```bash
# .claudeを再度Git管理に追加
git add .claude

# コミット
git commit -m "Rollback: Restore .claude from backup"
```

#### ステップ5: リモートにプッシュ（必要に応じて）

```bash
# force pushが必要な場合（慎重に）
git push origin main --force-with-lease
```

**検証**:
```bash
# .claudeの内容が元に戻っていることを確認
ls -la .claude/commands/
ls -la .claude/skills/

# Gitステータスを確認
git status
```

---

### シナリオ2: 運用開始後に問題が発生（フェーズ3以降）

**症状**:
- Subtree更新（`make claude-update`）後に問題が発生
- コマンドやスキルが正しく動作しない
- プロジェクト固有ファイルが失われた

**ロールバック手順**:

#### ステップ1: Subtree更新前の状態に戻す

```bash
# 最後のSubtree更新のコミットを特定
git log --grep="git-subtree-dir: .claude" --oneline | head -1

# コミットIDを確認（例: def5678）
# Subtree更新前の状態に戻す
git reset --hard <Subtree更新前のコミットID>
```

#### ステップ2: プロジェクト固有ファイルの確認

```bash
# local-ファイルが存在することを確認
ls -la .claude/skills/local-python-qa/
ls -la .claude/settings.local.json

# 存在しない場合はバックアップから復元
cp -r .claude.backup/skills/local-python-qa .claude/skills/
cp .claude.backup/settings.local.json .claude/
```

#### ステップ3: 動作確認

```bash
# コマンドが動作するか確認
# (Claude Codeで /spec-plan を実行)

# 品質チェックが動作するか確認
.venv/bin/pytest tests/ -v
.venv/bin/ruff check src/
.venv/bin/mypy src/
```

---

### シナリオ3: 共通リポジトリ自体に問題がある

**症状**:
- 共通リポジトリから取得したファイルにバグがある
- 共通リポジトリの構造が壊れている

**ロールバック手順**:

#### ステップ1: 共通リポジトリの特定のコミットを指定してpull

```bash
# 共通リポジトリの履歴を確認
cd ~/Development/projects/claude-python-toolkit
git log --oneline

# 正常だったコミットIDを特定（例: ghi9012）

# プロジェクト側で特定のコミットからpull
cd ~/Development/projects/ai-curated-newsletter
git subtree pull --prefix=.claude https://github.com/YOUR_USERNAME/claude-python-toolkit.git <コミットID> --squash
```

#### ステップ2: 共通リポジトリをロールバック（根本対策）

```bash
# 共通リポジトリ側で問題のあるコミットを取り消す
cd ~/Development/projects/claude-python-toolkit
git revert <問題のあるコミットID>
git push origin main

# 全プロジェクトで更新を取得
cd ~/Development/projects/ai-curated-newsletter
make claude-update
```

---

## 完全ロールバック: バックアップから全体を復元

**最終手段**: すべてがうまくいかない場合、プロジェクト全体をバックアップから復元します。

### 手順

#### ステップ1: 現在のプロジェクトをバックアップ（念のため）

```bash
cd /Users/Kei/Development/projects
mv ai-curated-newsletter ai-curated-newsletter-broken-$(date +%Y%m%d-%H%M%S)
```

#### ステップ2: バックアップを展開

```bash
# 最新のバックアップを確認
ls -lt ai-curated-newsletter-backup-*.tar.gz | head -1

# 展開
tar -xzf ai-curated-newsletter-backup-YYYYMMDD-HHMMSS.tar.gz
```

#### ステップ3: 復元を確認

```bash
cd ai-curated-newsletter

# .claudeの内容を確認
ls -la .claude/

# Gitステータスを確認
git status

# 動作確認
.venv/bin/pytest tests/ -v
```

---

## 部分的なロールバック

### `.claude/`ディレクトリのみをロールバック

```bash
# 現在の.claudeを削除
rm -rf .claude

# バックアップから復元
cp -r .claude.backup .claude

# Gitにステージング
git add .claude
git commit -m "Rollback: Restore .claude from backup"
```

### 特定のファイルのみをロールバック

```bash
# 特定のファイルをバックアップから復元
cp .claude.backup/commands/add-feature.md .claude/commands/

# Gitにステージング
git add .claude/commands/add-feature.md
git commit -m "Rollback: Restore add-feature.md from backup"
```

---

## ロールバック後の確認手順

### 1. `.claude/`の構造確認

```bash
# 必須ディレクトリの存在確認
ls -la .claude/commands/
ls -la .claude/skills/
ls -la .claude/agents/

# プロジェクト固有ファイルの存在確認
ls -la .claude/skills/local-python-qa/
ls -la .claude/settings.local.json
```

### 2. コマンド動作確認

```bash
# Claude Codeで以下を実行
# /spec-plan テスト機能
# /implement .steering/20260215-claude-python-toolkit共通リポジトリ化/
```

### 3. 品質チェック動作確認

```bash
.venv/bin/pytest tests/ -v
.venv/bin/ruff check src/
.venv/bin/mypy src/
```

### 4. Git状態確認

```bash
# ステータス確認
git status

# 履歴確認
git log --oneline | head -10

# Subtree状態確認（統合済みの場合）
make claude-status
```

---

## ロールバック判断基準

### 即座にロールバックすべきケース

- [ ] `.claude/`ディレクトリの内容が完全に失われた
- [ ] Git履歴が壊れてcheckoutできない
- [ ] コマンドやスキルがまったく動作しない
- [ ] プロジェクト固有ファイル（`local-*`）が失われた
- [ ] テストがすべて失敗する

### 修正を試みるべきケース

- [ ] 一部のコマンドが動作しない（個別に修正可能）
- [ ] コンフリクトが発生したが解決可能
- [ ] 共通リポジトリの特定のファイルに問題がある（個別にロールバック）

### 運用を継続すべきケース

- [ ] 軽微な設定の不整合（修正で対応可能）
- [ ] ドキュメントの誤り（更新で対応可能）
- [ ] パフォーマンスの低下（最適化で対応可能）

---

## ロールバック実行時の注意事項

### 1. リモートへのforce push

```bash
# force pushは慎重に（他の開発者がいる場合は特に）
git push origin main --force-with-lease

# 他の開発者に通知
# "Subtree統合をロールバックしました。git pull --rebase してください"
```

### 2. 作業中の変更の保護

```bash
# ロールバック前に必ずstash
git stash push -m "Before rollback"

# ロールバック後に復元
git stash pop
```

### 3. バックアップの管理

```bash
# 古いバックアップを削除しない（最低1週間は保持）
# 問題が後から発覚する可能性があるため

# バックアップの確認
ls -lt .claude.backup/
ls -lt ../ai-curated-newsletter-backup-*.tar.gz
```

---

## ロールバック後の再統合

ロールバック後、問題を修正してから再度Subtree統合を試みる場合:

### 1. 問題の原因を特定

```bash
# ログを確認
git log --grep="git-subtree" --oneline

# コンフリクトの原因を分析
# （前回のエラーメッセージを参照）
```

### 2. 対策を実施

- 共通リポジトリの構造を修正
- ファイル名の衝突を解消
- `.gitignore`の設定を確認

### 3. 再度Subtree統合

```bash
# 慎重に再統合
make claude-init

# 各ステップで確認
git status
ls -la .claude/
```

---

## まとめ

- **最優先**: バックアップが命。必ず事前に作成
- **段階的**: 部分的なロールバックから試す
- **慎重に**: force pushは最終手段
- **記録**: 何が起きたか、何をしたかを記録
- **再発防止**: 問題の原因を特定して再発を防ぐ

ロールバックは失敗ではなく、安全に元の状態に戻す正当な手段です。問題が発生したら、慌てずにこのプランに従って対処してください。
