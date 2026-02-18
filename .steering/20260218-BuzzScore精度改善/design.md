# BuzzScore精度改善 設計書

## GitHub Issue
https://github.com/k-negishi/ai-curated-newsletter/issues/44

## 変更概要

3つの独立した改善を同時に実施し、BuzzScoreの精度を向上させる。

1. **はてブスコアを区間マッピング方式に変更** — 実用帯域の分解能向上
2. **SP計算を適用重み正規化に変更** — 外部ブログの構造的不利を解消
3. **Recency廃止＋重み再配分** — 低SP記事の不当な底上げを排除

## TDDサイクル

1. **RED**: 失敗するテストを先に書く
2. **GREEN**: 最小限の実装でテストをパスさせる
3. **REFACTOR**: コード品質を向上させる

---

## 変更1: はてブスコアの区間マッピング

### 現状の問題

`min(100, log10(count + 1) * 25)` は10,000件で満点の設計。
テック記事のブクマ分布は0〜300件が大半だが、この帯域でスコアが潰れる。
- 50件 vs 100件の差がわずか1.5点
- 100件で50点止まり（テック記事では十分バズなのに半分の評価）

### 変更内容

`_calculate_scores()` メソッドの計算ロジックを、対数関数から区間マッピングテーブルに変更する。

```python
HATENA_SCORE_TABLE = [
    (500, 100.0),   # 500件以上: 大事件
    (200, 92.0),    # 200〜499件: 大バズ
    (100, 80.0),    # 100〜199件: バズ
    (50, 65.0),     # 50〜99件: 話題
    (30, 50.0),     # 30〜49件: 良記事（テック記事のスケール中央値）
    (15, 25.0),     # 15〜29件: 注目され始め
    (5, 12.0),      # 5〜14件: わずかに注目
    (1, 5.0),       # 1〜4件: ほぼノイズ
]
# 0件: 0点
```

### 対象ファイル

| ファイル | 変更内容 |
|---------|---------|
| `src/services/social_proof/hatena_count_fetcher.py` | `_calculate_scores()` を区間マッピングに変更、`math` import削除、`HATENA_SCORE_TABLE` 定数追加 |
| `tests/unit/services/test_hatena_count_fetcher.py` | `test_score_calculation_log_transform` → 区間マッピング検証に書き換え、`test_fetch_batch_success_under_50` のアサーション更新 |

---

## 変更2: SP計算の適用重み正規化

### 現状の問題

全URLに対して全4指標の重みで割っているため、Zenn/Qiitaランキングが取得できない外部ブログが構造的に不利。

- Zenn記事: H(0.45)+Z(0.35)+Y(0.05)=0.85 が獲得可能 → 最大85点
- 外部ブログ: H(0.45)+Y(0.05)=0.50 が上限 → 最大50点

### 変更内容

`_calculate_integrated_scores()` メソッドで、URLのドメインに基づいて適用可能な重みのみで正規化する。

```python
# ドメイン判定ロジック
# zenn.dev  → H, Z, Y が適用 → applicable_weight = 0.85
# qiita.com → H, Q, Y が適用 → applicable_weight = 0.65
# その他    → H, Y が適用    → applicable_weight = 0.50
```

各フェッチャーのスコア自体は変更しない。統合計算の分母のみ変更。

### 対象ファイル

| ファイル | 変更内容 |
|---------|---------|
| `src/services/social_proof/multi_source_social_proof_fetcher.py` | `_calculate_integrated_scores()` にドメイン判定と適用重み正規化を追加 |
| `tests/unit/services/test_multi_source_social_proof_fetcher.py` | 既存テストの期待値更新、ドメイン別正規化テスト追加 |

### 設計判断

- ドメイン判定は `urllib.parse.urlparse(url).netloc` で行う
- Zenn判定: `"zenn.dev" in netloc`
- Qiita判定: `"qiita.com" in netloc`
- その他: 上記以外すべて
- yamadashy(Y)とhatena(H)は全ドメインで適用（ドメイン非依存の指標）

---

## 変更3: Recency廃止＋重み再配分

### 現状の問題

- 毎日配信では全記事が0〜1日前のため、Recencyは全記事に一律ボーナスを与えるだけで差別化に寄与しない
- SPが「今の話題性」を既に反映しているためRecencyは冗長
- `external_buzz` プロパティにRecency成分が混入し、低SP記事を不当に底上げ

### 変更内容

#### BuzzScoreモデル (`src/models/buzz_score.py`)

- `recency_score` フィールドを削除
- `external_buzz` プロパティ: 計算式は同じ `(total - interest×0.35) / 0.65`
  - totalにrecencyが含まれなくなるため、純粋に「SP＋Authority」のみを反映
- `_MAX_EXTERNAL_BUZZ_RAW`: `1.0 - 0.35 = 0.65` のまま据え置き（Interest以外の重みの合計は変わらない: SP 0.55 + Authority 0.10 = 0.65）

#### BuzzScorer (`src/services/buzz_scorer.py`)

- `_calculate_recency_score()` メソッドを削除
- `WEIGHT_RECENCY` 定数を削除
- 重み再配分:
  ```python
  # Before
  WEIGHT_SOCIAL_PROOF = 0.45
  WEIGHT_INTEREST = 0.35
  WEIGHT_RECENCY = 0.15
  WEIGHT_AUTHORITY = 0.05

  # After
  WEIGHT_SOCIAL_PROOF = 0.55
  WEIGHT_INTEREST = 0.35
  WEIGHT_AUTHORITY = 0.10
  ```
- `_calculate_total_score()`: 引数から `recency` を削除、3要素の重み付き合算に変更
- `calculate_scores()`: `_calculate_recency_score()` 呼び出しを削除、BuzzScore生成から `recency_score` を削除

#### FinalSelector (`src/services/final_selector.py`)

- `_ZERO_BUZZ_SCORE` から `recency_score` を削除

### BuzzLabel閾値

HIGH≥70 / MID≥40 を維持（変更なし）。

### 対象ファイル

| ファイル | 変更内容 |
|---------|---------|
| `src/models/buzz_score.py` | `recency_score` フィールド削除、docstring更新 |
| `src/services/buzz_scorer.py` | Recency関連削除、重み再配分、`_calculate_total_score` 3引数化 |
| `src/services/final_selector.py` | `_ZERO_BUZZ_SCORE` から `recency_score` 削除 |
| `tests/unit/models/test_buzz_score.py` | 全BuzzScore生成箇所から `recency_score` 削除（約12箇所） |
| `tests/unit/services/test_buzz_scorer.py` | Recencyテスト3件削除、`_calculate_total_score` テスト更新、weight検証更新 |
| `tests/unit/services/test_final_selector.py` | `_make_buzz_score` ヘルパーから `recency_score` 削除 |
| `tests/integration/test_buzz_scorer_integration.py` | `recency_score` アサーション削除、total_score計算式更新（4箇所） |

---

## 影響範囲まとめ

### 変更するソースコード（4ファイル）
1. `src/models/buzz_score.py`
2. `src/services/buzz_scorer.py`
3. `src/services/social_proof/hatena_count_fetcher.py`
4. `src/services/social_proof/multi_source_social_proof_fetcher.py`
5. `src/services/final_selector.py`（`_ZERO_BUZZ_SCORE` のみ）

### 変更するテストコード（5ファイル）
1. `tests/unit/models/test_buzz_score.py`
2. `tests/unit/services/test_buzz_scorer.py`
3. `tests/unit/services/test_hatena_count_fetcher.py`
4. `tests/unit/services/test_multi_source_social_proof_fetcher.py`
5. `tests/unit/services/test_final_selector.py`
6. `tests/integration/test_buzz_scorer_integration.py`

### 変更しないファイル
- `src/services/final_selector.py` のロジック部分（Composite Score計算は変更なし）
- `src/services/candidate_selector.py`（total_scoreのみ参照、内部構造に依存しない）
- BuzzLabel閾値（HIGH≥70, MID≥40 据え置き）
