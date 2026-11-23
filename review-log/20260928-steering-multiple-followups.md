---
lane: L1
pr: 旧#195
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | d913064019ffa2ccd17ebd4e878bf068b0425006 | 0 | 1 | 0 | 2026-09-28T15:40+09:00 |
| 独立-2 | light-lane-independent-reviewer, 差分, model: opus | 343047ccf6e9d2ab1681666f967c8eb7d042780e | 0 | 1 | 0 | 2026-09-28T16:20+09:00 |
| 独立-3 | light-lane-independent-reviewer, 全差分, model: opus | b7542949a25f5077b7526358a45b2ebca3b8167b | 0 | 0 | 0 | 2026-09-28T17:10+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| F1 | 独立-1 | medium | no | inherited | doc-claim | fixed | TROUBLESHOOTING の複数 steering の項が、原因を複数 worktree と書き、復帰手順に worktree の削除を挙げている（影響先） |
| F2 | 独立-1 | low | no | inherited | doc-claim | fixed | pre-PR gate の multiple の案内（completion-check を通してから）に従っても複数 steering は解けない（影響先） |
| F3 | 独立-1 | low | no | self-inflicted | test-power | fixed | merge gate テストの active 側の Merge Approval が malformed になり、evidence-unparsable の否定 assert が常に通る |
| A1 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | session-start の案内の pre-push も止まるという添え書きに条件が無い |
| A2 | 独立-1 | advisory | no | inherited | product | accepted | session-start は終端の steering 2 件以上を知らせない |
| A3 | 独立-1 | advisory | no | self-inflicted | bookkeeping | accepted | 断片の節（Changed と Fixed）と Validation の括弧書き |
| A4 | 独立-1 | advisory | no | inherited | bookkeeping | accepted | 材料欄の文言が session に読み込まれた agent 定義のテンプレートと違う |
| G1 | 独立-2 | medium | no | inherited | doc-claim | fixed | pre-PR で done の steering が 2 件以上のときの案内が completion-check を通してからのままで、やり直しても解けない（影響先） |
| G2 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | TROUBLESHOOTING の移し先が .steering/ の中のサブディレクトリでもよいと読め、そこへ移すと done guard が検査しない |
| G3 | 独立-2 | low | no | inherited | doc-claim | next-pr | skills の archive 手順（.steering/<slug>-archived-YYYYMMDD/ へのリネーム）は .steering/*/state.md の深さに残り、作業中の値なら multiple を解かない |
| M1 | 独立-3 | medium | no | self-inflicted | guidance-scope | next-pr | 移す案内が対象の steering を限定せず、PR が open の steering を移すと、所有 marker が無い merge でその PR が merge gate の検査から外れる |
| M2 | 独立-3 | medium | no | self-inflicted | guidance-scope | next-pr | hook の案内 2 か所に .steering/ の外という条件が無く、.steering/ の中へ移すと done guard の検査が戻らない |
| M3 | 独立-3 | medium | no | self-inflicted | guidance-scope | next-pr | TROUBLESHOOTING の例の .steering-archive/ は gitignore と raw steering 検査の外で、全量 commit で steering が PR に混入しうる |
| L1 | 独立-3 | low | no | inherited | doc-claim | next-pr | references の 3 か所が tasklist.md の Next Action=cancelled で steering を終える手順を案内し、検出の候補から外れない |
