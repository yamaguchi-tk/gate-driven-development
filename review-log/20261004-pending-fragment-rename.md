---
lane: L1
pr: 314
follow_up_of: 312
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | fee67ef326a9629ae51e9942679a02da309e1301 | 0 | 0 | 0 | 2026-10-04T13:40+09:00 |
| 独立-2 | light-lane-independent-reviewer, 差分, model: opus | 3a8449b7cecc3531ca84f6569f9a73ac0c358b99 | 0 | 0 | 0 | 2026-10-04T14:10+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| L1 | 独立-1 | low | no | self-inflicted | product | fixed | commit 済みの改名と未 commit の自分の断片をパスの順に混ぜて数えるので、自分の断片が先に並ぶと名指しされない。commit 済みの改名に消えた断片の分を先に取らせた commit: 3a8449b7 |
| L2 | 独立-1 | low | no | self-inflicted | product | fixed | commit で消した merge-base の断片を index に戻すと、自分の断片として名指しされる。merge-base にあるパスを候補から外した commit: 3a8449b7 |
| L3 | 独立-1 | low | no | self-inflicted | test-power | fixed | `committed` 引数を通るテストが無い。commit 済みの改名と自分の断片を両方の並びで見るテストを足した commit: 3a8449b7 |
| L4 | 独立-1 | advisory | no | self-inflicted | product | accepted | 名前が NAME_RE に合わない候補も、消えた断片の分を取る（commit 側は取らない）。PR 本文に書く |
| L5 | 独立-1 | advisory | no | self-inflicted | doc-claim | fixed | 比べる中身が index から作業ツリーに変わったことを断片が書いていない。断片に書いた commit: 3a8449b7 |
| L6 | 独立-1 | advisory | no | self-inflicted | doc-claim | fixed | 限界の「filter で blob が違う」は hash-object が filter をかけるので当たらず、実際に食い違うのは index だけを commit したときと symlink。PR 本文を直した commit: なし（PR 本文） |
| M1 | 独立-2 | low | no | self-inflicted | product | accepted | commit 済みの改名を `git rm --cached` で index から外すと、同じパスが commit 済みの改名と新しい候補の両方に入り、名指しされる。PR 本文の限界に書く |
| M2 | 独立-2 | low | no | self-inflicted | test-power | accepted | 「作業ツリーで比べる」（`git mv` の後に作業ツリーだけ書き換えたもの）を固定するテストが無い。PR 本文の限界に書く |
| M3 | 独立-2 | low | no | inherited | product | accepted | index に足してから作業ツリーで消した断片（`AD`）が名指しされる。PR 本文の限界に書く |
| M4 | 独立-2 | low | no | inherited | product | accepted | 名前が規則外の候補も消えた断片の分を取る（L4 と同じ。severity が上がったので再掲にしない）。PR 本文の限界に書く |
| M5 | 独立-2 | low | no | self-inflicted | style | accepted | subTest の中で `self.setUp()`・`self.tearDown()` を呼び、一時ディレクトリの削除を finalizer に任せている。PR 本文の限界に書く |
| M6 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | 未リリースの 20261003-validate-hints-followup.md の「（index 上で）」が、この PR の「作業ツリーで比べる」と逆になる。リリースの dry-run で直す |
