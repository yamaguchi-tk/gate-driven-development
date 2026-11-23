---
type: patch
---

#### Summary

`scripts/check-gate-ledger.sh` の Self Review の sha がずれた行の案内を、「それ以外は、レビューを回し直してから行を書く（sha だけを書き換えない）。…」にした（「それ以外の証跡を直すときは」が Independent Review 以外の証跡とも読めたため）。`skills/gdd-pr-review/SKILL.md` に、`Independent Review` 行は pre-push gate（push 対象 tip と比べる）だけでなく pre-PR gate（HEAD と比べる）も検査すると書いた。判定は変えない。

#### Affected Files

- `plugins/gate-driven-development/scripts/check-gate-ledger.sh`
- `plugins/gate-driven-development/skills/gdd-pr-review/SKILL.md`
- `plugins/gate-driven-development/tests/test_check_gate_ledger.py`
- `plugins/gate-driven-development/changelog.d/20261013-ir-carry-lows.md`（`amends:`。この PR で変えた文面の引用を外した）

#### User Action Required

- なし

#### Validation / Eval Impact

- `tests/test_check_gate_ledger.py`（sha がずれた行と行が無いときの回復の本文が同じか）
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
