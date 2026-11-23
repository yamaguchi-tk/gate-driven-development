---
type: patch
---

#### Summary

gdd-task-breakdown が既存の `tasklist.md` を作り直すとき（`Route In Progress` の値を問わない）と gdd-refactor-planning の abort の手順に、`Reviewed by:` のある完了タスクを消すときは先に `## Pending Tasks` へ移し、次の書き込みで消すことを書いた。今までの手順どおり 1 回の書き込みで完了タスクを消すと、steering write guard（`completed_reviewed_by`）が止めていた。

#### Affected Files

- `plugins/gate-driven-development/references/task-breakdown-steps.md`
- `plugins/gate-driven-development/references/state-machine.md`
- `plugins/gate-driven-development/skills/gdd-refactor-planning/SKILL.md`

#### User Action Required

- なし

#### Validation / Eval Impact

- `tests/validate-plugin.sh`
- Skill RED-GREEN Evidence（PR 本文）
