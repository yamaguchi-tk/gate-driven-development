---
lane: L1+
pr: 旧#211
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 方針メモ | Fable 設計レビュー (general-purpose, model: fable) + user | d9055507296a9943ec030504d451a14874dc36c9 | 0 | 0 | 0 | 2026-09-28T19:10+09:00 |
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 58edb46b66e2f28fdddfe6378fcc3e314fff8110 | 2 | 0 | 2 | 2026-09-28T20:10+09:00 |
| 独立-2 | light-lane-independent-reviewer, 差分, model: opus | b0c4b520b1440cd9b95acfc1836fe47c44926c7d | 0 | 0 | 0 | 2026-09-28T20:40+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| M1 | 方針メモ | advisory | no | inherited | none | accepted | 要約: なし（ユーザー指示で Opus の代わりに Fable に相談。推奨は「tip の証跡で解く・全 state.md を走査・0/2 件以上は止める・全角区切りの書き込み拒否は見送る」で、そのまま採用） |
| B1 | 独立-1 | high | yes | self-inflicted | tip-resolution-task-size | fixed | tip で選んだ steering の Task Size（trivial・quick。cancelled も選ばれる）で検査が緩み、止まっていた push が検査なしで通る。tip で解いたときは standard で parse・検査する（5518179c、adfdf577） |
| B2 | 独立-1 | high | yes | self-inflicted | hook-timeout | fixed | multiple のとき全 state.md を parse し、件数で hook の 10 秒 timeout（無出力で素通り）に近づく。tip の sha の先頭 7 桁を含む state.md だけを 1 回の grep で先に絞る（5518179c、f58e9439、adfdf577） |
| B3 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | TROUBLESHOOTING の pre-push の停止条件が実際より広い（作業中 1＋done 2 は found）（adfdf577） |
| B4 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 断片の「state.md が読めないときは止める」が実装（一致に数えないだけ）より広い（adfdf577） |
| B5 | 独立-1 | low | no | self-inflicted | test-power | fixed | 一致がいつも走査の先頭にあり、先頭を選ぶ変異が生き残る。一致を 2 件目に置くテストを足した（5518179c）。tag の sha の peel は先に絞る設計と合わず外した（f58e9439） |
| B6 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | SessionStart の警告文が「pre-push も止まる」と条件なしで言い切る。PR 本文に列挙 |
| B7 | 独立-1 | advisory | no | self-inflicted | bookkeeping | accepted | 断片の type: patch と minor の妥当性。PR 本文に列挙 |
| C1 | 独立-2 | medium | no | self-inflicted | tip-prefilter-symmetry | next-pr | 先に絞る grep（tip の先頭 7 桁）と rev-parse ^{commit} の比較で受理集合が違い、tag の sha の証跡が落ちて一致 2 件が 1 件になりうる。比較に先頭一致を足し、コメント・断片・self-review-lanes をそろえる |
| C2 | 独立-2 | medium | no | self-inflicted | test-power | next-pr | 時間比のテストは prefilter を外す変異を見分けられない見込み（見積もり）。rev-parse の呼び出し回数を数えるテストにする |
| C3 | 独立-2 | low | no | self-inflicted | doc-claim | next-pr | テストモジュールの docstring が「以降の検査（Task Size・dry・Independent Review）」のまま |
| C4 | 独立-2 | low | no | self-inflicted | doc-claim | next-pr | 断片の「steering の件数で hook の時間を増やさない」が resolver を含む hook 全体の保証に読める |
| C5 | 独立-2 | low | no | self-inflicted | product | next-pr | tip で選んだ steering の block 文言が、standard として検査したことと復旧の手順を伝えない |
| C6 | 独立-2 | low | no | self-inflicted | doc-claim | next-pr | 「write・pre-push・pre-PR が同じ Task Size を渡す」が tip の経路で成り立たない（quick の steering に委譲形を書くと write guard が拒む） |
