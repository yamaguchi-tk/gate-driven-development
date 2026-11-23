---
lane: L1
pr: 555
follow_up_of: 553
amends: 20261021-fix-procedure-followup.md, 20261021-fix-procedure-followup2.md
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | a1205598 | 0 | 2 | 0 | 2026-10-21 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 29e4a047 | 0 | 1 | 0 | 2026-10-21 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| F1 | 独立-1 | medium | no | self-inflicted | request-drift | accepted | ユーザーが推奨の案 A（常に読ませる）を選んだ。直した（commit 29e4a047）。TDD Template の条件（Gate Rounds が 1 以上か Route In Progress が none でない）が、completion-check の差し戻しで作る remediation task の TDD route に届かない。依頼の「常に読ませる」を採らなかった |
| F2 | 独立-1 | medium | no | self-inflicted | request-drift | accepted | ユーザーが推奨の案 A（直した部品を tasklist に Round つきで残す）を選んだ。直した（commit 29e4a047）。§ 直し方 5 の材料を git log から拾うが、前の Round の修正 commit を特定する記録が無く、compaction・resume の後は拾えないまま |
| F3 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 参照元の行に subagent-dispatch.md だけを足し、§ 直し方 を指す rollback-patterns.md が無い |
| F4 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | § 直し方 2 が reviewer-common の基準を写し、欠陥を「誤った値・例外」に、(a)(b) の種類を「など」なしに閉じた |
| F5 | 独立-1 | low | no | self-inflicted | scope | accepted | rollback-patterns の固定の順序が「境界のテスト」だけを 1. の段に入れ、(a)(b) の種類ごとのテストを書く段が無い |
| F6 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 旧#553 の断片の「route の復帰のとき」が条件より広く、Changed の「§ 直し方 2」に当たる Summary が無い |
| F7 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | この PR の断片の Affected Files が変えたファイルを挙げず、範囲の決め方を移り変わりとして書く |
| F8 | 独立-1 | low | no | inherited | bookkeeping | accepted | 旧#550 の断片の Changed に changelog.d の行が残り、Affected Files とそろわない |
| F9 | 独立-1 | advisory | no | self-inflicted | wiring | accepted | TDD の runner は、§ 直し方 が指す先（reviewer-common の (a)(b) など）を読めない |
| F10 | 独立-1 | advisory | no | inherited | wiring | accepted | TDD route で戻った task は、RED Evidence があると Step 2〜4 を飛ばすと読め、§ 直し方 を使う段が無い |
| F11 | 独立-2 | medium | no | self-inflicted | wiring | accepted | Gate Rounds が 2 以上なのに「直した部品」の行が無いとき「なし」と「不明」のどちらかが決まらず、差し戻し元が替わるときの「前の Round」も決まっていない |
| F12 | 独立-2 | low | no | self-inflicted | wiring | accepted | 記録を task 単位に置いたので、completion-check の remediation task の Round どうしを結べない |
| F13 | 独立-2 | low | no | self-inflicted | wiring | accepted | Round の札の語彙と n の出所が書かれず、pre-PR loop の差し戻しに札が無い |
| F14 | 独立-2 | low | no | self-inflicted | wiring | accepted | TDD の subagent は、§ 直し方 が名指しする正本（reviewer-common の (a)(b) など）を読めない |
| F15 | 独立-2 | low | no | self-inflicted | wiring | accepted | 「直した部品」の行が、手順 12b の記録し直しで消えないことの保証が無い |
| F16 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | worker の agent 定義の return の項目が Expected output より少ない |
| F17 | 独立-2 | low | no | inherited | doc-claim | accepted | self-review-lanes.md の理由の文が、参照元の行に足した subagent-dispatch.md に追いついていない |
| F18 | 独立-2 | advisory | no | self-inflicted | bookkeeping | accepted | 未リリースの断片どうしで Changed の行が重なり、旧#553 の断片の Changed が Constraints だけのまま |
| F19 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | 限界の「約 180 行」は、1 行が数千字の行を含むので読む量を小さく見せる |
