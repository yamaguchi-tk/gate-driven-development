---
type: patch
---

#### Summary

利用者から見える変更なし。テスト用の共有 fixture `tests/_git_fixture.init_repo()` の集約を進める。同型の git repo 初期化 2 箇所を `init_repo()` に畳み、`init_repo()` の契約テストのうち初期ブランチ名の既定を見るものを、ホストの設定によらず退行を検出できる形にした。

#### Affected Files

- `plugins/gate-driven-development/tests/_git_fixture.py`
- `plugins/gate-driven-development/tests/test_git_fixture_contract.py`
- `plugins/gate-driven-development/tests/test_pre_push_gate_contract.py`
- `plugins/gate-driven-development/tests/test_state_field_value_less_line_contract.py`
- `plugins/gate-driven-development/tests/test_root_branch_guard_contract.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- `tests/test_git_fixture_contract.py` の `test_without_branch_the_host_default_is_kept` を、`GIT_CONFIG_GLOBAL` で `init.defaultBranch` を差し替えて見る形にした。`init_repo()` に `-b <ホスト既定と同じ名前>` を常に付けるミュータントで、新しいテストが落ち、旧いテストが通ることを確認した
- `python3 -m pytest plugins/gate-driven-development/tests/ --collect-only -q` の収集一覧が origin/main と一致することを確認した
- 変更したテストと、変更した helper を参照するテストを実行した
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
