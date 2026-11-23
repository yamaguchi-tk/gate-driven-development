---
type: patch
---

#### Summary

- TDD の subagent は、常に `references/self-review-lanes.md` § 直し方 を読み、レビューの指摘を直すテストを書くときに従う
- `references/rollback-patterns.md` § implementation_fix_only と `gdd-systematic-debugging` の復帰は、番号で切らずに § 直し方 を指し、文言・帳簿だけの修正には再現テストの段を見せない

#### Changed

- `references/self-review-lanes.md`（§ 直し方 2、参照元の `gdd-systematic-debugging` の注記と理由の文）
- `references/subagent-dispatch.md`（TDD Template の読むファイル）
- `references/rollback-patterns.md`（§ implementation_fix_only）
- `skills/gdd-subagent-driven-implementation/SKILL.md`（Subagent Prompt Contract の Constraints）
- `skills/gdd-systematic-debugging/SKILL.md`（§ Failure Routing の `implementation_fix_only` の復帰）

#### Affected Files

- `references/self-review-lanes.md`
- `references/subagent-dispatch.md`
- `references/rollback-patterns.md`
- `skills/gdd-subagent-driven-implementation/SKILL.md`
- `skills/gdd-systematic-debugging/SKILL.md`

#### User Action Required

- なし

#### Validation / Eval Impact

- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
