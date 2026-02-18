# 設計: Bedrockスロットリング改善

## GitHub Issue
https://github.com/k-negishi/ai-curated-newsletter/issues/46

## 実装方針
- Kent Beck の TDD (Test-Driven Development) で実装する
- RED → GREEN → REFACTOR のサイクルを遵守
- テストを先に書き、最小限の実装でパスさせ、その後リファクタリング

## TDDサイクル
1. **RED**: 失敗するテストを先に書く
2. **GREEN**: 最小限の実装でテストをパスさせる
3. **REFACTOR**: コード品質を向上させる

## 背景

CWログ調査（Issue #46）により、以下の問題が判明:

1. **boto3の二重リトライ**: boto3のデフォルトリトライ（max_attempts=5）と我々のカスタムリトライ（max_retries=4）が重複し、1記事あたり最大25回のAPI呼び出しが発生
2. **バーストパターン**: semaphore + 固定sleep の組み合わせで、全ワーカーが同時にAPI呼び出しを実行

## 改善1: boto3の内部リトライ無効化

### 現状
```python
# handler.py:68 - デフォルト設定（legacy retry, max_attempts=5）
bedrock_runtime = boto3.client("bedrock-runtime", region_name=config.bedrock_region)
```

### 変更後
```python
from botocore.config import Config

bedrock_config = Config(
    retries={"max_attempts": 0, "mode": "standard"},
)
bedrock_runtime = boto3.client(
    "bedrock-runtime",
    region_name=config.bedrock_region,
    config=bedrock_config,
)
```

### 判断根拠

| 選択肢 | 説明 | 推奨度 |
|--------|------|--------|
| **max_attempts=0** | boto3リトライを完全無効化。我々のリトライに一本化 | **推奨** |
| max_attempts=1 | boto3は1回だけ試行、リトライなし | 同等 |
| max_attempts=2 | boto3を2回に削減 | 非推奨: まだ二重リトライ |

`max_attempts=0` を選択。理由:
- 我々のリトライが指数バックオフ+ジッターを実装済みで十分
- boto3の内部リトライは短い固定間隔のため、スロットリング時に逆効果
- リトライロジックを一箇所に統一し、挙動を予測可能にする

## 改善2: リクエストの時間分散（staggered start）

### 現状の問題
```python
async def judge_with_semaphore(article):
    async with semaphore:
        await asyncio.sleep(self._request_interval)  # 全員が同時に待つ
        return await self._judge_single(article)
```

5ワーカーが同時にセマフォ取得 → 同時に2.5秒sleep → **同時にAPI呼び出し** → バースト

### 変更後
```python
async def judge_with_semaphore(index: int, article: Article) -> JudgmentResult | None:
    # 初回のみstaggered delay: ワーカーごとにずらす
    if index < self._concurrency_limit:
        stagger_delay = index * (self._request_interval / self._concurrency_limit)
        await asyncio.sleep(stagger_delay)
    async with semaphore:
        if self._request_interval > 0:
            await asyncio.sleep(self._request_interval)
        return await self._judge_single(article)
```

### 判断根拠

| 選択肢 | 説明 | 推奨度 |
|--------|------|--------|
| **staggered start** | 初回バッチのみインデックスで分散 | **推奨** |
| token bucket | 全体的なレート制御 | 過剰: 現状のsemaphore+intervalで十分 |
| request_interval増加 | 間隔を広げるだけ | 対症療法: バーストは解消されない |

staggered start を選択。理由:
- 最小限の変更で初回バーストを解消
- 既存の semaphore + request_interval の仕組みをそのまま活かせる
- 2回目以降は request_interval の効果で自然に分散される

## 変更対象ファイル一覧

| ファイル | 変更内容 |
|---------|---------|
| `src/handler.py` | boto3 Config で内部リトライ無効化 |
| `src/services/llm_judge.py` | staggered start の実装 |
| `tests/unit/services/test_llm_judge.py` | staggered start のテスト追加 |
| `tests/integration/test_judgment_flow.py` | 統合テストの確認（変更不要の可能性大） |

## リスク評価

| リスク | 影響度 | 対策 |
|--------|--------|------|
| boto3リトライ無効化による一時的エラー増加 | 低 | 我々のリトライが十分にカバー。テストで検証 |
| staggered startによるテスト破壊 | 低 | 既存テストの sleep モックに影響する可能性。テスト修正で対応 |
