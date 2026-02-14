# 設計書

## GitHub Issue

https://github.com/k-negishi/ai-curated-newsletter/issues/23

## issue 内容

- **タイトル**: サービスパッケージのファイル配置見直し
- **本文**: /services 配下にすべての py がおかれてカオスになっている。候補を複数挙げて、複数の評価軸で評価し推奨度と根拠を教えてください。キーワード：ケント・ベック、マーティンファウラー、エリック・エヴァンス、ロバート・マーティン
- **ラベル**: なし

## 実装方針

- **Kent Beck の TDD (Test-Driven Development) で実装する**: 今回はリファクタリング作業のため、既存テストを先に修正し、実装を変更する
- **RED → GREEN → REFACTOR のサイクルを遵守**: テストを先に修正し、最小限の変更でパスさせ、その後リファクタリング

---

## アーキテクチャ概要

### 採用する設計案

**案4: 機能単位フラット + サブパッケージ（最小変更）**

**選定理由**:
- **Kent Beck のシンプル設計原則（YAGNI）に準拠**: 今必要な分割のみを実施
- **移行コストが最小**: フェッチャー系（7ファイル）のみサブパッケージ化、コアロジック（9ファイル）はそのまま
- **テスト影響が最小**: 7テストファイルのみ修正（他11テストはそのまま）
- **既存パターンを踏襲**: `repository-structure.md` の思想を維持
- **Robert Martin のクリーンアーキテクチャに準拠**: レイヤーの依存方向を維持

### 変更前と変更後の構造

**変更前**:
```
services/
├── __init__.py
├── collector.py
├── normalizer.py
├── deduplicator.py
├── buzz_scorer.py
├── candidate_selector.py
├── llm_judge.py
├── final_selector.py
├── formatter.py
├── notifier.py
├── hatena_count_fetcher.py          # フェッチャー系
├── qiita_rank_fetcher.py            # フェッチャー系
├── yamadashy_signal_fetcher.py      # フェッチャー系
├── zenn_like_fetcher.py             # フェッチャー系
├── multi_source_social_proof_fetcher.py  # フェッチャー系
├── social_proof_fetcher.py          # フェッチャー系
└── external_service_policy.py       # フェッチャー系
```

**変更後**:
```
services/
├── __init__.py
├── collector.py                     # そのまま
├── normalizer.py                    # そのまま
├── deduplicator.py                  # そのまま
├── buzz_scorer.py                   # そのまま
├── candidate_selector.py            # そのまま
├── llm_judge.py                     # そのまま
├── final_selector.py                # そのまま
├── formatter.py                     # そのまま
├── notifier.py                      # そのまま
└── social_proof/                    # 新規サブパッケージ
    ├── __init__.py                  # 新規作成
    ├── hatena_count_fetcher.py      # 移動
    ├── qiita_rank_fetcher.py        # 移動
    ├── yamadashy_signal_fetcher.py  # 移動
    ├── zenn_like_fetcher.py         # 移動
    ├── multi_source_social_proof_fetcher.py  # 移動
    ├── social_proof_fetcher.py      # 移動
    └── external_service_policy.py   # 移動
```

---

## コンポーネント設計

### 1. social_proof/ サブパッケージ

**責務**:
- ソーシャルプルーフ（はてブ数、Qiitaランク、Zennいいね数など）の取得を担当
- 外部サービスへのアクセスポリシーを管理

**含まれるファイル**:
1. `hatena_count_fetcher.py`: はてなブックマーク数を取得
2. `qiita_rank_fetcher.py`: Qiitaランクを取得
3. `yamadashy_signal_fetcher.py`: yamadashy シグナルを取得
4. `zenn_like_fetcher.py`: Zennいいね数を取得
5. `multi_source_social_proof_fetcher.py`: 複数ソースからソーシャルプルーフを取得
6. `social_proof_fetcher.py`: ソーシャルプルーフ取得の基底クラス/インターフェース
7. `external_service_policy.py`: 外部サービスへのアクセスポリシー

**実装の要点**:
- `__init__.py` で各フェッチャークラスをエクスポート
- インポートパスは `from src.services.social_proof.hatena_count_fetcher import HatenaCountFetcher` 形式に変更
- ファイルの中身は変更しない（移動のみ）

### 2. 既存のコアロジックファイル

**責務**:
- 収集、正規化、重複排除、スコア計算、判定、選定、通知など、コアビジネスロジックを担当

**含まれるファイル**:
1. `collector.py`: RSS/Atom収集
2. `normalizer.py`: 正規化
3. `deduplicator.py`: 重複排除
4. `buzz_scorer.py`: Buzzスコア計算
5. `candidate_selector.py`: 候補選定
6. `llm_judge.py`: LLM判定
7. `final_selector.py`: 最終選定
8. `formatter.py`: メール本文生成
9. `notifier.py`: メール送信

**実装の要点**:
- **これらのファイルは移動しない**
- インポートパスも変更しない
- ファイルの中身も変更しない

---

## データフロー

### インポートパスの変更

**変更前**:
```python
from src.services.hatena_count_fetcher import HatenaCountFetcher
from src.services.qiita_rank_fetcher import QiitaRankFetcher
from src.services.yamadashy_signal_fetcher import YamadaskySignalFetcher
from src.services.zenn_like_fetcher import ZennLikeFetcher
from src.services.multi_source_social_proof_fetcher import MultiSourceSocialProofFetcher
from src.services.social_proof_fetcher import SocialProofFetcher
from src.services.external_service_policy import ExternalServicePolicy
```

**変更後**:
```python
from src.services.social_proof.hatena_count_fetcher import HatenaCountFetcher
from src.services.social_proof.qiita_rank_fetcher import QiitaRankFetcher
from src.services.social_proof.yamadashy_signal_fetcher import YamadaskySignalFetcher
from src.services.social_proof.zenn_like_fetcher import ZennLikeFetcher
from src.services.social_proof.multi_source_social_proof_fetcher import MultiSourceSocialProofFetcher
from src.services.social_proof.social_proof_fetcher import SocialProofFetcher
from src.services.social_proof.external_service_policy import ExternalServicePolicy
```

### 影響を受けるファイル

**ソースコード**:
1. `src/orchestrator/orchestrator.py`: インポートパスを修正（該当なし、buzz_scorerのみ使用）
2. `src/services/buzz_scorer.py`: social_proofフェッチャーをインポートしている場合、修正

**テストコード**:
1. `tests/unit/services/test_hatena_count_fetcher.py`
2. `tests/unit/services/test_qiita_rank_fetcher.py`
3. `tests/unit/services/test_yamadashy_signal_fetcher.py`
4. `tests/unit/services/test_zenn_like_fetcher.py`
5. `tests/unit/services/test_multi_source_social_proof_fetcher.py`
6. `tests/unit/services/test_social_proof_fetcher.py`
7. `tests/unit/services/test_external_service_policy.py`
8. `tests/integration/test_buzz_scorer_integration.py`: buzz_scorerがsocial_proofを使用している場合、修正

---

## エラーハンドリング戦略

### 既存のエラーハンドリングを維持

- ファイル移動のみのため、エラーハンドリング戦略は変更しない
- 既存のカスタムエラークラス（`CollectionError`, `LlmError`, `NotificationError`）はそのまま使用

---

## テスト戦略

### ユニットテスト

**修正対象**:
- `tests/unit/services/test_hatena_count_fetcher.py`: インポートパスを修正
- `tests/unit/services/test_qiita_rank_fetcher.py`: インポートパスを修正
- `tests/unit/services/test_yamadashy_signal_fetcher.py`: インポートパスを修正
- `tests/unit/services/test_zenn_like_fetcher.py`: インポートパスを修正
- `tests/unit/services/test_multi_source_social_proof_fetcher.py`: インポートパスを修正
- `tests/unit/services/test_social_proof_fetcher.py`: インポートパスを修正
- `tests/unit/services/test_external_service_policy.py`: インポートパスを修正

**テスト戦略**:
1. テストファイルのインポートパスを修正
2. テストを実行して、すべてのテストがパスすることを確認
3. テストロジックは変更しない（インポートパスのみ修正）

### 統合テスト

**修正対象**:
- `tests/integration/test_buzz_scorer_integration.py`: buzz_scorerがsocial_proofを使用している場合、インポートパスを修正

---

## 依存ライブラリ

**変更なし**: ファイル移動のみのため、新しいライブラリは追加しない

---

## ディレクトリ構造

### 変更後の完全な構造

```
src/
├── handler.py
├── orchestrator/
│   ├── __init__.py
│   └── orchestrator.py
├── services/
│   ├── __init__.py
│   ├── collector.py
│   ├── normalizer.py
│   ├── deduplicator.py
│   ├── buzz_scorer.py
│   ├── candidate_selector.py
│   ├── llm_judge.py
│   ├── final_selector.py
│   ├── formatter.py
│   ├── notifier.py
│   └── social_proof/              # 新規サブパッケージ
│       ├── __init__.py            # 新規作成
│       ├── hatena_count_fetcher.py
│       ├── qiita_rank_fetcher.py
│       ├── yamadashy_signal_fetcher.py
│       ├── zenn_like_fetcher.py
│       ├── multi_source_social_proof_fetcher.py
│       ├── social_proof_fetcher.py
│       └── external_service_policy.py
├── repositories/
├── models/
└── shared/
```

---

## 実装の順序

### TDDサイクル

今回はリファクタリング作業のため、以下の順序で実施:

1. **既存テストを確認（GREEN）**: 変更前にすべてのテストがパスすることを確認
2. **ファイル移動（RED）**: ファイルを移動してテストを実行、失敗することを確認
3. **インポートパス修正（GREEN）**: インポートパスを修正してテストをパス
4. **リファクタリング（REFACTOR）**: コードの品質チェック（lint, format, typecheck）

### 実装ステップ

1. **フェーズ1: サブパッケージ作成とファイル移動**
   - `src/services/social_proof/` ディレクトリを作成
   - 7ファイル（フェッチャー系）を `social_proof/` に移動
   - `__init__.py` を作成してエクスポート

2. **フェーズ2: インポートパス修正**
   - `src/services/buzz_scorer.py` のインポートパスを修正（該当する場合）
   - 7テストファイルのインポートパスを修正
   - 統合テストのインポートパスを修正（該当する場合）

3. **フェーズ3: 品質チェックと修正**
   - すべてのテストが通ることを確認: `.venv/bin/pytest tests/ -v`
   - リントチェック: `.venv/bin/ruff check src/`
   - コードフォーマット: `.venv/bin/ruff format src/`
   - 型チェック: `.venv/bin/mypy src/`

4. **フェーズ4: ドキュメント更新**
   - `docs/repository-structure.md` を更新（必要に応じて）
   - 実装後の振り返り（tasklist.md に記録）

---

## セキュリティ考慮事項

- **変更なし**: ファイル移動のみのため、セキュリティ上の新しい考慮事項はない
- 既存のセキュリティ原則（AWS Secrets Manager、ログマスキングなど）を維持

---

## パフォーマンス考慮事項

- **変更なし**: ファイル移動のみのため、パフォーマンスへの影響はない
- インポートパスが変わるが、Pythonのモジュールロード時間への影響は無視できる

---

## 将来の拡張性

### Phase 2 への移行パス

今回の案4を採用することで、将来的に以下の拡張が容易になる:

1. **案1（レイヤー分割）への移行**:
   - `social_proof/` → `data_fetching/social_proof/` に移動
   - コアロジックを `processing/` に移動
   - 通知系を `notification/` に移動

2. **案2（ドメイン分割）への移行**:
   - `social_proof/` はそのまま（既にドメインコンセプト単位）
   - 他のコアロジックを `curation/`, `collection/`, `notification/` に分割

3. **Step Functions化への対応**:
   - サブパッケージ構造により、Lambda関数の分割が容易
   - `social_proof/` を独立したLambda関数として切り出し可能

### 拡張のタイミング

以下の条件に該当する場合、さらなる分割を検討:

- 収集元が大幅に増える（現状の2倍以上）
- 処理時間が12分を超える（Step Functions化が必要）
- チーム開発に移行する（役割分担のため、より明確な分割が必要）

---

## 実装上の注意事項

### ファイル移動時の注意

1. **git mv を使用すること**: ファイルの履歴を保持するため、`git mv` コマンドを使用
2. **一度に全ファイルを移動すること**: 段階的な移動は混乱を招くため、一度に全ファイルを移動
3. **移動後すぐにテストを実行すること**: 移動後の状態を即座に確認

### インポートパス修正時の注意

1. **正規表現で一括置換**: インポートパスは正規表現で一括置換すると効率的
2. **テストを先に修正**: テストファイルを先に修正してから、ソースコードを修正
3. **段階的に修正して確認**: 1ファイルずつ修正してテストを実行、確実にパスすることを確認

### 品質チェック

1. **すべてのチェックを通すこと**: ruff, mypy, pytest のすべてがパスすること
2. **カバレッジを維持すること**: リファクタリング後もカバレッジが低下しないこと
3. **既存の機能を壊さないこと**: すべてのテストがパスし、既存の動作が維持されること
