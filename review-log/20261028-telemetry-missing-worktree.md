---
lane: L1
pr: 600
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 06447303caa47295e17a2619b39ac370a3b98b43 | 0 | 1 | 0 | 2026-10-28T13:10+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| r1-1 | 独立-1 | medium | no | self-inflicted | request-drift | fixed | 週次分析の【6】の 1 点目（GDD を使う別の repo の小さいタスクの gate 費用の比）を、確認なしに対象外にしていた。行き先（旧#567 の前後で gate ごとの費用を測る調査）を PR 本文に書いた。Opus・Fable の相談役も同じ案。commit: なし（PR 本文） |
| r1-2 | 独立-1 | low | no | self-inflicted | test-power | accepted | 消えた worktree の後に残っている linked worktree が fixture に無く、「残りを集計する」を固定していない |
| r1-3 | 独立-1 | low | no | self-inflicted | test-power | accepted | 警告の文言を、パスの部分一致でしか見ていない |
| r1-4 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | docstring と --include-worktrees の help が、消えた worktree を飛ばすことを書いていない |
| r1-5 | 独立-1 | advisory | no | self-inflicted | product | accepted | 飛ばした worktree が JSON・CSV に残らない |
| r1-6 | 独立-1 | advisory | no | self-inflicted | product | accepted | git worktree list が失敗したときは警告を出さない（差分より前から） |
| r1-7 | 独立-1 | advisory | no | self-inflicted | style | accepted | 共有の git fixture（init_repo）と subprocess の timeout を使っていない |
