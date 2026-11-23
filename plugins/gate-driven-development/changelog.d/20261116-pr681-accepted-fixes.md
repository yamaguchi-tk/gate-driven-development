---
type: patch
---

#### Summary

- human check を表示するときは、`記録の場所: なし` の行を compact の一次表示にも載せ、行数の目安を超えても落とさない
- Step 4 以外の経路で出す `done`（Auto-Arm の収束、Stage Continuation の最後の Stage、Post-PR Scope Continuation、Manual Merge Continuation、post-merge-qa）でも、その直前に `記録の場所: なし` の行を書く
- fail-closed の停止を `参照した正本` / `停止理由` / `次の1アクション` だけで定めていた箇所（loop の prompt を含む）に、`<gdd-stop>` の後の `## 👤 次にすること` を足した。Stop hook に押し返されずに止まれる

#### Affected Files

- `commands/gdd-dev.md`・`references/brainstorming-steps.md`・`references/common-guardrails.md`・`references/contract-overview.md`・`references/faq.md`・`references/human-check-template.md`・`references/human-check-template-compact.md`・`references/post-completion-pr-flow.md`・`references/post-merge-qa.md`・`references/self-contained-contract.md`・`references/state-machine.md`・`references/subagent-dispatch.md`・`scripts/setup-gdd-loop.sh`・`skills/gdd-brainstorming/SKILL.md`・`skills/gdd-pr-review-followup/SKILL.md`・`skills/gdd-systematic-debugging/SKILL.md`

#### User Action Required

- なし

#### Validation / Eval Impact

- `python3 scripts/light-lane-related-tests.py --run . origin/main`・`bash plugins/gate-driven-development/tests/validate-plugin.sh`
