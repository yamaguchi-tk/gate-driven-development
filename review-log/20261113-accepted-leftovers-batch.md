---
lane: L1+
pr: 671
amends: 20261003-wait-deadline-watchdog.md, 20261003-gate-runner-background.md, 20261003-task-notification-terminal-status.md, 20261015-stop-hook-background-wait.md, 20261016-stop-pushback-resumed-agent.md, 20261112-hitl-not-blocked-by-advisors.md, 20261113-lockin-revisit-before-hitl.md, 20261113-pr659-accepted-mediums.md, 20261113-taskstop-accepted-leftovers.md, 20261113-taskstop-error-inflight.md, 20261113-taskstop-result-judgment.md
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ | Opus 設計レビュー ×2 (gdd-opus-advisor, model: opus) + user | 7add41e970b3dddccb24ad225ed51bfb559227cd | 0 | 1 | 0 | 2026-11-13 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 0a5935b50fcddc02f3be082d198840e8cf7942f3 | 0 | 2 | 0 | 2026-11-13 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: fable | 6aba6870b855807ecbba9446363d763b288d02b7 | 0 | 2 | 0 | 2026-11-13 |
| 独立-3 | light-lane-independent-reviewer-xhigh, 差分, model: fable | 73a69513a8300e0320713051a9cfcfe8a0832a4f | 0 | 0 | 0 | 2026-11-13 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| I1-1 | 独立-1 | medium | no | self-inflicted | request-scope | fixed | PR 660 の I1-9（見直しの突き合わせに、見直しであることと止まった行が渡らない）を直していない。commit: 3102f4ea |
| I1-2 | 独立-1 | medium | no | self-inflicted | request-scope | fixed | PR 663 の I2-2（具体化の行に完了条件の変換の語があると lint が落とす）を直していない。commit: 3102f4ea |
| I1-3 | 独立-1 | low | no | self-inflicted | request-scope | fixed | PR 666 の I3-3、PR 670 の I1-9・I1-10・I1-12 の一部を、判定を変えるため確認なしに範囲外にした。ユーザーが A を選んだ。commit: 77637270 |
| I1-4 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | compact の「決定論で機械検査」が具体化の行に当たらない。commit: 3102f4ea |
| I1-5 | 独立-1 | low | no | self-inflicted | request-scope | fixed | 未リリースの 20261003-wait-deadline-watchdog の断片が「成功」の書き方のまま（PR 670 の I1-6 の漏れ）。commit: 3102f4ea |
| I1-6 | 独立-1 | low | no | self-inflicted | request-scope | fixed | 昇格のとき要件を固める確認を行うかが決まらない（PR 660 の I3-3 が閉じていない）。commit: 3102f4ea |
| I1-7 | 独立-1 | low | no | self-inflicted | request-scope | fixed | 要件ゲート再開の行を、委任で再入する手順が書かせていない（PR 663 の I1-7 が閉じていない）。commit: 3102f4ea |
| I1-8 | 独立-1 | low | no | self-inflicted | lockin-routing | fixed | 見直しでリスクの段を下げない規定の「前の判定」が、どこの段かを指していない。commit: 3102f4ea |
| I1-9 | 独立-1 | low | no | self-inflicted | request-scope | fixed | 見直しの突き合わせが unavailable のとき、返事の前のリスクの段を残す（PR 661 の I1-10 を直していない）。commit: 3102f4ea |
| I1-10 | 独立-1 | low | no | self-inflicted | request-scope | fixed | 「1 本目だけが返ったターン」が、相談役を 1 本しか起動していないときに当たり続ける（PR 663 の I2-6 の直しが閉じていない）。commit: 3102f4ea |
| I1-11 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 断片と PR 本文が、block の文面の指し先・planning reviewer の起動条件の広がり・読めない log での書き直しを書いていない |
| I1-12 | 独立-1 | advisory | no | self-inflicted | request-scope | accepted | 範囲の狭めの検査の例外が、記録の場所の種類を決めていない |
| I1-13 | 独立-1 | advisory | no | self-inflicted | test-power | accepted | 読めない log のテストが、root で走ると判別力を失う |
| I1-14 | 独立-1 | advisory | no | self-inflicted | style | accepted | 改名した定数に、テスト名が合っていない |
| I1-15 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | crosscheck agent の description が、昇格のときの回し直しを含めていない |
| I1-16 | 独立-1 | advisory | no | inherited | doc-claim | accepted | output-format.md の reason の表が 7 つのみのまま、行の中で staging-verification-blocked を挙げている |
| M1 | 方針メモ | medium | no | self-inflicted | taskstop-result | fixed | PR 670 の I1-9・I1-10・I1-12 と PR 666 の I3-3 を、成功の判定を 1 か所にまとめて直す（input の id と JSON の task_id・shell_id を照らす。2 本とも推奨。L1+ に切り替える）。ユーザーが A を選んだ。commit: 77637270 |
| I2-1 | 独立-2 | medium | no | self-inflicted | lockin-routing | fixed | 見直しの行を request.md に足す規定が、main の注記を書かない規定と突き合わせ agent の原文の定義にぶつかる（I1-1 の直しが閉じていない）。commit: d07e660f |
| I2-2 | 独立-2 | medium | no | self-inflicted | taskstop-result | fixed | 判定の変更を「リスクが低い」とする根拠が実測されていない。直近 30 日の TaskStop の成功の結果を数えた（notes に記録、PR 本文に件数）。commit: なし（PR 本文） |
| I2-3 | 独立-2 | low | no | self-inflicted | request-scope | fixed | 要件ゲート再開を書く規定が、委任で再入する行の片方にしか無い（I1-7 の直しが閉じていない）。commit: d07e660f |
| I2-4 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | compact の「この語を書かない」が何を指すか読めない（I1-2・I1-4 の直しが閉じていない）。commit: d07e660f |
| I2-5 | 独立-2 | low | no | self-inflicted | request-scope | fixed | 未リリースの断片 2 本に古い成功の書き方が残る（I1-5 の直しが閉じていない）。commit: d07e660f |
| I2-6 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 断片と PR 本文に、unavailable のときのリスクの段の書き換え・見直しの引用が無く、断片の 1 本目だけの語が古い |
| I2-7 | 独立-2 | low | no | self-inflicted | test-power | accepted | JSON でない block の後に JSON が来る形と、再開した agent で JSON が input と違う成功を固定するテストが無い |
| I2-8 | 独立-2 | low | no | self-inflicted | bookkeeping | fixed | 見直しをやり直すと、request.md に見直しの行が重ねて足される。commit: d07e660f |
| I2-9 | 独立-2 | advisory | no | self-inflicted | taskstop-result | accepted | 成功は全部の text block、エラーと記録は最後の block だけを読む |
| I2-10 | 独立-2 | advisory | no | self-inflicted | request-scope | accepted | 判定の変更はユーザーの返事待ちで、全件の網羅は差分の範囲では確かめられない |
| I3-1 | 独立-3 | low | no | self-inflicted | lockin-routing | accepted | 見直しの引用の扱いが、突き合わせ agent の hook の節がある形の項にしか書かれていない |
| I3-2 | 独立-3 | low | no | self-inflicted | lockin-routing | accepted | request.md の「時刻つきの行はユーザーの発言」とする hook の見出し・completion reviewer の記述と、見直しの引用が食い違う |
| I3-3 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | 要件ゲート再開を書く条件が、書く側（行き先によらず）と Step 4b・断片（再入したとき）で違う |
| I3-4 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | この PR の断片の Summary に、見直しの引用と agent の読み方が無い |
| I3-5 | 独立-3 | low | no | self-inflicted | bookkeeping | fixed | PR 本文の限界の行の先頭が、決められた 4 種類でない。commit: なし（PR 本文） |
| I3-6 | 独立-3 | advisory | no | inherited | doc-claim | accepted | 20261113-taskstop-result-judgment の断片が、output-format.md にも同じ書き方があると書いているが無い |
