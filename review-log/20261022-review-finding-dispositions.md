---
lane: L1+
pr: 旧#568
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 1d56da2e792febdee00da0e12533a20eb666895a | 1 | 4 | 0 | 2026-10-22T18:00+09:00 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 1afc423074aceee00bd42cb1405a8a6ab65f4135 | 0 | 1 | 0 | 2026-10-22T19:00+09:00 |
| 独立-3 | light-lane-independent-reviewer, 全差分（無効化後）, model: opus | 00a8499db206ce1bda98b4598ccb9c7bff9b00f6 | 0 | 8 | 0 | 2026-10-23T12:00+09:00 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| r1-1 | 独立-1 | high | no | self-inflicted | numbering | fixed | 設計: 変える（節の番号を task ごとの Gate Rounds から取る決定）。IG 節の番号が task ごとの Gate Rounds 依存で、2 回目の Round・2 つ目の task で重なり検査が ok にならない。IG・IR を steering 通しの連番にし検査に足した。commit: 1afc4230 |
| r1-2 | 独立-1 | medium | no | self-inflicted | count-path | accepted | rejected:duplicate の参照元の severity・category を見ないので、high を duplicate にして low を残すと独立レビューの件数から high が消える |
| r1-3 | 独立-1 | medium | no | self-inflicted | test-power | accepted | 今回の Round の IG 節が丸ごと無くても CLI は ok を返す |
| r1-4 | 独立-1 | medium | no | self-inflicted | request | accepted | 確認済み（2026-10-23、未測のまま足す）: 新しい発火条件を未測のまま足すことにユーザーの発言が無い。Independent Review 行を持つ steering の件数も PR 本文に無い |
| r1-5 | 独立-1 | medium | no | self-inflicted | request | accepted | 確認済み（2026-10-23、入れてからマージ。検証役を足した）: 検証役を入れない狭め方にユーザーの返事が無い |
| r1-6 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | check-gate-ledger.sh の header の直す行の列挙に independent-review が無い |
| r1-7 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 断片が gdd-completion-check の変更を書いていない |
| r1-8 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | PR 本文の挙動の変化に、直す行への independent-review の追加と、既存 steering で findings 行が missing になる点が無い。commit: なし（PR 本文） |
| r1-9 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 行き先 blocking の説明が件数の数え方（severity・category）と食い違う |
| r1-10 | 独立-1 | low | no | self-inflicted | bookkeeping | accepted | Step 1・1d の出口の Round は Step 8 を通らず IG 節を書かない |
| r1-11 | 独立-1 | low | no | self-inflicted | count-path | accepted | IR 節と Independent Review 行の sha を完全一致で比べ、gate の先頭一致と食い違う |
| r1-12 | 独立-1 | low | no | self-inflicted | test-power | accepted | findings 行の例外経路（ディレクトリ・非 UTF-8）を固定するテストが無い |
| r1-13 | 独立-1 | low | no | self-inflicted | product | accepted | 表は raw steering にあり、マージ後の cleanup で消えるので後で数えられない |
| r1-14 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | gdd-pr-review-followup の Independent Review 行の blocking の数え方が duplicate を数え、finding-dispositions.md と食い違う |
| r1-15 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 前回の指摘の解消は ID で追えるだけで機械では突き合わせない |
| r1-16 | 独立-1 | advisory | no | self-inflicted | product | accepted | findings の値が大きいと連番の list が重くなる |
| r1-17 | 独立-1 | advisory | no | self-inflicted | product | accepted | CLI の出力を UTF-8 にそろえていない |
| r1-18 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 断片に breaking に当たらない理由が無い |
| r1-19 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | ADR の番号が別の repo のものだと分からない |
| r1-20 | 独立-1 | advisory | no | self-inflicted | product | accepted | 表の欄のタブで出力の 4 欄が崩れる |
| r1-21 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | reviewer の行だけ並び順まで問う |
| r1-22 | 独立-1 | advisory | no | self-inflicted | doc-claim | fixed | 上限を上げた分の PR 本文の説明がずれている。commit: なし（PR 本文） |
| r2-1 | 独立-2 | medium | no | self-inflicted | request | re-reported | r1-5 の再掲（検証役を入れない狭め方にユーザーの返事が無い） |
| r2-2 | 独立-2 | medium | no | self-inflicted | test-power | accepted | 足した連番の条件が新しく止めるのは番号の飛びと順序違いだけで、止める損失が PR 本文に無い |
| r2-3 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | PR 本文の挙動の変化に、節の番号の連番の検査と findings 行が形の誤りでも invalid になる点が無い。commit: なし（PR 本文） |
| r2-4 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 追記専用の規定と、前の節の番号の誤りを直させる検査がぶつかりうる |
| r2-5 | 独立-2 | advisory | no | self-inflicted | test-power | accepted | test_main_carried_row_must_be_re_reported の fixture が IR2 単独で、2 つの理由で invalid になる |
| r2-6 | 独立-2 | advisory | no | self-inflicted | test-power | accepted | 重複の検査が連番の検査に包まれ、重複の検査そのものは固定されていない |
| r2-7 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | 断片の User Action Required に、最初の IR 節は IR1 と書いていない |
| r2-8 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | Step 8 が IG だけで数えることを書いていない |
| r3-1 | 独立-3 | medium | no | self-inflicted | request | accepted | 確認待ち: 検証役が判定するのは捨てる・下げる行の一部だけで、採った行・out_of_scope・素の advisory などは通らない。依頼の「各指摘の妥当性を判定し、合意したものだけを人に出す」より狭い |
| r3-2 | 独立-3 | low | no | self-inflicted | request | accepted | 確認待ち: 並行の finder を置かないことをユーザーに確かめていない |
| r3-3 | 独立-3 | low | no | self-inflicted | doc-claim | fixed | PR 本文が、検証役の起動も未測のまま足すことをユーザーが確かめたと書いている（確かめたのは検査の停止点だけ）。commit: なし（PR 本文） |
| r3-4 | 独立-3 | medium | no | self-inflicted | doc-claim | accepted | dialectic-review.md の Host Adapter の統合で、Cursor・Codex の Final synthesizer の model が変わり、cursor.md・codex.md・gdd-model-routing と食い違う |
| r3-5 | 独立-3 | medium | no | self-inflicted | product | accepted | high・実害クラスの advisory:unverified_file は検証役の refuted が要るが、根拠ファイルが無いと検証役は unverifiable を返すので、Step 1c の誤検知が差し戻しになる |
| r3-6 | 独立-3 | medium | no | self-inflicted | product | accepted | 同じ sha の IR 節が 2 つになると findings 行が invalid のまま直せない |
| r3-7 | 独立-3 | medium | no | self-inflicted | product | accepted | followup で PR レビューの指摘を Independent Review の件数に足すと IR 節に書けず invalid になる |
| r3-8 | 独立-3 | medium | no | self-inflicted | doc-claim | accepted | Step 8・changelog・PR 本文が検証役の範囲を実際より広く書いている |
| r3-9 | 独立-3 | medium | no | self-inflicted | test-power | accepted | 実害クラスは calibration で advisory にできない規則をテストが固定していない |
| r3-10 | 独立-3 | medium | no | self-inflicted | product | accepted | fixed-models.md に検証役の行が無く、Codex・Cursor の起動経路が無い |
| r3-11 | 独立-3 | low | no | self-inflicted | product | accepted | impl-gating での re-reported の扱いが決まっていない |
| r3-12 | 独立-3 | low | no | self-inflicted | product | accepted | duplicate の参照先の行き先を見ないので、refuted の行の duplicate にすれば high を検証役に見せずに捨てられる |
| r3-13 | 独立-3 | low | no | self-inflicted | product | accepted | impl-gating で high・実害クラスの advisory:out_of_scope をどの巡でも通す |
| r3-14 | 独立-3 | low | no | self-inflicted | doc-claim | fixed | 正本の限界のうち、表が cleanup で消えることと Round の節が丸ごと無い形が PR 本文に無い。commit: なし（PR 本文） |
| r3-15 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | 再報告で人に戻す経路の範囲があいまいで PR 本文に無い |
| r3-16 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | 検査を回す時点の記述が判定の前と後で食い違う（PR 本文の分は直した） |
| r3-17 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | check-gate-ledger.sh 冒頭の説明が independent-review を含まない |
| r3-18 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | subagent-dispatch.md の「この表」が指す表が無い |
| r3-19 | 独立-3 | low | no | self-inflicted | bookkeeping | accepted | changelog の断片の Validation・Affected Files にテストが無く、新しい agent が Changed にある |
| r3-20 | 独立-3 | low | no | self-inflicted | test-power | accepted | ledger 側の例外の経路にテストが無い |
| r3-21 | 独立-3 | low | no | self-inflicted | test-power | accepted | refuted の行も数えることが high でしか固定されていない |
| r3-22 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | README の agents 一覧に検証役が無い |
| r3-23 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | 検証役の材料の欄の名前（problem・evidence）が reviewer の出力に無い |
| r3-24 | 独立-3 | low | no | self-inflicted | product | accepted | security reviewer が findings: を出す保証が無い |
| r3-25 | 独立-3 | low | no | self-inflicted | style | accepted | テストの class 名がコピーのまま |
| r3-26 | 独立-3 | advisory | no | self-inflicted | product | accepted | 欄のタブで出力の欄が増える |
| r3-27 | 独立-3 | advisory | no | self-inflicted | product | accepted | IR 節と行の sha を文字列どおりに比べる |
| r3-28 | 独立-3 | advisory | no | self-inflicted | style | accepted | 限界の 1 行に種類が無い |
| r3-29 | 独立-3 | advisory | no | self-inflicted | doc-claim | accepted | file:line 欄の書き方が決まっておらず、絶対パスは steering の書き込みの検査に止められる |
