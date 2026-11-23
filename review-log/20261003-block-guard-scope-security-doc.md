---
lane: L1
pr: 331
follow_up_of: 328
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 1528a62f0d05393bd2ed58898bbcbb3ce6eb494e | 0 | 0 | 0 | 2026-10-03T21:40+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| K1 | 独立-1 | advisory | no | self-inflicted | bookkeeping | accepted | advisory: テンプレート外の記述あり。PR 本文の抜粋の「`follow_up_of: 328`」は review-log の値。判断には使われていない。次の巡は無い |
| K2 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | ADR の却下した代替案で、旧#279 の方針メモ-2 と方針メモ-3 の時系列が逆。限界に書いた |
| K3 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 旧#279 の根拠を ADR だけ方針メモ-2 に書き換え、CLAUDE.md の「レビュアーは語を足すだけでは閉じないと書いていた」と食い違う。限界に書いた |
| K4 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | SECURITY.md と断片の block guard の列挙に root-branch guard（validate-worktree-command.py）が無い。限界に書いた |
| K5 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | SECURITY.md と断片の「敵対的に作った形は止めない」が、構造の修正と既存の判定で止まる形もある挙動より強い。限界に書いた |
| K6 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | ADR-6 の正本（逐語アーカイブ）に、一部が置き換わった注記が無い。限界に書いた |
| K7 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | ADR の Consequences が `有限集合` を落としている。限界に書いた |
| K8 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | ADR が決めた (a) の「併用しない」の読み方が、運用の正本の CLAUDE.md (a) に無い。限界に書いた |
| K9 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | ADR の実測値の取得元に、集計した時点の sha・本数が無い。PR 本文に列挙 |
| K10 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | SECURITY.md の「repo の docs/adr/…」が、導入者には自分の repo を指すと読める。PR 本文に列挙 |
| K11 | 独立-1 | low | no | inherited | doc-claim | next-pr | SECURITY.md § 4 の hook の表に、Bash の PreToolUse の gate（pre-PR・worktree command guard・pre-push・merge gate など）が無い。次の PR |
