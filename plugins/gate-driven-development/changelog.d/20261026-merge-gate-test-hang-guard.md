---
type: patch
---

#### Summary

- 利用者から見える変更なし。merge gate の hook を実起動するテストの壁時計の打ち切りを、hooks.json の timeout と同じ 10 秒から、止まったときの保険（hooks.json の timeout の 6 倍）に替えた。並列の全量テストと外部の負荷の下で、判定が正しいテストが `subprocess.TimeoutExpired` で落ちていた

#### Changed

- `tests/_merge_gate_support.py` に `HOOK_TIMEOUT`・`HANG_GUARD` を置き、`_run_hook` の既定の打ち切りを `HANG_GUARD` にした。`test_merge_gate_ledger_fail_closed.py` は同じ値を import し、`test_merge_gate_followup_findings.py` の hook の起動も同じ値を使う。merge gate の FIFO のテスト（`test_merge_gate_ledger_fail_closed.py` の 2 本、`test_steering_enumeration_unreadable.py` の 1 本）も、打ち切りを hooks.json の timeout から `HANG_GUARD` に替えた。lib を壊したコピーで hook を直接起動する `test_shell_lexer_gates.py` の 1 本と `test_merge_gate_python_batch.py` の helper も `HANG_GUARD` を使う

#### Added

- `tests/test_merge_gate_hang_guard_contract.py`（打ち切りの値が hooks.json の timeout から導かれ、hook を起動する 2 つの helper がその値を使うことを固定する）

#### Affected Files

- `tests/_merge_gate_support.py`
- `tests/test_merge_gate_ledger_fail_closed.py`
- `tests/test_merge_gate_followup_findings.py`
- `tests/test_steering_enumeration_unreadable.py`
- `tests/test_shell_lexer_gates.py`
- `tests/test_merge_gate_python_batch.py`
- `tests/test_merge_gate_hang_guard_contract.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- `tests/test_merge_gate_hang_guard_contract.py`
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
