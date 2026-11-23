---
type: patch
---

#### Summary

root branch guard（`validate-worktree-command.py`）が、作業ディレクトリを解けないときに、ブランチか GDD 名の worktree を作るコマンドを止めるようにした。作業ディレクトリは `tool_input` の `cwd`・`workdir`、それが無いときは hook 自身の cwd（この guard は payload の最上位の `cwd` を読まず、Claude Code の Bash は `tool_input` に cwd を載せないので、Claude Code ではこちらになる）。これまでは解く処理が判定の try の外にあり、`~-`・NUL・lone surrogate を含む値や、消えたディレクトリで例外になって、hook が exit 1（PreToolUse では止めない）で終わっていた。作業ディレクトリを使わずに決められる「作る」コマンド（root branch の作成、GDD 名の worktree add）だけを止め、`git worktree prune` などの後始末は通す。文面には、作業ディレクトリを解けなかったことと戻し方を出す。payload が JSON として読めないとき（UTF-8 でない byte で壊れたときを含む）、JSON の object でないときは、今までどおり通す（コマンドを取り出せない）。

#### Affected Files

- `plugins/gate-driven-development/hooks/scripts/validate-worktree-command.py`
- `plugins/gate-driven-development/tests/test_root_branch_guard_payload_cwd.py`
- `plugins/gate-driven-development/tests/test_root_branch_guard_exec_target.py`
- `plugins/gate-driven-development/tests/_root_branch_guard_support.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- `tests/test_root_branch_guard_payload_cwd.py` を足した
- `bash tests/validate-plugin.sh`
