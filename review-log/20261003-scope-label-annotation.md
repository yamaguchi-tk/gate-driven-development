---
lane: L1
pr: 317
follow_up_of: 311
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 3c1bcf81e285f412abeaef08f56f1d0890d2236b | 0 | 0 | 0 | 2026-10-03T18:20+09:00 |
| 独立-2 | light-lane-independent-reviewer, 差分, model: opus | 4d2026c4ed521e9d110c11e52a04d68c613b1a21 | 0 | 0 | 0 | 2026-10-03T19:00+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| F1 | 独立-1 | low | no | self-inflicted | product | fixed | 括弧の中身を問わないので `自走範囲（補足）:` も自走範囲の行になり、PR 本文・断片の「別の欄は今までどおり」と食い違う。広い側のまま、断片と PR 本文に書き、テストで固定した commit: 4d2026c4 |
| F2 | 独立-1 | low | no | inherited | test-power | fixed | 欄名と値の間に空白が無いと欄名が語にくっつき、`自走範囲=**/auth/**` の WARN が出ない。自走範囲の行は欄名を外した値だけを語に分ける commit: b907ccd9 |
| F3 | 独立-1 | low | no | self-inflicted | test-power | fixed | 注記つき・`=` の欄名の続きの行を読むことをテストが固定していない commit: 5072ba44 |
| F4 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 断片の User Action Required が「なし」だが、注記つきの欄名の単一ファイルで新しく ERROR が出る commit: 4d2026c4 |
| F5 | 独立-1 | low | no | inherited | test-power | accepted | 見出しの形の glob の欄と `自走上限` の欄名は、注記と `=` を受けない。欄名の書き方は並べ尽くせない開いた入力なので、限界に書いてユーザーに確認する |
| F6 | 独立-1 | low | no | inherited | test-power | accepted | 太字・番号付きの箇条・`[]`・`【】` の注記、全角コロンの `Approved Direction：` は読まない。開いた入力なので、限界に書いてユーザーに確認する |
| F7 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 「どの拡張子の単一ファイルも」は、英字で始まる拡張子だけが正しい（断片は書き直した） |
| F8 | 独立-2 | low | no | self-inflicted | test-power | accepted | 括弧の注記の中身を語に分けなくなり、`自走範囲（scripts/foo.py の修正）:` の注記の単一ファイルを検査しない（main は ERROR） |
| F9 | 独立-2 | low | no | inherited | product | accepted | 注記の中身を問わないので、`自走範囲（外）:`・`自走範囲（対象外）:` の除外の一覧も ERROR になる |
| F10 | 独立-2 | low | no | inherited | test-power | accepted | 入れ子の注記つきの欄名が外側の自走範囲の字下げを上書きし、後ろの続きの行の `main.go` を検査しない（main は ERROR） |
| F11 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | テストの docstring と未リリースの別の断片に「どの拡張子の単一ファイルも ERROR」が残る |
| F12 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 欄名を外すのが `自走範囲` の行だけであることがコメントと限界から読めず、`戻し条件=**/auth/**` の WARN が出ないことが書かれていない |
