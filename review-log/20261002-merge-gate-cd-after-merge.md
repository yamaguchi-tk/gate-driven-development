---
lane: L1+
pr: 279
follow_up_of: 268
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ | Opus 設計レビュー (general-purpose, model: opus)（旧#268 の next-pr。ユーザーの指示「マージが自律的に出来ないのは困る、hook が原因なら修正して」と、2026-10-02 のユーザーの選択「誤 block を先に」に当たる。Opus は「マージを含む segment の終わりで切る」に賛成し、条件を思いつく語の列挙ではなく bash の予約語の全集合・括弧を含む token・`&`・入れ子 shell にするよう推した〔許可リスト側は関数定義の後の呼び出しを通すので危険〕。main の案と食い違いは残らず、Fable は呼んでいない。memory の 2026-09-28 の決定に従い、ユーザーへの確認は内部の相談で代えた） | - | 0 | 0 | 0 | 2026-10-02T23:20+09:00 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 2dfed7605b4321faf14eba0b91864911df878a57 | 2 | 1 | 2 | 2026-10-02T23:50+09:00 |
| 独立-2 | light-lane-independent-reviewer, 差分, model: opus | bba52bebd527c673db8027e2b189ef809d803323 | 1 | 0 | 1 | 2026-10-03T00:30+09:00 |
| 方針メモ-2 | Opus 設計レビュー (general-purpose, model: opus) + Fable アドバイザリ (general-purpose, model: fable)（安全策 4 の発火〔クラスタ fail-open の high が独立-1・独立-2 の 2 巡〕。Opus は、同じ型の穴がほかに 3 つ〔バッククォートの `repeat`、語の途中の行継続、`trap`〕あることを示した。main も実測で再現した〔どれも main は止め、この PR は通す〕。Opus は、拒否リストへの継ぎ足しをやめ、コマンド文字列に対する許可リストへ作り直すよう推した。main の案〔縮退フラグを渡す 1 行の修正〕と食い違ったので、信号 ①② で Fable を呼んだ。Fable は許可リストに賛成し、入れ子 shell・単独の `&`・`merge` の語の数・`~` を足すよう修正した。main は実データ〔transcript の、マージの後ろに cd がある Bash コマンド 164 件〕を測り、リダイレクトの `<` `>` も許すことにした。方針メモ〔2026-10-02〕で Opus が許可リストを退けた理由は「コマンド名の許可は関数定義の後の呼び出しを通す」だった。今回の許可リストは文字種で見て括弧・波括弧を除くので、関数定義を書けない。memory の 2026-09-28 の決定に従い、ユーザーへの確認は内部の相談で代えて、Fable の修正付きの Opus 案を採った） | - | 0 | 0 | 0 | 2026-10-03T01:00+09:00 |
| 独立-3 | light-lane-independent-reviewer, 差分, model: opus | 2ffffab68e473c73e2ff88a084f6a1a46e012eed | 2 | 0 | 2 | 2026-10-03T08:00+09:00 |
| 方針メモ-3 | Opus 設計レビュー (general-purpose, model: opus)（安全策 4 の 2 回目の発火〔high を含む巡が 3 回、どれも fail-open〕。main は 2 件とも実測で再現した〔zsh の括弧なしの `foreach` は位置パラメータで回る。`cd /Q`・パイプ・`gh pr merge 7 && cd /R` の形 は main では None、この PR では `/Q`〕。Opus は「続行して 2 件ともこの PR で直す」を推した〔予約語は zshmisc の表との差分で閉じ、`foreach`・`end`・`sched` を足す。`cd` の次の区切りは 4 種の列挙で閉じる。どちらも止める側に倒れる修正〕。main の案と食い違いは無かった。Fable はこの PR で 1 回使ったので呼んでいない。memory の 2026-09-28 の決定に従い、ユーザーへの確認は内部の相談で代えて続行した。無効化後の差分巡で同じ型の high がまた出たら、部品の撤回を選択肢の先頭に置く） | - | 0 | 0 | 0 | 2026-10-03T08:20+09:00 |
| 独立-4 | light-lane-independent-reviewer, 差分（無効化後）, model: opus | 3e26fd79bbb0e7d9b3c29ef3739ef5d53f5ec723 | 2 | 0 | 2 | 2026-10-03T09:00+09:00 |
| 方針メモ-4 | Opus 設計レビュー (general-purpose, model: opus)（安全策 4 の 3 回目の発火。main は縮小を提案した〔cd の次の区切りで実行先を変える変更を戻して main と同じ判定にし、代わりにマージより前の区切りが && と ; だけのときに限って切る〕。Opus は縮小案を実際の parse に差し込んで確かめ、main より緩くなるのは、root を解決できない経路で後ろの cd が生んでいた誤 block が消える差だけだとして、続行を推した。次の確かめの差分巡で、切ることに由来する fail-open の high がまた出たら「止める」にする。main の案と食い違いは無く、Fable はこの PR で 1 回使ったので呼んでいない。memory の 2026-09-28 の決定に従い、ユーザーへの確認は内部の相談で代えた） | - | 0 | 0 | 0 | 2026-10-03T09:20+09:00 |
| 独立-5 | light-lane-independent-reviewer, 差分（無効化後）, model: opus | 7f85eca51474efb96960bd9c038256be02bfcc00 | 2 | 0 | 2 | 2026-10-03T10:00+09:00 |
| 方針メモ-5 | Opus 設計レビュー (general-purpose, model: opus) + user（安全策 4 の 4 回目の発火で、確かめの差分巡の 2 回目〔上限〕。main は、同じ文字列の中で定義した alias が zsh -c・eval の外側・Bash ツールで 2 行目に効かないことを実測した。Opus は、eval を通せば効くこと〔その形は入れ子 shell として全体を見て止まる〕と、利用者のシェル設定の alias では届くことを示し、F1 を到達不能とは書かずに条件付きの限界として書き、「止める」とマージの判断をユーザーに 1 回確認するよう推した。Fable はこの PR で 1 回使ったので呼んでいない。残った high は accepted にし、ユーザーに確認した。ユーザーは「CI 後にマージ」を選んだ） | - | 0 | 0 | 0 | 2026-10-03T10:20+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| K1 | 方針メモ | - | - | - | - | - | なし |
| A1 | 独立-1 | high | yes | self-inflicted | approval-path | fixed | zsh の `repeat`・`foreach` が囲む構文の語に無く、`repeat 2 gh pr merge 7 && cd /other` で 2 回目のマージが別 repo で走るのに切り出して通す。zsh の予約語を足した commit: f33a9350 |
| A2 | 独立-1 | high | yes | self-inflicted | fail-open | fixed | 区切りごとに token 列全体を写すので切り出しが 2 乗になり、区切りの多いコマンドで hook の timeout を超えて通る。区切りの範囲だけを渡す commit: f33a9350 |
| A3 | 独立-1 | medium | no | self-inflicted | product | fixed | 入れ子 shell の有無を見るのに全層を展開し、IG-6 の展開をもう 1 回走らせる。1 層目の有無だけを見る commit: f33a9350 |
| A4 | 独立-1 | low | no | self-inflicted | product | fixed | `_extract_cd_target` が切り出しを通らず、本番経路と判定が食い違う。同じ切り出しを通す commit: f33a9350 |
| A5 | 独立-1 | low | no | self-inflicted | test-power | fixed | マージの前と後ろで別の repo に cd する形が止まることのテストが無い。テストを足した commit: 781ed86f |
| A6 | 独立-1 | low | no | self-inflicted | test-power | fixed | マージの後ろに `eval` を挟む形が止まることのテストが無い。テストを足した commit: 781ed86f |
| A7 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 断片が改行の形を広く止めると書くが、止まるのは演算子を置かずに改行して cd を続ける形だけ。断片を直した commit: 3b3c7981 |
| A8 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 断片が、マージより後ろの `env -C` なども判定に使わなくなることを書いていない。断片に書き足した commit: 3b3c7981 |
| A9 | 独立-1 | advisory | no | self-inflicted | product | accepted | gh_command_parse.py が 1500 行を超えたまま行が増える。PR 本文に例外の理由を書く |
| A10 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | PR 本文の草案の「`compgen -k` の 22 語」が、zsh の語を足すと合わない。PR 本文に列挙 |
| B1 | 独立-2 | high | yes | self-inflicted | fail-open | fixed | heredoc を含み縮退した形（`:;while true;do gh pr merge 7 && cd /x;done;git commit -m 'note <<E…`）で予約語が単独の token にならず、切り出してマージの後ろの cd を見落とす。コマンド文字列に対する許可リストにした commit: dfb0e4f6 |
| B2 | 独立-2 | low | no | self-inflicted | test-power | fixed | `foreach`・`end` を足したことをテストが固定していない（括弧で止まる）。許可リストに作り直して、括弧で止まる語を外した commit: dfb0e4f6 |
| B3 | 独立-2 | low | no | self-inflicted | test-power | fixed | 時間のテストの切り出しの assert が、どの実装でも通る。マージの後ろに cd を置いて切れる位置を確かめた commit: 11d85c80 |
| B4 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | `_extract_cd_target` の docstring の 2 段落目が、走査範囲を全体のままと書く。切り出せない形では、と直した commit: dfb0e4f6 |
| B5 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | 断片が、改行の形をマージがまた走りうる形の列挙に入れている。理由を分けて書き直した commit: bd1b8ee1 |
| B6 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | `_COMPOUND_WORDS` のコメントが zsh の予約語の全体に読める。許可リストへの作り直しで、コメントごと書き直した。PR 本文に列挙 |
| B7 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | `_has_chdir_intent` の docstring の例（マージより後ろの `git -C`）が、本番の経路では intent にならない。PR 本文に列挙 |
| B8 | 独立-2 | advisory | no | self-inflicted | style | accepted | gh_command_parse.py が 1,500 行を超えて増える。PR 本文に例外の理由を書く |
| B9 | 独立-2 | advisory | no | self-inflicted | test-power | accepted | 時間のテストが壁時計で測る（既存の timing_budget は CPU 時間）。PR 本文に列挙 |
| K2 | 方針メモ-2 | - | - | - | - | - | なし |
| C1 | 独立-3 | high | yes | self-inflicted | fail-open | fixed | zsh の括弧なしの `foreach`（`set -- 1 2; foreach p; gh pr merge 7 --merge; cd /x; end`）で切り出し、cd の後の 2 回目のマージを見落とす。`foreach`・`end`・`sched` の語を足した commit: f3026db5 |
| C2 | 独立-3 | high | yes | inherited | fail-open | fixed | マージより前の `cd /Q` の次の区切りがパイプ・`&`・論理和でも `/Q` を実行先にする。この PR では `cd /Q`・パイプ・`gh pr merge 7 && cd /R` の形 にも届く。次の区切りが 4 種のときは実行先にしない commit: f3026db5 |
| C3 | 独立-3 | low | no | self-inflicted | test-power | accepted | `trap` と `bash -c` のテストが、それぞれの条件ではなく merge の語の数・区切りの無さで止まり、条件を固定していない。PR 本文の限界に書く |
| C4 | 独立-3 | low | no | self-inflicted | test-power | accepted | `_extract_cd_target` は token をつないだ文字列で許可リストを見るので本番より切りやすい（本番からの呼び出しは無い）。PR 本文の限界に書く |
| C5 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | テストのモジュールの docstring が、構文の列挙で切る古い規則のまま。PR 本文の限界に書く |
| C6 | 独立-3 | advisory | no | self-inflicted | style | accepted | gh_command_parse.py が 1,500 行を超えたまま増える。PR 本文に例外の理由を書く |
| K3 | 方針メモ-3 | - | - | - | - | - | なし |
| D1 | 独立-4 | high | yes | self-inflicted | fail-open | fixed | cd の次の区切りで実行先を None にした変更で、marker の無い git の cwd の経路が台帳の照合を unknown にして通す（`cd <台帳の repo の clone> ‖ exit 1; gh pr merge 7` を main は止めていた）。変更を戻し、マージより前の区切りが && と ; だけのときに限って切る commit: cf670971 |
| D2 | 独立-4 | high | yes | inherited | fail-open | accepted | `cd /W && true & gh pr merge 7` と zsh の `cd /W &｜ gh pr merge 7` で /W を実行先にする。main も同じ値で、この PR の切り出しは & を含む形を切らないので判定は main と同じ。PR 本文の限界の先頭に書き、次の PR で直す |
| D3 | 独立-4 | low | no | self-inflicted | product | fixed | `cd X ‖ exit 1; gh pr merge …` を新たに誤 block し、理由の文も誤り。D1 の修正で main と同じ判定に戻り、文も消えた commit: cf670971 |
| D4 | 独立-4 | low | no | self-inflicted | test-power | accepted | 足したテストが新しい検査の範囲を固定していない。D1 の修正で検査ごと戻したので、テストも書き直した。PR 本文の限界に書く |
| D5 | 独立-4 | low | no | self-inflicted | test-power | accepted | `sched` の語にテストが無い。PR 本文の限界に書く |
| D6 | 独立-4 | advisory | no | self-inflicted | doc-claim | accepted | テストのコメントの演算子の数がループと合わない。D1 の修正でテストごと書き直した。PR 本文に列挙 |
| D7 | 独立-4 | advisory | no | self-inflicted | doc-claim | accepted | `_extract_cd_target` の docstring が新しい条件を含まない。D1 の修正で条件ごと戻した。PR 本文に列挙 |
| D8 | 独立-4 | advisory | no | self-inflicted | style | accepted | gh_command_parse.py が 1,500 行を超えたまま増える。PR 本文に例外の理由を書く |
| K4 | 方針メモ-4 | - | - | - | - | - | なし |
| E1 | 独立-5 | high | yes | self-inflicted | fail-open | accepted | 切り出しの予約語の検査が、alias で引用符を挟んだ予約語（`alias rr=rep'eat'` の後の `rr 2 gh pr merge 7 --merge && cd /other`）を見落とす。同じコマンド文字列の中の alias は eval を通さないと効かず、eval の形は止まる。利用者のシェル設定の alias では届く。PR 本文の限界の先頭に書く |
| E2 | 独立-5 | high | yes | inherited | fail-open | accepted | chdir の語が cd・pushd・popd の token 一致だけで、`. /dev/stdin <<< 'cd /x'`・zsh の `chdir`・alias 経由の cd を見ない（main と同じ）。PR 本文の限界の先頭に書き、次の PR で直す |
| E3 | 独立-5 | low | no | self-inflicted | test-power | accepted | 足した blocker の語（`sched`、`foreach` と `end` の片方）が 1 語ずつはテストで固定されていない。PR 本文の限界に書く |
| E4 | 独立-5 | low | no | inherited | test-power | accepted | `_extract_cd_target` と本番の経路が、許可リストを別の文字列に当てている（本番からの呼び出しは無い）。PR 本文の限界に書く |
| E5 | 独立-5 | advisory | no | self-inflicted | doc-claim | accepted | `_through_merge_segment` の docstring に、マージより前の区切りの条件が無い（コメントにはある）。PR 本文に列挙 |
| E6 | 独立-5 | advisory | no | inherited | doc-claim | accepted | PR 本文の抜粋の「`2>&1` 以外の `&`」が不正確。PR 本文を断片の書き方にそろえる |
| E7 | 独立-5 | advisory | no | self-inflicted | doc-claim | accepted | 限界の例に、マージより前にパイプ・論理和がある形が無い。PR 本文に書く |
| E8 | 独立-5 | advisory | no | self-inflicted | style | accepted | gh_command_parse.py が 1,500 行を超えたまま増える。PR 本文に例外の理由を書く |
| K5 | 方針メモ-5 | - | - | - | - | - | なし |
