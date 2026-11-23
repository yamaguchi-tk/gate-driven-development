---
type: patch
---

#### Summary

planning 差し戻し後の `tasklist.md` の作り直し（差し戻しの route を問わず全セクションを初期化する）に、残っていた記述をそろえた。

- gdd-requirements-amendment: `design_detail_only` に落ちるときの、影響 AC の task だけの部分再整備を許す記述を削り、どの route でも全セクションを再生成すると書いた
- gdd-task-breakdown の SKILL.md: 作り直しで `Reviewed by:` のある完了タスクは、先に `Pending Tasks` へ移す書き込みを挟んでから消すと書いた（今までは SKILL.md には書いていなかった）
- `references/rollback-patterns.md` の Refactor Task の除去と、`references/state-machine.md` の `human_recheck_required` の初期化にも、同じ 2 回の書き込みを書いた
- `references/state-machine.md` の再評価マトリクスで、`human_recheck_required` の `Refactor Gate Status` を「継続（tasklist を部分保持するため）」から「`absent`（tasklist 再生成で消える）」に直した
- `references/prompt-contract-map.md`: 作り直しの所有者を、`Route In Progress` ではなく `references/task-breakdown-steps.md` 手順 2 と書いた

#### Affected Files

- `plugins/gate-driven-development/skills/gdd-requirements-amendment/SKILL.md`
- `plugins/gate-driven-development/skills/gdd-task-breakdown/SKILL.md`
- `plugins/gate-driven-development/references/rollback-patterns.md`
- `plugins/gate-driven-development/references/state-machine.md`
- `plugins/gate-driven-development/references/prompt-contract-map.md`

#### User Action Required

- なし

#### Validation / Eval Impact

- `tests/validate-plugin.sh`
- Skill RED-GREEN Evidence（PR 本文）
