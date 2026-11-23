---
lane: L1
pr: 382
follow_up_of: 379
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | e4f9bb15e691ff756dc628a22ec8e322018b925d | 0 | 3 | 0 | 2026-10-06T12:00+09:00 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | d4b93e6ef6b1eefb717fd071bddf369b8bb39a98 | 0 | 0 | 0 | 2026-10-06T12:40+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| M1 | 独立-1 | medium | no | self-inflicted | product | fixed | Template の `## Round <Gate Rounds>` が呼び出し側の欄に見え、gate 前の値で埋めると判断が一度も行われない。番号は gate が決めると書いた（規定外で直した） commit: 481b0f1 |
| M2 | 独立-1 | medium | no | self-inflicted | product | fixed | 前の task の `## Round 1` が残り、先頭の節で数えうる。最後に足した節で数えるとした（規定外で直した） commit: 481b0f1 |
| M3 | 独立-1 | medium | no | self-inflicted | product | accepted | 事前回答の「人に戻す条件」の閉じた一覧に早期の方式判断の停止が無く、委任先に聞き直しうる |
| L1 | 独立-1 | low | no | self-inflicted | product | accepted | rollback-patterns の新しい文が `自律判断: human-recheck / 採った案: 人間に止める` の行を書くことに触れていない |
| L2 | 独立-1 | low | no | self-inflicted | product | accepted | Step 1・1d・8a の本文が handoff の節を書くことを指していない（Step 9 の中にだけ書いた） |
| L3 | 独立-1 | low | no | self-inflicted | product | accepted | 判断役を起動できないときを止まる場面から除いていない。worklog の行に「読めない」の値が無い |
| A1 | 独立-1 | advisory | no | self-inflicted | doc-claim | fixed | 断片の「state-machine.md にしか無く」が言い過ぎ。参照元の行を足した commit: 481b0f1 |
| A2 | 独立-1 | advisory | no | self-inflicted | doc-claim | fixed | PR 本文に番号の決め方と節を消さないことが無い commit: なし（PR 本文） |
| L4 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | 断片の Affected Files に state-machine.md が無い commit: 0fc027c |
| A3 | 独立-2 | advisory | no | self-inflicted | doc-claim | fixed | 断片の番号の説明に、足さなかったときの値が無い commit: 0fc027c |
| A4 | 独立-2 | advisory | no | inherited | doc-claim | accepted | 前の未リリースの断片の「`## Round 1` の節」が粗い。リリースで版の節をまとめる |
