---
lane: L1
pr: 464
follow_up_of: 458
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 8c6a25053824a8a79483bd3f85dbbc2909e791e0 | 0 | 0 | 0 | 2026-10-13T17:30+09:00 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | a3ca97f74a80fc6b88957ea48f1d170e83ff9a73 | 0 | 0 | 0 | 2026-10-13T18:10+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| K1 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 断片・テストの docstring・PR 本文が「提案が出るようになった」と読めるが、変わるのは gh への問い合わせが 1 回増えることだけ（branch 名は \\uXXXX に置き換わり実在しない）。書き直した。commit: c6e2afa4 |
| K2 | 独立-1 | low | no | self-inflicted | product | fixed | 判定できない push が skipped(no-pr) として記録され、"no" が 300 秒キャッシュされることを開示していない。断片と PR 本文の限界に書いた。commit: c6e2afa4 |
| K3 | 独立-1 | low | no | self-inflicted | test-power | fixed | テストが gh に渡る branch を固定していない（書けない行を捨てる実装でも通る）。args_file で branch 名を完全一致で見るようにした。commit: c6e2afa4 |
| K4 | 独立-1 | advisory | no | inherited | product | accepted | merge gate の emit にある改行・タブの置換が、nudge と pre-push gate には無い（block しない hook で、改行を運べるのは root だけ） |
| K5 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 選択肢の説明は「書けない文字だけ backslashreplace」、実装は行全体（判定には届かない） |
| K6 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 断片と test の docstring の「lone surrogate」「branch 名は \\uXXXX に置き換わる」が広い。\\udc80〜\\udcff は直す前から byte として書けていて置き換わらず、行全体の backslashreplace で同じ名前のほかの非 ASCII も書き換わる。PR 本文の限界に書く |
| K7 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | 断片の skipped(no-pr) は gh が PR なしと応答したときだけで、gh の失敗では undeterminable（30 秒キャッシュ）になる |
| K8 | 独立-2 | advisory | no | self-inflicted | test-power | accepted | test は has-pr の stub で提案を出させており、docstring の「提案の有無は変わらない」は確かめていない（固定するのは gh に渡る名前だけ） |
