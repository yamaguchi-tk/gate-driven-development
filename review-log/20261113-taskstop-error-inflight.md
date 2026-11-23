---
lane: L1+
pr: 665
follow_up_of: 663
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ | Opus 設計レビュー ×2 (gdd-opus-advisor, model: opus) + user | aa24d1beca64342b544a7b3fc802e580695440fc | 0 | 6 | 0 | 2026-11-13 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | ce04331bf52854307131a1fb72a4a55095275ccf | 0 | 3 | 0 | 2026-11-13 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: fable | 0efcdf92a018cb5c978b0d25222904591a82efcd | 0 | 1 | 0 | 2026-11-13 |
| 独立-3 | light-lane-independent-reviewer-xhigh, 差分, model: fable | 578c4e5231d75c1898eb4d8ee9adff551583ed7e | 0 | 0 | 0 | 2026-11-13 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| M1 | 方針メモ | medium | no | self-inflicted | resume-inflight | accepted | 依頼の行の案 B（再開の境界より前に起動したものだけ外す）を採らず、案 A（host が動いていないと答えた結果だけで外す）にした。実測で No task found は同じプロセスの終わった task にも返り（57 件中 52 件）、エラーの後に動いていた agent は 0/70 件。ユーザーが案 A に決めた（2026-11-13 12:30） |
| M2 | 方針メモ | medium | no | self-inflicted | resume-inflight | fixed | 未知のエラーで待ちに残ったときの手順の出口を subagent-dispatch.md に書く（TaskStop を繰り返さず gdd-stop で人に渡す）。commit: なし（方針メモ。実装の commit で入れる） |
| M3 | 方針メモ | medium | no | self-inflicted | resume-inflight | fixed | 配線に pre-push の _reviewer_outcomes と wait_watchdog のコメントを足し、テストを足す。commit: なし（方針メモ） |
| M4 | 方針メモ | medium | no | self-inflicted | resume-inflight | fixed | 入力集合に id の前方一致・包みの有無・text block の list・未知のエラーの後の No task found・再開と TaskStop の順を足す。commit: なし（方針メモ） |
| M5 | 方針メモ | medium | no | self-inflicted | resume-inflight | fixed | QA を parser の前後比較にし、結果の無い TaskStop と結果の行が先に来る件を数える（1,936 件中 2 件・0 件）。commit: なし（方針メモ） |
| M6 | 方針メモ | medium | no | self-inflicted | resume-inflight | accepted | 決まった文面に当たらないエラーの記録は足さない（新しい記録の仕組みになる。host の文面の変化は transcript の実測で気づける）。限界: host が文面を変えると、再開の手順で PR 659 の型が戻る |
| I1-1 | 独立-1 | medium | no | self-inflicted | request-scope | accepted | 依頼の「この PR が扱う行」の手段（再開の境界で絞る）を、host が動いていないと答えた結果で外す形に替えた。ユーザーが案 A に決めた（2026-11-13 12:30） |
| I1-2 | 独立-1 | medium | no | self-inflicted | resume-inflight | fixed | ユーザーの指示で直した。拒否などで返ったときの停止を、loop state を保つ clarification-needed と決め、手順と押し返しの文面に書いた。commit: 0efcdf92 |
| I1-3 | 独立-1 | medium | no | self-inflicted | resume-inflight | fixed | ユーザーの指示で直した。state-machine.md・setup-gdd-loop.sh・subagent-dispatch.md の超過の段落・wait_watchdog の 2 つの文面に、TaskStop がほかのエラーで返ったときの出口を足した。commit: 0efcdf92 |
| I1-4 | 独立-1 | low | no | self-inflicted | resume-inflight | accepted | 再開の手順の条件「TaskStop も無い dispatch」が、結果の無い TaskStop だけが残った dispatch に当たらない |
| I1-5 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | PR 本文の限界に、前のプロセスの dispatch への TaskStop が拒否されたときも待ちに残ることを足した。commit: なし（PR 本文） |
| I1-6 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | stop-hook-structured-markers.md などの「TaskStop もまだ」の説明が残る |
| I1-7 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 未リリースの 20261112 の断片と、この断片の「今までは」が食い違う |
| I1-8 | 独立-1 | low | no | self-inflicted | bookkeeping | accepted | 断片の Validation に時点の実測値を書いている |
| I1-9 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | PR 本文の PR 659 の症状の向き（押し返しが出なくなった）を直した。commit: なし（PR 本文） |
| I1-10 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | _TASK_STOP_NOT_RUNNING_RES のコメントが文面を場面（前のプロセス）に結び付けている |
| I1-11 | 独立-1 | low | no | self-inflicted | resume-inflight | accepted | 成功の側は is_error でなければ本文を問わず外す（拒否が is_error なしで書かれると外れる。実データでは未確認） |
| I1-12 | 独立-1 | advisory | no | inherited | resume-inflight | accepted | TaskStop の input の別名（shell_id）を読まない |
| I1-13 | 独立-1 | advisory | no | self-inflicted | style | accepted | 否定先読みは働いておらず、前方一致は等号の比較が防いでいる |
| I2-1 | 独立-2 | medium | no | self-inflicted | resume-inflight | fixed | ユーザーが指示した I1-2 の修正の欠けとして直した。押し返しの文面の条件を、成功・No task found・is not running 以外のエラーにそろえた。commit: 578c4e52 |
| I2-2 | 独立-2 | low | no | self-inflicted | request-scope | fixed | 依頼の原文（I1-3）との突き合わせ。stop-hook-structured-markers.md・human-check-template.md・docstring 3 か所の「TaskStop もまだ」を、動いていないと答えた結果に言い換えた。commit: 578c4e52 |
| I2-3 | 独立-2 | low | no | self-inflicted | resume-inflight | fixed | ユーザーが指示した I1-2 の修正の欠けとして直した。手順の文書と押し返しの文面に、STOP_PATTERN に当たる完全な marker を書かない。commit: 578c4e52 |
| I2-4 | 独立-2 | low | no | self-inflicted | test-power | accepted | 足した入口のテストの clarification-needed の側は、停止が通ることまでは固定していない（wait watchdog が押し返さないことだけ） |
| I2-5 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | ユーザーが指示した I1-3 の修正の欠けとして直した。state-machine.md の括弧の説明を、先に TaskStop で止めるの直後に戻した。commit: 578c4e52 |
| I2-6 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | clarification-needed の用途を定める state-machine.md:58・gdd-dev.md:154・setup-gdd-loop.sh の一覧が、TaskStop のエラーの出口の用途に追随していない |
| I2-7 | 独立-2 | low | no | self-inflicted | request-scope | fixed | 依頼の原文に、ユーザーの発言が指す案 A と I1-2・I1-3 の文を、assistant の文と分かる形で引用して足した。commit: なし（review-log） |
| I2-8 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | 押し返されるの全称が、連続 block の上限などの飛ばす条件より広い |
| I2-9 | 独立-2 | advisory | no | self-inflicted | style | accepted | 期限切れの dispatch が複数あると、案内の文が行ごとに重なる |
| I3-1 | 独立-3 | low | no | self-inflicted | resume-inflight | accepted | human-check-template.md の相談役の TaskStop が拒否されたときの出口が、指し先（再開の手順の clarification-needed）と、返事をそのまま扱う読みの 2 通りに読める |
| I3-2 | 独立-3 | low | no | self-inflicted | bookkeeping | accepted | 変更断片の Affected Files と Summary に human-check-template.md・stop-hook-structured-markers.md が無い |
| I3-3 | 独立-3 | low | no | self-inflicted | doc-claim | fixed | PR 本文の挙動の変化に、human check で相談役の TaskStop が拒否されても繰り返さないことを足した。commit: なし（PR 本文） |
| I3-4 | 独立-3 | low | no | inherited | doc-claim | accepted | test_stop_hook_resumed_agent_wait.py の module docstring と test_wait_watchdog.py:173 に「TaskStop が来たら終わり」の言い方が残る |
| I3-5 | 独立-3 | low | no | self-inflicted | bookkeeping | re-reported | 変更断片の Validation 欄の時点の実測値（I1-8 と同じ） |
| I3-6 | 独立-3 | advisory | no | self-inflicted | style | accepted | state_clear の押し返しの文面から marker の書式の例が消えた |
