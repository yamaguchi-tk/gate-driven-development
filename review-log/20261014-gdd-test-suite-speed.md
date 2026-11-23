---
lane: L1
pr: 旧#502
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | aedda9c9233a855390858b9132062f7081a06d3a | 0 | 2 | 0 | 2026-10-14T20:40+09:00 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | d383cd286b41c83abb4c41056ad502e42ab5b3cf | 0 | 1 | 0 | 2026-10-14T21:40+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| r1-1 | 独立-1 | medium | no | self-inflicted | request-scope | fixed | 依頼の 3 項目を、確認なしに assert を減らさない組み立ての変更へ狭めた。分け方はユーザーが返事で選んだ案（.request.md の 2 つ目の発言）に従い、PR 本文に項目ごとの行き先を書いた。commit: なし（PR 本文） |
| r1-2 | 独立-1 | medium | no | self-inflicted | doc-claim | fixed | 全量の時間を縮めたと断定するのに前後の数値が無い。断片の要約を変えた内容の記述にし、変えた 2 本の前後の時間を PR 本文に書いた。commit: d383cd28 |
| r1-3 | 独立-1 | low | no | self-inflicted | observability | accepted | log ごとに分けたので --durations の一覧で review-log の検査の合計が見えなくなる |
| r1-4 | 独立-1 | low | no | self-inflicted | test-hygiene | accepted | log ごとの repo の複製を tmp_path に作るので、pytest の既定の保持（直近 3 回）で約 320 個が残る |
| r1-5 | 独立-1 | low | no | self-inflicted | test-stability | accepted | 収集時に review-log/ を glob するので、収集中に review-log/ が変わると xdist の worker 間で収集が食い違い全体が止まる |
| r1-6 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | template の fixture は module scope なので、worksteal で module が交互に来ると worker ごとに 1 回にならない |
| r1-7 | 独立-1 | low | no | self-inflicted | test-power | accepted | unittest discover（DISTRIBUTION_READINESS.md:139）では pytest の関数になった後方互換の検査が走らない |
| r1-8 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 目的の「assert を減らさずに」に対し、worker cap のテストは worker の中で走った確認をやめた。PR 本文の目的を観測点の変更を含めて書き直した。commit: なし（PR 本文） |
| r1-9 | 独立-1 | advisory | no | inherited | doc-claim | out-of-diff | CONTRIBUTING.md:89 の addopts の引用に --maxprocesses=8 が無い |
| r1-10 | 独立-1 | advisory | no | self-inflicted | doc-claim | fixed | 断片が全部の review-log を検査すると書くが、対象は L1・L1+ のみ。commit: d383cd28 |
| r2-1 | 独立-2 | medium | no | self-inflicted | request-scope | accepted | setUp の共有・重複 helper の整理・列挙の間引きを別の PR に回すことに、ユーザーの確認の記録が無かった。2026-10-15 にユーザーが Fable の案（分ける。PR 本文の「次の PR」にスリム化を名指しで書き、その PR に follow_up_of: 502 を書く）を選んだ。PR 本文の「次の PR」に足した。commit: なし（PR 本文） |
| r2-2 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | 全量を測っていないのに「短縮は一部にとどまる」と書いた。PR 本文を「全量の時間が縮むかは測っていない」に改め、ローカルの全量の結果を書いた。commit: なし（PR 本文） |
| r2-3 | 独立-2 | advisory | no | inherited | doc-claim | accepted | 未リリースの断片 20260928-review-log-test-template-repo.md・20261004-pytest-worker-cap.md が、この PR で変えた 2 本のテストの古い仕組みを書いている |
| r2-4 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | 未参照の関数・クラスは見つからなかった、の探し方が無い。PR 本文に方法を書いた。commit: なし（PR 本文） |
| r2-5 | 独立-2 | low | no | self-inflicted | bookkeeping | fixed | 時間の表の変更後に測った commit の sha が無い。PR 本文に at <sha> を足した。commit: なし（PR 本文） |
| r2-6 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | module scope の fixture の docstring が「worker ごとに 1 回」と書くが、worksteal で別の module を挟むと作り直す |
