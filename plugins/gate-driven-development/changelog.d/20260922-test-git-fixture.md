---
type: patch
---

#### Summary

利用者から見える変更なし。テストが書き写していた「`git init` → user 設定 → README.md の 1 commit」を、共有 fixture `tests/_git_fixture.py` の `init_repo()` に集約した。各テストの `_init_repo` は名前を残したまま、この関数へ委譲する。assert・入力・既存テストの本数は変えていない。

#### Affected Files

- `plugins/gate-driven-development/tests/_git_fixture.py`（新規）
- `plugins/gate-driven-development/tests/test_git_fixture_contract.py`（新規）
- `plugins/gate-driven-development/tests/_root_branch_guard_support.py`
- `plugins/gate-driven-development/tests/test_active_gdd_skill_gate_contract.py`
- `plugins/gate-driven-development/tests/test_agent_dispatch_model_gate_contract.py`
- `plugins/gate-driven-development/tests/test_block_enter_worktree_hook.py`
- `plugins/gate-driven-development/tests/test_pre_pr_gate_contract.py`
- `plugins/gate-driven-development/tests/test_review_followup_nudge_hook.py`
- `plugins/gate-driven-development/tests/test_steering_detection_contract.py`
- `plugins/gate-driven-development/tests/test_task_binding_resolve_security_contract.py`
- `plugins/gate-driven-development/tests/test_task_binding_resolver.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- 新規 contract test: `tests/test_git_fixture_contract.py`（`init_repo()` が commit 1 つと user 設定を持つ repo を作る。`branch` を渡したときだけ初期ブランチ名が決まり、渡さないときはホストの既定に従う）
- `python3 -m pytest plugins/gate-driven-development/tests/ --collect-only -q` の収集一覧が、origin/main と新規テストの分だけ差があることを確認した
- 変更したテストと、変更した helper を import するテストを実行した
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
