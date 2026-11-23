---
lane: L1
pr: 468
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 97b50e2e | 1 | 1 | 1 | 2026-10-13 |
| 方針メモ-1 | Opus 設計レビュー (gate-driven-development:gdd-opus-advisor, model: opus) | 97b50e2e | 0 | 0 | 0 | 2026-10-13 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 5bdd55eb | 1 | 0 | 1 | 2026-10-13 |
| 方針メモ-2 | Opus 設計レビュー (gate-driven-development:gdd-opus-advisor, model: opus) + user | 5bdd55eb | 0 | 0 | 0 | 2026-10-13 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| I1-1 | 独立-1 | high | yes | inherited | fail-open | accepted | 列挙: marker の無い git cwd から cd 先を決められない形（相対・~・$・cd 2 つ）で打つ merge は、cd 先に marker があっても証跡を読まず、台帳で当たらなければ通す。方針メモ-1 で (b)。入力者は 1 件以上（34 件、cd 先に marker があるのは $ を含む 13 件、相対は 0 件）。(a) の候補（marker 不在の出口で cd の意図があり cd 先が空なら止める）は正当な merge 20 件（$(…) で unresolvable になる -R つきの 13 件と、同じ worktree へ戻る形 7 件）を止め、cd 先の解決を広げる案も 13 件を untrusted-root-unverified で止める見込みで、誤 block 0 件の受理の形が無い。限界の節の先頭に書く |
| I1-2 | 独立-1 | medium | no | self-inflicted | doc-claim | next-pr | SECURITY.md の項の「cwd が git repo でなければ止める」は、URL か -R で対象を明示した merge では成り立たない（台帳で当たらなければ通す） |
| I1-3 | 独立-1 | medium | no | self-inflicted | product | fixed | 止めない根拠が相対パスの 0 件だけで、項に並べた ~・$・cd 2 つの形の件数と直さない理由が PR 本文にしか無く、(C) の理由（正本を 2 か所に割らない）から外れる。項に件数・ADR の範囲の内であること・誤 block の数・近似であることを書いた commit: f2a5e278 |
| I1-4 | 独立-1 | low | no | self-inflicted | doc-claim | next-pr | 「cd 先が 1 つの絶対パスのときだけ」は、先頭の cd であること・コマンド全体に $・env が無いこと・cd 先に marker があることなどの条件を落としている。正本の _select_cd_target を名指しする |
| I1-5 | 独立-1 | low | no | self-inflicted | doc-claim | next-pr | 変更断片の「台帳に無ければ通す」が、台帳を読めない・対象 PR を特定できないときも通ることを書いていない |
| I1-6 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | PR 本文の「682 行付近のコメント」は 777〜779 行の誤り commit: なし（PR 本文） |
| I1-7 | 独立-1 | low | no | inherited | product | next-pr | repo-root-unresolvable・pr-target-unresolvable の案内が、cd 先を絶対パスでコマンドの先頭に 1 つだけ書くことを伝えず、相対パスで打ち直すと同じ理由で止まり続ける |
| I1-8 | 独立-1 | advisory | no | self-inflicted | product | accepted | 承認された案の「PR 本文に Fable の行を書く」が PR 本文の抜粋に無い（抜粋の外の節にあれば外れではない） |
| I1-9 | 独立-1 | advisory | no | self-inflicted | product | accepted | 依頼の 1・2（判定の表、原因の位置）が差分にも PR 本文にも無く、次に hooks/ を触る PR が原因の位置を辿れない |
| I1-10 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 件数の測り方（コマンド、merge の判定条件、marker の近似）が書かれておらず、ADR の撤回条件で測り直すときに母集合を再現できない |
| I1-11 | 独立-1 | advisory | no | self-inflicted | product | accepted | 依頼の原文は L1+ と書くが、この巡は L1（近道）。差分は文書だけで、近道を含む案をユーザーが承認しているので外れではない |
| I2-1 | 独立-2 | high | yes | inherited | fail-open | accepted | 列挙: I1-1 と同じ穴（marker の無い git cwd から cd 先を決められない merge が、台帳で hit しなければ通る）。新しく挙がった、番号を位置引数の $(…) で渡す形は実データ 0 件。照合する番号・URL を読めない形はループの $pr の 2 件。方針メモ-2 で (b)。番号を読めない形だけを止める狭い案は、その 2 件（同じ cwd から root checkout へ移る一括 merge で、正当に見える）だけを止め、通った 13 件は閉じない。Fable も (b)、ユーザーが (b) を選んだ。SECURITY.md の項に 1 文を足し、限界の節の先頭に書く |
| I2-2 | 独立-2 | medium | no | self-inflicted | doc-claim | re-reported | I1-2 の再掲（「cwd が git repo でなければ止める」は明示した merge では成り立たない） |
| I2-3 | 独立-2 | low | no | self-inflicted | doc-claim | next-pr | ADR の守る範囲の内なのに直さない根拠（誰が決めたか、PR 番号）と、ADR のパス、開き直す条件を書いていない |
| I2-4 | 独立-2 | low | no | self-inflicted | doc-claim | next-pr | 34 件の内訳（13＋7＋8）が 34 にならず、止める分岐の条件も書いていない |
| I2-5 | 独立-2 | low | no | self-inflicted | doc-claim | next-pr | 「$(…) の語が引数に入るので -R で明示しても決められない」は、位置引数か -R の値に入るときだけで、flag の値なら当たらない |
| I2-6 | 独立-2 | low | no | self-inflicted | doc-claim | next-pr | 「承認の無い merge が通った例は見つかっていない」の確かめ方と対象の件数が書かれていない |
| I2-7 | 独立-2 | low | no | self-inflicted | doc-claim | re-reported | I1-5 の再掲（変更断片が、台帳を読めない・対象を特定できないときも通ることを書いていない） |
| I2-8 | 独立-2 | low | no | self-inflicted | product | fixed | 承認された案の「PR 本文に Fable の行を書く」が PR 本文の抜粋に無い。PR 本文に Fable の行を書いた commit: なし（PR 本文） |
| I2-9 | 独立-2 | low | no | inherited | doc-claim | next-pr | run-merge-gate-hook.sh:777-779 のコメント「非対称を解消する」が、cd 先を決められない形では成り立たない |
| I2-10 | 独立-2 | advisory | no | self-inflicted | product | accepted | 依頼は L1+ と書くが、この巡は L1。差分は文書だけで、近道を含む案をユーザーが承認している |
| I2-11 | 独立-2 | advisory | no | self-inflicted | product | accepted | 依頼の 1 の表と、2 の判定の位置（_mg_outside_gdd_merge・AC-18）が PR 本文に無い |
| pm-1 | 方針メモ-1 | - | - | - | - | - | なし |
| pm-2 | 方針メモ-2 | - | - | - | - | - | なし |
