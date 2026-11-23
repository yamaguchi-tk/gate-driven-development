---
type: patch
---

#### Summary

pre-push gate・root-branch guard・GDD worktree guard（`git_command_parse`）と、merge gate・pre-PR gate（`gh_command_parse`）は、shell の字句解析の芯（行継続・語頭のコメント・引用符をまたぐ改行・引用符の中の演算子の退避・fd 番号・shlex と、その失敗時の読み）を、新しい `lib/shell_lexer.py` から読むようになった。前は 2 つの lib がそれぞれ別の字句解析を持ち、互いに相手が直した形で読み違えていた。

pre-push gate は、複数行の commit メッセージ（`git commit -m "…⏎…" && git push`）の後ろの `git push` を、push として検査する。前は行ごとに字句解析をしていたので、引用符の中の文字と読んで通していた。引用符が末尾まで閉じないときは、行ごとの読みでも push を探し、どちらかで見つかれば検査する。

merge gate は、`gh pr merge 8 --squash` の後に改行して別のコマンドを書いた形を、PR 旧#8 の merge と読む。前は改行を空白として読み、対象を決められないとして止めていた。

worktree guard は、`git branch 2>&1` の `2` をブランチ名と読まなくなった。引用符が末尾まで閉じないときは、worktree guard も行ごとの読みでブランチの作成を探し、どちらかで見つかれば止める。

pre-push gate・worktree guard も、merge gate・pre-PR gate と同じく、語頭の `#` から行末をコメントとして読む（前は `#` をコメントとして扱わず、`# git push …` の行も push として検査していた）。二重引用符の中の `$(…)`・`${…}` の中では、引用符と `#` を入れ子の文脈で読む（`git commit -m "$(printf "fix #12")" && git push` の後ろの push を落とさない）。バッククォートは、bash と同じく、エスケープされていない次の `` ` `` までを区間として読み、中のコメントは閉じの手前で終わる（`` v=`… # it's …` `` の `'` で、次の行の `git push`・`gh pr merge` を隠さない）。heredoc の本文の入れ子は 32 段までを読み、それより深いときは行ごとの読みでも push を探す。

opt-out（`GDD_SKIP_PRE_PUSH_GATE=1`）と `cd` の受理、push の refspec・`--dry-run` の走査、git の global option の値の判定は、引用符の中の `;`・`&&`・`&` などを区切りとして読まない（`git push origin main '&' feature` は、前は `main` だけを push 対象と読んでいた。今は refspec が複数あるとして止める）。

merge gate・pre-PR gate も、二重引用符の中の `$(…)` の中の `#` をコメントとして読まなくなった。`echo "$(echo "a #b")" && gh pr merge 7` の後ろの `gh pr merge`（`gh pr create` も）を、新しく検査する（前は `#b` から行末をコメントとして落として通していた。bash も zsh も gh を実行する形）。

merge gate は、`$'…'` の中に `\'` を含む入力のうち、引用符が閉じないと読む形を、新しく対象を決められないとして止める（bash も zsh も gh を実行しない形）。

入れ子の shell の展開（`bash -c`・`eval`・`env -S`）、コマンド置換、区切りの集合（`(`・`)`）、heredoc の本文の落とし方は、lib ごとの実装のまま残る。

#### Affected Files

- `plugins/gate-driven-development/hooks/scripts/lib/shell_lexer.py`
- `plugins/gate-driven-development/hooks/scripts/lib/gh_command_parse.py`
- `plugins/gate-driven-development/hooks/scripts/lib/git_command_parse.py`
- `plugins/gate-driven-development/hooks/scripts/lib/push_command_parse.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- `python3 scripts/light-lane-related-tests.py --run . origin/main`
- 追加: `tests/test_shell_lexer.py`（字句解析の芯）、`tests/test_shell_lexer_gates.py`（pre-push・worktree guard・merge・pre-PR の各 gate を hook の入口から通す）
- 期待値を変えた: 語の途中の行継続、merge の後の改行、`{MERGE}⏎cd`（merge の後の cd）、語頭の `#` の token の形、引用符の中の改行の後の `git push`（bash と zsh の読みに合わせた）
- 追加: `tests/test_push_command_parse.py` の CORPUS（複数行の commit メッセージ、二重引用符の中の置換と `#`、引用した heredoc の行末の `\`、コメントの後の行、`2>&1`）
