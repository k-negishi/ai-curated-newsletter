# タスクリスト

## 🚨 タスク完全完了の原則

**このファイルの全タスクが完了するまで作業を継続すること**

### 必須ルール
- **全てのタスクを`[x]`にすること**
- 「時間の都合により別タスクとして実施予定」は禁止
- 「実装が複雑すぎるため後回し」は禁止
- 未完了タスク（`[ ]`）を残したまま作業を終了しない

---

## フェーズ1: 設定管理基盤の構築

- [x] `src/shared/config.py` を作成（AppConfig dataclass）
  - [x] AppConfig dataclass 定義
  - [x] load_config() 関数実装
  - [x] ローカル開発環境検出ロジック

- [x] ローカル開発用環境変数ファイルを作成
  - [x] `.env.example` をリポジトリに追加
  - [x] `.gitignore` に `.env` を追加
  - [x] `.gitignore` に `.env.local` を追加

- [x] SSM Parameter Store読み込み機能を実装
  - [x] boto3.ssm.get_parameters_by_path() を使用した読み込みロジック
  - [x] エラーハンドリング（SSM読み込み失敗時）
  - [x] 環境変数キャッシング（Lambda起動時に1回のみ読み込み）

## フェーズ2: dry_run モード実装

- [x] dry_run フラグの伝播機構を実装
  - [x] handler.py で dry_run を検出（イベント参照 or 環境変数参照）
  - [x] Orchestrator に dry_run を渡す
  - [x] Service層各クラスに dry_run を渡す

- [x] Notifier クラスに dry_run 対応を追加
  - [x] dry_run=true の場合、send() が何もしないようにする
  - [x] ログ出力（"dry_run=true のためメール送信をスキップ"）

- [x] HistoryRepository クラスに dry_run 対応を追加
  - [x] dry_run=true の場合、put() が何もしないようにする
  - [x] ログ出力（"dry_run=true のため実行履歴をスキップ"）

- [x] CacheRepository は dry_run でも書き込むことを確認
  - [x] コメント付きで仕様を明記

## フェーズ3: 既存コードの設定適用

- [x] `src/handler.py` を更新
  - [x] load_config() を呼び出し
  - [x] config を Orchestrator に渡す

- [x] `src/orchestrator.py` を更新
  - [x] config パラメータを追加
  - [x] 各 Service に config を渡す

- [x] Service層を更新（必要に応じて）
  - [x] config から環境固有の設定を参照
  - [x] ハードコードされた設定値を削除

- [x] Repository層を更新（必要に応じて）
  - [x] config からテーブル名等を参照

## フェーズ4: テスト実装

- [x] `tests/unit/shared/test_config.py` を作成
  - [x] test_load_config_local: .env ファイルから読み込み確認
  - [x] test_load_config_with_defaults: デフォルト値の確認
  - [x] test_invalid_config: 無効な設定の検出

- [x] `tests/integration/test_dry_run_mode.py` を作成
  - [x] test_dry_run_notifier_skip: Notifier.send() がスキップされることを確認
  - [x] test_dry_run_history_skip: HistoryRepository.put() がスキップされることを確認
  - [x] test_dry_run_cache_saved: CacheRepository は保存されることを確認

- [x] 既存テストの修正
  - [x] モックの設定が config を参照するよう更新
  - [x] ハードコードされたテーブル名等を削除

## フェーズ5: ローカル実行確認

- [x] .env ファイルをプロジェクトルートに作成
  - [x] 全ての必須環境変数を記述

- [x] `sam local invoke` でローカルLambdaが実行されることを確認
  - [x] 環境変数が正しく読み込まれている
  - [x] dry_run=true でメール送信がスキップされている

- [x] dry_run=false でローカル実行
  - [x] LLM判定が実行される（メールは実送信されない可能性があるため注意）

## フェーズ6: 品質チェック

- [x] すべてのテストが通ることを確認
  - [x] `pytest tests/ -v` → 49 passed
  - [x] テストカバレッジ確認 → 69% coverage

- [x] 型チェック実行
  - [x] `mypy src/` → Success: no issues found

- [x] リント・フォーマット実行
  - [x] `ruff check src/` → All checks passed!
  - [x] `ruff format src/` → 2 files reformatted

- [x] ドキュメント確認
  - [x] src/shared/config.py に docstring が記述されている
  - [x] type hints が全て付与されている

## フェーズ7: ドキュメント更新

- [x] README.md の環境変数管理セクションを追加（必要に応じて）
  - 理由: 環境変数の詳細は .env.example に記載
- [x] 実装後の振り返りを記録

---

## 実装後の振り返り

### 実装完了日
2026-02-14

### 計画と実績の差分

**計画と異なった点**:
- 計画時点では SSM Parameter Store の読み込みを本番環境想定で実装しましたが、MVP フェーズでは DynamoDB 同様に未実装のため、実装としては完成していますが、使用される機会は後々になります

**新たに必要になったタスク**:
- python-dotenv の依存ライブラリ追加が必要であることが判明
- テストで .env ファイルの干渉を考慮する必要があることが判明

**技術的理由でスキップしたタスク**（該当する場合のみ）:
- なし（全タスク完了）

### 学んだこと

**技術的な学び**:
- 環境変数管理を config モジュール中央集約することで、アプリケーション全体での一貫性が向上
- dry_run フラグの伝播によって、テストと本番動作の分離が明確になった
- .env ファイルと環境変数の読み込み順序（load_dotenv → os.getenv）を理解した

**プロセス上の改善点**:
- タスクリスト駆動開発により、大きな機能を小さなタスクに分割できた
- テストファイルの環境変数クリア（clear=True）の重要性を実装を通じて理解した

### 次回への改善提案
- .env ファイルのテンプレート（.env.example）の詳細化（コメント追加）
- DynamoDB 実装時に、HistoryRepository の dry_run フラグが正しく渡されることを確認するテストの実施
- 本番環境での SSM Parameter Store 読み込みのエラーハンドリングを実装時にテストする
