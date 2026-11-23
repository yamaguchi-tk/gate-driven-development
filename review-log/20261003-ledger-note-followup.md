---
lane: L1
pr: 329
follow_up_of: 319
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 4daa1d0cb048b597ff85e12b306565c5a36b7c11 | 0 | 0 | 0 | 2026-10-03T02:10+09:00 |
| 独立-2 | light-lane-independent-reviewer, 差分, model: opus | 83eaa4611b3c0f9b49181b46f188e0e8ab0ca7f7 | 0 | 0 | 0 | 2026-10-03T01:50+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| P1 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 注記の出口に、ほかの 9 か所の入口がそろって持つ「どれを終えるかユーザーに確認する」前提が無い commit: 83eaa461 |
| P2 | 独立-1 | low | no | inherited | doc-claim | accepted | 前の PR の未リリース断片（20261003-ledger-multiple-note.md）が注記の比べ方を逆向きに書いている。他の PR の断片は書き換えず、リリースの dry-run で版の節を直す |
| P3 | 独立-1 | low | no | self-inflicted | test-power | fixed | 比べる向きを元に戻してもテストが落ちず、「詳細の最後」はテストが確かめる範囲より広い言い方 commit: 74d44f76 |
| P4 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | コメントの実測のコマンドは grep -c に -H が無く、除外と数え上げが括弧の説明にしかない commit: 83eaa461 |
| P5 | 独立-1 | advisory | no | self-inflicted | test-power | accepted | 新しいテストが pre-PR の hook と突き合わせていない |
| Q1 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 注記の出口が steering を終えることだけで、0 件のとき（push する steering の証跡がまだ tip を指さない）の普通の出口（tip の sha で証跡を書く）が無い |
| Q2 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 実測のコメントは「直近 30 日」と書くが、block 文の書き出しが 09-28 からなので、数えた期間は実際には 09-28 以降。件数は文を含む transcript の数で、block の回数の上限 |
| Q3 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | PR 本文の「そのまま走らせて同じ件数になる形」は、同じ端末で同じ時期に走らせたときだけ成り立つ commit: なし（PR 本文） |
| Q4 | 独立-2 | low | no | self-inflicted | test-power | fixed | テストは出口の「PR が open のものは除く」を固定しておらず、PR 本文の「出口をテストで固定した」は広すぎる。PR 本文を狭めた commit: なし（PR 本文） |
| Q5 | 独立-2 | low | no | inherited | doc-claim | re-reported | 前の PR の未リリース断片が注記の比べ方を逆向きに書いている（P2 の再掲） |
