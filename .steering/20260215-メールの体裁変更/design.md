# 設計書

## アーキテクチャ概要

既存のアーキテクチャを変更せず、以下のコンポーネントのみを修正:
- `src/models/judgment.py` - データモデル変更
- `src/services/llm_judge.py` - データ生成ロジック変更
- `src/services/formatter.py` - メール本文フォーマット変更

## コンポーネント設計

### 1. JudgmentResult モデル

**責務**:
- LLM判定結果のデータ構造を定義
- 記事の公開日を保持

**変更内容**:
```python
@dataclass
class JudgmentResult:
    url: str
    title: str
    description: str
    interest_label: InterestLabel
    buzz_label: BuzzLabel
    confidence: float
    reason: str
    model_id: str
    judged_at: datetime
    tags: list[str] = field(default_factory=list)
    published_at: datetime  # 追加: 記事の公開日時
```

**実装の要点**:
- `published_at` は `Article.published_at` を引き継ぐ
- 既存のコードとの後方互換性を保つため、デフォルト値は設定しない（必須フィールド）
- テストデータでは `datetime(2026, 2, 13, 12, 0, 0, tzinfo=timezone.utc)` などを使用

### 2. LlmJudge サービス

**責務**:
- LLM判定を実行し、`JudgmentResult` を生成
- 記事の公開日を `JudgmentResult` に含める

**変更内容**:
```python
# _judge_single メソッド内
judgment = JudgmentResult(
    url=article.url,
    title=article.title,
    description=article.description,
    interest_label=InterestLabel(judgment_data["interest_label"]),
    buzz_label=BuzzLabel(judgment_data["buzz_label"]),
    confidence=float(judgment_data["confidence"]),
    reason=judgment_data["reason"][:200],
    model_id=self._model_id,
    judged_at=now_utc(),
    tags=self._extract_tags(judgment_data),
    published_at=article.published_at,  # 追加
)

# _create_fallback_judgment メソッド内も同様に追加
```

**実装の要点**:
- `article.published_at` をそのまま引き継ぐ
- フォールバック判定（失敗時）でも `published_at` を含める

### 3. Formatter サービス

**責務**:
- メール本文（HTML版・プレーンテキスト版）を生成
- 1行形式のシンプルなレイアウトで可読性を向上

**変更内容（HTML版）**:

現在の構造:
```html
<li>
  <p>[{index}] {safe_title}</p>
  <p>URL: <a href="{safe_url}">{safe_url}</a></p>
  <p>Buzz: {article.buzz_label.value}</p>
  <p>概要: {safe_description}</p>
  <p>Tag: {safe_tag_text}</p>
</li>
```

変更後の構造:
```html
<li>
  [{index}] {safe_title}<br/>
  Tag: {safe_tag_text}<br/>
  公開日: {published_date}<br/>
  URL: <a href="{safe_url}">{safe_url}</a><br/>
  Buzz: {article.buzz_label.value}<br/>
  概要: {safe_description}
</li>
```

**変更内容（プレーンテキスト版）**:

現在の構造:
```
[{index}] {article.title}
URL: {article.url}
Buzz: {article.buzz_label.value}
概要: {article.description}
Tag: {self._format_tags(article.tags)}
```

変更後の構造:
```
[{index}] {article.title}
Tag: {self._format_tags(article.tags)}
公開日: {published_date}
URL: {article.url}
Buzz: {article.buzz_label.value}
概要: {article.description}
```

**実装の要点**:
- `<p>` タグを削除し、`<br/>` タグで改行のみ
- Tag をタイトルの直後に移動
- 公開日は YYYY-MM-DD 形式（`published_at.strftime('%Y-%m-%d')`）
- JST変換は既存の `_to_jst()` メソッドを使用

## データフロー

### メール本文生成フロー

```
1. Orchestrator が FinalSelector から選定された記事リストを受け取る
2. Formatter.format() または Formatter.format_html() を呼び出す
3. 各記事の published_at を JST に変換
4. YYYY-MM-DD 形式にフォーマット
5. メール本文を生成
6. Notifier に渡す
```

## TDDサイクル

### 各タスクでの実装手順

#### RED: テストを先に書く
1. 期待する振る舞いを明確にする
2. 失敗するテストケースを作成
3. テストを実行して失敗を確認

#### GREEN: 最小限の実装でテストをパスさせる
1. テストをパスさせる最小限のコードを書く
2. テストを実行して成功を確認
3. まだリファクタリングはしない

#### REFACTOR: コード品質を向上させる
1. 重複を排除
2. 命名を改善
3. 構造を整理
4. テストを実行して成功を確認（リファクタリング後も動作すること）

## テスト戦略

### ユニットテスト

#### `test_judgment.py` (新規作成または既存に追加)
- `JudgmentResult` に `published_at` が含まれることを検証

#### `test_llm_judge.py` (既存に追加)
- `_judge_single` で `published_at` が正しく設定されることを検証
- フォールバック判定で `published_at` が正しく設定されることを検証

#### `test_formatter.py` (既存に追加)
- HTML版で Tag がタイトルの下に表示されることを検証
- HTML版で公開日が YYYY-MM-DD 形式で表示されることを検証
- HTML版で `<p>` タグが使われていないことを検証
- プレーンテキスト版で Tag と公開日が正しい位置に表示されることを検証

### 統合テスト

- `test_notification_flow.py` (既存) が引き続き動作することを確認

## 依存ライブラリ

既存のライブラリのみ使用（新規追加なし）

## 実装の順序

### フェーズ1: モデル変更
1. `JudgmentResult` に `published_at` フィールド追加
2. テストデータを更新して既存テストを修正

### フェーズ2: LLM Judge 変更
1. `_judge_single` メソッドで `published_at` を含める
2. `_create_fallback_judgment` メソッドで `published_at` を含める
3. テストケースを追加

### フェーズ3: Formatter 変更
1. `_append_html_section` メソッドで1行形式に変更
2. `_format_article` メソッドで Tag と公開日を追加
3. `_format_published_date` ヘルパーメソッドを追加（YYYY-MM-DD形式）
4. テストケースを追加・更新

### フェーズ4: 品質チェック
1. pytest でテスト実行
2. ruff でリントチェック
3. mypy で型チェック

### フェーズ5: ドキュメント更新
1. tasklist.md の振り返りを記録

## セキュリティ考慮事項

- HTML出力時のエスケープ処理は既存の `_escape_non_url_html_text` を継続使用
- 公開日の表示は既にUTCからJSTに変換されているため、タイムゾーン処理は既存ロジックを使用

## パフォーマンス考慮事項

- 公開日のフォーマット処理は軽量（`strftime`のみ）
- 既存のパフォーマンスに影響なし

## 将来の拡張性

- 公開日の表示形式を設定ファイルで変更可能にする（将来的に）
- HTML版にCSSスタイルを追加する（将来的に）
