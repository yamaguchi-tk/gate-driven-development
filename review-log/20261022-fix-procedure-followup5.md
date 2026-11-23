---
lane: L1
pr: 566
follow_up_of: 560
amends: 20261021-fix-procedure-followup2.md, 20261021-fix-procedure-followup4.md
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 0bcf05af | 0 | 1 | 0 | 2026-10-22 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | e209826b | 0 | 2 | 0 | 2026-10-22 |
| 独立-3 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 50096a47 | 0 | 3 | 0 | 2026-10-22 |
| 独立-4 | light-lane-independent-reviewer-xhigh, 差分（ユーザーの指示で追加）, model: opus | a1bf2141 | 1 | 1 | 0 | 2026-10-22 |
| 独立-5 | light-lane-independent-reviewer-xhigh, 差分（独立-4 の修正の確かめ）, model: opus | 2aaf6b2c | 0 | 1 | 0 | 2026-10-22 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| F1 | 独立-1 | medium | no | self-inflicted | wiring | fixed | TDD の「Error Log に行がある steering の task」は task も巡も区別せず、ほかの task や解消済みの指摘を再現するテストを足させる。未測の発火条件を足さない規定（全レーン共通）に合わせて条件を外した（medium・low を直す判断ではない）。commit: e209826b |
| F2 | 独立-1 | low | no | self-inflicted | request-drift | fixed | 設計: 変える（直す指摘を steering 単位の Error Log から推し量っていた）。再オープンと systematic-debugging からの TDD route は、Error Log の記録が任意なので、まだ観測できないことがある。ユーザーの指示（2026-10-22 20:42）で設計を変え、TDD に戻す task に `Fix Findings:` を書く形にした。commit: 5bfdec96 |
| F3 | 独立-1 | low | no | self-inflicted | wiring | accepted | TDD Template の「従う先として名指しする節」では、§ 直し方 2 が「と同じ」で指す reviewer-common の節を読まないと読める |
| F4 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | Error Log の全行を渡す Constraints が、Carry Forward の「他 task のログは渡さない」とぶつかる |
| F5 | 独立-1 | low | no | self-inflicted | test-power | accepted | 修正の前から通るテストの記録の仕方と、1. に戻るときに修正の前のコードで落ちるかを確かめる手順が無い |
| F6 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | AC ID の例外を足したが、同じ節の必須ルール 3 つが例外を持たない |
| F7 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 理由の文の括弧「§ 修正時規律・§ 直し方 を使うものだけ」が、表だけを参照する skill と合わない |
| F8 | 独立-1 | low | no | self-inflicted | bookkeeping | accepted | 旧#553・旧#560 の断片の Changed・Affected Files に、外した仕組みの SKILL.md と rollback-patterns の行が残る |
| F9 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | PR 本文の限界の「Gate Batch では」が、Error Log が steering 単位で残ることより狭い |
| F10 | 独立-1 | low | no | self-inflicted | scope | fixed | TDD の新しい発火条件（Error Log に行がある task）の件数と、止まる損失を測っていない。未測の発火条件を足さない規定（全レーン共通）に合わせて条件を外した（medium・low を直す判断ではない）。commit: e209826b |
| F11 | 独立-1 | low | no | self-inflicted | bookkeeping | accepted | Skill RED-GREEN Evidence が review-log に無い |
| F12 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | Expected output の 4・5 の記録の値に `材料なし` が無い |
| F13 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | § 直し方 2 の「決め方は同じ」が、まだ block / allow に狭まって読める |
| F14 | 独立-1 | advisory | no | self-inflicted | doc-claim | fixed | 設計: 変える（直す指摘を steering 単位の Error Log から推し量っていた）。Error Log の 1 行の要約では、TDD が直す指摘の file:line・severity を読めないことがある。ユーザーの指示（2026-10-22 20:42）で設計を変え、TDD に戻す task に `Fix Findings:` を書く形にした。commit: 5bfdec96 |
| F15 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | PR 本文が、旧#560 の断片から rollback-patterns の Summary の行を消したことを書いていない |
| F16 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | PR 本文の「うち 6 件」は、仕組みに触れる行を数えると 7 件 |
| F17 | 独立-1 | advisory | no | self-inflicted | style | accepted | TDD Template の欄が `<…<…>>` と入れ子になっている |
| F18 | 独立-2 | medium | no | self-inflicted | request-drift | fixed | TDD の「戻った task」を `Gate Rounds` だけにしたので、main（旧#560 でユーザーが選んだ案 B）の 3 種類から狭まった。相談の材料の「Gate Rounds だけに戻す」が誤りだったので、main の 3 種類に戻した。commit: 50096a47 |
| F19 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | systematic-debugging の「どの route でも § 直し方 に従う」が、Gate Rounds の無い TDD route で成り立たない。3 種類に戻して解消。commit: 50096a47 |
| F20 | 独立-2 | low | no | self-inflicted | wiring | fixed | TDD Step 1 が Error Log の場所（`worklog.md`）を名指ししていない。commit: 50096a47 |
| F21 | 独立-2 | medium | no | self-inflicted | wiring | fixed | 設計: 変える（直す指摘を steering 単位の Error Log から推し量っていた）。TDD が直す指摘を読む Error Log には task id と巡の列が無く、ほかの task や直し済みの指摘を拾いうる。ユーザーの指示（2026-10-22 20:42）で設計を変え、TDD に戻す task に `Fix Findings:` を書く形にした。commit: 5bfdec96 |
| F22 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | 設計: 変える（直す指摘を steering 単位の Error Log から推し量っていた）。「決められないときは戻った task」の「決められない」が何を指すか定まらない。ユーザーの指示（2026-10-22 20:42）で設計を変え、TDD に戻す task に `Fix Findings:` を書く形にした。commit: 5bfdec96 |
| F23 | 独立-2 | low | no | self-inflicted | bookkeeping | fixed | 旧#560 の断片の括弧に「決められないときは戻った task」の既定が無い。commit: 50096a47 |
| F24 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | PR 本文の限界の「TDD route で戻った task は入らない」が、Gate Rounds のある TDD route と、completion-check が作成した task の扱いと合わない。commit: なし（PR 本文） |
| F25 | 独立-2 | advisory | no | self-inflicted | doc-claim | fixed | PR 本文の「Error Log を書かない経路」が、changes_requested から来た route を含んで読める。commit: なし（PR 本文） |
| F26 | 独立-3 | medium | no | self-inflicted | request-drift | fixed | 設計: 変える（直す指摘を steering 単位の Error Log から推し量っていた）。再オープンと systematic-debugging からの TDD route を runner が見分けられない残りを、ユーザーに確かめずに限界にした。ユーザーの指示（2026-10-22 20:42）で設計を変え、TDD に戻す task に `Fix Findings:` を書く形にした。commit: 5bfdec96 |
| F27 | 独立-3 | medium | no | self-inflicted | wiring | fixed | 設計: 変える（直す指摘を steering 単位の Error Log から推し量っていた）。「決められないときは戻った task」が、RED Evidence が記録済みで Gate Rounds が 0 の task にも広がり、直し済み・ほかの task の指摘で落ちないテストを足させうる。再現しない指摘の出口が無い。ユーザーの指示（2026-10-22 20:42）で設計を変え、TDD に戻す task に `Fix Findings:` を書く形にした。commit: 5bfdec96 |
| F28 | 独立-3 | medium | no | self-inflicted | wiring | fixed | 設計: 変える（直す指摘を steering 単位の Error Log から推し量っていた）。systematic-debugging から TDD に戻す route は Error Log の記録が任意なので、戻った task なのに読む指摘が無い。ユーザーの指示（2026-10-22 20:42）で設計を変え、TDD に戻す task に `Fix Findings:` を書く形にした。commit: 5bfdec96 |
| F29 | 独立-3 | low | no | self-inflicted | wiring | fixed | 設計: 変える（直す指摘を steering 単位の Error Log から推し量っていた）。completion-check が作った remediation task は RED Evidence の節を持たないので、「同じ節に追記」の前提が無い。ユーザーの指示（2026-10-22 20:42）で設計を変え、TDD に戻す task に `Fix Findings:` を書く形にした。commit: 5bfdec96 |
| F30 | 独立-3 | advisory | no | self-inflicted | bookkeeping | fixed | 設計: 変える（直す指摘を steering 単位の Error Log から推し量っていた）。旧#560 と followup5 の断片の両方が、TDD が Error Log を読むことを書いている。ユーザーの指示（2026-10-22 20:42）で設計を変え、TDD に戻す task に `Fix Findings:` を書く形にした。commit: 5bfdec96 |
| F31 | 独立-4 | high | no | self-inflicted | budget | fixed | 設計: 変える（書き込みを route ごとの行に足していた）。`gdd-systematic-debugging` の本文が 465 行で、allowlist の基準 463 行を超え、`validate-plugin.sh` が止まる。route ごとの 2 行を消し、Failure Routing の前置きの 1 文に、route によらずに書く形で入れた。commit: 2aaf6b2c |
| F32 | 独立-4 | medium | no | self-inflicted | wiring | fixed | completion-check が `Pending Tasks` に置いた再オープン・作成の task は、systematic-debugging を経ずに TDD に入るので `Fix Findings:` が書かれない。completion-check の手順 17 で、再オープン・作成した task のすべてに書くようにした。commit: 2aaf6b2c |
| F33 | 独立-4 | low | no | self-inflicted | wiring | fixed | `Fix Findings:` の出所が impl-gate と completion-check の 2 つに限られ、PR 後のレビューなどからの差し戻しを書けない。出所を、finding を出した gate・レビューの名前に開いた。commit: 2aaf6b2c |
| F34 | 独立-4 | low | no | self-inflicted | wiring | fixed | `Fix Findings:` の行を消す手順が無く、承認後も残る。impl-gate Step 11 と Implementation-Gating Template の State Update Contract 1 で、`Completed Tasks` に移すときに消すようにした。commit: 2aaf6b2c |
| F35 | 独立-4 | low | no | self-inflicted | wiring | fixed | finding を持たない差し戻しで行を書き直すと、前の finding が消える。行は承認まで残し、書き直すのは差し戻しの finding があるときにした。commit: 2aaf6b2c |
| F36 | 独立-4 | low | no | self-inflicted | wiring | fixed | `再現せず` を返しても読む側が無い。その task の RED Evidence の節に書く形にし、worker への handoff で届くようにした。commit: 2aaf6b2c |
| F37 | 独立-4 | low | no | self-inflicted | wording | fixed | Gate Batch で対象の task を決められない finding の書き先が「対象の全 task」で循環している。batch の全 task にした。commit: 2aaf6b2c |
| F38 | 独立-4 | low | no | self-inflicted | measurement | accepted | systematic-debugging から TDD に戻す件数は Error Log の記録が任意なので、transcript の route の出力（`### 選択した route:`）で測るべき。未測のまま受け入れる |
| F39 | 独立-4 | advisory | no | self-inflicted | wording | fixed | `Fix Findings:` の 1 行の形の例が無い。state-field-tiers の行に形を書いた。commit: 2aaf6b2c |
| F40 | 独立-4 | advisory | no | inherited | wiring | accepted | Express の Step 1 が tasklist を作り直すと、`Fix Findings:` の行も消えうる。前からある作り直しの規定で、この PR では直さない |
| F41 | 独立-4 | advisory | no | inherited | bookkeeping | accepted | advisory: テンプレート外の記述あり。PR 本文の抜粋の 18 行目が、テンプレートの欄に当たらない記述だった。次の巡の抜粋から除く |
| F42 | 独立-5 | medium | no | self-inflicted | request-drift | accepted | PR 後のレビューから TDD に戻す経路では、task を Current・Pending に戻す規定が無く、systematic-debugging が書く `Fix Findings:` は Completed の task に付くので TDD Step 1 に届かない。依頼の「systematic-debugging からの TDD route を観測できるようにする」から外れたまま。巡の上限の後なので直さず、PR 本文の限界の節に書く |
| F43 | 独立-5 | low | no | self-inflicted | wiring | accepted | systematic-debugging は completion-check の差し戻しをすべて書かないが、completion-check が書くのは手順 14〜16 で再オープン・作成した task だけ。4c-3 Codebase Health の High など、再オープンを経ない差し戻しではどちらも書かない |
| F44 | 独立-5 | low | no | self-inflicted | wording | accepted | 「その回の finding で書き直す」は、impl-gate の Advisory Findings に記録した medium・low も含むと読め、gate がこの loop では直さないとした指摘にもテストを足させうる |
| F45 | 独立-5 | low | no | self-inflicted | bookkeeping | accepted | 消す側の文が「`Fix Findings:` の行」で、見出しの下の finding の行まで消すと読めない |
| F46 | 独立-5 | low | no | self-inflicted | bookkeeping | accepted | completion-check の差し戻しの書き込みの列挙（gate-checklists Checklist E）に `Fix Findings` が無く、`Completion Reviewed Through` との順序が決まらない |
| F47 | 独立-5 | low | no | self-inflicted | wiring | accepted | 「前の行は残さない」ので、completion-check の未解消の blocker が、後の impl-gate の差し戻しの書き直しで TDD から見えなくなりうる |
| F48 | 独立-5 | low | no | self-inflicted | wiring | accepted | TDD に入り直すと、`再現せず:` と記録した finding にも条件がまた当たり、同じ節に重ねて追記しうる |
| F49 | 独立-5 | low | no | self-inflicted | doc-claim | fixed | PR 本文の「TDD に戻した回数は Error Log に残らないので測れない」は、`changes_requested` の行では数えられる。数えた件数を本文に書き、測れないのは completion の差し戻しから TDD に回した分だけとした。commit: なし（PR 本文） |
| F50 | 独立-5 | advisory | no | self-inflicted | doc-claim | accepted | task-breakdown の Progress Rule と state-machine の tasklist の canonical state が `Fix Findings` に触れていない。正本は impl-gate Step 11 と state-field-tiers なので挙動は変わらない |
| F51 | 独立-5 | advisory | no | self-inflicted | wording | accepted | 書式が表のセルの中にあり、区切りの縦棒をバックスラッシュでエスケープしているので、原文を読む書き手がバックスラッシュごと写しうる |
