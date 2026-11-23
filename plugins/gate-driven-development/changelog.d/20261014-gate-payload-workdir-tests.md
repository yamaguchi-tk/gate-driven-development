---
type: patch
---

#### Summary

- 利用者から見える変更なし。pre-push gate・pre-PR gate・root-branch guard が payload の `tool_input.workdir`（Codex が渡す実行先）を `tool_input.cwd` と同じく読むことを、テストで固定した

#### Affected Files

- `plugins/gate-driven-development/tests/_pre_push_gate_support.py`
- `plugins/gate-driven-development/tests/test_pre_push_root_resolution.py`
- `plugins/gate-driven-development/tests/test_pre_pr_gate_contract.py`
- `plugins/gate-driven-development/tests/test_root_branch_guard_payload_cwd.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- 各 gate の既存の payload の cwd のテストを、`cwd`・`workdir` の両方の key で回す
- 関係するテスト（`scripts/light-lane-related-tests.py`）
- `tests/validate-plugin.sh`
