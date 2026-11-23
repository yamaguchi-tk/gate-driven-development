---
lane: L1
pr: 310
follow_up_of: 300
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | e7e269c46d5c5461d3d22c7d5125111bb5496f9f | 0 | 0 | 0 | 2026-10-03T23:10+09:00 |
| 独立-2 | light-lane-independent-reviewer, 差分, model: opus | b68d4328210e37191b5529122bd0a75b11f12202 | 0 | 1 | 0 | 2026-10-03T23:50+09:00 |
| 独立-3 | light-lane-independent-reviewer, 差分, model: opus | cf0514374c27a021746f7faa059186729f1bc316 | 0 | 0 | 0 | 2026-10-04T00:15+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| N1 | 独立-1 | low | no | self-inflicted | product | fixed | `--no-renames` で、merge-base にある他の PR の断片を改名しただけのものも名指しする。index の中身が merge-base の断片と同じなら名指ししない commit: a66d6d95 |
| N2 | 独立-1 | low | no | inherited | test-power | next-pr | merge-base の断片を中身を変えずに改名して commit すると、断片を足したと数えて PASS する（判定を変えるので別 PR） |
| N3 | 独立-1 | advisory | no | self-inflicted | test-power | accepted | 改名のテストが、ホストの `status.renames=false` で `--no-renames` を消しても通る。PR 本文に書く |
| N4 | 独立-1 | advisory | no | self-inflicted | product | accepted | `git mv` の後に消した `AD` を名指しする。PR 本文に書く |
| N5 | 独立-1 | advisory | no | self-inflicted | product | accepted | `git status --no-renames` は Git 2.18 以上が要る。PR 本文に書く |
| N6 | 独立-1 | advisory | no | inherited | product | accepted | 直下かを親の名前だけで見て、NAME_RE も見ない。PR 本文に書く |
| N7 | 独立-1 | advisory | no | self-inflicted | doc-claim | fixed | PR 本文の `git add -N` を名指ししない理由が誤っている commit: なし（PR 本文） |
| N8 | 独立-1 | advisory | no | inherited | style | accepted | 名指しが複数でも単数形の文。PR 本文に書く |
| N9 | 独立-1 | advisory | no | self-inflicted | style | accepted | 新しいテストが git を直に呼び、ファイルの `git()` を使っていない。PR 本文に書く |
| Q1 | 独立-2 | medium | no | inherited | test-power | accepted | 判定側は、他の PR の断片を改名して commit すると足した断片と数えて通る（案内と判定の定義が食い違う）。判定を変えるので、N2 の次の PR で直す。PR 本文の限界に書く |
| Q2 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | 断片の Summary が、`git mv` を使わない改名も名指ししないように読める commit: cf051437 |
| Q3 | 独立-2 | low | no | self-inflicted | test-power | accepted | merge-base に断片がある状態で、自分の新しい断片が名指しされることを確かめるテストが無い。PR 本文の限界に書く |
| Q4 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | `:{path}` が porcelain のパスの基点に頼る前提のコメントが無い。PR 本文に書く |
| Q5 | 独立-2 | advisory | no | self-inflicted | style | fixed | 断片の区切りの前に余分な空白 commit: cf051437 |
| S1 | 独立-3 | low | no | inherited | doc-claim | accepted | 名指しの除外は index の `A` 行だけに掛かり、`mv` だけの改名は名指しし、`git mv` の後に作業ツリーだけ書き換えたものは名指ししない。PR 本文の限界に書く |
| S2 | 独立-3 | low | no | inherited | test-power | re-reported | Q1・N2 の再掲（判定側が改名を断片を足したと数える） |
| S3 | 独立-3 | advisory | no | self-inflicted | style | accepted | 断片の「（index 上で）」の掛かり方が読み分けにくい。PR 本文に書く |
