---
lane: L1
pr: 479
follow_up_of: 475
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | d4dd1a7e | 0 | 0 | 0 | 2026-10-14 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| I1-1 | 独立-1 | low | no | inherited | doc-claim | accepted | independent-review.md:19・self-review-lanes.md:99 の Task Size ごとの免除に、tip の証跡で選んだときの例外が無い。follow_up_of のある PR なので限界に書く |
| I1-2 | 独立-1 | low | no | inherited | doc-claim | accepted | gdd-pr-review/SKILL.md:78 の dry の免除に、tip の証跡で選んだときの例外が無い。限界に書く |
| I1-3 | 独立-1 | low | no | inherited | doc-claim | accepted | self-review-lanes.md:93 の発火表の Independent Review の sha に「PR 作成時は HEAD」が無い。限界に書く |
| I1-4 | 独立-1 | low | no | inherited | doc-claim | accepted | independent-review.md:12 の (3-a) が sha 一致検査を pre-push gate だけで書いている。限界に書く |
| I1-5 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | independent-review.md:51 が merge gate の一致の検査を条件なしで書いた。merge gate が読むのは received: no の経路だけ。限界に書く |
| I1-6 | 独立-1 | advisory | no | self-inflicted | doc-claim | fixed | PR 本文の変更内容に、sha の「PR 作成時は HEAD」と merge gate の書き足しが無い commit: なし（PR 本文） |
| I1-7 | 独立-1 | advisory | no | self-inflicted | bookkeeping | fixed | skill 本文を変えたのに Skill RED-GREEN Evidence が無い commit: なし（PR 本文） |
