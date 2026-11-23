---
type: patch
---

#### Summary

- done マーカーを出した後（`Resume From=external-review-waiting` の暫定の done を除く）に、PR 後のレビューの finding を Hotfix Lane に回す route（`human_recheck_required`・`planning_rework_required`）に決めた主体は、skill・節を問わず（`gdd-systematic-debugging` も `gdd-pr-review-followup` も）、元の steering に `Fix Findings:` を書かない代わりに、同じ形の行を差し戻しを受けた steering の `worklog.md` の `## Hotfix Findings` に書く。systematic-debugging の戻り先は、同じ steering の復帰シーケンスではなく Hotfix Lane の新しい steering になる
- Hotfix Lane の新しい steering を起こすときは、`Origin Steering:` を記録する者が同じ段で（元の worktree を cleanup する前に）、その行をそのまま新しい steering の `worklog.md` の `## Origin Findings` に写す。`worklog.md` が読めない（マージ後の cleanup で消えた等）か見出しが無ければ、その PR のコメントと review thread から Hotfix Lane に回したクラスタの指摘を同じ形で起こし、新しい steering の human check で承認された行だけを写す。どちらからも取れなければ写さずに `human-check-waiting` で止める
- 新しい steering の `gdd-task-breakdown`（express では `gdd-test-driven-development` Step 1）は、tasklist を作るときに `## Origin Findings` の行を、作った task の `Fix Findings:` に写す。写し先は再オープンと同じ規則（finding のファイルを `Files:` に持つ task、AC を名指す finding はその AC の primary owner、決められない行は remediation task）。Task-Breakdown Template と TDD Template（express）の読むファイルに `worklog.md` を足した

#### Changed

- `skills/gdd-systematic-debugging/SKILL.md`（§ Failure Routing の前置き）
- `skills/gdd-pr-review-followup/SKILL.md`（Route）
- `skills/gdd-test-driven-development/SKILL.md`（Step 1 の Express Path）
- `references/state-machine.md`（§ tasklist.md の canonical state）
- `references/state-field-tiers.md`（Tier 3 の `Fix Findings`）
- `references/task-breakdown-steps.md`（手順 2）
- `references/phase-progression.md`（§ Post-PR / Post-Merge Contract の 2・3）
- `references/subagent-dispatch.md`（Task-Breakdown Template・TDD Template の読むファイル）
- `skills/gdd-using-git-worktrees/SKILL.md`（hotfix の実装場所の規約）

#### Affected Files

- `skills/gdd-systematic-debugging/SKILL.md`
- `skills/gdd-pr-review-followup/SKILL.md`
- `skills/gdd-test-driven-development/SKILL.md`
- `references/state-machine.md`
- `references/state-field-tiers.md`
- `references/task-breakdown-steps.md`
- `references/phase-progression.md`
- `references/subagent-dispatch.md`
- `skills/gdd-using-git-worktrees/SKILL.md`

#### User Action Required

- なし

#### Validation / Eval Impact

- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
