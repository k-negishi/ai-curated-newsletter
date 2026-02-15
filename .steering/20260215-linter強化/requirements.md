# 要求内容

## GitHub Issue
https://github.com/k-negishi/ai-curated-newsletter/issues/32

## issue 内容
- **タイトル**: linter強化
- **本文**: ruffのtomlは別ファイルに分ける。以下のルールを導入。tomlには日本語で何やってるかコメントを書く
- **ラベル**: なし

## 概要

ruffのlinter設定を強化し、コード品質を向上させる。現在は基本ルール（E, W, F, I, B, C4, UP）のみ導入されているが、セキュリティ、async、複雑度、pytestなど、より広範囲のルールを段階的に導入する。また、設定ファイルをpyproject.tomlから独立したruff.tomlに分離し、日本語コメントで各ルールの目的を明確にする。

## 背景

### なぜこの機能が必要か

1. **コード品質の向上**: 基本ルールだけでは検出できないバグパターンやアンチパターンを早期発見する必要がある
2. **セキュリティ強化**: boto3とhttpxを使用しているため、認証情報漏洩やインジェクション攻撃のリスクを自動検出したい
3. **非同期コードの品質**: httpx + pytest-asyncioを使用しているため、asyncアンチパターンを防ぐ必要がある
4. **保守性の向上**: 循環的複雑度管理やprint文検出により、保守しやすいコードベースを維持したい
5. **設定の可読性**: pyproject.tomlに設定が集中すると可読性が低下するため、ruff.tomlに分離して管理しやすくする
6. **日本語コメント**: 各ルールの目的を日本語で説明することで、チーム全体（将来的な拡張を想定）が理解しやすくする

### どんな問題を解決するか

- **検出漏れ**: 現在のルールでは検出できないバグパターンが本番環境で発覚する可能性がある
- **セキュリティリスク**: boto3使用時の認証情報ハードコードやhttpx使用時のインジェクション攻撃を防ぐ
- **非同期エラー**: async/awaitの誤用による実行時エラーやデッドロックを防ぐ
- **複雑すぎるコード**: 循環的複雑度が高いコードは保守性が低く、バグの温床になる
- **デバッグコードの残留**: print文が本番コードに残ると、structlogによる構造化ログの利点が損なわれる
- **設定の分散**: pyproject.tomlに全ての設定が集中すると、ruff特有の設定が見つけにくい

## 実装対象の機能

### 1. ruff設定の分離

- pyproject.tomlからruff設定を削除
- 独立したruff.tomlファイルを新規作成
- 既存の基本ルール（E, W, F, I, B, C4, UP）を引き継ぐ

### 2. フェーズ2ルールの導入

- **S (bandit)**: セキュリティチェック（boto3 + httpx使用時の認証情報漏洩・インジェクション検出）
- **ASYNC (flake8-async)**: asyncアンチパターン検出（httpx + pytest-asyncio使用）
- **C901 (mccabe)**: 循環的複雑度管理（閾値10推奨）
- **T20 (flake8-print)**: print文検出（structlog使用中にprint混入を防止）
- **SIM (flake8-simplify)**: コード簡素化（冗長な条件分岐・ループの改善提案）

### 3. フェーズ3ルールの導入

- **PT (flake8-pytest-style)**: pytestベストプラクティス（fixture/assertの書き方統一）
- **RET (flake8-return)**: return文の改善（不要なelse/return Noneの検出）
- **PIE (flake8-pie)**: 不要コード検出（不要なpass文・不要スプレッド等）
- **N (pep8-naming)**: 命名規則（クラス名・関数名の命名統一）
- **PL (pylint)**: pylint互換チェック群（PLE、PLW、PLR0911、PLR0912、PLR0913、PLR2004）
- **RUF (Ruff独自)**: Ruff独自ルール

### 4. フェーズ4ルールの導入（チーム合意後）

- **TCH (flake8-type-checking)**: TYPE_CHECKING最適化（mypy strict + 型ヒント多用時に実行時importを削減）
- **D (pydocstyle)**: docstring形式チェック（Googleスタイル準拠）
- **LOG (flake8-logging)**: logging誤用検出（structlog主体だが標準logging混入チェック）

### 5. 日本語コメントの追加

- 各ルールに対して、何をチェックするのか日本語でコメント
- なぜこのルールが必要なのか、プロジェクト固有の理由をコメント
- ignoreに追加したルールについても、なぜignoreしたのか理由をコメント

### 6. 既存コードの修正

- 新しいルールを適用した際に出るエラー/警告をすべて修正
- ruff check src/ --fix で自動修正可能なものは自動修正
- 手動修正が必要なものは個別に対応
- 全てのチェックがパスすることを確認

## 受け入れ条件

### ruff設定の分離
- [ ] pyproject.tomlからruff設定が削除されている
- [ ] ruff.tomlが新規作成され、全ての設定が移行されている
- [ ] ruff check src/ が正常に動作する（設定ファイルを正しく読み込む）

### フェーズ2ルールの導入
- [ ] S (bandit) が有効化されている
- [ ] ASYNC (flake8-async) が有効化されている
- [ ] C901 (mccabe) が有効化され、閾値10に設定されている
- [ ] T20 (flake8-print) が有効化されている
- [ ] SIM (flake8-simplify) が有効化されている

### フェーズ3ルールの導入
- [ ] PT (flake8-pytest-style) が有効化されている
- [ ] RET (flake8-return) が有効化されている
- [ ] PIE (flake8-pie) が有効化されている
- [ ] N (pep8-naming) が有効化されている
- [ ] PL (pylint) が有効化されている（PLE、PLW、PLR0911、PLR0912、PLR0913、PLR2004）
- [ ] RUF (Ruff独自) が有効化されている

### フェーズ4ルールの導入
- [ ] TCH (flake8-type-checking) が有効化されている
- [ ] D (pydocstyle) が有効化されている
- [ ] LOG (flake8-logging) が有効化されている

### 日本語コメントの追加
- [ ] 各ルールに日本語コメントが追加されている
- [ ] コメントには「何をチェックするか」と「なぜ必要か」が記載されている
- [ ] ignoreに追加したルールについても理由がコメントされている

### 既存コードの修正
- [ ] ruff check src/ でエラー/警告が0件になっている
- [ ] All checks passed! が表示される
- [ ] 自動修正可能なものは ruff check src/ --fix で修正済み
- [ ] 手動修正が必要なものも全て対応済み

## 成功指標

- **定量的な目標**:
  - ruff check src/ の実行結果が "All checks passed!" になる
  - 導入ルール数: 基本7ルール → 全27ルール（約4倍）
  - カバー範囲: PEP8準拠 → セキュリティ・async・複雑度・pytest・命名規則等を包括

- **定性的な目標**:
  - コード品質が向上し、バグの早期発見が可能になる
  - セキュリティリスクが自動検出される
  - チーム全体（将来的な拡張を想定）がルールの目的を理解できる
  - 保守性の高いコードベースが維持される

## スコープ外

以下はこのフェーズでは実装しません:

- **CI/CDパイプラインへの統合**: 既存の `.github/workflows/ci.yml` は既にruffチェックを含んでいるため、設定ファイル分離後も動作するが、新しいルールの追加はスコープ外
- **pre-commitフックの追加**: ローカル開発環境でのコミット前チェックは将来的な拡張として検討
- **ルールの段階的な有効化**: 全ルールを一度に導入する方針のため、段階的な有効化はスコープ外
- **既存のignore設定の見直し**: 現在のignore設定（E501など）はそのまま維持

## 実装方針

- Kent Beck の TDD (Test-Driven Development) で実装する
- RED → GREEN → REFACTOR のサイクルを遵守
- テストを先に書き、最小限の実装でパスさせ、その後リファクタリング

## 参照ドキュメント

- `docs/product-requirements.md` - プロダクト要求定義書
- `docs/functional-design.md` - 機能設計書
- `docs/architecture.md` - アーキテクチャ設計書
- `docs/development-guidelines.md` - 開発ガイドライン（ruffの使用方法が記載されている）
- issue #32: https://github.com/k-negishi/ai-curated-newsletter/issues/32
