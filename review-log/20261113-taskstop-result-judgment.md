---
lane: L1+
pr: 670
follow_up_of: 666
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ | Opus 設計レビュー ×2 (gdd-opus-advisor, model: opus) + user | 2a9c49a3cca682ee1ec7f4ddc1c6a1d4f1cf7792 | 0 | 3 | 0 | 2026-11-13 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | fbfba9910ede31411214721693213d8fd75fe4c1 | 0 | 0 | 0 | 2026-11-13 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| M1 | 方針メモ | medium | no | self-inflicted | taskstop-result | fixed | I1-11 は、成功の結果で target を外す分岐に比較を足すのではなく、分岐を消す（成功は _stopped_task_id の JSON の id だけで外す。2 本とも推奨）。commit: 9f913781 |
| M2 | 方針メモ | medium | no | self-inflicted | taskstop-result | fixed | M6 の記録の対象を、未知の文面のエラーだけでなく、target があって待ちから外さなかった TaskStop の結果の全部にする（2 本とも推奨）。commit: 9f913781 |
| M3 | 方針メモ | medium | no | self-inflicted | taskstop-result | fixed | 受理集合を書き並べた agent 向けの文面と文書を、成功に止めた id が書かれていることを含む形にそろえる（Opus-1）。commit: fbfba991 |
| M4 | 方針メモ | low | no | self-inflicted | taskstop-result | fixed | I1-12 は task_id が無いときだけ shell_id を読むのではなく、両方を候補にし、文面の id が候補のどれかと同じときに外す（Opus-2。Opus-1 は main の案のままでよいとした。広い側を採った）。commit: 9f913781 |
| I1-1 | 独立-1 | low | no | self-inflicted | request-scope | accepted | 記録を書くのは GDD の loop の中の Stop だけで、マージ待ちの押し返し・pre-push の経路では書かない。依頼は経路を決めておらず、目的（host の結果の形の変化に気づく）は 1 か所で足りる（Opus 2 本とも、依頼を縮めていないので聞かずに進める。直近 30 日の TaskStop の 94% は GDD の loop の transcript の中） |
| I1-2 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | record_unaccepted_task_stops の docstring の「log が読めないときは書く側に倒す」が実装と合わない（読めないと OSError で抜ける） |
| I1-3 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 案内の「止めた id の書かれた成功」が、判定（本文の JSON の task_id が input の id と同じ）より広く読める |
| I1-4 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | transcript.py の parse_transcript・subagent_in_flight_from_parsed の docstring が古い判定のまま |
| I1-5 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | human-check-template.md:54 の相談役の TaskStop の出口がエラーだけを挙げている |
| I1-6 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 同じ release に入る未リリースの断片が、成功なら外れるの書き方のまま |
| I1-7 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 成功のケースを抜いたテストの docstring が「成功で返るか」のまま |
| I1-8 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | test_wait_watchdog.py・test_stop_hook_resumed_agent_wait.py の docstring が古い言い方のまま |
| I1-9 | 独立-1 | advisory | no | self-inflicted | resume-inflight | accepted | 成功の経路は input に無い id でも本文の JSON の task_id を外す（host の field を信じる前提） |
| I1-10 | 独立-1 | advisory | no | self-inflicted | resume-inflight | accepted | 成功の本文の JSON は shell_id を読まず、最後の text block だけを読む（待ちに残す側に倒れる） |
| I1-11 | 独立-1 | advisory | no | self-inflicted | bookkeeping | accepted | PR 本文の限界の節の書き方（確かめた結果の行・件数の無い行）。PR 本文で直す |
| I1-12 | 独立-1 | advisory | no | self-inflicted | style | accepted | _TASK_STOP_ERROR_EXIT の名前・record_unaccepted_task_stops の置き場所・JSON の 2 回の parse |
| I1-13 | 独立-1 | advisory | no | self-inflicted | resume-inflight | accepted | lone surrogate や escape される tool_use_id で、記録が Stop のたびに書き直される形がある（hook は落ちない） |
| I1-14 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | PR 本文の、止めた id の無い成功の影響の説明が一部だけ（継続・マージ待ちの押し返し、pre-push の理由）。PR 本文で直す |
