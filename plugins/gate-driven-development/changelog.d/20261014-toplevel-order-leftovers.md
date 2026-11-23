---
type: patch
---

#### Summary

- 利用者から見える変更なし。pre-PR gate が、tool_input の実行先（`tool_input.cwd` か `tool_input.workdir`）を payload の最上位の `cwd` より先に読むことを、両方の key のテストで固定した

#### Affected Files

- `plugins/gate-driven-development/tests/test_gates_toplevel_cwd.py`
- `plugins/gate-driven-development/tests/test_merge_gate_hook_gate_activation.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- 追加: `test_gates_toplevel_cwd.py` の `PrePrGateToplevelCwdTests.test_tool_input_cwd_comes_before_the_toplevel_cwd`（`cwd`・`workdir`）
- `PrePushGateToplevelCwdTests.test_tool_input_cwd_still_wins_over_the_toplevel_cwd` は、subTest ごとに `pre-push-optout.log` を消す
- 関係するテスト（`scripts/light-lane-related-tests.py`）
- `tests/validate-plugin.sh`
