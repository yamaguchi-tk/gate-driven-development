---
type: patch
---

#### Summary

- 利用者から見える変更なし。merge gate が payload の `tool_input.workdir`（Codex が渡す実行先）を `tool_input.cwd` と同じく gh の実行先として読み、その repo の binding で判定することを、テストで固定した

#### Affected Files

- `plugins/gate-driven-development/tests/test_merge_gate_binding_steering.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- `tests/test_merge_gate_binding_steering.py` の `test_payload_cwd_picks_the_repo_to_look_up` を、`cwd`・`workdir` の両方の key で回す
- 関係するテスト（`scripts/light-lane-related-tests.py`）
- `tests/validate-plugin.sh`
