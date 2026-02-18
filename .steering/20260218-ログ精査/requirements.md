# 要件定義: ログ精査

## GitHub Issue
https://github.com/k-negishi/ai-curated-newsletter/issues/45

## issue 内容
- タイトル: ログ精査
- 本文:
  - CWlogs にログが出すぎないようにしたい。本番はWarn以上から。
  - ローカルはdebugもだす。.envを.env.localと分ける。

## ユーザーとの対話で明確化された追加要件
1. 本番の LOG_LEVEL は INFO（当初のWARNINGから変更）
2. 現在の INFO ログ（66箇所）の大半を DEBUG に降格し、本番のログノイズを削減
3. 外部連携系（Bedrock, SES, RSS, はてブAPI等）のログは INFO 維持（本番で可視化）
4. LLM の実際のトークン数（input/output tokens）をログに出力
5. .env と .env.local の分離

## 実装方針
- Kent Beck の TDD (Test-Driven Development) で実装する
- RED → GREEN → REFACTOR のサイクルを遵守
- テストを先に書き、最小限の実装でパスさせ、その後リファクタリング

## 現状分析

### ログ統計
| レベル | 箇所数 |
|--------|--------|
| debug | 31 |
| info | 66 |
| warning | 14 |
| error | 25 |
| **合計** | **136** |

### 設定ファイル
- `.env`: ローカル開発用（LOG_LEVEL=INFO）
- `.env.example`: テンプレート（LOG_LEVEL=DEBUG）
- `.env.local`: 存在しない
- 本番: SSM Parameter Store から読み込み

### ログレベル方針（確定）
| 環境 | LOG_LEVEL | 目的 |
|------|-----------|------|
| ローカル | DEBUG | 開発時の全ログ出力 |
| 本番 | INFO | 運用に必要なログのみ出力 |
