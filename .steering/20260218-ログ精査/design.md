# 設計: ログ精査

## 設計方針

### 1. .env / .env.local 分離

**現状**: `.env` 1ファイルでローカル設定を管理
**変更後**: `.env`（共通/本番デフォルト）+ `.env.local`（ローカル上書き）

```
.env          → 共通設定・本番デフォルト（gitignore済み）
.env.local    → ローカル開発固有の設定（gitignore済み）
.env.example  → テンプレート（git管理）
```

**config.py の変更**:
- ローカル環境: `.env` を読み込み後、`.env.local` で上書き（override=True）
- 本番環境: SSM Parameter Store（変更なし）

### 2. ログレベル見直し基準

**INFO 維持（本番で出力）**: 29箇所
- 実行サマリ（件数、時間、コスト）
- 外部サービス呼び出し結果（Bedrock, SES, RSS, はてブAPI等）
- エラーカウント
- Lambda開始/終了

**DEBUG 降格（ローカルのみ）**: 24箇所
- `*_start` 系（ステップ開始ログ）
- 個別アイテム処理ログ（final_candidate, article_selected等）
- 設定読み込みプロセスの中間ログ
- スキップ・中間状態ログ

### 3. トークン数ログの追加

**Bedrock API レスポンスから実際のトークン数を抽出してログ出力する。**

Bedrock のレスポンス構造:
```python
response_body = {
    "content": [...],
    "usage": {
        "input_tokens": 900,
        "output_tokens": 140
    }
}
```

**変更箇所**: `src/services/llm_judge.py`
- `_judge_single()` メソッドで `response_body["usage"]` を抽出
- 個別記事のトークン数は DEBUG レベルでログ出力
- `judge_batch()` 完了時にバッチ全体の合計トークン数を INFO レベルでログ出力

### 4. 外部サービス応答時間のログ追加

各外部サービス呼び出しの所要時間を INFO レベルでログ出力:
- RSS/Atom収集全体の所要時間（collector.py）
- はてブAPI全体の所要時間（hatena_count_fetcher.py）
- Bedrock LLM判定全体の所要時間（llm_judge.py）
- SESメール送信の所要時間（notifier.py）

**実装方法**: `time.time()` で開始/終了を計測し、完了ログに `elapsed_seconds` を追加

## 変更対象ファイル一覧

### 設定関連
| ファイル | 変更内容 |
|---------|---------|
| `src/shared/config.py` | `.env.local` 読み込み対応 + INFO→DEBUG降格 |
| `.env` | 共通設定として整理 |
| `.env.local`（新規） | ローカル固有設定（LOG_LEVEL=DEBUG等） |
| `.env.example` | 両ファイルの説明追加 |
| `.gitignore` | `.env.local` 追加確認 |

### ログレベル変更（INFO→DEBUG降格）
| ファイル | 降格箇所数 |
|---------|-----------|
| `src/orchestrator/orchestrator.py` | 5箇所（step*_start, step*_complete中間ログ） |
| `src/services/final_selector.py` | 3箇所（start, candidate, selected個別ログ） |
| `src/services/buzz_scorer.py` | 1箇所（start） |
| `src/services/normalizer.py` | 1箇所（start） |
| `src/services/deduplicator.py` | 2箇所（start, cache_check_skipped） |
| `src/services/notifier.py` | 2箇所（start, skipped） |
| `src/services/formatter.py` | 1箇所（start） |
| `src/services/candidate_selector.py` | 1箇所（start） |
| `src/services/collector.py` | 1箇所（start） |
| `src/services/llm_judge.py` | 1箇所（start） |
| `src/shared/config.py` | 3箇所（loading_*, ssm_dotenv_loaded） |
| `src/handler.py` | 2箇所（config_loaded, event_parsed） |
| `src/repositories/interest_master.py` | 1箇所（start） |
| `src/repositories/history_repository.py` | 1箇所（skipped） |
| `src/services/social_proof/*.py` | 5箇所（各fetcher start） |
| `src/services/social_proof/external_service_policy.py` | 1箇所（retrying） |

### 新規ログ追加
| ファイル | 追加内容 | レベル |
|---------|---------|-------|
| `src/services/llm_judge.py` | 個別記事トークン数 | DEBUG |
| `src/services/llm_judge.py` | バッチ合計トークン数 | INFO |
| `src/services/collector.py` | 収集全体の応答時間 | INFO（既存ログに追加） |
| `src/services/llm_judge.py` | LLM判定全体の応答時間 | INFO（既存ログに追加） |
| `src/services/notifier.py` | メール送信の応答時間 | INFO（既存ログに追加） |
| `src/services/social_proof/hatena_count_fetcher.py` | はてブAPI応答時間 | INFO（既存ログに追加） |

### テスト変更
| ファイル | 変更内容 |
|---------|---------|
| `tests/unit/shared/test_config.py`（新規） | .env.local 読み込みテスト |
| `tests/unit/services/test_llm_judge.py` | トークン数ログのテスト |
| 既存テスト | ログレベル変更による影響確認 |

## TDDサイクル

1. **RED**: 失敗するテストを先に書く
2. **GREEN**: 最小限の実装でテストをパスさせる
3. **REFACTOR**: コード品質を向上させる
