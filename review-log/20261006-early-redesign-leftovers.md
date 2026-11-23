---
lane: L1
pr: 384
follow_up_of: 383
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 825e0773ac3a38b66984776c80ea851161c14127 | 0 | 1 | 0 | 2026-10-06T16:10+09:00 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 8e7c0cdeb78b9e7fc248da2cfa13c9bd013d913c | 1 | 1 | 1 | 2026-10-06T16:40+09:00 |
| 方針メモ-1 | Opus 設計レビュー (gdd-opus-advisor, model: opus) | 8e7c0cdeb78b9e7fc248da2cfa13c9bd013d913c | 0 | 0 | 0 | 2026-10-06T16:50+09:00 |
| 独立-3 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 9ee69879bfec98d8f9082ce41c2d7c7c5efd8fb1 | 0 | 3 | 0 | 2026-10-06T18:10+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| M1 | 独立-1 | medium | no | self-inflicted | product | fixed | 推奨を材料に渡す文が `止めるべきか:` を含まず、`no` が届かないと毎回止まる。2 欄をそのまま渡すとした（規定外で直した） commit: 9642ae7 |
| L1 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 「答えが読めない」がどの欄か決まらない。止まる条件を `止めるべきか:` の値で書いた commit: 9642ae7 |
| L2 | 独立-1 | low | no | self-inflicted | bookkeeping | accepted | § 事前回答 2 の「確かめられないとき」の行が `human-check` に固定で、`human-recheck` の対が無い |
| L3 | 独立-1 | low | no | self-inflicted | bookkeeping | accepted | `human-recheck` の `対象:` が completion の途中（Current Task が無い）と Gate Batch で決まらない |
| L4 | 独立-1 | low | no | inherited | bookkeeping | accepted | 自律モードの止める行が 2 欄の省略形で、手順 5 の全欄の形と揃っていない |
| A1 | 独立-1 | advisory | no | inherited | bookkeeping | accepted | advisory: テンプレート外の記述あり（起動時の git status の commit 件名と untracked の review-log のファイル名。判断には使っていない） |
| H1 | 独立-2 | high | yes | self-inflicted | fail-open | fixed | 列挙: 送る側は欄をそのまま渡すが、受ける側は「推奨が材料にあれば」で入り、`推奨:` 欄が無いと止まる規定が発火しない。方針メモ-1 で、答えを main が 1 つの route に写して渡し、止まる例外をやめるとした commit: 834c6c6 |
| M2 | 独立-2 | medium | no | self-inflicted | product | fixed | Codex・Cursor では問いに「人間に止めるべきか」が無く、`止めるべきか:` が常に読めない。問いと欄を書いた（規定外で直した） commit: 834c6c6 |
| L5 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | state-machine.md が止まる根拠を手順 4 のまま指す。例外ごと消した commit: 834c6c6 |
| L6 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | 断片と PR 本文が「答えが読めないとき」のまま。書き直した commit: 834c6c6 |
| L7 | 独立-2 | low | no | self-inflicted | product | fixed | rollback・事前回答 3 の止める条件に、起動できなかったときの除外が無い。例外ごと消した commit: 834c6c6 |
| L8 | 独立-2 | low | no | inherited | bookkeeping | fixed | 自律モードの止める行が省略形。止める行を書かせる規定ごと消した commit: 834c6c6 |
| A2 | 独立-2 | advisory | no | self-inflicted | doc-claim | fixed | 推奨が読めず止めるべきか: no の扱いを PR 本文が明示しない。写し方で human_recheck_required に決めた commit: 834c6c6 |
| P1 | 方針メモ-1 | advisory | no | self-inflicted | product | fixed | Opus の推奨: 止める例外をやめ、答えを 1 つの route に写す（ユーザーへの選択肢では A。Opus の返答内では案 C と呼んでいた）。main の案（例外を残して値で閉じる。選択肢 B）から Opus の案に替えた。ユーザーの指示で Fable にも聞き、推奨は A。ユーザーは A を選んだ。自分で worklog を読む fallback は、T-1 の行を T-2 に当てうるので採らない commit: 834c6c6 |
| M3 | 独立-3 | medium | no | self-inflicted | product | accepted | autonomy.md から「早期の方式判断の判断役を起動できなかったときは当たらない」の句が消え、手順 1（起動できないときは止まる）と state-machine.md（通常どおり判定）が食い違う。止まる側に倒れる |
| M4 | 独立-3 | medium | no | self-inflicted | product | accepted | 「起動できない」を Agent tool のエラーだけにしたので、Codex の委譲の許可なし・Cursor の起動失敗・代わりの経路の前のエラーの読みが 2 通りになる |
| M5 | 独立-3 | medium | no | self-inflicted | doc-claim | fixed | 事前回答の委任先が `なし` なら、判断役の「止めるべき」を main の仮決定で覆せるのに書いていない。断片と PR 本文の限界に書いた commit: b9fd351 |
| L9 | 独立-3 | low | no | self-inflicted | product | accepted | Handoff の本文から事前回答への導線が消え、「表示してから止まる」と § 事前回答 2 の「表示せずに」が食い違う。止まる側に倒れる |
| L10 | 独立-3 | low | no | inherited | bookkeeping | accepted | § 事前回答 2 の「確かめられないとき」の行が `human-check` に固定で、Handoff で着いたときの形が無い |
| L11 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | 未リリースの 3 つの断片が、この PR で消した止まる例外を書いたまま。リリースの dry-run で版の節を直す（PR 本文に列挙） |
| L12 | 独立-3 | low | no | self-inflicted | doc-claim | fixed | 「Codex・Cursor の経路でも欄が返る」が未測の断定。意図として書き直した commit: b9fd351 |
| A3 | 独立-3 | advisory | no | self-inflicted | doc-claim | accepted | `写した route:` の欄と「採った route はこの行に書かない」が並び、取り違えやすい |
