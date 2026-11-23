---
type: patch
---

#### Summary

planning 差し戻し後に `tasklist.md` の全セクションを作り直すときに、何を引き継ぎ、何が途切れるかを書いた。

- `Completion Rounds` / `Completion Baseline` の行は作り直しでも消さずに引き継ぐ（completion-check の Round 上限が初回に戻らないようにする）
- 並列 batch の例外（`human_recheck_required` の carry-over、`design_detail_only` の単独発火）では、carry-over した `Completed Tasks` と継続中の他タスクの `Current Task` を残す
- 作り直すと task id と `Fix Attempts`・`Gate Rounds` が振り直され、同じ `Current Task` 単位の上限（blind `implementation_fix_only` の 3/3・Reviewer Loop Escape Hatch・承認後の 2/2・root cause の 3 連続・remediation ADR の 2 件）の数えは途切れる。作り直しをまたいで数え続けるのは `Scope Drift Counter` で、Scope Drift Guard は再評価のきっかけ（上限ではない）。`planning_rework_required` では人の再承認だけが残る
- `design_detail_only` で残した commit が既に満たす AC は、既存 coverage inspection で閉じるか、まだカバーしていない挙動だけを Planned RED にする

drift 経由の `human_recheck_required` での Refactor Gate の追加リセットは、作り直しで `Refactor Gate Status` が `absent` になり、build 完了後に `gdd-implementation-gating` が `gdd-refactor-planning` へ進める形に直した。`state.md` で `pending` に戻す・design-gating 通過時に `Next Action=gdd-refactor-planning` にする・Refactor Task を marker 付きで残す、の 3 つをやめた。Task Size 再評価マトリクスの Scope Drift Guard 行の `Refactor Gate Status` も `absent` にし、`Fix Attempts` を振り直しにした。

#### Affected Files

- `plugins/gate-driven-development/references/state-machine.md`
- `plugins/gate-driven-development/references/task-breakdown-steps.md`
- `plugins/gate-driven-development/references/rollback-patterns.md`
- `plugins/gate-driven-development/references/gate-checklists.md`
- `plugins/gate-driven-development/skills/gdd-completion-check/SKILL.md`
- `plugins/gate-driven-development/skills/gdd-task-breakdown/SKILL.md`
- `plugins/gate-driven-development/references/state-field-tiers.md`
- `plugins/gate-driven-development/references/bounce-log-schema.md`

#### User Action Required

- なし

#### Validation / Eval Impact

- `tests/validate-plugin.sh`
- Skill RED-GREEN Evidence（PR 本文）
