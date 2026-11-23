---
lane: L1
pr: 379
follow_up_of: 377
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 910894e2c9d49265ce8cc0845d210df1a85f5062 | 0 | 3 | 0 | 2026-10-05T16:20+09:00 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | e6f6d4c9f49e52e41b805f6c0912486d101e344b | 0 | 2 | 0 | 2026-10-05T17:30+09:00 |
| 独立-3 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 932174446a61f9d4d9a518f7dc3cd34bdf87a2e6 | 0 | 2 | 0 | 2026-10-05T19:10+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| M1 | 独立-1 | medium | no | self-inflicted | product | fixed | 1 steering 1 回の判定に使う worklog の行を書く指示が消えている。起動する側が起動を試みた直後に書くとした（ユーザーの指示で取り込み） commit: 526e7d04 |
| M2 | 独立-1 | medium | no | self-inflicted | product | fixed | 推奨と ADR ≥ 2 の判定の順序が skill と判定表で逆。ADR ≥ 2 などの後、テスト設計の前にそろえた commit: 526e7d04 |
| M3 | 独立-1 | medium | no | self-inflicted | product | fixed | skill の前置きに、止めるべきという答えと route でない案の置き換えが無い。当て方を正本に従わせた commit: 526e7d04 |
| L1 | 独立-1 | low | no | self-inflicted | product | fixed | main が high を数える入力の場所が無い。impl gate の handoff で数えるとした commit: 526e7d04 |
| L2 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 自走範囲の外で human_recheck_required になると言い切っている。決定木の 3b〜5 で判定するとした commit: 526e7d04 |
| L3 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 「作り直しが繰り返されない」が言い過ぎ。防げる範囲に狭めた commit: 526e7d04 |
| L4 | 独立-1 | low | no | self-inflicted | product | fixed | TDD などの戻し先を推すと人間停止になる。戻し先を通常の判定に入れた commit: 526e7d04 |
| L5 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 自律モードで数える箇所の語彙が決まっていない。一覧 2（human-recheck）とした commit: 526e7d04 |
| L6 | 独立-1 | low | no | self-inflicted | bookkeeping | fixed | Gate Batch での task と high の書き方が無い commit: 526e7d04 |
| L7 | 独立-1 | low | no | inherited | product | fixed | skill の Steps 5 が推奨より implementation_fix_only を先に置く commit: 526e7d04 |
| A1 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 前の未リリースの断片に古い記述が残る。リリースの dry-run で版の節を直す |
| A2 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | commands/gdd-dev.md の概要に判断役が無い。詳細は subagent-dispatch.md に委ねている |
| A3 | 独立-1 | advisory | no | self-inflicted | style | accepted | 1 つの箇条に規定を詰め込みすぎている。references の行予算の残りが 2 行で分けられない |
| A4 | 独立-1 | advisory | no | self-inflicted | doc-claim | fixed | 閾値の根拠の判定が自由文の部分一致。発火でない言及も数えうると書いた commit: 526e7d04 |
| A5 | 独立-1 | advisory | no | self-inflicted | doc-claim | fixed | 数えが途切れるのは design_detail_only だけではない commit: 526e7d04 |
| A6 | 独立-1 | advisory | no | self-inflicted | product | fixed | 起動できなかった回も 1 回に数える。本文に書いた commit: 526e7d04 |
| A7 | 独立-1 | advisory | no | self-inflicted | test-power | fixed | RED-GREEN の場面が足りない。1 回目に行が書かれる場面と順序の場面を足す commit: なし（PR 本文） |
| M4 | 独立-2 | medium | no | self-inflicted | product | fixed | high を数える handoff のファイルを書く側が無い。impl gate の handoff の例に Round ごとの finding を書くとした（2 巡目だが直した） commit: 9321744 |
| M5 | 独立-2 | medium | no | self-inflicted | product | fixed | 自律モードで止めるべきという答えが一覧 2 に入り、人間に止まらない。手順 4 で止めるとした（2 巡目だが直した） commit: 9321744 |
| L8 | 独立-2 | low | no | self-inflicted | product | fixed | 3 回連続・承認後 2/2 より推奨を先に当てうる。それらの後に当てるとした commit: 9321744 |
| L9 | 独立-2 | low | no | self-inflicted | product | fixed | root-cause-investigation は Decision Tree の戻し先ではない。No Root Cause Routing に戻すとした commit: 9321744 |
| L10 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | 断片に handoff が読めないときと起動できなかったときの扱いが無い commit: 9321744 |
| A8 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | 前の未リリースの断片の古い記述はリリースで直す（A1 と同じ） |
| M6 | 独立-3 | medium | no | self-inflicted | product | accepted | impl gate の handoff の書き方が subagent-dispatch.md の例にしか無く、Template と SKILL.md の Step 9 に無い。書かれないと判断は飛ぶ（前と同じ挙動） |
| M7 | 独立-3 | medium | no | self-inflicted | product | accepted | 止めるべきなら手順 4 で止まる例外が autonomy.md の止まる場面と rollback-patterns.md の handoff に無く、一覧 2 経由で進みうる |
| L11 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | 答えが読めないときに止まることが PR 本文・断片・autonomy.md のヘッダに無い |
| L12 | 独立-3 | low | no | self-inflicted | bookkeeping | accepted | worklog の 早期方式判断: 行に「読めない」の値が無い |
| L13 | 独立-3 | low | no | self-inflicted | bookkeeping | accepted | 自律判断: の行が手順 5 の書式より欄が少ない |
| L14 | 独立-3 | low | no | self-inflicted | product | accepted | ## Round <Gate Rounds> の見出しが task をまたいで重複しうる |
| L15 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | root-cause-investigation の推奨の戻し先は Methodology Delegation が実行できる規定 |
| L16 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | Decision Tree 1 で 3 回連続・2/2 に当たったときの行き先が書かれていない（Escalation Decision Table が受け止める） |
| A9 | 独立-3 | advisory | no | inherited | product | accepted | 判断役への問いに TDD・root-cause-investigation の選択肢が無く、自由文から読み替える |
