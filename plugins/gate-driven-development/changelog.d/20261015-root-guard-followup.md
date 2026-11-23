---
type: patch
---

#### Summary

root-branch guard（`validate-worktree-command.py`）の deny の文に、root の `active: true` の session state で止めた場合の理由（state の持ち主を照合できない・この session の state・読めない state）と確かめ方、抜け方（持ち主がもう動いていないことをユーザーに確かめてから `active: false` にする。読めない state は、通常のファイルに戻すか権限を直す）を足した。state を判定する関数の名前を `active_gdd_state_exists` から `root_state_blocks` に改めた。`lib/regular_file.py` の import に失敗して止めるときは、回復手順がそのファイルも名指しする。止める・通すの判定は変えない。

#### Affected Files

- `plugins/gate-driven-development/hooks/scripts/validate-worktree-command.py`（deny の文）
- `plugins/gate-driven-development/docs/SECURITY.md`（Bash の PreToolUse の行に session の照合を足す）
- `plugins/gate-driven-development/changelog.d/20261014-root-branch-guard-session.md`（止める条件と抜け方の書き足し）
- `plugins/gate-driven-development/tests/test_root_branch_guard_session_owner.py`・`tests/test_root_branch_guard_fail_closed.py`・`tests/test_root_branch_guard_contract.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- `tests/test_root_branch_guard_session_owner.py`（state で止めたときの文、`setup-gdd-loop.sh` が書いた state で持ち主だけを止めること）
- `tests/test_root_branch_guard_fail_closed.py`（`lib/regular_file.py` が欠けても止め、回復手順がそのファイルを名指しすること）
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
