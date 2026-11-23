---
lane: L1
pr: 396
follow_up_of: 391
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 4c6b8f5b | 0 | 1 | 0 | 2026-10-07T10:01+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| F1 | 独立-1 | medium | no | self-inflicted | 範囲の定義 | accepted | 食い違いを指摘した blocking の片側だけを直したとき、もう片側が範囲の外なので、再入で解消を確かめられない |
| F2 | 独立-1 | low | no | self-inflicted | 範囲の定義 | accepted | security reviewer の「差分と影響範囲」と、契約 3 の「処置箇所と変えた節」が食い違う |
| F3 | 独立-1 | low | no | self-inflicted | 文言 | fixed | 限界の「advisory の反映か human check で拾う」が design には当たらない。commit: なし（PR 本文） |
| F4 | 独立-1 | low | no | self-inflicted | 文言 | fixed | 目的の A/B の比較の相手と出典が無い。commit: なし（PR 本文） |
| F5 | 独立-1 | low | no | self-inflicted | 文言 | fixed | Skill RED-GREEN Evidence が無い。commit: なし（PR 本文） |
| F6 | 独立-1 | low | no | self-inflicted | 計測 | accepted | 範囲を広げる変更の A/B に、変えていない節へ食い違いを仕込んだ入力が要らず、常に狭い側が勝つ |
| F7 | 独立-1 | advisory | no | self-inflicted | 文言 | accepted | A/B の条件は開発の手順で、gate が読む reference と断片に入っている |
| F8 | 独立-1 | advisory | no | self-inflicted | 文言 | accepted | 未リリースの断片 2 本が、外した影響節を足したと書いたまま残る。リリースの dry-run でまとめる |
