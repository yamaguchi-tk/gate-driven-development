---
lane: L1
pr: 560
follow_up_of: 555
amends: 20261021-fix-procedure-followup.md, 20261021-fix-procedure-followup2.md, 20261021-fix-procedure-followup3.md
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | e5e6b259 | 0 | 3 | 0 | 2026-10-21 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | bda0c240 | 1 | 2 | 0 | 2026-10-22 |
| 独立-3 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 92ea4d10 | 0 | 0 | 0 | 2026-10-22 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| F1 | 独立-1 | medium | no | self-inflicted | request-drift | fixed | ユーザーが案 B を選んだ。completion-check の remediation task の Round どうしを結べない件を直さず、限界の種類を `その他` にした（依頼より狭い）。commit: bda0c240 |
| F2 | 独立-1 | medium | no | self-inflicted | request-drift | fixed | ユーザーが案 B を選んだ。TDD route で戻った task が RED Evidence で Step 2〜4 を飛ばす advisory を、直しも開示もしていない。commit: bda0c240 |
| F3 | 独立-1 | medium | no | self-inflicted | wiring | accepted | 「不明」を受け取った worker が何をするか（§ 直し方 5 を当てるか）が決まっていない |
| F4 | 独立-1 | low | no | self-inflicted | request-drift | fixed | ユーザーが案 B を選んだ。読む量の advisory を手当てせず、TDD の subagent が読む reference を増やした。限界に読む量か未測を書いていない。commit: bda0c240 |
| F5 | 独立-1 | low | no | self-inflicted | request-drift | fixed | ユーザーが案 B を選んだ。旧#553 の断片（tests/checks の行、Changed の括弧）をそろえず、PR 本文が対象を 旧#550・旧#555 に絞った。commit: bda0c240 |
| F6 | 独立-1 | low | no | self-inflicted | wiring | accepted | 「なし」の条件が Gate Rounds の数え方（Gate Batch で全 task に足す、approved で消える、remediation task）と合わない |
| F7 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | Round の札が一意にならず、直前の Round を何で決めるかが書かれていない |
| F8 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | pre-PR loop は Pre-PR Fix Attempts を数えるのに、Round を数えない例に挙げた |
| F9 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | TDD の subagent が読む reference が「など」で開き、light-task-runner の読む範囲の規定と合わない |
| F10 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 「直した部品」の行を消さない規定が、Verification Evidence を書く手順 12b に無い |
| F11 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 理由の文の「2 reference に限る」が、self-review-lanes を参照するほかの reference と合わない |
| F12 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | agent 定義が指す § Subagent Prompt Contract の下に Expected output の箇条が無い（Codex の見出しの下にある） |
| F13 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | § 直し方 2 の届くかの基準が、指す先の block / allow に狭まって読める |
| F14 | 独立-1 | low | no | self-inflicted | scope | accepted | 1. の段でテストをすべて書くと、2. で分岐が変わったときに足す道が無く、修正前から通るテストの扱いも無い |
| F15 | 独立-1 | advisory | no | self-inflicted | bookkeeping | accepted | 同じ終わりの状態を 旧#550 と この PR の 2 本の断片が書く |
| F16 | 独立-1 | advisory | no | self-inflicted | wiring | accepted | 「直した部品」の仕組みを 3 本続けて直している。機械で取り出す案・外す案と比べていない |
| F17 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | gdd-systematic-debugging の復帰の要約が、§ 直し方 2 のテストも RED の段で書く順序を書いていない |
| F18 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | PR 本文の目的が 旧#555 とその中身を書いていない |
| F19 | 独立-1 | advisory | no | self-inflicted | bookkeeping | accepted | Skill RED-GREEN Evidence の置き場が tip に見えない |
| F20 | 独立-2 | high | no | self-inflicted | doc-claim | fixed | TDD の SKILL.md が self-review-lanes を名指ししたのに参照元の行を足さず、validate の self-review-lane-tokens が FAIL になる。commit: 5f1f9a1f |
| F21 | 独立-2 | medium | no | self-inflicted | wiring | accepted | TDD の新しい段は、直す指摘を読む経路（Template の欄）を名指ししていない |
| F22 | 独立-2 | low | no | self-inflicted | wiring | accepted | 再オープンと systematic-debugging からの TDD route は、runner の入力から観測できない |
| F23 | 独立-2 | medium | no | self-inflicted | wiring | accepted | remediation task の規則に時期の限定が無く、一般の「直前の Round」「なし」の規則とぶつかる |
| F24 | 独立-2 | low | no | self-inflicted | wiring | accepted | remediation task で前の completion の行が無いとき、「不明」でなく「なし」が渡る |
| F25 | 独立-2 | low | no | self-inflicted | wiring | accepted | 「直前の completion R<n>」が、同じ Round の兄弟の task の行を拾いうる |
| F26 | 独立-2 | low | no | self-inflicted | wiring | accepted | task をまたいで completion の行を渡すのが remediation task だけで、再オープンした task に渡らない |
| F27 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | TDD の新しい文に、文言・帳簿の指摘を除く限定が無い |
| F28 | 独立-2 | low | no | self-inflicted | wiring | accepted | Covers AC の無い remediation task で、TDD が追記するエントリの AC ID の例外が無い |
| F29 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 断片の「ほかの task の行」と SKILL.md の「全 task の行」が食い違う |
| F30 | 独立-2 | low | no | self-inflicted | bookkeeping | fixed | request.md に、返事が指す案 B の文が引用されていない。commit: 45c7b01b |
| F31 | 独立-2 | advisory | no | self-inflicted | doc-claim | fixed | PR 本文の字数に測り方が無く、byte 数を字と書いていた。commit: なし（PR 本文） |
| F32 | 独立-2 | advisory | no | self-inflicted | doc-claim | fixed | PR 本文が TDD Template の変更を 2 行に分け、1 行が今の文言と合わない。commit: なし（PR 本文） |
| F33 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | 理由の文の「8 skill と 2 reference に限る」が、self-review-lanes を書式・表で参照するほかの reference と合わず、「参照先」と「参照元」の語も逆 |
| F34 | 独立-3 | advisory | no | self-inflicted | doc-claim | accepted | TDD の SKILL.md が § 直し方 を「1・2」と番号で切り、冒頭の当てない範囲が指す範囲に入らない |
| F35 | 独立-3 | advisory | no | self-inflicted | doc-claim | accepted | 理由の文で TDD が「§ 直し方だけを使い」の側に入り、注記の「1・2」より広く読める |
