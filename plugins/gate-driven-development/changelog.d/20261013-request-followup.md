---
type: patch
---

#### Summary

依頼の原文との突き合わせ（`Request Drift`）で、承認の記録に数えるものを 2 つにした。本人の発言（`request.md`）は今までどおり全部数える。判断役（`GDD Autonomy: internal`）と事前回答の委任による承認は、`worklog.md` の `自律判断:`・`事前回答の適用:` の行の末尾に ` / 承認した変換: <行>` として「完了条件の変換」表の行を引用し、扱いが `具体化` で、初期条件の語が `request-crosscheck.md` の `原文だけでは決まらない` に挙がっているものだけを数える。それ以外の型は委任では承認できない。これまでは委任の承認がどこにも残らず、承認済みの具体化も High になり、判断役が承認し直しても同じ High が Round の上限まで続いた。あわせて、`Request Drift` を理由にした `human_recheck_required` で、依頼に合わせて実装を直す以外の案を採ることを、判断役の「止まる案」と事前回答の「人に戻す条件」に足した。

ほかに次をそろえた。依頼より広げた分の revert は、依頼に合わせて直すことに当たる（`gdd-pr-review` の 3a）。方式転換で委任先・判断役が採れる案は、`autonomy.md` の止まる案を指す形にした（`post-completion-pr-flow.md`）。Round の上限のメニューの「人が承認した限界」も、依頼から外れた限界は同じ承認の記録だけを数える（`rollback-patterns.md`）。本人の入力を `request.md` に写す手順を、振り分けの前段（`gdd-using-skills`）、HITL Pending Hard Invariant、Planning Interrupt Decision Menu、事前回答の記録にも入れ（同じ入力は 1 回だけ足す）、写す対象を「cross-session 経由を除く本人のターンの入力すべて」にそろえた。完了前の最終レビューには `request-crosscheck.md`・`worklog.md` のパスも渡す。

#### Affected Files

- `plugins/gate-driven-development/agents/gdd-completion-reviewer.md`
- `plugins/gate-driven-development/skills/gdd-pr-review/SKILL.md`・`skills/gdd-completion-check/SKILL.md`・`skills/gdd-using-skills/SKILL.md`
- `plugins/gate-driven-development/references/autonomy.md`・`references/human-check-template.md`・`references/rollback-patterns.md`・`references/post-completion-pr-flow.md`・`references/brainstorming-steps.md`・`references/subagent-dispatch.md`
- `plugins/gate-driven-development/tests/checks/skill-body-budget.sh`・`tests/checks/lint-scripts-functional.sh`（runtime profile の推定 token の上限を、standard は 45472 から 45480 に、express は 30117 から 30125 に上げた）

#### User Action Required

- なし

#### Validation / Eval Impact

- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
