---
type: patch
---

#### Summary

- `pr-review-followup` の Push の手順で、push 先を PR の head にする（`git push origin HEAD:<headRefName>`）。`git push origin HEAD` は手元の branch 名で push するので、worktree の branch 名と PR の head が違うと、PR を更新せずに別のリモートブランチを作った

#### Affected Files

- `skills/pr-review-followup/SKILL.md`

#### User Action Required

- なし

#### Validation / Eval Impact

- `python3 scripts/light-lane-related-tests.py --run . origin/main`・`bash plugins/gate-driven-development/tests/validate-plugin.sh`
