---
lane: L1
pr: 337
follow_up_of: 331
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 25fa3e7fa51f1c8941f6cb70ef6c049774e1eee4 | 0 | 2 | 0 | 2026-10-03T23:30+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| L1 | 独立-1 | medium | no | self-inflicted | doc-claim | accepted | § 通信境界・§ 1・全体図が「plugin は外部通信しない」のままで、§ 4 に足した gh pr view の例外と食い違う。限界に書いた |
| L2 | 独立-1 | medium | no | self-inflicted | doc-claim | accepted | Bash の行が ~/.claude/.gdd-hook-state/ の読み書き（絶対パスの PR 台帳 gdd-pr-roots、ログ、キャッシュ）と .claude/gdd-dev.local.md の読み取りを載せていない。限界に書いた |
| L3 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | EnterPlanMode・EnterWorktree・Skill の行の読み取り範囲は state.md ではなく .claude/gdd-dev.local.md。Agent の行に tasklist.md の Next Action が無い。限界に書いた |
| L4 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | matcher の MultiEdit・ApplyPatch・SwitchMode が表に無い。限界に書いた |
| L5 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 「root-branch guard」が worktree command guard の止めるものの一部（GDD worktree の作成元の検査）を指さず、README と呼び名も割れる。限界に書いた |
| L6 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 外部通信の例外の文に、許可より前に走ること・GDD の active を問わないこと・止め方・「書き込みはしない」が GitHub への書き込みを指すことが無い。限界に書いた |
| L7 | 独立-1 | low | no | inherited | doc-claim | accepted | Write/Edit の行が、steering への書き込みの検査の読むもの・deny の counter の書き込みを載せていない。限界に書いた |
| L8 | 独立-1 | low | no | inherited | doc-claim | next-pr | SessionStart の行が、state dir の last-turn-failure.json の読み取りと削除を載せていない。次の PR |
| L9 | 独立-1 | advisory | no | inherited | doc-claim | accepted | 「Hook（4 種類）」の表に無い event（PreCompact・StopFailure・Notification・UserPromptExpansion）があることが文書に無い。PR 本文に列挙 |
| L10 | 独立-1 | advisory | no | inherited | doc-claim | accepted | 表と hooks.json の matcher の集合を突き合わせるテストが無い。PR 本文に列挙 |
