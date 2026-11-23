---
type: patch
---

#### Summary

planning 差し戻し後に gdd-task-breakdown が `tasklist.md` を作り直す範囲を、差し戻しの route を問わず全セクションの初期化にそろえた。`design_detail_only` のとき影響タスクだけをリセットする（`Completed Tasks` を残す）規定を削った。`Route In Progress` は task-breakdown に handoff する前に `none` へ戻るので、規定上この部分リセットは選ばれず、全セクションの初期化に進んでいた。部分リセットで Current Task を Pending Tasks に戻したときの `Fix Attempts`・`Scope Drift Counter` の「逆戻り時の扱い」も削った。gdd-systematic-debugging の `design_detail_only` の復帰シーケンスも「影響タスクのみ再分割」から全セクションの作り直しに直した。

あわせて、並列 batch の `human_recheck_required` で完了タスクを cleanup task に降格する手順に、`Reviewed by:` のある完了タスクは 2 回の書き込みで外すこと（1 回で外すと steering write guard が止める）を書いた。存在しない節「Tasklist Reset Policy」への参照は、`references/state-machine.md` § planning 差し戻し後の tasklist.md リセットに直した（逐次の `human_recheck_required` の全 revert を述べる参照は § planning 差し戻し時の code artifact 扱いに直した）。

#### Affected Files

- `plugins/gate-driven-development/skills/gdd-task-breakdown/SKILL.md`
- `plugins/gate-driven-development/references/task-breakdown-steps.md`
- `plugins/gate-driven-development/references/state-machine.md`
- `plugins/gate-driven-development/references/phase-progression.md`
- `plugins/gate-driven-development/references/self-contained-contract.md`
- `plugins/gate-driven-development/skills/gdd-systematic-debugging/SKILL.md`

#### User Action Required

- なし

#### Validation / Eval Impact

- `tests/validate-plugin.sh`
- Skill RED-GREEN Evidence（PR 本文）
