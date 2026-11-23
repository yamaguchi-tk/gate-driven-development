---
type: patch
---

#### Summary

`.steering/` への書き込みの検査（`validate-steering-write.py`）が、`TBD` / `TODO` / `要検討` などの語（placeholder）を検出しなくなった。自己レビューの証跡の行（`Stub grep: TODO なし` など）を止める誤 block が続いていたため。`.steering/` にプレースホルダーを書かない規定は残り、task-breakdown・brainstorming の Self-Review が見る。自己レビューの証跡のように語に触れるだけの記録とコード例は、規定の対象外にした。email・ローカル絶対パス・省略記法・AWS アカウント ID・秘密の値の検出は変わらない。

#### Affected Files

- `plugins/gate-driven-development/hooks/scripts/validate-steering-write.py`
- `plugins/gate-driven-development/hooks/scripts/lib/secret_scanning.py`
- `plugins/gate-driven-development/references/common-guardrails.md`
- `plugins/gate-driven-development/docs/SECURITY.md`
- `plugins/gate-driven-development/CONTRIBUTING.md`
- `plugins/gate-driven-development/tests/test_completed_reviewed_by_write_guard.py`
- `plugins/gate-driven-development/tests/test_distribution_readiness_contract.py`
- `plugins/gate-driven-development/tests/test_origin_session_write_once_contract.py`
- `plugins/gate-driven-development/tests/test_steering_size_deny_contract.py`
- `plugins/gate-driven-development/tests/test_steering_write_fence_scan.py`
- `plugins/gate-driven-development/tests/test_stop_hook_validate.py`
- `plugins/gate-driven-development/tests/test_validate_steering_write.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- 足したテスト: `test_todo_in_steering_write_is_allowed`、`test_todo_with_email_is_denied_by_email_only`（`tests/test_stop_hook_validate.py`）
- `python3 -m pytest` で上の Affected Files のテスト 7 本
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
