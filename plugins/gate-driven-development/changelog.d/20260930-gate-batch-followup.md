---
type: patch
---

#### Summary

Gate Batch で、task ごとに数えるものと対象の task の決め方を書いた。これまでは「同じ `Current Task`」で数える規定が、batch の全 task を `changes_requested` にする規定と並んでいて、batch 全体で数えるのか task ごとに数えるのかが決まらなかった。

- `Fix Attempts` の 3/3・5/5・2/2（Reviewer Loop Escape Hatch を含む）、root cause カテゴリの連続、remediation 由来 ADR entry の件数は、task ごとに数え、finding の対象の task にだけ足す。`Gate Rounds` はこれまでどおり全 task に同じだけ足す
- ADR の `Origin` には、その ADR を書いた remediation の対象の task id（例: `remediation / T-2`）を書く
- 対象の task を決められない finding（`## Worktree` が解決できない、どの task にも属さない scope 外の変更など）は、batch の全 task を対象にする
- 対象が複数で severity が同じなら、`Current Task` には `Gate Batch <N>` に書いた順に並べる。全 task を `changes_requested` にするのは reviewer status の話で、`Execution Status: in_progress` に戻すのは対象の task だけである
- `gdd-implementation-gating` Step 8a が finding 無しで発火したときは、ADR entry が 2 件以上になった task を対象にする
- 差し戻し後、実装の手順 1b は `Execution Status: in_progress` を対象の task だけに書く。実装を終えた task の `completed` は変えない
- reviewer selection は、Gate Batch では batch ごとに残し、security reviewer の条件は batch のどれかの task に当たるかで見る

#### Changed

- `references/state-machine.md` § Remediation Loop Safety に Gate Batch の項を足した（数え方と対象の task の正本）
- `skills/gdd-implementation-gating/SKILL.md` の Step 8a・Step 9、`skills/gdd-systematic-debugging/SKILL.md` § Loop Safety、`references/rollback-patterns.md` § Reviewer Loop Escape Hatch、`references/phase-progression.md` の方式転換の行を、task ごとに数えると揃えた
- `references/task-breakdown-steps.md` § Gate Batch の要約を、Step 9 の「どの出口からも全 task を差し戻す」に揃えた
- `skills/gdd-subagent-driven-implementation/SKILL.md` の手順 1b、`references/reviewer-selection.md`、`references/self-contained-contract.md` の単一 task の記述に Gate Batch の読み方を足した

#### Affected Files

- `plugins/gate-driven-development/references/state-machine.md`
- `plugins/gate-driven-development/references/rollback-patterns.md`
- `plugins/gate-driven-development/references/phase-progression.md`
- `plugins/gate-driven-development/references/task-breakdown-steps.md`
- `plugins/gate-driven-development/references/reviewer-selection.md`
- `plugins/gate-driven-development/references/self-contained-contract.md`
- `plugins/gate-driven-development/skills/gdd-implementation-gating/SKILL.md`
- `plugins/gate-driven-development/skills/gdd-systematic-debugging/SKILL.md`
- `plugins/gate-driven-development/skills/gdd-subagent-driven-implementation/SKILL.md`

#### User Action Required

- なし

#### Validation / Eval Impact

- 文書だけの変更。Gate Batch の 5 つの状況（Escape Hatch の数え方・ADR の `Origin`・task に属さない finding・finding 無しの 8a・1b の書き込み先）を、変更前後の文書で controller 役に答えさせ、変更前は 5 問とも文書から決まらず、変更後は決まることを確かめた
