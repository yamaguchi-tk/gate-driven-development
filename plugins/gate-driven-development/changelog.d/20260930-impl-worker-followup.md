---
type: patch
---

#### Summary

実装 worker の起動と、model を検査する hook の案内を、旧#249 の選び方に揃えた。

- hook は、model を省略した sonnet の worker（`gdd-implementation-worker`）を opus 必須の工程で起動したとき、「model="sonnet" が指定されています」ではなく、agent 定義の model で動くことを伝え、先に `Next Action` を確かめるよう促す。この工程のまま起動するなら、heavy（`Gate Rounds` ≥ 2 は remediation）の worker を model 省略で使い、`## Worktree` と `## Plugin Root` を渡すよう案内する
- 実装の工程で model 未指定の起動には、worker を起動する場合に限って 3 つの worker を案内し、`## Worktree` と `## Plugin Root` を渡すことまで伝える。worker 以外の起動には model の明示を求める
- `references/fixed-models.md` の、model 省略時の免除の記述を、hook の挙動（免除は opus に固定した agent だけ、sonnet の worker は工程で判定）に合わせた
- remediation worker を起動する箇所（`gdd-implementation-gating`・`references/subagent-dispatch.md`）に、`## Worktree` と `## Plugin Root` を渡すことを書いた
- heavy・remediation の worker の description と `remediation_loop` tier の段落に、`BLOCKED` の昇格先としての使い方を書いた。昇格で remediation worker を使っても `remediation_loop` tier は始まらない

あわせて、同じファイルの前からの食い違いを直した。

- `gdd-model-routing` の「`max` は使わない」を、通常は 4 段階を使い、`max` は使う用途（`remediation_loop`・`independent_review`・`gdd-planning-reviewer`）に限る、に揃えた
- `gdd-implementation-gating` § Review Set の security reviewer の適用条件を、Step 3 と `references/reviewer-selection.md` § Gate Rules の両方への参照にした（どちらかに当たれば selected）。`references/fixed-models.md` の `complex` の条件の security-sensitive も同じ 2 つを指す
- `gdd-task-breakdown` の tasklist の雛形の見出しを、正準形 `### Task: T-N <名前>` にした
- `references/task-breakdown-steps.md` § Task Self-Review の番号の重複（9・10 が 2 回）を振り直した

#### Changed

- `hooks/scripts/run-agent-dispatch-model-gate-hook.sh`: agent 定義の model で判定したことを finding に載せ、案内文を分けた
- `references/fixed-models.md`・`references/subagent-dispatch.md`・`references/task-breakdown-steps.md`
- `skills/gdd-implementation-gating/SKILL.md`・`skills/gdd-model-routing/SKILL.md`・`skills/gdd-task-breakdown/SKILL.md`
- `agents/gdd-implementation-worker-heavy.md`・`agents/gdd-remediation-worker.md` の description

#### Affected Files

- `plugins/gate-driven-development/hooks/scripts/run-agent-dispatch-model-gate-hook.sh`
- `plugins/gate-driven-development/references/fixed-models.md`
- `plugins/gate-driven-development/references/subagent-dispatch.md`
- `plugins/gate-driven-development/references/task-breakdown-steps.md`
- `plugins/gate-driven-development/skills/gdd-implementation-gating/SKILL.md`
- `plugins/gate-driven-development/skills/gdd-model-routing/SKILL.md`
- `plugins/gate-driven-development/skills/gdd-task-breakdown/SKILL.md`
- `plugins/gate-driven-development/agents/gdd-implementation-worker-heavy.md`
- `plugins/gate-driven-development/agents/gdd-remediation-worker.md`
- `plugins/gate-driven-development/tests/test_implementation_worker_agents.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- `tests/test_implementation_worker_agents.py` に、hook スクリプトの入口から、sonnet の worker を opus 必須の工程で model 省略で起動したときの案内、model を明示したときの案内、実装の工程の案内を確かめるテストを足した
