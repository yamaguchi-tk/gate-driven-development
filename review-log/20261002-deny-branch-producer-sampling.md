---
lane: L1
pr: 297
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | f051dddec245fec1557b68fa7844c315a2e4aace | 0 | 0 | 0 | 2026-10-02T16:30+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| D1 | 独立-1 | medium | no | self-inflicted | doc-claim | next-pr | self-review-lanes.md:6 の参照元の理由が「上記 4 skill」のままで、5 件目の gdd-subagent-driven-implementation に当てはまらない |
| D2 | 独立-1 | medium | no | self-inflicted | bookkeeping | next-pr | 規律 C の followup 側の記録先「証跡の Fixed findings」が id だけの欄で、gdd-pr-review-followup の ① の記録先（Verification 相当）とも食い違う |
| D3 | 独立-1 | medium | no | self-inflicted | product | next-pr | formal gate の修正を書く worker subagent（remediation・implementation worker）に規律 C が届かず、return にも deny の分岐を足したと伝える欄が無い |
| D4 | 独立-1 | low | no | self-inflicted | doc-claim | next-pr | self-review-lanes.md:61 の総称文が「規律 A / B は手順の骨格」のままで、規律 C の位置づけが無い |
| D5 | 独立-1 | low | no | self-inflicted | test-power | next-pr | 規律の数のテストを A〜C に広げ、文書に箇条があるかだけを見る assert を足した（root CLAUDE.md § テストと食い違う） |
| D6 | 独立-1 | low | no | self-inflicted | product | next-pr | formal gate の記録先 findings.md は存在率 6% で避けられている置き場所。tasklist.md の Verification Evidence か worklog.md が候補 |
| D7 | 独立-1 | low | no | self-inflicted | bookkeeping | next-pr | 記録の項目に、正当な入力の件数・比べた直し方と採った理由が無く、design-gating Step 5d の記録ともそろわない |
| D8 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | PR 本文の目的の「GDD の形式レーン」が定義の無い語で、差分の範囲（pr-review-followup を含む）より狭い。commit: なし（PR 本文） |
| D9 | 独立-1 | low | no | inherited | doc-claim | next-pr | tests/checks/self-review-lane-tokens.sh:69 のコメントが「参照側は 3 skill」のまま |
| D10 | 独立-1 | advisory | no | self-inflicted | bookkeeping | accepted | 断片の type: patch が、同じ種類の変更の先例（external-format-sampling-first は minor）とそろわない。PR 本文に列挙 |
| D11 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 「外部形式の実測 ①〜④ と同じ」の範囲が広く（③ の fixture を含む）、番号も固定されていない。PR 本文に列挙 |
