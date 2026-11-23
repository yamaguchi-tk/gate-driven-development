# Cursor Guide

> **所有**: Claude Code / Cursor で gate-driven-development を使う際の差分・制約・導入手順
> **上位正本**: `self-contained-contract.md`
> **参照元**: `README.md`、`onboarding.md`、`faq.md`

## Claude Code / Cursor の差分一覧

| 観点                                                         | Claude Code                                | Cursor                                                                         |
| ------------------------------------------------------------ | ------------------------------------------ | ------------------------------------------------------------------------------ |
| Plugin 読み込み                                              | `--plugin-dir` / plugin import             | symlink（`install-cursor-links.sh`）または manifest                            |
| Hooks（SessionStart / Stop / PreToolUse / UserPromptSubmit） | 自動で有効                                 | **manifest 経由で有効化が必要**。symlink 方式だけでは hook が動かない          |
| Autonomous Continuation                                      | Stop hook が非 terminal stop を block      | hook が無効なら手動で次 phase を指示する必要がある                             |
| Quick Reboot（セッション復帰）                               | SessionStart hook が自動注入               | hook が無効なら `/gdd-dev 再開` で手動復帰                                     |
| Goal + AC 注入（context 保護）                               | PreToolUse hook が Write/Edit 前に自動注入 | hook が無効なら注入なし。長い build で AC を見失う可能性がある                 |
| モデル                                                       | `opus` / `sonnet`（alias）                              | Grok 4.6 / Grok 4.5 / Composer 2.5 / Opus (Dialectic Counter)（`references/cursor.md` 参照）                      |
| Subagent（reviewer）                                         | Agent tool で reviewer subagent を起動     | Cursor の subagent 機能に依存。agent 定義のままで起動できなければ、定義の本文を貼って起動する（`references/cursor.md`）。それも不可なら inline review にフォールバック |
| Plan mode                                                    | GDD は Plan mode を使わない                | `.cursor/plans/*.plan.md` は optional artifact。Plan mode とは別物             |
| worktree                                                     | git worktree 必須                          | 同じ。git worktree 必須                                                        |

## 導入手順

### 方式 1: symlink（hooks なし）

```bash
bash scripts/install-cursor-links.sh
# dry-run: bash scripts/install-cursor-links.sh --dry-run
```

- `commands/`、`skills/`、`agents/` が `~/.cursor/` 以下に symlink される
- `cursor-links.tsv` で管理され、`uninstall-cursor-links.sh` で解除可能
- **制約**: hooks が動かないため、Autonomous Continuation / Quick Reboot / Goal+AC 注入は無効

### 方式 2: manifest 経由（hooks あり）

manifest（`.cursor-plugin/plugin.json`）経由で plugin を有効化する。hooks を含む全機能が利用可能。

- 有効化後は Cursor の reload が必要
- symlink 方式と併用する場合は、same-name ambient asset 衝突に注意する

## hooks が無効な場合の運用

hooks が無効な場合は、次の手動対応に切り替える:

| hook の機能                         | 手動対応                                                                       |
| ----------------------------------- | ------------------------------------------------------------------------------ |
| **SessionStart**: Quick Reboot 注入 | `/gdd-dev 再開` で明示的に resume する                                         |
| **Stop**: Autonomous Continuation   | 各 phase の出力後、手動で次の phase を指示する（例: 「次に進めて」）           |
| **PreToolUse**: Goal + AC 注入      | build が長引く場合は `gdd-status` で現在の AC を確認し、必要なら再掲を依頼する |
| **UserPromptSubmit**: context 注入  | 追加対応不要（hook は補助的な context 追加のみ）                               |

## モデル選択

Cursor 環境のモデル選択は `references/cursor.md` を正本とする（`gdd-model-routing` skill 内の参照ファイル）。

要点（2026-08-25 最新化: heavy は Grok 4.6 の effort 差別化、light / leaf は Grok 4.5、実装は Composer 2.5、Dialectic Counter は Opus high。詳細は `references/cursor.md`）:

- `gdd-pre-workflow-brainstorming`: `Grok 4.5 + reasoning.effort=medium`
- **formal gate（brainstorming / requirements / design / impl / completion）**: `Grok 4.6 + reasoning.effort=medium`
- 一般 heavy（debug / refactor / advisory review）: `Grok 4.6 + reasoning.effort=low`
- 一般 heavy の risk escalation（undocumented step / large working-set / security-sensitive / final review）: `Grok 4.6 + reasoning.effort=high`
- **Dialectic Counter（cross-system）**: `Opus + reasoning.effort=high`
- 実装: `Composer 2.5`（`composer-2-fast` は使わない）
- leaf task: `Grok 4.5 + reasoning.effort=low`（cheap/read-only lane も Grok 4.5 + low。GPT 系は使わない）

## `.cursor/plans/*.plan.md` の扱い

- GDD の workflow artifact ではなく **optional artifact**
- デフォルトでは作らない
- ユーザーが明示的に比較案や壁打ちログの保存を求めたときだけ作る
- `gdd-pre-workflow-brainstorming` では作らない（artifact-free lane）
- routing source / gate 条件には使わない

## プリフライトチェック（hooks 有効化の検知）

Cursor 環境では hooks が無効な場合に **劣化モードに気づかないまま作業が進む** リスクがある。以下のチェックで早期に検知する。

### 検知方法

`gdd-brainstorming` の Step 1 で Cursor 環境を検知した場合（モデルが Grok 4.6 / Grok 4.5 / Composer 2.5 の場合）、以下を確認する:

1. **SessionStart hook の応答を確認**: session 開始時に `[GDD] Quick Reboot` のような context 注入があるか
2. **hook 応答がない場合**: 以下の警告を表示する

```
⚠ Cursor 環境で hooks が検出されませんでした。
以下の機能が無効です:
- Autonomous Continuation（phase 間の自動遷移）
- Quick Reboot（session 復帰時の自動 context 復元）
- Goal + AC 注入（長い build での AC 追跡）

hooks を有効にするには manifest 経由でインストールしてください:
→ 方式 2: manifest 経由（本ファイルの「導入手順」参照）

hooks なしでも作業は可能ですが、各 phase の出力後に手動で次を指示する必要があります。
```

3. **作業は停止しない**: 警告は表示するが fail-closed にはしない（hooks なしでも GDD は動作する）

### 方式選択の判断基準

| 求める機能                        | symlink（方式 1） | manifest（方式 2） |
| --------------------------------- | ----------------- | ------------------ |
| skills / agents / commands の利用 | ✓                 | ✓                  |
| Autonomous Continuation           | ✗                 | ✓                  |
| Quick Reboot                      | ✗                 | ✓                  |
| Goal + AC 注入                    | ✗                 | ✓                  |

**推奨**: Autonomous Continuation を使う場合は manifest 経由を選択する。

## 既知の制約

1. **reviewer subagent の互換性**: Cursor の subagent 機能が Claude Code の Agent tool と異なる場合、reviewer subagent が起動できない可能性がある（agent 定義の `model: opus` は Cursor の Task で解決できずに落ちる）。その場合は定義の本文を貼って別コンテキストで起動し（`references/cursor.md`）、それも不可なら inline review（`references/inline-review-checklists.md`）にフォールバックする
2. **same-name ambient asset**: `install-cursor-links.sh` が作った symlink は衝突判定から除外されるが、別実体の同名 asset がある場合は fail-closed で停止する
3. **Cursor reload**: plugin / symlink の変更後は Cursor の reload が必要
