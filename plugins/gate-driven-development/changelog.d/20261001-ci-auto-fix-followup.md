---
type: minor
---

#### Summary

PR を作る option を選んだとき、GDD は CI が終わるまで待ち、required check の失敗を直して push する。この動きを、Claude Code の既定の経路（completion-check の subagent が PR を作る経路）で動くようにした。CI の待機はどの環境でも同じ方法で行い、Auto-fix をオンにするのは Claude Code desktop のメインセッションだけにした。PR を作った後、CI の待機と自動修正が終わるまで `done` にしない。

#### Changed

- `references/post-completion-pr-flow.md` Option 1 手順 6 の「CI 失敗の自動修正」: CI の待ち方を `references/phase-progression.md` § Post-PR / Post-Merge Contract 1（上限 `PR CI Wait Timeout`）にそろえた。止まる条件に、外部の障害・flaky・待機の上限を足し、3 回の数え方を followup の Escape Hatches に合わせ、テストの削除・assert の緩和・skip で通すことを禁じた。Auto-fix はメインセッションがオンにし、`address_comments` は自走上限が外部レビューの収束を含むときだけ `true` にする。オンにできなければ待機だけで進める。PR が開いている間に届いた CI の失敗は `done` の後でもその PR で直し、衝突は報告だけにする
- `references/post-completion-pr-flow.md` Step 4、`skills/gdd-completion-check/SKILL.md`、`references/subagent-dispatch.md`、`references/phase-progression.md`: PR を作った後の `done` を、CI の待機と自動修正の後にした
- `references/subagent-dispatch.md` § Completion-Check Post-Return Routing: subagent が PR を作って戻ったら、メインセッションが Auto-fix をオンにする
- `references/phase-progression.md` § Post-PR / Post-Merge Contract: required check の失敗で直ちに `blocked` にせず、上の自動修正に回す。PR が開いている間の CI の失敗は Hotfix Lane にしない
- `references/human-check-template.md` 自走上限の表: 「PR 作成まで」に、PR の CI の失敗の修正と push を足した

#### Affected Files

- `plugins/gate-driven-development/references/post-completion-pr-flow.md`
- `plugins/gate-driven-development/references/phase-progression.md`
- `plugins/gate-driven-development/references/subagent-dispatch.md`
- `plugins/gate-driven-development/references/human-check-template.md`
- `plugins/gate-driven-development/skills/gdd-completion-check/SKILL.md`

#### User Action Required

- 操作は要らない。PR を作った後は、CI が終わり、required check の失敗を直し終えるまで GDD が止まらなくなる。止まるのは、原因が差分の外のとき、同じ check の失敗が 3 回続いたとき、待機が上限を過ぎたときである

#### Validation / Eval Impact

- `tests/validate-plugin.sh`
- Skill RED-GREEN Evidence（PR 本文）
