---
lane: L1
pr: 472
follow_up_of: 444
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | d80a777b | 1 | 0 | 1 | 2026-10-13 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 8a241dd8 | 0 | 0 | 0 | 2026-10-13 |
| 独立-3 | light-lane-independent-reviewer, 全差分（無効化後）, model: opus | fdcb738d | 1 | 1 | 1 | 2026-10-14 |
| 独立-4 | light-lane-independent-reviewer-xhigh, 差分（無効化後）, model: opus | c6de3a0f | 0 | 0 | 0 | 2026-10-14 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| K1-1 | 独立-1 | high | yes | self-inflicted | fail-open | fixed | Step 13 が返った直後に Completion Reviewed Through を書くので、Round の結果を書く前に runner が止まり、再実行までに commit が入ると、Step 13 が指摘した箇所が advisory に落ちて done に届く。差し戻しか Step 19 の停止の結果を書き終えた後の最後に書く形にした。commit: 110e9d52 |
| K1-2 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 「欠落」の定義が SKILL:48（Step 13 より前だった Round の後を含む）と手順 6（すべて Step 13 より前）で違う。どちらに読んでも安全側。PR 本文の限界に書いた |
| K1-3 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 書く条件の「判定を返したら」「その判定に渡した tip」が、reviewer の実際の入出力（finding の一覧、sha は渡さない）を指していない。出力が返った Round で、Step 13 で reviewer を起動する直前の HEAD を書く形にした。commit: 110e9d52 |
| K1-4 | 独立-1 | low | no | self-inflicted | bookkeeping | accepted | 節名「Completion Rounds / Completion Baseline の操作手順」に新しい field の名前が無い。PR 本文の限界に書いた |
| K1-5 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | gdd-task-breakdown SKILL:55 だけ「`Completion` で始まる 3 つの field」と接頭辞で書き、ほかの 5 か所と書き方がそろっていない。PR 本文の限界に書いた |
| K1-6 | 独立-1 | low | no | self-inflicted | bookkeeping | accepted | 断片の Affected Files に変えたテストのファイルが無い。PR 本文の限界に書いた |
| K1-A1 | 独立-1 | advisory | no | self-inflicted | request-drift | fixed | 依頼の「Opus と設計を相談してから直し」の記録が抜粋に無い。PR 本文に相談の記録を書いた。commit: なし（PR 本文） |
| K1-A2 | 独立-1 | advisory | no | self-inflicted | bookkeeping | fixed | skill 本文を変えたのに Skill RED-GREEN Evidence が抜粋・断片に無い。PR 本文に書いた。commit: なし（PR 本文） |
| K1-A3 | 独立-1 | advisory | no | inherited | test-power | accepted | 書き換えたテストの pin は文の有無だけを見ていて、差分の起点の挙動は固定していない |
| K1-A4 | 独立-1 | advisory | no | self-inflicted | product | accepted | completion gate の判定を替えるので、L1+ に当たるとも読める（旧#444 と同じく L1 で進めた） |
| K1-A5 | 独立-1 | advisory | no | self-inflicted | product | accepted | Baseline の値を読む箇所が無くなったが、手順 2 は値を更新し続け、SKILL は「カウンタ」と呼ぶ |
| K2-1 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 正本（手順 4）だけ書く出口の範囲が広く読め、Step 14 の human_recheck・Step 21 の cancelled・Step 20 の done の後に書くかが分かれる。どの読み方でも素通りは起きない。PR 本文の限界に書いた |
| K2-2 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 欠落の説明「Step 13 がまだ判定を返していない」が、Step 13 が返っても行が無い場合（Step 14・21 で終わった、書き終える前に止まった）を含まない。挙動は全量で変わらない。PR 本文の限界に書いた |
| K2-3 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 断片 :9 が「Step 19 で止まった後の再実行は差分スコープ」と条件なしに書く（commit が無ければ diff が空で全量）。PR 本文は直した。断片は PR 本文の限界に書いた |
| K2-A1 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | Step 13 の起動手順に、起動の直前に HEAD を控える指示が無い（再実行ではどちらの直前かも決まっていない） |
| K2-A2 | 独立-2 | advisory | no | self-inflicted | doc-claim | fixed | PR 本文の目的の「推奨のとおり」が、書く時点を絞ったことを言っていない。PR 本文を直した。commit: なし（PR 本文） |
| K3-1 | 独立-3 | high | yes | self-inflicted | fail-open | fixed | 全量に戻す条件が「解決不能 sha」だけで、Completion Reviewed Through が HEAD の祖先でない（reset・rebase で commit が落ちた）ときに差分スコープになり、Step 13 が通した修正の消失が diff に出ない（origin: pre-existing。Baseline の時代からの欠落を引き継いだ）。祖先でないときも全量にした。commit: 3a82b279 |
| K3-2 | 独立-3 | medium | no | self-inflicted | request-drift | fixed | Step 19 の停止でも field を書くので、依頼に無い Step 19 の後の再実行まで全量から差分スコープに狭めていた。書くのを差し戻し（Round 上限超過を含む）のときだけにし、依頼の範囲に戻した。commit: 3a82b279 |
| K3-3 | 独立-3 | low | no | self-inflicted | doc-claim | fixed | 書く契機が正本（Round の結果を書き終えた後）と 3 つの要約（差し戻すか Step 19 で止めるとき）で食い違い、Step 14・20 の後に書くかが分かれる。正本に差し戻し以外の出口を書かないと列挙し、要約を差し戻しのときにそろえた。commit: 3a82b279 |
| K3-4 | 独立-3 | low | no | self-inflicted | product | accepted | HEAD を控える指示と field を書く指示が、Step 13 の本文と State Update Contract に無い。書き忘れても全量か広い側に倒れる。PR 本文の限界に書いた |
| K3-5 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | 「Step 13 が見ていない変更はすべて diff に入る」が、未 commit の変更などを含まず言い過ぎ。PR 本文の限界に書いた |
| K3-6 | 独立-3 | low | no | self-inflicted | bookkeeping | accepted | 断片の Validation に Skill RED-GREEN Evidence の行が無い（PR 本文には書いた）。PR 本文の限界に書いた |
| K3-7 | 独立-3 | low | no | self-inflicted | doc-claim | fixed | 断片が Step 19 の再実行を条件なしに差分スコープと書いている。Step 19 では書かなくなったので、その文を消した。commit: 3a82b279 |
| K3-8 | 独立-3 | low | no | self-inflicted | doc-claim | fixed | PR 本文の「Step 13 の出力が返っていない停止の後は field が無いので全量」が、前の Round で Step 13 が返っているときに成り立たない。PR 本文を直した。commit: なし（PR 本文） |
| K3-9 | 独立-3 | low | no | self-inflicted | style | re-reported | Checklist E の節名に新しい field の名前が無い（K1-4 と同じ） |
| K3-10 | 独立-3 | low | no | self-inflicted | style | re-reported | gdd-task-breakdown の SKILL だけ 3 つの field を名前で挙げていない（K1-5 と同じ） |
| K3-A1 | 独立-3 | advisory | no | self-inflicted | bookkeeping | fixed | テンプレート外の記述あり（PR 本文の抜粋の目的に、前の PR の revert の経緯と Opus への相談の過程）。次の巡の抜粋から除いた。commit: なし（PR 本文） |
| K3-A2 | 独立-3 | advisory | no | self-inflicted | doc-claim | accepted | 未リリースの断片（20261012-gate-result-completion-timeout）に、置き換えた「Rounds が 0 なら全量」の規則が残る |
| K3-A3 | 独立-3 | advisory | no | self-inflicted | doc-claim | re-reported | Baseline の値は読まれないのに、手順 2 は差分の起点の意味で更新を書いている（K1-A5 と同じ） |
| K4-1 | 独立-4 | low | no | self-inflicted | doc-claim | accepted | 欠落の説明「Step 13 がまだ判定を返していない」が、書くのを差し戻しだけにした後の条件（Step 13 が返っても Step 19・Step 14 で止まれば行が無い）と合わない。動きは全量で変わらない。PR 本文の限界に書いた |
| K4-2 | 独立-4 | low | no | inherited | doc-claim | fixed | PR 本文の目的の例「Step 2a」は、+1 を gdd-systematic-debugging のときだけとする読みでは Baseline を進めず、断定が当たらない。例を Step 4 などの gdd-systematic-debugging に戻す出口に替えた。commit: なし（PR 本文） |
| K4-A1 | 独立-4 | advisory | no | inherited | doc-claim | accepted | 書く順序の括弧が、Baseline の更新・task の再オープン・gate結果 の行など、その Round の書き込みを全部は挙げていない |
