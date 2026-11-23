---
lane: L1
pr: 306
follow_up_of: 304
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 098c723f63216812b45ff0d306229b63c9c4f4cf | 0 | 1 | 0 | 2026-10-03T21:45+09:00 |
| 独立-2 | light-lane-independent-reviewer, 差分, model: opus | 7ed82708fa15a885287cd7373d32113578311628 | 0 | 1 | 0 | 2026-10-03T22:20+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| L1 | 独立-1 | medium | no | self-inflicted | test-power | fixed | 終了コードのテストがテスト対象の定数と比べていて、値を固定していない。65・64 のリテラルにした commit: 875d8090 |
| L2 | 独立-1 | low | no | self-inflicted | product | fixed | `--` の後ろの存在しないパスを、選んだテストが 0 件のときに黙って捨てる。64 で止める commit: c9cf9d6b |
| L3 | 独立-1 | low | no | self-inflicted | product | fixed | option の値だけが足すテストのとき、位置引数なしの pytest が tree 全体を集める。足すテストを位置引数でも渡す commit: c9cf9d6b |
| L4 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | CONTRIBUTING.md 項 1 の関係するテストに helper の規則が無い commit: c9cf9d6b |
| L5 | 独立-1 | low | no | self-inflicted | product | fixed | aws-investigate の validate-plugin.sh を手で回す規則を足したのに、スクリプトが案内しない。stderr に出す commit: c9cf9d6b |
| L6 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | docstring の和集合に `--` の項目が入っていて実装と合わない。stderr の一覧に足すテストも出す commit: c9cf9d6b |
| L7 | 独立-1 | advisory | no | self-inflicted | product | accepted | `tests/__init__.py` を helper として扱う。PR 本文に書く |
| L8 | 独立-1 | advisory | no | self-inflicted | doc-claim | fixed | `__pycache__` の除外は tracked にも効くのに、文書は untracked だけと書く commit: c9cf9d6b |
| L9 | 独立-1 | advisory | no | self-inflicted | doc-claim | fixed | テストのファイルを読めない失敗も「変えたファイルを決められない」で 64 になる。文を分けた commit: c9cf9d6b |
| M1 | 独立-2 | medium | no | self-inflicted | product | accepted | `--` の後ろの option の値（`-n 0`・`--ignore <path>`・`-c <ini>`）を、足すテストか無いパスとして扱う。PR 本文の限界に書く |
| M2 | 独立-2 | low | no | self-inflicted | test-power | accepted | validate-plugin.sh の案内のテストが、誤った実装も通す。PR 本文の限界に書く |
| M3 | 独立-2 | low | no | self-inflicted | test-power | accepted | 「テストのファイルを読めない」の分岐にテストが無い。PR 本文の限界に書く |
| M4 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 断片の Validation 欄に、案内のテストの種類が無い。PR 本文の限界に書く |
| M5 | 独立-2 | advisory | no | self-inflicted | product | accepted | 足すテストが pytest に 2 回渡る（pytest 9 は重複を除く）。PR 本文に書く |
| M6 | 独立-2 | advisory | no | self-inflicted | style | accepted | テストで commit の後に同じ内容で書き直している。PR 本文に書く |
| M7 | 独立-2 | advisory | no | inherited | doc-claim | accepted | usage 文が足すテストの規則に追随していない。PR 本文に書く |
| M8 | 独立-2 | advisory | no | inherited | doc-claim | accepted | 名前の切り出し方が CLAUDE.md とスクリプトで違う（スクリプトが広い）。PR 本文に書く |
