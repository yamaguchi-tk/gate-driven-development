---
lane: L1
pr: 300
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | bd9af9d89c7acdaa8c8248b99db4d110b3f6f5b2 | 0 | 0 | 0 | 2026-10-03T17:20+09:00 |
| 独立-2 | light-lane-independent-reviewer, 差分, model: opus | 7955d8b08de187196182c27328508d9350298e62 | 0 | 1 | 0 | 2026-10-03T18:05+09:00 |
| 独立-3 | light-lane-independent-reviewer, 差分, model: opus | 894aaa47aed60b57bd77b2f2866452d01a0371c0 | 0 | 0 | 0 | 2026-10-03T18:35+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| G1 | 独立-1 | low | no | self-inflicted | product | fixed | `git status` の状態を見ずに名指しするので、commit 済みの断片を作業ツリーで書き換えた・消したものも「commit していない」と案内する。untracked と index に足しただけのものに絞った commit: b3da823d |
| G2 | 独立-1 | low | no | self-inflicted | test-power | fixed | 否定のテストが clean な作業ツリーで走り、名指しのフィルタを消しても通る。ドットファイル・.txt・サブディレクトリと、commit 済みの断片の書き換えのテストにした commit: 268869c8 |
| G3 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | コメントの「この検査は commit だけを見る」が、作業ツリーで書式を見る実装より広い。数え方を書き分けた commit: b3da823d |
| G4 | 独立-1 | advisory | no | self-inflicted | product | accepted | 実害=yes の行でも `対応` の一覧に件数から外す値（next-pr など）が出る。PR 本文に書く |
| G5 | 独立-1 | advisory | no | self-inflicted | style | fixed | 300 行を超える `run()` がさらに伸びた。名指しを `_uncommitted_new_fragments` に出した commit: b3da823d |
| H1 | 独立-2 | medium | no | self-inflicted | doc-claim | fixed | 変更断片の Validation 欄が改名前のテスト名のままで、Summary も名指しの範囲（新しく足した断片だけ）を表していない commit: 894aaa47 |
| H2 | 独立-2 | low | no | self-inflicted | test-power | next-pr | index に足しただけ（`A `）の名指しと、index に載せた書き換え（`M `）の非名指しを固定するテストが無い |
| H3 | 独立-2 | low | no | self-inflicted | doc-claim | next-pr | コメントの「merge-base..HEAD の commit で数える」が、作業ツリーの書式検査も条件にする実装より広い |
| H4 | 独立-2 | advisory | no | self-inflicted | product | accepted | 直下かを親ディレクトリの名前だけで見るので、`changelog.d/changelog.d/x.md` も名指しする。PR 本文に書く |
| H5 | 独立-2 | advisory | no | self-inflicted | product | accepted | porcelain v1 を -z なしで読むので、quote されるパス・intent-to-add・rename の追加は名指ししない。PR 本文に書く |
| H6 | 独立-2 | advisory | no | self-inflicted | test-power | accepted | 否定のテストが案内の文言に依存し、文言を変えると空振りする。PR 本文に書く |
| H7 | 独立-2 | advisory | no | inherited | product | accepted | `git status` の失敗を見ず、案内が黙って出なくなる（FAIL は変わらない）。PR 本文に書く |
| I1 | 独立-3 | low | no | self-inflicted | test-power | re-reported | H2 の再掲（index に足しただけの断片の名指しを固定するテストが無い） |
| I2 | 独立-3 | low | no | self-inflicted | product | next-pr | `git mv` で改名した断片は `R` と出て名指しされない。`--no-renames` で `A` に分ける |
| I3 | 独立-3 | advisory | no | self-inflicted | product | re-reported | H4 の再掲に、`AD`・`AA` も名指しする端を足したもの |
| I4 | 独立-3 | advisory | no | self-inflicted | test-power | re-reported | H6 の再掲 |
| I5 | 独立-3 | advisory | no | self-inflicted | product | accepted | `git status` が index.lock を取り、`--no-optional-locks` が無い。PR 本文に書く |
| I6 | 独立-3 | advisory | no | self-inflicted | style | accepted | 名指しが複数件でも単数形の文になる。PR 本文に書く |
