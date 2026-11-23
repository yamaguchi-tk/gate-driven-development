---
lane: L1
pr: 390
follow_up_of: 388
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 52d5b869 | 0 | 2 | 0 | 2026-10-06T21:27+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| F1 | 独立-1 | medium | no | self-inflicted | 範囲の定義 | accepted | 影響節を誰が列挙するかが無く、reviewer は参照: 行の節しか読まないので、影響節を読まないか計画 doc を探すかが決まらない |
| F2 | 独立-1 | medium | no | self-inflicted | 範囲の定義 | accepted | 影響節が節単位なので、受入条件の 1 行を直すと全 AC を引く節が範囲に入り、再入の範囲が Round 1 と同じに戻る |
| F3 | 独立-1 | low | no | self-inflicted | 範囲の定義 | accepted | agent 定義の再入の定義に human check をまたいだ Round の除外が無い。観点レーンの見出しが「Round 1 では」のまま |
| F4 | 独立-1 | low | no | self-inflicted | 範囲の定義 | accepted | 「同じエピソードの」が落ち、human check の後に番号を続けた Round が再入に当たる |
| F5 | 独立-1 | low | no | self-inflicted | 文言 | accepted | 前の断片に「2 回目の Round」の定義が残り、版の節で 2 通りの説明になる |
| F6 | 独立-1 | low | no | self-inflicted | 計測 | accepted | reviews.md の見出しの所要の欄に 不明 の選択肢が無い。1 Round に起動が複数あるときの値が決まらない |
| F7 | 独立-1 | low | no | self-inflicted | 計測 | accepted | 計れないときの 不明 が reviews.md にだけ掛かり、Attempts に掛からない |
| F8 | 独立-1 | low | no | self-inflicted | 範囲の定義 | accepted | 初回でも再入でもない design の Round で 1 枚の中身が決まらない |
| F9 | 独立-1 | low | no | inherited | 範囲の定義 | accepted | design で最後の Round の後に直した advisory の high を誰もレビューしない |
| F10 | 独立-1 | low | no | self-inflicted | 文言 | accepted | 変更断片に、この変更ではない内容（前の変更の記録）が書かれている |
| F11 | 独立-1 | advisory | no | self-inflicted | 文言 | accepted | User Action Required に、agent 定義はセッションを開き直してから効くことが無い |
| F12 | 独立-1 | advisory | no | self-inflicted | 文言 | accepted | RED-GREEN の記録が PR 本文の抜粋に無い（PR 本文の Skill RED-GREEN Evidence に書く） |
