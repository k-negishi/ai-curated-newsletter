# タスクリスト

## Issue情報
- **Issue URL**: https://github.com/k-negishi/ai-curated-newsletter/issues/24
- **タイトル**: Bedrock インファレンスプロファイルARNに対応する

## 実装タスク

### Phase 1: 設定とコード変更

- [x] **環境変数の追加**
  - [x] `.env` に `BEDROCK_INFERENCE_PROFILE_ARN` を追加
  - [x] `.env.example` に `BEDROCK_INFERENCE_PROFILE_ARN` のサンプル追加（コメント付き）

- [x] **config.py の変更**
  - [x] `bedrock_inference_profile_arn` 設定を追加
  - [x] 環境変数から読み込む（デフォルト値は空文字列）

- [x] **llm_judge.py の変更**
  - [x] コンストラクタで `inference_profile_arn` を受け取る
  - [x] `invoke_model` の `modelId` パラメータを条件分岐
    - inference_profile_arn が設定されていればそれを使用
    - 未設定なら従来通り model_id を使用

- [x] **handler.py の変更**
  - [x] `LlmJudge` 初期化時に `inference_profile_arn` を渡す

### Phase 2: テストと検証

- [x] **ユニットテスト追加/更新**
  - [x] `test_llm_judge.py` にインファレンスプロファイルARN使用時のテストを追加
  - [x] `test_config.py` で新しい設定項目をテスト

- [x] **品質チェック**
  - [x] `pytest tests/ -v` 実行
  - [x] `ruff check src/` 実行
  - [x] `ruff format src/` 実行
  - [x] `mypy src/` 実行（変更ファイルのみ）

- [ ] **ローカル動作確認**
  - [ ] `.env` にインファレンスプロファイルARNを設定
  - [ ] `./run_local.sh` でdry_runモード実行
  - [ ] ValidationExceptionが発生しないことを確認
  - [ ] LLM判定が正常に動作することを確認

### Phase 3: ドキュメント更新

- [ ] **architecture.md 更新**
  - [ ] インファレンスプロファイルARN対応について記載
  - [ ] モデルID vs インファレンスプロファイルARNの使い分けを説明

- [ ] **README.md 更新（必要に応じて）**
  - [ ] 環境変数の説明にインファレンスプロファイルARNを追加

### Phase 4: コミットとクローズ

- [ ] **変更をコミット**
  - [ ] 適切なコミットメッセージで変更をコミット

- [ ] **Issue #24 をクローズ**
  - [ ] 動作確認完了後、issueをクローズ

## メモ

**インファレンスプロファイルARNの形式:**
```
arn:aws:bedrock:ap-northeast-1::inference-profile/anthropic.claude-haiku-4-5-20251001-v1:0
```

**設計方針:**
- 既存の `model_id` 設定は維持（後方互換性）
- `inference_profile_arn` が設定されていればそちらを優先
- 未設定の場合は従来通り `model_id` を使用

**コスト:**
- インファレンスプロファイルARN使用による追加コストなし
- Haiku 4.5: 120記事で約$0.19（Sonnet比 83%削減）
