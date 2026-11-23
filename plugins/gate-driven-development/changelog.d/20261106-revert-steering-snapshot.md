---
type: patch
---

#### Summary

- 利用者から見える変更なし。同じ版の `20261106-steering-snapshot-at-gate-dispatch.md` で足した、`gdd-formal-gate-runner` の起動時に steering を保存する PreToolUse hook（設定のキー `GDD Steering Snapshot:`）を取り下げた。gate の判定の多くは runner が起動する reviewer が決めるので、runner を別の model で当て直しても差を見分けられず、保存した steering に使い道が無かった

#### Affected Files

- `hooks/hooks.json`
- `hooks/scripts/run-steering-snapshot-hook.sh`（削除）
- `hooks/scripts/lib/steering_snapshot.py`（削除）
- `references/operation-levels.md`
- `tests/test_steering_snapshot_hook.py`（削除）
- `tests/test_hooks_kill_switch.py`
- `tests/test_pre_push_gate_contract.py`

#### User Action Required

- `~/.gdd/config.local.md` に `GDD Steering Snapshot: on` の行を足していたら、消してよい（残しても何も起きない）

#### Validation / Eval Impact

- `scripts/light-lane-related-tests.py --run`、`tests/validate-plugin.sh`
