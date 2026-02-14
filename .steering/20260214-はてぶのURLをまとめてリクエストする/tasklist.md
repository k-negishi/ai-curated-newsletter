# タスクリスト: はてぶのURLをまとめてリクエストする

## 実装タスク

- [x] SocialProofFetcher のバッチ取得テストを先に整備する
  - [x] RED: `/count/entries` 利用・50件分割・部分失敗継続のテストを追加し、失敗を確認する
  - [x] GREEN: 既存テストと整合する最小修正を入れてテストを通す
  - [x] REFACTOR: テストデータ生成とモック重複を整理する

- [x] SocialProofFetcher を `/count/entries` ベースへ実装変更する
  - [x] RED: 単発取得前提の既存実装で新テストが落ちることを確認する
  - [x] GREEN: 50件分割 + バッチ取得 + 結果統合を実装してテストを通す
  - [x] REFACTOR: バッチ分割処理とHTTP呼び出し処理を責務分離して可読性を上げる

- [x] エラーハンドリング・ログを仕様に合わせる
  - [x] RED: バッチ失敗時ログ/戻り値を検証するテストを追加する
  - [x] GREEN: 失敗バッチをスキップしつつ他バッチ結果を返す実装にする
  - [x] REFACTOR: ログキーとメッセージを統一し運用観測性を向上させる

- [x] 回帰確認を実施する
  - [x] RED: 関連テストが未実行/失敗状態であることを明示する
  - [x] GREEN: `tests/unit/services/test_social_proof_fetcher.py` と `tests/unit/services/test_buzz_scorer.py` をパスさせる
  - [x] REFACTOR: 必要ならテスト命名・共通fixtureを整理する

## 完了条件
- [x] `/count/entry` の単発呼び出しが SocialProofFetcher から除去されている
- [x] 50件超入力で複数バッチ取得が行われる
- [x] 既存の BuzzScorer 連携に影響がない（型・戻り値互換）
- [x] 関連ユニットテストがすべてパスする
- [x] lint/format/型チェックがすべて通る

## 申し送り
- 実装完了日: 2026-02-14
- 計画と実績の差分:
  - 差分なし。`SocialProofFetcher` を `/count/entries` + 50件分割へ置換し、既存公開インターフェース (`fetch_batch -> dict[str, int]`) を維持。
- 学んだこと:
  - 既存の `HatenaCountFetcher` と `SocialProofFetcher` で重複責務があるため、将来は共通化余地がある。
- 次回への改善提案:
  - `SocialProofFetcher` のエラーログにバッチ識別子（先頭URLまたはインデックス）を追加すると運用調査が容易になる。
