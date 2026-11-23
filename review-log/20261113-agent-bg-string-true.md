---
lane: L1+
pr: 662
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ | Opus 設計レビュー ×2 (gate-driven-development:gdd-opus-advisor, model: opus) + user | 247b0d102f2140196464eca063096d1e09a311d8 | 0 | 2 | 0 | 2026-11-13 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus（general-purpose で定義本文を貼って起動。effort は main から継承） | d28f4d7f36a3aff27fa50e3bfdc85eaf39d54bd1 | 0 | 0 | 0 | 2026-11-13 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| M-1 | 方針メモ | medium | no | self-inflicted | same-input-readers | fixed | 設計: 変えない（実測で Bash の timer は bool だけ）。同じ欄を読む transcript.py:178 を測らずに除外していた。Bash の sleep N の run_in_background を数え 2,321 件すべて bool・文字列 0 件で、直さない根拠を PR 本文に書いた。commit: なし（PR 本文） |
| M-2 | 方針メモ | medium | no | self-inflicted | review-material | fixed | 相談に渡した差分を origin/main..HEAD で取り、進んだ main の変更が巻き戻しとして混ざっていた。merge-base からの差分で取り直した（ブランチ自体に巻き戻しは無い）。commit: なし（材料のみ） |
| M-3 | 方針メモ | low | no | self-inflicted | doc-claim | fixed | hook のコメント・テストの docstring・断片が、host の型変換の推定を事実として書いていた。観測と推定に分けた。commit: d28f4d7f |
| M-4 | 方針メモ | low | no | self-inflicted | qa | fixed | QA を「マージ前は測れない」としていた。拒否された実際の入力 3 件を worktree の hook の入口に通し、3 件とも通過・"True" の対照は拒否を確かめた。commit: なし（確認のみ） |
| M-5 | 方針メモ | advisory | no | inherited | symmetry | accepted | wait_loop_gate.py:45 も run_in_background を is True で読む。Bash は bool で届く実測なので今回は揃えない |
| I1-1 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | PR 本文が transcript.py の読み手を Bash だけと書いていた。git_pre_push_review.py:158（log だけの pre-push、reviewer の Agent 起動で agentId が読めないときだけ）も読むと書き直した。commit: なし（PR 本文） |
| I1-2 | 独立-1 | low | no | inherited | symmetry | accepted | transcript.py:178 が is True で読むので、文字列の "true" で起動し agentId が読めない reviewer を pre-push の log で ok と書きうる。log のみ |
| I1-3 | 独立-1 | advisory | no | inherited | symmetry | accepted | wait_loop_gate.py:45 の受理集合が非対称。Bash は bool で届く実測 |
| I1-4 | 独立-1 | advisory | no | self-inflicted | fail-open | accepted | 文字列の "true" が届くのに同期で動く host があれば watchdog が当たらない。実測では見つからず、PR 本文の限界に記載 |
| I1-5 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | テストの docstring の「比較で例外になりうる値」は実際には例外にならない |
