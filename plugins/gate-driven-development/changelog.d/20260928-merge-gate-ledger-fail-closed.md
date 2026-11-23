---
type: patch
---

#### Summary

merge gate と pre-PR gate が、止めるべき操作を通していた経路を閉じた。

- PR 番号の先頭の 0（`gh pr merge 007`）: gh は 旧#7 として扱うが、merge gate は文字列で比べていたので、GDD worktree の steering の PR とも、GDD の PR 台帳とも一致せずに通っていた。コマンドの番号と state.md の `PR URL` の番号の両方で先頭の 0 を落としてから比べる。長すぎる `PR URL` は比べずに止める側に倒す（比べる展開が長さに二乗で効き、hook の timeout で通ってしまうため）
- 台帳（`~/.claude/.gdd-hook-state/gdd-pr-roots`）が通常ファイルでない（ディレクトリ・FIFO・壊れた symlink）か、親のディレクトリが辿れないとき: merge gate は読めないのに「台帳に無い」として通していた。読めないものとして扱う。FIFO では merge gate も pre-PR gate（台帳に書く側）も待ち続けて timeout し、検査を飛ばしていた。どちらも開かずに返す。merge gate の抑止ログ（`merge-gate-suppressed.log`）が FIFO のときも同じく待っていたので、通常ファイルでなければ書かない
- 読めない steering: merge gate の台帳の走査は、最初の読めない state.md で照合を打ち切って後ろの一致を見ず、root・`.steering`・task dir が辿れないときは「無い」として通していた。全部を走査し、一致 > 読めない > 一致なし の順で決める。GDD worktree の中でも、読めない state.md・辿れない task dir（一覧できないものを含む）があれば、対象 PR の steering を見つけられないとき（steering が 1 件も解決できないときを含む）に `state-unreadable` で止める。以前は読める steering の件数によって素通りしていた
- 台帳の照合は、ドットで始まる task dir の state.md も見る（worktree の中の探し直しと同じ範囲）

経路ごとの倒し方は変えていない。root が解決できない実行先では、読めないときは止める。marker の無い git repo から実行したときは、台帳に一致したときだけ止める。

#### Affected Files

- `plugins/gate-driven-development/hooks/scripts/run-merge-gate-hook.sh`
- `plugins/gate-driven-development/hooks/scripts/lib/gdd-pr-roots.sh`
- `plugins/gate-driven-development/tests/test_merge_gate_ledger_fail_closed.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- `tests/test_merge_gate_ledger_fail_closed.py` を足した（先頭 0 と長い番号・URL を本体と台帳の両経路で、台帳のパスの種類、走査の順序と辿れないもの、worktree の中の読めない steering、pre-PR gate の FIFO の台帳、FIFO の抑止ログ）
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
