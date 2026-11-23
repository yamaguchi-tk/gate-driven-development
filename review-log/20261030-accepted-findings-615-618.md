---
lane: L1
pr: 623
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | a0b64525 | 0 | 3 | 0 | 2026-10-30 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| F1-1 | 独立-1 | medium | no | self-inflicted | 再入 | accepted | human check の一部変更からの再入を契約 3 の再入と同じにしたが、前回 Round が approved だと lint --entry requirements-reentry が「処置が無い」で ERROR になり、契約 3 と reviewer 定義の再入の定義とも外れる。Round 上限に当たったときの扱いも未定 |
| F1-2 | 独立-1 | medium | no | self-inflicted | security | accepted | express の要件レビューで起動する security reviewer に、agent 定義の Phase Context・1 枚の種類・Record Format の定義が無い |
| F1-3 | 独立-1 | medium | no | self-inflicted | ファイル数 | accepted | 昇格条件を実装コードで数えるようにしたが、同じ条件を写した state-machine.md:362・faq.md:195 が「変更ファイル 3+」のまま |
| F1-4 | 独立-1 | low | no | inherited | ファイル数 | accepted | task-sizing.md:261 の Scope Breadth が変更ファイルで数え、brainstorming-steps.md:100 が無い Step 7a-4 を指す |
| F1-5 | 独立-1 | low | no | self-inflicted | ファイル数 | accepted | テンプレートの Files の欄に skill 設定が無く、:5・:29 の限定が無い |
| F1-6 | 独立-1 | low | no | self-inflicted | 机上追跡 | accepted | gdd-planning-reviewer.md:358 に「design phase 専用の」が残る |
| F1-7 | 独立-1 | low | no | self-inflicted | 説明 | accepted | skill-body-budget.sh:359-360 のコメントが上限を X-53 のときの値と書いたまま |
| F1-8 | 独立-1 | low | no | inherited | 説明 | accepted | worked-examples.md:128 の express の流れに要件レビューが無い |
| F1-9 | 独立-1 | low | no | self-inflicted | 再入 | accepted | express で AC が変わったときの行き先が gdd-dev.md（brainstorming に戻す）と requirements-gating-steps.md:76・:123（再入）で違う |
| F1-10 | 独立-1 | low | no | inherited | 再入 | accepted | express の「実装方針変更」の返答が、express に無い design-gating へ送られる（gdd-dev.md:190） |
| F1-11 | 独立-1 | low | no | self-inflicted | 説明 | fixed | PR 本文の変更内容に README の注記・archive の例・budget のコメントが無い。commit: なし（PR 本文） |
| F1-12 | 独立-1 | advisory | no | self-inflicted | security | accepted | 昇格後の再入で design の観点が選定の記録では selected、起動はされない形が残る（reviewer-selection.md:151・152） |
| F1-13 | 独立-1 | advisory | no | self-inflicted | 説明 | accepted | README の注記「build phase が素直に進んだ場合」と express の行の「要件レビューを含む」が分かりにくい |
| F1-14 | 独立-1 | advisory | no | self-inflicted | 説明 | accepted | compact テンプレートの「（trivial 以外の）」は常に真で、本体と書き方がそろっていない |
