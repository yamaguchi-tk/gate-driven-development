---
lane: L1
pr: 434
follow_up_of: 428
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 8a607d61 | 0 | 1 | 0 | 2026-10-12 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| F1-M1 | 独立-1 | medium | no | self-inflicted | product | accepted | 3 つ以上に分かれる AC で、止める枝どうしが接する境目（保留と拒否の間など）がどの行にも入らない。PR 本文の限界に書いた |
| F1-L1 | 独立-1 | low | no | self-inflicted | product | accepted | AC が止める側を定めていないと、止める側の行が not_applicable で閉じ、planning / design へ戻す規定が無い。PR 本文の限界に書いた |
| F1-L2 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 「2 行」と、枝ごとに増える止める側の行が合わない。PR 本文の限界に書いた |
| F1-L3 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 対照の語を書く行が、規定の行と語彙の行で食い違う。PR 本文の限界に書いた |
| F1-L4 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 「上の行に加えて」が、一覧の途中にあるので下の観点を含まない。PR 本文の限界に書いた |
| F1-L5 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | PR 本文の限界の「success path に書く」が skill に無い。PR 本文を「書く行は skill では決めていない」に直した。commit: なし（PR 本文） |
| F1-L6 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 次の版の節に 旧#428 の断片の旧い規定が並ぶ。PR 本文の限界に書いた |
| F1-A1 | 独立-1 | advisory | no | self-inflicted | bookkeeping | fixed | Superpowers Benchmark Summary と Skill RED-GREEN Evidence が抜粋に見えない。PR 本文に書いた。commit: なし（PR 本文） |
| F1-A2 | 独立-1 | advisory | no | self-inflicted | bookkeeping | accepted | skill 本文の合計行数の余裕が 0 になる |
| F1-A3 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 効いたかの数え方が、根拠の数の分け方と合っていない |
