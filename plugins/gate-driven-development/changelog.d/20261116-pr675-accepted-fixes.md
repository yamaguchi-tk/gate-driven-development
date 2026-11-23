---
type: patch
---

#### Summary

- 既存側がユーザーの決めた規則・方針の `既存とぶつかる` で、依頼の原文どおりの側に仮決定した行も、human check の一次表示の § ズレ確認 に載せる（記録の場所が無ければ `記録の場所: なし` を添える）。「推奨で進めて」と任された行も同じに扱う。規則とぶつかることを本人が見られるようにした
- 記録の場所に数える `CLAUDE.md`・`AGENTS.md` の行の「着手前の commit」を、fetch の後の `git merge-base origin/<既定のブランチ> HEAD` と決めた。requirements の reviewer は、記録の場所の種類だけでなく、この条件も当てる
- 要件を固める確認が未収束で終わった後の「human check に回さない」は、問いとして回さないという意味で、既存側が規則・方針の行の仮決定（どちらの側に仮決定しても）は一次表示に出すと書き分けた
- human check への返答を `request.md` に写すとき、§ ズレ確認 の質問などのほかの行は、本人が答えたときに、答えが指した行を添える
- 事前回答の委任で human check を表示する条件（規則・方針の側の仮決定の行がある）は、その行を引用した本人の承認が `request.md` に無いときだけにした。リスクの段が低いときの承認（`risk-low:`）も、同じ条件の steering では使わず、本人の承認を待つ。`記録の場所: なし` の行は、PR 本文の残した問題の欄と、PR を作らない完了も含めた最後の完了の報告に書く（書くかを決める印は PR 684 の分の断片）
- `<gdd-stop>` の reason を並べていた `references/stop-hook-structured-markers.md`・`skills/gdd-brainstorming/SKILL.md`・`references/subagent-dispatch.md` は、`references/output-format.md` の許容値の表を指す

#### Affected Files

- `agents/gdd-planning-reviewer.md`・`references/brainstorming-steps.md`・`references/gate-status-schema.md`・`references/human-check-template.md`・`references/human-check-template-compact.md`・`references/post-completion-pr-flow.md`・`references/requirements-gating-steps.md`・`references/stop-hook-structured-markers.md`・`references/subagent-dispatch.md`・`skills/gdd-brainstorming/SKILL.md`

#### User Action Required

- なし

#### Validation / Eval Impact

- `python3 scripts/light-lane-related-tests.py --run . origin/main`・`bash plugins/gate-driven-development/tests/validate-plugin.sh`
