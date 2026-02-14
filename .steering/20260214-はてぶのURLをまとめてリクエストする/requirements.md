# 要求定義: はてぶのURLをまとめてリクエストする

## GitHub Issue
https://github.com/k-negishi/ai-curated-newsletter/issues/18

## issue 内容
- タイトル: はてぶのURLはまとめてリクエスト
- 本文:
  - はてなAPIは `/count/entries` で複数 `url` をまとめてリクエストできる
  - 1リクエストあたりの `url` 指定は最大50件
  - 現状の `/count/entry?url=...` の単発連打はNG
- ラベル: なし

## 背景と課題
- 現行実装の実行経路では、`SocialProofFetcher` が `/count/entry?url=...` をURLごとに呼び出している。
- `handler -> BuzzScorer -> SocialProofFetcher` の経路で実際に利用されるため、URL件数が多いほどHTTPリクエスト数が線形増加する。
- はてなAPIの仕様に沿った効率的なバッチ取得に置き換える必要がある。

## スコープ
- 対象:
  - `src/services/social_proof_fetcher.py` のHatena取得ロジックを `/count/entries` ベースに変更
  - 最大50件で分割し、複数バッチを処理する
  - 既存の `BuzzScorer` とのインターフェース（URL -> はてブ件数 `int`）は維持
  - 関連ユニットテストの更新・追加
- 非対象:
  - SocialProofのスコアリングロジック変更
  - `MultiSourceSocialProofFetcher` / `HatenaCountFetcher` 側の仕様変更
  - 他ソース（Zenn/Qiita/yamadashy）のロジック変更

## 機能要件
1. Hatena API呼び出しは `/count/entries` を使用する。
2. クエリは `url` パラメータを複数指定する。
3. 50件を超えるURL入力時は、50件単位で分割して処理する。
4. バッチ取得失敗時も他バッチ処理は継続する。
5. `fetch_batch()` の戻り値は従来どおり `dict[str, int]` を返す。

## 非機能要件
1. 既存の公開メソッドシグネチャ互換性を維持する。
2. ログでバッチ分割数・失敗件数を追跡できる。
3. テストで以下をカバーする:
  - 50件以下の正常系
  - 51件以上の分割処理
  - 部分失敗時の継続性
  - 空入力時の挙動

## 受け入れ条件
- [ ] `SocialProofFetcher` が `/count/entries` を利用している。
- [ ] 入力URLが79件の場合、API呼び出しが2回（50 + 29）になる。
- [ ] API失敗時に全体がクラッシュせず、取得できたURL分のみ結果を返す。
- [ ] `tests/unit/services/test_social_proof_fetcher.py` が新仕様でパスする。

## 実装方針
- Kent Beck の TDD (Test-Driven Development) で実装する
- RED -> GREEN -> REFACTOR のサイクルを遵守
- テストを先に書き、最小限の実装でパスさせ、その後リファクタリング

