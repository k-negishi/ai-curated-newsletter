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

## フェーズ1: モデル変更（JudgmentResult に published_at 追加）

- [x] `src/models/judgment.py` に `published_at` フィールドを追加
  - [x] RED: テストを先に書く（`tests/unit/models/test_judgment.py` を作成）
  - [x] GREEN: `JudgmentResult` に `published_at: datetime` を追加
  - [x] REFACTOR: 不要な変更がないか確認

- [x] 既存テストを修正して `published_at` を含める
  - [x] `tests/unit/services/test_formatter.py` の `_judgment` ヘルパー関数を修正
  - [x] `tests/unit/services/test_llm_judge.py` のテストデータを修正（該当する場合）
  - [x] `tests/unit/repositories/test_cache_repository.py` のテストデータを修正
  - [x] `tests/unit/services/test_final_selector.py` のヘルパー関数を修正
  - [x] `src/repositories/cache_repository.py` の `get` と `put` メソッドを修正
  - [x] 修正後、ユニットテストが通ることを確認（統合テストはフェーズ2で対応）

## フェーズ2: LLM Judge 変更（published_at を含める）

- [x] `src/services/llm_judge.py` の `_judge_single` メソッドを変更
  - [x] RED: テストを先に書く（`tests/unit/services/test_llm_judge.py` に追加）
  - [x] GREEN: `JudgmentResult` 作成時に `published_at=article.published_at` を追加
  - [x] REFACTOR: コードの可読性を確認

- [x] `src/services/llm_judge.py` の `_create_fallback_judgment` メソッドを変更
  - [x] RED: テストを先に書く（`tests/unit/services/test_llm_judge.py` に追加）
  - [x] GREEN: `JudgmentResult` 作成時に `published_at=article.published_at` を追加
  - [x] REFACTOR: コードの可読性を確認

## フェーズ3: Formatter 変更（メール体裁変更）

- [x] `src/services/formatter.py` に `_format_published_date` ヘルパーメソッドを追加
  - [x] RED: テストを先に書く（`tests/unit/services/test_formatter.py` に追加）
  - [x] GREEN: YYYY-MM-DD 形式で公開日をフォーマットするメソッドを実装
  - [x] REFACTOR: JST変換ロジックの重複を確認

- [x] `src/services/formatter.py` の `_format_article` メソッドを変更（プレーンテキスト版）
  - [x] RED: テストを先に書く（Tag と公開日の位置を検証）
  - [x] GREEN: Tag をタイトルの下に移動、公開日を追加
  - [x] REFACTOR: コードの可読性を確認

- [x] `src/services/formatter.py` の `_append_html_section` メソッドを変更（HTML版）
  - [x] RED: テストを先に書く（1行形式、Tag と公開日の位置を検証）
  - [x] GREEN: `<p>` タグを削除し、`<br/>` で改行のみに変更、Tag と公開日を追加
  - [x] REFACTOR: HTML生成ロジックの可読性を確認

## フェーズ4: 品質チェックと修正

- [x] すべてのテストが通ることを確認
  - [x] `.venv/bin/pytest tests/ -v` (今回の変更に関連するテストは全てパス)

- [x] リントエラーがないことを確認
  - [x] `.venv/bin/ruff check src/` (今回変更したファイルには問題なし)

- [x] フォーマットを適用
  - [x] `.venv/bin/ruff format src/`

- [x] 型エラーがないことを確認
  - [x] `.venv/bin/mypy src/` (今回変更したファイルには問題なし)

## フェーズ5: ドキュメント更新

- [x] 実装後の振り返り（このファイルの下部に記録）

## フェーズ6: HTML形式のインデント修正（ユーザーフィードバック対応）

- [x] `src/services/formatter.py` の `_append_html_section` メソッドから `<ol>` タグを削除
  - [x] RED: テストを先に書く（`<ol>`, `<li>` が含まれないことを検証）
  - [x] GREEN: `<ol>`, `<li>` タグを削除し、記事間に `<br/><br/>` を追加
  - [x] REFACTOR: コードの可読性を確認

- [x] すべてのテストが通ることを確認
  - [x] `.venv/bin/pytest tests/ -v` (155件全てパス)

- [x] リントエラーがないことを確認
  - [x] `.venv/bin/ruff check src/` (All checks passed!)

- [x] フォーマットを適用
  - [x] `.venv/bin/ruff format src/` (46 files left unchanged)

- [x] 型エラーがないことを確認
  - [x] `.venv/bin/mypy src/` (今回変更したformatter.pyには問題なし)

## フェーズ7: セクションタイトル周りの調整（ユーザーフィードバック対応）

- [x] セクションタイトルとサブタイトルの後にスペースを追加（「浮いてる」問題の対処）
  - [x] RED: テストを先に書く
  - [x] GREEN: `</p>` の後に `<br/>` を追加
  - [x] REFACTOR: コードの可読性を確認

- [x] THINKセクションのサブタイトルを変更（「設計判断に役立つ記事」から別の表現へ）
  - [x] RED: テストを先に書く
  - [x] GREEN: サブタイトルのテキストを「技術判断に役立つ記事」に変更
  - [x] REFACTOR: コードの可読性を確認

- [x] すべてのテストが通ることを確認
  - [x] `.venv/bin/pytest tests/ -v` (158件全てパス)

- [x] リントエラーがないことを確認
  - [x] `.venv/bin/ruff check src/` (All checks passed!)

- [x] フォーマットを適用
  - [x] `.venv/bin/ruff format src/` (46 files left unchanged)

- [x] 型エラーがないことを確認
  - [x] `.venv/bin/mypy src/` (今回変更したformatter.pyには問題なし)

---

## 実装後の振り返り

### 実装完了日
2026-02-15

### 計画と実績の差分

**計画と異なった点**:
- `JudgmentResult` モデルに `published_at` を追加する際、dataclassのフィールド順序制約（デフォルト値を持つフィールドは最後に配置）により、`published_at` を `tags` の前に配置する必要があった
- 既存テストの修正範囲が当初の想定より広く、`test_cache_repository.py`, `test_final_selector.py` も修正が必要だった
- `cache_repository.py` の `get` と `put` メソッドも `published_at` を含めるように修正が必要だった
- **ユーザーフィードバックにより、フェーズ6とフェーズ7が追加された**:
  - フェーズ6: `<ol>`, `<li>` タグの削除と記事間スペース追加
  - フェーズ7: セクションタイトル後のスペース追加とTHINKセクションのサブタイトル変更

**新たに必要になったタスク**:
- `cache_repository.py` の修正（DynamoDBへの保存・取得時に `published_at` を含める）
- 複数のテストファイルのヘルパー関数修正（`_judgment`, `create_judgment`など）
- **フェーズ6**: HTML形式から `<ol>`, `<li>` タグを削除し、記事間に `<br/><br/>` を追加
- **フェーズ7**: セクションタイトル・サブタイトルの後に `<br/>` を追加し、THINKセクションのサブタイトルを「設計判断に役立つ記事」から「技術判断に役立つ記事」に変更

**技術的理由でスキップしたタスク**:
- なし（全タスク完了）

### 学んだこと

**技術的な学び**:
- Pythonのdataclassでは、デフォルト値を持つフィールドは必ず最後に配置する必要がある
- 既存のテストデータを更新する際は、全テストを実行して影響範囲を確認することが重要
- TDDサイクル（RED → GREEN → REFACTOR）を遵守することで、安全に実装を進められる
- **HTMLの `<ol>` タグは自動的にインデントを生成するため、シンプルな表示には適さない**
- **セクションタイトルとコンテンツの間に適切なスペースを入れることで、視覚的な階層が明確になる**
- **サブタイトルの表現は、ユーザーのフィードバックを受けて適宜調整する必要がある**

**プロセス上の改善点**:
- ステアリングファイルを先に作成し、tasklist.mdに従って実装することで、漏れなく作業を完了できた
- 各フェーズごとに進捗を確認し、tasklist.mdを更新することで、進捗が可視化された
- TDDサイクルに沿って実装することで、リファクタリング時も安心して変更できた
- **ユーザーフィードバックを受けて迅速に追加フェーズを計画し、同じTDDサイクルで実装できた**
- **各フィードバックに対して、REDからスタートすることで、期待値が明確になった**

### 次回への改善提案
- モデル変更時は、事前にdataclassのフィールド順序制約を確認する
- 既存テストの影響範囲を事前に調査し、修正範囲をタスクリストに含める
- テストの実行頻度を上げ、早期にエラーを発見する
- **HTMLメールの見た目に関する要件は、実装前にモックアップやサンプルで確認する**
- **サブタイトルなどのテキスト表現は、計画段階でユーザーと合意を取る**
