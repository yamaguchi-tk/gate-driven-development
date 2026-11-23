# Workspace Policy（worktree 有無の判断・唯一の正本）

worktree か root かの判断ルールの正本はここ（DRY、他ファイルに判断本文を持ち込まない）。手続き（作成・cleanup・禁止コマンド等の enforcement）は対象外（各 skill、例: `gdd-using-git-worktrees` に残る）。

## 2値ルール

判断軸は「出口（commit を生むか）」の 2 値だけ。レーン・サイズ・系統で変えない。

- **worktree**: PR / ブランチ / commit を生む作業すべて（GDD `quick` 以上。GDD 対象外のコード変更依頼も本来は対象だが、現時点では § 適用範囲の但し書き の前提が未整備のため GDD セッション内でのみ有効）。
- **root**: commit を生まない作業（相談・壁打ち・調査・コードリーディング・レビュー・運用確認・メトリクス集計）。

## trivial の扱い

`trivial` は 3 値目ではなく root 側のサブケース。**root のまま**（worktree 化しない、作業場所宣言のみ必須）。対象は「1 行以下の typo / 文言 / 設定値変更で behavior change なし」に限る。`task-sizing.md` § 昇格条件（2 行以上 / ロジック変更 / テスト影響 / behavior change）を満たせば即 `quick` 以上へ昇格。

## 作業場所宣言の必須化

コード変更開始時、最初の応答の1行目で宣言する（スキル開始アナウンス・フェーズ遷移ヘッダーより前。書式は `references/output-format.md` § 作業場所宣言を参照）。

- worktree版: `作業場所: worktree（<worktree の絶対パス>）`
- root(trivial)版: `作業場所: root（trivial: <1行以下の typo/文言/設定値変更のため worktree 化しない>）`

## 相談レーンの分類

`gdd-pre-workflow-brainstorming` は root 側（commit を生まないため）。現状挙動の追認で変更なし。

## 系統の注記

GDD 管理 worktree（`~/.gdd/worktrees` 配下）を正とする。harness native 機構（`EnterWorktree` 等）は別系統。

active `/gdd-dev` session 中は `EnterWorktree` の呼び出しが PreToolUse hook（`run-block-enter-worktree-hook.sh`）で block される。worktree はこの skill（`gdd-using-git-worktrees`）経由で作成すること。非 active session では従来通り動作する。marker で判定できないとき（state 破損・読めないなど）は block 側に倒す。

この hook は Claude Code harness-native `EnterWorktree` tool のみを対象とする。Cursor には該当 tool が存在しないため matcher は発火しない（no-op）。Cursor では本節の静的な使い分け指示（GDD 管理 worktree を正とする旨）が唯一の抑止手段になる。

## 適用範囲の但し書き

GDD 対象外のコード変更依頼への発火は**グローバル CLAUDE.md への追記が前提**。未追記の間、本ルールは GDD セッション内でのみ有効（「書いたのに効いていない」誤認防止のため明記）。

## レビュー中の commit 発生時の再宣言

root で開始したレビュー・調査中に「その場で直す」判断をしたら、worktree へ**再宣言してから** fix を始める（root bleed 防止）。ただし trivial 相当の1行修正は § trivial の扱いの root 例外どおり、宣言のみで継続可。
