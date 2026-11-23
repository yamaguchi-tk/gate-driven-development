---
lane: L1
pr: 216
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 8d77948145724aff5103a61f0b4a1b76b3495e78 | 0 | 1 | 0 | 2026-09-28T23:20+09:00 |
| 独立-2 | light-lane-independent-reviewer, 差分, model: opus | af9be0da1ace5243b19583ed766604496e36298c | 0 | 0 | 0 | 2026-09-29T00:25+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| M1 | 独立-1 | medium | no | self-inflicted | test-power | fixed | 見出しの assert を件数なしの正規表現に緩め、新しいテストは行の不在だけを見ていたので、件数 30 と閾値 1 秒をどのテストも固定していなかった。見出しを `slowest 30 durations` に戻し、`durations < 1s hidden` を assert した（3879a2e2。閾値 2.0・件数 5 に変えると落ちることを確かめた）。差分が assert の緩和を含んでいたので、近道ではなく通常の巡として扱う |
| L1 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | テストの module docstring が `--durations-min` に追随していなかった（3879a2e2） |
| L2 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 同じ版の既存断片が「上位 30 件を毎回出す」と書いたまま。既存断片は書き換えられないので、新しい断片に前後の変化を書いた（3879a2e2）。既存断片の文は次のリリースで版の節を直す |
| L3 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | `-vv` では 1 秒未満が出なくなったことが書かれていなかった。CONTRIBUTING と断片に `--durations-min=0` を書いた（3879a2e2） |
| L4 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | 断片の Validation に「見出しのテストは件数を写さない正規表現にした」が残り、件数 30 を固定した実物と逆だった。文を消した（62e6a098）。差分巡の low は next-pr だが、断片は後続の PR で書き換えられないので、旧#215 の F1 と同じくこの PR で直した。changelog.d だけの commit なので巡は無効にならない |
| A1 | 独立-2 | advisory | no | inherited | test-flake | accepted | 速いテストの標本（test_git_fixture_contract.py）が CI の負荷で 1 秒を超えると、durations の行が出てテストが揺れる。落ちた実績は無い。出たら標本を I/O をしないテストに替える |
