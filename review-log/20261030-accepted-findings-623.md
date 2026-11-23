---
lane: L1
pr: 625
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | c5e87a7e | 0 | 2 | 0 | 2026-10-30 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 5d03e729 | 0 | 0 | 0 | 2026-10-30 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| F1-1 | 独立-1 | medium | no | self-inflicted | 依頼 | fixed | skills/gdd-brainstorming/SKILL.md:233 が express の部分修正を「再入」に送ったままで、依頼の F1-1・F1-9 が届いていない。commit: 5d03e729 |
| F1-2 | 独立-1 | medium | no | self-inflicted | security | accepted | express の security に渡す「design の観点の組と同じ 1 枚」の中身が決まらず、gdd-security-reviewer.md に design.md 不在の除外が無い（reviewer-selection.md:152） |
| F1-3 | 独立-1 | low | no | self-inflicted | security | accepted | 昇格後の再入で not_applicable と記録させる規定が、:120 の reason の書式と state-machine.md:376 の理由に合わない |
| F1-4 | 独立-1 | low | no | self-inflicted | 再入 | accepted | Round を回す条件の `## Implementation Policy` が requirements-gating-steps.md:123・brainstorming-steps.md:111 に無い |
| F1-5 | 独立-1 | low | no | self-inflicted | ファイル数 | accepted | Scope Breadth の「低」だけ実装コードで数え、「中」「高」は総数のままで重なる（task-sizing.md:261-263） |
| F1-6 | 独立-1 | low | no | self-inflicted | ファイル数 | accepted | 12a を express で飛ばすことが task-sizing.md の表示例と SKILL.md:197 に合わない（brainstorming-steps.md:100） |
| F1-7 | 独立-1 | low | no | self-inflicted | 依頼 | fixed | テンプレートの自走範囲（:29）にテスト・文書を数えない限定が無く、依頼の F1-5 が届いていない。commit: 5d03e729 |
| F1-8 | 独立-1 | low | no | inherited | 説明 | accepted | 消えた Step 7a を指す参照が skills/gdd-brainstorming/SKILL.md:134・:173 に残る |
| F1-9 | 独立-1 | low | no | inherited | 再入 | accepted | 返答分類の表の「部分修正」の行（human-check-template.md:782、common-guardrails.md:227）に express の Round が無い |
| F1-10 | 独立-1 | low | no | inherited | ファイル数 | accepted | faq.md:204-205・README.md:80・:379・gdd-dev.md:29・:231 が express の件数を変更ファイルの総数で書く |
| F1-11 | 独立-1 | low | no | self-inflicted | security | accepted | reviewer-selection.md:36 の起動フェーズで、req-gate の security が express だけに見える |
| F1-12 | 独立-1 | low | no | self-inflicted | 再入 | accepted | 上限で回さずに一括提示するとき、最新 Round が approved の場合の Status と選択肢が決まっていない（requirements-gating-steps.md:76） |
| F1-13 | 独立-1 | advisory | no | self-inflicted | 再入 | accepted | subagent-dispatch.md:60 の (1) に express の一部変更で回す Round が書かれていない |
| F1-14 | 独立-1 | advisory | no | inherited | 説明 | accepted | worked-examples.md:136・:139 に express が通らない工程が残る |
| F2-1 | 独立-2 | low | no | inherited | 再入 | re-reported | brainstorming-steps.md:111・requirements-gating-steps.md:123・human-check-template.md:782 の Round を回す条件に `## Implementation Policy` が無い（F1-4・F1-9 の再掲） |
| F2-2 | 独立-2 | low | no | self-inflicted | 再入 | accepted | SKILL.md:233 の写しが「範囲（Scope・Non-goals）」の定義と、Round の起点を戻さず上限で一括提示する扱いを落としている |
| F2-3 | 独立-2 | low | no | self-inflicted | ファイル数 | accepted | テンプレート :29 の「実装コードが Files の外へ波及したら昇格」が、:54・:70・task-sizing.md:191 の昇格・差し戻しの条件と食い違う |
| F2-4 | 独立-2 | advisory | no | self-inflicted | ファイル数 | accepted | テンプレート :29 で、付随するテスト等が自走範囲の内か外かが書かれていない |
| F2-5 | 独立-2 | advisory | no | self-inflicted | 説明 | accepted | 変更断片 :11 が、未リリースの 20261029-express-planning-review・20261030-accepted-findings-615-618 の「再入」の記述を置き換えると書いていない |
| F2-6 | 独立-2 | advisory | no | self-inflicted | 説明 | accepted | 変更断片 :15 のファイル一覧に skills/gdd-brainstorming/SKILL.md が無い |
| F2-7 | 独立-2 | low | no | inherited | ファイル数 | out-of-diff | state-machine.md:457 が trivial の昇格先を Express 昇格条件（express を続けられない条件）で決めており、向きが逆 |
| F2-8 | 独立-2 | advisory | no | inherited | 再入 | out-of-diff | express 以外の一部変更で AC が +2 以上増えたら CE を回す（SKILL.md:234）が、gdd-dev.md:191 の AC 変更は brainstorming に戻す分類と食い違う |
