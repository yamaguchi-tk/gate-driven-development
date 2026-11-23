---
type: patch
---

#### Summary

pre-PR gate と merge gate が、行継続（`\` + 改行）の直後に書いた `gh pr create`・`gh pr merge` を検査せずに通していた経路を閉じた。

- `cd <worktree> && \` の次の行に `gh pr create …` を書く形（Claude Code が既定で書く形）は、`gh` の語の先頭に改行が付いて `gh` と一致せず、pre-PR gate が PR 作成と判定していなかった。今は PR 作成として検査し、`cd` の先を本文ファイルの基準のディレクトリにする
- `gh pr review N --approve && \` の次の行に `gh pr merge N` を書く形も、merge gate が merge と判定していなかった。今は merge として、PR 番号・`cd` の先・台帳の照合を含む通常の検査を受ける
- 行継続は、字句解析の前に空白 + 改行に置き換える。字下げ付きの行継続（`gh \` + 改行 + `  pr create`、`--head \` + 改行 + `  other` のような flag と値の間）も読む。`gh pr merge 7 \` + 改行 + `  --squash` は、これまで PR を特定できないとして止めていたが、今は PR 7 として通常の検査を受ける
- 語の途中の行継続（`gh pr merge 1\` + 改行 + `23`。行継続が続く形と、エスケープした区切り文字 `a\ ` の後ろの行継続を含む）は置き換えない。今までどおり PR を特定できない側に倒す（2 語に割ると別の PR 番号として読むため）。引用符の中の改行（`"\n&&"`）と空の値（`--body ""`・`-R ''`）は変えない
- pre-PR gate は、hook の入力（コマンドのほか cwd・説明文なども含む）に `create`・`new`・`pulls` のどれかの文字列があれば解析に進む（merge gate が `merge` の 1 語で絞るのと同じ）。これまでは `pr create` などの 2 語の並びを字面で探していたため、`gh pr  create`（空白 2 つ）・`gh pr "create"`・`gh pr` + TAB + `create`・`gh pr \` + 改行 + `create` を検査せずに通していた
- pre-PR gate の `bash -c`・`eval` の本体を、コマンド全体と同じ規則で語に分ける。これまでは `bash -c 'true&&gh pr create …'`・`eval 'true;gh pr create …'` の、演算子に密着した `gh` を見落としていた。`eval` は後ろの語を区切りまでつないで読む（`eval "gh pr" create …`）。本体の中の語の途中の `#`（`echo $#; gh pr create …`）はコメントにせず、語頭の `#` から行末まではコメントとして捨てる（merge gate と同じ規則）。語頭の判定は、`$'…'`（ANSI-C 引用）の中の `\'`、`$$`（PID）の後ろの単引用符、`$` と `'` の間の行継続を、bash と同じく読む
- merge gate も同じ語頭コメントの除去を通るので、`$'…'` の中に `\'` と `#` を含む入力は、これまで gh を見落としていたのが、shlex が引用を閉じられずに縮退し、GDD の repo では解析できないとして止まる（parse-error）

#### Affected Files

- `plugins/gate-driven-development/hooks/scripts/run-pre-pr-gate-hook.sh`
- `plugins/gate-driven-development/hooks/scripts/lib/gh_command_parse.py`
- `plugins/gate-driven-development/docs/design/2026-08-21-pr-w3-self-review-adr.md`
- `plugins/gate-driven-development/tests/test_gh_line_continuation_tokens.py`
- `plugins/gate-driven-development/tests/test_merge_gate_hook_quoted_operator.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- `tests/test_gh_line_continuation_tokens.py` を足した（行継続の後ろの PR 作成・merge、字下げ付きの行継続、語の途中の行継続、`cd` の先の本文ファイル、`bash -c`・`eval` の本体〔演算子の密着・語中の `#`〕、空の値と改行だけの値の位置、前段の照合を通る空白・引用符の形、引用符の中の改行と演算子、エスケープした空白の後ろの行継続、`$'…'` の中の引用符、末尾の行継続、改行・行継続だけの入力、埋め込みの複製と lib の一致）
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
