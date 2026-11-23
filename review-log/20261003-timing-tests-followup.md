---
lane: L1
pr: 309
follow_up_of: 296
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | b633ada1000cce7002d7974e062463196a067528 | 0 | 0 | 0 | 2026-10-03T23:15+09:00 |
| 独立-2 | light-lane-independent-reviewer, 差分, model: opus | 802402bdc185f591173f76abcd3becc491ed4338 | 0 | 0 | 0 | 2026-10-03T23:55+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| P1 | 独立-1 | low | no | self-inflicted | test-power | fixed | 解析時間のテストが CPU 時間だけになり、壁時計の上限が無くなった。ADR X-37 の二本立てにそろえ、hook の timeout の半分を backstop にした commit: 802402bd |
| P2 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | ADR X-37 が却下した「CPU 時間だけ」の形を採っていた。二本立てにして ADR に合わせた commit: 802402bd |
| P3 | 独立-1 | advisory | no | self-inflicted | test-power | accepted | pre-PR gate の FIFO テストの打ち切りが 20 秒から 10 秒になった。-n auto で 4.6 秒（baseline を含む）。PR 本文に書く |
| P4 | 独立-1 | advisory | no | inherited | doc-claim | accepted | コメントに hooks.json の timeout の literal（10 秒）が残る。PR 本文に書く |
| P5 | 独立-1 | advisory | no | self-inflicted | doc-claim | fixed | PR 本文が HANG_GUARD のコメントも書き直したと読める commit: なし（PR 本文） |
| P6 | 独立-1 | advisory | no | self-inflicted | test-power | accepted | CPU 時間に替えたテストが退行で落ちることを確かめた記録が無い。PR 本文に書く |
| R1 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 「CPU を使わずに止まる退行を拾う」が戻らない停止まで含むように読める。PR 本文の限界に書く |
| R2 | 独立-2 | low | no | inherited | test-power | accepted | cd_after_merge の解析時間テストだけ壁時計の backstop が無い。PR 本文の限界に書く |
| R3 | 独立-2 | low | no | self-inflicted | style | accepted | 足した壁時計の assert が CPU より先に評価され、メッセージに CPU の値が無い。PR 本文の限界に書く |
| R4 | 独立-2 | advisory | no | self-inflicted | style | accepted | backstop の定数と assert が複数のファイルに複製されている。PR 本文に書く |
| R5 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | ADR X-37 の既知の穴と後続タスクが、この PR で閉じた分を反映していない。PR 本文に書く |
| R6 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | 限界に、極端な負荷では backstop でなお落ちうることが無い。PR 本文に書く |
| R7 | 独立-2 | advisory | no | inherited | style | accepted | テスト名の「1 秒」がいまは CPU 時間の閾値。PR 本文に書く |
