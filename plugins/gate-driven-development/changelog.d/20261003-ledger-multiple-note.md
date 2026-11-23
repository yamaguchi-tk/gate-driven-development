---
type: patch
---

#### Summary

`scripts/check-gate-ledger.sh` の steering 行は、pre-push の解決が複数の steering になったとき（multiple）に、pre-push の hook がどう選ぶか（tip の sha で始まる valid な Pre-Push Self Review を持つ steering〔cancelled を含む〕がちょうど 1 件ならそれを検査し、0 件・2 件以上なら steering-multiple で止める）を詳細に書くようにした。この行は pre-push を判定しない。push の前の読み方（スクリプトの header と `references/self-review-lanes.md`）に、詳細が `pre-push=multiple` なら gate 列と状態によらず読むことを足した。

#### Affected Files

- `plugins/gate-driven-development/scripts/check-gate-ledger.sh`
- `plugins/gate-driven-development/references/self-review-lanes.md`
- `plugins/gate-driven-development/tests/test_check_gate_ledger.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- `tests/test_check_gate_ledger.py` の `test_steering_gate_column_names_only_the_failing_gate` に詳細の確認を、`test_all_present`・`test_steering_gate_column_skips_pre_push_when_it_resolves_none` に詳細に注記が出ないことの確認を足した
