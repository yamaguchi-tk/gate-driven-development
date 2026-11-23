---
lane: L1
pr: 611
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 981f227a | 0 | 4 | 0 | 2026-10-29T23:10+09:00 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | c3707ea5 | 0 | 0 | 0 | 2026-10-29T23:55+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| r1-1 | 独立-1 | medium | no | self-inflicted | request-drift | fixed | 依頼 B1 が挙げた gate-skill-dispatch-nudge が、GDD を使っていないセッションで動く hook の表に無い。行を足した。commit: c3707ea5 |
| r1-2 | 独立-1 | medium | no | self-inflicted | request-drift | fixed | 依頼 B3 の gh・git の版が書かれていない。前提に Python・git・GitHub CLI の確かめた版と版で変わることの表を足した。commit: c3707ea5 |
| r1-3 | 独立-1 | medium | no | self-inflicted | request-drift | accepted | 依頼 B2 は「公開 repo の marketplace 名が決まったら追加」だが、private の個人 repo の名前で書いていた。条件が満たされていないので手順の節を外した（Fable の推奨。Opus は読み替えの形を推奨）。ユーザーが外したままにすると決めた（2026-10-30）。commit: c3707ea5 |
| r1-4 | 独立-1 | medium | no | self-inflicted | doc-claim | accepted | wait-loop-gate の行が止める範囲を狭く書いている。`--watch` を含む background の Bash は dev watcher でも止まる（README.md:36、wait_loop_gate.py:28-37） |
| r1-5 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 前提の表の Python の行が、無いときにすべての Write・Edit が止まることを書いていない（README.md:232） |
| r1-6 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | Stop hook の行が、宣言による押し返しと repo の .claude/・.gdd/ への書き込みを書いていない（README.md:40） |
| r1-7 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 「記録だけ」の行が、push のたびの gh pr list の通信を書いていない（README.md:43） |
| r1-8 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | ブランチ名の `20YYYYMM` が判定（20 で始まる 8 桁、大文字小文字を問わない）と合っていない（README.md:37） |
| r1-9 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | `.steering/` の行の「当たれば止める」が、3 回続くと警告付きで通す種類を書いていない（README.md:38） |
| r1-10 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | kill switch の「消せば元に戻る」が、SessionStart で入るものは次のセッションからであることを書いていない（README.md:46） |
| r1-11 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 環境別セットアップの推奨の変更が、断片と PR 本文に無い（手順の節を外した後は推奨の変更も無くなった） |
| r1-12 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | docs/ONBOARDING.md の前提と入れ方が新しい README と食い違う（ONBOARDING.md:27-33, 49-64） |
| r1-13 | 独立-1 | low | no | inherited | doc-claim | accepted | README の Plugin Structure の agent の列挙が古い（README.md:490） |
| r1-14 | 独立-1 | low | no | inherited | doc-claim | accepted | references/onboarding.md:209 の見出しに「4 agents」が残っている |
| r1-15 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | PR 本文の「既存の pre-push hook と並んで動くかは未検証」が、hook のコメントの git 2.54 での実測と食い違う。PR 本文の限界を直した。commit: なし（PR 本文） |
| r1-16 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 依頼の jq を前提から外した理由が PR 本文に無い（hook は gh の --jq だけを使う） |
| r1-17 | 独立-1 | advisory | no | self-inflicted | test-power | accepted | GDD を使っていないセッションで動く hook の表は手で保つ一覧で、ずれを見る検査が無い |
| r2-1 | 独立-2 | medium | no | self-inflicted | request-drift | re-reported | 依頼 B2 のインストール手順を消し、PR 本文に扱いが無い（r1-3 の再掲。PR 本文の限界に確認待ちとして書いてある） |
| r2-2 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | PR 本文の git の確かめた版が README（2.50.1 も）より狭い。PR 本文を直した。commit: なし（PR 本文） |
| r2-3 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | Python の版の欄が、`-I` を付けずに起動する python を子の python だけに狭めている（README.md:243、kill-switch.sh:21-23） |
| r2-4 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | gh の版の欄が、版が違うと何が起きるかを書いていない（README.md:245） |
| r2-5 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | 依頼の jq を前提から外した理由が PR 本文に無い（r1-16 と同じ点） |
