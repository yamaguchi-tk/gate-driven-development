---
lane: L1
pr: 旧#253
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | f74424cd0f89df761ba7184d1c132d49aca17dae | 0 | 0 | 0 | 2026-09-30T14:40+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| F1 | 独立-1 | low | no | self-inflicted | product | next-pr | 表記が揺れた Advisor の行（コロン前の空白・小文字・全角コロン・箇条書き・太字）は「行が無い」扱いになり opus で進む |
| F2 | 独立-1 | low | no | self-inflicted | bookkeeping | next-pr | Fable を判断役にして起動しなかった行で、Fable: 欄が「使わない」と「判断役」のどちらかが決まらない |
| F3 | 独立-1 | low | no | self-inflicted | doc-claim | next-pr | § 限界の「比較実験で検出力は約 1/3」に出典が無く、判断役と同じ素の Opus との比（0.5〜0.7）より差を大きく書いている |
| F4 | 独立-1 | low | no | self-inflicted | doc-claim | next-pr | 断片の Changed が、冒頭の段落の変更を挙げていない |
| F5 | 独立-1 | low | no | self-inflicted | doc-claim | next-pr | Codex・Cursor では fable の判断役を起動できず、共有の .gdd-config.md に fable を書くと、それらのセッションの自律モードが止まることが断片と § 限界に無い |
| F6 | 独立-1 | advisory | no | self-inflicted | product | accepted | Fable が判断役のときは、食い違いを確かめる第二意見が無い（§ 限界に無い） |
| F7 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | ~/.gdd/config.local.md の Advisor の行を数えないことが明記されていない |
| F8 | 独立-1 | advisory | no | inherited | doc-claim | accepted | § 限界の dispatch model gate の warn が、Plan で起動する判断役にも出ると読める（出るのは手順 3 の Fable だけ） |
| F9 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 断片の Validation が、RED-GREEN の結果の置き場（PR 本文）を指していない |
