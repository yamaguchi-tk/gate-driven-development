---
lane: L1
pr: 482
follow_up_of: 479
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 9433af62 | 0 | 0 | 0 | 2026-10-14 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| I1-1 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | self-review-lanes.md:99 の「Task Size だけで分岐し」と、足した例外の文が食い違う。限界に書く |
| I1-2 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | independent-review.md:12 の (3-a) 主節が「push 対象 ref の tip」のままで「PR 作成時は HEAD」が無い。限界に書く |
| I1-3 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | independent-review.md:19 の「独立レビュー自体を要求しない」は、Task Size で分岐しない merge gate の received: no の経路と合わない。限界に書く |
| I1-4 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 変更断片の Summary が「5 か所」と書くが、変えた行は 6 か所。限界に書く |
| I1-5 | 独立-1 | low | no | inherited | doc-claim | accepted | 列挙: self-review-lanes.md:90-92 の発火表の quick・trivial の「要求しない」に、tip の証跡で選んだときの例外が無い。限界に書く |
| I1-6 | 独立-1 | low | no | inherited | doc-claim | accepted | 列挙: CONTRIBUTING.md:147・149 の独立レビューの節に、tip の証跡で選んだときの例外が無い。限界に書く |
| I1-7 | 独立-1 | advisory | no | self-inflicted | style | accepted | independent-review.md:19 の例外を入れ子の括弧に足した。(3-c) の下に項を立てる案。PR 本文に列挙 |
| I1-8 | 独立-1 | advisory | no | inherited | doc-claim | accepted | hooks/scripts/lib/self-review-evidence.sh:45 の注記に例外が無い（判定のコードなので直さない）。PR 本文に列挙 |
| I1-9 | 独立-1 | advisory | no | inherited | doc-claim | accepted | (3-c) の merge gate の経路の条件に、Bot Review Received の sha が HEAD と一致することが無い。PR 本文に列挙 |
| I1-10 | 独立-1 | advisory | no | self-inflicted | bookkeeping | fixed | skill 本文を変えたのに Skill RED-GREEN Evidence が無い commit: なし（PR 本文） |
