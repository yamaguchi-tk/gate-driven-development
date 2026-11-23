---
lane: L1
pr: 553
follow_up_of: 550
amends: 20261020-fix-procedure.md, 20261021-fix-procedure-followup.md
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 74f22805 | 0 | 3 | 0 | 2026-10-21 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 5edfdd36 | 0 | 0 | 0 | 2026-10-21 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| F1 | 独立-1 | medium | no | self-inflicted | wiring | accepted | TDD Template の条件「Route In Progress が none でない」は TDD を起動する整合した state では成り立たず、TDD route と通常の差し戻しの TDD に § 直し方 が届かない |
| F2 | 独立-1 | medium | no | self-inflicted | scope | fixed | 列挙: § 直し方 2 の狭めた範囲から、判定が使う解析・正規化の共有部品が落ちる。F3 の確認の推奨（Opus と Fable が一致して案 A）で、判定に届く部品の句を足した。commit: 5edfdd36 |
| F3 | 独立-1 | medium | no | self-inflicted | request-drift | accepted | ユーザーが推奨の案 A（判定に届く部品＋(a)(b)）を選んだ。ユーザーが選んだ和の範囲を、数値の理由なしに狭め、限界に「依頼より狭い」が無い |
| F4 | 独立-1 | low | no | self-inflicted | wiring | accepted | § 直し方 5 の材料の出所（前の Round の worker の報告）がディスクに残らず、compaction や resume の後に拾えない |
| F5 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 新しい断片が 2 断片の Summary と Changed を合わせたと書くが、旧#550 の断片の Changed は変えていない。Changed と Affected Files の挙げ方が食い違う |
| F6 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 未リリースの 3 断片が同じ最終の範囲を 3 回、中間の状態からの移り変わりとして書く |
| F7 | 独立-1 | low | no | self-inflicted | scope | accepted | (a)(b) に届く部分の欠陥の種類（消し損じ・誤発火など）を、fail-open の 3 ケースが覆わない |
| F8 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | TDD Template が § 直し方 を「1・2」と番号で切り、冒頭と 3 が読む範囲に入らない。参照元の行に subagent-dispatch.md が無い |
| F9 | 独立-1 | low | no | self-inflicted | request-drift | fixed | 4・5 の件数の定義とコマンドが PR 本文に無く、「止まる損失」として何を数えたかが無い。PR 本文に足した。commit: なし（PR 本文） |
| F10 | 独立-1 | advisory | no | self-inflicted | request-drift | accepted | ユーザーが推奨の案 A（残す）を選んだ。4 はほぼ 0 件と測れたが、残すか外すかをユーザーに問うていない |
| F11 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 範囲を 3 項目にしたのに、続く文が 2 項目向けの「前者」「どちらか」のまま。「同節」が括弧の中の名指しを指す |
| F12 | 独立-2 | low | no | self-inflicted | scope | accepted | 「届くかは判定に届くかで決める」が同語反復で、§ 常時 High の「変更の意図ではなく、欠陥が判定に届くか」と主語がずれる |
| F13 | 独立-2 | low | no | self-inflicted | scope | re-reported | F7 の再掲。(a)(b) に届く部分の欠陥の種類を fail-open の 3 ケースが覆わない |
| F14 | 独立-2 | low | no | self-inflicted | request-drift | re-reported | F3 の再掲。和の範囲を縮めた点をユーザーが確かめた発言が無い |
| F15 | 独立-2 | low | no | self-inflicted | request-drift | fixed | 4・5 の件数のコマンドがプレースホルダで、5 の窓が差 2、4 の損失の上限が無い。PR 本文に script と差 1 の数え直しと 4 の上限を書いた。commit: なし（PR 本文） |
| F16 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 新しい断片が「§ 直し方 を足した」と書き、TDD Template が足したのは 1・2 だけ |
| F17 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | 新しい断片の「§ 常時 High の適用範囲の全体は外した」が、ほかの断片を書き換えた後は何を外したか読めない |
| F18 | 独立-2 | advisory | no | inherited | doc-claim | accepted | root CLAUDE.md の「指摘を直すとき」の fail-open の範囲（block / allow の判定を変える修正）が § 直し方 2 より狭い。合わせるなら L0 の別 PR |
