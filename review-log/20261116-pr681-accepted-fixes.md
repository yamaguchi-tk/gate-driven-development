---
lane: L1
pr: 684
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | b66eddbc7d9b286e87709dd10c06089176a6c624 | 0 | 0 | 0 | 2026-11-16 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: fable | 705107900be66ce023ddc8fe2483456d6897b14f | 0 | 0 | 0 | 2026-11-16 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| I1-1 | 独立-1 | low | no | self-inflicted | request-scope | fixed | 3 項目だけで停止の形を定めた箇所が、self-contained-contract § Blocked Response Contract・state-machine § 停止時の返答契約・gdd-dev.md の Worktree Post-Return Validation と系統 A/B の停止に残っていた。commit: 1eca7152 |
| I1-2 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 断片と PR 本文が、3 項目だけの箇所をすべて直したと書いていた。I1-1 を直して記述どおりにした。commit: 1eca7152 |
| I1-3 | 独立-1 | low | no | self-inflicted | approval-path | accepted | risk-low の後に human-recheck を委任で承認すると、evidence が human: に変わり、1 欄目が human-check の行も無いので、記録の場所: なし の行がどこにも書かれない |
| I1-4 | 独立-1 | low | no | self-inflicted | approval-path | accepted | 前の承認ポイントの事前回答の行が残ったまま人間に止めて表示した steering、適用しない（理由）の行、planning_rework の 2 回目で、表示して承認したのに書く |
| I1-5 | 独立-1 | low | no | self-inflicted | approval-path | accepted | Stage Continuation の最後の Stage の done で、どの steering の requirements.md・worklog.md を読むかが決まらず、何も書かれない |
| I1-6 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 断片は compact でも行を落とさないと書くが、compact 側には「落とさない」の文が無い |
| I1-7 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 「表示したときは必ず載る」は文書の規定だけで、表示から落ちたときに届かないことを限界に書いていない |
| I1-8 | 独立-1 | advisory | no | inherited | doc-claim | accepted | gdd-completion-check の手順 7 の done が、記録の場所: なし の行に触れていない |
| I1-9 | 独立-1 | advisory | no | inherited | doc-claim | accepted | TDD の SKILL.md・README・TROUBLESHOOTING・onboarding・evals が、停止時に返すものを 3 項目のままにしている |
| I1-10 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | PR 本文が、full 版の § ズレ確認 に足した「行数の目安を超えても落とさない」を書いていない |
| I2-1 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | gdd-dev.md の Worktree Post-Return Validation と系統 A/B の停止が「Instruction 4 の見出し」と番号で指し、マーカーと順序を書いていない |
| I2-2 | 独立-2 | low | no | self-inflicted | bookkeeping | accepted | 変更断片の Affected Files に references/self-contained-contract.md が無い |
| I2-3 | 独立-2 | low | no | inherited | doc-claim | accepted | onboarding・README・TROUBLESHOOTING が、停止時に返すものを 3 項目のままにしている |
| I2-4 | 独立-2 | advisory | no | inherited | doc-claim | accepted | evals の期待出力が 3 項目のまま（採点の結果は変わらない） |
| I2-5 | 独立-2 | advisory | no | inherited | doc-claim | accepted | TDD の SKILL.md の AC ID の無い RED の fail-closed が、3 項目だけを返すと書く |
