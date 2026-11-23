---
lane: L1
pr: 394
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | b082c4be | 0 | 0 | 0 | 2026-10-07T00:00+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| F1 | 独立-1 | medium | no | self-inflicted | route の順序 | next-pr | systematic-debugging の Decision Tree 1 から、承認後の 2/2・同一 root cause 3 回連続の句も消え、TDD の問いが先に来て phase-progression の判定テーブルと順序が食い違う |
| F2 | 独立-1 | low | no | self-inflicted | 参照元 | next-pr | autonomy.md の参照元から state-machine.md を丸ごと外したが、§ Stop hook の判定順序 rule 2 が今も autonomy.md を参照している |
| F3 | 独立-1 | low | no | inherited | 参照元 | next-pr | autonomy.md の参照元に post-merge-qa.md と gate-status-schema.md が前から無い |
| F4 | 独立-1 | advisory | no | self-inflicted | 文言 | accepted | subagent-dispatch.md:35 の phase 名の例から implementation_gating.md の項目ごと消えた |
| F5 | 独立-1 | low | no | self-inflicted | 断片 | next-pr | 断片の「取り除いたもの」に、Post-Return Routing の判断役の起動、Decision Tree 1・Steps 5、Step 1・1d・8a の ## Round の参照が無い |
| F6 | 独立-1 | advisory | no | self-inflicted | 断片 | accepted | 「一度も発火していない」の測り方（条件に当たった回か、起動した回か）と期間が無い |
| F7 | 独立-1 | advisory | no | self-inflicted | 断片 | accepted | skill 本文を変えたのに Skill RED-GREEN Evidence が断片の Validation に無い（PR 本文に書く） |
| F8 | 独立-1 | advisory | no | self-inflicted | 文言 | accepted | 限界の節に、早期の方式判断を足した未リリースの断片 6 本の名前と、版の節に残る記述が無い |
