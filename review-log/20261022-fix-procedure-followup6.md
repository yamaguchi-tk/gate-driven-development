---
lane: L1
pr: 569
follow_up_of: 566
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | e9394ce5 | 0 | 3 | 0 | 2026-10-22 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | cdc0f4c1 | 0 | 4 | 0 | 2026-10-22 |
| 独立-3 | light-lane-independent-reviewer-xhigh, 差分, model: opus | a9ff9ef3 | 0 | 2 | 0 | 2026-10-22 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| F1 | 独立-1 | medium | no | self-inflicted | request-drift | accepted | 確認済み（2026-10-23 12:47、ユーザーが今の形を選んだ）: 推奨（Opus・Fable が一致。remediation task の形を state-machine.md で決め、TDD の Covers AC の例外を既存の例外にそろえ、再オープンを同じ steering で直す route に限る）で進めている。決められない finding で作る remediation task は Covers AC・Planned RED / E2E を持たないので、TDD Step 2 が task-breakdown に戻し、Resume From=external-review-waiting も消える。依頼の効果がこの部分集合で出ない。PR 本文の「前からの挙動」も事実と違う |
| F2 | 独立-1 | medium | no | self-inflicted | wiring | accepted | 確認済み（2026-10-23 12:47、ユーザーが今の形を選んだ）: 推奨（Opus・Fable が一致。remediation task の形を state-machine.md で決め、TDD の Covers AC の例外を既存の例外にそろえ、再オープンを同じ steering で直す route に限る）で進めている。再オープンが route を問わないので、Hotfix Lane に回す route でも元の steering の task を開き、done のまま開いた task が残って done guard が止める（phase-progression.md 626 行は再 open しないと書く） |
| F3 | 独立-1 | medium | no | self-inflicted | wiring | accepted | 複数の task が同じファイルを Files に持つとき、対象を 1 件に決める方法が無く、読み方で再オープンする task の数が分かれる |
| F4 | 独立-1 | low | no | self-inflicted | wording | accepted | 対象の task を Files で決める文が done の後に限る語を持たず、impl-gate の差し戻しの対象を決める一般の規則とも読める |
| F5 | 独立-1 | low | no | self-inflicted | wiring | accepted | Pre-PR loop の差し戻しを completion-check の差し戻しと読むと、systematic-debugging の除外に当たり誰も Fix Findings を書かない |
| F6 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | phase-progression.md 691 行の「Completed Tasks は保持（revert しない）」が、Pre-PR loop での再オープンと食い違って読める |
| F7 | 独立-1 | low | no | self-inflicted | wiring | accepted | PR 後の Route はクラスタ単位なので、同じ task を指すクラスタごとに systematic-debugging を通すと、Fix Findings が後のクラスタの finding だけで書き直される |
| F8 | 独立-1 | low | no | self-inflicted | wording | accepted | 「上の 2 行と同じ順序と置き方」が、箇条の中の文なのでどの 2 行を指すか決まらない |
| F9 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | PR 本文が発火条件の件数を「1 件以上」としか書かず、件数と止まる分を書いていない |
| F10 | 独立-1 | advisory | no | self-inflicted | wording | accepted | state-field-tiers の行の中で、決められない finding の扱いが Gate Batch（全 task）と done の後（remediation task）に分かれ、後者が行の中に見えない |
| F11 | 独立-2 | medium | no | self-inflicted | request-drift | accepted | 確認済み（2026-10-23 12:47、ユーザーが今の形を選んだ）: design_detail_only（PR 後の 2 件以上・self-inflicted のクラスタ）では task-breakdown が tasklist を作り直すので、再オープンして書いた Fix Findings が消え、PR 後に TDD に戻る主な経路で finding が TDD に届かない。変更断片の「TDD Step 1 が読む」も言い過ぎ |
| F12 | 独立-2 | medium | no | self-inflicted | doc-claim | accepted | state-field-tiers.md の書き手の規定に、同じ steering の route に限る条件が無く、systematic-debugging・state-machine と食い違う |
| F13 | 独立-2 | medium | no | self-inflicted | wiring | accepted | remediation task の欄の規定を、作る側の completion-check 手順 16 が指していない |
| F14 | 独立-2 | medium | no | self-inflicted | wiring | accepted | Gate Batch で再オープンした 2 件目の task が古い Execution Status: completed のままで、TDD と実装が飛ばし、Fix Findings が読まれない |
| F15 | 独立-2 | low | no | self-inflicted | wording | accepted | systematic-debugging の同じ段落で「route によらず書く」と「Hotfix Lane では書かない」がぶつかる |
| F16 | 独立-2 | low | no | self-inflicted | wiring | accepted | AC ID Binding の例外が節の出所で分けられ、remediation task の節への Step 1 の追記が漏れる |
| F17 | 独立-2 | low | no | self-inflicted | wiring | accepted | TDD が remediation task かどうかを見分ける欄が無く、AC を書き損ねた通常の task も例外に入る |
| F18 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | remediation task に legacy の Covers AC を書かせ、canonical の AC と混在する |
| F19 | 独立-2 | low | no | self-inflicted | wiring | accepted | remediation task の欄の一覧に、後段が読む Complexity・Depends on・Execution Status・Carry Forward が無い |
| F20 | 独立-2 | low | no | self-inflicted | wording | accepted | finding のファイルを Files に持つ task が複数あるときの扱いが決まっていない |
| F21 | 独立-2 | advisory | no | self-inflicted | request-drift | accepted | Hotfix Lane では書かないことを、ユーザーに確かめずに決めている |
| F22 | 独立-2 | advisory | no | self-inflicted | wording | accepted | phase-progression.md の「Completed Tasks は保持」と再オープンが字面でぶつかる |
| F23 | 独立-3 | medium | no | self-inflicted | doc-claim | accepted | gdd-task-breakdown/SKILL.md:55 の作り直しで引き継ぐものの列挙に、Fix Findings を写す規定が入っておらず、task-breakdown-steps・state-machine と食い違う。変更断片の「作り直しを通る route で TDD Step 1 が読む」もこの経路では言い過ぎ |
| F24 | 独立-3 | medium | no | self-inflicted | wiring | accepted | 写す規定が、commit を revert する human_recheck_required・planning_rework_required の作り直しにも当たり、消えたコードへの再現テストや余分な remediation task を生む |
| F25 | 独立-3 | low | no | self-inflicted | wiring | accepted | completion-check の手順 14・15 が、再オープンした task を in_progress に戻すことを書かず、state-machine の規定も指さない |
| F26 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | task-breakdown の Execution Status の値域では Pending Tasks の task は not_started で、再オープンで in_progress にした task と食い違う |
| F27 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | 変更断片の Changed の state-machine.md の括弧に、planning 差し戻し後の tasklist.md リセットの節が無い |
| F28 | 独立-3 | low | no | self-inflicted | wiring | re-reported | remediation task の欄の一覧に Complexity・Execution Status・Depends on が無い |
| F29 | 独立-3 | low | no | self-inflicted | wiring | accepted | Gate Batch で batch の全 task に書いた同じ行を、作り直しで畳む規定が無く、同じ finding が重なって写る |
| F30 | 独立-3 | low | no | inherited | request-drift | next-pr | ユーザーの指示で次の PR（2026-10-22 23:09）: PR 後のレビューで Hotfix Lane に回る route では、新しい steering の TDD に finding が届かず、この扱いをユーザーに確かめた記録が無い |
| F31 | 独立-3 | advisory | no | self-inflicted | doc-claim | accepted | 作り直しで写す規定が発火する件数（PR 後に design_detail_only で作り直した件数）を、測るか未測と書いていない |
| F32 | 独立-3 | advisory | no | inherited | doc-claim | accepted | Execution Status の値域が task-breakdown-steps.md:116 では pending で、ほかの 2 か所の not_started と食い違う |
