# 要件定義

## GitHub Issue
https://github.com/k-negishi/ai-curated-newsletter/issues/17

## issue 内容
- タイトル: メールの体裁変更
- 本文:
  - インデントがあって見づらい
  - Tag は タイトルの下に
  - 記事の公開日がほしい
- ラベル: なし

## 概要

メール本文のHTMLフォーマットを改善し、可読性を向上させる。

## 背景

現在のメールフォーマットには以下の問題がある:
- HTML版で `<p>` タグが多用され、インデントが深くなっている
- Tag が記事情報の一番下に配置されており、タイトルから離れている
- 記事の公開日が表示されていない

これらを改善し、ユーザーがメールを読みやすくする必要がある。

## ユーザーの選択

- **インデント改善方法**: 1行形式（タイトル、Tag、公開日、URL、概要を1つの `<li>` 内に改行で配置）
- **公開日形式**: YYYY-MM-DD（例: 2026-02-15）

## 実装対象の機能

### 1. JudgmentResultモデルに公開日フィールドを追加
- `JudgmentResult` に `published_at` フィールドを追加
- `Article.published_at` を引き継ぐ形で実装

### 2. LLM Judge サービスで公開日を含める
- `LlmJudge._judge_single()` で `JudgmentResult` 作成時に `article.published_at` を含める
- フォールバック判定でも `published_at` を含める

### 3. Formatter サービスでメール体裁を変更
- HTML版のフォーマットを1行形式に変更
- Tag をタイトルの下に移動
- 公開日を YYYY-MM-DD 形式で表示
- プレーンテキスト版も同様に変更

## 受け入れ条件

### JudgmentResultモデル
- [x] `JudgmentResult` に `published_at: datetime` フィールドが追加されている
- [x] 既存のテストが動作する（後方互換性）

### LLM Judge サービス
- [x] `JudgmentResult` 作成時に `article.published_at` が含まれる
- [x] フォールバック判定でも `published_at` が含まれる
- [x] 既存のテストが動作する

### Formatter サービス
- [x] HTML版で Tag がタイトルの下に表示される
- [x] HTML版で公開日が YYYY-MM-DD 形式で表示される
- [x] HTML版で1行形式（改行のみ）のシンプルなレイアウトになっている
- [x] プレーンテキスト版でも Tag と公開日が適切に表示される
- [x] 既存のテストが動作する

### テスト
- [x] `test_formatter.py` に新しいテストケースが追加されている
- [x] HTML版のフォーマットが正しいことを検証するテスト
- [x] 公開日が正しく表示されることを検証するテスト

## 成功指標

- ユニットテストが全てパスする
- リント・型チェックエラーがない
- メール本文のHTML版が1行形式で見やすくなっている

## スコープ外

以下はこのフェーズでは実装しません:

- プレーンテキスト版のフォーマット大幅変更（最小限の変更のみ）
- メール件名の変更
- 実行サマリのフォーマット変更
- CSS スタイルの追加（シンプルなHTMLのみ）

## 実装方針
- Kent Beck の TDD (Test-Driven Development) で実装する
- RED → GREEN → REFACTOR のサイクルを遵守
- テストを先に書き、最小限の実装でパスさせ、その後リファクタリング

## 参照ドキュメント

- `docs/product-requirements.md` - プロダクト要求定義書
- `docs/functional-design.md` - 機能設計書（Formatter, Notifier の仕様）
- `docs/architecture.md` - アーキテクチャ設計書
- `docs/development-guidelines.md` - 開発ガイドライン
