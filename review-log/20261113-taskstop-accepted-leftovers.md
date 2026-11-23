---
lane: L1
pr: 666
amends: 20261003-gate-runner-background.md, 20261003-wait-deadline-watchdog.md, 20261015-stop-hook-background-wait.md, 20261016-stop-pushback-resumed-agent.md, 20261112-hitl-not-blocked-by-advisors.md, 20261113-taskstop-error-inflight.md
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 1fb37c6370bc6148da757ae8543be2f12624ce6c | 0 | 0 | 0 | 2026-11-13 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: fable | 9bb5a5fe0e269ecc76508f8839b7dc26f183d528 | 0 | 0 | 0 | 2026-11-13 |
| 独立-3 | light-lane-independent-reviewer-xhigh, 差分, model: fable | 0240c1409a1e575c45066da5d84b5891fea30ecd | 0 | 0 | 0 | 2026-11-13 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| I1-1 | 独立-1 | low | no | self-inflicted | request-scope | fixed | 依頼の M6（決まった文面に当たらないエラーの記録）を変えずに残した根拠が、PR 本文に無い。直近 30 日でその形のエラーは 0 件で、root CLAUDE.md の当たる件数が 0 なら足さない規則に当たることを PR 本文に書いた。commit: なし（PR 本文） |
| I1-2 | 独立-1 | advisory | no | self-inflicted | request-scope | fixed | 依頼の I1-13（効いていない否定先読み）を残した。先読みが一致を変えず、効いているのは等号の比較であることを transcript.py のコメントに書いた。commit: d9edd964 |
| I1-3 | 独立-1 | low | no | inherited | request-scope | fixed | 依頼の I1-6・I1-7 の「など」に当たる未リリースの断片 4 本に、TaskStop を呼べば外れるという書き方が残る。host が動いていないと答えた結果に書き換えた。commit: d9edd964 |
| I1-4 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 断片の「前の版では」の比べる相手が、リリース済みの版に無い。前の版との比較を消し、今の条件だけを書いた（20261112 の断片も同じ）。commit: d9edd964 |
| I1-5 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | output-format.md の blocked の行（正本の表）が、TaskStop のエラーのときの例外に追随していない。例外を足した。commit: d9edd964 |
| I1-6 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | state-machine.md:58 で、複数回発火してよいの文が要件を固める確認の括弧に入り、intake 停止に掛からなくなった。intake 停止と要件を固める確認の 2 つに掛かる文にした。commit: d9edd964 |
| I1-7 | 独立-1 | low | no | self-inflicted | test-power | accepted | timer の終わりのテストは成功の TaskStop だけで、shell への No task found・is not running を通すテストが無い |
| I1-8 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 出口の案内が指す書式の文書には、## 👤 次にすること の見出しが要ることが書かれていない |
| I1-9 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | state-machine.md:657 の押し返すの全称に、飛ばす条件の指し先が無い |
| I1-10 | 独立-1 | advisory | no | self-inflicted | doc-claim | fixed | PR 本文に setup-gdd-loop.sh の押し返しを飛ばす条件の指し先の追加が無い。足した。commit: なし（PR 本文） |
| I1-11 | 独立-1 | advisory | no | self-inflicted | doc-claim | fixed | 断片の setup-gdd-loop.sh の記述が、もとからあった受け渡しの文を足したように読める。足したものに合わせて書き直した。commit: d9edd964 |
| I2-1 | 独立-2 | low | no | self-inflicted | request-scope | next-pr | 依頼の I1-11・I1-12・M6 を、実測 0 件と root CLAUDE.md の規則で足さずに閉じていた。ユーザーが別 PR で足すと決めた |
| I2-2 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | 否定先読みのコメントが 2 本目の正規表現に当たらない（2 本目の先読みは running の後ろで一致を変える）。2 本を書き分けた。commit: c73b8c8b |
| I2-3 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | output-format.md の例外を blocked の行だけに足したので、cancelled・done など、ほかの loop state を消す停止の行に例外が無い |
| I2-4 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | state-machine.md:58 の複数回発火の文が、TaskStop の受け渡しにも複数回起きうることを書いていない |
| I2-5 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | 20261112 の断片の再開の手順の条件が、そろえた条件に追随していない。subagent-dispatch.md と同じ条件にした。commit: c73b8c8b |
| I2-6 | 独立-2 | advisory | no | inherited | doc-claim | accepted | 20261003-task-notification-terminal-status の断片が、成功の結果だけを書き、ほかの 6 本と粒度が違う |
| I2-7 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | この PR の断片の「1 回だけ出すようにした」は、未リリースの状態との比較である |
| I2-8 | 独立-2 | advisory | no | inherited | doc-claim | out-of-diff | output-format.md の正本の表が 7 つのみと書き、staging-verification-blocked の行が無い |
| I2-9 | 独立-2 | advisory | no | inherited | doc-claim | accepted | faq.md の blocked の説明に、TaskStop のエラーの例外が無い |
| I3-1 | 独立-3 | medium | no | self-inflicted | request-scope | next-pr | I2-1 と同じ。依頼の I1-11・I1-12・M6 をコードを変えずに閉じていた。ユーザーが別 PR で足すと決めた |
| I3-2 | 独立-3 | low | no | inherited | test-power | accepted | 2 本目の否定先読みが外す文面（is not runnings など）を固定するテストが無い |
| I3-3 | 独立-3 | advisory | no | inherited | style | accepted | 1 本目の、一致の結果を変えない否定先読みが正規表現に残る |
| I3-4 | 独立-3 | advisory | no | self-inflicted | bookkeeping | fixed | 足さない根拠の実測のコマンドが残っていない。notes.md に書いた。commit: なし（review-log） |
