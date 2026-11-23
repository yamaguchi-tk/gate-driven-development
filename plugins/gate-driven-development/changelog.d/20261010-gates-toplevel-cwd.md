---
type: patch
---

#### Summary

pre-push gate・pre-PR gate・merge gate と、push 後の review-followup nudge が、Claude Code の PreToolUse payload の最上位の `cwd` で判定するようにした。これまでは tool_input の `cwd`・`workdir` と hook のプロセスの cwd だけを読んでいた。desktop の worktree のセッションでは hook のプロセスの cwd が root checkout になるので、worktree からの push・PR 作成・マージを、root の state で判定するか（root に別タスクの active な state があるとき）、worktree の GDD を検査せずに通していた。2026-10 のログでは、pre-push gate の session-mismatch（別セッションの active な state を見て検査せずに通した記録）148 行のうち 147 行が root checkout の記録で、nudge は 335 行のうち 208 行が root checkout を見て「PR なし」で通していた。

最上位の `cwd` が使えるときは、4 つの hook がそれを判定の基準にする。nudge・pre-PR gate・merge gate はプロセスの cwd をそこへ移し、pre-push gate は相対の root を絶対パスにする基準をそれにする。pre-push gate・nudge・pre-PR gate では、相対パス（`git --git-dir=../x/.git`、相対の `cd` 先、`--body-file` の相対パス）も、セッションの cwd から解くようになる。tool_input の `cwd`・`workdir` は、pre-push gate・nudge・pre-PR gate では今までどおりこれより優先する。merge gate では、最上位の `cwd` が trusted の候補（今までの hook のプロセスの cwd の位置）に入る。値を書くのは harness で、モデルが書く tool_input ではない。最上位の `cwd` は前の Bash 呼び出しの `cd` に追従するが、CLI では hook のプロセスの cwd も同じ値で一緒に動く（2026-10-11、headless の claude で実測）ので、CLI の trusted の候補は変更前と同じ値になる。

merge gate は、trusted root の steering が対象 PR を記録していない出口（steering が無い、別の PR を記録している、done が 2 件以上）でも、GDD の PR 台帳（`gdd-pr-roots`）を照合し、対象 PR を別の root が記録していれば（hit）止めるようにした。miss・照合できない（unknown）・台帳を読めない（unreadable）ときは今までどおり通す。最上位の `cwd` を trusted にしたことで、desktop の worktree のセッションから別の worktree の PR を cd なしで merge すると、root checkout での台帳の照合を通らずに通る形ができたため。この変更で、desktop の worktree のセッションでも、CLI のセッション（marker のある worktree で起動したもの）でも、別の GDD の worktree の PR を cd なしで merge すると新しく止まる。止まったら `cd <その PR の worktree> && gh pr merge <番号>` の形で打ち直す。

使える最上位の `cwd` は、空でない絶対パスの文字列で、存在して中に入れる（実行権のある）ディレクトリで、タブ・改行・CR を含まないものである。判定は新しい `hooks/scripts/lib/hook_cwd.py` にまとめ、root branch guard（`validate-worktree-command.py`）の判定も同じ条件にした。未リリースの断片 `20261009-guard-payload-cwd.md` の「存在するディレクトリのときだけ使い」には、この 2 つの条件（中に入れること、タブ・改行・CR を含まないこと）が加わる。使えないときは、今までどおりプロセスの cwd で判定する。

#### Affected Files

- `plugins/gate-driven-development/hooks/scripts/lib/hook_cwd.py`
- `plugins/gate-driven-development/hooks/scripts/run-pre-push-gate-hook.sh`
- `plugins/gate-driven-development/hooks/scripts/run-pre-pr-gate-hook.sh`
- `plugins/gate-driven-development/hooks/scripts/run-merge-gate-hook.sh`
- `plugins/gate-driven-development/hooks/scripts/run-review-followup-nudge-hook.sh`
- `plugins/gate-driven-development/hooks/scripts/validate-worktree-command.py`
- `plugins/gate-driven-development/hooks/scripts/lib/gdd-pr-roots.sh`
- `plugins/gate-driven-development/tests/test_gates_toplevel_cwd.py`
- `plugins/gate-driven-development/tests/test_merge_gate_toplevel_ledger.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- `python3 scripts/light-lane-related-tests.py --run . origin/main`
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
