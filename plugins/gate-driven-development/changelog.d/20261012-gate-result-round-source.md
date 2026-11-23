---
type: patch
---

#### Summary

gate の `worklog.md` の `gate結果:` 行（20261010-gate-result-ledger で足したもの）の書き方を決めた。`task:` の欄を足し、`Round <n>` は同じ phase・同じ task の既存の `gate結果:` 行の数に 1 を足した値にした（`Gate Rounds`・`Completion Rounds`・`reviews.md` の見出しからは取らない）。判定の値に `blocked` を足し、Round を進めずに止まる出口（design・implementation の時間超過など）でも `blocked` と書く。`timeout` は requirements の、Round を消費する時間超過だけに使う。書く時点は Round の判定を決めた後、件数は blocking の再現を確かめた後の値とした。gate runner の文には、どの phase が gate に当たるか（requirements-gating は planning の `## Phase gdd-brainstorming` の中で実行する）を書き、実装・完了の gate の行と時間上限の項には書き手（gate runner。inline 実行なら main。main が gate runner を時間上限・エラーで止めて出口を決めたときも main。worker 経由なら結果を統合する main で、worker 自身は書かない）を書いた。

#### Affected Files

- `plugins/gate-driven-development/references/subagent-dispatch.md`
- `plugins/gate-driven-development/references/requirements-gating-steps.md`
- `plugins/gate-driven-development/agents/gdd-formal-gate-runner.md`
- `plugins/gate-driven-development/agents/gdd-light-task-runner.md`
- `plugins/gate-driven-development/skills/gdd-implementation-gating/SKILL.md`
- `plugins/gate-driven-development/skills/gdd-completion-check/SKILL.md`

#### User Action Required

- なし

#### Validation / Eval Impact

- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
- Skill RED-GREEN Evidence は PR 本文に書く
