---
lane: L1
pr: 旧#187
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 990ab36aadba13c4f5638b1228b48d0348ab6ef9 | 0 | 0 | 0 | 2026-09-28T12:30+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| F1 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 断片の Summary と PR 本文の目的が「残りを直した」「残っていた 2 か所」と完全性を言い切っていた（13 本の skill の `## Fixed Model` 節は `Sonnet` のまま）。直した 2 か所の名指しに縮めた（断片と PR 本文だけの修正。規則の文書・判定のコードは変えていない） |
| F2 | 独立-1 | low | no | inherited | style | next-pr | 13 本の skill の `## Fixed Model` 節が Claude Code の起動モデルを `Sonnet` と書いていて、tier 表の `sonnet` と揃っていない（`fixed-models.md:97`）。次の PR で揃える。F4 を先に決める |
| F3 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | PR 本文の草案が「2 行下」（実際は 3 行下）と書き、`fixed-models.md` の規定を「表は alias で書く」と広げて引用していた。PR 本文を原文に合わせた（PR 本文だけの修正） |
| F4 | 独立-1 | low | no | inherited | doc-claim | next-pr | `gdd-requesting-code-review` の `## Fixed Model` が Claude Code を `Sonnet` + medium（dispatcher なので軽い）としているが、`resolve-gdd-model.py:227` と `gdd-model-routing` の表は general_heavy（`opus` + high）。次の PR でどちらを正本にするか決める |
