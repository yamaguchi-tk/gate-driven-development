---
lane: L1
pr: 389
follow_up_of: 384
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | db379f16a1c94241c91266e1ac201dfa5df7e642 | 0 | 2 | 0 | 2026-10-06T20:00+09:00 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 6d860704654ac37dcc442a367a7cc83090b75663 | 0 | 1 | 0 | 2026-10-06T20:40+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| M1 | 独立-1 | medium | no | self-inflicted | product | fixed | Handoff に足した事前回答の文に主語が無く、Handoff を出す subagent が止める行を書くと Stop hook の押し返しが効かない。判定は main が行い subagent は行を書かないとした（規定外で直した） commit: 4046f64 |
| M2 | 独立-1 | medium | no | inherited | product | accepted | 事前回答の適用中に上限の方式転換へ繰り返し着いても、§ 事前回答 3 に 2 回目で止まる条件が無い（数え方が決まっていない） |
| L1 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | Handoff で autonomy と事前回答のどちらを先に見るかが書かれていない。事前回答を先にした commit: 4046f64 |
| L2 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 起動できないの 1 つ目が代わりの経路を条件なしに求め、autonomy.md 手順 1（定義が読み込まれていないときだけ）と食い違う |
| L3 | 独立-1 | low | no | self-inflicted | bookkeeping | accepted | Completion Rounds 上限の Handoff では Current Task が無く、`対象:` が決まらない |
| A1 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 未リリースの断片 20261006-early-redesign-leftovers.md の旧い「起動できない」の定義。リリースで版の節を直す |
| A2 | 独立-1 | advisory | no | self-inflicted | doc-claim | fixed | 限界の「hook では強制しない」に、Stop hook の 1 回の押し返しを添える commit: なし（PR 本文） |
| M3 | 独立-2 | medium | no | self-inflicted | product | accepted | Handoff の判定を main に移したが、main の入口（HITL Pending Hard Invariant・build loop の post-return routing）に自律モードの枝が無く、subagent の Handoff では一覧 2・3 と手順 5 の行を誰も担わない。人間に表示して止まる側に倒れる |
| L4 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 判定を main に移した後も「出力の前に」「出力の代わり」のままで、subagent 経路では指す先が合わない |
| L5 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | 限界の「Stop hook が 1 回押し返す」は事前回答の行があるときだけ。条件を書いた commit: なし（PR 本文） |
| L6 | 独立-2 | low | no | inherited | product | accepted | completion-check の Round 上限超過では Current Task が無く、`human-recheck` の `対象:` が決まらない |
| L7 | 独立-2 | low | no | inherited | product | accepted | Completion-Check Post-Return Routing が Next Action だけで分岐し、Round 上限超過の Handoff の判定に着かないことがありうる |
| A3 | 独立-2 | advisory | no | inherited | doc-claim | accepted | 未リリースの断片 20261006-early-redesign-stop-wiring.md の止める行の記述が古い。リリースで版の節を直す |
