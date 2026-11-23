---
lane: L1+
pr: 453
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ | Opus 設計レビュー (gate-driven-development:gdd-opus-advisor, model: opus) + user | 4ee07068 | 0 | 0 | 0 | 2026-10-13 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | ca8bf985 | 0 | 1 | 0 | 2026-10-13 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | c549f04a | 0 | 1 | 0 | 2026-10-13 |
| 方針メモ-1 | Opus 設計レビュー (gate-driven-development:gdd-opus-advisor, model: opus) + user | c549f04a | 0 | 0 | 0 | 2026-10-13 |
| 独立-3 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 4908fb3d | 0 | 0 | 0 | 2026-10-13 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| M-1 | 方針メモ | advisory | no | inherited | design | accepted | 採用: 案 D。読む側の完全一致は変えず、WARN の入口を「値にマージを含み表の値でない」と「マージの値で evidence が human: でない」に広げ、§ 事前回答 5 に当てはめの例を足す。ユーザーは Fable の意見を求め、Fable も D を推した後に D を選んだ |
| I1-1 | 独立-1 | medium | no | self-inflicted | product | fixed | human: でない evidence の WARN が status を見ず、承認前（pending・changes_requested）の正規の書き込みでも出ていた。承認前は出さず、gate の subagent は書き換えない旨を足した commit: 55d91df3 |
| I1-2 | 独立-1 | low | no | self-inflicted | bookkeeping | fixed | 新しい発火条件の件数とコマンドが PR 本文の目的に無かった。既存の state.md で数えて PR 本文に書いた commit: なし（PR 本文） |
| I1-3 | 独立-1 | low | no | self-inflicted | product | fixed | PR マージ後検証 / 再学習まで を startswith で除き、注記付きの値を知らせていなかった。表の値そのものだけを除き、注記付きには 1 操作ごとの承認のままと知らせる文を返す commit: 55d91df3 |
| I1-4 | 独立-1 | low | no | self-inflicted | product | accepted | 列挙: 入口が マージ の語の部分一致で、英語の merge の値は知らせず、マージを外す文にも知らせる。入口はユーザーが案 D で選んだ形で、入力が開いているので限界に書く |
| I1-5 | 独立-1 | low | no | self-inflicted | product | fixed | 書き込みを含み宣言の無い repo の当てはめ先が template に無く、案 D に無い「引き上げない」を足していた。PR 作成まで にそろえた commit: 55d91df3 |
| I1-6 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | lint-approved-direction.py と test_pre_answer_contract.py の docstring が古い入口のままだった commit: 55d91df3 |
| I1-7 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | template に足した文が hook の入口より狭く読めた commit: 55d91df3 |
| I1-8 | 独立-1 | low | no | self-inflicted | style | fixed | 入口とループで human: の後の空白の扱いが違い、WARN が重複した。値を 1 回だけ正規化する commit: 55d91df3 |
| I1-9 | 独立-1 | low | no | inherited | product | fixed | approved でない status（承認・approved（注記））を知らせていなかった commit: 55d91df3 |
| I1-10 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 名指しで起動した後の扱い（推奨を確認に載せ直し、承認として扱わない）が description に無い |
| I1-11 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | opus にも同じ扱いが要ると判断した根拠が PR 本文に無い（PR 本文に書く） |
| I1-12 | 独立-1 | advisory | no | self-inflicted | bookkeeping | fixed | 断片の Validation に test_pre_answer_contract.py が無い commit: 48a087bb |
| I1-13 | 独立-1 | advisory | no | self-inflicted | bookkeeping | accepted | Skill RED-GREEN Evidence が要るかが PR 本文から見えない |
| I2-1 | 独立-2 | medium | no | self-inflicted | product | next-pr | human: でない evidence の WARN が、表の外の自走上限をそのまま human: に写すよう示す。自走上限が表の値のときだけ human:<値> を示す形にする |
| I2-2 | 独立-2 | medium | no | self-inflicted | product | fixed | approved でない status の WARN は案 D の外で、実測 0 件だった。枝を外した commit: 4908fb3d |
| I2-3 | 独立-2 | medium | no | self-inflicted | test-power | next-pr | 承認前の status を除くテストが、除外を消しても落ちない。assertEqual(notes, []) にする |
| I2-4 | 独立-2 | low | no | self-inflicted | product | accepted | 列挙: 「マージの値」を「マージ を含む値」と読み、マージを人に残す値にも知らせる。入口の語の一致はユーザーが案 D で選んだ形で、I1-4 と同じく限界に書く |
| I2-5 | 独立-2 | low | no | self-inflicted | product | fixed | 承認前の status で evidence の WARN を出さないことは案 D を狭める。ユーザーに確かめ、A（出さない）を選んだ発言を request.md に足した commit: 4908fb3d |
| I2-6 | 独立-2 | low | no | self-inflicted | product | fixed | 注記付きの PR マージ後検証 / 再学習まで の WARN は実測 0 件で、件数が PR 本文に無かった。案 D の入口の字面に入るので残し、件数を PR 本文に書いた commit: なし（PR 本文） |
| I2-7 | 独立-2 | low | no | self-inflicted | product | next-pr | 注記の無い PR マージ後検証 / 再学習まで も、行の数・形の WARN に進むようになった |
| I2-8 | 独立-2 | low | no | self-inflicted | product | fixed | template の「決められなければ PR 作成まで」は案 D の外で、引き上げの発話で値が下がりうる。外した commit: 4908fb3d |
| I2-9 | 独立-2 | low | no | self-inflicted | test-power | next-pr | 新しい WARN に hook の入口からのテストが無い（注記付きの PR マージ後検証、status だけの書き込み） |
| I2-10 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | 断片の書き方では evidence の WARN が status を問わないと読めた commit: 4908fb3d |
| I2-11 | 独立-2 | low | no | self-inflicted | doc-claim | next-pr | 同じ WARN の範囲を書く human-check-template.md:707・rollback-patterns.md:117・gdd-systematic-debugging/SKILL.md:213・autonomy_value.py:5 が狭い説明のまま |
| I2-12 | 独立-2 | low | no | self-inflicted | doc-claim | next-pr | test_pre_answer_contract の docstring が、status と evidence を見る条件（自走上限がマージの値のとき）を書いていない |
| I2-13 | 独立-2 | advisory | no | self-inflicted | product | accepted | status の WARN が evidence の WARN を隠す（status の WARN は外したので当たらない） |
| P1-1 | 方針メモ-1 | advisory | no | inherited | design | accepted | 採用: A。承認前の status（pending・changes_requested）では evidence の WARN を出さない。Opus・Fable とも A を推し、ユーザーが A を選んだ |
| I3-1 | 独立-3 | low | no | self-inflicted | doc-claim | next-pr | template から外した「どちらとも決められなければ PR 作成まで」が、hook の表の外の値の WARN の本文（autonomy_value.py:103）に残っている |
| I3-2 | 独立-3 | low | no | self-inflicted | doc-claim | next-pr | 断片と PR 本文の除外の理由「evidence: none が正規の形」は、changes_requested では成り立たない（schema では review run の id など） |
| I3-3 | 独立-3 | low | no | self-inflicted | test-power | next-pr | _status_notes の条件を、schema の 3 値の外の status（承認 など）と、pending での値の WARN で固定するテストが無い |
| I3-4 | 独立-3 | advisory | no | self-inflicted | doc-claim | accepted | approved でない status（注記付きの approved など）を知らせないことが、限界の節に無い |
| I3-5 | 独立-3 | advisory | no | self-inflicted | doc-claim | accepted | PR 本文に、本文の中で定義していない「案 D」の語がある |
