---
lane: L1+
pr: 631
amends: 20261028-design-gating-off-default.md, 20261029-task-breakdown-into-stage1.md, 20261029-express-planning-review.md
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ | Opus 設計レビュー ×2 (gdd-opus-advisor, model: opus) + user | - | 0 | 0 | 0 | 2026-11-02 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | c6df96ff69ad0e166168f2436894b8d190f50052 | 0 | 1 | 0 | 2026-11-02 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| M1-1 | 方針メモ | advisory | no | self-inflicted | same-rule-elsewhere | fixed | 2 本とも、reviewer-selection.md:151 の末尾の「飛ばせる」の 1 文は 旧#607 が足したもので、外さないと AC-1 と AC-2 が食い違うと指摘した。末尾の 1 文だけを 旧#607 の前の文に戻した。commit: なし（この PR の最初の commit） |
| M1-2 | 方針メモ | advisory | no | self-inflicted | doc-claim | fixed | 2 本とも、未リリースの断片 3 本（旧#607・旧#610・旧#615）を amends: で書き換え、新しい断片の type を patch にするよう推した（Fable も同じ）。草案の「書き換えない」をやめた。commit: なし（この PR の最初の commit） |
| M1-3 | 方針メモ | advisory | no | self-inflicted | same-rule-elsewhere | fixed | 2 本目は、grep の語を含まない代わりの文（requirements-gating Step 5 の括弧・:39 の tasklist.md・state-machine.md の Next Action の注記・token の上限の注記）の消し漏れを挙げた。戻し、言い換えの語を拾う grep を足した。commit: なし（この PR の最初の commit） |
| M1-4 | 方針メモ | advisory | no | self-inflicted | test-power | fixed | 2 本目は、notes.md に Skill RED-GREEN Evidence と、安全策 2 の fail-open のテストを書かない理由を書くよう求めた。commit: なし（この PR の最初の commit） |
| r1-1 | 独立-1 | medium | no | self-inflicted | migration | accepted | 旧#610 の期間に brainstorming が書いた tasklist.md の下書きが進行中の steering に残ると、design-gating の planning reviewer のタスク分解の質チェックがその下書きに当たり、task-breakdown Step 2 には下書きを作り直す規定が無い（task-breakdown-steps.md:10、gdd-planning-reviewer.md:294）。該当は 11/02 時点で 1 件。PR 本文の限界に、Tasklist Basis の行がある tasklist.md は design-gating の前に消すと書いた |
| r1-2 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 新しい断片の User Action Required が残る token として design-lens-reviewing: だけを挙げ、design-lens: の形を挙げていない（20261102-remove-design-gate-skip.md:19）。PR 本文には 2 つの形を書いた |
| r1-3 | 独立-1 | low | no | inherited | doc-claim | accepted | 戻した phase-progression.md:198 の「design-gating の最終 step で External Guardrails Inventory を生成する」に当たる step が gdd-design-gating/SKILL.md に無い（旧#607 の前と同じ状態） |
| r1-4 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 書き直した 20261028-design-gating-off-default.md の Summary は、dialectic-review.md:30 の規定（requirements-gating の planning reviewer の出力で起動）より狭く、design の観点の組を起動したときに限って書いている |
| r1-5 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 戻した reviewer-selection.md:151 の括弧の 1 文目に主語が無く、design-gating が requirements の時点の design.md を見るとも読める |
| r1-6 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | token の上限を 45497 に戻した根拠の実測値が PR 本文に無い。PR 本文の確認したことに standard の実測 44512 を書いた |
| r1-7 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | requirements-gating Step 5 の行数の削減を Step 4 の前に済ませる順序を 旧#607 の前の形に戻したことが、PR 本文の挙動の変化に無い。PR 本文に書いた |
| r1-8 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | PR 本文が 9 件から 8 件に絞った理由を書いていない。PR 本文に書いた |
| r1-9 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 5a・5b・5d と External Guardrails Inventory を design-gating 側に戻した理由が PR 本文に無い。PR 本文に書いた |
| r1-10 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 20261029-task-breakdown-into-stage1.md の Summary が経緯（同じ版の別の断片で外した）を書き、リリースで断片が消えると指す先を失う |
