---
lane: L1
pr: 363
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 3c3b91605456b1c1c7eb51c4b23594eb1b494292 | 0 | 0 | 0 | 2026-10-04T22:40+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| A1 | 独立-1 | medium | no | self-inflicted | doc-claim | next-pr | `CONTRIBUTING.md:89` が pytest.ini の addopts を字句どおり再掲しており、`--maxprocesses=8` が入っていない。上限と `--maxprocesses=N` での変え方も書かれていない |
| A2 | 独立-1 | low | no | self-inflicted | doc-claim | next-pr | 明示の `-n N`（8 より大きい）も警告なしに 8 へ丸められることが、ini のコメント・断片・PR 本文に書かれていない |
| A3 | 独立-1 | low | no | self-inflicted | test-power | next-pr | 子のテストの `<= 8` は、32 コアの差し替えが効いたことを固定しない。`== 8` にすれば空振りと上限の引き下げも検出できる |
| A4 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 「論理 CPU 数」は psutil が入っていると物理コア数になる。PR 本文に書く |
| A5 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | ini のコメントとテストの docstring の負荷平均 40 に、背景負荷の中の参考値という但し書きが無い。PR 本文に書く |
| A6 | 独立-1 | advisory | no | self-inflicted | product | accepted | テストが子で 8 worker を 2 回起動し、一時的に負荷を上げる。PR 本文に書く |
| A7 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 宣言された xdist の下限 3.2 に `--maxprocesses` と `PYTEST_XDIST_AUTO_NUM_WORKERS` があるかは未確認。PR 本文に書く |
