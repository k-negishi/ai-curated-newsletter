# 設計: Interestスコア階段見直し

## 変更対象

1. `src/services/buzz_scorer.py` - `_calculate_interest_score` メソッドのスコア値とデフォルト値
2. `tests/unit/services/test_buzz_scorer.py` - 期待値の更新

## 変更内容

### buzz_scorer.py

`topic_levels` のスコアマッピングを変更:
- (max_interest, 100.0) → 変更なし
- (high_interest, 85.0) → 80.0
- (medium_interest, 70.0) → 55.0
- (low_interest, 50.0) → 30.0
- (ignore_interest, 0.0) → 変更なし
- デフォルト return 50.0 → 15.0

### test_buzz_scorer.py

期待値を更新:
- test_calculate_interest_score_high: 85.0 → 80.0
- test_calculate_interest_score_medium: 70.0 → 55.0
- test_calculate_interest_score_low: 50.0 → 30.0
- test_calculate_interest_score_default: 50.0 → 15.0
- test_calculate_total_score: interest=80のまま、結果は変わらない（スコア値のテストではない）
