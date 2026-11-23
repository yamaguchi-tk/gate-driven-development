---
lane: L1
pr: 旧#183
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | general-purpose, 全差分, model: opus, effort 継承 | 2027776a49c564eec982077f532cfa75d801ecbb | 0 | 0 | 0 | 2026-09-24T19:49+09:00 |
| 独立-2 | light-lane-independent-reviewer, 差分（無効化後）, model: opus | 22ff3d8a12cc1bb2d62170fb6fada9cfb8849f47 | 0 | 0 | 0 | 2026-09-28T11:46+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| G1 | 独立-1 | low | no | self-inflicted | split-doc-pointer | fixed | PR 本文の草案が、元のファイルに残る class を「9 class」と書いていたが、実際は 8 個（merge-base の 15 個から 7 個を移した）。直す先は PR 本文だけなので、push 時に書く PR 本文で「8 class」に直した。コードと規則の文書は変えないので、巡は無効にならない |
| G2 | 独立-2 | low | no | inherited | model-names-fragment-stale | next-pr | main から取り込んだ未リリースの断片 3 本（20260923-model-names-without-version・20260924-model-names-followup・20260924-model-names-shrink-contract）が、Cursor の Counter の選び方と「版は 2 行だけを直す」規定について、同じ版の節で食い違う指示を並べる。他の PR の断片は通常の PR では書き換えられないため、次のリリースの release.py dry-run で版の節を直す |
| G3 | 独立-2 | low | no | inherited | pr-body-limit-vs-template | next-pr | main から取り込んだ root CLAUDE.md:53 と agent 定義:18 は PR 本文に前の巡の指摘とその対応を書かないと定める一方、CLAUDE.md:81・:93・:172・:173 は直していない high・blocking を限界の節に書かせるので、規定どおりの限界が巡ごとにテンプレート外の advisory として報告されうる。この PR の直後に、両者を調停する 1 文を足す次の PR を出す |
