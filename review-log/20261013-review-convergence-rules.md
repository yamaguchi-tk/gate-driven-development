---
lane: L1
pr: 446
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | f548c265 | 2 | 4 | 1 | 2026-10-13 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 8d1d9bad | 2 | 1 | 3 | 2026-10-13 |
| 独立-3 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 844e912c | 0 | 1 | 0 | 2026-10-13 |
| 独立-4 | light-lane-independent-reviewer-xhigh, 差分（無効化後）, model: opus | fd380e24 | 0 | 1 | 0 | 2026-10-13 |
| 独立-5 | light-lane-independent-reviewer-xhigh, 差分（無効化後）, model: opus | a3fcb237 | 0 | 0 | 0 | 2026-10-13 |
| 独立-6 | light-lane-independent-reviewer, 全差分（無効化後）, model: opus | c38ebb66 | 0 | 0 | 0 | 2026-10-13 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| F1 | 独立-1 | high | no | self-inflicted | test-guard | fixed | (3-f) が 750 字を超える 1 行で、出力フォーマットの文の挿入も pin と合わず、doc guard の 2 件が落ちる。(3-f) を 2 行に割り、pin を足した。commit: 6086aa45 |
| F2 | 独立-1 | high | yes | self-inflicted | fail-open | fixed | (3-f) の基準を main が当てて reviewer の high を medium に数え直せる。main は reviewer の severity を変えずに数えると書いた。commit: 16ea8dfc |
| F3 | 独立-1 | medium | no | self-inflicted | product | next-pr | Decision の対象が「など」で開いていて、当たるか判定できないときの既定が無い |
| F4 | 独立-1 | medium | no | self-inflicted | product | next-pr | 昇格処理の順序 2（新値 < 3 で通常差し戻し）が先に評価され、(3-f) の例外が 3 の括弧の中にしか無い |
| F5 | 独立-1 | medium | no | self-inflicted | product | next-pr | 取り直しの回数と「前回の high がすべて Decision」の判定を記録する置き場が無い |
| F6 | 独立-1 | medium | no | self-inflicted | product | fixed | 事前回答 3 の「上限で残った blocking を accept」が受け入れより優先し、受け入れが働かない。3 から除き、対象を Round 上限の一括提示に絞った。commit: 16ea8dfc |
| F7 | 独立-1 | medium | no | self-inflicted | product | fixed | Medium Disposition は人の承認なしに書けるので、事前回答の文から届かない。Medium Disposition の文を外し、検討の結果を PR 本文に書いた。commit: 16ea8dfc |
| F8 | 独立-1 | medium | no | self-inflicted | product | fixed | 受け入れの許可だけの発話を記録する形が無い。自走上限を今の値にして 1 の行を書くとした。commit: 16ea8dfc |
| F9 | 独立-1 | medium | no | self-inflicted | product | fixed | 依頼の 4 の doc guard（このテスト）に触れずに限界にしていた。pin を足し、root CLAUDE.md § テストとのぶつかりを PR 本文に書いた。commit: 6086aa45 |
| F10 | 独立-1 | low | no | self-inflicted | product | next-pr | 後続の test の要件の申し送り先と、それを読む経路が無い |
| F11 | 独立-1 | low | no | self-inflicted | doc-claim | next-pr | agent の「列挙なら Medium」と (3-f) の high が、実装仕様だけの Decision で食い違う |
| F12 | 独立-1 | low | no | self-inflicted | doc-claim | next-pr | `閉じ方: 列挙` を修正案ではなく Decision の文に当てている |
| F13 | 独立-1 | low | no | self-inflicted | product | next-pr | reviewer-common.md § 常時 High と followup の Classify が (3-f) に触れていない |
| F14 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 契約 3 の前置きが (3-a)〜(3-e) のまま。(3-a)〜(3-f) にした。commit: 6086aa45 |
| F15 | 独立-1 | low | no | self-inflicted | product | next-pr | self-review-lanes.md と pr-review-followup の「是正して再実行」が取り直しの上限を指していない |
| F16 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 受け入れが 2 の原文の照合を明記していない。受け入れを 2 の中に移した。commit: 6086aa45 |
| F17 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 断片が範囲の条件を落とし、届かない Medium Disposition を書き、Validation にテストが無い。commit: 16ea8dfc |
| F18 | 独立-1 | advisory | no | self-inflicted | doc-claim | fixed | PR 本文の「4 ファイル」が 5 つと合わない。commit: なし（PR 本文） |
| F19 | 独立-1 | advisory | no | self-inflicted | doc-claim | fixed | RED-GREEN Evidence の置き場が PR 本文から分からない。commit: なし（PR 本文） |
| F20 | 独立-1 | advisory | no | self-inflicted | bookkeeping | accepted | レビュー中に作業ツリーが tip から変わった。差分巡で確かめる |
| F21 | 独立-1 | advisory | no | inherited | product | accepted | この repo の軽いレーンの reviewer には (3-f) が届かない。plugin の外 |
| F22 | 独立-1 | advisory | no | self-inflicted | doc-claim | fixed | 「同 § Fix の影響範囲」「§ 常時 High」がどのファイルの節か読み違えうる。ファイル名を書いた。commit: 16ea8dfc |
| G1 | 独立-2 | high | yes | self-inflicted | approval-path | fixed | 受け入れだけの発話から事前回答の行ができ、その steering の承認ポイントまで人を通らない。依頼の場面にも届かないので、事前回答の受け入れを外し、検討の結果を PR 本文に書いた。commit: b728a09e |
| G2 | 独立-2 | high | yes | self-inflicted | fail-open | fixed | 「(3-a) の全量に代わる」が (3-a) の fail-closed の条件（履歴の書き換え・証跡が無効・差分が空）まで上書きして読める。1 つ目の条件にだけ代わると書いた。commit: b728a09e |
| G3 | 独立-2 | medium | yes | self-inflicted | approval-path | fixed | 受け入れの条件に「1 件以上」が無く、指摘 0 件の timeout の一括提示にも当たる。受け入れを外した。commit: b728a09e |
| G4 | 独立-2 | medium | no | self-inflicted | product | next-pr | (3-f) と reviewer-common.md § 常時 High の優先が書かれておらず、reviewer が常時 High に従うと (3-f) が効かない |
| G5 | 独立-2 | medium | no | self-inflicted | product | next-pr | (3-f) は severity だけを決め、category が実害クラスなら medium でも blocking のまま残る |
| G6 | 独立-2 | medium | no | self-inflicted | product | next-pr | 取り直しの回数と判定の記録先が無い（独立-1 の F5 と同じ） |
| G7 | 独立-2 | low | no | self-inflicted | product | fixed | 依頼に無い Round 上限の一括提示に事前回答を掛けた。外した。commit: b728a09e |
| G8 | 独立-2 | low | no | self-inflicted | product | fixed | 受け入れが design-gating に届かない。受け入れを外した。commit: b728a09e |
| G9 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | 「同ファイルのとおり」が指す先が違う。受け入れを外した。commit: b728a09e |
| G10 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | 「3 が優先する」が消えた。受け入れを外した。commit: b728a09e |
| G11 | 独立-2 | low | no | self-inflicted | doc-claim | next-pr | 「gate の Round 上限とは別に数える」が消えた |
| G12 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | 断片に受け入れだけの発話の扱いが無い。受け入れを外し、断片からも消した。commit: b728a09e |
| G13 | 独立-2 | advisory | no | self-inflicted | doc-claim | fixed | autonomy.md の止まる案が除外なしで食い違って見える。受け入れを外したので食い違いは無くなった。commit: b728a09e |
| G14 | 独立-2 | advisory | no | self-inflicted | test-power | accepted | 足した pin は root CLAUDE.md § テストのクラス E に当たる。依頼の 4 に従った |
| G15 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | GDD に独立レビューの agent 定義が無く、(3-f) が届くかは main の prompt の組み方による |
| H1 | 独立-3 | medium | no | self-inflicted | product | fixed | (3-f) は severity だけを決め、経路 P 型の指摘に実害クラスが付くと blocking のまま後続へ送れない。ユーザーの指示でこの PR で直し、category を `test-power` にした。commit: fd380e24 |
| H2 | 独立-3 | medium | no | self-inflicted | product | next-pr | 人に戻す条件が high だけで、取り直しの条件（high・blocking）と揃っていない |
| H3 | 独立-3 | low | no | self-inflicted | product | next-pr | 取り直しの範囲が (3-a) の定義語「対象」を使わず、「両方 0 の場合だけ」にも触れていない |
| H4 | 独立-3 | low | no | self-inflicted | doc-claim | next-pr | 断片と PR 本文が全量に戻る条件を 3 つに狭めて書いている |
| H5 | 独立-3 | low | no | self-inflicted | product | fixed | PR 本文が依頼の 3 の場面を design-gating と書いていた。独立レビューの Medium に直し、design-gating の Medium は直すしかないことを書いた。commit: なし（PR 本文） |
| H6 | 独立-3 | low | no | self-inflicted | product | next-pr | 取り直しを使ったかを数える記録が無い（独立-1 の F5 と同じ） |
| H7 | 独立-3 | advisory | no | self-inflicted | doc-claim | fixed | 「残すか外すかは別に決める」に行き先が無い。次の PR に入れた。commit: なし（PR 本文） |
| I1 | 独立-4 | medium | no | self-inflicted | product | fixed | 括弧書き「fail-open の向きと判定できないときは実害クラスを付けてよい」が経路 P 型にも当たると読める。「fail-open の向きには」にし、reviewer-common も「判定できないときを含む」にした。commit: e3d69c04 |
| I2 | 独立-4 | low | no | self-inflicted | doc-claim | next-pr | 経路 P 型と category の対応を 2 ファイルに書いていて、正本が 1 か所でない |
| I3 | 独立-4 | low | no | self-inflicted | product | next-pr | agent の「列挙なら Medium」と (3-f) の向きの判定が、列挙そのものの指摘で食い違う |
| I4 | 独立-4 | low | no | self-inflicted | doc-claim | next-pr | PR 本文の変更内容に、reviewer 2 本の category も (3-f) に従うことが書かれていない |
| I5 | 独立-4 | low | no | self-inflicted | doc-claim | next-pr | 変更断片に、reviewer 2 本の category も (3-f) に従うことが書かれていない |
| I6 | 独立-4 | advisory | no | inherited | product | accepted | PR 後の外部レビューの severity は Classify が決めるので、(3-f) が届かない（依頼の範囲の外） |
| J1 | 独立-5 | advisory | no | self-inflicted | bookkeeping | accepted | review-log の commit の件名に巡の種類が入り、git status から reviewer に届いた。以後の件名には書かない |
| K1 | 独立-6 | medium | no | self-inflicted | product | next-pr | (3-f) と reviewer-common.md § 常時 High のどちらが先かが書かれておらず、reviewer ごとに High と medium に割れうる |
| K2 | 独立-6 | medium | no | self-inflicted | product | next-pr | self-review-lanes.md と pr-review-followup の「是正して再実行」が (3-f) の取り直しの上限と食い違う。依頼 1 の「矛盾させない」から外れたまま（3 巡目の後のため限界に書く） |
| K3 | 独立-6 | medium | no | self-inflicted | product | next-pr | 昇格処理の順序 2 が先に評価され、(3-f) の例外が 3 の括弧の中にしか無い |
| K4 | 独立-6 | medium | no | self-inflicted | product | next-pr | 取り直しの回数と「前回の high がすべて Decision」の判定に使える記録と、確かめられないときの既定が無い |
| K5 | 独立-6 | medium | no | self-inflicted | product | next-pr | 経路 P 型の後続の test の要件を写す先が決まっていない |
| K6 | 独立-6 | low | no | self-inflicted | doc-claim | next-pr | (3-f) が category の値をリテラルで再掲していて、reviewer-common.md の再掲しない規定に当たる |
| K7 | 独立-6 | low | no | self-inflicted | product | accepted | 依頼の「差分だけを見る」に「前回の high・blocking がすべて Decision なら」の条件を足した。依頼から外れたまま（3 巡目の後のため限界に書く） |
| K8 | 独立-6 | low | no | self-inflicted | product | accepted | security reviewer の観点を design phase にだけ足し、Implementation phase には足していない。依頼から外れたまま（3 巡目の後のため限界に書く） |
| K9 | 独立-6 | low | no | self-inflicted | product | next-pr | rollback-patterns.md の 4 択の読み替え、autonomy.md の一覧、gdd-pr-review-followup に (3-f) の経路が無い |
| K10 | 独立-6 | low | no | self-inflicted | doc-claim | next-pr | 契約 3 の前置きが (3-f) を 2 回目以降の起動範囲として読ませる |
| K11 | 独立-6 | low | no | self-inflicted | doc-claim | accepted | 新しい発火条件の件数を測っていない。PR 本文の限界に「発火件数: 未測」と書く。commit: なし（PR 本文） |
| K12 | 独立-6 | advisory | no | self-inflicted | doc-claim | accepted | high の基準を常設の方針として届けたことが PR 本文に無い。PR 本文に足す。commit: なし（PR 本文） |
| K13 | 独立-6 | advisory | no | self-inflicted | product | accepted | doc guard の pin を残すか外すかは PR を待たずにユーザーに確かめられる |
| K14 | 独立-6 | advisory | no | self-inflicted | doc-claim | accepted | Skill RED-GREEN Evidence が抜粋に無い。PR 本文の末尾の節にあり、対応不要 |
