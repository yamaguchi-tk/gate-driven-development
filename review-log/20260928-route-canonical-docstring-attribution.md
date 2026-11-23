---
lane: L1
pr: 旧#209
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 17c5b8c011432da769ad14e08d27f056d2e527c1 | 0 | 0 | 0 | 2026-09-28T21:45+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| L1 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | PR 本文の抜粋の「今の `tasklist_parse.route_value` を前身として併記する」が、差分と前身の向きが逆。PR 本文だけを直した（差分は変えていない） |
| A1 | 独立-1 | advisory | no | inherited | release-fragment-overlap | accepted | 未リリースの断片 `20260928-split-test-docstring-followups.md` が「読み取りの関数は `tasklist_parse.route_value`」と書き、この PR の断片（帰属を `_route_value` に戻す）と同じ版の節で並ぶ。既存の断片は書き換えられないので、次のリリースの dry-run で版の節をまとめる |
