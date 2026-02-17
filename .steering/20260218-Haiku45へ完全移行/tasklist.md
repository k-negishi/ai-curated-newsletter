# Haiku 4.5 へ完全移行 タスクリスト

## GitHub Issue
https://github.com/k-negishi/ai-curated-newsletter/issues/35

## 概要
コードベースに残っている Claude 3.5 Sonnet の参照を完全に除去し、Claude Haiku 4.5 (`anthropic.claude-haiku-4-5-20251001-v1:0`) に統一する。

## 実装方針
- 文字列の置き換えが中心のため、TDDサイクルではなく直接修正 → テスト確認のフローで進める
- 影響範囲を漏れなく洗い出し、一括で対応する

## 影響範囲

### コード（必須修正）
| ファイル | 箇所 | 内容 |
|---------|------|------|
| `src/shared/config.py:114` | デフォルト値 | `anthropic.claude-3-5-sonnet-20241022-v2:0` → `anthropic.claude-haiku-4-5-20251001-v1:0` |
| `template.yaml:39` | Lambda環境変数 | `anthropic.claude-3-5-sonnet-20240620-v1:0` → `anthropic.claude-haiku-4-5-20251001-v1:0` |
| `template.yaml:49` | IAMポリシーリソース | `anthropic.claude-3-5-sonnet*` → `anthropic.claude-haiku-4-5*` |

### テスト（必須修正）
| ファイル | 箇所 | 内容 |
|---------|------|------|
| `tests/unit/shared/test_config.py:23,41` | ローカルデフォルトテスト | モデルIDを Haiku 4.5 に更新 |
| `tests/unit/shared/test_config.py:196,224` | SSM dotenvテスト | モデルIDを Haiku 4.5 に更新 |
| `tests/unit/shared/test_config.py:245` | SSM必須パラメータ不足テスト | モデルIDを Haiku 4.5 に更新 |

### ドキュメント（任意・参考情報の更新）
| ファイル | 内容 |
|---------|------|
| `README.md:101` | Sonnet v2 単価の記述 |
| `docs/product-requirements.md:214` | LLM技術選定 |
| `docs/functional-design.md:74,164,726` | モデルID参照 |
| `docs/glossary.md:55,559,561,564` | Bedrock / LLM判定の用語定義 |
| `docs/architecture.md:18` | 既にHaiku 4.5記載済み（確認のみ） |

### 対象外（過去のステアリング・バックアップ）
- `.steering/20260214-*`, `.steering/20260215-*` — 過去の作業記録のため変更不要
- `.claude.backup/` — バックアップのため変更不要
- `test_bedrock_tokyo.py` — 手動テスト用スクリプトのため対象外

## タスクリスト

- [x] コード修正
  - [x] `src/shared/config.py:114` のデフォルト値を Haiku 4.5 に変更
  - [x] `template.yaml:39` のモデルIDを Haiku 4.5 に変更
  - [x] `template.yaml:49` の IAMリソース ARN パターンを Haiku 4.5 に変更
- [x] テスト修正
  - [x] `tests/unit/shared/test_config.py` 内の全 Sonnet 3.5 参照を Haiku 4.5 に更新
- [x] ドキュメント更新
  - [x] `README.md` のモデル記述を更新
  - [x] `docs/product-requirements.md` のLLM記述を更新
  - [x] `docs/functional-design.md` のモデルID参照を更新
  - [x] `docs/glossary.md` の用語定義を更新
- [x] 品質チェック
  - [x] `pytest tests/ -v` — 9 passed（カバレッジ閾値は全体設定のため既知）
  - [x] `ruff check src/` — All checks passed
  - [x] `ruff format src/` — 今回変更ファイルはフォーマット済み
  - [x] `mypy src/` — Success: no issues found in 46 source files
