---
lane: L1+
pr: 395
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ-1 | Opus 設計レビュー (gdd-opus-advisor, model: opus) + user（実測: 9/17 以降の transcript で、引用符の中の改行が原因で push 先が ambiguous になった push は 236 件・83 セッション。main の草案は `_lex` の行分割を引用符を考えて行う案だった。Opus は、heredoc の本文とコメントのアポストロフィで行を結合して push を飲み込む fail-open を挙げ、`_lex_segment` の fallback だけを区切り記号の連で割る正規表現に置き換える案を推奨した。main はこれを採った。git を含む Bash コマンド 27,517 件の新旧比較で、ambiguous→解決 246 件、push の非検出→検出 21 件、検出→非検出 0 件、opt-out の受理の変化 0 件、root branch guard の判定の変化 1 件（`main;` を branch 名と読む誤判定が直るもの）。ユーザーが承認した。食い違いは残らないので max・Fable には相談していない） | - | 0 | 0 | 0 | 2026-10-06T23:31+09:00 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 2467ae583e05fb2e6a1b8e732013a76dcaa4dcf8 | 4 | 1 | 4 | 2026-10-07T08:27+09:00 |
| 方針メモ-2 | Opus 設計レビュー (gdd-opus-advisor, model: opus)（独立-1 の 閉じ方: 列挙 の high 4 件。入力者の実測: git を含む Bash コマンド 27,517 件で、文字列の中の cd・opt-out を新たに読む件 0、push の検出の消失 0、heredoc 本文の cd・opt-out の後ろに push がある件 0、pre-PR gate で密着した `;gh` 0。root が変わった 93 件はすべて本物の cd。main の案は 4 件とも (b)。Opus も 4 件とも (b) を推奨し、refspec の解決だけに新しい token 列を使う狭い変更には、push の非検出→検出 21 件を失うので反対した。食い違いは残らないので max・Fable には相談していない） | - | 0 | 0 | 0 | 2026-10-07T08:33+09:00 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | dcead0db3ee213cfe593f573110f80d60597e149 | 2 | 0 | 2 | 2026-10-07T08:55+09:00 |
| 方針メモ-3 | Opus 設計レビュー (gdd-opus-advisor, model: opus) + user（安全策 4 の発火: fail-open のクラスタの high を含む巡が独立-1・独立-2 の 2 回。独立-2 の high 2 件は独立-1 の R1-1・R1-2 と同じ形で、この PR の変更行に入る。入力者の実測: git を含む Bash コマンド 27,517 件で、この形は 0 件。main の案は「止める」、Opus も「止める」を推奨し、断片の changelog.d は巡を無効にしないと補った。ユーザーは「止める」を選んだ。食い違いは残らないので max・Fable には相談していない） | - | 0 | 0 | 0 | 2026-10-07T09:00+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| M1 | 方針メモ-1 | - | - | - | - | - | なし |
| R1-1 | 独立-1 | high | yes | self-inflicted | fail-open | accepted | 列挙: 引用符が閉じない行で、文字列の中に語と密着した `(cd <dir>`・`(GDD_SKIP_PRE_PUSH_GATE=1 git push` を pre-push gate が cd 先・opt-out として読み、active な repo の外の実在する cd 先なら後ろの本物の push を検査せずに通す（方針メモ-2 で (b)。実データ 0 件） |
| R1-2 | 独立-1 | high | yes | self-inflicted | fail-open | accepted | 列挙: 引用符が閉じない行で、引用符の中の区切り記号（`"../wt(1)"`・`"user.name=ci(bot)"`）が segment を切り、root branch guard の worktree・switch の作成と pre-push gate の push の検出を見落とす（方針メモ-2 で (b)。実データの検出の消失 0 件） |
| R1-3 | 独立-1 | high | yes | inherited | fail-open | accepted | 列挙: heredoc の本文と、複数行の文字列の中間の行（shlex が通る行）の cd・opt-out を pre-push gate が読む（既存。方針メモ-2 で (b)。実データ 0 件） |
| R1-4 | 独立-1 | high | yes | inherited | fail-open | accepted | 列挙: pre-PR gate の `lex()` の fallback が `text.split()` のままで、密着した `;gh pr create` を見落とす（既存。方針メモ-2 で (b)。実データ 0 件） |
| R1-5 | 独立-1 | medium | no | self-inflicted | doc-claim | fixed | PR 本文の抜粋の限界と断片が、block gate で許可側に倒れる向きと、pre-push gate の root の決め方の変化を書いていない（断片を直した。PR 本文は push のときに書く） commit: 3bd2355c |
| R1-6 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 断片とテストの名前・docstring の root branch guard の記述が、変更前の挙動（noclobber の redirect の後ろの `-c` は変更前も止めていた・`-sb` を `-b` と読んでいた）と合わない commit: 3bd2355c |
| R1-7 | 独立-1 | low | no | self-inflicted | test-power | fixed | fallback が例外を出さないことのテストが token 数の下限だけを見ていて、変更前の実装でも通る commit: 3bd2355c |
| R1-8 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 未リリースの断片 `changelog.d/20260915-x58-x59-review-followup-nudge.md:103` の fallback（`segment.split()`）の記述が古くなる（未リリースの断片は通常の PR で書き換えないので、リリースのときに直すものとして PR 本文に書く） |
| R1-9 | 独立-1 | low | no | self-inflicted | product | accepted | 引用符が閉じない行で、文字列の中の `(git push origin <x>` を最初の push と読み、nudge が別の branch の PR を引く（入力が開いていて列挙で閉じないので、限界として PR 本文に書く） |
| R1-10 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | `_FALLBACK_TOKEN_RE` のコメントの参照先が `_split_glued_punctuation` で、opt-out の事例がある `token_ends_with_separator` ではない commit: 3bd2355c |
| M2 | 方針メモ-2 | - | - | - | - | - | なし |
| R2-1 | 独立-2 | high | yes | self-inflicted | fail-open | accepted | 列挙: R1-1 と同じ形。引用符が閉じない行で、文字列の中に語と密着した `(GDD_SKIP_PRE_PUSH_GATE=1 git push`・`(cd <dir>` を pre-push gate が opt-out・cd 先として読み、後ろの本物の push を検査せずに通す（安全策 4 で止める。実データ 0 件） |
| R2-2 | 独立-2 | high | yes | self-inflicted | fail-open | accepted | 列挙: R1-2 と同じ形。引用符が閉じない行で、`git -C "../wt(1)" switch -c <branch>` の引用符の中の区切り記号で segment が切れ、root branch guard が branch の作成を見落とす（安全策 4 で止める。実データ 0 件） |
| R2-3 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 断片の `W=<path>; cd $W` の例が誤り。`$W` は展開されず、push の対象の repo は hook の cwd で決まる（安全策 4 で止めた後なので直さず、PR 本文の限界に書く） |
| R2-4 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 断片に実測の件数と受け入れた限界を書いていて、CHANGELOG の Policy（利用者から見える変更だけを書く）に反する（同上） |
| R2-5 | 独立-2 | low | no | inherited | doc-claim | accepted | `git_command_parse.py` の :45・:95 と `test_push_command_parse_lexing.py` の :300 に、`_lex_segment` は token 列を再分割しないという古い記述が残る（安全策 4 で止めた後なので直さず、PR 本文の限界に書く） |
| R2-6 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | PR 本文の草案の限界に、文字列の中で受理してしまう opt-out の名前が無い（PR 本文で直す） |
| R2-7 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | 断片の区切り記号の列挙で、`<` `>` は「別のコマンド」の区切りではなく redirect である |
| R2-8 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | 断片の、同じ解析を使う判定の列挙に、heredoc の本文が実行されるかの判定（`_feeds_shell_interpreter`。deny の側に倒れる変化）が入っていない |
| M3 | 方針メモ-3 | - | - | - | - | - | なし |
