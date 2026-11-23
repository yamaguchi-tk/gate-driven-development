---
type: patch
---

#### Summary

root branch 作成禁止の guard（`validate-worktree-command.py`）が、Claude Code の PreToolUse payload の最上位の `cwd` で判定するようにした。Claude Code の Bash は tool_input に cwd を持たないので、これまでは hook のプロセスの cwd で判定していた。desktop の worktree のセッションでは、hook のプロセスの cwd が root checkout になる（2026-10-09 実測。0.41.11 の「最上位の `cwd` は hook のプロセスの cwd と同じ値」は CLI での実測）。そのため、worktree の中のブランチ作成を、root に残った `active: true` の state で止めていた。

読む順は、tool_input の `cwd`・`workdir`、payload の最上位の `cwd`、hook のプロセスの cwd である。最上位の `cwd` は、空でない絶対パスの文字列で、存在するディレクトリのときだけ使い、それ以外は今までどおりプロセスの cwd で判定する。cwd を解けないときの deny の文面も、この順に合わせた。`git -C`・先行する `cd` の実行先にも、cwd と同じく GDD 名のブランチ（`gdd/…`）の作成を止める条件を当てるようにした（今までは実行先には active な state の判定だけを当てていた）。未リリースの断片 `20261003-root-branch-guard-cwd-in-try.md` の「この guard は payload の最上位の `cwd` を読まず」は、この変更で当たらなくなる。

#### Affected Files

- `plugins/gate-driven-development/hooks/scripts/validate-worktree-command.py`
- `plugins/gate-driven-development/tests/test_root_branch_guard_toplevel_cwd.py`
- `plugins/gate-driven-development/tests/_root_branch_guard_support.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- `python3 scripts/light-lane-related-tests.py --run . origin/main`（`validate-worktree-command` を参照するテストを含む）
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
