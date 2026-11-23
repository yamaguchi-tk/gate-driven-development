---
lane: L1
pr: 574
amends: 20261022-review-finding-dispositions.md, 20261023-finding-dispositions-followup.md
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | f60a021ca155e8b935bd0e0ced1c79584bd4511e | 0 | 0 | 0 | 2026-10-24T01:30+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| r1-1 | 独立-1 | low | no | inherited | changelog | accepted | 旧#568 の断片の Step 8 の行が、検査を回す時点を「判定を決めたら」と書いたまま |
| r1-2 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | refuted の行の再報告で人に戻す条件が全 severity に広がり、「(3-a) により全差分」が medium・low では成り立たない |
| r1-3 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 人に戻す手順が Route In Progress の 1 欄だけで、rollback-patterns.md の組（Next Action など）を指していない |
| r1-4 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 前の節を直してよい場合を「形・番号の誤り」に絞ったが、検査は値域・行き先・absent@ の誤りも前の節に出す。断片とも食い違う |
| r1-5 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | Step 8 の括弧の「同書」が指す先が無く、absent@ が 3 つの行き先すべてに使えると読める |
| r1-6 | 独立-1 | low | no | self-inflicted | changelog | accepted | 旧#568 の断片の書き換えた行が、absent@ の行でも検証役を起動すると読める |
| r1-7 | 独立-1 | low | no | inherited | doc-claim | accepted | absent@ の条件を「merge-base にも tip にも無い」と狭く書く箇所が述語のコメントとテストの docstring に残る |
| r1-8 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | path の文字の規定が、CLI が欄を NFC にそろえてから読むことと、行-数字・片側のバッククォートも受けることを書いていない |
| r1-9 | 独立-1 | low | no | self-inflicted | changelog | accepted | 新しい断片が、amends で書き換えた 2 つの断片と、検証役の起動の条件・CLI のエラー文の変更を書いていない |
| r1-10 | 独立-1 | low | no | self-inflicted | bookkeeping | fixed | skill 本文・agent の prompt を変えたが Skill RED-GREEN Evidence の notes が無い。notes を足した。commit: なし（review-log） |
| r1-11 | 独立-1 | advisory | no | self-inflicted | pr-body | accepted | テンプレート外の記述あり（PR 本文の抜粋に、他の PR の指摘の ID とその対応、テストを確かめ済みとする文があった） |
| r1-12 | 独立-1 | advisory | no | self-inflicted | pr-body | accepted | 機械の検査の穴 14 件を直す PR が抜粋に書かれていない |
| r1-13 | 独立-1 | advisory | no | inherited | doc-claim | accepted | README の agents 一覧に gdd-code-simplifier が無い |
| r1-14 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | subagent-dispatch.md の warn は model だけを見ることを書いていない |
| r1-15 | 独立-1 | advisory | no | self-inflicted | style | accepted | CLI のエラー文の「tip」と「未 commit の file」が実際の分類と少しずれる |
| r1-16 | 独立-1 | advisory | no | inherited | product | accepted | ledger と CLI の text is None の分岐には競合のときしか着かない |
| r1-17 | 独立-1 | advisory | no | self-inflicted | test | accepted | 足したテストの後片付けが subTest の assert の後ろにある |
| r1-18 | 独立-1 | advisory | no | self-inflicted | changelog | accepted | 2 つの未リリースの断片が absent@ の許可を両方に書いている |
