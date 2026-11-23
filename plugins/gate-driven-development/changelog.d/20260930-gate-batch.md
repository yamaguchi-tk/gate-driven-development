---
type: minor
---

#### Summary

逐次実行の task をまとめて impl-gating を 1 回だけ回す `Gate Batch` を足した。これまでは task ごとに gate を回していた（1 本あたり約 $10、8 task の steering で 15 本）。

まとめてよいのは、次のすべてを満たす task である。

- standard で、task 数が 3 以上
- 依存順に連続している
- 最大 3 個
- 各 task が自分の `Planned RED / E2E` を持つ

task-breakdown が `## Execution Plan` に `Gate Batch <N>` を宣言し、実装は Gate Batch の最後の task まで進めてから gate に回す。`Mode: parallel` とは併用しない。

Gate Batch は 1 つの gate 単位として判定する。

- どの出口から `changes_requested` を返すときも、batch の全 task を `changes_requested` にし、`Gate Rounds` を足すときは全 task に同じだけ足す
- finding には対象の task id を付ける。対象の task を `Execution Status: in_progress` に戻して `Current Task` の先頭に移し、remediation はその task だけを直す。`Fix Attempts` は systematic-debugging が対象の task に足す
- 承認したら全 task を `Completed Tasks` に移し、それぞれに `Reviewed by:` を付ける
- reviewer selection の Task ID は `Gate Batch <N>` と書く

task ごとの混合判定にしないのは、impl-gating の返却と `Review Status` が gate 全体で 1 つの状態しか持たないためである。並列バッチの gate の扱いは変えていない。

`Current Task` には、同じ batch の実装を終えた task と実装中の task が並ぶ。文脈を注入する hook（UserPromptSubmit・plan reread）は task 名を最初の task から読むので、実装中の task を先頭に置く。

#### Changed

- `references/task-breakdown-steps.md` に § Gate Batch（条件・記録の形・判定の単位・`Current Task` の並び）を追加
- `skills/gdd-task-breakdown/SKILL.md`
  - 手順 6 で、並列にしないときに Gate Batch を組む
  - `Current Task` の件数制約に、Gate Batch の場合を追加
  - `Execution Status: completed` を、実装の手順 12b の条件を満たした後（gate の前でもよい）に揃えた
- `skills/gdd-subagent-driven-implementation/SKILL.md`
  - 手順 2b で、`Execution Status: completed` でない task（差し戻し後は対象の task すべて）を対象にする
  - 手順 17 で、次の task が同じ Gate Batch なら gate に回さず、`Pending Tasks` から外して `Current Task` の先頭に移し、TDD へ進む
- `skills/gdd-test-driven-development/SKILL.md` で、`Execution Status: completed` でない task（差し戻し後は finding の対象の task）を対象にする
- `skills/gdd-implementation-gating/SKILL.md`
  - Step 9 に Gate Batch の差し戻し（Step 1・1d・8a の出口にも当てる）を、Step 11 に承認を追加
  - RED Evidence の照合（1d）と security reviewer の適用判定を batch の全 task に当てる
  - reviewer selection の Task ID を `Gate Batch <N>` にする
- `skills/gdd-systematic-debugging/SKILL.md` で、`Fix Attempts` を finding の対象の task に足す
- `references/state-machine.md`（`## Execution Plan`・`## Current Task`・件数制約・`Fix Attempts`）と `references/subagent-dispatch.md`（impl-gating の Template の転記）を揃えた

#### Affected Files

- `plugins/gate-driven-development/references/task-breakdown-steps.md`
- `plugins/gate-driven-development/references/state-machine.md`
- `plugins/gate-driven-development/references/subagent-dispatch.md`
- `plugins/gate-driven-development/skills/gdd-task-breakdown/SKILL.md`
- `plugins/gate-driven-development/skills/gdd-subagent-driven-implementation/SKILL.md`
- `plugins/gate-driven-development/skills/gdd-test-driven-development/SKILL.md`
- `plugins/gate-driven-development/skills/gdd-implementation-gating/SKILL.md`
- `plugins/gate-driven-development/skills/gdd-systematic-debugging/SKILL.md`
- `plugins/gate-driven-development/tests/test_gate_batch_hook_injection.py`

#### User Action Required

- なし。すでに tasklist.md がある steering には Gate Batch が無いので、これまでどおり task ごとに gate する

#### Validation / Eval Impact

- `tests/test_gate_batch_hook_injection.py` を追加した。Gate Batch 中の tasklist.md で UserPromptSubmit と plan reread の hook を実際に起動し、先頭の実装中の task 名が注入されること、ほかの field の読み方を固定する
- 手順 17 と Step 9 の差し戻しは、文言のテストではなく PR の `Skill RED-GREEN Evidence`（pressure scenario 2 本）で確かめた
