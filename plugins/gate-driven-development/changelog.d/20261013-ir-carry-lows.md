---
type: patch
---

#### Summary

`references/self-review-lanes.md` の、standard の push 前の `Independent Review` 行の sha（push 対象 tip）にも、Independent Review の引き継ぎで引き継いだものを含むと書いた。`skills/gdd-pr-review/SKILL.md` の pre-push gate の `independent-review-stale` の説明に、引き継げるときを除くと書いた。`scripts/check-gate-ledger.sh` の Self Review の sha がずれた行は、引き継ぎの例外の後ろの案内を、ほかの行と同じ回復の文から作るようにした。判定は変えない。

#### Affected Files

- `plugins/gate-driven-development/references/self-review-lanes.md`
- `plugins/gate-driven-development/skills/gdd-pr-review/SKILL.md`
- `plugins/gate-driven-development/scripts/check-gate-ledger.sh`
- `plugins/gate-driven-development/tests/test_merge_gate_ir_carry.py`
- `plugins/gate-driven-development/changelog.d/20261013-ir-carry-followup.md`（`amends:`。Validation から、main で削除したテストの記述を外した）

#### User Action Required

- なし

#### Validation / Eval Impact

- `tests/test_merge_gate_ir_carry.py`（Medium Disposition の経路の allow も、終了コードと出力の空で見る）・`tests/test_check_gate_ledger.py`
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
