---
lane: L1
pr: 661
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 8b6e2a417fbc854ddcc6e61657b8086e4ba2ed1f | 0 | 3 | 0 | 2026-11-13 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: fable | 924e632dd5f9a55d7024529d3f0b9109ceda7be5 | 0 | 0 | 0 | 2026-11-13 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| I1-1 | 独立-1 | medium | no | self-inflicted | request-scope | fixed | 設計: 変える（例外を足さず、依頼どおり原文の側に倒すだけにする）。原文どおりにできないときに延期・削除へ回す例外を外し、Step 4c は狭めた仮決定をそのまま blocking にした。commit: 4e032d3b |
| I1-2 | 独立-1 | medium | no | self-inflicted | reviewer-input | fixed | I1-1 で延期・削除の行を判定に使わなくなり、変換表を reviewer に渡す必要が無くなった。commit: 4e032d3b |
| I1-3 | 独立-1 | medium | no | self-inflicted | doc-claim | fixed | 見直しのきっかけになった行が消えることを直したという主張を PR 本文から外した。commit: なし（PR 本文） |
| I1-4 | 独立-1 | low | no | self-inflicted | lockin-routing | accepted | 答えから足した行の印・足し直す行の番号・写しの再上書きが決まっていない |
| I1-5 | 独立-1 | low | no | self-inflicted | lockin-routing | accepted | 起動後の失敗や見出しの欠けた出力は上書きされ、unavailable の理由も残らない |
| I1-6 | 独立-1 | low | no | self-inflicted | request-scope | accepted | 既存側がユーザーの決めた方針（基準 0）のときの扱いが無い |
| I1-7 | 独立-1 | low | no | self-inflicted | reviewer-input | accepted | planning reviewer の観点の起動条件が、原文だけでは決まらない行のあるときのまま |
| I1-8 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 写す時機を差分どおり上書きの前に揃えた。commit: なし（PR 本文） |
| I1-9 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 件数を 0 件・ユーザーの指示で足すと書いた。commit: なし（PR 本文） |
| I1-10 | 独立-1 | advisory | no | self-inflicted | risk-tier | accepted | 見直しが unavailable のとき、リスクの段が返事の前の判定のまま残る |
| I2-1 | 独立-2 | low | no | self-inflicted | request-scope | fixed | 原文どおりにできない既存とぶつかる行は行き先の規定が無く、Step 4c の blocking を経て人に届くことを PR 本文の限界に書いた。commit: なし（PR 本文） |
| I2-2 | 独立-2 | low | no | inherited | reviewer-input | re-reported | I1-7 の再掲（planning reviewer の観点の起動条件） |
