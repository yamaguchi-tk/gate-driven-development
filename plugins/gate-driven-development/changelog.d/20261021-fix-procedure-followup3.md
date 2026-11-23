---
type: patch
---

#### Summary

- `references/self-review-lanes.md` § 直し方 2 で、ある部品が判定に届くかを、`references/reviewer-common.md` § 常時 High の適用範囲の基準で決めることにした
- block しない hook の (a)(b) に届く部分を直すときは、fail-open の 3 ケースに加えて、同節が挙げる欠陥の種類（書き損じ・消し損じなど）ごとのテストも書く

#### Changed

- `references/self-review-lanes.md`（§ 直し方 2、参照元の行）
- `references/subagent-dispatch.md`（TDD Template の読むファイル）
- `skills/gdd-subagent-driven-implementation/SKILL.md`（Subagent Prompt Contract の Constraints と Expected output）

#### Affected Files

- `references/self-review-lanes.md`
- `references/subagent-dispatch.md`
- `skills/gdd-subagent-driven-implementation/SKILL.md`

#### User Action Required

- なし

#### Validation / Eval Impact

- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
