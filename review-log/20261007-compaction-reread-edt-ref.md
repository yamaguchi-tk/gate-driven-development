---
lane: L1
pr: 398
follow_up_of: 397
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 1db3b7d4 | 0 | 0 | 0 | 2026-10-07T00:00+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| R1 | 独立-1 | low | no | inherited | 参照元 | accepted | state-machine.md:375 の Root Cause Tag の行も「escalation table 2 行目」と行番号で指していて、ずれている |
| R2 | 独立-1 | low | no | self-inflicted | compaction | accepted | common-guardrails.md:132 の「route 判断なら state.md + tasklist.md」の例が、読み直しを足した skill と合わない |
| R3 | 独立-1 | low | no | self-inflicted | compaction | accepted | rationalization-root-causes.md:99 の対抗策が、route 判定の前に読み直すものを 2 ファイルのまま挙げている |
| R4 | 独立-1 | low | no | inherited | 書き手 | accepted | Root Cause Tag には書く手順が skill に無く、参照を直しても判定には効かない |
| R5 | 独立-1 | advisory | no | self-inflicted | 文言 | accepted | 468 行の理由の文に、足した読み直しの理由（方式転換の判定）が無い |
| R6 | 独立-1 | advisory | no | self-inflicted | 計測 | accepted | 読み直しは散文の指示で、守られるかは測っていない |
