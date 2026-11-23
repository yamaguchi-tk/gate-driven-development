---
lane: L1
pr: 旧#204
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 2670cd78eb40ae278300516aef7114ac24bed0ab | 0 | 0 | 0 | 2026-09-28T16:20+09:00 |
| 独立-2 | light-lane-independent-reviewer, 差分（無効化後）, model: opus | eb6a75f5a8af4465ae62af365b6374164f11f16d | 0 | 1 | 0 | 2026-09-28T17:05+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| C1 | 独立-1 | low | no | self-inflicted | measurement-wording | fixed | `CLAUDE.md:54` の実測値「55 本（README を除く）」「誘導・抑制に当たりうるものは実行結果の断定 1 件」に時点と数えた基準が無く照合できない（今の review-log は 61〜62 本。同じ手順 6 には同じ日付の「46 本」もある）。時点の sha と該当行を添えた（2c11dafe。`a00e872d` 時点で数え直し 62 本、報告 9 件は不変）。近道では next-pr だが、この PR の目的（実測値の訂正）そのものなので Fable への相談を経て直した |
| C2 | 独立-1 | low | no | self-inflicted | test-power | fixed | 手順 6 の冒頭の assert が「…有効な独立レビューに数える」で終わり、後ろの区切りを固定していない（「数えるとは限らない」に変えても通る）。「（扱いは下の報告の行のとおり）」まで延ばした（a941850c。テストを強める変更で巡は無効にならない） |
| C3 | 独立-2 | medium | no | self-inflicted | measurement-wording | deferred | `CLAUDE.md:54` の実測値が語の grep の件数になっている。要約に「テンプレート外」の語を含まない同じ種類の報告の行が少なくとも 12 行あり、分類で数えると報告 21 件・誘導・抑制に当たりうるもの 3 件（`20260920-typed-dispatch-templates.md:145`・`:158` を含む）。規定の結論は変わらない。旧#180 からの「次の PR」連鎖（7 本目）を閉じるため、Fable への相談を経て、ユーザーの自律進行の指示を後回しの指示として扱い deferred にした（Issue 旧#202。いつ直すか: next-pr の連鎖を止める規定を足す PR と同時に） |
| C4 | 独立-2 | advisory | no | inherited | template-outside-harness | accepted | `advisory: テンプレート外の記述あり`。harness が差し込んだ gitStatus の直近 commit の件名（巡の ID と修正を含む）と、reflog の件名。判断には使っていない。main が取り除けない経路で、PR 本文の限界に開示済み。手順 6 のとおり巡は有効のまま |
