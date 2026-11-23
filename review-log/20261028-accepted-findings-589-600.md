---
lane: L1
pr: 604
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | acd553064a7d2432405af222059e0691f78ba5a9 | 0 | 0 | 0 | 2026-10-28T21:40+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| r1-1 | 独立-1 | advisory | no | inherited | same-rule-elsewhere | accepted | 規定は「merge 後」の箇条の中にあり、PR 状態を確かめられないときの「Next Action が done だが追跡先なし」（:74）の補完候補には掛からない |
| r1-2 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | PR 本文の限界が、ユーザーが推奨の 5 件で決めた範囲を、決めたことを書かずに「依頼より狭い」とだけ書いていた |
| r1-3 | 独立-1 | advisory | no | self-inflicted | test-power | accepted | --root の側のテストは、stderr を部分一致で見ている |
