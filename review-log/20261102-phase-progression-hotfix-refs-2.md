---
lane: L1
pr: 630
follow_up_of: 629
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 570fb4a9 | 0 | 0 | 0 | 2026-11-02 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| I1-1 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | stub.md の雛形に足した行のコメントが置き場所を root state.md と書くが、state-machine.md:311 は Abandoned Hotfix Attempts を Hotfix Lane 側の state.md に持つと定める |
| I1-2 | 独立-1 | low | no | inherited | product | accepted | phase-progression.md:600 は archive 前の正本を root state.md とするが、root state.md に書き込む規定が無く、archive 後の件数閾値（3 件）が少なく数えられうる |
| I1-3 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 変更断片の検証欄のコマンドが `--run` だけで、`. origin/main` を欠き、書いたとおりでは usage で終わる |
| I1-4 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 断片と PR 本文が、変えた 357 行目を「batch の hotfix 退避の手順」と呼ぶが、文書の語では Case 2（緊急明示時の手動 Hotfix 起動）に当たる |
| I1-5 | 独立-1 | advisory | no | inherited | bookkeeping | accepted | このブランチに PR 旧#628・旧#629 の変更が入っていない。変える行は離れていて衝突しない |
| I1-6 | 独立-1 | advisory | no | inherited | bookkeeping | accepted | 後続 PR の連鎖の 4 本目に当たり、CLAUDE.md の「3 本目のマージ後、4 本目を作る前に残りを 1 本にまとめるかを問う」の記録が無い |
