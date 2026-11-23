---
type: patch
---

#### Summary

PR 作成前のセルフレビュー（Pre-PR loop）の差し戻しが上限（`Pre-PR Fix Attempts` 3）に達したときの方式転換 4 択が、人に届き、返答で元のループに戻らないようにした。

- 止めるときは Round 上限超過と同じ state の組（`Route In Progress=human_recheck_required`・`Resume From=human-check-waiting`・`Human Check Status=pending`・`Next Action=gdd-systematic-debugging`）を書き、`<gdd-stop reason="human-check-waiting">` で止める。これまでは `blocked` で止めて loop state が消え、再開時の整合性検証でも止まっていた
- このメニューへの「OK」などの案名の無い返答を、承認として STEP 2 に通さない
- 自律モードの一覧と `<箇所>` の語彙に `Pre-PR Fix Attempts` の上限（`pre-pr-fix-limit`）を足した。判断役と事前回答の委任先が採れるのは再設計と AC を削らないスコープ縮小だけで、task 撤回と「限界として開示して人に渡す」は人に止まる
- main は subagent から `Resume From=human-check-waiting` で戻ったとき、`Next Action=gdd-systematic-debugging` でも debugging を起動せず、HITL を先に表示する

#### Affected Files

- `plugins/gate-driven-development/commands/gdd-dev.md`
- `plugins/gate-driven-development/references/post-completion-pr-flow.md`
- `plugins/gate-driven-development/references/rollback-patterns.md`
- `plugins/gate-driven-development/references/state-machine.md`
- `plugins/gate-driven-development/references/subagent-dispatch.md`
- `plugins/gate-driven-development/references/autonomy.md`
- `plugins/gate-driven-development/references/human-check-template.md`
- `plugins/gate-driven-development/references/phase-progression.md`
- `plugins/gate-driven-development/skills/gdd-completion-check/SKILL.md`

#### User Action Required

- なし

#### Validation / Eval Impact

- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
- Skill RED-GREEN Evidence（PR 本文）
