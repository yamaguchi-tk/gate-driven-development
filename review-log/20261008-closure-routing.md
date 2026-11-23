---
lane: L1
pr: 405
follow_up_of: 403
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 2e5ef2ac | 0 | 4 | 1 | 2026-10-08T03:10+09:00 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 44435341 | 0 | 1 | 0 | 2026-10-08T03:40+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| F1 | 独立-1 | medium | yes | self-inflicted | approval-path | fixed | 列挙: 新しい規定が「仕組みを外す」を `fixed` で終えてよい側にも (c) の側にも置き、ユーザーの指示の要るスコープの縮小を main だけで `fixed` にできる。設計の閉じ方: 開いている（この差分が足した規定そのもの）を受けて、規定ごと外した。commit: 44435341 |
| F2 | 独立-1 | medium | no | self-inflicted | 範囲の定義 | fixed | ① の `閉じ方: 列挙` の medium・low の `accepted` が、2 巡目以降・近道・差分（無効化後）・全レーン共通の `next-pr` と割れる。F1 の修正（足した 3 択の規定を外し、① の 2 文目を元に戻す）で原因が消えた。commit: 44435341 |
| F3 | 独立-1 | medium | no | self-inflicted | 範囲の定義 | fixed | 適用範囲外の部品の high・blocking の `列挙` が 1 巡目から `accepted` になり、②③・近道・3 巡目の「直す」と食い違う。F1 の修正（足した 3 択の規定を外し、① の 2 文目を元に戻す）で原因が消えた。commit: 44435341 |
| F4 | 独立-1 | medium | no | self-inflicted | 範囲の定義 | fixed | 「迷ったら 3 択」が迷った形を実測しない側に倒す。F1 の修正（足した 3 択の規定を外し、① の 2 文目を元に戻す）で原因が消えた。commit: 44435341 |
| F5 | 独立-1 | low | no | self-inflicted | 範囲の定義 | fixed | 列挙: 入力でない形の修正に (a) の誤 block の実測が写っていない。F1 の修正（足した 3 択の規定を外し、① の 2 文目を元に戻す）で原因が消えた。commit: 44435341 |
| F6 | 独立-1 | low | no | self-inflicted | 文言 | fixed | ADR の追記の「全 reviewer の全 finding」が広すぎる。追記を書き直すときに `concrete fix` に直した。commit: 44435341 |
| F7 | 独立-1 | low | no | self-inflicted | 文言 | accepted | `設計の閉じ方:` の位置を 2 つの出力形式だけで書き、それ以外（security reviewer の companion lane）の既定が無い |
| F8 | 独立-1 | low | no | self-inflicted | 配線 | fixed | 再掲の例外に、`列挙` で `accepted` にした medium・low が入っていない。F1 の修正（足した 3 択の規定を外し、① の 2 文目を元に戻す）で原因が消えた。commit: 44435341 |
| F9 | 独立-1 | low | no | self-inflicted | 文言 | fixed | 「直し続けず」が 1 巡目から `accepted` にする新しい規定と合わない。F1 の修正（足した 3 択の規定を外し、① の 2 文目を元に戻す）で原因が消えた。commit: 44435341 |
| F10 | 独立-1 | advisory | no | self-inflicted | 文言 | accepted | 旧#403 の断片が `設計の閉じ方` の位置の古い書き方のまま。リリースのときに版の節で直す |
| F11 | 独立-1 | advisory | no | self-inflicted | 記録 | accepted | Skill RED-GREEN Evidence が PR 本文にあるかを確かめられない（PR 本文に書く） |
| F12 | 独立-1 | advisory | no | self-inflicted | 記録 | accepted | `列挙:` の記録では、入力者の実測と 3 択のどちらで決めたかを見分けられない |
| F13 | 独立-2 | medium | no | self-inflicted | 文言 | accepted | ADR :51 と PR 本文の限界 1 は、入力の形でない `列挙` に既定が無く方針メモ-N で決めると書くが、CLAUDE.md :89・:92・:128 の文面では規律 C の入力者を測れないので既定は (b)。PR 本文の限界は文面に合わせて書いた（ADR は限界として残す） |
| F14 | 独立-2 | low | no | self-inflicted | 文言 | accepted | ADR :51 の「方針メモ-N で決める」が、同じ ADR :39 で却下した「PR ごとに方針メモで決める」と食い違って読める |
| F15 | 独立-2 | low | no | inherited | 文言 | accepted | ADR :27 の `列挙` の注釈「列挙でしか閉じない」が、修正案が閉じないことを指す新しい定義と合わない |
| F16 | 独立-2 | advisory | no | inherited | 範囲の定義 | accepted | ① の `accepted` の側の条件が main の判断で、送る側（reviewer の固定フィールド）と軸が 2 つある。規定の境界の型の `列挙` は 1 巡目で直す側に入る |
