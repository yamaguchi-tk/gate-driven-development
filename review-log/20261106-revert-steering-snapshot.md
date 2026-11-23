---
lane: L1
pr: 639
amends: 20261106-steering-snapshot-at-gate-dispatch.md
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 92a50cf344ad4895559b1f0512857a482c7763fc | 1 | 0 | 0 | 2026-11-06 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | f1b6f52ccce3983e2cc3cb04629edd1567ddf26e | 0 | 0 | 0 | 2026-11-06 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| I1-1 | 独立-1 | high | no | self-inflicted | fragment-removal | fixed | 設計: 変えない（version-not-consumed.sh が既に持つ amends: の経路に合わせる）。旧#638 の断片を消したので version-not-consumed.sh の層 B が FAIL する。断片を同じパスに戻し、amends: で中身を「利用者から見える変更なし」に書き換えた。commit: f1b6f52c |
| I1-2 | 独立-1 | low | no | self-inflicted | session-reload | accepted | 旧#638 の後に開いて動いているセッションは、この PR の pull の後も消したスクリプトを起動しようとして hook のエラーが出るが、断片に開き直す案内が無い |
| I1-3 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | PR 本文の「保存は 1 件も無い」「cache 読みの単価が同じ」に、確かめたコマンドや出典が無い |
| I2-1 | 独立-2 | low | no | self-inflicted | fragment-type | accepted | 書き換えた 旧#638 の断片が「利用者から見える変更なし」なのに type: minor のままで、版を MINOR に上げる側に入る |
| I2-2 | 独立-2 | low | no | self-inflicted | doc-copy | accepted | 取り下げの断片の Affected Files に、amends: で書き換えた 旧#638 の断片が無い |
| I2-3 | 独立-2 | low | no | self-inflicted | doc-copy | accepted | 2 つの断片の Affected Files が食い違う（片方は「なし」、片方は同じ版で足して消したファイルの削除を挙げる） |
| I2-4 | 独立-2 | advisory | no | self-inflicted | bookkeeping | accepted | amends: の宣言が push する tip に commit されていないと version-not-consumed が落ちる |
