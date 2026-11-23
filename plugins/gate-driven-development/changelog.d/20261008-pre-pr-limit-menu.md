---
type: patch
---

#### Summary

PR 作成前のセルフレビュー（Pre-PR loop）の差し戻しが上限（`Pre-PR Fix Attempts` 3）に達したときも、completion-check の Round 上限と同じ方式転換の 4 択（task 撤回 / 再設計 / スコープ縮小 / 限界として開示して人に渡す）を出すようにした。もう 1 周回す案や上限の引き上げは選択肢に置かず、事前回答・自律モードの判断役が答えるときも 4 択の中から選ぶ。これまでは止まった後の選択肢が決まっておらず、続行を選び続けると上限の後も 1 回ずつ回り続けていた。

#### Affected Files

- `plugins/gate-driven-development/references/post-completion-pr-flow.md`
- `plugins/gate-driven-development/references/rollback-patterns.md`

#### User Action Required

- なし

#### Validation / Eval Impact

- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
