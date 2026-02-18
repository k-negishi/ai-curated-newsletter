# プロジェクト用語集 (Glossary)

## 概要

このドキュメントは、`ai-curated-newsletter` プロジェクト内で使用される用語の定義を管理します。

**更新日**: 2026-02-18

---

## ドメイン用語

プロジェクト固有のビジネス概念や機能に関する用語。

### 出力最小主義

**定義**: 収集は多くてよいが、出力（通知）は厳選する設計思想

**説明**:
本プロジェクトの最重要原則。大量の情報を収集しても、ユーザーへの通知は各回最大15件に制限する。通知が少ないこと自体が価値であり、判断コストの削減とノイズの排除が目的。

**関連用語**:
- [TooMuch原則](#toomuch原則): 個人開発における複雑さの回避
- [最終選定](#最終選定): 最大15件への絞り込みプロセス

**使用例**:
- 「出力最小主義に従い、最終通知は15件以内に制限する」
- 「収集は400件でも、出力最小主義により通知は10件のみ」

**PRD参照**: [プロダクト要求定義書](./product-requirements.md#基本思想)

**英語表記**: Output Minimalism

### LLM判断器

**定義**: LLMを記事の価値判断のみに限定して使用する設計パターン

**説明**:
LLMは以下のみを実行：
- Interest判定（ACT_NOW/THINK/FYI/IGNORE）
- 要約生成（summary）
- タグ付け（tags）

LLMが実行しないこと：
- 件数制御（ロジックで制御）
- 重複排除（URL一致で処理）
- Buzz定量（非LLMアルゴリズム）
- Buzzラベル化（BuzzScoreから閾値変換で導出）

**関連用語**:
- [Interest Label](#interest-label): LLMが判定する関心度ラベル
- [Buzzスコア](#buzzスコア): 非LLMで計算する話題性スコア

**使用例**:
- 「LLM判断器として、Bedrock Claude Haiku 4.5を使用する」
- 「LLM判断器は判定のみを行い、件数制御はOrchestratorで実行する」

**実装箇所**: `src/services/llm_judge.py`

**英語表記**: LLM as Judge

### Buzzスコア

**定義**: 記事の話題性を定量化する非LLM計算スコア（0-100点）

**説明**:
以下の3要素から算出される：
- SocialProof（外部反応）: 4指標統合スコア（55%）
- Interest（興味との一致度）: InterestProfileとの5段階マッチング（35%）
- Authority（公式補正）: authority_levelに応じたスコア（10%）

LLMは使用せず、純粋なアルゴリズムで計算する。

**計算式**:
```
total_score = (social_proof × 0.55) + (interest × 0.35) + (authority × 0.10)

where:
  # SocialProof 4指標統合スコア（55%）
  social_proof_score = yamadashy × 0.05 + hatena × 0.45 + zenn × 0.35 + qiita × 0.15

  # Interest 5段階マッチングスコア（35%）
  interest_score = max: 100, high: 80, medium: 55, low: 30, ignore: 0, デフォルト: 15

  # Authority スコア（10%）
  authority_score = OFFICIAL: 100, HIGH: 80, MEDIUM: 50, LOW/未設定: 0
```

**external_buzz（外部話題性）**:
total_scoreからinterest成分を除去し、残りを0-100スケールに正規化したもの。Composite Scoreの構成要素（60%）として使用。

```
external_buzz = (total_score - interest_score × 0.35) / 0.65
（clamp: 0.0 ～ 100.0）
```

**関連用語**:
- [候補選定](#候補選定): Buzzスコアでソートして上位を選定
- [Composite Score](#composite-score): Buzzスコアのexternal_buzzがComposite Scoreの構成要素

**使用例**:
- 「Buzzスコア80点以上の記事を優先的にLLM判定に回す」
- 「SocialProof（外部反応）が高い記事はBuzzスコアが高くなる」

**実装箇所**: `src/services/buzz_scorer.py`

**英語表記**: Buzz Score

### 鮮度スコア

**定義**: 記事の公開日時・判定日時に基づく時間的な優先度指標

**説明**:
BuzzScoreの直接的な構成要素ではなくなったが、最終選定（FinalSelector）において
Composite Scoreが同値の場合のソートキー（judged_at降順）として使用される。

**関連用語**:
- [Buzzスコア](#buzzスコア): 鮮度はBuzzスコアの直接的な構成要素ではない
- [最終選定](#最終選定): Composite Score同値時のソートキーとして使用

**使用例**:
- 「Composite Scoreが同値の場合、鮮度（judged_at降順）でソートする」
- 「より新しい記事が同スコアであれば優先される」

**英語表記**: Recency Score

### Interest Label

**定義**: LLMが判定する記事の関心度を示す4段階のラベル

**取りうる値**:

| ラベル | 意味 | 定義 |
|-------|------|------|
| `ACT_NOW` | 今すぐ読むべき | ユーザーの強い関心領域に合致し、実践的な価値がある |
| `THINK` | 深く考えるべき | アーキテクチャ・設計思想など、熟考が必要な内容 |
| `FYI` | 参考情報 | 知っておくと良いが、緊急性は低い |
| `IGNORE` | 通知不要 | ユーザーの関心外、または低優先度 |

**優先順位**: ACT_NOW > THINK > FYI > IGNORE

**関連用語**:
- [Buzz Label](#buzz-label): 話題性のラベル
- [最終選定](#最終選定): Interest Labelの優先順位で選定

**使用例**:
```python
@dataclass
class JudgmentResult:
    interest_label: Literal["ACT_NOW", "THINK", "FYI", "IGNORE"]
    # ...
```

**実装箇所**: `src/models/judgment.py`

**英語表記**: Interest Label

### Buzz Label

**定義**: BuzzScoreのtotal_scoreから閾値変換で導出される話題性の3段階ラベル

**取りうる値**:

| ラベル | 意味 | 閾値 |
|-------|------|------|
| `HIGH` | 高い話題性 | total_score ≥ 70 |
| `MID` | 中程度の話題性 | 40 ≤ total_score < 70 |
| `LOW` | 低い話題性 | total_score < 40 |

**導出方法**: `BuzzScore.to_buzz_label()` メソッドで変換。LLMでは判定しない。

**関連用語**:
- [Interest Label](#interest-label): 関心度のラベル（LLMが判定）
- [Buzzスコア](#buzzスコア): Buzz Labelの導出元となる定量スコア

**使用例**:
```python
@dataclass
class JudgmentResult:
    buzz_label: Literal["HIGH", "MID", "LOW"]
    # ...
```

**実装箇所**: `src/models/judgment.py`

**英語表記**: Buzz Label

### 判定キャッシュ

**定義**: URL単位でLLM判定結果を永続保存するキャッシュ（DynamoDB）

**説明**:
同一URLは再判定しない「再判定禁止」の原則に基づく。一度判定した記事は、判定結果をキャッシュに保存し、次回以降はLLM呼び出しをスキップする。

**データ構造**:
- PK: `URL#<sha256(url)>`
- SK: `JUDGMENT#v1`
- TTL: なし（永続保存）

**関連用語**:
- [再判定禁止](#再判定禁止): キャッシュヒット時はLLM判定をスキップ
- [実行履歴](#実行履歴): 各実行のサマリを保存（キャッシュとは別）

**使用例**:
- 「判定キャッシュにヒットした記事は、LLM判定をスキップする」
- 「判定キャッシュは永続保存され、削除されない」

**実装箇所**: `src/repositories/cache_repository.py`

**DynamoDBテーブル**: `ai-curated-newsletter-cache`

**英語表記**: Judgment Cache

### 再判定禁止

**定義**: 同一URLは一度判定したら、二度と判定しない絶対制約

**説明**:
コスト削減と一貫性維持のため、同一URLのLLM判定は1回のみ。判定結果は判定キャッシュに永続保存され、再度同じURLが収集されても、キャッシュから結果を取得する。

**関連用語**:
- [判定キャッシュ](#判定キャッシュ): 再判定禁止を実現するための仕組み

**使用例**:
- 「再判定禁止の原則により、同一URLは判定キャッシュから取得する」
- 「再判定禁止により、月間LLMコストを$4以内に抑える」

**PRD参照**: [プロダクト要求定義書](./product-requirements.md#絶対制約)

**英語表記**: No Re-judgment

### 収集元マスタ

**定義**: RSS/Atomフィードの収集元設定を管理するマスタデータ

**説明**:
Phase 1ではS3上のYAML設定ファイル（`sources.yaml`）として管理。Phase 2ではDynamoDBテーブルに移行予定。追加・削除はマスタの変更のみで完結し、コード改修は不要。

**設定項目**:
```yaml
source_id: hacker_news
name: Hacker News
feed_url: https://news.ycombinator.com/rss
feed_type: rss
priority: high
timeout_seconds: 10
retry_count: 2
enabled: true
```

**関連用語**:
- [Collector](#collector): 収集元マスタを読み込んで記事を収集

**使用例**:
- 「収集元マスタに新しいフィードを追加する」
- 「収集元マスタでフィードを無効化する（enabled: false）」

**実装箇所**: `src/repositories/source_master.py`

**設定ファイル**: `config/sources.yaml` (Phase 1)

**英語表記**: Source Master

### 実行履歴

**定義**: ニュースレター実行ごとのサマリ情報を保存するデータ（DynamoDB）

**説明**:
各実行（run_id単位）のメトリクスを保存：
- 収集件数
- LLM判定件数
- 最終選定件数
- 実行時間
- 推定コスト

**データ構造**:
- PK: `RUN#<YYYYWW>`（例: `RUN#202503`）
- SK: `SUMMARY#<timestamp>`
- TTL: 90日後に自動削除

**関連用語**:
- [判定キャッシュ](#判定キャッシュ): 判定結果を保存（実行履歴とは別）

**使用例**:
- 「実行履歴から週次のコスト推移を確認する」
- 「実行履歴のTTLは90日で、古いデータは自動削除される」

**実装箇所**: `src/repositories/history_repository.py`

**DynamoDBテーブル**: `ai-curated-newsletter-history`

**英語表記**: Execution History

### TooMuch原則

**定義**: 個人開発において複雑さ・コスト・運用負荷を最小限に抑える原則

**説明**:
本プロジェクトの絶対制約の一つ。以下を避ける：
- 過度な機能追加
- 複雑な設計
- 高コストなインフラ
- 手動運用が必要な機能

**判断基準**:
> これは本当に通知する価値があるか？

**関連用語**:
- [出力最小主義](#出力最小主義): 通知件数を増やさない
- [MVP](#mvp): 必要最小限の機能のみ実装

**使用例**:
- 「TooMuch原則に従い、この機能は実装しない」
- 「TooMuch原則により、月額コストを$10以内に抑える」

**PRD参照**: [プロダクト要求定義書](./product-requirements.md#絶対制約)

**英語表記**: TooMuch Principle

### 候補選定

**定義**: Buzzスコアでソートし、上位最大100件をLLM判定対象として選定するプロセス

**説明**:
重複排除後の記事をBuzzスコア順にソートし、上位最大100件をLLM判定に回す。これによりLLM判定コストを制御する。

**選定基準**:
1. Buzzスコアでソート（降順）
2. 上位最大100件を選定
3. キャッシュヒットは除外（再判定禁止）

**関連用語**:
- [Buzzスコア](#buzzスコア): 候補選定のソートキー
- [最終選定](#最終選定): LLM判定後、最大15件への絞り込み

**使用例**:
- 「候補選定により、LLM判定対象を100件以内に制限する」
- 「候補選定はBuzzスコア順で実行する」

**実装箇所**: `src/services/candidate_selector.py`

**英語表記**: Candidate Selection

### 最終選定

**定義**: LLM判定済みの記事をComposite Scoreで統合的にソートし、最大15件に絞り込むプロセス

**説明**:
LLM判定済みの記事をComposite Scoreで統合的にソートし、最大15件に絞り込む：

**Composite Score方式**:
```
composite = 0.4 × LABEL_SCORE[label] + 0.6 × normalized_external_buzz

LABEL_SCORE:
- ACT_NOW: 100
- THINK: 60
- FYI: 20
- IGNORE: 0
```

**ソート順**:
1. Composite Score降順
2. 鮮度（judged_at降順）
3. Confidence降順

**選定ルール**:
- IGNOREは除外
- Composite Score順で上位15件を選定
- ドメイン偏り制御（max_per_domain > 0のとき適用）

**関連用語**:
- [候補選定](#候補選定): LLM判定前の選定（最大100件）
- [出力最小主義](#出力最小主義): 最大15件の根拠
- [Composite Score](#composite-score): 最終選定のランキングスコア

**使用例**:
- 「最終選定により、通知件数を15件以内に制限する」
- 「最終選定では、Composite Score降順で記事をソートする」

**実装箇所**: `src/services/final_selector.py`

**英語表記**: Final Selection

### Composite Score

**定義**: InterestLabelと外部話題性を重み付き混合した統合スコア（0-100）

**説明**:
FinalSelectorで使用される記事の最終的なランキングスコア。LLMが判定したInterestLabelのスコア化値と、BuzzScoreからinterest成分を除外した外部話題性（external_buzz）を組み合わせて算出する。

**計算式**:
```
composite = α × LABEL_SCORE[label] + (1-α) × normalized_external_buzz

where:
  α = 0.4（InterestLabel側の重み）
  LABEL_SCORE = {ACT_NOW: 100, THINK: 60, FYI: 20, IGNORE: 0}
  normalized_external_buzz = BuzzScore.external_buzz（0-100）
```

**関連用語**:
- [Interest Label](#interest-label): Composite Scoreの構成要素（40%）
- [Buzzスコア](#buzzスコア): external_buzzがComposite Scoreの構成要素（60%）
- [最終選定](#最終選定): Composite Scoreでソートして選定

**使用例**:
- 「Composite Score降順で記事をソートし、上位15件を選定する」
- 「ACT_NOW + 高いexternal_buzzの記事はComposite Scoreが最も高くなる」

**実装箇所**: `src/services/final_selector.py` の `_calculate_composite_score()`

**英語表記**: Composite Score

---

## 技術用語

プロジェクトで使用している技術・フレームワーク・ツールに関する用語。

### uv

**定義**: Rust製の超高速Pythonパッケージマネージャー

**公式サイト**: https://github.com/astral-sh/uv

**本プロジェクトでの用途**:
依存関係の管理とインストール。Poetry比で10-100倍高速な依存解決を実現。

**バージョン**: 0.1+

**選定理由**:
- 超高速な依存解決（Rust製、Poetry比10-100倍）
- pip/pip-tools互換
- pyproject.toml（PEP 621）対応
- Astral社製（ruffと同じ開発元）

**代替技術**:
- Poetry: 依存解決が遅い
- pip-tools: 機能が限定的

**主要コマンド**:
```bash
# 依存関係のインストール
uv pip install -e ".[dev]"

# requirements.txt 生成
uv pip compile pyproject.toml -o requirements.txt

# 依存関係の更新
uv pip compile --upgrade pyproject.toml -o requirements.txt
```

**関連ドキュメント**:
- [アーキテクチャ設計書](./architecture.md#依存関係管理)
- [開発ガイドライン](./development-guidelines.md#依存関係管理)

**設定ファイル**: `pyproject.toml`

### moto

**定義**: AWSサービスをモックするPythonライブラリ

**公式サイト**: https://github.com/getmoto/moto

**本プロジェクトでの用途**:
統合テストでDynamoDB、SES、Bedrockをモック化。Docker不要でAWSサービスをローカルテスト可能。

**バージョン**: 5.0+

**選定理由**:
- Docker不要（LocalStackと比較）
- pytest統合が簡単
- TooMuch原則に準拠（複雑さ最小）

**代替技術**:
- LocalStack: Docker必要、セットアップが複雑

**使用例**:
```python
from moto import mock_dynamodb
import boto3

@mock_dynamodb
def test_cache_repository():
    dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
    table = dynamodb.create_table(...)
    # テスト実行
```

**関連ドキュメント**:
- [アーキテクチャ設計書](./architecture.md#テスト戦略)
- [開発ガイドライン](./development-guidelines.md#統合テスト)

### structlog

**定義**: 構造化ログ（JSON形式）を出力するPythonライブラリ

**公式サイト**: https://www.structlog.org/

**本プロジェクトでの用途**:
CloudWatch Logsに構造化ログを出力。run_id単位でログを追跡可能。

**バージョン**: 24.1+

**選定理由**:
- JSON形式でログ出力（CloudWatch Logs Insightsで検索しやすい）
- 構造化データによる高度なフィルタリング
- Python標準loggingとの統合

**使用例**:
```python
import structlog

logger = structlog.get_logger()

logger.info(
    "orchestrator_started",
    run_id=run_id,
    dry_run=dry_run
)
```

**関連ドキュメント**:
- [開発ガイドライン](./development-guidelines.md#ログ出力)

### feedparser

**定義**: RSS/Atomフィードを解析するPythonライブラリ

**公式サイト**: https://github.com/kurtmckee/feedparser

**本プロジェクトでの用途**:
収集元マスタに定義されたRSS/AtomフィードのURL、タイトル、公開日時等を解析。

**バージョン**: 6.0+

**選定理由**:
- Python標準的なフィードパーサー
- 広範なフォーマット対応（RSS 1.0, 2.0, Atom）
- 安定性が高い

**使用例**:
```python
import feedparser

feed = feedparser.parse("https://news.ycombinator.com/rss")
for entry in feed.entries:
    print(entry.title, entry.link, entry.published)
```

**実装箇所**: `src/services/collector.py`

### AWS Lambda

**定義**: サーバーレスコンピューティングサービス（AWS）

**公式サイト**: https://aws.amazon.com/lambda/

**本プロジェクトでの用途**:
ニュースレター実行環境。EventBridgeから週2-3回実行される。

**設定**:
- ランタイム: Python 3.14
- メモリ: 1024MB
- タイムアウト: 15分（900秒）
- 同時実行数: 1

**選定理由**:
- サーバーレス（運用負荷ゼロ）
- 実行時のみ課金（週2-3回実行で月$1程度）
- 15分のタイムアウト（10分の処理時間に対応可能）

**関連ドキュメント**:
- [アーキテクチャ設計書](./architecture.md#AWS-Lambda)

### DynamoDB

**定義**: フルマネージドNoSQLデータベース（AWS）

**公式サイト**: https://aws.amazon.com/dynamodb/

**本プロジェクトでの用途**:
判定キャッシュと実行履歴の保存。

**テーブル**:
1. `ai-curated-newsletter-cache`: 判定キャッシュ
2. `ai-curated-newsletter-history`: 実行履歴

**課金モード**: オンデマンド（使用量に応じた自動スケール）

**選定理由**:
- サーバーレス（運用負荷ゼロ）
- 低レイテンシ
- オンデマンドモードで低コスト（月$0.50程度）

**関連ドキュメント**:
- [アーキテクチャ設計書](./architecture.md#DynamoDB)

### Bedrock

**定義**: AWSのマネージドLLMサービス

**公式サイト**: https://aws.amazon.com/bedrock/

**本プロジェクトでの用途**:
Claude Haiku 4.5によるLLM判定（Interest Label、要約、タグの生成）。

**使用モデル**: `anthropic.claude-haiku-4-5-20251001-v1:0`

**選定理由**:
- Claude Haiku 4.5へのマネージドアクセス
- JSON出力の信頼性
- AWSアカウント内で完結（セキュリティ）

**関連ドキュメント**:
- [アーキテクチャ設計書](./architecture.md#Bedrock)

### SES

**定義**: Amazon Simple Email Service - メール送信サービス（AWS）

**公式サイト**: https://aws.amazon.com/ses/

**本プロジェクトでの用途**:
ニュースレター通知メールの送信。

**選定理由**:
- 低コスト（$0.10/1000通）
- 高い到達率
- HTMLメール対応

**関連ドキュメント**:
- [アーキテクチャ設計書](./architecture.md#SES)

### SAM

**定義**: AWS Serverless Application Model - サーバーレスアプリケーションのIaC

**公式サイト**: https://aws.amazon.com/serverless/sam/

**本プロジェクトでの用途**:
Lambda、DynamoDB、EventBridgeのインフラ定義とデプロイ。

**主要コマンド**:
```bash
# ローカル実行
sam local invoke NewsletterFunction --event events/test_event.json

# ビルド
sam build

# デプロイ
sam deploy --guided
```

**設定ファイル**: `template.yaml`

**関連ドキュメント**:
- [アーキテクチャ設計書](./architecture.md#デプロイ戦略)

---

## 略語・頭字語

### PRD

**正式名称**: Product Requirements Document

**意味**: プロダクト要求定義書

**本プロジェクトでの使用**:
`docs/product-requirements.md` として管理。プロジェクトの要件、目的、成功指標を定義。

**関連ドキュメント**: [product-requirements.md](./product-requirements.md)

### MVP

**正式名称**: Minimum Viable Product

**意味**: 必要最小限の機能を持つプロダクト

**本プロジェクトでの使用**:
Phase 1として、RSS/Atom収集、LLM判定、メール通知の基本機能のみを実装。

**PRD参照**: [プロダクト要求定義書](./product-requirements.md#デリバリ段階)

### SRP

**正式名称**: Single Responsibility Principle

**意味**: 単一責務の原則

**本プロジェクトでの適用**:
各クラス・関数は1つの責務のみを持つ。変更理由が2つ以上ある場合は分割を検討。

**関連ドキュメント**: [開発ガイドライン](./development-guidelines.md#基本原則)

### RSS

**正式名称**: Really Simple Syndication

**意味**: Webサイトの更新情報を配信するフォーマット

**本プロジェクトでの使用**:
収集元マスタで定義されたRSSフィードから記事を収集。

### Atom

**正式名称**: Atom Syndication Format

**意味**: RSSの代替として開発されたフィードフォーマット

**本プロジェクトでの使用**:
RSSと同様に、収集元マスタで定義されたAtomフィードから記事を収集。

### TTL

**正式名称**: Time To Live

**意味**: データの有効期限

**本プロジェクトでの使用**:
実行履歴テーブルに90日のTTLを設定し、古いデータを自動削除。

### UTC

**正式名称**: Coordinated Universal Time

**意味**: 協定世界時

**本プロジェクトでの使用**:
全ての日時データはUTCで管理。タイムゾーン変換は通知時のみ。

---

## アーキテクチャ用語

システム設計・アーキテクチャに関する用語。

### レイヤードアーキテクチャ

**定義**: システムを役割ごとに複数の層に分割し、上位層から下位層への一方向の依存関係を持たせる設計パターン

**本プロジェクトでの適用**:

```
handler.py (Lambdaエントリーポイント)
    ↓
orchestrator/ (オーケストレーションレイヤー)
    ↓
services/ (サービスレイヤー: ビジネスロジック)
    ↓
repositories/ (データレイヤー: データ永続化)
    ↓
models/ (データモデル)
```

**各層の責務**:
- `handler.py`: Lambda イベント受信、Orchestrator呼び出し
- `orchestrator/`: 全体フロー制御
- `services/`: ビジネスロジック（収集、判定、通知等）
- `repositories/`: データ永続化（DynamoDB、S3）
- `models/`: データモデル（dataclass）

**依存関係のルール**:
- ✅ orchestrator → services
- ✅ services → repositories
- ✅ repositories → models
- ❌ repositories → services
- ❌ models → 任意のレイヤー

**メリット**:
- 関心の分離による保守性向上
- テストが容易（各層を独立してテスト可能）
- Phase 2移行時の変更範囲が限定的

**関連ドキュメント**:
- [アーキテクチャ設計書](./architecture.md#レイヤードアーキテクチャ)
- [リポジトリ構造定義書](./repository-structure.md#依存関係のルール)

### Orchestrator

**定義**: 全体フローを制御し、各サービスの呼び出し順序を管理するコンポーネント

**本プロジェクトでの役割**:
1. 収集（Collector）
2. 正規化（Normalizer）
3. 重複排除（Deduplicator）
4. Buzzスコア計算（BuzzScorer）
5. 候補選定（CandidateSelector）
6. LLM判定（LlmJudge）
7. 最終選定（FinalSelector）
8. フォーマット・通知（Formatter, Notifier）
9. 実行履歴保存（HistoryRepository）

上記9ステップを順次実行。

**実装箇所**: `src/orchestrator/orchestrator.py`

**関連用語**:
- [レイヤードアーキテクチャ](#レイヤードアーキテクチャ): Orchestratorはオーケストレーションレイヤー

**英語表記**: Orchestrator

### Collector

**定義**: 収集元マスタからRSS/Atomフィードを収集するサービス

**実装箇所**: `src/services/collector.py`

**英語表記**: Collector

### Phase 1 / Phase 2

**定義**: プロジェクトの実装フェーズ

**Phase 1（MVP）**:
- 単一Lambda構成
- 処理時間: 10分以内（目標）
- LLM判定対象: 最大100件

**Phase 2（将来）**:
- Step Functions構成（3つのLambda）
- S3によるデータ受け渡し
- 処理時間の制約緩和

**移行トリガー**:
- 実行時間が12分を超える
- 収集元が大幅に増える
- LLM判定対象を100件以上に拡大

**関連ドキュメント**:
- [アーキテクチャ設計書](./architecture.md#Phase-1--Phase-2)

---

## データモデル用語

データベース・データ構造に関する用語。

### Article

**定義**: 収集された記事のエンティティ

**主要フィールド**:
- `url`: 正規化されたURL（一意キー）
- `title`: 記事タイトル
- `published_at`: 公開日時（UTC）
- `source_name`: ソース名
- `description`: 記事の概要（最大800文字）
- `normalized_url`: 正規化前の元URL
- `collected_at`: 収集日時（UTC）

**実装**:
```python
@dataclass
class Article:
    url: str
    title: str
    published_at: datetime
    source_name: str
    description: str
    normalized_url: str
    collected_at: datetime
```

**実装箇所**: `src/models/article.py`

### JudgmentResult

**定義**: LLM判定結果のエンティティ

**主要フィールド**:
- `url`: 記事URL（キャッシュキー）
- `title`: 記事タイトル
- `description`: 記事の概要（最大800文字、RSS/Atomから取得、LLMプロンプトの入力として使用）
- `interest_label`: 関心度ラベル（ACT_NOW/THINK/FYI/IGNORE）
- `buzz_label`: 話題性ラベル（HIGH/MID/LOW）※LLMでは判定しない。BuzzScore.to_buzz_label()でOrchestratorが事後設定
- `confidence`: 信頼度（0.0-1.0）
- `summary`: LLM生成の要約（最大300文字、メール表示用）
- `tags`: 記事タグ（例: ["Kotlin", "Claude"]）
- `published_at`: 記事の公開日時（UTC）
- `model_id`: 使用したモデルID
- `judged_at`: 判定日時（UTC）

**実装**:
```python
@dataclass
class JudgmentResult:
    url: str
    title: str
    description: str
    interest_label: Literal["ACT_NOW", "THINK", "FYI", "IGNORE"]
    buzz_label: Literal["HIGH", "MID", "LOW"]
    confidence: float
    summary: str
    model_id: str
    judged_at: datetime
    published_at: datetime
    tags: list[str] = field(default_factory=list)
```

**実装箇所**: `src/models/judgment.py`

### ExecutionSummary

**定義**: ニュースレター実行のサマリエンティティ

**主要フィールド**:
- `run_id`: 実行ID（UUID）
- `executed_at`: 実行日時（UTC）
- `collected_count`: 収集件数
- `deduped_count`: 重複排除後の件数
- `llm_judged_count`: LLM判定件数
- `cache_hit_count`: キャッシュヒット件数
- `final_selected_count`: 最終選定件数
- `notification_sent`: 通知送信成功フラグ
- `execution_time_seconds`: 実行時間（秒）
- `estimated_cost_usd`: 推定コスト（USD）

**実装箇所**: `src/models/execution_summary.py`

### SourceConfig

**定義**: 収集元設定のエンティティ

**主要フィールド**:
- `source_id`: 収集元ID
- `name`: 収集元名
- `feed_url`: フィードURL
- `feed_type`: フィード種別（rss/atom）
- `priority`: 優先度（high/medium/low）
- `timeout_seconds`: タイムアウト時間（秒）
- `retry_count`: リトライ回数
- `enabled`: 有効フラグ

**実装箇所**: `src/models/source_config.py`

---

## エラー・例外

システムで定義されているエラーと例外。

### CollectionError

**クラス名**: `CollectionError`

**継承元**: `Exception`

**発生条件**:
RSS/Atomフィード収集時にHTTPエラー、タイムアウト、パースエラーが発生した場合。

**エラーメッセージフォーマット**:
```
Failed to collect from {source_name}: {original_error}
```

**対処方法**:
- ユーザー: なし（システムが自動的に他ソースを継続）
- 開発者: フィードURLの確認、タイムアウト設定の見直し

**実装箇所**: `src/shared/exceptions/collection_error.py`

**使用例**:
```python
try:
    response = httpx.get(source.feed_url, timeout=10)
except httpx.HTTPError as e:
    raise CollectionError(source.name, e)
```

### LlmError

**クラス名**: `LlmError`

**継承元**: `Exception`

**発生条件**:
LLM判定時にエラーが発生した場合。

**サブクラス**:
- `LlmJsonParseError`: LLM出力のJSON解析エラー
- `LlmTimeoutError`: LLMタイムアウトエラー

**対処方法**:
- ユーザー: なし（システムが自動的にIGNOREとして扱う）
- 開発者: プロンプトの見直し、タイムアウト設定の見直し

**実装箇所**: `src/shared/exceptions/llm_error.py`

### NotificationError

**クラス名**: `NotificationError`

**継承元**: `Exception`

**発生条件**:
メール送信時にSESエラーが発生した場合。

**対処方法**:
- ユーザー: なし（開発者に通知）
- 開発者: SES設定の確認、メールアドレスの検証状態確認

**実装箇所**: `src/shared/exceptions/notification_error.py`

---

## 計算・アルゴリズム

特定の計算方法やアルゴリズムに関する用語。

### Buzzスコア計算アルゴリズム

**定義**: 記事の話題性を定量化する計算式

**計算式**:
```
total_score = (social_proof × 0.55) + (interest × 0.35) + (authority × 0.10)

where:
  # SocialProof 4指標統合スコア（55%）
  social_proof_score = yamadashy × 0.05 + hatena × 0.45 + zenn × 0.35 + qiita × 0.15

  # Interest 5段階マッチングスコア（35%）
  interest_score = max: 100, high: 80, medium: 55, low: 30, ignore: 0, デフォルト: 15

  # Authority スコア（10%）
  authority_score = OFFICIAL: 100, HIGH: 80, MEDIUM: 50, LOW/未設定: 0
```

**実装箇所**: `src/services/buzz_scorer.py`

**例**:
```
# 例1: social_proof=60, interest=80（high_interest一致）, authority=50（MEDIUM）
total_score = (60 × 0.55) + (80 × 0.35) + (50 × 0.10) = 33 + 28 + 5 = 66

# 例2: social_proof=90, interest=100（max_interest一致）, authority=100（OFFICIAL）
total_score = (90 × 0.55) + (100 × 0.35) + (100 × 0.10) = 49.5 + 35 + 10 = 94.5
```

**関連用語**:
- [Buzzスコア](#buzzスコア): このアルゴリズムで計算されるスコア
- [候補選定](#候補選定): Buzzスコアでソートして上位を選定

---

## 索引

### あ行
- [Atom](#atom) - 略語
- [Orchestrator](#orchestrator) - アーキテクチャ用語

### か行
- [鮮度スコア](#鮮度スコア) - ドメイン用語
- [候補選定](#候補選定) - ドメイン用語
- [Collector](#collector) - アーキテクチャ用語
- [CollectionError](#collectionerror) - エラー・例外

### さ行
- [再判定禁止](#再判定禁止) - ドメイン用語
- [最終選定](#最終選定) - ドメイン用語
- [収集元マスタ](#収集元マスタ) - ドメイン用語
- [出力最小主義](#出力最小主義) - ドメイン用語
- [実行履歴](#実行履歴) - ドメイン用語
- [structlog](#structlog) - 技術用語
- [SES](#ses) - 技術用語
- [SAM](#sam) - 技術用語
- [SRP](#srp) - 略語

### た行
- [TooMuch原則](#toomuch原則) - ドメイン用語
- [DynamoDB](#dynamodb) - 技術用語
- [TTL](#ttl) - 略語

### は行
- [Buzzスコア](#buzzスコア) - ドメイン用語
- [Buzzスコア計算アルゴリズム](#buzzスコア計算アルゴリズム) - 計算・アルゴリズム
- [Buzz Label](#buzz-label) - ドメイン用語
- [Bedrock](#bedrock) - 技術用語
- [判定キャッシュ](#判定キャッシュ) - ドメイン用語
- [Phase 1 / Phase 2](#phase-1--phase-2) - アーキテクチャ用語
- [feedparser](#feedparser) - 技術用語

### ま行
- [moto](#moto) - 技術用語
- [MVP](#mvp) - 略語

### ら行
- [LLM判断器](#llm判断器) - ドメイン用語
- [LlmError](#llmerror) - エラー・例外
- [レイヤードアーキテクチャ](#レイヤードアーキテクチャ) - アーキテクチャ用語
- [RSS](#rss) - 略語

### A-Z
- [Article](#article) - データモデル用語
- [AWS Lambda](#aws-lambda) - 技術用語
- [Composite Score](#composite-score) - ドメイン用語
- [ExecutionSummary](#executionsummary) - データモデル用語
- [Interest Label](#interest-label) - ドメイン用語
- [JudgmentResult](#judgmentresult) - データモデル用語
- [NotificationError](#notificationerror) - エラー・例外
- [PRD](#prd) - 略語
- [SourceConfig](#sourceconfig) - データモデル用語
- [UTC](#utc) - 略語
- [uv](#uv) - 技術用語

---

## 変更履歴

| 日付 | 変更内容 | 更新者 |
|------|---------|--------|
| 2026-02-18 | BuzzScore計算体系を3要素に更新、Composite Score方式追加、LLM出力フォーマット更新（summary/tags）、候補数150→100 | システム |
| 2025-01-15 | 初版作成 | システム |
