---
lane: L1
pr: 237
follow_up_of: 231
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 30211d9e83e0ac8499afe91fddac1dd8bd44807c | 0 | 3 | 3 | 2026-09-29T18:10+09:00 |
| 独立-2 | light-lane-independent-reviewer, 差分, model: opus | 299145e15ef4f4ee065c12981aa51b9ff83db538 | 0 | 0 | 0 | 2026-09-29T18:45+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| J1 | 独立-1 | medium | yes | self-inflicted | approval-path | fixed | 一覧 3 の除外を Approved Direction か Human Check Status=approved で決めたが、上限の経路は判定の前に pending を書くので成り立たず、Codex＋明示委譲＋Auto-Confirm の steering が止まらなくなった。除外を worklog の自律判断: human-check の行の有無にした commit: 299145e1 |
| J2 | 独立-1 | medium | yes | self-inflicted | approval-path | fixed | 手順 3 で Fable の止めるべきを止まる条件にしたが、手順 4 は判断役の止めるべきだけで分岐し、Fable の答えが捨てられた。手順 4 に Fable を足した commit: 299145e1 |
| J3 | 独立-1 | medium | yes | self-inflicted | approval-path | fixed | 人間の返答の行が一覧 1 を止める記録になったのに、書く条件に Approved Direction の定義が及ぶかと <箇所> が曖昧だった。定義を節全体に効く行へ移し、行を自律判断: human-check と明示した commit: 299145e1 |
| J4 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | autonomy.md の参照元の欄に gate-status-schema.md が無い。PR 本文の限界に書く |
| J5 | 独立-1 | low | no | self-inflicted | bookkeeping | accepted | evidence の autonomy: が state-schema.json に無い（読むコードは無い）。PR 本文の限界に書く |
| J6 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | Autonomy Decisions Check から「全件」が落ちた。PR 本文の限界に書く |
| J7 | 独立-1 | low | no | self-inflicted | product | accepted | 宣言の判定で「前後の空白を除いて」とインデントコードの除外がぶつかり、除外も列挙型のまま。PR 本文の限界に書く |
| J8 | 独立-1 | low | no | inherited | doc-claim | accepted | human check の表示中の返答を扱う requirements-gating-steps.md の回答パターンと phase-progression.md の Active Session Follow-up Classification に手順 5 への参照が無い。PR 本文の限界に書く |
| J9 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 手順 3 が Fable をアドバイザリとしたまま止めるべきの答えだけを拘束した。意見を求める書き方にした（J2 と同じ手順） commit: 299145e1 |
| J10 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | gdd-pr-review-followup の参照は human_recheck_required にも掛かるが、説明は 2 回目の設計し直しだけ。PR 本文に列挙する |
| J11 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 旧#231 の未リリースの断片が旧い規定のまま。リリース時に直す箇所として PR 本文に書く |
| J12 | 独立-1 | advisory | no | self-inflicted | doc-claim | fixed | 断片の User Action が、宣言の受理の範囲が狭まったことを書いていない。1 文足した commit: 299145e1 |
| J13 | 独立-1 | advisory | no | self-inflicted | product | accepted | worklog.md が無いときを行なしと読むので、ファイルを失うと一覧 1 がまた成り立ちうる。PR 本文の限界に書く |
| J14 | 独立-1 | advisory | no | inherited | product | fixed | 判断役が止めるべきと答えた食い違いでも Fable を呼んでいた。呼ばずに止まると書いた commit: 299145e1 |
| K1 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 一覧 3 の「宣言の下で 旧#9 の human check に着いた steering は必ず行を持つ」が、STEP 2 と手順 5 の間の中断を覆わない（挙動は止まる側で正しい）。PR 本文の限界に書く |
| K2 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | 断片の「人間の返答の行の書式を明示した」は main からの差ではない。消した commit: c1e28edc |
| K3 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | PR 本文の限界「Auto-Confirm の steering では上限は毎回止まる」が言い過ぎ。その後 human check を経ていない steering に限った commit: なし（PR 本文） |
| K4 | 独立-2 | low | no | self-inflicted | doc-claim | re-reported | autonomy.md の参照元の欄に gate-status-schema.md が無い（J4 の再掲） |
| K5 | 独立-2 | advisory | no | self-inflicted | doc-claim | fixed | 断片の一覧 3 の括弧が main からの差でない分まで含む。新たに止まる分だけを書いた commit: c1e28edc |
| K6 | 独立-2 | advisory | no | self-inflicted | doc-claim | fixed | 断片の User Action が、インデント・HTML コメントの中に宣言を書いていた利用者の作業を書いていない。1 文足した commit: c1e28edc |
| K7 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | RED-GREEN の場面に、判断役と Fable の止めるべきの場面が無い。PR 本文に書く |
| K8 | 独立-2 | advisory | no | inherited | doc-claim | accepted | 人間の返答の行の欄の値を一般の規定に任せたので、判断役が止めるべきと答えた後の返答の行の値が読み手で分かれうる。PR 本文に列挙する |
| K9 | 独立-2 | advisory | no | inherited | doc-claim | accepted | Fable を呼べないときは Fable の止めるべきが効かないことが限界に無い。PR 本文の限界に書く |
