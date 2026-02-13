# 設計書

## アーキテクチャ概要

DynamoDB処理のコメントアウトは、以下のアプローチで実施する:

1. **最小侵襲的な変更**: コードの削除ではなく、コメントアウトで対応
2. **段階的な無効化**: handler → orchestrator → services の順で依存を解消
3. **ログでの代替**: キャッシュ・履歴保存の代わりにログ出力で記録

```
┌─────────────────────────────────────────────────────────┐
│ handler.py                                              │
│  - DynamoDB初期化をコメントアウト                        │
│  - CacheRepository/HistoryRepository生成をスキップ       │
│  - Orchestratorに None を渡す（または削除）              │
└────────────────────┬────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────┐
│ orchestrator.py                                         │
│  - CacheRepository/HistoryRepositoryへの依存を無効化     │
│  - 履歴保存処理をコメントアウト                          │
│  - ログで実行サマリを出力                                │
└────────────────────┬────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────┐
│ services/                                               │
│  - deduplicator.py: キャッシュチェックをスキップ         │
│  - llm_judge.py: キャッシュ保存をスキップ                │
└─────────────────────────────────────────────────────────┘
```

## コンポーネント設計

### 1. handler.py

**責務**:
- DynamoDBリソース初期化のコメントアウト
- CacheRepository/HistoryRepositoryのインスタンス化をスキップ
- Orchestratorに渡す依存を調整（Noneまたは削除）

**実装の要点**:
- boto3.resource("dynamodb")の呼び出しをコメントアウト
- 環境変数（CACHE_TABLE_NAME, HISTORY_TABLE_NAME）の取得もコメントアウト
- Orchestratorの初期化時にcache_repository=None, history_repository=Noneを渡す
- または、Orchestratorのコンストラクタを変更してOptional型に

### 2. orchestrator.py

**責務**:
- CacheRepository/HistoryRepositoryへの依存を無効化
- 履歴保存処理をスキップ
- 実行サマリをログ出力

**実装の要点**:
- `__init__`でcache_repository/history_repositoryをOptional型に
- `execute`メソッド内の`self._history_repository.save(summary)`をコメントアウト
- 代わりに`logger.info("execution_summary", summary=summary)`でログ出力
- cache_repository/history_repositoryがNoneの場合のガード処理を追加

### 3. services/deduplicator.py

**責務**:
- キャッシュチェック処理をスキップ
- 全記事をユニークとして扱う（重複排除のみ実施）

**実装の要点**:
- `__init__`でcache_repositoryをOptional型に
- `deduplicate`メソッド内の`self._cache_repository.batch_exists()`をスキップ
- cache_repositoryがNoneの場合、cached_count=0として処理を継続
- ログに「キャッシュチェックスキップ」を記録

### 4. services/llm_judge.py

**責務**:
- 判定結果のキャッシュ保存をスキップ
- LLM判定自体は継続（キャッシュなしで全記事を判定）

**実装の要点**:
- `__init__`でcache_repositoryをOptional型に
- `judge_batch`メソッド内の`self._cache_repository.put(result)`をスキップ
- cache_repositoryがNoneの場合、キャッシュ保存をスキップするだけで判定は実施
- ログに「キャッシュ保存スキップ」を記録

## データフロー

### ニュースレター生成フロー（DynamoDBなし）
```
1. handler: DynamoDB初期化をスキップ
2. handler: Orchestratorを初期化（cache_repository=None, history_repository=None）
3. orchestrator: 収集・正規化を実行
4. deduplicator: キャッシュチェックをスキップし、URL重複排除のみ実施
5. orchestrator: Buzzスコア計算・候補選定
6. llm_judge: 全記事をLLM判定（キャッシュヒットなし）
7. llm_judge: 判定結果のキャッシュ保存をスキップ
8. orchestrator: 最終選定・フォーマット・通知
9. orchestrator: 履歴保存をスキップし、ログに実行サマリを出力
10. handler: レスポンス返却
```

## エラーハンドリング戦略

### Noneチェック

各コンポーネントでcache_repository/history_repositoryがNoneの場合のガード処理を追加:

```python
if self._cache_repository is not None:
    self._cache_repository.put(judgment)
else:
    logger.info("cache_put_skipped", url=judgment.url)
```

### エラーハンドリングパターン

- DynamoDB関連エラーは発生しない（呼び出し自体をスキップ）
- Noneチェック漏れによるAttributeErrorに注意
- ログで「スキップ」を明示的に記録

## テスト戦略

### ユニットテスト
- deduplicator: cache_repository=Noneでのテスト
- llm_judge: cache_repository=Noneでのテスト
- orchestrator: history_repository=Noneでのテスト

### 統合テスト
- DynamoDB依存のテストはスキップ（@pytest.mark.skipでマーク）
- キャッシュなしでの全体フロー確認

### E2Eテスト
- dry_runモードでの実行確認
- DynamoDB接続エラーが発生しないことを確認

## 依存ライブラリ

変更なし（既存のpyproject.tomlをそのまま使用）

## ディレクトリ構造

変更対象ファイル:
```
src/
├── handler.py                   # DynamoDB初期化をコメントアウト
├── orchestrator/
│   └── orchestrator.py          # 履歴保存をコメントアウト
├── services/
│   ├── deduplicator.py          # キャッシュチェックをスキップ
│   └── llm_judge.py             # キャッシュ保存をスキップ
└── repositories/
    ├── cache_repository.py      # 変更なし（使用されなくなる）
    └── history_repository.py    # 変更なし（使用されなくなる）
```

テスト:
```
tests/
├── unit/
│   ├── services/
│   │   ├── test_deduplicator.py  # cache_repository=Noneのテスト追加
│   │   └── test_llm_judge.py     # cache_repository=Noneのテスト追加
│   └── orchestrator/
│       └── test_orchestrator.py  # history_repository=Noneのテスト追加
└── integration/
    └── test_*_flow.py            # DynamoDB依存テストをスキップ
```

## 実装の順序

1. **Phase 1: handler.pyの変更**
   - DynamoDB初期化をコメントアウト
   - Orchestrator初期化時の引数調整

2. **Phase 2: orchestrator.pyの変更**
   - コンストラクタでOptional型に変更
   - 履歴保存処理をコメントアウト
   - ログ出力で代替

3. **Phase 3: servicesの変更**
   - deduplicator.py: キャッシュチェックをスキップ
   - llm_judge.py: キャッシュ保存をスキップ

4. **Phase 4: テストの調整**
   - DynamoDB依存テストをスキップ
   - cache_repository=Noneでのテストを追加

5. **Phase 5: 動作確認**
   - 全テストの実行
   - dry_runモードでの実行確認

## セキュリティ考慮事項

- DynamoDB接続がなくなるため、セキュリティリスクは減少
- 実行履歴が永続化されないため、監査証跡が残らない点に注意（Phase 1のみの一時的な状態）

## パフォーマンス考慮事項

- キャッシュが無効化されるため、全記事がLLM判定される
- DynamoDB通信がなくなるため、ネットワークレイテンシは減少
- LLM判定数が増加するため、コストと実行時間が増加する可能性

## 将来の拡張性

Phase 2でDynamoDBを再有効化する際の考慮事項:
- コメントアウトを解除するだけで復元可能
- Optional型の設計により、段階的な再有効化が可能
- テストもDynamoDBありなしの両方に対応
