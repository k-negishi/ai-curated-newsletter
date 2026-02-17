# LLM候補数削減とConsensus廃止 設計書

## GitHub Issue
https://github.com/k-negishi/ai-curated-newsletter/issues/42

## 背景

- 毎日配信に移行済みで、月額LLMコストが予算$10を超過する可能性がある
- Prompt CachingはHaiku 4.5の最低4,096トークン閾値を満たせず断念（#41）
- 候補数削減とBuzzScoreの簡素化で対応する

## 変更内容

### 1. LLM候補数を150→100に削減

- `CandidateSelector` のデフォルト `max_candidates` を 150→100
- `config.py` の `LLM_CANDIDATE_MAX` デフォルト値を "150"→"100"
- コスト削減効果: 約33%（$0.42→$0.28/run、$12.60→$8.40/月）

### 2. BuzzScoreからConsensus要素を廃止

**理由**: 同一記事が複数RSSフィードに出現する頻度は、Social Proof（はてブ・Zenn等の反応数）に比べてシグナルとして弱い。

**重み再配分（確定）**:

| 要素 | 変更前 | 変更後 |
|------|--------|--------|
| social_proof | 0.35 | **0.45** |
| interest | 0.25 | **0.35** |
| recency | 0.20 | **0.15** |
| consensus | 0.15 | **廃止** |
| authority | 0.05 | **0.05** |

**削除対象**:
- `BuzzScore.consensus_score` フィールド
- `BuzzScore.source_count` フィールド
- `BuzzScorer._calculate_consensus_score()` メソッド
- `BuzzScorer.WEIGHT_CONSENSUS` 定数

## 影響範囲

| ファイル | 変更内容 |
|---------|---------|
| `src/models/buzz_score.py` | `consensus_score`, `source_count` 削除 |
| `src/services/buzz_scorer.py` | consensus関連削除、重み更新 |
| `src/services/candidate_selector.py` | デフォルト150→100 |
| `src/shared/config.py` | デフォルト"150"→"100" |
| `tests/unit/models/test_buzz_score.py` | consensus_score/source_count 削除 |
| `tests/unit/services/test_buzz_scorer.py` | consensusテスト削除、total_score再計算 |
| `tests/integration/test_buzz_scorer_integration.py` | score計算値の更新 |
| `tests/unit/services/test_final_selector.py` | ヘルパーのBuzzScore修正 |

## 実装方針

- Kent Beck の TDD (Test-Driven Development) で実装する
- RED → GREEN → REFACTOR のサイクルを遵守
