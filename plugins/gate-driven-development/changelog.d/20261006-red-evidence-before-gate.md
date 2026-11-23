---
type: patch
---

#### Summary

実装 gate に回す前に、gate にかける task の `#### RED Evidence` を確かめて書き写すようにした。

- `gdd-subagent-driven-implementation` で `Next Action=gdd-implementation-gating` にする前（手順 2a・17・20）と、`gdd-systematic-debugging` の並列修正パスで gate に進む前に、gate にかける task の `#### RED Evidence` を確かめる
- 節か行が欠けていたら、その task で観測した RED の結果（TDD の runner・controller・worker のどれが観測したものでもよい。RED 再現テストを含む）を `gdd-test-driven-development` の形式で書き写してから gate に回す。無い `Worktree:` の行は、Worktree Binding Precheck で今観測した値で足す。既にある `Worktree:` の値が今の観測値と違うときは書き換えない
- 観測した RED が無い task は、推定で埋めずにそのまま gate に回す
- これまでは、`gdd-completion-check` の差し戻しで作った remediation task や、`gdd-test-driven-development` を経ずに進めた task で `#### RED Evidence` が欠け、`gdd-implementation-gating` の Step 1d が High で差し戻していた。Step 1d の判定は変えていない

#### Affected Files

- `plugins/gate-driven-development/skills/gdd-subagent-driven-implementation/SKILL.md`
- `plugins/gate-driven-development/skills/gdd-systematic-debugging/SKILL.md`

#### User Action Required

- なし

#### Validation / Eval Impact

- `bash tests/validate-plugin.sh`
- 関係するテスト（`scripts/light-lane-related-tests.py --run`）
- Skill RED-GREEN Evidence は PR 本文に書く
