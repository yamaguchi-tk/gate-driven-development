---
lane: L1
pr: 215
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 535d14a069ef327ad9ee50877686df68f2856ab0 | 0 | 0 | 0 | 2026-09-29T00:10+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| F1 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | テストのコメントと断片の Summary が、複製で実行時間の伸びが止まるように読め、PR 本文の限界（本数に比例して伸び続ける）と食い違っていた。両方を「1 本あたりの費用が下がるだけ」に直した（7d501c70）。近道では ① の low は next-pr だが、断片は層 B で後から直せず、この PR で区切る方針なので、ユーザーが迷ったときの判断を委ねた Fable の案でこの PR に取り込んだ。テストと changelog.d だけの commit なので巡は無効にならない |
| F2 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | PR 本文の限界の「review-log-present.sh は base の commit の sha と時刻を読まない」は広すぎた（merge-base の sha は ls-tree の引数に使う）。PR 本文で修正、ファイルは変えない |
