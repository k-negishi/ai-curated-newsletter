# 要求内容

## 概要

GitHub Issue #5: メール文面の調整

メール通知の本文フォーマットをPRDに定義されている形式に合わせる。現在の実装では記事のURL、話題性、信頼度、判定理由のみが表示されているが、PRDの例では記事のタイトル、URL、Buzz、概要が表示されている。

## 背景

現在のメール文面には以下の情報が不足している:
- 記事のタイトル
- 記事の概要(description)

PRDのメールフォーマット例(docs/product-requirements.md 245-280行目)には、タイトルとURLと概要が含まれている。Issue #5のコメントにも同様の形式が示されており、ユーザーがメールを見ただけで記事の内容を把握できるようにする必要がある。

## 実装対象の機能

### 1. メール文面フォーマットの改善

- 記事のタイトルを表示する
- 記事の概要(description)を表示する
- PRDのメールフォーマット例に準拠した形式にする

**PRDのメールフォーマット例**:
```
1. [タイトル]
   URL: https://...
   Buzz: HIGH
   概要: PostgreSQLのインデックス戦略について実践的な知見
```

**現在の実装**:
```
[1] https://...
話題性: HIGH
信頼度: 0.85
理由: PostgreSQLのインデックス戦略について実践的な知見
```

### 2. データモデルの拡張

- `JudgmentResult`に`title`と`description`フィールドを追加
- `LlmJudge`でArticle情報を保持するように変更
- `CacheRepository`のスキーマに合わせる(既にtitleとsource_nameが含まれている)

## 受け入れ条件

### メール文面フォーマット
- [ ] 記事のタイトルが表示される
- [ ] 記事のURLが表示される
- [ ] 記事のBuzz Label(HIGH/MID/LOW)が表示される
- [ ] 記事の概要が表示される
- [ ] PRDのメールフォーマット例と同じ形式になっている

### データモデル
- [ ] `JudgmentResult`に`title`フィールドがある
- [ ] `JudgmentResult`に`description`フィールドがある
- [ ] `LlmJudge`が`Article`情報を`JudgmentResult`に設定している
- [ ] `CacheRepository`が新しいフィールドを保存・取得できる

### 既存機能への影響
- [ ] Orchestratorが正常に動作する
- [ ] FinalSelectorが正常に動作する
- [ ] 既存のテストが通る(または適切に修正される)

## 成功指標

- メール通知を見たユーザーが、記事のタイトルと概要から内容を把握できる
- PRDで定義されたメールフォーマットに準拠している
- 既存機能に影響を与えない

## スコープ外

以下はこのフェーズでは実装しません:

- キーワードフィールドの追加(PRDの例には含まれているが、現状のArticleモデルにはない)
- HTMLメール形式への変更(プレーンテキスト形式を維持)
- メール件名の変更
- メールの送信ロジックの変更

## 参照ドキュメント

- `docs/product-requirements.md` - プロダクト要求定義書(245-280行目: メールフォーマット例)
- `docs/functional-design.md` - 機能設計書(CacheRepositoryスキーマ: 891-906行目)
- `docs/architecture.md` - アーキテクチャ設計書
- GitHub Issue #5: https://github.com/k-negishi/ai-curated-newsletter/issues/5
