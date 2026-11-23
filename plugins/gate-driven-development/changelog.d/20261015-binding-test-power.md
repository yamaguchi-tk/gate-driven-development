---
type: patch
---

#### Summary

利用者から見える変更なし。task の binding の resolver のテスト 2 本が、実装の分岐を外しても通る状態だったので直した。`resolve_bind` の広い except を固定するテストは resolver を差し替えて例外を投げさせ、Python 3.12 以前の `Path.exists` の権限エラーを固定するテストは `Path.exists` を差し替えて、インタプリタの版に依らず分岐を通す。

#### Affected Files

- `plugins/gate-driven-development/tests/test_task_binding_resolve_security_contract.py`
- `plugins/gate-driven-development/tests/test_task_binding_worktree_path_absolute.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- `python3 -m pytest plugins/gate-driven-development/tests/test_task_binding_resolve_security_contract.py plugins/gate-driven-development/tests/test_task_binding_worktree_path_absolute.py -q`
