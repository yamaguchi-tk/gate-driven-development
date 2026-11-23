---
type: patch
---

#### Summary

利用者から見える変更なし。merge gate の長い入力のテスト 3 本は、壁時計で上限を見ていたので、並列の実行や別のセッションの負荷で落ちていた。CPU 時間で見るように直した。

#### Changed

- `tests/test_merge_gate_ledger_fail_closed.py` の `test_many_leading_zeros_do_not_time_out` と `test_oversized_state_url_fails_closed_without_waiting` は、hook の CPU 時間（`timing_budget()`）が hook の timeout より短いことを見る。壁時計は、止まったときの保険（subprocess の timeout）だけにする
- `tests/test_merge_gate_cd_after_merge.py` の `test_many_segments_before_the_merge_are_read_in_linear_time` は、切り出しの時間を `timing_budget()` の CPU 時間で測る
- `tests/test_merge_gate_ledger_fail_closed.py` の hook の timeout は、`hooks.json` から `hook_timeout_seconds()` で読む
- FIFO を待たずに返すことを見るテストは、待つ間に CPU を使わないので、壁時計のまま残す

#### Affected Files

- `plugins/gate-driven-development/tests/test_merge_gate_ledger_fail_closed.py`
- `plugins/gate-driven-development/tests/test_merge_gate_cd_after_merge.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- `python3 -m pytest tests/test_merge_gate_ledger_fail_closed.py tests/test_merge_gate_cd_after_merge.py tests/test_steering_enumeration_unreadable.py`
- `bash tests/validate-plugin.sh`
- `run-merge-gate-hook.sh` の `_MG_URL_MAX` を外した退行で、`test_oversized_state_url_fails_closed_without_waiting` が CPU 時間の判定で落ちることを確かめた
