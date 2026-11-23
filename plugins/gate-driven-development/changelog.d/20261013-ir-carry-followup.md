---
type: patch
---

#### Summary

merge gate が `review-wait-not-elapsed`・`independent-review-missing` で止めるとき、引き継ぎを試せた場面（`Independent Review` の sha が HEAD と違い、high 0・blocking 0）では、`Independent Review Carry` 行が無いときも含めて、引き継げない理由と引き継ぎの行の案内を観測値に出す（先頭の reason code が別の検査のときも出る）。引き継ぎの判定は、hook の起動からの経過を秒の切り捨ての 1 秒も差し引いて測り、時計を張れない環境（Windows など）では「この環境では時間の上限を張れない」で引き継がない。`references/independent-review.md`・`references/self-review-lanes.md`・`skills/gdd-pr-review-followup/SKILL.md` の、`Independent Review` の sha を tip・HEAD に合わせる規定に、引き継ぎの例外を書いた。`skills/gdd-completion-check/SKILL.md` には、引き継ぐときに sha を書き換えてよい行（`Pre-Push Self Review`・`Pre-PR Self Review`・`Medium Disposition`）を名指しし、`Independent Review` の行は旧 sha のまま残すと書いた。`scripts/check-gate-ledger.sh` の Self Review の sha がずれた行では、引き継ぎの例外を「sha だけを書き換えない」の案内より先に置き、2 つが食い違わないようにした。`references/self-review-lanes.md` の引き継ぎの節は、引き継げないときに止める reason code を gate ごとに書き分け、判定が確かめることを狭めて書き、ブロックの中でどちらかの側が削った行が merge で戻る形と、Windows で引き継がないことを限界に足した。判定の条件・閾値・行の書式は変えない。

#### Affected Files

- `plugins/gate-driven-development/hooks/scripts/run-merge-gate-hook.sh`
- `plugins/gate-driven-development/hooks/scripts/lib/gate-ledger.sh`
- `plugins/gate-driven-development/hooks/scripts/lib/ir_merge_carry.py`
- `plugins/gate-driven-development/scripts/check-gate-ledger.sh`
- `plugins/gate-driven-development/references/self-review-lanes.md`
- `plugins/gate-driven-development/references/independent-review.md`
- `plugins/gate-driven-development/skills/gdd-pr-review-followup/SKILL.md`
- `plugins/gate-driven-development/skills/gdd-completion-check/SKILL.md`
- `plugins/gate-driven-development/changelog.d/20261013-ir-merge-carry.md`（`amends:`。merge gate が止める reason code を gate ごとに書き分けた）

#### User Action Required

- なし

#### Validation / Eval Impact

- `tests/test_merge_gate_ir_carry.py`・`tests/test_ir_merge_carry.py`
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
