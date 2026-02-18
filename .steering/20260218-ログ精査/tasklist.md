# タスクリスト: ログ精査

## フェーズ1: .env / .env.local 分離

- [x] .env.local ファイルを作成（現在の.envからローカル固有設定を移動）
  - [x] RED: config.pyの.env.local読み込みテストを書く
  - [x] GREEN: config.pyに.env.local読み込みロジックを実装
  - [x] REFACTOR: コードを整理
- [x] .env を共通設定・本番デフォルトとして整理
- [x] .env.example を更新（.env と .env.local の説明を追加）
- [x] .gitignore に .env.local が含まれていることを確認
- [x] lint/format/型チェックがすべて通る

## フェーズ2: INFOログのDEBUG降格（24箇所）

- [x] orchestrator.py: 5箇所のINFO→DEBUG降格
  - step5_5_complete, step7_start, step7_complete(dry_run後), step8_start, step8_complete
- [x] final_selector.py: 3箇所のINFO→DEBUG降格
  - final_selection_start, final_candidate(個別), article_selected(個別)
- [x] サービス層の *_start ログ降格（8箇所）
  - buzz_scorer.py, normalizer.py, deduplicator.py(2箇所), notifier.py(2箇所), formatter.py, candidate_selector.py
- [x] collector.py, llm_judge.py の *_start ログ降格（2箇所）
- [x] config.py: 3箇所のINFO→DEBUG降格
  - loading_config_from_local_env, loading_config_from_ssm, ssm_dotenv_loaded
- [x] handler.py: 2箇所のINFO→DEBUG降格
  - config_loaded, event_parsed
- [x] repositories/interest_master.py: 1箇所のINFO→DEBUG降格
- [x] repositories/history_repository.py: 1箇所のINFO→DEBUG降格
- [x] social_proof/*.py: 5箇所の *_start ログ降格 + external_service_policy.py: 1箇所降格
- [x] lint/format/型チェックがすべて通る

## フェーズ3: トークン数ログの追加

- [x] llm_judge.py: Bedrockレスポンスからトークン数を抽出
  - [x] RED: _judge_singleでトークン数がDEBUGログに出力されるテストを書く
  - [x] GREEN: response_body["usage"]からinput_tokens/output_tokensを抽出しDEBUGログ出力
  - [x] REFACTOR: コードを整理
- [x] llm_judge.py: バッチ全体の合計トークン数をINFOログに追加
  - [x] RED: judge_batchで合計トークン数がINFOログに出力されるテストを書く
  - [x] GREEN: バッチ内のトークン数を集計しINFOログに追加
  - [x] REFACTOR: コードを整理
- [x] lint/format/型チェックがすべて通る

## フェーズ4: 外部サービス応答時間のログ追加

- [x] collector.py: 収集全体の応答時間を既存INFOログに追加
- [x] llm_judge.py: LLM判定全体の応答時間を既存INFOログに追加
- [x] notifier.py: メール送信の応答時間を既存INFOログに追加
- [x] social_proof/hatena_count_fetcher.py: はてブAPI応答時間を既存INFOログに追加
- [x] lint/format/型チェックがすべて通る

## フェーズ5: 最終検証

- [x] 全テスト実行（pytest tests/ -v）: 237 passed, coverage 90.69%
- [x] ruff check & format: All checks passed!
- [x] mypy 型チェック: Success: no issues found in 46 source files
- [x] ~~ローカル実行で DEBUG ログが出ることを確認~~（任意: スキップ）

---

## 実装後の振り返り

- **実装完了日**: 2026-02-18
- **計画と実績の差分**:
  - フェーズ4のllm_judge.pyで、`judge_batch`内の結果集約ロジックを `_aggregate_results` メソッドに抽出するリファクタリングが追加で行われた（サブエージェント判断）
  - 計画の26箇所のINFO→DEBUG降格は実質的にほぼ計画通り完了
- **学んだこと**:
  - asyncioでのインスタンス変数蓄積パターン（`_batch_input_tokens`/`_batch_output_tokens`）は、await点がない加算操作なら安全に使える
  - `python-dotenv` の `load_dotenv(override=True)` で .env.local の上書きが簡潔に実現できる
  - 既存INFOログへの `elapsed_seconds` フィールド追加は、テストで `assert_any_call` の厳密マッチが壊れるため注意が必要
- **次回への改善提案**:
  - ログレベル設計は最初から方針を決めておくと後からの大量変更を避けられる
  - 外部サービス応答時間はデコレータ化するとDRYになる可能性がある
- **申し送り事項**:
  - 本番デプロイ時、SSM Parameter Store の `LOG_LEVEL` が `INFO` であることを確認すること
  - `.env` のデフォルト `LOG_LEVEL=INFO` が本番環境で適切であることを確認済み
