---
lane: L1
pr: 旧#254
follow_up_of: 253
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | e0c6f5faf8adaf673cda5eeb1dcd12bf4d9a583d | 0 | 0 | 0 | 2026-09-30T15:20+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| F1 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | Autonomy Advisor を含む行を探すときに、フェンス・HTML コメント・引用を除く読み方が掛かるかが決まっておらず、PR 本文の草案の「コメントでも数える」と食い違った |
| F2 | 独立-1 | low | no | self-inflicted | product | accepted | Autonomy Advisor を部分列として含まない崩れ（全角空白・ハイフン・空白なし・綴り違い）は、行が無いものとして黙って opus で進む |
| F3 | 独立-1 | low | no | inherited | product | accepted | ~/.gdd/config.local.md や context に書いた Advisor の行は読まれず、黙って opus で進む |
| F4 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 断片の User Action Required が、見出しや説明の行も止まる原因になることを案内していない |
| F5 | 独立-1 | low | no | self-inflicted | product | accepted | Advisor の行が原因で止まったことが、worklog の行でも HITL でも他の理由と区別できない |
| F6 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 断片の Validation の「5 問」に対して、列挙が 4 項目 |
| F7 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 断片の Summary に、Fable: 判断役 の条件を「起動した行」に狭めたことが書かれていない |
