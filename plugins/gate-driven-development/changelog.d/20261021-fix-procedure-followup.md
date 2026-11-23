---
type: patch
---

#### Summary

- `references/self-review-lanes.md` § 直し方 の当て方と記録先をそろえた。指摘の出所を問わずに当てる。規律 C の記録先に当たらない修正（`gdd-pr-review` の中、`gdd-receiving-code-review` の IMPLEMENT）は、`worklog.md` か PR 本文に書く
- § 直し方 から、`common-guardrails.md` § 選ぶときの基準 2・4、`root-cause-investigation` の Phase 4、`gdd-writing-skills` § Skill RED-GREEN Evidence を指す
- `gdd-subagent-driven-implementation` の worker に渡す prompt の Constraints で § 直し方 を指し、報告で 4・5 の記録を返させる。`gdd-systematic-debugging` は、どの route でも指摘を直す段に § 直し方 を当てる。`gdd-pr-review` は skill の中のすべての修正に当てる
- `references/rollback-patterns.md` § implementation_fix_only で、実害クラス・`High` では § 直し方 2 が求めるテストを RED の段で書くことにした

#### Changed

- `references/self-review-lanes.md`（§ 直し方、参照元の注記）
- `references/rollback-patterns.md`（§ implementation_fix_only）
- `skills/gdd-subagent-driven-implementation/SKILL.md`（Subagent Prompt Contract の Constraints と Expected output）
- `skills/gdd-systematic-debugging/SKILL.md`（§ Failure Routing）
- `skills/gdd-pr-review/SKILL.md`（手順の後の「直す順序」の段落）
- `skills/gdd-pr-review-followup/SKILL.md`・`skills/pr-review-followup/SKILL.md`（指す文）

#### Affected Files

- `references/self-review-lanes.md`
- `references/rollback-patterns.md`
- `skills/gdd-subagent-driven-implementation/SKILL.md`
- `skills/gdd-systematic-debugging/SKILL.md`
- `skills/gdd-pr-review/SKILL.md`
- `skills/gdd-pr-review-followup/SKILL.md`
- `skills/pr-review-followup/SKILL.md`

#### User Action Required

- なし

#### Validation / Eval Impact

- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
