# 設計書

## アーキテクチャ概要

ruff設定の分離と強化を行う。設定ファイルの構造はシンプルで、以下の方針で設計する:

1. **設定ファイルの分離**: pyproject.tomlからruff設定を削除し、ruff.tomlに独立させる
2. **段階的なルール構成**: フェーズごとにルールをグループ化し、コメントで明確に分類する
3. **日本語コメント**: 各ルールの目的とプロジェクト固有の理由を日本語で説明
4. **既存設定の継承**: 現在のline-length、target-version、format設定を維持

## コンポーネント設計

### 1. ruff.toml（新規作成）

**責務**:
- ruffの全設定を集約
- ルールの有効化・無効化
- 各ルールの閾値設定（C901の複雑度閾値など）
- フォーマッター設定

**実装の要点**:
- **セクション構成**:
  - `[tool.ruff]`: 基本設定（line-length、target-version）
  - `[tool.ruff.lint]`: lintルール設定（select、ignore）
  - `[tool.ruff.lint.mccabe]`: 循環的複雑度の閾値設定
  - `[tool.ruff.format]`: フォーマッター設定
- **日本語コメント**: 各ルールに対して「# ルール名: 何をチェックするか（なぜ必要か）」の形式でコメント
- **フェーズ分類**: `# === フェーズ1: 基本ルール（導入済み） ===` のように区切る

### 2. pyproject.toml（既存ファイルの修正）

**責務**:
- Python依存関係の定義
- pytest設定の保持
- mypy設定の保持
- ruff設定の削除

**実装の要点**:
- `[tool.ruff]` セクション全体を削除
- `[tool.ruff.lint]` セクション全体を削除
- `[tool.ruff.format]` セクション全体を削除（該当する場合）
- 他のツール設定（pytest、mypy）はそのまま維持

## データフロー

### ruff実行フロー
```
1. ruff check src/ 実行
2. カレントディレクトリのruff.tomlを読み込み
3. src/配下のPythonファイルをスキャン
4. 有効化されたルールに基づいてチェック
5. エラー/警告を出力
6. ruff check src/ --fix で自動修正可能なものを修正
7. 手動修正が必要なものをリストアップ
```

## ルール設計

### フェーズ1: 基本ルール（導入済み）

| コード | ルール名 | 目的 | おすすめ度 |
|--------|---------|------|-----------|
| E | pycodestyle errors | PEP8エラー（空白、行長等） | ⭐⭐⭐ |
| W | pycodestyle warnings | PEP8警告 | ⭐⭐⭐ |
| F | pyflakes | 未使用変数・import、未定義変数 | ⭐⭐⭐ |
| I | isort | import文の並び順・グループ化 | ⭐⭐⭐ |
| B | flake8-bugbear | よくあるバグパターン検出 | ⭐⭐⭐ |
| C4 | flake8-comprehensions | 内包表記の最適化 | ⭐⭐ |
| UP | pyupgrade | 古い構文のモダン化 | ⭐⭐⭐ |

### フェーズ2: 次に入れる

| コード | ルール名 | 目的 | おすすめ度 | このプロジェクトでの理由 |
|--------|---------|------|-----------|-------------------------|
| S | bandit | セキュリティ | ⭐⭐⭐ | boto3+httpxで認証情報漏洩・インジェクション検出 |
| ASYNC | flake8-async | asyncアンチパターン | ⭐⭐⭐ | httpx+pytest-asyncio使用。async誤用防止 |
| C901 | mccabe | 循環的複雑度 | ⭐⭐⭐ | 複雑度管理。閾値10推奨 |
| T20 | flake8-print | print文検出 | ⭐⭐⭐ | structlog使用中にprint混入を防止 |
| SIM | flake8-simplify | コード簡素化 | ⭐⭐ | 冗長な条件分岐・ループの改善提案 |

### フェーズ3: 安定後

| コード | ルール名 | 目的 | おすすめ度 | このプロジェクトでの理由 |
|--------|---------|------|-----------|-------------------------|
| PT | flake8-pytest-style | pytestベストプラクティス | ⭐⭐ | pytest使用中。fixture/assertの書き方統一 |
| RET | flake8-return | return文の改善 | ⭐⭐ | 不要なelse/return Noneの検出 |
| PIE | flake8-pie | 不要コード検出 | ⭐⭐ | 不要なpass文・不要スプレッド等 |
| N | pep8-naming | 命名規則 | ⭐⭐ | クラス名・関数名の命名統一 |
| PL | pylint | pylint互換チェック群 | ⭐ | PLR(リファクタ)、PLE(エラー)等 |
| RUF | Ruff独自 | Ruff独自ルール | ⭐⭐ | 他ツールにない独自検出 |

### フェーズ4: チーム合意後

| コード | ルール名 | 目的 | おすすめ度 | このプロジェクトでの理由 |
|--------|---------|------|-----------|-------------------------|
| TCH | flake8-type-checking | TYPE_CHECKING最適化 | ⭐ | mypy strict+型ヒント多用時に実行時importを削減 |
| D | pydocstyle | docstring形式チェック | ⭐ | docstringルールはチーム合意が必要 |
| LOG | flake8-logging | logging誤用検出 | ⭐ | structlog主体だが標準logging混入チェック |

### ignore設定の設計

**既存のignore**:
- `E501`: line too long (formatterが処理するため)

**追加が必要になる可能性のあるignore**（実装中に判断）:
- 既存コードで大量に発生し、修正が困難な場合のみignoreに追加
- 追加する場合は必ず理由をコメント

## エラーハンドリング戦略

### ruff実行エラー

**設定ファイルエラー**:
- ruff.tomlの構文エラー → 修正後に再実行
- 存在しないルールコードの指定 → 削除または正しいコードに修正

**チェックエラー**:
- 自動修正可能 → `ruff check src/ --fix` で修正
- 手動修正が必要 → エラーメッセージを確認して個別に修正

### 既存コード修正の優先順位

1. **自動修正可能なもの**: `ruff check src/ --fix` で一括修正
2. **重大度の高いもの**: セキュリティ（S）、async誤用（ASYNC）
3. **中程度**: 複雑度（C901）、print文（T20）
4. **軽微なもの**: 命名規則（N）、簡素化（SIM）、不要コード（PIE）

## TDDサイクル

linter設定の強化はTDD（Test-Driven Development）の対象ではないが、以下のサイクルで実装を進める:

### RED: ルールを有効化してエラーを確認

1. ruff.tomlに新しいルールを追加
2. `ruff check src/` を実行
3. 新しいルールによるエラー/警告を確認
4. エラー件数を記録

### GREEN: エラーを修正してチェックをパスさせる

1. `ruff check src/ --fix` で自動修正
2. 残りのエラーを手動修正
3. `ruff check src/` を実行してAll checks passed!を確認

### REFACTOR: コード品質を向上させる

1. 修正したコードをレビュー
2. 可読性や保守性の観点で改善
3. `pytest tests/` でテストがパスすることを確認
4. `mypy src/` で型チェックがパスすることを確認

## テスト戦略

### linter設定のテスト

**手動テスト**:
- `ruff check src/` で全チェックがパスすることを確認
- `ruff format src/` でフォーマットが正しく適用されることを確認

**CI/CDでのテスト**（既存の `.github/workflows/ci.yml` を活用）:
- プルリクエスト時に `ruff check src/` を自動実行
- `ruff format --check src/` でフォーマット違反をチェック

### 既存テストの実行

**ユニットテスト**:
- `pytest tests/unit/ -v` で全テストがパスすることを確認

**統合テスト**:
- `pytest tests/integration/ -v` で全テストがパスすることを確認

**E2Eテスト**:
- `pytest tests/e2e/ -v` で全テストがパスすることを確認

**型チェック**:
- `mypy src/` で型エラーがないことを確認

## 依存ライブラリ

既存の依存関係を維持:

```toml
[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "pytest-cov>=4.1.0",
    "mypy>=1.8.0",
    "ruff>=0.2.0",  # 既存
    # ...
]
```

新しい依存関係の追加は不要（ruffは既にインストール済み）

## ディレクトリ構造

```
ai-curated-newsletter/
├── ruff.toml                 # 新規作成
├── pyproject.toml            # ruff設定を削除
├── src/                      # 既存コードを修正
│   ├── handler.py
│   ├── orchestrator/
│   ├── services/
│   ├── repositories/
│   ├── models/
│   └── shared/
└── tests/                    # テストは修正不要（既存のテストがパスすることを確認）
```

## 実装の順序

### フェーズ1: 設定ファイルの分離

1. ruff.tomlを新規作成（基本設定のみ）
2. pyproject.tomlからruff設定を削除
3. `ruff check src/` を実行して動作確認（基本ルールが正しく適用されることを確認）

### フェーズ2: フェーズ2ルールの導入と修正

1. ruff.tomlにフェーズ2ルール（S, ASYNC, C901, T20, SIM）を追加
2. `ruff check src/` を実行してエラー件数を確認
3. `ruff check src/ --fix` で自動修正
4. 残りのエラーを手動修正
5. `ruff check src/` でAll checks passed!を確認

### フェーズ3: フェーズ3ルールの導入と修正

1. ruff.tomlにフェーズ3ルール（PT, RET, PIE, N, PL, RUF）を追加
2. エラー修正（フェーズ2と同様）

### フェーズ4: フェーズ4ルールの導入と修正

1. ruff.tomlにフェーズ4ルール（TCH, D, LOG）を追加
2. エラー修正（フェーズ2と同様）

### フェーズ5: 最終確認

1. `pytest tests/` で全テストがパスすることを確認
2. `mypy src/` で型チェックがパスすることを確認
3. `ruff check src/` でAll checks passed!を確認
4. `ruff format src/` でコードフォーマットを実行

## セキュリティ考慮事項

- **S (bandit) ルールの導入により、以下のセキュリティリスクを自動検出**:
  - ハードコードされた認証情報（API キー、パスワード等）
  - SQL インジェクション
  - コマンドインジェクション
  - 弱い暗号化アルゴリズムの使用
  - 安全でないデシリアライゼーション

- **既存コードでの対応**:
  - boto3使用時の認証情報は環境変数またはAWS Secrets Managerから取得していることを確認
  - httpx使用時のURL構築が安全であることを確認
  - structlogによるログ出力が適切であることを確認

## パフォーマンス考慮事項

- **ruff実行時間**: ruffはRust製で高速なため、全ルールを有効化してもチェック時間への影響は軽微（数秒程度）
- **CI/CD実行時間**: 既存のCI/CDパイプラインでのruffチェック時間が若干増加する可能性があるが、許容範囲内

## 将来の拡張性

- **pre-commitフック**: 将来的にローカル開発環境でコミット前にruffチェックを自動実行するフックを追加可能
- **ルールのカスタマイズ**: プロジェクトの成長に応じて、ignoreルールを追加・削除可能
- **CI/CDの強化**: ruff checkの結果をPRコメントに自動投稿する機能を追加可能
- **複数環境対応**: 開発環境と本番環境で異なるルールセットを適用可能（現時点では不要）
