# 設計: はてぶのURLをまとめてリクエストする

## 設計方針
- 既存呼び出し経路（`BuzzScorer -> SocialProofFetcher`）を壊さず、`SocialProofFetcher` 内部実装のみを置換する。
- API呼び出し方式を単発 (`/count/entry`) からバッチ (`/count/entries`) に変更する。
- 1リクエストあたりURL上限50件を厳守するため、入力URLをチャンク分割する。

## 現状整理
- `src/services/social_proof_fetcher.py`
  - 現在は `_fetch_single(url)` で1URLずつ取得
  - `fetch_batch(urls)` は内部的にURLごと並列呼び出し
- `src/services/buzz_scorer.py`
  - `fetch_batch(urls)` の戻り値を `dict[str, int]` として利用
  - 件数閾値（1/10/50/100）でスコア計算

## 変更後アーキテクチャ
1. `fetch_batch(urls)` がURL配列を最大50件で分割
2. 各チャンクを `_fetch_single_batch(batch_urls)` で取得
3. `/count/entries?url=...&url=...` 形式でHTTP GET
4. レスポンスJSON（`{url: count}`）を統合
5. `dict[str, int]` を返却（既存互換）

## 主要インターフェース
- 変更なし:
  - `async fetch_batch(urls: list[str]) -> dict[str, int]`
- 追加/置換予定の内部メソッド:
  - `_split_batches(urls: list[str], batch_size: int = 50) -> list[list[str]]`
  - `_fetch_single_batch(urls: list[str]) -> dict[str, int]`

## エラーハンドリング
- バッチ単位で例外を捕捉し、失敗バッチは空結果として扱う。
- 他バッチの成功結果は保持して返却する。
- JSON値が `int` 変換不可の場合は当該URLを0件扱いまたはスキップし、ログを出す。

## ログ設計
- 開始ログ: URL総数、バッチ数
- バッチ成功ログ: バッチサイズ、取得件数
- バッチ失敗ログ: エラー内容、対象件数
- 完了ログ: 総URL数、成功URL数、失敗バッチ数

## テスト設計
- `tests/unit/services/test_social_proof_fetcher.py` を中心に更新
- 追加/更新観点:
  1. 50件以下で1回のバッチ取得になる
  2. 51件以上で複数バッチに分割される
  3. 一部バッチ失敗時に他バッチ結果を返す
  4. 空配列入力で空辞書を返す
  5. API URLが `/count/entries` で生成される

## TDDサイクル
1. **RED**: 失敗するテストを先に書く
2. **GREEN**: 最小限の実装でテストをパスさせる
3. **REFACTOR**: コード品質を向上させる

## リスクと対策
- リスク: URLエンコード不備でAPIが正しく解釈できない
  - 対策: `urllib.parse.urlencode` の `doseq` 相当の扱いをテストで固定
- リスク: バッチ失敗時に戻り値欠損が増える
  - 対策: 失敗時ログを明確化し、部分成功を返す既存方針を維持

