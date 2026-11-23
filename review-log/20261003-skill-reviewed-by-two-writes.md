---
lane: L1
pr: 339
follow_up_of: 315
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 09ed6d89 | 0 | 1 | 0 | 2026-10-03T07:30+09:00 |
| 独立-2 | light-lane-independent-reviewer, 差分, model: opus | 0966ac74 | 0 | 0 | 0 | 2026-10-03T08:00+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| F1 | 独立-1 | medium | no | self-inflicted | 手順と guard | fixed | 2 回の書き込みを route の枝に書いたが、route は task-breakdown の前に none へ戻るので入らない。この PR の目的（旧#315 の G6）が達成されないので、ユーザーの依頼の範囲として近道でも直した。route を問わない手順 2 の冒頭へ移した。commit: 0966ac74 |
| F2 | 独立-1 | medium | no | inherited | 手順と guard | next-pr | route で分ける作り直しの枝にどの route でも入らない（design_detail_only の部分リセットが選ばれない）。route のクリアの時機の問題 |
| F3 | 独立-1 | low | no | self-inflicted | 文言 | fixed | state-machine.md のリセットの規定が 2 回の書き込みに追随していない。commit: 0966ac74 |
| F4 | 独立-1 | low | no | self-inflicted | 文言 | fixed | 「pending に戻さない」の直後に「Pending Tasks へ移す」が来て矛盾して読める。commit: 0966ac74 |
| F5 | 独立-1 | low | no | inherited | 手順と guard | next-pr | phase-progression.md の並列 batch の「cleanup task に降格」も、1 回の書き込みで完了タスクを外すと guard に止められる |
| F6 | 独立-1 | advisory | no | self-inflicted | 文言 | accepted | 変更断片の「今まで…止めていた」は、まだリリースしていない guard を指している |
| F7 | 独立-1 | advisory | no | self-inflicted | 手順と guard | accepted | refactor の abort で 2 回の書き込みの間に止まると、abort したタスクが Pending に残る |
| G1 | 独立-2 | low | no | self-inflicted | 文言 | accepted | 手順 2 の冒頭の「route は task-breakdown の前に none へ戻る」が、同じ手順 2 の route ごとの枝と食い違う全称の断定 |
| G2 | 独立-2 | medium | no | inherited | 手順と guard | re-reported | design_detail_only の部分リセットが route では選べない（F2 の再掲） |
| G3 | 独立-2 | low | no | inherited | 手順と guard | accepted | state-machine.md:688・rollback-patterns.md:77・phase-progression.md:271・state-machine.md:398 も、完了タスクを 1 回の書き込みで消す・分け直す手順のまま |
| G4 | 独立-2 | low | no | inherited | 文言 | accepted | 「Tasklist Reset Policy」という参照先の節が無く、state-machine.md の注記に辿り着けない |
| G5 | 独立-2 | low | no | self-inflicted | 文言 | fixed | PR 本文の限界「手順 2 にだけある」が、state-machine.md の注記と合わない。commit: なし（PR 本文） |
| G6 | 独立-2 | advisory | no | self-inflicted | 手順と guard | accepted | SKILL.md だけを読む task-breakdown の subagent には 2 回の書き込みが届かず、最初の 1 回の deny が残りうる |
