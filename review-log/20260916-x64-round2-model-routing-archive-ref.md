---
lane: L1
pr: 95
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ | PR 旧#89 独立レビュー round 2（範囲外 advisory 指摘） | - | 0 | 0 | 0 | 2026-09-16T20:42+09:00 |
| PR後-1 | GitHub PR 旧#95 review (yamaguchi-tk) | 28aa18dc4a26b3ad2a4963027431231e4fdb368b | 0 | 1 | 0 | 2026-09-16T22:46+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| F1 | 方針メモ | advisory | no | inherited | archived-reference-drift | fixed | gdd-model-routing/SKILL.md が退避済み docs/references-archive/autonomous-model-workers.md を現役参照先として案内していた（X-55 と同型） |
| F2 | PR後-1 | medium | no | self-inflicted | scope-description-accuracy | fixed | PR本文の「スコープ」段落が references/requirements-template.md:117 と scripts/lint-ac.py:64,261（同型の archive 誤参照）を見落としており、読み手が「残りは全部履歴」と誤読しうる状態だった |
| F3 | PR後-1 | low | no | self-inflicted | test-naming-nit | accepted | test_x64_fable_remnant_cleanup_contract.py への並置は保守性のnitで、既存のX-55同型テストと同じ置き場のため現状維持 |
| F4 | PR後-1 | low | no | inherited | source-of-truth-map-prefix-guard-gap | accepted | prefixなしの `references-archive/` 再導入を検出しないのは SOURCE_OF_TRUTH_MAP 側の既存の穴で、今回の回帰対象（`docs/references-archive/` リテラル）とは別軸のため今回は対象外 |
