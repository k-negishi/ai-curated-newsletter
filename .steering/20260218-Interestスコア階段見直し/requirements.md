# 要求: BuzzScorerのInterestスコア階段を見直す

## GitHub Issue

- https://github.com/k-negishi/ai-curated-newsletter/issues/38

## 背景

はてブ0件の記事が配信された原因調査で、`_calculate_interest_score` のスコア設計に問題を発見:
- デフォルト(50) = low_interest(50) で同スコア
- 未定義トピックが「低関心」と同格扱い

## 要求

C案（下位厳格型）でスコア階段を変更:

| レベル | 現状 | 変更後 |
|--------|------|--------|
| max_interest | 100 | 100 |
| high_interest | 85 | 80 |
| medium_interest | 70 | 55 |
| low_interest | 50 | 30 |
| default（未定義） | 50 | 15 |
| ignore_interest | 0 | 0 |
