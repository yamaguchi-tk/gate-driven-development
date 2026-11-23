---
lane: L1
pr: 旧#252
follow_up_of: 248
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 4a865a4e6e940f648d1c349f37939343a888dc7e | 0 | 0 | 0 | 2026-09-30T13:30+09:00 |
| 独立-2 | light-lane-independent-reviewer, 差分, model: opus | ef09f3c98648c29d6e73d6decc48019e73c32562 | 0 | 0 | 0 | 2026-09-30T14:00+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| F1 | 独立-1 | low | no | self-inflicted | acceptance-set-asymmetry | fixed | Gate Batch の行の注記（(after T-3)）の task id まで batch に数え、同じ提案が 2 回出たり別の batch の提案が消えたりした。各項目の先頭の id だけを読み、2 つの行に出る id は batch に入れない。commit: d1e57f83 |
| F2 | 独立-1 | low | no | self-inflicted | test-power | fixed | Execution Plan 節だけを読むことをテストが固定しておらず、節の切り出しを外す変異が通った。節の外の Gate Batch の行を読まないテストを足した。commit: 9e200068 |
| F3 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 区切りの正本として名指しされたテストの docstring に、Gate Batch の task を batch でまとめる規定が無かった。区切り 4 に書き足した。commit: 9e200068 |
| F4 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 断片の「これまでは最大 3 回出ていた」が、未リリースの Gate Batch の途中の状態を指す |
| F5 | 独立-1 | advisory | no | self-inflicted | product | accepted | 記録キーが batch の番号だけで、番号が steering の中で一意だという規定が無い（振り直すと新しい batch の提案が出ない） |
| F6 | 独立-1 | advisory | no | self-inflicted | style | accepted | テストの fixture の組み立て（_tasklist の replace）が 3 か所で重複している |
| F7 | 独立-2 | low | no | self-inflicted | acceptance-set-asymmetry | accepted | カッコの中にカンマを含む注記（(after T-3, T-4)）の 2 つ目以降の id を batch の一員に数え、単独の task の Round 3 で batch の記録が埋まり、batch の提案が 1 回消えることがある |
| F8 | 独立-2 | low | no | self-inflicted | test-power | accepted | 「Execution Plan 節の外を読まない」テストの fixture に Execution Plan 節が無く、節の終わりの境界を外す変異が通る |
| F9 | 独立-2 | low | no | self-inflicted | style | accepted | 項目の先頭の task id の正規表現が、_task_blocks の既存の正規表現と同じもので 2 つある |
| F10 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 断片の Summary と Validation に、項目の先頭の id だけを読む規則と足したテスト 2 本が書かれていない |
| F11 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | PR 本文の「注記の中の id は task ごとのまま」がテストの期待（その行の batch に数えない）と違った。PR 本文を直した。commit: なし（PR 本文） |
| F12 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | docstring の「2 つ以上の行に出る id」と、同じ行の重複も外す実装がずれている |
| F13 | 独立-2 | advisory | no | self-inflicted | product | accepted | 全角の読点・空白区切り・バッククォート付きの行は、先頭の id だけを読むか何も読まない（提案が task の数だけ出る側） |
