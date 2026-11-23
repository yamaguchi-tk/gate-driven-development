---
lane: L1
pr: 旧#251
follow_up_of: 248
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 4d960810acb7a91b7ca65efa1ebf54acf449b557 | 0 | 2 | 0 | 2026-09-30T12:50+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| F1 | 独立-1 | medium | no | self-inflicted | wiring | accepted | 8a が finding つきで発火したとき、systematic-debugging の Decision Tree Step 1・8 が「同一 Current Task」のままで、ADR ≥2 の task が finding の対象でないと方式転換に届かない |
| F2 | 独立-1 | medium | no | self-inflicted | wiring | accepted | task ごとに数えると決めたが、worklog の Error Log に task の列が無く、root cause の連続と Attempt を task ごとに突き合わせられない |
| F3 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | gdd-test-driven-development:250 の「差し戻し後は finding の対象の task」が、finding 無しの 8a の後で空になり、手順 2b と揃っていない |
| F4 | 独立-1 | low | no | self-inflicted | product | accepted | 対象の task が複数のとき、ADR の Origin の書き方（並べるか、task ごとに entry を分けるか）と数え方が決まらない |
| F5 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | remediation / <Current Task> を書かせる箇所が subagent-driven-implementation:109・design-gating:125,132・adr-vs-design.md:59 にもあり、限界の節は debugging の行しか挙げていない |
| F6 | 独立-1 | low | no | self-inflicted | product | accepted | human_recheck_required の後の reset（0 に戻し分母を 2）が、Gate Batch では発火した task だけか全 task かが書かれていない |
| F7 | 独立-1 | low | no | self-inflicted | product | accepted | Remediation Loop Safety の「changes_requested が 2 回連続なら worklog に書く」が task ごとに数える一覧から外れていて、読みが割れる |
| F8 | 独立-1 | low | no | inherited | product | accepted | Architecture Gate（同じ route で 3 回連続）を Gate Batch で task ごとに数えるか batch で数えるかが決まらない |
| F9 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 「reviewer status は gate 全体で 1 つ」は、reviewer ごとに持つ schema の正本と合わない |
| F10 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | task-breakdown-steps の「全 task を差し戻し」が、Execution Status を全 task で戻すとも読め、「in_progress に戻すのは対象だけ」と読みが割れる |
| F11 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | impl-gating Step 9 の閾値表と phase-progression の Fix Attempts の行が「同一 Current Task」のままで、断片の「task ごとに数えると揃えた」と合わない |
| F12 | 独立-1 | low | no | inherited | doc-claim | accepted | reviewer-selection.md:108 と state-machine.md:212 の selection 変更の規定が「同じ Current Task」のまま |
| F13 | 独立-1 | low | no | inherited | product | accepted | terraform checklist の「current task」に、security reviewer と同じ Gate Batch の読み（batch のどれかの task）が無い |
| F14 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 断片の Validation に検証の結果を書いている（§ Policy では種類だけ）。5 つの状況に 8a が finding つきで発火する場合が入っていない |
| F15 | 独立-1 | advisory | no | self-inflicted | bookkeeping | accepted | type: patch で契約レベルの self-contained-contract.md を変えている（旧#248 の断片が minor なので版数は変わらない） |
| F16 | 独立-1 | advisory | no | inherited | product | accepted | telemetry は tasklist.md の最初の Fix Attempts だけを読む |
| F17 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | task ごとに数えると、3 task の batch で finding が毎回別の task に出れば 5/5 まで 12 巡でき、1 つの gate 単位としては上限が緩くなる |
