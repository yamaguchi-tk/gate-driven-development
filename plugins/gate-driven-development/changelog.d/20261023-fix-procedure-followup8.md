---
type: patch
---

#### Summary

- `gdd-task-breakdown` の SKILL.md の Task State Rule（planning 差し戻しの後に tasklist を作り直すときに引き継ぐもの）に、task の `Fix Findings:` の行を作り直した task に写すことを足した。これまでは references（`task-breakdown-steps.md`・`state-machine.md`）にしか書かれておらず、SKILL.md だけを読んだ runner は作り直しで行を落とした

#### Changed

- `skills/gdd-task-breakdown/SKILL.md`（Task State Rule の planning 差し戻し後の再到達）

#### Affected Files

- `skills/gdd-task-breakdown/SKILL.md`

#### User Action Required

- なし

#### Validation / Eval Impact

- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
