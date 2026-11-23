---
type: patch
---

#### Summary

複数行のコミットメッセージと push を 1 コマンドにした形（`git commit -m "件名\n\nCo-Authored-By: …" && git push origin HEAD 2>&1|tail -1`）で、push 先を正しく読むようにした。これまでは引用符が閉じない行を空白だけで割っていたので、`2>&1|tail` が 1 つの語のまま残り、push 先が 2 つあると読まれていた。そのため、review-followup の nudge は PR がある branch への push でも何も出さず、pre-push gate は `refspec-ambiguous` で止めていた。引用符が閉じない行でも、区切り記号（`;` `|` `&` `<` `>` `(` `)` の連）を別の語として割るようにした。行の分け方（改行での分割）は変えていない。

同じ解析を使うほかの判定も、引用符が閉じない行では、語に密着した区切り記号の後ろを別のコマンドとして読むようになった。

- root branch guard: `…";git switch -c <branch>` の branch の作成を止めるようになった。`…; git checkout -q main; git status -sb` は、`git status -sb` の `-sb` を `git checkout` の `-b` と読んで止めることがなくなった。
- pre-push gate: `W=<path>; cd $W && …` や `cd <path>; …` の cd を読み、push の対象の repo をその cd 先で決めるようになった（これまでは `;` が語に密着して、cd を見落とすか `;` の付いた存在しない path を cd 先と読み、hook の cwd で決めていた）。語に密着した `…"&&git push` の push も検出するようになった。

fallback の行では引用符を見ないので、引用符の中の区切り記号でも割る。そのため、文字列の中に語と密着して書かれた `(cd <dir>` や `(GDD_SKIP_PRE_PUSH_GATE=1 git push` を cd・opt-out として読み、`"../wt(1)"` のような引用符つきの引数の途中でコマンドを区切ることがある。この形は、9/17 以降の transcript の git を含むコマンド 27,517 件で 0 件だった。

#### Affected Files

- `plugins/gate-driven-development/hooks/scripts/lib/git_command_parse.py`
- `plugins/gate-driven-development/tests/test_lex_fallback_operator_split.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- `tests/test_lex_fallback_operator_split.py` を足した（複数行のコミットメッセージと push を 1 コマンドにした形で、push 先を解決すること、nudge の hook の入口から nudge が出ること、pre-push gate の入口から refspec-ambiguous ではなく証跡の検査で止めること、root branch guard の入口から branch の作成を止め、次のコマンドの `-sb` では止めないこと、push 先が 2 つの形は判定不能のままにすること、heredoc の本文とコメントのアポストロフィで後ろの push を見逃さないこと、fallback の token 列が区切り記号の連を 1 token に保つこと）
- `bash tests/validate-plugin.sh`
