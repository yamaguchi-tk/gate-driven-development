---
type: patch
---

#### Summary

- 利用者から見える変更なし。並列の全量テストの負荷で、判定が正しいテストが落ちていた残りを直した。pre-push gate・pre-PR gate・root branch guard・Stop hook を起動するテストの壁時計の打ち切りを、hooks.json の timeout から、止まったときの保険（timeout の 6 倍）に替えた。打ち切りの無かった review-followup nudge のテストの helper には、同じ打ち切りを足した。durations の一覧のテストは、git を起動しない何もしないテストで確かめる。Stop hook の押し返しの判定の表は、hook を起動せず in-process で確かめる

#### Changed

- `tests/_timing_budget.py` に `hang_guard_seconds`（hooks.json の timeout の 6 倍）を置き、`tests/_merge_gate_support.py` の `HANG_GUARD` もここから導く
- `tests/_root_branch_guard_support.py` の `run_root_branch_guard` などの既定の打ち切りを `hang_guard_seconds` にした（壁時計 backstop の `GUARD_HOOK_TIMEOUT_SEC / 2` は変えない）。pre-push gate の FIFO のテスト（`test_steering_enumeration_unreadable.py`）、pre-PR gate の FIFO のテスト（`test_merge_gate_ledger_fail_closed.py`）、`test_pre_push_root_resolution.py` の 7 か所、`test_stop_hook_failopen.py` の打ち切りも同じ値にした
- `test_shell_lexer_gates.py` の深いバッククォートのテストは、壁時計ではなく CPU 時間を hooks.json の timeout と比べる
- `test_pytest_ini_durations_contract.py` は、一時ディレクトリの何もしないテストを `-c` で plugin の `pytest.ini` を読ませて回す
- `test_stop_hook_autonomy_pushback.py` の `MergeIntentAfterMergeDenialTest` の判定の表（拒否なら止める・拒否でなければ押し返す・壊れた行が混ざる）は、`merge_wait_reason` を in-process で呼び、gh の `subprocess.run` を差し替えて確かめる。入口から起動するのは、拒否で止まる 1 本・押し返す 1 本・試行の多い transcript の 1 本・記録の場所を確かめる陽性対照の 1 本の 4 本だけにした
- `tests/_review_followup_nudge_support.py` の `_run_hook` に打ち切り（`hang_guard_seconds`）を足した。`test_review_followup_nudge_hook_gh.py` の gh の待ちの頭打ちのテストは、壁時計ではなく、hook が gh を待つ `sleep 1` の回数（6 回）で確かめる

#### Added

- `tests/test_timing_budget_contract.py` の `HangGuardSecondsTests`（打ち切りが hooks.json の timeout の 6 倍で、root branch guard の helper の既定がその値であることを固定する）

#### Affected Files

- `tests/_timing_budget.py`
- `tests/_merge_gate_support.py`
- `tests/_root_branch_guard_support.py`
- `tests/test_steering_enumeration_unreadable.py`
- `tests/test_merge_gate_ledger_fail_closed.py`
- `tests/test_pre_push_root_resolution.py`
- `tests/test_stop_hook_failopen.py`
- `tests/test_shell_lexer_gates.py`
- `tests/test_pytest_ini_durations_contract.py`
- `tests/test_stop_hook_autonomy_pushback.py`
- `tests/test_timing_budget_contract.py`
- `tests/_review_followup_nudge_support.py`
- `tests/test_review_followup_nudge_hook_gh.py`
- `docs/adr/2026-09-12-x37-test-timing-flakiness.md`（repo 直下）

#### User Action Required

- なし

#### Validation / Eval Impact

- `tests/test_timing_budget_contract.py`
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
