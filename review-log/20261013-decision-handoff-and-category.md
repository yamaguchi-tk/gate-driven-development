---
lane: L1
pr: 474
follow_up_of: 463
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 25fb17f8 | 0 | 2 | 0 | 2026-10-14 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分（無効化後）, model: opus | 05458d20 | 0 | 1 | 0 | 2026-10-14 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| A1 | 独立-1 | medium | no | self-inflicted | product | accepted | Consequences への追記の commit が独立レビューの後に積まれると、sha に結び付いた証跡が古くなり、差分だけの独立レビューが 1 回増える。PR 本文の限界に書く |
| A2 | 独立-1 | low | no | self-inflicted | product | accepted | 確定文面の manifest に載った ADR では、追記で照合が DIFFERENT になる（edits に reason を付けて足せば通る）。PR 本文の限界に書く |
| A3 | 独立-1 | medium | no | self-inflicted | product | fixed | 蒸留されない経路では Issue 参照が別のセッションに届かない（依頼の原文の行）。申し送りのある Decision は Task Size によらず repo ADR へ蒸留し、蒸留の前なら adr.md に書いて運ぶとした。commit: 2244ecc3 |
| A4 | 独立-1 | low | no | self-inflicted | product | accepted | guardrail の文書にだけある Decision には書く先が無い。PR 本文の限界に書く |
| A5 | 独立-1 | low | no | self-inflicted | product | fixed | 参照だけでは満たす要件として読まれない（依頼の原文の行）。Consequences に「実装するときは Issue #N の要件を満たす」と書く形にした。commit: 2244ecc3 |
| A6 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 「この型の severity と category は本項が正本」が、足した列挙の形の category の文を含まないとも読める（実害なし） |
| A7 | 独立-1 | advisory | no | self-inflicted | bookkeeping | accepted | Skill RED-GREEN Evidence が抜粋に無い。PR 本文の末尾の節に書く |
| B1 | 独立-2 | medium | no | self-inflicted | product | accepted | 「Task Size によらず蒸留」が、蒸留の要否を決める post-completion-learning.md・post-completion-pr-flow.md の not_applicable と gate-ledger.sh に入っておらず、quick (express) では申し送りが repo ADR に届かない。PR 本文の限界に書く |
| B2 | 独立-2 | low | no | self-inflicted | product | accepted | 蒸留の義務を pre-PR gate が検査しないことが限界に無い。PR 本文の限界に書く |
| B3 | 独立-2 | low | no | inherited | product | accepted | 「guard・contract test を実装する作業はその Decision を読む」は、GDD の手順で保証されていない。PR 本文の限界に書く |
| B4 | 独立-2 | low | no | inherited | product | re-reported | guardrail の文書にだけある Decision には書く先が無い（A4 と同じ） |
| B5 | 独立-2 | advisory | no | self-inflicted | request-drift | accepted | 依頼の案（ADR の Consequences に Issue 参照を書く）を、Task Size によらない蒸留の義務に広げた。ユーザーに確かめる |
