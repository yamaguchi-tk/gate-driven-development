---
lane: L1+
pr: 459
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ | Opus 設計レビュー (gdd-opus-advisor, model: opus) | 775988f7 | 2 | 3 | 0 | 2026-10-13 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 1e03cc0f | 3 | 1 | 3 | 2026-10-13 |
| 方針メモ-1 | Opus 設計レビュー (gdd-opus-advisor, model: opus) | 1e03cc0f | 0 | 0 | 0 | 2026-10-13 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | d2706d21 | 2 | 0 | 2 | 2026-10-13 |
| 方針メモ-2 | Opus 設計レビュー (gdd-opus-advisor, model: opus) | d2706d21 | 0 | 0 | 0 | 2026-10-13 |
| 独立-3 | light-lane-independent-reviewer-xhigh, 差分, model: opus | d6d285fd | 0 | 0 | 0 | 2026-10-13 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| P-1 | 方針メモ | high | no | self-inflicted | fail-open | fixed | 衝突の解消の行数を対称差だけで測ると、`--ours` で main の行を捨てた解消が 1 行として通る。両側の追加行が残ることを必須にした commit: aff58341 |
| P-2 | 方針メモ | high | no | self-inflicted | fail-open | fixed | `-U0` の差分の比較は行の位置を見ず、PR の行を別の位置へ動かした merge が一致する。自動 merge の tree との一致を必須にし、criss-cross を不成立にした commit: aff58341 |
| P-3 | 方針メモ | medium | no | self-inflicted | trust-boundary | fixed | default branch を gdd_resolve_base_ref で解くと gh-merge-base や local の branch まで落ちる。remote-tracking の ref に限った commit: aff58341 |
| P-4 | 方針メモ | medium | no | self-inflicted | product | fixed | merge gate は `received: no` の経路で HEAD の sha の Independent Review を要求し、引き継ぎを読まない。ユーザーが「この PR に含める」を選び、merge gate も引き継ぎを読むようにした commit: f6162ac7 |
| P-5 | 方針メモ | medium | no | self-inflicted | product | fixed | 閾値 10 を「測れない」とせず、git の履歴で測る。GDD を使う別の repo の 432 件で測り references に書いた commit: e2a6692d |
| P-6 | 方針メモ | low | no | self-inflicted | style | fixed | python3 を -I -X utf8 なしで起動していた commit: aff58341 |
| I1-1 | 独立-1 | high | yes | self-inflicted | fail-open | fixed | 判定の期限 5 秒が hook の経過時間を見ず、hook の timeout 10 秒を超えて gate が通りうる。hook の起動からの残り時間を渡す commit: ed20b7a0 |
| I1-2 | 独立-1 | high | yes | self-inflicted | fail-open | fixed | `.gitattributes` で binary 扱いのテキストが衝突すると、行の検査が空のまま通る。blob を直接読む commit: c67b44c1 |
| I1-3 | 独立-1 | high | yes | self-inflicted | fail-open | fixed | 列挙: 衝突ファイルの中で PR の行を動かしても数えない。方針メモ-1 で (a) を選び、自動 merge の blob と構造で照合する。履歴 432 件で衝突の外の行が違う merge 12 件（事故の形が 1 件以上）、新しい判定で止まる分は 315 件から 307 件 commit: c67b44c1 |
| I1-4 | 独立-1 | medium | no | self-inflicted | test-power | fixed | 時間切れ・バイナリ・消えたファイルの分岐にテストが無い commit: 43137a40 |
| I1-5 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 同じ規定を書いた gdd-pr-review・CONTRIBUTING が引き継ぎを指さない（independent-review.md は文を pin するテストがあり足せない） commit: c67b44c1 |
| I1-6 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 「merge sha で書き直す」と検算の「sha だけを書き換えない」が食い違う commit: c67b44c1 |
| I1-7 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 検算の出力の変化が断片に無い commit: c67b44c1 |
| I1-8 | 独立-1 | low | no | self-inflicted | product | fixed | 依頼の (a)(b)(c) に無い条件を足した。ユーザーが「残す」を選び、(c) の読み替えも確かめた（request.md に追記） commit: なし（request.md） |
| I1-9 | 独立-1 | low | no | self-inflicted | product | fixed | 引き継ぎを pre-PR gate にも広げた。ユーザーが「広げたまま」を選んだ（request.md に追記） commit: なし（request.md） |
| I1-10 | 独立-1 | low | no | self-inflicted | product | fixed | 閾値 10 が実測の最大から導かれていない。新しい数え方で測り直し、最大 3 に余裕を足して 5 にした commit: c67b44c1 |
| I1-11 | 独立-1 | low | no | self-inflicted | product | fixed | 同じ diff --git 行の 2 件目で 1 件目を上書きする commit: ed20b7a0 |
| I1-12 | 独立-1 | low | no | self-inflicted | product | fixed | 衝突マーカーの検査が 7 文字ちょうどに限る commit: ed20b7a0 |
| I1-13 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | PR 本文の目的の断定が広い commit: なし（PR 本文） |
| I1-14 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 履歴に判定を当てたコマンドが無い commit: なし（PR 本文） |
| I1-15 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | (a) の働きと取り直しになる場合の列挙が不正確 commit: c67b44c1 |
| I1-16 | 独立-1 | advisory | no | self-inflicted | style | fixed | コードの条件の番号が正本とずれている commit: c67b44c1 |
| I1-17 | 独立-1 | advisory | no | self-inflicted | style | fixed | 使っていない局所変数 commit: ed20b7a0 |
| I1-18 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | steering_size.py の残す行の例に Carry 行が無い |
| I1-19 | 独立-1 | advisory | no | self-inflicted | product | fixed | origin/HEAD が PR の base と違う repo・積み PR では引き継げないことを限界に書く commit: c67b44c1 |
| I1-20 | 独立-1 | advisory | no | self-inflicted | product | accepted | 検算が既定で同じ判定を 2 回走らせる |
| I1-21 | 独立-1 | advisory | no | self-inflicted | product | accepted | block の文が、引き継げなかった理由の確かめ方を示さない |
| PM1-1 | 方針メモ-1 | advisory | no | self-inflicted | product | fixed | パーサの先頭・末尾の固定、`=======` の本数、共有行の数え方、conflictStyle のテストを足す commit: c67b44c1 |
| I2-1 | 独立-2 | high | yes | self-inflicted | fail-open | fixed | 区切りの `=======` だけを残した解消をマーカーと見ず、余分な 1 行として引き継ぐ（依頼の (b) より狭い）。余分な行に 7 文字以上のマーカーの形（`=` を含む）を当てて止める。履歴 432 件で該当 0 件 commit: 2ffb5714 |
| I2-2 | 独立-2 | high | yes | self-inflicted | fail-open | fixed | Python 側の期限を git を呼ぶ前にしか見ず、衝突ファイルの照合（O(n·k)）が期限を越えて hook の timeout を過ぎうる。setitimer の時計 1 つで verify 全体を切る。履歴の衝突ファイルは最大 31,098 行 commit: 2ffb5714 |
| I2-3 | 独立-2 | low | no | self-inflicted | doc-claim | next-pr | SECONDS の切り捨てで、hook の起動から 8 秒の上限が最悪 9 秒になる |
| I2-4 | 独立-2 | low | no | self-inflicted | product | next-pr | merge gate で引き継げずに止めるとき、引き継ぎの案内と理由が出ない |
| I2-5 | 独立-2 | low | no | self-inflicted | doc-claim | next-pr | self-review-lanes.md の待機免除の括弧が HEAD sha のまま |
| I2-6 | 独立-2 | low | no | self-inflicted | doc-claim | next-pr | independent-review.md・gdd-pr-review-followup が HEAD sha のレビューだけを要件と読める |
| I2-7 | 独立-2 | low | no | self-inflicted | doc-claim | next-pr | 検算の Self Review の行の文で、書き換えない・書き換えてよいが同じ文に並ぶ。gdd-completion-check に例外が無い |
| I2-8 | 独立-2 | low | no | self-inflicted | doc-claim | next-pr | 断片が merge gate も independent-review-stale で止め、案内を足したと読める |
| I2-9 | 独立-2 | low | no | self-inflicted | test-power | next-pr | 残り時間 0 のテストが存在しない repo で、budget の検査を固定していない |
| I2-10 | 独立-2 | low | no | self-inflicted | test-power | next-pr | 遅い git のテストが経過時間を見ず、budget を無視する変異を落とさない |
| I2-11 | 独立-2 | low | no | self-inflicted | test-power | next-pr | merge gate の待機経過後の経路（independent-review-missing）にテストが無い |
| I2-13 | 独立-2 | low | no | self-inflicted | doc-claim | next-pr | 「merge が PR の中身を変えていない」の断定が広い。ブロックの中で PR 側が消した行が戻る形を限界に書いていない |
| I2-14 | 独立-2 | low | no | self-inflicted | doc-claim | next-pr | テストの docstring が対称差の数え方のまま |
| I2-15 | 独立-2 | low | no | self-inflicted | doc-claim | next-pr | gate-ledger.sh の冒頭の呼び出し元に merge gate が無い |
| I2-12 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | PR 本文の変異の表で、(a) と default branch 側の検査を外す変異の落ちたテストが例外による。raise を pass に替えて当て直す commit: なし（PR 本文） |
| PM2-1 | 方針メモ-2 | advisory | no | self-inflicted | product | fixed | 安全策 4 の発火（fail-open の high を含む巡が 2 回）。memory の 2026-10-08 の決定で、続行は Opus への相談で決めた。Opus の推奨（F1 は余分な行に 7 文字以上のマーカーの形を当てる、F2 は setitimer の時計 1 つ、blob の上限は入れない、3 巡目で high が残ったら止めて限界に書く）を採った。食い違いは無く、Fable は呼ばない commit: 2ffb5714 |
| I3-1 | 独立-3 | low | no | self-inflicted | product | next-pr | Windows には SIGALRM・setitimer が無く、引き継ぎが常に「判定できない」で無効になる。理由の文が分からない（PR 本文の限界に書いた） |
| I3-2 | 独立-3 | low | no | self-inflicted | test-power | next-pr | Python の計算が長いときのテストの上限 5 秒が、渡した残り時間 0.5 秒をほとんど縛らない |
| I3-3 | 独立-3 | low | no | self-inflicted | doc-claim | re-reported | SECONDS の切り捨てで「8 秒を過ぎる分も使わない」が最大 1 秒ずれる（I2-3 の再掲） |
| I3-4 | 独立-3 | advisory | no | self-inflicted | product | accepted | マーカーの行を読む正規表現どうしで、CR だけの行末・タブの扱いが少しずつ違う |
| I3-5 | 独立-3 | advisory | no | self-inflicted | doc-claim | accepted | _resolution_lines の docstring に余分な行のマーカーの検査が無い |
| I3-6 | 独立-3 | advisory | no | self-inflicted | product | accepted | signal.signal の前の handler を戻していない |
| I3-7 | 独立-3 | advisory | no | self-inflicted | test-power | accepted | 時計と subprocess の timeout のどちらが効いたかをテストが区別しない |
| I3-8 | 独立-3 | advisory | no | self-inflicted | bookkeeping | accepted | advisory: テンプレート外の記述あり。起動時の git status に、巡の対応を含む commit の件名が届いた（判断には使っていない） |
