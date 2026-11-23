---
lane: L1
pr: 461
follow_up_of: 455
amends: 20261013-merge-intent-followup.md
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | a9ace500 | 0 | 0 | 0 | 2026-10-13 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 399c508c | 0 | 0 | 0 | 2026-10-13 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| I1-1 | 独立-1 | low | no | self-inflicted | intent | fixed | 依頼の 3 行目の「encode の条件は前の PR の断片にだけ書き、この PR の断片は言及だけ」を扱っていない。前の PR の断片から、前の断片を書き足したという言及を消した。commit: 4195836b |
| I1-2 | 独立-1 | low | no | self-inflicted | docs | fixed | VERSIONING.md の「判定の分岐は test_changelog_fragments.py が固定する」に amends: のテストが無い。commit: 4195836b |
| I1-3 | 独立-1 | low | no | self-inflicted | docs | fixed | 検査の冒頭の文に、同じパス・同じ type: の条件が無い。commit: 4195836b |
| I1-4 | 独立-1 | low | no | self-inflicted | docs | fixed | 変更断片の Affected Files に、amends: で書き換えた断片とテストが無い。commit: 4195836b |
| I1-5 | 独立-1 | low | no | inherited | product | fixed | head を読めないときの `gh run list --commit <head>` が shell に貼るとリダイレクトになる。commit: 4195836b |
| I1-6 | 独立-1 | low | no | inherited | product | accepted | 列挙: steering write guard の size deny の文も plugin のパスを置き換えずに載せる。plugin のパスを理由文に載せる箇所は列挙でしか閉じず、依頼の範囲の外（PR 本文の限界に書く） |
| I1-7 | 独立-1 | low | no | self-inflicted | style | fixed | wait_loop_gate.py の import の後に空行が無い。commit: 4195836b |
| I1-8 | 独立-1 | advisory | no | self-inflicted | docs | accepted | 「制御文字・surrogate」は Cf・Zl・Zp も含む判定の略し方（PR 本文に列挙） |
| I1-9 | 独立-1 | advisory | no | inherited | docs | accepted | wait-until.py の docstring は `<plugin>` の placeholder を使う（記録のみ。PR 本文に列挙） |
| I2-1 | 独立-2 | low | no | inherited | test-power | accepted | head を読めるときの `--commit <sha>` を固定する assert が無い（PR 本文の限界に書く） |
| I2-2 | 独立-2 | low | no | self-inflicted | docs | accepted | この PR の断片の Summary に、同じパス・同じ type: の条件が無い（PR 本文の限界に書く） |
| I2-3 | 独立-2 | low | no | self-inflicted | docs | accepted | 前の PR の断片の Affected Files に、言及を消した断片が説明なしで残る（PR 本文の限界に書く） |
| I2-4 | 独立-2 | advisory | no | self-inflicted | intent | accepted | `<head>` の置き換えは依頼の行の文字どおりの範囲より広い（同じ型。PR 本文に列挙） |
| I2-5 | 独立-2 | advisory | no | self-inflicted | intent | accepted | encode の条件の扱いは言及を消す側で閉じた（記録のみ） |
| I2-6 | 独立-2 | advisory | no | self-inflicted | product | accepted | headRefOid が空なら `--commit ""` で絞らずに出る（未測。PR 本文に列挙） |
| I2-7 | 独立-2 | advisory | no | inherited | docs | accepted | 「改名は FAIL」は書き換えを伴う改名に限る言い方が正確（PR 本文に列挙） |
| I2-8 | 独立-2 | low | no | self-inflicted | docs | fixed | PR 本文のテストの列挙に head を読めないときのテストが無い。commit: なし（PR 本文） |
