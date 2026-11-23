---
lane: L1
pr: 578
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 0b09dd998ea244125522d913a38ef56af842e5a2 | 0 | 8 | 0 | 2026-10-24T16:05+09:00 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | ac733c764793fb287af6d3cbcf235beb949a0faa | 0 | 3 | 0 | 2026-10-26T10:09+09:00 |
| 独立-3 | light-lane-independent-reviewer-xhigh, 差分（無効化後）, model: opus | b92712904961cfea168e1c67466c8f3a20d58320 | 0 | 4 | 0 | 2026-10-26T11:50+09:00 |
| 独立-4 | light-lane-independent-reviewer-xhigh, 差分（無効化後）, model: opus | 1a92dbcd245f3eaefe1fa90e7f1408cfd0c8233a | 0 | 2 | 0 | 2026-10-26T13:45+09:00 |
| 独立-5 | light-lane-independent-reviewer-xhigh, 差分（無効化後）, model: opus | 795c2d94b2f36361d8ff5e5e238dd1e508955f89 | 0 | 0 | 0 | 2026-10-26T14:20+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| r1-1 | 独立-1 | medium | no | self-inflicted | request-drift | accepted | 確認待ち: 依頼の出典の steering から作ったケースが 0 件で、missed を 4 ケース（既知 6 件）に絞った。review-log には PR後-N の high が 43 行ある。ケースの書式に repo の欄が無い |
| r1-2 | 独立-1 | medium | no | self-inflicted | doc-claim | accepted | 基準の実行の節が未記入なのに、断片は結果があると書いていた（基準の結果は予定どおり文書に書いた。振り分けでは直すものに数えない） |
| r1-3 | 独立-1 | medium | no | self-inflicted | cost-cap | accepted | 時間切れ・読めない出力の run を費用 $0 で数え、費用の上限が効かない。予約額に写し役の分が入っていない |
| r1-4 | 独立-1 | medium | no | self-inflicted | tally | accepted | error・budget の run を 2 つ目の表で「hit なし」に、一部 error のケースを「全 run で hit」に数える。error があっても exit 0 |
| r1-5 | 独立-1 | medium | no | self-inflicted | leak | accepted | reviewer の読める範囲（--add-dir の plugin 全体と case_dir）に、直した後のコード・断片・ケースの JSON・前の run の出力と、tip の版の reference がある。基準の 30 本の transcript では、plugin 側で開いたのは reviewer-common.md と testing-anti-patterns.md だけだった |
| r1-6 | 独立-1 | medium | no | self-inflicted | plugin-identity | accepted | --plugin-dir と、入っている同じ名前の plugin のどちらの agent 定義で回るかを確かめず、記録もしない |
| r1-7 | 独立-1 | medium | no | self-inflicted | severity-map | accepted | 重さの判定が impl-gating と違う（category の表記ゆれ・9 値の外・failure scenario の無い high） |
| r1-8 | 独立-1 | medium | no | self-inflicted | test-power | accepted | テストが summary の 2 つ目の表の値・絶対パスの当て方・medium の実害クラス・env・budget の再開を固定していない |
| r1-9 | 独立-1 | low | no | self-inflicted | request-drift | accepted | 確認待ち: 回す条件を「reviewer の定義」から「reviewer が読む policy」へ、範囲を開いたまま広げた |
| r1-10 | 独立-1 | low | no | self-inflicted | matching | accepted | 当て方が貪欲で、reviewer の出力の順で hit の数が変わる |
| r1-11 | 独立-1 | low | no | self-inflicted | resume | accepted | 結果を使い直すときに、どの agent・plugin・ケースの版で回したかを確かめない |
| r1-12 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 限界の節の missed が少ない理由（71 件中 4 件）が、missed の出どころ（PR後-N）と合わない |
| r1-13 | 独立-1 | low | no | self-inflicted | case-kind | accepted | M02・M04 の tip は独立レビューが high を出した後の sha で、独立レビューが見た sha ではない |
| r1-14 | 独立-1 | low | no | self-inflicted | empty-output | accepted | reviewer の出力が空でも、写し役の行が崩れていても、ok として全部 miss に数える |
| r1-15 | 独立-1 | low | no | self-inflicted | robustness | accepted | 書きかけの result.json や dict でない JSON で runner 全体が落ちる |
| r1-16 | 独立-1 | low | no | self-inflicted | env-isolation | accepted | --strict-mcp-config が無く、利用者の MCP と settings に評価が左右される。使ったモデルを残さない |
| r1-17 | 独立-1 | low | no | self-inflicted | bookkeeping | accepted | CONTRIBUTING の新しい手順（条件に当たったときだけ回す）の当たる件数が、PR 本文の目的の節に無い |
| r1-18 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | PR 本文の CONTRIBUTING・weak・missed の単位の書き方が差分と合わない（commit: なし（PR 本文）） |
| r1-19 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | docstring の「末尾の path 要素で一致」がコードと違う |
| r1-20 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 「budget と記録し、exit 3 で終わる」と書くが、その後も残りの run を始める |
| r1-21 | 独立-1 | advisory | no | self-inflicted | style | accepted | 写し役の値の縦棒を置き換える処理は何もしていない（分けた後の値に縦棒は無い） |
| r1-22 | 独立-1 | advisory | no | self-inflicted | changelog | accepted | 断片の User Action Required が「なし」の後に手順を書いている |
| r1-23 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | CONTRIBUTING の構成の説明（docs/・evals/）が新しいファイルと合わない |
| r1-24 | 独立-1 | advisory | no | self-inflicted | robustness | accepted | --only に知らない id を渡しても 0 件で exit 0 |
| r2-1 | 独立-2 | medium | no | self-inflicted | doc-claim | accepted | M01〜M04／M05〜M07 の分け方が review-log の行と合わない（直前の独立レビューが high を出したのは M02・M04 だけ） |
| r2-2 | 独立-2 | medium | no | self-inflicted | severity-map | accepted | missed の期待値の一部（M05 の F6、M06 の F21・F22）は、今の reviewer-common の適用範囲では weak が上限で、hit を主な指標にすると規則どおりの変更が「減った」と見える |
| r2-3 | 独立-2 | medium | no | self-inflicted | request-drift | accepted | 確認待ち: CONTRIBUTING の発火条件を agents/gdd-*-reviewer.md と reviewer-common.md に狭め、implementation reviewer が名指しする testing-anti-patterns.md などが外れた |
| r2-4 | 独立-2 | medium | no | self-inflicted | request-drift | re-reported | 確認待ち: missed の候補を基準の実行の予算（$40）を理由に外した（r1-1 の再掲） |
| r2-5 | 独立-2 | low | no | self-inflicted | request-drift | re-reported | 確認待ち: steering を出典から外した判断と数えた範囲（46 slug と finding-dispositions.md の 71 件の違い）（r1-1 の再掲） |
| r2-6 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 「found の hit は run 2 で 7 件」が表の合計 6 件と合わない |
| r2-7 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 「基準の 30 本の transcript」と「36 本とも ok」が合わない |
| r2-8 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | found の 28 件のうち F05〜F08 の 7 件は xhigh の差分巡で見つけたもので、「max が見つけた」に当たらない |
| r2-9 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | ケースの JSON の description が、docs で変えた missed の定義のまま残っている |
| r2-10 | 独立-2 | low | no | self-inflicted | case-kind | accepted | M06 に、規則上は入る F25（PR後-1・medium・実害 yes・fixed）が無い |
| r2-11 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | CONTRIBUTING は planning reviewer の変更でも評価を求めるが、docs は planning に当てるケースが無いと書く |
| r2-12 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | security・completion reviewer を --agent で回す案内に裏付けが無い（review-input が成果物の無い 1 枚） |
| r2-13 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | docs で足した 3 つの限界（読める範囲・plugin の同名・missed の件数）が PR 本文の限界の節に無い |
| r2-14 | 独立-2 | low | no | self-inflicted | cost-cap | accepted | 18 ケースで基準が $35.88 になり、既定の上限 $40 では reviewer の費用が少し増えるだけで残りの run が budget になり、集計が偏る |
| r2-15 | 独立-2 | low | no | self-inflicted | leak | re-reported | reviewer が --add-dir でケースの答えと前の run の出力を読める（r1-5 の再掲） |
| r2-16 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | $35.88＋$1.33 が $37.22 と書かれている（1 セントずれる） |
| r3-1 | 独立-3 | medium | no | self-inflicted | request-drift | fixed | 確認済み（2026-10-26、問い 1 は残りを足す）: 「missed の残りの候補を足して」に、1 PR 2 ケースの規則を当てて 14 巡を外した（commit: 1a92dbcd） |
| r3-2 | 独立-3 | medium | no | self-inflicted | request-drift | fixed | 確認済み（2026-10-26、全部回し直す）: 「基準の実行を回し直して」で、60 本のうち 37 本は 10-24 の結果の使い直し。本文の基準の行に 2 日の混在を書いていない（commit: 1a92dbcd。新しい出力先で 88 本を回し直した） |
| r3-3 | 独立-3 | medium | no | self-inflicted | bookkeeping | fixed | 依頼の写しに、ユーザーが番号で指した問い 1〜3 と推奨の文が引用されていない（commit: なし（review-log）。request.md に引用を足した） |
| r3-4 | 独立-3 | medium | no | self-inflicted | doc-claim | accepted | 「基準の 30 本の transcript」が 60 本の基準のどれかを書かず、10-26 の 23 本で答えの JSON を開いていないかを確かめていない |
| r3-5 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | 「同じ PR では若い巡を選んだ」が PR 94（M07 の PR後-3 を残し PR後-2 を外した）と合わない |
| r3-6 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | 「1 回の比較が約 $60」は、前後を別々に回すので約 $120 |
| r3-7 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | 「行から全部選んだ」が、M06 の F25・M05 の F7 が入っていないことと合わない |
| r3-8 | 独立-3 | low | no | self-inflicted | doc-claim | re-reported | ケースの JSON の description が missed の定義の古いまま（r2-9 の再掲） |
| r3-9 | 独立-3 | advisory | no | self-inflicted | case-kind | accepted | M19 の P1 と M13 の F2 は CI・環境の観測で見つかったもので、外部レビューの指摘に入りにくい |
| r3-10 | 独立-3 | advisory | no | self-inflicted | doc-claim | re-reported | 「found の hit は run 2 で 7 件」が表の 6 件と合わない（r2-6 の再掲） |
| r4-1 | 独立-4 | medium | no | self-inflicted | request-drift | fixed | 問い 1 が名指しした残りの候補（旧#140 の PR後-1 の U1・U2）を「直した commit が無い」として外したが、旧#141 は 旧#156 で直っていた。同じ見方で 旧#124 の PR後-2 の X2・X3（旧#125・旧#126 → 旧#218）も直っていた。ユーザーが足すよう答えた候補なので、確認せずに M34・M35 を足した（commit: d446cf61） |
| r4-2 | 独立-4 | medium | no | self-inflicted | case-kind | accepted | missed の多くは reviewer-common の severity の上限（検査スクリプト・warn-only の lint と hook）がかかる部品で、方針どおりなら weak になる。docs はそれを reviewer の見逃しとして書いている |
| r4-3 | 独立-4 | low | no | self-inflicted | runner-reuse | accepted | 使い回しの鍵が case id と run 番号だけで、ケースを変えた後に同じ `--out` で回すと古い wt と結果が混ざる |
| r4-4 | 独立-4 | low | no | self-inflicted | case-check | accepted | `--check` が base の祖先関係と fix_commit の触ったファイルを見ず、M30 の base の誤りを通しうる |
| r4-5 | 独立-4 | low | no | self-inflicted | doc-claim | fixed | PR 本文の「1 回の比較が約 $90」は前後 2 回の起動で約 $175（commit: なし（PR 本文）） |
| r4-6 | 独立-4 | advisory | no | self-inflicted | doc-claim | accepted | 新しい基準の実行の出力先が docs に無い |
| r5-1 | 独立-5 | low | no | self-inflicted | doc-claim | accepted | PR ごとの件数の列挙が「ほかは 1」のままで、M35 を足した 旧#124 は 2 件になる |
| r5-2 | 独立-5 | advisory | no | self-inflicted | doc-claim | accepted | 基準の実行の出力先が docs に無く、結果を後から辿れない（r4-6 と同じ） |
| r5-3 | 独立-5 | advisory | no | self-inflicted | doc-claim | accepted | 旧#124 の X1 を除いた理由「対応不要で閉じた」が、同じ PR の J1 の修正で一部を閉じた記録と合わない |
