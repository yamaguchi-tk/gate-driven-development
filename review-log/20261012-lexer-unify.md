---
lane: L1+
pr: 473
follow_up_of: 433
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ | Opus 設計レビュー (gdd-opus-advisor, model: opus) + user | 5fb051fe | 0 | 0 | 0 | 2026-10-13 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 42ce65e7 | 5 | 3 | 5 | 2026-10-13 |
| 方針メモ-1 | Opus 設計レビュー (gdd-opus-advisor, model: opus) + Fable (gdd-fable-advisor) + user | 42ce65e7 | 0 | 0 | 0 | 2026-10-13 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | d7fe65ac | 3 | 2 | 3 | 2026-10-13 |
| 方針メモ-2 | Opus 設計レビュー (gdd-opus-advisor, model: opus) + user | d7fe65ac | 0 | 0 | 0 | 2026-10-13 |
| 独立-3 | light-lane-independent-reviewer-xhigh, 差分, model: opus | c41a96b1 | 7 | 0 | 7 | 2026-10-13 |
| 方針メモ-3 | Opus 設計レビュー (gdd-opus-advisor, model: opus) + user | c41a96b1 | 0 | 0 | 0 | 2026-10-13 |
| 独立-4 | light-lane-independent-reviewer-xhigh, 差分（無効化後）, model: opus | f4b8524b | 2 | 2 | 2 | 2026-10-13 |
| 方針メモ-4 | Opus 設計レビュー (gdd-opus-advisor, model: opus) | f4b8524b | 0 | 0 | 0 | 2026-10-13 |
| 方針メモ-5 | Fable (gdd-fable-advisor) + user | f4b8524b | 0 | 0 | 0 | 2026-10-13 |
| 独立-5 | light-lane-independent-reviewer-xhigh, 差分（無効化後）, model: opus | 79ffdeed | 4 | 0 | 4 | 2026-10-14 |
| 独立-6 | light-lane-independent-reviewer, 全差分（無効化後）, model: opus | d9604ea7 | 3 | 0 | 3 | 2026-10-14 |
| 方針メモ-6 | Opus 設計レビュー (gdd-opus-advisor, model: opus) + user | dfa46752 | 0 | 0 | 0 | 2026-10-14 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| M1 | 方針メモ | - | - | - | - | - | なし |
| F1 | 独立-1 | high | yes | self-inflicted | comment-quote | fixed | git 側も語頭コメントを落とすようになり、二重引用符の中の `$(printf "fix #12")` の後ろの `&& git push` ごと消える（旧の行ごとの読みは検出）。閉じ方: 構造。transcript で同じ形の 5 件は新しい読みでも検出できていた normalize の引用符の追跡を文脈のスタックにし、行ごとの読みはコメントを落とさない形に戻した。commit: 17673b0e |
| F2 | 独立-1 | high | yes | inherited | comment-quote | fixed | 列挙: 同じ読み違いで merge gate・pre-PR gate が `echo "$(echo "a #b")" && gh pr merge 999` を見落とす。transcript で gh 側の該当 0 件。方針メモ-1 で、F1 の根の修正（normalize の引用符の追跡に文脈のスタック）で同じ入力を閉じる（規定の (a)〜(c) の外）。merge gate のテストで固定できなければ (b) に戻す F1 と同じ根の修正で閉じ、merge gate・pre-PR gate を hook の入口から通すテストで固定した。commit: 17673b0e |
| F3 | 独立-1 | high | yes | self-inflicted | exception-path | fixed | heredoc 本文の再帰が深い入れ子で RecursionError になり、pre-push hook の except で通る。閉じ方: 構造 本文の再帰に 32 段の上限を置き、芯の例外は行ごとの読みに倒す。終端の行の索引で 2 乗の走査も減らした。commit: a4b54ac3 |
| F4 | 独立-1 | high | yes | self-inflicted | request-drift | fixed | PR 本文が合否「push の見落とし 44→0」を「45→3」に替えていた。実測で残る 3 件は 44 件に入っておらず（0 件）、44→0 は満たしていた。PR 本文の書き方を直し、別の型の 3 件（変数・python 経由の実行。統合の前から）は限界に書く PR 本文で、44→0 を満たしたことと、別の型の 3 件を限界に書いた。commit: なし（PR 本文） |
| F5 | 独立-1 | high | yes | inherited | quoted-separator | fixed | opt-out・cd の受理面（find_optout・_find_cd_root）が引用符の中の `;` を区切りと読む。閉じ方: 構造 受理面（find_optout・_find_cd_root）とコマンド先頭の判定で、引用した区切りを区切りと読まない。commit: 22993af7 |
| F6 | 独立-1 | medium | yes | self-inflicted | product | fixed | 先頭のコメント行・空行の後ろに `;` が付き、merge gate の cd_target が None になって新しく止める 最初の token より前に区切りを置かない。commit: 2dc90dbc |
| F7 | 独立-1 | medium | no | self-inflicted | request-drift | accepted | (a) merge gate が新しく 1 件止める（`$'…'` の中の `\'`、両 shell とも gh を実行しない）(b) `$'…'` の中の行継続を bash の読みに合わせた（該当 0 件）。方針メモ-1 でユーザーが限界として受け入れた。限界の節に書く |
| F8 | 独立-1 | medium | no | self-inflicted | test-power | fixed | 検出面を変えたのに CORPUS（test_push_command_parse.py）に足していない CORPUS に 7 形を足した。commit: 8274f52c |
| F9 | 独立-1 | low | no | self-inflicted | test-power | fixed | 縮退の和のテストが git_command_parse.py:238-241 を固定しない 縮退の和を固定する入力を足した。commit: 8274f52c |
| F10 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | docstring・ADR・テストの説明が今の実装と違う docstring・テストの説明・ADR の Addendum を直した。commit: 9121044e |
| F11 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | PR 本文の wrapper の記述が不正確で、コメントの扱いの変化が無い PR 本文を直した。commit: なし（PR 本文） |
| F12 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 断片に期待値の変更 2 件とコメントの扱い・新しく止める形が無い 断片を直した。commit: 9b1e47dd |
| A1 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | PR 本文の数の出どころ。PR 本文に書く |
| A2 | 独立-1 | advisory | no | self-inflicted | product | accepted | `$$'` で normalize と split_unquoted_newlines の読みが割れる（止める側）。PR 本文に書く |
| R1 | 方針メモ-1 | - | - | - | - | - | なし |
| G1 | 独立-2 | high | yes | self-inflicted | quoted-separator | fixed | 引用符の中が改行だけの語は QuotedWord にならず、opt-out・cd の受理面が区切りと読む（`echo '⏎' cd /tmp && git push origin main`）。閉じ方: 構造。transcript 0 件。安全策 4 の発火で HITL へ commit: 77608f16 |
| G2 | 独立-2 | high | yes | self-inflicted | comment-quote | fixed | 列挙: バッククォートの中の `$(` の中の `#` をコメントとして落とし、閉じの backquote と後ろの `; git push`・`gh pr merge` も消える。この PR の退行。修正後の実データの照合で新しい見落とし 0 件。安全策 4 の発火で HITL へ commit: 0cfe1d6a |
| G3 | 独立-2 | high | yes | self-inflicted | quoted-separator | fixed | classify_refspec などが引用した `&` を区切りと読み、`git push origin main '&' feature` の feature を見落とす（`&` の ref を作らないと出ない）。閉じ方: 構造。transcript 0 件。安全策 4 の発火で HITL へ commit: 602286ed |
| G4 | 独立-2 | medium | no | self-inflicted | doc-claim | fixed | 断片・PR 本文に merge gate・pre-PR gate の挙動の変化 2 つ（先頭の区切り、二重引用符の中の置換の後ろの merge を新しく止める）が無い (i) は main と tip で判定が同じだった。(ii) と refspec の変化を断片と PR 本文に書いた。commit: 7808a9c3 |
| G5 | 独立-2 | medium | no | self-inflicted | request-drift | fixed | pre-PR gate の 1 件の変化が、正しい block か誤 block か書いていない（条件 5） 両 shell が gh pr create を実行し、本文も同じだった（正しい block）。commit: なし（PR 本文） |
| G6 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | QuotedWord・push_command_parse の docstring が区切りの扱いを古いまま書く。follow_up_of のある PR の 2 巡目の low なので限界の節に書く |
| G7 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | ADR の `$(…)` の中の `#`・単引用符の中の行継続の記述が実装と違う。限界の節に書く |
| G8 | 独立-2 | low | no | self-inflicted | test-power | accepted | 二重引用符の中のバッククォートの形が CORPUS と hook の入口のテストに無い。限界の節に書く |
| G9 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | PR 本文の数を測った sha とコマンドが無い。PR 本文に書く |
| G10 | 独立-2 | low | no | self-inflicted | request-drift | fixed | worktree guard に条件 2（縮退で行ごとの読み）を入れず、確かめずに限界にした worktree guard にも縮退で行ごとの読みを足した（ユーザーが「入れる」を選んだ）。commit: 42220d2d |
| R2 | 方針メモ-2 | - | - | - | - | - | なし |
| H1 | 独立-3 | high | yes | self-inflicted | comment-quote | fixed | normalize がバッククォートの中の `(` を積み、閉じた後も `` ` `` がスタックに残って後ろの語頭の `#` をコメントにしない。`# ; cd /tmp` の cd を root にして通る。main と同じ挙動（2 巡目からの退行）。閉じ方: 構造 バッククォートの区間を先に確定する。commit: 22be65e5 |
| H2 | 独立-3 | high | yes | self-inflicted | timeout | fixed | `"`" not in stack` がスタックの深さに比例し、`(`×4 万と `#`×4 万の 2 行で 10 秒の timeout に届きうる（概算、未実測）。閉じ方: 構造 バッククォートの区間を先に確定する。commit: 22be65e5 |
| H3 | 独立-3 | high | yes | self-inflicted | comment-quote | fixed | バッククォートの中のコメントの `'` を引用符と読み、次の行の `git push` を落とす（`` v=`… # it's …`⏎git push origin main # don't ``）。main は検出していた（この PR の退行を tip で確かめた）。merge gate も同じ。閉じ方: 構造 バッククォートの区間を先に確定する。commit: 22be65e5 |
| H4 | 独立-3 | high | yes | self-inflicted | degraded-fallback | accepted | 縮退したとき、pre-push gate の opt-out と cd を引用符を見ない fallback の token から読む（`$'…\'…(cd ..…)'`）。mask が `$'…'` のエスケープを知らない。条件 2 から外れる。閉じ方: 構造 方針メモ-3 でユーザーが B を選び、限界の節の先頭に「直していない常時 High・実害クラス」として書く |
| H5 | 独立-3 | high | yes | inherited | quoted-separator | accepted | 列挙: `_dash_c_argument_index`（git_command_parse.py:317）が引用した区切りで走査を止める（`bash --rcfile ';' -c 'git push …'`） 方針メモ-3 でユーザーが B を選び、限界の節の先頭に「直していない常時 High・実害クラス」として書く |
| H6 | 独立-3 | high | yes | inherited | quoted-separator | accepted | is_redirection_operator が QuotedWord を除かず、`git push origin '>' main` の main を飛ばす（`>` の ref が要る）。閉じ方: 構造 方針メモ-3 でユーザーが B を選び、限界の節の先頭に「直していない常時 High・実害クラス」として書く |
| H7 | 独立-3 | high | yes | self-inflicted | cd-root | accepted | `_find_cd_root` がサブシェルの範囲を見ず、`(cd /tmp/other && make); git push` の root を /tmp/other にする。main・2 巡目・tip で同じ（以前からの穴）。閉じ方: 構造 方針メモ-3 でユーザーが B を選び、限界の節の先頭に「直していない常時 High・実害クラス」として書く |
| L1 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | PR 本文の `_expand_once_grouped` の主語は worktree guard ではなく pre-push gate・nudge |
| L2 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | QuotedWord・`_lex_by_line`・gh の `_tokenize_checked` の docstring が古い |
| L3 | 独立-3 | low | no | self-inflicted | request-drift | fixed | 承認の範囲（引用した改行、比較 2 か所）より広く直した（`{`、global option の値、dry-run の走査）。ユーザーの確認に載せる ユーザーが「このままでよい」を選んだ。commit: なし（PR 本文） |
| L4 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | 断片の Validation の CORPUS に、この巡の 5 形が無い |
| A3 | 独立-3 | advisory | no | self-inflicted | doc-claim | accepted | 退避の文字数の期待値の変更が PR 本文に無い |
| R3 | 方針メモ-3 | - | - | - | - | - | なし |
| J1 | 独立-4 | high | yes | self-inflicted | comment-quote | fixed | `_escape_quotes` が単引用符と読んだ範囲の `"` をエスケープせず、後段が引用の開始と読む（`` a=`echo "it's"`; gh pr merge 7; b=`echo "don't"` `` の merge を落とす）。閉じ方: 構造 引用符の外の区間はエスケープしない。commit: 9ba9f780 |
| J2 | 独立-4 | high | yes | self-inflicted | quoted-separator | fixed | 列挙: 区間の中の引用を外すので、引用した `;`・改行が外の区切りになり、cd・opt-out を受理する（`` echo `echo "; cd /tmp "`; git push origin main ``） 列挙ではなく構造で閉じた（方針メモ-4）。commit: 9ba9f780 |
| J3 | 独立-4 | medium | no | self-inflicted | test-power | fixed | 足したテストは `_escape_quotes` を恒等にしても通る 両方向で落ちるテストを足した。commit: fbfffe97 |
| J4 | 独立-4 | medium | no | self-inflicted | request-drift | accepted | 区間を bash の規則だけで決め、zsh と割れる形を止める側に倒していない（条件 4） 方針メモ-5 でユーザーが A（bash の読み）を選んだ。限界の節に書く |
| J5 | 独立-4 | low | no | self-inflicted | doc-claim | accepted | 区間の中の `#` を「コメントにならない」「スタックで追う」と書いた docstring・ADR・テスト名が古い |
| J6 | 独立-4 | low | no | self-inflicted | doc-claim | fixed | 「中の `'`・`"` は後の段に引用符として届かない」が偽 docstring を新しい挙動に合わせた。commit: 9ba9f780 |
| J7 | 独立-4 | advisory | no | self-inflicted | product | accepted | normalize が冪等でなく、`_mask_for_fd` の後に 2 回かける経路で読みがずれる |
| J8 | 独立-4 | advisory | no | inherited | product | accepted | `_backtick_interval` と `_scan_backtick_substitution` で閉じの規則が違う |
| R4 | 方針メモ-4 | - | - | - | - | - | なし |
| R5 | 方針メモ-5 | - | - | - | - | - | なし |
| K1 | 独立-5 | high | yes | self-inflicted | nested-shell | accepted | 二重引用符の中の区間を全部エスケープしたので、入れ子の shell の読み直しで区間の中のコマンドが 1 語になる（`` bash -c "echo `echo a; git push origin main`" ``・`` eval "x=`true; gh pr merge 7`" ``）。main は検出していた（tip で見落とすことを確かめた）。transcript の比較では該当 0 件。 差分（無効化後）巡の 2 回目の後に残った。限界の節の先頭に「直していない常時 High・実害クラス」として書く |
| K2 | 独立-5 | high | yes | self-inflicted | comment-quote | accepted | 引用符の外の区間で引用が奇数個だと引用符が区間の外へ漏れ、後ろの push・merge を見落とす（`` m=`echo don't`; git push o m; n=`echo can't` ``）。main も見落とす。J4 でユーザーが限界として受け入れた形。 差分（無効化後）巡の 2 回目の後に残った。限界の節の先頭に「直していない常時 High・実害クラス」として書く |
| K3 | 独立-5 | high | yes | self-inflicted | timeout | accepted | 区間ごとに `'"' in stack` を走査し、深さ×区間数で timeout に届きうる（見積もり、未実測）。 差分（無効化後）巡の 2 回目の後に残った。限界の節の先頭に「直していない常時 High・実害クラス」として書く |
| K4 | 独立-5 | high | yes | inherited | backtick-word | accepted | 引用符の外の区間の先頭の語がバッククォートとくっつき、`` out=`git push …` `` を git と読まない。main も同じ。 差分（無効化後）巡の 2 回目の後に残った。限界の節の先頭に「直していない常時 High・実害クラス」として書く |
| K5 | 独立-5 | low | no | self-inflicted | doc-claim | accepted | 変更断片が区間の中の引用の扱いを書いていない |
| K6 | 独立-5 | low | no | self-inflicted | doc-claim | accepted | PR 本文の「バッククォートの中の `$(…)`・`(…)` の `#` はコメントと読まない」が実装と食い違う |
| K7 | 独立-5 | advisory | no | self-inflicted | product | accepted | 二重引用符の中の区間のエスケープが `` \` `` を作り、normalize を 2 回かける経路で区間が切り直される |
| K8 | 独立-5 | advisory | no | self-inflicted | doc-claim | accepted | テストの入力の変更（閉じないバッククォート）が、PR 本文の変えたテストの一覧に無い |
| K9 | 独立-5 | advisory | no | inherited | doc-claim | accepted | 数値の主張の証拠（リポジトリの外のスクリプト）を再現できない。主張は transcript に現れた形について |
| P1 | 独立-6 | high | yes | self-inflicted | degraded-fallback | accepted | pre-push gate が、main の行ごとの読みで検査していた push を通す（複数行の二重引用符の中の `$(` の中の push、入れ子の引用の取り違え、引用符の中の `<<WORD`、縮退した片が行をまたぐときの cd・opt-out）。閉じ方: 列挙。安全策 4 で「止める」を選んだ後の指摘なので直さず、限界の節の先頭に「直していない常時 High・実害クラス」として書く |
| P2 | 独立-6 | high | yes | self-inflicted | comment-quote | accepted | 二重引用符の中の `$(…)` の素の語頭の `#` をコメントとして落とし（main は残していた）、pre-PR gate と heredoc を含む merge gate が後ろの gh を通す（bash 3.2 は実行すると推定、未実測）。閉じ方: 列挙。安全策 4 で「止める」を選んだ後なので直さず、限界の節の先頭に書く |
| P3 | 独立-6 | high | yes | inherited | degraded-fallback | accepted | 縮退した片の fallback が、1 行の中の引用の中の `;` の後ろの opt-out と cd を受理する（main の行ごとの fallback も同じ）。閉じ方: 列挙。安全策 4 で「止める」を選んだ後なので直さず、限界の節の先頭に書く |
| P4 | 独立-6 | low | no | self-inflicted | doc-claim | accepted | ADR の Addendum 2 つ（`$(…)` の中の `#`、gh 側の行継続）が実装と食い違う。限界の節に書く |
| P5 | 独立-6 | low | no | self-inflicted | doc-claim | accepted | PR 本文と断片の「二重引用符の中の `$(…)` の `#` をコメントとして読まなくなった」は入れ子の引用の中の形だけに当たる。限界の節に書く |
| P6 | 独立-6 | low | no | self-inflicted | doc-claim | accepted | 「heredoc の本文の中の `git push` の行は main と同じく検査する」が、コメントの行と本文の中の引用の対の中の行に当たらない。限界の節に書く |
| P7 | 独立-6 | low | no | self-inflicted | doc-claim | accepted | PR 本文の shell_lexer の行数（341、実際は 369）と、変えたテストの一覧の漏れ 3 件。限界の節に書く |
| P8 | 独立-6 | advisory | no | self-inflicted | doc-claim | accepted | Stop hook の押し返し（autonomy_pushback）が、変更の影響先として PR 本文と断片に挙がっていない |
| R6 | 方針メモ-6 | - | - | - | - | - | なし |
