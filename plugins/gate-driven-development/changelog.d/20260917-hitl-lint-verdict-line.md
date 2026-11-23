---
type: patch
---

#### Summary

PR 旧#93 で `validate-plugin.sh` に入った VERDICT 番兵（check が rc=0 で終わるとき `VERDICT: <check_name>: OK|SKIP` の行を必須にする）に対し、`tests/checks/hitl-required-fields-lint.sh` だけが VERDICT 行を出していなかった。そのため main の `validate-plugin.sh` は、manifest の最後の check で `VERDICT_MISSING` になり、rc=1 で終わっていた。

#### Fixed

- `hitl-required-fields-lint.sh` の成功時に `VERDICT: hitl-required-fields-lint: OK` を出すようにした

#### Affected Files

- `plugins/gate-driven-development/tests/checks/hitl-required-fields-lint.sh`
- `plugins/gate-driven-development/tests/test_validate_plugin_verdict_sentinel.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- `tests/test_validate_plugin_verdict_sentinel.py` にテストを 1 本追加した。実物の `hitl-required-fields-lint.sh` を validate-plugin.sh と同じ環境変数（`ROOT`・`PYTHON_BIN`）で実行し、`VERDICT: hitl-required-fields-lint: OK` が行全体で一致して出ることを確かめる（全 check の VERDICT 行の有無は、validate-plugin.sh の番兵が実行時に判定する）
- `python3 -m pytest plugins/gate-driven-development/tests/ -q -n auto`
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
