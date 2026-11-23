---
type: patch
---

#### Summary

- 利用者から見える変更なし。review-followup nudge・pre-push gate・root-branch guard が、tool_input の実行先（`tool_input.cwd` か `tool_input.workdir`）を payload の最上位の `cwd` より先に読むことを、両方の key のテストで固定した

#### Affected Files

- `plugins/gate-driven-development/tests/test_gates_toplevel_cwd.py`
- `plugins/gate-driven-development/tests/test_root_branch_guard_toplevel_cwd.py`
- `plugins/gate-driven-development/tests/test_merge_gate_same_repo_worktree.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- 追加: `test_gates_toplevel_cwd.py` の `ReviewFollowupNudgeToplevelCwdTests.test_tool_input_cwd_comes_before_the_toplevel_cwd`（`cwd`・`workdir`）
- `cwd`・`workdir` の両方の key で回す: `PrePushGateToplevelCwdTests.test_tool_input_cwd_still_wins_over_the_toplevel_cwd`、`test_root_branch_guard_toplevel_cwd.py` の `test_tool_input_cwd_comes_before_toplevel_cwd`
- 関係するテスト（`scripts/light-lane-related-tests.py`）
- `tests/validate-plugin.sh`
