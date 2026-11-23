---
lane: L1
pr: 673
amends: 20261113-accepted-leftovers-batch.md
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 51b30a711d3053efdae717f5fdeb241723e8e3fd | 0 | 0 | 0 | 2026-11-13 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: fable | cf72af5f8ba09103a558f44edb083b94adaf255d | 0 | 0 | 0 | 2026-11-13 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| I1-1 | 独立-1 | low | no | inherited | doc-claim | fixed | state-machine.md の stop の reason が 7 種類のまま。output-format.md の許容値を指す形にした。commit: 34f6e833 |
| I1-2 | 独立-1 | low | no | self-inflicted | test-power | fixed | 再開した agent のテストが、JSON の id を input と照らさない退行を検出しない。別の再開した agent を指す形を足した。commit: 34f6e833 |
| I1-3 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | brainstorming の見直しの引用の除外が、hook の節がある形にしか掛からない。形によらない文にした。commit: 34f6e833 |
| I1-4 | 独立-1 | low | no | self-inflicted | request-scope | accepted | PR 671 の断片の 3 か所の書き換えが依頼の A-1 の外か。元の指摘 I2-6（:11 の語、express の書き直し）と I1-11（faq の書き先）に含まれると照らした |
| I1-5 | 独立-1 | low | no | inherited | request-scope | accepted | planning reviewer と completion reviewer で、ユーザーの決定の記録の範囲が違う |
| I1-6 | 独立-1 | advisory | no | self-inflicted | doc-claim | fixed | 記録の場所の種類が「など」で開き、基準 0 の global の規則・前のタスクの承認の扱いが無い。commit: 34f6e833 |
| I1-7 | 独立-1 | advisory | no | inherited | doc-claim | fixed | human-check-template.md の原文の引き方が、見直しの引用を除いていない。commit: 34f6e833 |
| I1-8 | 独立-1 | advisory | no | self-inflicted | bookkeeping | fixed | 断片の Affected Files に、amends で直した断片が無い。commit: 34f6e833 |
| I2-1 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 断片と PR 本文の「state-machine.md は値を並べず」が、§ Autonomous Continuation だけの話で、:54・:57 には列挙が残る |
| I2-2 | 独立-2 | low | no | self-inflicted | request-scope | accepted | 記録の場所に数えない決定に「ユーザーに聞く」と書いたが、未収束の後に聞く経路が無い |
| I2-3 | 独立-2 | low | no | inherited | request-scope | accepted | 記録の場所の CLAUDE.md・AGENTS.md の行が、着手前からある行に限られていない |
| I2-4 | 独立-2 | low | no | inherited | doc-claim | accepted | human-check-template.md の原文の引き方が、hook の節の下に足したユーザーの発言を含まない |
| I2-5 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | repo のほかの規則のファイル（.claude/rules など）が記録の場所の除く例に無い |
