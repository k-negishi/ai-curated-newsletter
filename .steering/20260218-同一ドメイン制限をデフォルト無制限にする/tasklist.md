# 同一ドメイン制限をデフォルト無制限にする タスクリスト

## GitHub Issue
https://github.com/k-negishi/ai-curated-newsletter/issues/37

## 概要
`FINAL_SELECT_MAX_PER_DOMAIN` のデフォルト値を「制限なし (0)」に変更し、環境変数で指定があればその値に従うようにする。

## 実装方針
- Kent Beck の TDD (Test-Driven Development) で実装する
- RED → GREEN → REFACTOR のサイクルを遵守

## 設計判断
- `max_per_domain = 0` を「制限なし」として扱う（0件制限ではない）
- ドメイン制限を有効にしたい場合は、環境変数 `FINAL_SELECT_MAX_PER_DOMAIN` に正の整数を設定する
- SSM Parameter Store の必須パラメータリストからは外さない（本番環境では明示的に設定させる）

## 影響範囲

### コード
| ファイル | 箇所 | 変更内容 |
|---------|------|---------|
| `src/services/final_selector.py:35` | `__init__` デフォルト値 | `max_per_domain=4` → `max_per_domain=0` |
| `src/services/final_selector.py:151` | ドメイン制限チェック | `max_per_domain == 0` の場合はスキップする条件を追加 |
| `src/shared/config.py:125` | ローカル設定デフォルト値 | `"4"` → `"0"` |

### テスト
| ファイル | 変更内容 |
|---------|---------|
| `tests/unit/services/test_final_selector.py:17` | fixtureの `max_per_domain` をテストケースに応じて調整 |
| `tests/unit/services/test_final_selector.py:89-102` | `test_respects_max_per_domain` のテストを更新 |
| `tests/unit/services/test_final_selector.py:104-133` | `test_handles_multiple_domains` のテストを更新 |
| `tests/unit/services/test_final_selector.py` (新規) | `max_per_domain=0` で制限なしの動作テスト追加 |
| `tests/unit/shared/test_config.py:27,46` | デフォルト値テストを `0` に更新 |

### 設定ファイル
| ファイル | 変更内容 |
|---------|---------|
| `.env.example:32` | デフォルト値とコメントを更新 |

### ドキュメント
| ファイル | 変更内容 |
|---------|---------|
| `docs/architecture.md:288` | `FINAL_SELECT_MAX_PER_DOMAIN` の説明更新 |
| `docs/functional-design.md:789,1353` | デフォルト値の記述更新 |
| `README.md:64` | `max_per_domain 4` の記述更新 |

## タスクリスト

- [x] `FinalSelector` のドメイン制限ロジックを修正する
  - [x] RED: `max_per_domain=0` で全記事が選定されるテストを書く
  - [x] GREEN: `_select_with_domain_control` で `max_per_domain == 0` の場合にドメイン制限をスキップする実装
  - [x] REFACTOR: 条件分岐を明確にする（1行の条件追加で十分シンプル）
- [x] `FinalSelector` のデフォルト値を変更する
  - [x] RED: デフォルトコンストラクタで制限なしになるテストを書く
  - [x] GREEN: `__init__` のデフォルト値を `max_per_domain=0` に変更
  - [x] REFACTOR: docstringを更新
- [x] 既存テストを更新する
  - [x] `test_respects_max_per_domain` — fixture で `max_per_domain=4` を明示指定済みのため変更不要
  - [x] `test_handles_multiple_domains` — fixture で `max_per_domain=4` を明示指定済みのため変更不要
  - [x] fixture の `FinalSelector(max_articles=15, max_per_domain=4)` はそのまま維持（明示的に指定済み）
- [x] 設定のデフォルト値を変更する
  - [x] `src/shared/config.py:125` のデフォルト値を `"0"` に変更
  - [x] `tests/unit/shared/test_config.py` のデフォルト値テストを更新
  - [x] `.env.example:32` の値とコメントを更新
- [x] ドキュメントを更新する
  - [x] `docs/architecture.md` の `FINAL_SELECT_MAX_PER_DOMAIN` 説明を更新
  - [x] `docs/functional-design.md` のデフォルト値記述を更新
  - [x] `README.md` の `max_per_domain` 記述を更新
- [x] 品質チェック
  - [x] `pytest tests/ -v` — 209 passed（integration 3件は外部サービス依存で既知）
  - [x] `ruff check src/` — All checks passed
  - [x] `ruff format src/` — フォーマット確認済み
  - [x] `mypy src/` — Success: no issues found in 46 source files
