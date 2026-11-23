---
lane: L1
pr: 旧#212
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 94554399d95537f16c98018deb6d54a26f794aee | 0 | 0 | 0 | 2026-09-28T22:30+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| L1 | 独立-1 | low | no | self-inflicted | local-output-cost | next-pr | 手元で関係するテストを回すたびに一覧の最大 30 行が出力に加わり、agent の文脈に積まれる。近道の ① の blocking でない low なので、次の PR で `--durations-min=1.0` を足す |
| L2 | 独立-1 | low | no | inherited | doc-claim | out-of-diff | PR 本文の pytest step 約 6.5 分と、CONTRIBUTING.md:83・CLAUDE.md:104 の「ジョブ約 5 分」が合わない。後者は過去の日付の実測で、差分の外。PR 本文には測った日付と run を書いた |
| A1 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 「上位 30 件」は 30 テストではなく setup・call・teardown の 30 行で、位置も末尾ではなく集計行の手前。次の PR で L1 と一緒に書き方を直す |
| A2 | 独立-1 | advisory | no | self-inflicted | test-power | accepted | 新しいテストが件数 30 を写している。次の PR で `slowest \d+ durations` の正規表現にする |
