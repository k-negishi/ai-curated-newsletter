# 要求内容

## 概要

`.claude`ディレクトリをGit Subtreeで共通リポジトリ化し、複数のPythonプロジェクト間でワークフロー（コマンド、スキル、エージェント）を共有する仕組みを構築する。

**採用パターン**: パターンB（`.claude/`がSubtree、プロジェクト固有ファイルも`.claude/`内に混在）

## 背景

### 現在の問題点

- **非効率な管理**: プロジェクトごとに同じワークフローを手動でコピー・メンテナンスしている
- **知見の分散**: 改善が一箇所に集約されず、知見が分散している
- **新規プロジェクトの負担**: 新規プロジェクト立ち上げ時に毎回設定を作り直す必要がある

### なぜこの機能が必要か

現在、`.claude`ディレクトリにはスペック駆動開発のワークフローが蓄積されており、これらは他のPythonプロジェクトでも再利用可能な汎用的な内容が多く含まれています。これらを共通化することで、以下の問題を解決できます:

- プロジェクト間でのワークフローの一貫性を保つ
- ワークフロー改善を1箇所で行い、全プロジェクトに波及させる
- 新規プロジェクトでの立ち上げ時間を短縮

## 実装対象の機能

### 1. 共通リポジトリの作成

**リポジトリ名**: `claude-python-toolkit`

**公開設定**: Public

**命名規則**:
- **共通リポジトリ**: `local-`プレフィックスのファイルは置かない（厳守）
- **プロジェクト側**: プロジェクト固有ファイルには必ず`local-`プレフィックスを付ける

**共通化するファイル（約25ファイル）**:
- **Commands（6個）**: add-feature.md, spec-plan.md（旧plan.md）, review-docs.md, commit-push-close.md, research-plan.md, setup-project.md
- **Skills（10スキル、計23ファイル）**: steering/, prd-writing/, functional-design/, architecture-design/, repository-structure/, glossary-creation/, git-commit/, close-issue/, feedback-response/, python-pro/
- **Agents（2個）**: doc-reviewer.md, implementation-validator.md（一部修正）
- **設定**: settings.example.json（テンプレート）、CLAUDE.md.template（スペック駆動開発の基本原則）

**プロジェクト固有として残すファイル**:
- **Skills**: local-python-qa/（Python品質チェックスキル、`/implement`から読み込まれる）
- **設定**: settings.local.json、CLAUDE.md（プロジェクト固有部分のみ）

**内容分割が必要なファイル**:
- **implement.md**: 共通部分（TDD基本フロー）と個別部分（Python品質チェック）を分離
- **CLAUDE.md**: 共通部分（スペック駆動開発の基本原則）と個別部分（Python/AWS/Lambda実行方法）を分離
- **implementation-validator.md**: 共通部分（コーディング規約検証）と個別部分（Python特化検証）を分離

### 2. 現プロジェクトでのSubtree統合

**Makefile作成**:
- `claude-init`: Subtree追加
- `claude-update`: 共通リポジトリから更新取得
- `claude-push`: ローカル変更をプッシュ
- `claude-status`: Subtree状態確認

**統合フロー**:
1. 既存`.claude`をGitから削除
2. Subtreeで共通リポジトリを追加
3. プロジェクト固有ファイルを配置
4. `.gitignore`を更新

### 3. 検証とドキュメント整備

**機能テスト**:
- `/spec-plan`（旧`/plan`）コマンドの動作確認
- `/implement`コマンドの動作確認
- 品質チェック（pytest, ruff, mypy）の動作確認

**Subtree操作テスト**:
- `make claude-update`の動作確認
- `make claude-push`の動作確認

**ドキュメント更新**:
- プロジェクトREADME.mdにSubtreeの使い方を追記
- 共通リポジトリREADME.mdに実際の使用例を追加

## 受け入れ条件

### 共通リポジトリ作成

- [ ] 共通リポジトリ（claude-python-toolkit）が作成され、Publicで公開されている
- [ ] 共通ファイル（約25個）が共通リポジトリに配置されている
- [ ] `plan.md`が`spec-plan.md`にリネームされている
- [ ] 共通リポジトリに`local-`ファイルが存在しないことを確認

### Subtree統合

- [ ] Makefileが作成され、claude-init/update/push/statusが実装されている
- [ ] プロジェクト固有ファイルが`local-`プレフィックスで配置されている
- [ ] `.gitignore`が更新され、`local-*`が除外されている（ただし`settings.local.json`は強制track）
- [ ] Subtree統合がコミット&プッシュされている

### 機能確認

- [ ] `/spec-plan`（旧`/plan`）コマンドが正常に動作する
- [ ] `/implement`コマンドが正常に動作する
- [ ] 品質チェック（pytest, ruff, mypy）が正常に動作する
- [ ] Subtree更新（`make claude-update`）が動作する
- [ ] Subtreeプッシュ（`make claude-push`）が動作する

### ドキュメント更新

- [ ] プロジェクトREADME.mdにSubtreeの使い方が追記されている
- [ ] 共通リポジトリREADME.mdに使用例が追加されている

## 成功指標

### 定量的目標

- 共通ファイル数: 約25ファイル
- 新規プロジェクトでの立ち上げ時間: 5分以内（Subtree追加のみ）
- ワークフロー改善の波及時間: 5分以内（`make claude-update`実行のみ）

### 定性的目標

- 新規プロジェクトで即座に`.claude`設定を利用可能
- ワークフロー改善の効率化（1箇所の更新で全体に波及）
- Python開発のベストプラクティスを標準化

## スコープ外

以下はこのフェーズでは実装しません:

- 他プロジェクトへの展開（別タスクとして実施）
- CI/CDでの自動Subtree更新（Phase 2で検討）
- 共通リポジトリのバージョン管理（当面はmainブランチのみ）

## 参照ドキュメント

- `docs/product-requirements.md` - プロダクト要求定義書
- `docs/architecture.md` - アーキテクチャ設計書
- `docs/development-guidelines.md` - 開発ガイドライン

## 実装方針

- **Git Subtree**: Git SubmoduleではなくSubtreeを使用（理由: ファイルの実体を持ち、操作が簡単）
- **段階的移行**: 3フェーズに分けて段階的に実装
- **バックアップ必須**: すべての作業開始前に必ずバックアップを作成
- **リスク管理**: コンフリクトやマージエラーに備えた対策を事前に準備
