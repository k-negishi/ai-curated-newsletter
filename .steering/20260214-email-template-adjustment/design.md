# 設計書

## アーキテクチャ概要

メール文面フォーマットの改善のため、以下のコンポーネントを変更します:

```
Article (既存)
  ↓
LlmJudge (変更: ArticleのtitleとdescriptionをJudgmentResultに追加)
  ↓
JudgmentResult (変更: titleとdescriptionフィールドを追加)
  ↓
CacheRepository (変更: 新しいフィールドを保存・取得)
  ↓
FinalSelector (影響なし: JudgmentResultのリストを処理)
  ↓
Formatter (変更: titleとdescriptionを表示)
  ↓
Notifier (影響なし: フォーマット済みテキストを送信)
```

## コンポーネント設計

### 1. JudgmentResult (src/models/judgment.py)

**変更内容**:
- `title: str` フィールドを追加
- `description: str` フィールドを追加

**実装の要点**:
- Articleの`title`と`description`をそのまま保持
- descriptionは最大800文字(Articleの制約を継承)
- 既存のフィールド(url, interest_label, buzz_label, confidence, reason, model_id, judged_at)は変更なし

**変更後のモデル**:
```python
@dataclass
class JudgmentResult:
    """LLM判定結果.

    Attributes:
        url: 記事URL(キャッシュキー)
        title: 記事タイトル
        description: 記事の概要(最大800文字)
        interest_label: 関心度ラベル
        buzz_label: 話題性ラベル
        confidence: 信頼度(0.0-1.0)
        reason: 判定理由(最大200文字)
        model_id: 使用したLLMモデルID
        judged_at: 判定日時(UTC)
    """

    url: str
    title: str
    description: str
    interest_label: InterestLabel
    buzz_label: BuzzLabel
    confidence: float
    reason: str
    model_id: str
    judged_at: datetime
```

### 2. LlmJudge (src/services/llm_judge.py)

**変更内容**:
- `judge`メソッドで`JudgmentResult`を生成する際に、`Article`の`title`と`description`を設定

**実装の要点**:
- 既存のLLM判定ロジックは変更しない
- JudgmentResult生成時に、Articleから`title`と`description`をコピー
- LLM APIへのリクエストやレスポンス処理は変更なし

### 3. CacheRepository (src/repositories/cache_repository.py)

**変更内容**:
- `put`メソッドで`title`と`description`をDynamoDBに保存
- `get`メソッドで`title`と`description`をDynamoDBから取得

**実装の要点**:
- DynamoDBのAttributesに`title`と`description`を追加
- 既存のキャッシュデータとの互換性を考慮(getメソッドで欠損値を処理)
- Functional Designのスキーマ(891-906行目)では既に`title`と`source_name`が含まれている

**DynamoDBスキーマ**:
```python
{
  "PK": "URL#<sha256(url)>",
  "SK": "JUDGMENT#v1",
  "url": "https://example.com/article",
  "title": "Article Title",  # 追加
  "description": "Article description...",  # 追加
  "interest_label": "ACT_NOW",
  "buzz_label": "HIGH",
  "confidence": 0.85,
  "reason": "...",
  "model_id": "...",
  "judged_at": "2025-01-15T10:30:00Z"
}
```

### 4. Formatter (src/services/formatter.py)

**変更内容**:
- `_format_article`メソッドで、`title`、`URL`、`Buzz`、`概要`を表示
- PRDのメールフォーマット例に準拠

**実装の要点**:
- 信頼度(confidence)と理由(reason)の表示は削除
- PRDの形式: `[番号] タイトル`, `URL: ...`, `Buzz: HIGH`, `概要: ...`
- 既存のセクション分け(ACT_NOW, THINK, FYI)は維持

**変更後のフォーマット例**:
```
[1] PostgreSQL Index Strategies
URL: https://example.com/article
Buzz: HIGH
概要: PostgreSQLのインデックス戦略について実践的な知見
```

## データフロー

### メール通知生成フロー
```
1. LlmJudge: Article → LLM判定 → JudgmentResult(title, descriptionを含む)を生成
2. CacheRepository: JudgmentResult(title, descriptionを含む)をDynamoDBに保存
3. FinalSelector: JudgmentResultのリストを選定(変更なし)
4. Formatter: JudgmentResult(title, descriptionを含む)をメール本文にフォーマット
5. Notifier: メール送信(変更なし)
```

## エラーハンドリング戦略

### 既存データとの互換性

**問題**: 既存のDynamoDBキャッシュには`title`と`description`が含まれていない可能性がある

**対処法**:
- `CacheRepository.get`メソッドで、`title`と`description`が存在しない場合はデフォルト値を設定
  - `title`: "No Title"
  - `description`: ""
- これにより、既存キャッシュの読み込みでエラーが発生しない

## テスト戦略

### ユニットテスト

**src/services/formatter.py**:
- `test_format_article_with_title_and_description`: タイトルと概要が正しく表示されることを確認
- `test_format_email_body`: PRDのフォーマットに準拠していることを確認

**src/repositories/cache_repository.py**:
- `test_put_judgment_with_title_and_description`: titleとdescriptionが保存されることを確認
- `test_get_judgment_with_missing_fields`: 欠損値が適切に処理されることを確認

### 統合テスト

**src/orchestrator/orchestrator.py**:
- E2Eテストでメール本文が正しくフォーマットされることを確認

## 依存ライブラリ

新しいライブラリの追加は不要です。

## ディレクトリ構造

変更されるファイル:
```
src/
├── models/
│   └── judgment.py (変更: titleとdescriptionフィールドを追加)
├── services/
│   ├── llm_judge.py (変更: ArticleのtitleとdescriptionをJudgmentResultに設定)
│   └── formatter.py (変更: titleとdescriptionを表示)
└── repositories/
    └── cache_repository.py (変更: titleとdescriptionを保存・取得)

tests/
├── unit/
│   ├── services/
│   │   └── test_formatter.py (変更: 新しいフォーマットのテスト)
│   └── repositories/
│       └── test_cache_repository.py (変更: 新しいフィールドのテスト)
└── integration/
    └── test_orchestrator.py (変更: E2Eテスト)
```

## 実装の順序

1. **JudgmentResultモデルの変更**: `title`と`description`フィールドを追加
2. **LlmJudgeの変更**: ArticleのtitleとdescriptionをJudgmentResultに設定
3. **CacheRepositoryの変更**: titleとdescriptionを保存・取得
4. **Formatterの変更**: PRDのフォーマットに準拠
5. **テストの更新**: 変更したコンポーネントのテストを更新
6. **E2Eテスト実行**: 全体フローの動作確認

## セキュリティ考慮事項

- titleとdescriptionは外部ソース(RSS/Atom)から取得されるため、XSS対策は不要(プレーンテキストメール)
- DynamoDBへの保存時に文字数制限を超えないように、Articleの制約(title: 最大500文字、description: 最大800文字)を維持

## パフォーマンス考慮事項

- JudgmentResultのサイズが増加するが、影響は軽微(title: 平均100文字、description: 平均400文字)
- DynamoDBの読み書きコストへの影響は無視できる範囲

## 将来の拡張性

- キーワードフィールドの追加: Articleモデルにkeywordsフィールドを追加すれば、同様の方法でJudgmentResultに含められる
- HTMLメール形式: FormatterでHTMLテンプレートを使用し、Notifierでマルチパート形式で送信
