# 要求内容

## 概要

LLMからbuzz_label判定を廃止し、既存のBuzzScore（非LLM計算）の`total_score`から閾値でBuzzLabelを導出するように変更する。

## 背景

現在、記事の「話題性（Buzz）」に関してBuzz Score（非LLM定量計算）とBuzz Label（LLM定性判定）の2つが共存している。しかし：

1. **LLMは実際の話題性を知らない** — はてブ数、複数ソース出現回数などの実データをプロンプトに渡していない
2. **すでに非LLMで定量計算している** — Buzz Scoreが客観的な実データに基づいて計算済み
3. **LLMの得意領域ではない** — LLMが得意なのは「内容理解」「要約」「関心度判定」であり、「業界でどれだけ話題か」は外部シグナルの問題

## 実装対象の機能

### 1. LLMプロンプトからbuzz_label判定を削除
- プロンプトからbuzz_labelの指示・出力形式を削除
- `_parse_response()`から`buzz_label`の必須フィールド検証を削除
- LLMの責務を「内容理解」に集中させる（Interest Label, Summary, Tags）

### 2. BuzzScore → BuzzLabel 変換ロジックの追加
- `BuzzScore.total_score`から`BuzzLabel`への閾値変換関数を追加
- 閾値: HIGH ≥ 70, MID ≥ 40, LOW < 40

### 3. JudgmentResultへのbuzz_label設定方法の変更
- LLMからではなく、BuzzScoreから導出したBuzzLabelを設定
- OrchestratorでBuzzScoreの辞書をLlmJudge（またはその後のステップ）に渡す

### 4. FinalSelectorのソートキー改善
- buzz_label（3段階）ではなく、buzz_score.total_score（連続値）でソート
- より精度の高い優先順位付けを実現

## 受け入れ条件

### LLMプロンプト変更
- [ ] プロンプトにbuzz_labelの指示が含まれないこと
- [ ] LLM出力JSONにbuzz_labelフィールドが不要になること
- [ ] `_parse_response()`でbuzz_labelを必須フィールドとしてチェックしないこと

### BuzzScore → BuzzLabel変換
- [ ] total_score >= 70 → BuzzLabel.HIGH
- [ ] 40 <= total_score < 70 → BuzzLabel.MID
- [ ] total_score < 40 → BuzzLabel.LOW
- [ ] 変換関数のユニットテストがあること

### FinalSelector
- [ ] buzz_score.total_score（連続値）でソートされること
- [ ] 既存テストが更新されパスすること

### メール表示
- [ ] メール本文にBuzz: HIGH/MID/LOWが引き続き表示されること（変更なし）

### DynamoDBキャッシュ
- [ ] 新規保存時にbuzz_labelが引き続き保存されること
- [ ] 既存キャッシュデータの読み込みに影響がないこと

### 品質チェック
- [ ] pytest全テストパス
- [ ] ruff check: All checks passed!
- [ ] mypy: Success: no issues found

## 成功指標

- LLMプロンプトのトークン数が削減されること
- 話題性判定が客観データ（BuzzScore）に基づくものになること

## スコープ外

以下はこのフェーズでは実装しません:

- BuzzScore計算アルゴリズムの変更（既存ロジックをそのまま使用）
- 閾値のチューニング（仮値で実装、運用データで後日調整）
- BuzzLabel enum自体の削除（メール表示・最終選定で引き続き使用）

## 参照ドキュメント

- `docs/functional-design.md` - 機能設計書（LLM判定仕様、BuzzScore仕様）
- `docs/glossary.md` - 用語集（Buzz Label、Buzzスコアの定義）
- `docs/architecture.md` - 技術仕様書（データフロー）
- GitHub Issue #39
