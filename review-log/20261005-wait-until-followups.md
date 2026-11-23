---
lane: L1
pr: 374
follow_up_of: 371
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | b4f01de8a596c4986736a22107716819b12da309 | 0 | 1 | 0 | 2026-10-05T13:25+09:00 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 8b88724a54754703f97323bde693831796e7e4ea | 0 | 0 | 0 | 2026-10-05T13:35+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| F1 | 独立-1 | medium | no | self-inflicted | doc-claim | fixed | post-merge-qa の完了の条件から「run が無い → まだ」が抜け、連鎖する workflow で完了を早く返す。workflow ごとに出現・完了の順に待つ形にした commit: 36f4a6d7 |
| F2 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 環境の承認待ちの run を、完了の条件では上限まで見分けられない。status が waiting なら 3 を返す形にした commit: 36f4a6d7 |
| F3 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 例外のメッセージが複数行だと、例外の名前が stderr= から消える commit: 36f4a6d7 |
| F4 | 独立-1 | low | no | self-inflicted | test-power | fixed | 別グループの前提の assert が、テストのプロセスのグループと比べていて常に真 commit: e58b8a1d |
| F5 | 独立-1 | low | no | self-inflicted | test-power | fixed | 例外のテストが -- <条件コマンド> の経路しか見ていない commit: e58b8a1d |
| F6 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | head= が整えられないまま観測行に入り、改行で最終行が割れうる commit: 36f4a6d7 |
| A1 | 独立-1 | advisory | no | self-inflicted | test-power | accepted | 止められない確認のテストに約 11 秒かかる（PR 本文に列挙） |
| A2 | 独立-1 | advisory | no | self-inflicted | style | accepted | テストの後片付けが、pidfile が無いと元の失敗を隠す・_run が落ちると子を残す（PR 本文に列挙） |
| A3 | 独立-1 | advisory | no | self-inflicted | style | accepted | 止められない確認のテストの置き場所と class の docstring が合わない（PR 本文に列挙） |
| A4 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 待ちが broken で終わったときの扱いが、手順 3 の止まる条件に無い（PR 本文に列挙） |
| G1 | 独立-2 | low | no | self-inflicted | test-power | accepted | 例外のテストが、メッセージの最後の行と行の形を固定せず、名前が残ることだけを見る（PR 本文の限界に記載） |
| G2 | 独立-2 | low | no | self-inflicted | test-power | accepted | head のテストの「last_stdout に改行が無い」の assert が常に真で、head= の値も固定していない（PR 本文の限界に記載） |
| G3 | 独立-2 | low | no | self-inflicted | ci-classification | accepted | head= の整形が入力の最後の行を採り、押し返しの 40 桁の 16 進数の検査とそろっていない（PR 本文の限界に記載） |
| G4 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 手順 3 で、承認待ちの 3 と「gh の失敗は 2 以上」が重なり、last_exit から読み分けられない（PR 本文の限界に記載） |
| G5 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | workflow ごとに順に待つと、完了の待ちの合計が QA 計画の時間の上限を超えうる（PR 本文の限界に記載） |
| A5 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | docstring の例外の説明が「例外の名前」だけで、メッセージの最後の行を書いていない（PR 本文に列挙） |
