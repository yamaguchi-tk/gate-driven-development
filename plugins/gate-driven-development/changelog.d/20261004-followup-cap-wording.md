---
type: patch
---

#### Summary

`gdd-pr-review-followup` の skill が、ポーリング上限を「上限（既定 12 回）を超えたら `blocked`」と書いていた。stop hook は回数が上限に達した時点（12 回目）で `blocked` にするので、skill を「達したら」に直した。

#### Affected Files

- `plugins/gate-driven-development/skills/gdd-pr-review-followup/SKILL.md`

#### User Action Required

- なし

#### Validation / Eval Impact

- `bash tests/validate-plugin.sh`
- Skill RED-GREEN Evidence（PR 本文）
