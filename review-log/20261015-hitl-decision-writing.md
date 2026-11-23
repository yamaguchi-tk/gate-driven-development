---
lane: L1
pr: 528
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | be7ef7ed | 0 | 2 | 0 | 2026-10-15 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| A1 | 独立-1 | medium | no | self-inflicted | product | accepted | 長さを優先する規定（必須ルール 12 の 3-5 行、Compact First の line budget、gdd-requirements-gating の圧縮、self-contained-contract・faq の短い自然文）が、§ 判断の書き方 と食い違ったまま残る |
| A2 | 独立-1 | medium | no | self-inflicted | product | accepted | § 判断の書き方 1 は、規則が人の判断を求める処置（上限で残った指摘の受け入れ）を結果で書き直して残す。依頼 (b) の「外すか場所を指す」と手段が違う |
| A3 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 判断ポイントを WHY・要件の直後に置く規定が、必須ルール 13（承認サマリを前に）と full の出力テンプレートの並びと食い違う |
| A4 | 独立-1 | low | no | self-inflicted | product | accepted | 行数の上限で警告する lint-hitl-complexity を、確認なしに限界にした |
| A5 | 独立-1 | low | no | self-inflicted | product | fixed | 3 例の比較と指標の数え方が PR 本文に無い。表と数え方を書いた。commit: なし（PR 本文） |
| A6 | 独立-1 | low | no | self-inflicted | product | accepted | rollback-patterns.md の人に戻す停止本文の書式が § 判断の書き方 を指していない |
| A7 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 6 の良い例が、元の文脈を知らないと読めない |
| A8 | 独立-1 | low | no | self-inflicted | test-power | fixed | Skill RED-GREEN Evidence が PR 本文に無い。書いた。commit: なし（PR 本文） |
| A9 | 独立-1 | advisory | no | self-inflicted | product | fixed | 限界の「必須欄を減らしていない」は依頼の範囲内なので、種類を `その他` にした。commit: なし（PR 本文） |
| A10 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 断片の Summary に `材料:` の行が無い |
| A11 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | CLAUDE.md の安全策 1 の「短い質問か 1 通」と、§ 判断の書き方 のどちらに従うか読めない |
| A12 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | compact の判断ポイント 1 行目（変更前・変更後）と `材料:` の行が重なる |
| A13 | 独立-1 | advisory | no | inherited | doc-claim | accepted | eval fixture が指す compact の判断ポイント節の行番号がずれている（変更前から） |
| A14 | 独立-1 | advisory | no | self-inflicted | bookkeeping | accepted | 依頼の原文がユーザーの発言の写しではなく、依頼したセッションの brief である |
