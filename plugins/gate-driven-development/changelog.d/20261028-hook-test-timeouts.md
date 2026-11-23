---
type: patch
---

#### Summary

- 利用者から見える変更なし。hook や gate の lib を起動するテストのうち、壁時計の上限や literal の打ち切りが残っていたもの、打ち切りが無かったものを、止まったときの保険（`hang_guard_seconds`。hooks.json の timeout の 6 倍）にそろえた。打ち切りの値を固定するテストも足した

#### Changed

- `test_stop_hook_autonomy_pushback.py` の `GuardSurvivesPushbackFailureTest`: 入口から起動する 4 本から壁時計 8 秒の上限を外し、打ち切りを Stop hook の `hang_guard_seconds` にした。遅い gh の stub は `exec sleep 600` にして、打ち切りが効かないと戻らないようにした。大きな transcript の 1 本は、CPU 時間を hooks.json の timeout と比べる
- pre-push gate の lib を起動するテスト（`test_pre_push_gate_optout_contract.py` の 2 か所、`test_push_command_parse_optout.py` の 1 か所）と、merge gate の lib を起動するテスト（`test_merge_gate_followup_findings.py`、`test_merge_gate_hook_evidence_parsing.py` の 7 か所、`test_merge_gate_python_batch.py` の 2 か所、`test_ir_merge_carry.py`）と、Stop hook の lib を起動するテスト（`test_next_plan_check_fence.py`、`test_regular_file.py`）の literal の 10 秒を、それぞれの hook の `hang_guard_seconds` にした
- review-followup nudge の hook を helper を通さずに起動する 2 か所（`test_review_followup_nudge_hook.py`、`test_review_followup_nudge_hook_gh.py`）に、打ち切り（`HANG_GUARD`）を足した

#### Added

- `GuardSurvivesPushbackFailureTest.test_pushback_time_limit_fits_the_hook_timeout`（押し返しの持ち時間の上限が、Stop hook の hooks.json の timeout より小さいことを固定する）
- `test_timing_budget_contract.py` の `HangGuardSecondsTests`: `run_root_branch_guard_raw` の打ち切りが hang guard であることと、`hang_guard_seconds` が一致の無い hook 名で `LookupError` を出す（既定値に倒さない）ことを固定する 2 本

#### Affected Files

- `tests/test_stop_hook_autonomy_pushback.py`
- `tests/test_pre_push_gate_optout_contract.py`
- `tests/test_push_command_parse_optout.py`
- `tests/test_merge_gate_followup_findings.py`
- `tests/test_merge_gate_hook_evidence_parsing.py`
- `tests/test_merge_gate_python_batch.py`
- `tests/test_review_followup_nudge_hook.py`
- `tests/test_review_followup_nudge_hook_gh.py`
- `tests/test_timing_budget_contract.py`
- `tests/test_ir_merge_carry.py`
- `tests/test_next_plan_check_fence.py`
- `tests/test_regular_file.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- 上の Affected Files のテスト
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
