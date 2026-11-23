---
type: patch
---

#### Summary

利用者から見える変更なし。テスト用の共有 fixture `tests/_git_fixture.init_repo()` の集約を進める。`f.txt` を commit する形で書き写していた git repo 初期化 4 箇所を `init_repo()` に委譲した。commit の日時を指定する 2 箇所のために、`init_repo()` に省略可能な引数 `commit_date`（author date と committer date を揃えて設定する）を足した。

#### Affected Files

- `plugins/gate-driven-development/tests/_git_fixture.py`
- `plugins/gate-driven-development/tests/test_git_fixture_contract.py`
- `plugins/gate-driven-development/tests/_merge_gate_support.py`
- `plugins/gate-driven-development/tests/test_merge_gate_followup_findings.py`
- `plugins/gate-driven-development/tests/test_merge_gate_hook_block_reason_quality.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- `commit_date` の契約テストを先に書き、失敗を確認してから実装した
- `commit_date` を無視する変異で、日時に依存する merge gate のテストが落ちることを確認した
- 変更したファイルと、それを参照するテストを実行した
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
