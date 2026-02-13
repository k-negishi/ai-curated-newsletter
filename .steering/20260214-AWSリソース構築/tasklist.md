# タスクリスト

## 🚨 タスク完全完了の原則

**このファイルの全タスクが完了するまで作業を継続すること**

### 必須ルール
- **全てのタスクを`[x]`にすること**
- 「時間の都合により別タスクとして実施予定」は禁止
- 「実装が複雑すぎるため後回し」は禁止
- 未完了タスク（`[ ]`）を残したまま作業を終了しない

---

## フェーズ1: DynamoDB テーブル構築

- [ ] キャッシュテーブル (`ai-curated-newsletter-cache`) を作成
  - [ ] テーブル名、PK/SK を正しく設定
  - [ ] オンデマンド課金モードを設定
  - [ ] Point-in-Time Recovery を有効化（35日間）
  - [ ] AWS マネジメントコンソールまたは CloudFormation で作成確認

- [ ] 履歴テーブル (`ai-curated-newsletter-history`) を作成
  - [ ] テーブル名、PK/SK を正しく設定
  - [ ] オンデマンド課金モードを設定
  - [ ] TTL を設定（`ttl` 属性、90日自動削除）
  - [ ] 作成確認

- [ ] DynamoDB ローカルテスト
  - [ ] `sam local invoke` でテーブルアクセスが可能か確認
  - [ ] 書き込み・読み込みがエラーなく実行できることを確認

## フェーズ2: SES セットアップ

- [ ] SES で送信元メールアドレスを検証
  - [ ] AWS マネジメントコンソール → SES → Verified identities
  - [ ] `Verified` ステータスになることを確認
  - [ ] 検証メール受信・クリック完了

- [ ] サンドボックスモード解除を申請（オプション）
  - [ ] AWS Support に申請
  - [ ] または自動でクォーター引き上げ申請
  - [ ] 解除されるまで待機（通常 1-2 日）

- [ ] テストメール送信
  - [ ] boto3 で `send_email()` を呼び出し
  - [ ] テストメール受信確認
  - [ ] ログに成功メッセージが出力されることを確認

## フェーズ3: Bedrock 確認

- [ ] Claude 3.5 Sonnet へのアクセス確認
  - [ ] AWS マネジメントコンソール → Bedrock
  - [ ] リージョン: `us-east-1` を選択
  - [ ] モデル: `anthropic.claude-3-5-sonnet-20241022-v2:0` が利用可能か確認

- [ ] Bedrock API テスト
  - [ ] boto3 で `invoke_model()` を呼び出し
  - [ ] JSON レスポンスが正しく返されることを確認
  - [ ] モデル ID が正しいことを確認

## フェーズ4: Secrets Manager セットアップ

- [ ] Secrets Manager にメール機密情報を保存
  - [ ] シークレット名: `/ai-curated-newsletter/email`
  - [ ] `from_address` と `to_address` を JSON で保存
  - [ ] KMS 暗号化を有効化

- [ ] boto3 でシークレット取得テスト
  - [ ] `get_secret_value()` を呼び出し
  - [ ] JSON パース成功
  - [ ] 値が正しく取得されることを確認

## フェーズ5: IAM ロール・ポリシー作成

- [ ] IAM ロール (`NewsletterLambdaExecutionRole`) を作成
  - [ ] 信頼関係: Lambda service を設定
  - [ ] 基本的な CloudWatch Logs ポリシーを自動アタッチ

- [ ] DynamoDB アクセスポリシーを追加
  - [ ] GetItem, PutItem, BatchGetItem, Query を許可
  - [ ] 対象テーブル: 2つの DynamoDB テーブルのみ
  - [ ] ポリシーが正しくアタッチされることを確認

- [ ] Bedrock アクセスポリシーを追加
  - [ ] bedrock:InvokeModel を許可
  - [ ] リソース: Claude 3.5 Sonnet のみ
  - [ ] ポリシーが正しくアタッチされることを確認

- [ ] SES アクセスポリシーを追加
  - [ ] ses:SendEmail を許可
  - [ ] 条件: FromAddress を検証済みメールアドレスのみに制限
  - [ ] ポリシーが正しくアタッチされることを確認

- [ ] Secrets Manager アクセスポリシーを追加
  - [ ] secretsmanager:GetSecretValue を許可
  - [ ] リソース: `/ai-curated-newsletter/email` シークレットのみ
  - [ ] ポリシーが正しくアタッチされることを確認

## フェーズ6: EventBridge スケジュール設定

- [ ] EventBridge スケジュールルール (`ai-curated-newsletter-schedule`) を作成
  - [ ] スケジュール式: `cron(0 9 * * TUE,FRI *)`（火曜・金曜 09:00 UTC）
  - [ ] ルールが Enabled 状態であることを確認

- [ ] Lambda をターゲットとして登録
  - [ ] ターゲット: `NewsletterFunction`
  - [ ] 入力: JSON で `{"command": "run_newsletter", "dry_run": false}` を指定
  - [ ] IAM ロールが EventBridge から Lambda を実行する権限を持つことを確認

- [ ] スケジュール実行テスト（オプション）
  - [ ] `aws events put-events` でテストイベント送信
  - [ ] Lambda が実行されることを確認
  - [ ] CloudWatch Logs でログ出力を確認

## フェーズ7: ローカル実行確認

- [ ] AWS 認証情報を確認
  - [ ] `~/.aws/credentials` または環境変数で AWS_PROFILE が設定されている
  - [ ] `aws sts get-caller-identity` で認証確認

- [ ] `sam build` を実行
  - [ ] エラーなく完了
  - [ ] `.aws-sam/build` ディレクトリが作成されることを確認

- [ ] `sam local invoke` でドライラン実行
  - [ ] コマンド: `sam local invoke NewsletterFunction --event events/dry_run.json`
  - [ ] `events/dry_run.json` が存在することを確認
  - [ ] Lambda が正常に実行される
  - [ ] DynamoDB キャッシュ読み込みが成功する
  - [ ] Bedrock 呼び出しが成功する（実際に呼び出される）
  - [ ] SES 呼び出しがスキップされる（dry_run=true）
  - [ ] CloudWatch Logs に実行ログが出力される

- [ ] `sam local invoke` でテスト実行（dry_run=false）
  - [ ] コマンド: `sam local invoke NewsletterFunction --event events/test_event.json`
  - [ ] `events/test_event.json` を作成（dry_run=false）
  - [ ] Lambda が正常に実行される
  - [ ] メール送信が実行される（実際にテストメールが送信される）
  - [ ] 実行履歴が DynamoDB に保存される

## フェーズ8: 品質チェック

- [ ] 全テストが通ることを確認
  - [ ] `pytest tests/ -v`

- [ ] 型チェック実行
  - [ ] `mypy src/`

- [ ] リント・フォーマット実行
  - [ ] `ruff check src/`
  - [ ] `ruff format src/`

- [ ] ドキュメント確認
  - [ ] 設定ドキュメントが最新であることを確認

## フェーズ9: コスト確認と最終確認

- [ ] AWS コスト見積もりツールで月額コストを確認
  - [ ] DynamoDB: $0.50 以下
  - [ ] Bedrock: $4.00 以下
  - [ ] 合計: $10 以下

- [ ] 最終チェック
  - [ ] すべてのリソースが正しく接続されている
  - [ ] IAM ポリシーが最小権限の原則に準拠している
  - [ ] ログにセキュリティ上の問題がない（メールアドレスマスキング等）

---

## 実装後の振り返り

### 実装完了日
{YYYY-MM-DD}

### 計画と実績の差分

**計画と異なった点**:
- {計画時には想定していなかった技術的な変更点}

**新たに必要になったタスク**:
- {実装中に追加したタスク}

**技術的理由でスキップしたタスク**（該当する場合のみ）:
- {タスク名}（理由: {スキップ理由}）

### 学んだこと

**技術的な学び**:
- {実装を通じて学んだ技術的な知見}

**プロセス上の改善点**:
- {タスク管理で良かった点}

### 次回への改善提案
- {次回の機能追加で気をつけること}
