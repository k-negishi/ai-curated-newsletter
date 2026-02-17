# LLM コスト削減 タスクリスト

## GitHub Issue
https://github.com/k-negishi/ai-curated-newsletter/issues/36

## 概要
事前フィルタリング強化とプロンプト最適化により、LLM コストを削減する。

## 実装方針
- Kent Beck の TDD (Test-Driven Development) で実装する
- RED → GREEN → REFACTOR のサイクルを遵守

## 影響範囲

### 調査が必要なファイル
| ファイル | 調査内容 |
|---------|---------|
| `src/services/llm_judge.py` | 現在のプロンプト内容・トークン数 |
| `src/orchestrator/newsletter_orchestrator.py` | 現在の処理フロー（フィルタ挿入ポイント） |
| `config/sources.yaml` | 現在のソース設定構造 |

### 変更予定ファイル
| ファイル | 変更内容 |
|---------|---------|
| `src/services/llm_judge.py` | プロンプト最適化 |
| `src/services/` (新規 or 既存拡張) | 事前フィルタリング |
| `src/orchestrator/newsletter_orchestrator.py` | フィルタ統合 |
| `config/sources.yaml` | フィルタ設定追加 |
| `docs/architecture.md` | コスト推定更新 |

## タスクリスト

### Phase 1: 現状分析と計測
- [ ] 現在のプロンプトのトークン数を計測する
  - [ ] `src/services/llm_judge.py` のプロンプトを確認
  - [ ] 平均入力トークン数・出力トークン数の実測値を確認
- [ ] 現在の事前フィルタリングの有無を確認する
  - [ ] `src/orchestrator/newsletter_orchestrator.py` のフロー確認
  - [ ] RSS収集 → LLM判定 の間にフィルタがあるか確認

### Phase 2: プロンプト最適化
- [ ] プロンプトを最適化する
  - [ ] RED: 最適化後のトークン数が削減されることのテスト
  - [ ] GREEN: プロンプトの不要な指示・コンテキストを削減
  - [ ] REFACTOR: 判定品質が維持されていることを確認
- [ ] lint/format/型チェックがすべて通る

### Phase 3: 事前フィルタリング
- [ ] 事前フィルタリング機能を実装する
  - [ ] RED: フィルタリングのテスト（除外キーワードに一致する記事が除外される）
  - [ ] GREEN: フィルタリングロジックを実装
  - [ ] REFACTOR: コード改善
- [ ] オーケストレーターにフィルタを統合する
  - [ ] RED: 統合テスト
  - [ ] GREEN: フロー内にフィルタを組み込む
  - [ ] REFACTOR: 不要な処理の整理
- [ ] lint/format/型チェックがすべて通る

### Phase 4: ドキュメント・計測
- [ ] コスト削減効果を定量化する
  - [ ] 変更前後のコスト推定を比較
  - [ ] `docs/architecture.md` のコスト推定を更新
- [ ] 品質チェック
  - [ ] `pytest tests/ -v` — 全テストパス
  - [ ] `ruff check src/` — All checks passed
  - [ ] `ruff format src/` — フォーマット確認
  - [ ] `mypy src/` — Success: no issues found
