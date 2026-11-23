---
type: patch
---

#### Summary

利用者から見える変更なし。テスト用の共有 fixture `tests/_git_fixture.init_repo()` の集約を進める。「`git init` → user 設定 → README.md → add → commit」と同じ形で書き写していた 3 箇所を `init_repo()` に委譲した。後続の `git worktree add` や steering の作成は呼び出し側に残す。

#### Affected Files

- `plugins/gate-driven-development/tests/_stop_hook_test_base.py`
- `plugins/gate-driven-development/tests/test_stop_hook_bounce_containment_contract.py`
- `plugins/gate-driven-development/tests/test_worktree_registry_contract.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- `python3 -m pytest plugins/gate-driven-development/tests/ --collect-only -q` の収集一覧が、merge-base と一致することを確認した
- 変更したファイルと、それを参照するテストを実行した
- `python3 -m unittest tests.<module>` の起動でも共有 fixture を解決できることを確認した
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
