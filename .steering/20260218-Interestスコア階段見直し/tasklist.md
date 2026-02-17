# タスクリスト: Interestスコア階段見直し

## タスク

- [x] 1. テストの期待値を新スコアに更新（RED: 4テスト失敗を確認）
- [x] 2. buzz_scorer.py のスコア階段を変更（GREEN: 全21テスト合格）
- [x] 3. 品質チェック（ruff: All checks passed, mypy: Success, pytest: 21 passed）

## 申し送り事項

- 今回の変更はBuzzスコアの**候補選定（Step 4: 上位150件）** に影響する。LLM判定（Step 5）やFinalSelector（Step 6）のロジックは変更なし
- 未定義トピックの記事は Total Buzz が約8.75pt低下する（Interest寄与: 12.5→3.75）
- 本番環境での配信結果を数回分観察し、想定通りの効果が出ているか確認を推奨
