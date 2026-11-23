---
type: patch
---

#### Summary

- TDD の subagent は、§ 直し方 が従う先として名指しする節（reviewer 側の点検として挙げるものは除く）も読む
- `gdd-test-driven-development` で、指摘を直すために戻った task は、RED Evidence が記録済みでも指摘を再現するテストが無ければ、§ 直し方 の冒頭と 1・2 のテストを足して RED を確かめる（文言・帳簿だけの指摘は除く）
- 実装 worker の agent 定義は、return の項目を prompt の Expected output に従わせる

#### Changed

- `skills/gdd-subagent-driven-implementation/SKILL.md`（Subagent Prompt Contract の Constraints と Expected output）
- `references/subagent-dispatch.md`（TDD Template の読むファイル）
- `skills/gdd-test-driven-development/SKILL.md`（Step 1 の Post-Compaction Resume Check）
- `references/self-review-lanes.md`（§ 直し方 2、参照元の行と理由の文）
- `references/rollback-patterns.md`（§ implementation_fix_only）
- `agents/gdd-implementation-worker.md`・`agents/gdd-implementation-worker-heavy.md`・`agents/gdd-remediation-worker.md`（return の項目）

#### Affected Files

- `skills/gdd-subagent-driven-implementation/SKILL.md`
- `references/subagent-dispatch.md`
- `skills/gdd-test-driven-development/SKILL.md`
- `references/self-review-lanes.md`
- `references/rollback-patterns.md`
- `agents/gdd-implementation-worker.md`
- `agents/gdd-implementation-worker-heavy.md`
- `agents/gdd-remediation-worker.md`

#### User Action Required

- なし

#### Validation / Eval Impact

- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
