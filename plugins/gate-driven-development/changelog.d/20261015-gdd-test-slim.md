---
type: patch
---

#### Summary

- 利用者から見える変更なし。テストの中で同じ定義が 2 回以上書かれていた helper 14 組を、1 つの定義の参照にまとめた（テストの本数・assert は変えない）

#### Affected Files

- `plugins/gate-driven-development/tests/test_done_guard_state_line_break_chars_contract.py`
- `plugins/gate-driven-development/tests/test_peer_turn_write_boundary_e2e_contract.py`
- `plugins/gate-driven-development/tests/test_pr_review_followup_polling_cap_contract.py`
- `plugins/gate-driven-development/tests/test_pre_pr_gate_contract.py`
- `plugins/gate-driven-development/tests/test_pre_push_tip_sha_resolution_contract.py`
- `plugins/gate-driven-development/tests/test_queued_task_notification.py`
- `plugins/gate-driven-development/tests/test_session_start_no_shadow_marker.py`
- `plugins/gate-driven-development/tests/test_steering_write_fence_scan.py`
- `plugins/gate-driven-development/tests/test_stop_failure_hook_contract.py`
- `plugins/gate-driven-development/tests/test_stop_hook_hitl_lint_gate_e2e.py`
- `plugins/gate-driven-development/tests/test_stop_hook_stop_reason_unit.py`
- `plugins/gate-driven-development/tests/test_task_binding_worktree_path_absolute.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- `pytest --collect-only` で集めるテストの一覧が、変更の前後で同じ（4,646 本）
- 関係するテスト（`scripts/light-lane-related-tests.py`）
- `tests/validate-plugin.sh`
