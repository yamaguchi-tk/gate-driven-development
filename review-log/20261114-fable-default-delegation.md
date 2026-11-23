---
lane: L1+
pr: 676
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 1038bfb01988aa7db35c72791564e699305a91d6 | 0 | 4 | 1 | 2026-11-14 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: fable | 9271089915cf649fba483d6afc4b252cf280999e | 1 | 3 | 1 | 2026-11-14 |
| 方針メモ-1 | Opus 設計レビュー ×2 (gdd-opus-advisor, model: opus) | 9271089915cf649fba483d6afc4b252cf280999e | 0 | 0 | 0 | 2026-11-14 |
| 独立-3 | light-lane-independent-reviewer-xhigh, 差分, model: fable | 2d56ffabab0d09f1edd23c5e83bb0c740b9ceb47 | 1 | 3 | 2 | 2026-11-14 |
| 独立-4 | light-lane-independent-reviewer-xhigh, 差分（無効化後）, model: fable | 732dce7df56ae58d858f27afa0ae16dc8feb98a6 | 0 | 5 | 4 | 2026-11-14 |
| 独立-5 | light-lane-independent-reviewer-xhigh, 差分（無効化後）, model: fable | 87e2f21760f24cfb008112738063c3d54f760349 | 0 | 4 | 2 | 2026-11-14 |
| 方針メモ-2 | 再設計, Opus 設計レビュー ×2 (gdd-opus-advisor, model: opus) | 87e2f21760f24cfb008112738063c3d54f760349 | 0 | 0 | 0 | 2026-11-14 |
| 独立-6 | light-lane-independent-reviewer-xhigh, 差分, model: fable | 0141fd820ecca61080b3deff5dff34e49c5076dc | 0 | 3 | 0 | 2026-11-14 |
| 独立-7 | light-lane-independent-reviewer-xhigh, 差分, model: fable | df09e94356c08d844b6c95a0611e93bcce5e948e | 0 | 0 | 0 | 2026-11-14 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| I1-1 | 独立-1 | medium | yes | self-inflicted | delegation-default | fixed | 設計: 変える（既定を毎回の確認の OK に当てていた）。既定は steering の最初の human check だけに出し、後の確認の OK は今の値を保つ。commit: 92710899 |
| I1-2 | 独立-1 | medium | no | self-inflicted | delegation-stop-conditions | fixed | Approved Direction の正本テンプレート・許可表・段階実装案・evals に広い人間に戻す条件が残っていた。I1-4 の依頼の原文に合わせる修正として同じ原則にそろえた。commit: 92710899 |
| I1-3 | 独立-1 | medium | no | self-inflicted | delegation-stop-conditions | fixed | 委任先が依頼を広げる AC を足すと、completion-reviewer の Request Drift High で後から人に戻る。2026-11-15 にユーザーが D を選んだ（委任先は依頼の範囲の中だけ決め、広げる案は範囲を広げる提案として残す）。設計: 変える（委任先が決める範囲を依頼の範囲の中に限る）。commit: 0c35eab8 |
| I1-4 | 独立-1 | medium | no | self-inflicted | delegation-stop-conditions | fixed | 依頼より多い人に戻す条件が残っていた。各項目を、要件を満たせない見込み・要件が決まらない／判定できない・許可の境界の 3 つに分けて書き、要件を満たせない見込みを一覧の項目に足した。commit: 92710899 |
| I1-5 | 独立-1 | low | no | self-inflicted | delegation-stop-conditions | fixed | README の「要件を満たせないときだけ」が言い過ぎ。判定できないとき・許可の境界を足した。commit: 92710899 |
| I1-6 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | Fable の相談 1 本 約 $3.6 の測定記録が repo に無い |
| I1-7 | 独立-1 | low | no | inherited | delegation-stop-conditions | accepted | human-check-template.md:29・requirements-gating-steps.md:106 の要約と post-completion-pr-flow.md:209 の 4 択の特則が新しい一般則と食い違う |
| I1-8 | 独立-1 | low | no | self-inflicted | delegation-stop-conditions | fixed | compact の人間に戻す条件と § 事前回答 3 の一覧に「満たせない見込み」が無い。足した。commit: 92710899 |
| I1-9 | 独立-1 | low | no | inherited | bookkeeping | accepted | 未リリースの断片 20261015・20261113 の既定・並んでいない案の記述が、この断片と食い違う（amends: で直せる） |
| I1-10 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 並んでいない案で決める変更が PR 本文の挙動の変化に無い。commit: なし（PR 本文） |
| I1-11 | 独立-1 | advisory | no | self-inflicted | security-boundary | accepted | 新しい信頼境界を作る追加では人に戻らない |
| I1-12 | 独立-1 | advisory | no | self-inflicted | product | accepted | 読む時期と戻す条件が PR 本文に無い（PR 本文に足す） |
| I1-13 | 独立-1 | advisory | no | self-inflicted | bookkeeping | accepted | 既定の stop 条件の変更を breaking にするか |
| I1-14 | 独立-1 | advisory | no | self-inflicted | doc-claim | accepted | 他の環境で model: fable が受け付けられるかが未検証（限界に書く） |
| I2-1 | 独立-2 | high | yes | self-inflicted | delegation-default | fixed | 列挙: 設計: 変える（人に止める以外のときだけ選択を記録していた）。方針メモ-1 の 2 本の推奨どおり、人に止めるを事前回答の行の委任先の値にし、承認のたびに行を書き、最後の行を今の値にした。hook は変えず、テストで固定。commit: 2d56ffab |
| I2-2 | 独立-2 | medium | no | self-inflicted | delegation-default | fixed | 最初の human check の境目と今の値が定義されていない。I2-1 と同じ設計の変更で、行と Approved Direction の有無で定義した。commit: 2d56ffab |
| I2-3 | 独立-2 | medium | no | self-inflicted | delegation-default | accepted | compact の判断の委任の行が 499 行目の求める中身を満たさず、後の human check の形も無い |
| I2-4 | 独立-2 | medium | no | self-inflicted | delegation-stop-conditions | accepted | 依頼の「要件が満たせないときだけ」を 3 種類（満たせない見込み・判定できない・許可の境界）で読む。2026-11-15 にユーザーが推奨のままでよいと答えた |
| I2-5 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 499 行目と autonomy.md の括弧が 3 種類のうち 1 つしか言っていない |
| I2-6 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 断片の種類の名前と分け方が § 事前回答 3 と違う |
| I2-7 | 独立-2 | low | no | inherited | doc-claim | accepted | 記入例の人間に戻す主な条件と許可表が古い 3 系統のまま |
| I2-8 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 「足す・技術スタックを変えるだけなら戻さない」が委任の値を問わない書き方 |
| I2-9 | 独立-2 | low | no | inherited | doc-claim | accepted | E2E Discovery Loop 側と evals id 55 が古い 3 条件のまま |
| I2-10 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 短い形から「意味を変える」が落ちた |
| I2-11 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | 既定を戻す条件に値が無い |
| P1-1 | 方針メモ-1 | advisory | no | self-inflicted | delegation-default | fixed | 2 本とも、取り消しの別の行ではなく事前回答の行の 5 つ目の値を推奨。未選択の定義は Opus-1（行も Approved Direction も無いとき）を採り、後続 Stage へ写すのは最後の行とした。commit: 2d56ffab |
| I3-1 | 独立-3 | high | yes | self-inflicted | delegation-default | fixed | 設計: 変える（最後の事前回答の行がすべての欄を決めていた）。最後の行が決めるのは委任先だけにし、人に戻す条件は対象に含む全行の和で読む。後続 Stage へは全行を順に写す。commit: 732dce7d |
| I3-2 | 独立-3 | medium | yes | self-inflicted | delegation-default | fixed | 設計: 変える（I3-1 と同じ決定）。人に止めるの行の対象を、それまでのすべての事前回答の行の対象の和にした。commit: 732dce7d |
| I3-3 | 独立-3 | medium | no | self-inflicted | delegation-default | fixed | 後の human check の OK だけの行を照合で読めず、1 回人に戻ると委任が効かなくなる（依頼の原文から外れる）。返事が値を挙げていなければ表示した行の値を読むとした。commit: 732dce7d |
| I3-4 | 独立-3 | medium | no | self-inflicted | delegation-default | accepted | 修正指示での再提示が、前の返事で選んだ値を未選択に戻す |
| I3-5 | 独立-3 | low | no | self-inflicted | delegation-default | accepted | 最後の行が人に止めるのとき、後続 Stage に待たずに着手するかが決まらない |
| I3-6 | 独立-3 | low | no | self-inflicted | delegation-default | accepted | STEP 2 の行を書く文が、委任先の承認のときにも読める |
| I3-7 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | hook のコメントが template の集合と同じだと書いたまま |
| I3-8 | 独立-3 | low | no | self-inflicted | delegation-stop-conditions | re-reported | I2-4 の再掲（依頼の「要件が満たせないときだけ」より人に戻す条件が広い。確認待ち） |
| I3-9 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | この既定より前に承認した steering は人に止めるのままになることが PR 本文と断片に無い |
| I3-10 | 独立-3 | low | no | inherited | doc-claim | accepted | compact 版の判断の委任の行に後の human check の表示の形が無い |
| I4-1 | 独立-4 | medium | yes | self-inflicted | delegation-default | fixed | 設計: 変えない（I3-1 の欄ごとの読み分けに自走上限が抜けていた）。自走上限も最後の行で読むとした。commit: 87e2f217 |
| I4-2 | 独立-4 | medium | yes | self-inflicted | delegation-default | fixed | 設計: 変えない（同上）。原文を確かめられない行の条件も和に数え、照合は最後の行だけにした。着手の合図も最後の行で確かめる。commit: 87e2f217 |
| I4-3 | 独立-4 | medium | yes | self-inflicted | delegation-default | fixed | 設計: 変えない（同上）。人に止めるの行の対象を、書いた経路によらず全行の対象の和とし、§ 事前回答 1 に 1 回だけ書いた。commit: 87e2f217 |
| I4-4 | 独立-4 | medium | no | self-inflicted | delegation-default | accepted | 列挙: 「消す・緩めるのは本人が明示したときだけ」に記録の形と照合が無い |
| I4-5 | 独立-4 | medium | yes | inherited | delegation-default | fixed | 原文が自走上限に触れる行の後に 5 の引き上げ・引き下げ行があれば state.md の値を読むとした。commit: 87e2f217 |
| I4-6 | 独立-4 | low | no | self-inflicted | doc-claim | fixed | 断片に和で読むこと・全行を写すことが無い。Summary に足した。commit: 87e2f217 |
| I4-7 | 独立-4 | low | no | self-inflicted | doc-claim | fixed | PR 本文の挙動の変化に全行を写すことと人に止めるの対象の和が無い。commit: なし（PR 本文） |
| I4-8 | 独立-4 | low | no | self-inflicted | delegation-stop-conditions | re-reported | I2-4 の再掲（確認待ち） |
| I5-1 | 独立-5 | medium | yes | self-inflicted | delegation-default | accepted | 表示した human check で人に止めるを選んだ行の対象が 499・715 と 714 で食い違う（再設計で扱う） |
| I5-2 | 独立-5 | medium | yes | inherited | delegation-default | accepted | 原文が自走上限に触れる行は、元の steering での引き下げが後続 Stage に写らない（再設計で扱う） |
| I5-3 | 独立-5 | medium | no | self-inflicted | delegation-default | accepted | 全行を写した後の「同じ値」がどの行を指すか書いていない |
| I5-4 | 独立-5 | medium | no | self-inflicted | delegation-default | accepted | 列挙: 人に止めるの和が 3 本目以降の Stage に届かない |
| I5-5 | 独立-5 | low | no | self-inflicted | doc-claim | accepted | 消す・緩めるの記録と読み方が無い |
| I5-6 | 独立-5 | low | no | self-inflicted | doc-claim | accepted | 後続 Stage の着手を指す別の文書が元の事前回答行のまま |
| I5-7 | 独立-5 | low | no | inherited | product | accepted | Stop hook は対象を見ずにファイルの最後の行で押し返す |
| I5-8 | 独立-5 | low | no | self-inflicted | doc-claim | accepted | 差分の挙動のうち PR 本文と断片に無いもの |
| I5-9 | 独立-5 | low | no | self-inflicted | delegation-stop-conditions | re-reported | I2-4 の再掲（確認待ち） |
| I5-10 | 独立-5 | low | no | self-inflicted | bookkeeping | accepted | 対象欄の形が和の行を書けない |
| P2-1 | 方針メモ-2 | advisory | no | self-inflicted | delegation-stop-conditions | fixed | 再設計: 前提: ずれる（判断の委任を毎回の確認に出し、選択を事前回答の行に積んで欄ごとに読み分ける前提）。2 本が割れ、作り直す側（Approved Direction の `判断の委任` の欄に 1 つの値を持ち、Stop hook も欄を読む）を採った。設計: 変える（委任の値を行の積み上げから 1 つの欄へ）。commit: 0141fd82 |
| I6-1 | 独立-6 | medium | no | self-inflicted | delegation-entry | fixed | 依頼の原文から外れた指摘として直す。既定の fable は行を書かないのに、human check の入口 5 か所が事前回答の行だけを条件にしていた。設計: 変えない（§ 事前回答 2 が欄を読む規定はあり、入口の条件の写しだけが古い）。commit: df09e943 |
| I6-2 | 独立-6 | medium | no | self-inflicted | hook-field-read | accepted | state.md が読めないと行に戻り、人に止めるの欄があっても 1 回押し返す |
| I6-3 | 独立-6 | medium | no | self-inflicted | hook-field-read | accepted | 列挙: 正本の形でない欄（字下げ・全角コロンなど）は欄なしと読み、行に戻る |
| I6-4 | 独立-6 | low | no | self-inflicted | doc-claim | accepted | ひな形の値の後ろの注記が、値として写されると押し返さない側に倒れる |
| I6-5 | 独立-6 | low | no | self-inflicted | doc-claim | accepted | § 事前回答の導入文と 2 が、1 から消した記録の形を指したまま |
| I6-6 | 独立-6 | low | no | self-inflicted | doc-claim | accepted | 取り消しの『前の委任の行は効かなくなる』と 4 の後続 Stage の着手が合わない |
| I6-7 | 独立-6 | low | no | self-inflicted | delegation-entry | accepted | 欄を書く・保つ場面（事前回答で承認・後の承認・Stage を挙げた委任）の規定の抜け |
| I6-8 | 独立-6 | low | no | self-inflicted | hook-field-read | accepted | hook は欄が承認の後に書かれたかを確かめない |
| I6-9 | 独立-6 | low | no | self-inflicted | test-power | accepted | FIELD_DELEGATES とひな形の値域を突き合わせるテストが無い |
| I6-10 | 独立-6 | low | no | self-inflicted | doc-claim | accepted | hooks.json・テストの docstring・compact 版・post-merge-qa が行だけの説明のまま |
| I6-11 | 独立-6 | low | no | self-inflicted | delegation-stop-conditions | re-reported | I2-4 の再掲（確認待ち） |
| I6-12 | 独立-6 | low | no | self-inflicted | bookkeeping | accepted | 欄による押し返しの発火件数が PR 本文に無い |
| I6-13 | 独立-6 | advisory | no | self-inflicted | doc-claim | accepted | PR 本文に無い外から見える挙動（判断の委任の変更の行、読めないときの fallback、理由文） |
| I7-1 | 独立-7 | low | no | inherited | doc-claim | accepted | gdd-dev.md の入口だけ「欄があれば」で、ほかの 4 文の「欄が委任の値」と揃っていない |
| I7-2 | 独立-7 | low | no | self-inflicted | hook-field-read | accepted | 「委任の値」の受理集合が入口・正本・hook で揃っていない（欄が 2 つ・表示ラベルの値） |
| I7-3 | 独立-7 | low | no | self-inflicted | bookkeeping | accepted | 変更断片の Affected Files に rollback-patterns・subagent-dispatch・gdd-pr-review-followup が無い |
| I7-4 | 独立-7 | low | no | inherited | doc-claim | accepted | 「後続 Stage の steering には欄の値を写す」は事前回答で後続PRも実施許可の Stage だけ |
| I7-5 | 独立-7 | low | no | self-inflicted | delegation-stop-conditions | re-reported | I2-4 の再掲（確認待ち） |
| I7-6 | 独立-7 | low | no | self-inflicted | bookkeeping | fixed | 新しい発火条件の件数か未測の理由が PR 本文に無い。commit: なし（PR 本文） |
| I7-7 | 独立-7 | advisory | no | inherited | product | accepted | 欄は原文の照合なしに信頼され、書き込みを見る hook が無い |
| I7-8 | 独立-7 | advisory | no | inherited | product | accepted | 進行中の steering（欄が無いもの）は既定が変わらない |
