---
lane: L1
pr: 445
follow_up_of: 443
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 26b9f43a | 0 | 0 | 0 | 2026-10-13 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 7ee27829 | 0 | 0 | 0 | 2026-10-13 |
| 独立-3 | light-lane-independent-reviewer, 全差分（無効化後）, model: opus | a182d299 | 0 | 0 | 0 | 2026-10-13 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| I1-1 | 独立-1 | low | no | self-inflicted | bookkeeping | fixed | 同じ本人の入力を複数の手順が request.md に何度も足しうる。9 の (1) に 1 回だけと書き、gdd-using-skills も「1 回足す」にした commit: 80379672 |
| I1-2 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 承認した変換: の書き方が autonomy.md と事前回答 2 で違う。事前回答 2 を（初期条件 → 変換後、扱い）か なし にそろえた commit: 80379672 |
| I1-3 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | post-completion-pr-flow.md:214 の採れる案の列挙が、Request Drift の止まる案とぶつかる。autonomy.md の止まる案を指す形にした commit: 80379672 |
| I1-4 | 独立-1 | low | no | self-inflicted | bookkeeping | fixed | 新しく足した止まる条件が読む入力（Request Drift の指摘、承認した変換: の欄）が既存の記録に無いことを、PR 本文の限界に書いていない commit: なし（PR 本文） |
| I1-5 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | autonomy.md 手順 5 の行の書式の正本に、末尾の 承認した変換: の欄が載っていない |
| I1-6 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | Approved Direction を数えない理由「agent が自分で書ける」が (2) の worklog の行にも当てはまる |
| I1-7 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | completion-reviewer の Mission に worklog.md・request-crosscheck.md が無い |
| I1-8 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 止まる案に足した項の理由「承認の記録に数えられず」が、具体化の引用があるときには当たらない |
| I1-9 | 独立-1 | advisory | no | self-inflicted | product | accepted | 判断役・委任先に渡す材料に request.md・request-crosscheck.md を足すと、委任の承認の質が上がる |
| I1-10 | 独立-1 | advisory | no | self-inflicted | bookkeeping | accepted | Skill RED-GREEN Evidence が PR 本文の抜粋に無い |
| I2-1 | 独立-2 | low | no | self-inflicted | product | accepted | 方式転換の 4 択に「依頼に合わせて直す」案が無く、Request Drift が残るときに採れる案が空か読み手しだいになる。Round 上限の経路は autonomy.md の止まる案の語に当たるかが読み方で変わる |
| I2-2 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | post-completion-pr-flow.md:214 が事前回答の委任先も autonomy.md の止まる案に結びつけたが、委任先の正本は human-check-template.md § 事前回答 3 |
| I2-3 | 独立-2 | low | no | self-inflicted | product | accepted | tip で推定 token が上限内か read-only では確かめられない（tip の validate-plugin.sh は skill-body-budget.sh を含めて通っている） |
| I2-4 | 独立-2 | advisory | no | self-inflicted | product | accepted | 「1 回だけ足す」が、承認後に引用を添え直すことを禁じるように読める |
| I2-5 | 独立-2 | advisory | no | self-inflicted | bookkeeping | accepted | 承認した変換: を足す条件が next-stage の着手にも読める |
| I2-6 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | 予算のコメントの句が tip の「に 1 回足す」と違い、相殺の書き換えも書いていない |
| I2-7 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | gdd-using-skills:88 だけ brainstorming-steps 9 の (1) への指し先が無い |
| I2-8 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | 変更断片に、Request Drift が残るときは直す案だけ、が無い |
| I3-1 | 独立-3 | low | no | self-inflicted | product | accepted | 承認された句「request.md にも足す」と入った句「に 1 回足す」が違い、同じ行の「権限境界を適用する」も詰めた。依頼の原文から外れた指摘なので、Fable に相談したうえでユーザーに確かめ、「今の句でよい」を request.md に足した。予算のコメントの引用のずれは PR 本文に書く |
| I3-2 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | autonomy.md の止まる案の理由「承認の記録に数えられず」が (2) と食い違う |
| I3-3 | 独立-3 | low | no | self-inflicted | product | accepted | 止まる案の発火条件「Request Drift を理由にした human_recheck_required」が、上限による方式転換に着いた場面に当たるか読めない。rollback-patterns の Round 上限には対応する文が無い |
| I3-4 | 独立-3 | low | no | self-inflicted | product | accepted | (2) が読む入力（承認した変換: の引用、変換表の扱い、request-crosscheck.md）はどれも main が書き、扱いを具体化と偽れば読み替えも承認に数えうる |
| I3-5 | 独立-3 | advisory | no | self-inflicted | doc-claim | accepted | 手順 5 の行の書式に末尾の 承認した変換: の欄が載っていない |
| I3-6 | 独立-3 | advisory | no | self-inflicted | doc-claim | accepted | 変更断片が、未観測の「同じ High が続いた」を起きた事実のように書いている |
| I3-7 | 独立-3 | advisory | no | inherited | product | accepted | 最初の human check で、委任では承認できない変換表の行があっても判断役が承認できる |
| I3-8 | 独立-3 | advisory | no | self-inflicted | bookkeeping | accepted | 未測のまま足すことをユーザーが確かめたかが request.md から読めない |
| I3-9 | 独立-3 | advisory | no | inherited | product | accepted | request.md を作る前の本人の入力が残らない |
