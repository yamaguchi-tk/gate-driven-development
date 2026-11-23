---
lane: L1
pr: 437
follow_up_of: 430
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | cb708d5e | 0 | 2 | 0 | 2026-10-12 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | b2c1eeeb | 0 | 1 | 0 | 2026-10-12 |
| 独立-3 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 3e20f098 | 0 | 0 | 0 | 2026-10-12 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| G1-1 | 独立-1 | medium | no | self-inflicted | request-drift | fixed | 依頼の「worker の経路の規定とそろえる」が届いておらず、SKILL の書き手から worker の経路が落ちていた。書き手を 3 者にし、worker 自身は書かないと書いた。commit: b2c1eeeb |
| G1-2 | 独立-1 | medium | no | self-inflicted | bookkeeping | accepted | `task:` 欄が Gate Batch・並列実行で 1 つに決まらず（Current Task の並びが Round の間に変わる）、Round <n> が 1 に戻りうる。PR 本文の限界に書いた |
| G1-3 | 独立-1 | low | no | self-inflicted | product | accepted | `<phase>` に書く字句（`## Phase` の値か短い名前か）が決まっていない。PR 本文の限界に書いた |
| G1-4 | 独立-1 | low | no | self-inflicted | product | accepted | 判定を出口に合わせたのが超過→blocked だけで、ほかの出口で書くか・判定をどれにするかが決まらない。PR 本文の限界に書いた |
| G1-5 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | ポインタ 6 箇所が「Round を進めずに止まる出口でも」を落としている。PR 本文の限界に書いた |
| G1-6 | 独立-1 | low | no | self-inflicted | bookkeeping | accepted | 件数の「blocking の再現を確かめた後」が 2 つの gate にしか当たらず、blocking の意味も gate ごとに違う。PR 本文の限界に書いた |
| G1-7 | 独立-1 | low | no | self-inflicted | bookkeeping | accepted | プレースホルダの末尾が `->` に読める。PR 本文の限界に書いた |
| G1-A1 | 独立-1 | advisory | no | self-inflicted | bookkeeping | accepted | 前の書式（`task:` の無い行）の扱いが無い |
| G1-A2 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | requirements-gating-steps.md のポインタが、reviews.md の見出しで Round を数える項の中にある |
| G1-A3 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | blocked・timeout の行を数えるときに除く読み方が書かれていない |
| G1-A4 | 独立-1 | advisory | no | self-inflicted | doc-claim | fixed | Skill RED-GREEN Evidence を抜粋から確かめられない。PR 本文に書いた。commit: なし（PR 本文） |
| G2-F1 | 独立-2 | medium | no | self-inflicted | request-drift | fixed | main が gate runner を時間上限・エラーで止めて出口を決めたとき、書き手がいない（依頼の「design・implementation の timeout は blocked で止まる」「書き手を書く」がこの出口で届かない）。書き手に main を足した。commit: 3e20f098 |
| G2-F2 | 独立-2 | low | no | inherited | wiring | accepted | worker 経由のとき、main が判定と件数を読む入力（worker の result.json に欄が無い）が決まっていない。PR 本文の限界に書いた |
| G2-F3 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | requirements-gating-steps.md の再掲に書き手が無く、worker 経由の planning で worker も書きうる。PR 本文の限界に書いた |
| G2-F4 | 独立-2 | low | no | self-inflicted | request-drift | fixed | `timeout` と `blocked` を出口ごとにどう使い分けるかが無く、依頼の「design・implementation の timeout は blocked で止まる」が規定に無い。正本に書いた。commit: 3e20f098 |
| G2-A1 | 独立-2 | advisory | no | self-inflicted | doc-claim | fixed | Skill RED-GREEN Evidence を抜粋から確かめられない。PR 本文に書いた。commit: なし（PR 本文） |
| G3-1 | 独立-3 | low | no | self-inflicted | request-drift | accepted | completion-check の時間超過の出口に当たる判定の値が決まっていない（依頼の「判定の値の集合を gate の出口に合わせる」が completion だけ閉じていない）。巡の上限の 3 巡目のため直さず、PR 本文の限界の先頭に依頼から外れたままとして書いた |
| G3-2 | 独立-3 | low | no | self-inflicted | bookkeeping | re-reported | `<phase>` の値の書き方（`gdd-` の有無）が決まっていない（G1-3 と同じ） |
| G3-3 | 独立-3 | low | no | self-inflicted | bookkeeping | accepted | main が runner を止めたときに書く行の件数の値が決まっていない（`不明` が無い）。PR 本文の限界に書いた |
| G3-4 | 独立-3 | low | no | self-inflicted | bookkeeping | accepted | runner が自分の行を書いた後に止められると、同じ Round の行が 2 本になる。PR 本文の限界に書いた |
| G3-5 | 独立-3 | low | no | self-inflicted | bookkeeping | accepted | planning の runner を brainstorming の途中で止めても requirements-gating の行が増える。PR 本文の限界に書いた |
| G3-A1 | 独立-3 | advisory | no | self-inflicted | doc-claim | accepted | 「main が…エラーで止めて」が、runner が自分でエラーで返った場合を含むと読めない |
| G3-A2 | 独立-3 | advisory | no | self-inflicted | doc-claim | fixed | Skill RED-GREEN Evidence を抜粋から確かめられない。PR 本文に書いた。commit: なし（PR 本文） |
