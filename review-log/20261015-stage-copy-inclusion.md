---
lane: L1
pr: 524
follow_up_of: 521
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 37774b48 | 0 | 0 | 0 | 2026-10-15 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| A1 | 独立-1 | low | no | self-inflicted | product | accepted | 行の値か元の値が表の値でない（注記付き・読めない）とき、`PR 作成まで` が写り、元が `実装完了まで` だとそれより上になる（変更前から） |
| A2 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 断片の Summary が、対象の限定（原文が自走上限に触れていない行）を落とし、直した不具合を「下げた値より上」と書いている |
| A3 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | PR 本文の限界の「ほとんど無い」に件数もコマンドも無い。「未測」と、記録に残らない入力を書いた。commit: なし（PR 本文） |
| A4 | 独立-1 | advisory | no | self-inflicted | bookkeeping | fixed | Skill RED-GREEN Evidence を PR 本文に書いた。commit: なし（PR 本文） |
| A5 | 独立-1 | advisory | no | self-inflicted | bookkeeping | fixed | 全差分巡の base は 旧#521 の先端（0ca83f28）で、この PR は 旧#521 を base にした stacked PR である。PR 本文に書いた。commit: なし（PR 本文） |
