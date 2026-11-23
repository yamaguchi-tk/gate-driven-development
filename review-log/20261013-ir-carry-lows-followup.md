---
lane: L1
pr: 475
follow_up_of: 471
amends: 20261013-ir-carry-lows.md
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 20e28515 | 0 | 0 | 0 | 2026-10-14 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 3e2615d8 | 0 | 2 | 0 | 2026-10-14 |
| 独立-3 | light-lane-independent-reviewer-xhigh, 差分, model: opus | ca7c4cc4 | 0 | 0 | 0 | 2026-10-14 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| I1-1 | 独立-1 | low | no | inherited | doc-claim | accepted | self-review-lanes.md:103 が Independent Review 行を検査する gate を pre-push gate だけ挙げる。依頼の行の外なので、直した分を戻し（commit: 9eed1ccf）、PR 本文の限界に書く |
| I1-2 | 独立-1 | low | no | inherited | doc-claim | accepted | CONTRIBUTING.md:149 が変更前の SKILL.md:84 と同じ文のまま。依頼の行の外なので、直した分を戻し（commit: 9eed1ccf）、PR 本文の限界に書く |
| I1-3 | 独立-1 | low | no | inherited | doc-claim | accepted | independent-review.md § 証跡に PR 作成前の比較先（HEAD、pre-PR gate）が無い。依頼の行の外なので、直した分を戻し（commit: 9eed1ccf）、PR 本文の限界に書く |
| I1-4 | 独立-1 | low | no | inherited | doc-claim | accepted | SKILL.md:84 の quick・trivial の免除が無条件。依頼の行の外なので、直した分を戻し（commit: 9eed1ccf）、PR 本文の限界に書く |
| I1-5 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 旧#471 の未リリースの断片の文面の引用が、この差分の後は当たらない。amends: で引用を外した commit: 40c225a3 |
| I1-6 | 独立-1 | advisory | no | self-inflicted | doc-claim | fixed | 断片の「戻した」が前の文面と合わない。「にした」にした commit: 40c225a3 |
| I1-7 | 独立-1 | advisory | no | self-inflicted | bookkeeping | fixed | 断片に RECOVERY_CORE の作り方が書いてある。消した commit: 40c225a3 |
| I1-8 | 独立-1 | advisory | no | self-inflicted | style | fixed | 新しいテストが使わない hook も起動している。検算だけを走らせる形にした commit: 40c225a3 |
| I2-1 | 独立-2 | medium | no | self-inflicted | intent | fixed | SKILL.md:84 の免除の但し書きは依頼の外。戻した commit: 9eed1ccf |
| I2-2 | 独立-2 | medium | no | self-inflicted | intent | fixed | 3 つの文書への pre-PR gate の追記は依頼の外。戻した commit: 9eed1ccf |
| I2-3 | 独立-2 | low | no | inherited | doc-claim | fixed | 同じ免除を書くほかの箇所に但し書きが無い。但し書きを戻したので当たらなくなった commit: 9eed1ccf |
| I2-4 | 独立-2 | low | no | inherited | doc-claim | fixed | independent-review.md の (3-a) が pre-push gate しか挙げない。§ 証跡への追記を戻したので当たらなくなった commit: 9eed1ccf |
| I2-5 | 独立-2 | advisory | no | self-inflicted | bookkeeping | fixed | Skill RED-GREEN Evidence を PR 本文に書く commit: なし（PR 本文） |
| I3-1 | 独立-3 | low | no | inherited | doc-claim | re-reported | self-review-lanes.md:103・independent-review.md § 証跡・CONTRIBUTING.md:149 が pre-push gate だけを挙げる（I1-1〜I1-3 と同じ） |
| I3-2 | 独立-3 | low | no | inherited | doc-claim | re-reported | SKILL.md:84 の quick・trivial の免除に、tip の証跡で選んだときの例外が無い（I1-4 と同じ） |
