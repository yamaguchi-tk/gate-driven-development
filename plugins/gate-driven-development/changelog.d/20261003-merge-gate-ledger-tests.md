---
type: patch
---

#### Summary

merge gate（`run-merge-gate-hook.sh`）の挙動は変えていない。同じ repo の別 worktree・root checkout へ共通ディレクトリで通した merge で、GDD の PR 台帳の照合が hit のほか、unknown（対象 PR を特定できない）・unreadable（台帳や台帳に載った root を読めない）でも止めることをテストで確かめた。台帳の読み手を列挙する注記を、この経路を含む 3 経路に直した。

#### Affected Files

- `plugins/gate-driven-development/hooks/scripts/run-merge-gate-hook.sh`（注記だけ）
- `plugins/gate-driven-development/hooks/scripts/lib/gdd-pr-roots.sh`（注記だけ）
- `plugins/gate-driven-development/tests/test_merge_gate_same_repo_worktree.py`
- `plugins/gate-driven-development/tests/test_merge_gate_hook_non_gdd_merge.py`
- `plugins/gate-driven-development/tests/_merge_gate_support.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- `tests/test_merge_gate_same_repo_worktree.py` にテストを足した
- `bash tests/validate-plugin.sh`
