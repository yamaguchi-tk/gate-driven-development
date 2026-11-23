---
type: patch
---

#### Summary

- 配線レビュー（別系統モデル）の指摘の重さに `reviewer-common.md` § 常時 High を掛け、blocking の指摘を後続課題に回さないようにした

#### Changed

- `gdd-pr-review` の 3g の依頼文で、Codex に `reviewer-common.md` § 常時 High の 4 型と適用範囲も書き写して渡すようにした
- § 常時 High の適用範囲に当たる指摘は、Codex が付けた severity によらず high にするようにした
- advisory を PR 本文に後続課題として記録してよいのは、blocking でないときだけにした

#### Affected Files

- `plugins/gate-driven-development/skills/gdd-pr-review/SKILL.md`

#### User Action Required

- なし

#### Validation / Eval Impact

- `tests/validate-plugin.sh`
- Skill RED-GREEN Evidence（PR 本文）
