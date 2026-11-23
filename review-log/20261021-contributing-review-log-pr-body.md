---
lane: L1
pr: 557
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | b46e4f7f | 0 | 1 | 0 | 2026-10-21 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | c2174789 | 0 | 0 | 0 | 2026-10-21 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| F1 | 独立-1 | medium | no | self-inflicted | doc-claim | fixed | CONTRIBUTING.md:136 の 2 文目「PR 本文に書くのは、マージの後も残る限界とまだ決まっていないことだけ」が、手順 7 で限界の節にだけかかる「だけ」を PR 本文全体にかけ、レビュー結果の行と「次の PR:」を外すと読める。ユーザーの指示で取り込み、2 文目を消した。commit: c2174789 |
| F2 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | CONTRIBUTING.md:136 の主語が「受け入れた限界」のままで、手順 7 の語「受け入れた medium・low と advisory」でない。CLAUDE.md:160 の「受け入れた限界は PR 本文に書く」とぶつかる。ユーザーの指示で取り込み、主語を受け入れた指摘（medium・low と advisory）にした。commit: c2174789 |
| F3 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | CONTRIBUTING から root CLAUDE.md を指す最初の参照を足した。changelog.d/20260920-contributing-full-suite-in-ci.md:32 の「CONTRIBUTING からは root CLAUDE.md を指さない」と食い違う。ユーザーの指示で取り込み、2 文目を消して root CLAUDE.md への参照をなくした。commit: c2174789 |
| F4 | 独立-1 | low | no | self-inflicted | product | accepted | 依頼は CONTRIBUTING.md 1d だけだが、正本の CHANGELOG.md § Policy の同じ文言も直して範囲を広げた。ユーザーが残すと答えた |
| F5 | 独立-1 | advisory | no | self-inflicted | style | accepted | 断片の節名が Changed で、Entry Template では Fixed（不整合の修正）に当たる |
| F6 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 断片の「利用者から見える変更なし」が、配布物の CHANGELOG.md § Policy の文言が変わることと言い方の上で食い違う |
| F7 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | CHANGELOG.md:20 の § Policy の主語が「受け入れた限界」のままで、1d の「受け入れた指摘（medium・low と advisory）」と食い違う |
| F8 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | PR 本文の「PR 本文に何を書くかは CHANGELOG.md § Policy に任せる」が、1d の文面（正本と呼ぶ範囲は断片の内容・書式）より強い |
| F9 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | 断片の Summary の括弧が「マージの後も残る限界」で、手順 7 の語「不利益」とずれている |
