# 設計書

## GitHub Issue

https://github.com/k-negishi/ai-curated-newsletter/issues/49

### issue 内容
- **タイトル**: メールが配信されてない
- **本文**: Lambda実行ログ（添付ファイル）
- **ラベル**: なし

### 調査結果の要約

Lambda関数がBedrock APIを呼び出す際に、以下のエラーが発生：

```
ValidationException: Invocation of model ID anthropic.claude-haiku-4-5-20251001-v1:0
with on-demand throughput isn't supported. Retry your request with the ID or ARN of
an inference profile that contains this model.
```

**根本原因:**
- **ローカル環境**: `.env.local`で`BEDROCK_INFERENCE_PROFILE_ARN`が設定されている → 正常動作
- **Lambda環境**: `template.yaml`に環境変数設定がない → ValidationException発生

LLM判定が全件失敗 → 全記事がIGNORE判定 → 選抜記事0件 → メール未送信

---

## アーキテクチャ概要

今回の修正は、**Lambda環境の設定変更**のみで、コード変更は不要です。

**修正箇所:**
- `template.yaml`: 環境変数とIAM権限の追加

**影響範囲:**
- Lambda環境の設定のみ
- コード変更なし（既に実装済み）
- テストコードへの影響なし

```
┌─────────────────────────────────────────────────┐
│ template.yaml                                    │
│ ┌─────────────────────────────────────────────┐ │
│ │ Environment.Variables (追加)                 │ │
│ │  - BEDROCK_INFERENCE_PROFILE_ARN            │ │
│ └─────────────────────────────────────────────┘ │
│ ┌─────────────────────────────────────────────┐ │
│ │ IAM Policies (追加)                         │ │
│ │  - bedrock:InvokeModel (inference-profile) │ │
│ └─────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────┘
```

---

## コンポーネント設計

### 1. 環境変数設定

**責務**:
- Lambda環境で`BEDROCK_INFERENCE_PROFILE_ARN`を設定
- ローカル環境との設定の一致を保証

**実装の要点**:
- CloudFormation組み込み関数（`!Sub`）を使用してARNを動的に生成
- アカウントIDとリージョンを自動的に取得
- inference profileは`jp.anthropic.claude-haiku-4-5-20251001-v1:0`を使用

**設定値:**
```yaml
BEDROCK_INFERENCE_PROFILE_ARN: !Sub 'arn:aws:bedrock:${AWS::Region}:${AWS::AccountId}:inference-profile/jp.anthropic.claude-haiku-4-5-20251001-v1:0'
```

### 2. IAM権限設定

**責務**:
- inference profileリソースへのアクセス権を付与
- 既存の`foundation-model`権限と併用

**実装の要点**:
- `bedrock:InvokeModel`アクションを`inference-profile` ARNにも適用
- ワイルドカードパターンで複数のinference profileをサポート
- セキュリティ: Claude Haikuモデルのみに限定

**IAM Policy:**
```yaml
Resource:
  - !Sub 'arn:aws:bedrock:${AWS::Region}::foundation-model/anthropic.claude-haiku-4-5*'
  - !Sub 'arn:aws:bedrock:${AWS::Region}:${AWS::AccountId}:inference-profile/*anthropic.claude-haiku-4-5*'
```

---

## データフロー

### Lambda起動からBedrock呼び出しまで

```
1. Lambda関数起動
   ↓
2. config.py: 環境変数BEDROCK_INFERENCE_PROFILE_ARNを読み込み
   - Lambda環境: template.yamlから取得
   - ローカル環境: .env.localから取得
   ↓
3. handler.py: LlmJudgeを初期化（inference_profile_arnを渡す）
   ↓
4. llm_judge.py: 条件分岐
   - inference_profile_arn が設定されている → ARNを使用
   - 設定されていない → model_idを直接使用（今回のエラー原因）
   ↓
5. Bedrock API呼び出し
   - modelId: arn:aws:bedrock:ap-northeast-1:{AccountId}:inference-profile/jp.anthropic.claude-haiku-4-5-20251001-v1:0
   ↓
6. LLM判定成功 → 記事選抜 → メール送信
```

---

## エラーハンドリング戦略

### ValidationException

**現在の実装:**
- `llm_judge.py`でValidationExceptionを捕捉
- リトライ対象外として処理（ThrottlingExceptionのみリトライ）
- フォールバック: 記事をIGNORE判定に変更

**今回の修正後:**
- ValidationExceptionが発生しない（inference profileを使用）
- LLM判定が成功するようになる

---

## テスト戦略

### 手動テスト（ローカル実行）

**実行方法:**
```bash
# 1. .env.localの設定確認
cat .env.local | grep BEDROCK_INFERENCE_PROFILE_ARN

# 2. ローカル実行（dry_runモード推奨）
./run_local.sh
# → dry_runモードを選択

# 3. 実行結果確認
# - LLM判定が成功すること
# - final_selected_count が 0 でないこと
# - ValidationException が発生しないこと
```

**期待される結果:**
- LLM判定が全て成功
- 記事が適切に選抜される（10-15件程度）
- メール送信処理が実行される（dry_runモードでは実際には送信されない）

### デプロイ後の動作確認

**確認方法:**
```bash
# 1. SAM deploy実行
sam deploy --config-file samconfig.toml

# 2. Lambda環境変数の確認
aws lambda get-function-configuration --function-name ai-curated-newsletter \
  --query 'Environment.Variables.BEDROCK_INFERENCE_PROFILE_ARN'

# 3. Lambda手動実行（dry_runモード）
aws lambda invoke --function-name ai-curated-newsletter \
  --payload '{"dry_run": true}' \
  response.json

# 4. CloudWatch Logsで確認
# - ValidationExceptionが発生していないこと
# - LLM判定が成功していること
# - final_selected_countが0でないこと
```

---

## 依存ライブラリ

既存のライブラリのみ使用。新規追加なし。

---

## ディレクトリ構造

```
.
├── template.yaml                    # 修正対象
├── .env                             # 変更なし
├── .env.local                       # 変更なし（既に設定済み）
└── src/
    ├── handler.py                   # 変更なし（既に実装済み）
    ├── shared/
    │   └── config.py                # 変更なし（既に実装済み）
    └── services/
        └── llm_judge.py             # 変更なし（既に実装済み）
```

---

## 実装の順序

1. `template.yaml`の環境変数を追加
2. `template.yaml`のIAM権限を追加
3. ローカル実行で動作確認（dry_runモード）
4. SAM deployでLambda環境にデプロイ
5. Lambda環境での動作確認

---

## セキュリティ考慮事項

- **最小権限の原則**: Claude Haikuモデルのみにアクセス権を限定
- **認証情報の管理**: inference profile ARNは環境変数で管理（ハードコードしない）
- **アカウントID**: CloudFormation組み込み関数で動的に取得（セキュアな運用）

---

## パフォーマンス考慮事項

- **影響なし**: 設定変更のみで、パフォーマンスへの影響はない
- **コスト**: inference profileの使用による追加コストはない（モデルは同じ）

---

## 将来の拡張性

- **他のモデルへの対応**: inference profileのパターンをワイルドカードで指定済み
- **リージョン対応**: `${AWS::Region}`で動的に取得済み
- **マルチアカウント対応**: `${AWS::AccountId}`で動的に取得済み
