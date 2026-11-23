---
lane: L1
pr: 493
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 93d1ba7f | 0 | 4 | 0 | 2026-10-14T16:56+09:00 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分（無効化後）, model: opus | a237c7d9 | 0 | 1 | 0 | 2026-10-14T17:15+09:00 |
| 独立-3 | light-lane-independent-reviewer-xhigh, 差分（無効化後）, model: opus | 5ec1153c | 0 | 1 | 0 | 2026-10-14T17:28+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| 独立-1-1 | 独立-1 | medium | no | self-inflicted | request-drift | fixed | 依頼が求めた事前の確認（旧#1327 の差分で 旧#1333・旧#1335 の対象が列挙に出るか）の結果が PR 本文に無い。commit: なし（PR 本文） |
| 独立-1-2 | 独立-1 | medium | no | self-inflicted | request-drift | fixed | completion の Coverage が件数だけで、依頼の「箇所を列挙し 1 行ずつ」から縮んでいた。commit: ba76ae90 |
| 独立-1-3 | 独立-1 | medium | no | self-inflicted | scope-exclusion | accepted | completion の除外条件「理由が成り立つ」に基準が無い |
| 独立-1-4 | 独立-1 | medium | no | self-inflicted | measurement-base | accepted | 影響範囲節の記録が Cumulative Diff Base の glob と混ざりうる |
| 独立-1-5 | 独立-1 | low | no | self-inflicted | wording-consistency | accepted | 記録の書式と grep の除外が 3 ファイルでそろっていない |
| 独立-1-6 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | トークン予算に収めた実測値が PR 本文に無い。commit: なし（PR 本文） |
| 独立-1-7 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | Why 行の実測の出典が無い |
| 独立-1-8 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | quick (express) ではどちらの確認も働かないことが限界に無い |
| 独立-1-9 | 独立-1 | low | no | self-inflicted | bookkeeping | accepted | 断片の type が patch（前例は minor） |
| 独立-1-10 | 独立-1 | low | no | self-inflicted | duplicate-rule | accepted | completion-check の Checklist D と Focus 10 が同じ関心を別々に定める |
| 独立-1-11 | 独立-1 | advisory | no | self-inflicted | severity | accepted | planning reviewer の新しい Medium が接地条件で advisory に落ちうる |
| 独立-1-12 | 独立-1 | advisory | no | self-inflicted | severity | accepted | Severity examples の Low と Focus 10 の Medium がずれる |
| 独立-1-13 | 独立-1 | advisory | no | inherited | coverage-gap | accepted | completion の後に変えた規定はどこでも確かめない |
| 独立-1-14 | 独立-1 | advisory | no | self-inflicted | runtime | accepted | 正本名の grep が completion reviewer の時間上限を圧迫しうる |
| 独立-1-15 | 独立-1 | advisory | no | self-inflicted | design-alt | accepted | 規定を書き写さず正本を指す形にする代案 |
| 独立-1-16 | 独立-1 | advisory | no | self-inflicted | bookkeeping | fixed | Skill RED-GREEN Evidence が抜粋に無い。commit: なし（PR 本文） |
| 独立-1-17 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 断片に Coverage の変化と除外の入口が無い |
| 独立-1-18 | 独立-1 | advisory | no | self-inflicted | severity | accepted | 例に無い文書の High／Medium の扱いが無い |
| 独立-2-1 | 独立-2 | medium | no | self-inflicted | request-drift | fixed | Coverage の区分が網羅せず、依頼の「直さない」を design で宣言した場合に狭めていた。commit: ab582e75 |
| 独立-2-2 | 独立-2 | low | no | self-inflicted | wording-consistency | fixed | 「diff の外」と「直した」の区分が同じ節で食い違う。commit: ab582e75 |
| 独立-2-3 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | PR 本文の変更内容に Coverage の 1 行ずつの列挙が無い。commit: なし（PR 本文） |
| 独立-2-4 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | 断片の区分が agent の区分とそろっていない。commit: ab582e75 |
| 独立-2-5 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | 実データの比較の sha・記録の場所・指摘か列挙かが PR 本文に無い。commit: なし（PR 本文） |
| 独立-2-6 | 独立-2 | advisory | no | self-inflicted | runtime | accepted | 列挙の件数しだいで completion reviewer の 30 分の上限に近づく（未測） |
| 独立-2-7 | 独立-2 | advisory | no | inherited | bookkeeping | accepted | completion-check 手順 13 は Coverage を steering に残さない |
| 独立-3-1 | 独立-3 | medium | no | self-inflicted | request-drift | fixed | 依頼の「列挙に出るか」を出荷する tip の定義で測っていない。tip の定義で 旧#1327 を測り直す。commit: なし（PR 本文） |
| 独立-3-2 | 独立-3 | low | no | self-inflicted | doc-claim | fixed | PR 本文の変更内容に「決められない箇所は指摘に倒す」が無い。commit: なし（PR 本文） |
| 独立-3-3 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | 断片に「決められない箇所は指摘に倒す」が無い |
| 独立-3-4 | 独立-3 | low | no | self-inflicted | coverage-gap | accepted | design で「直す」とした箇所が tip で直ったかを照らし合わせる手順が無い |
| 独立-3-5 | 独立-3 | low | no | self-inflicted | scope-exclusion | accepted | 列挙: 過去を記録した文書（CHANGELOG・review-log など）が grep の除外に無い |
| 独立-3-6 | 独立-3 | advisory | no | self-inflicted | doc-claim | accepted | 決められずに出た High を completion でどう閉じるかが無い |
