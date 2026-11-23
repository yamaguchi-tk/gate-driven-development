# Copilot へのレビュー指示

このリポジトリ（gate-driven-development）は、Claude Code / Codex / Cursor 向けの
個人用 SKILL・Plugin コレクションです。アプリケーションコードそのものではなく、
主に Markdown（skill 定義・agent 定義・ドキュメント）と、補助的な shell / python
スクリプトで構成されています。レビュー時は以下を踏まえてください。

## 言語

- レビューコメントは日本語で書いてください。

プラグインごとの追加観点は `.github/instructions/*.instructions.md` に分けています
（`applyTo` で対象パスが限定されます）。

## 設計原則

- YAGNI / KISS / DRY を優先してください。将来の拡張を見込んだ過剰な抽象化、
  使われていない後方互換レイヤーやフォールバック処理の追加は指摘してください。
- ドキュメント（skill / reference / CONTRIBUTING 等）の追加は、既存文書との重複記述を
  整理・削除した上での追加になっているか確認してください。追記だけで完結する変更
  （加算式改修）は `gate-driven-development` では明示的に禁止されています。詳細は
  [plugins/gate-driven-development/CONTRIBUTING.md](../plugins/gate-driven-development/CONTRIBUTING.md)
  を参照してください。

## コードの健全性

- 実装コード（`*.py`, `*.sh`, `*.ts` 等。ドキュメント・テストは対象外）は、目安として
  1 ファイル 1500 行以内、1 関数・メソッド 300 行以内を超えないようにしてください。
  既存の超過分をさらに増やす変更（分割を伴わない追記）は指摘してください。

## 機密情報

- 秘密鍵、パスワード、APIキー、トークン、`.env` の実値がコミットに含まれていないか
  確認してください。AWSアカウントID（12桁の数値）単体は機密情報として扱いません。

## PR の前提

- PRタイトル・本文は日本語で書かれているか確認してください。
- `plugins/gate-driven-development` の変更では、pytest の全量
  （`python3 -m pytest plugins/gate-driven-development/tests/ -q -n auto`）と
  `bash plugins/gate-driven-development/tests/validate-plugin.sh` は CI（`plugin-lint` の
  `gdd-plugin`）が回します。PR の check で `gdd-plugin` が success かを確認して
  ください（CI は PR を作った後に走るので、PR本文に run の URL や結果があることは
  求めません）。手元の確認は、関係するテストと `validate-plugin.sh` で足ります
  （全量をローカルで回した結果は求めません）。
- `plugins/plain-writing` と `plugins/japanese-reply-guard` の pytest
  （`python3 -m pytest plugins/plain-writing/tests/ -q` など）も、同じ `gdd-plugin` が回します。
