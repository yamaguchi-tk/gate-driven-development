---
lane: L1
pr: 362
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | be58f92c1bd34595306369e6f83b90fb24e2c382 | 0 | 1 | 0 | 2026-10-04T16:40+09:00 |
| 独立-2 | light-lane-independent-reviewer, 差分, model: opus | 32a29fba099987f3bd31d597c9d77f06ef510513 | 0 | 0 | 0 | 2026-10-04T17:30+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| A1 | 独立-1 | medium | no | self-inflicted | product | fixed | 代わりの経路を general-purpose にしたので、fable のときに dispatch gate が工程の model への変更を求める warn を新しく返し、Edit・Write の制限も無くなる。代わりの経路を Plan に戻した commit: 9b098929 |
| A2 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 「model: fable には opus への変更を求める」は sonnet の工程では成り立たず、断片も手順 1 の Fable まで警告されていたように読める。文を直した commit: 9b098929 |
| A3 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | fixed-models.md の gate の対象外の列挙と docstring に相談役が無い。足した commit: 9b098929 |
| A4 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | README の agents/ の内訳に相談役が無い。足した commit: 9b098929 |
| A5 | 独立-1 | low | no | self-inflicted | test-power | fixed | 相談役の model と 3 本の本文の一致を固定するテストが無い。tests/test_advisor_agents.py を足した commit: 54fe4a8c |
| A6 | 独立-1 | low | no | self-inflicted | bookkeeping | fixed | effort の継承を記録する欄が決まっていない。model: の欄に（effort: main から継承）と書く形にした commit: 9b098929 |
| A7 | 独立-1 | low | no | self-inflicted | test-power | fixed | 相談役の免除が model の値を見ず、Opus の相談役に model: sonnet を明示しても警告しない。Opus の 2 本を FIXED 表に移した commit: 9b098929 |
| A8 | 独立-1 | low | no | self-inflicted | bookkeeping | fixed | 断片の Affected Files にテスト 3 本が無い。足した commit: 9b098929 |
| A9 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | description がユーザーの「Opus に聞いて」「Fable に聞いて」での直接起動を書き、repo の root の agent と重なる。手順からだけ起動すると書き直した commit: 9b098929 |
| A10 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 「repo に置いた同じ定義では動いた」は同じ定義ではない。--plugin-dir で plugin の定義を実測した結果に書き直した commit: 9b098929 |
| A11 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 根拠の数値（max 19/20 など）の元データの場所が tree の中で辿れない。PR 本文に書く |
| A12 | 独立-1 | advisory | no | self-inflicted | bookkeeping | fixed | autonomy.md の参照元の一覧に相談役と fixed-models.md が無い。足した commit: 9b098929 |
| A13 | 独立-1 | advisory | no | self-inflicted | product | accepted | gdd-opus-advisor-max はこの tree では誰も起動しない。PR 本文の限界に書く |
| B1 | 独立-2 | low | no | self-inflicted | product | next-pr | Opus の相談役を model: sonnet に明示して下げても、sonnet の工程では警告が出ない（judge が sonnet を許す）。PR 本文の限界に書き、表で opus に固定した agent を固定の model と比べる直しは次の PR |
| B2 | 独立-2 | advisory | no | self-inflicted | product | accepted | Opus の相談役に model を明示したときの警告文が、model を省略せず工程の model に変えるよう勧める。PR 本文に書く |
| B3 | 独立-2 | low | no | self-inflicted | doc-claim | next-pr | 断片の「今までどおり Plan」は、手順 3 の Fable（これまで subagent_type 無し）には当たらない。次の PR |
| B4 | 独立-2 | low | no | self-inflicted | bookkeeping | next-pr | 手順 3 の Fable を代わりの経路で起動したとき、effort の継承を書く欄が手順 5 の行に無い。次の PR |
| B5 | 独立-2 | low | no | self-inflicted | doc-claim | next-pr | 「references/fixed-models.md § 相談役」の指し先が見出しではなく段落。次の PR |
| B6 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | テストのコメント「相談役の免除は agent の名前だけで決め」が、Opus の相談役の免除の規則と合っていない。PR 本文に書く |
| B7 | 独立-2 | advisory | no | self-inflicted | style | accepted | test_advisor_agents.py の effort の assert が agent-effort-schema.sh と重なる固定値 pin。PR 本文に書く |
| B8 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | autonomy.md の「--plugin-dir で fable・medium で動いた」に確かめた方法が無い。PR 本文に CLI の版と方法を書く |
| B9 | 独立-2 | advisory | no | inherited | doc-claim | accepted | 代わりの経路の Plan が Bash を持つなら read-only は散文だけになる（Plan のツール集合は未確認）。PR 本文に書く |
