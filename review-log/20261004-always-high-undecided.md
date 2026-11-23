---
lane: L1
pr: 360
follow_up_of: 358
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 6b3617dd1d99dd3d261ad18eda1d2c6abd4317ff | 0 | 0 | 0 | 2026-10-04T21:23+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| L1 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | gdd-receiving-code-review:135 の「呼び出し元の Classify に従う」が、Classify を持たない呼び出し元（gdd-requesting-code-review など）を取りこぼし、選択肢が High/Medium のままで Classify の Low と合わない。follow_up_of のため PR 本文の限界に書いた |
| L2 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 戻す条件「4 型・適用範囲に当たらない」が「両方」とも「どちらか」とも読め、受け入れ判定の「範囲外」（比較 diff の外）とも取り違えうる。follow_up_of のため PR 本文の限界に書いた |
| L3 | 独立-1 | low | no | self-inflicted | product | accepted | severity を付けない source では「reviewer の severity に戻す」の戻し先が無く、戻した根拠を残す規定も無い。follow_up_of のため PR 本文の限界に書いた |
| L4 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | Classify の括弧が category の値をバッククォートで再掲し（reviewer-common.md:87 の語彙の規則）、pr-review-followup に category を付ける手順が無く、4 型を理由に実害クラスを付けない制約も無い。follow_up_of のため PR 本文の限界に書いた |
| L5 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 「適用範囲外と判定できた部品」の決め方（block / allow の判定に届くか）が書かれず、括弧の主語も読み分けにくい。follow_up_of のため PR 本文の限界に書いた |
| L6 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 変更断片の User Action Required が「適用範囲外の部品への指摘は High にならない」と言い過ぎている（reviewer が High を付けたものは残る）。follow_up_of のため PR 本文の限界に書いた |
| A1 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 未リリースの断片 20261004-always-high-wording.md:11・:12・:25 が、この差分の後の挙動と合わない。リリースの dry-run で直す |
| A2 | 独立-1 | advisory | no | inherited | doc-claim | accepted | root CLAUDE.md:197 の PR後-N の規定が Classify とそろっていない。root CLAUDE.md を触る open の PR が無くなった後に直す |
