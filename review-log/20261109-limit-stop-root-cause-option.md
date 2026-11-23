---
lane: L1
pr: 641
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 6e5fab1ec67d359e3e1ae05bf021faa75ad3c4ae | 0 | 4 | 2 | 2026-11-09 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 15cf55d0c01e8678a5a4edb27a258126e95231f7 | 1 | 6 | 2 | 2026-11-09 |
| 独立-3 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 937492db4a01942b2481b981651aa1a4670bc3a0 | 0 | 6 | 3 | 2026-11-09 |
| 独立-4 | light-lane-independent-reviewer-xhigh, 差分（無効化後）, model: opus | 7b9b53dc95e6687e2f426c3daaeb9fc90830a907 | 1 | 5 | 5 | 2026-11-09 |
| 独立-5 | light-lane-independent-reviewer-xhigh, 差分（無効化後）, model: opus | 575bf1a2ec57cd0302e6f69c968521a9e04491e6 | 0 | 5 | 2 | 2026-11-09 |
| 方針メモ-1 | 再設計, Opus 設計レビュー ×2 (gdd-opus-advisor, model: opus) | d6054cb06610d945e5247f2cd03bdd9ecf37a066 | 0 | 0 | 0 | 2026-11-09 |
| 独立-6 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 88e5e529a2b974bc70905878819269df1b4766c9 | 0 | 4 | 1 | 2026-11-09 |
| 独立-7 | light-lane-independent-reviewer-xhigh, 差分, model: opus | 2811645a70e34a3e17278525452889fcf3d8172e | 0 | 2 | 0 | 2026-11-09 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| I1-1 | 独立-1 | medium | yes | self-inflicted | limit-option-route | fixed | 設計: 変える（新しい案に独自の進み方を足した決定をやめ、既存の分類に乗せる）。推奨が新しい案のとき、案名の無い返答が承認に流れて blocking が残ったまま進む。返答の分類に行を足し、案を名前で復唱して確かめる。commit: 3cbf3910 |
| I1-2 | 独立-1 | medium | yes | self-inflicted | limit-option-route | fixed | 設計: 変える（同上）。委任先が前提を変える案を人に戻さず採れる。依頼の読み方や前提を変える案を分類 1 にして、既存の人に戻す条件（planning_rework_required）に当て、その条件に案を名指しした。commit: 152ee8a2 |
| I1-3 | 独立-1 | medium | no | self-inflicted | limit-option-menu | accepted | 方式転換の固定の選択肢と「選択肢に加える」が矛盾する。委任先への「4 択の外は選ばず」ともぶつかる |
| I1-4 | 独立-1 | medium | no | self-inflicted | limit-option-route | fixed | 回答後の 2 分岐が排他でなく、修正指示の 4 分類とずれる。I1-1 の直しで独自の分岐が消えた。commit: 3cbf3910 |
| I1-5 | 独立-1 | low | no | self-inflicted | limit-option-menu | fixed | 時間超過の一括提示に別の 3 択が残る。依頼から外れたという指摘なので、案を足さないことを明記した。commit: 3cbf3910 |
| I1-6 | 独立-1 | low | no | self-inflicted | limit-option-menu | accepted | 「ほかの上限（修正の回数など）」が gdd-systematic-debugging の読み手に届かない |
| I1-7 | 独立-1 | low | no | self-inflicted | limit-option-menu | accepted | 推奨の優先と、ユーザーがすでに決めたことを覆さない基準の順序が書かれていない |
| I1-8 | 独立-1 | low | no | self-inflicted | limit-option-menu | accepted | 比べる問いが判断軸の 6 軸に居場所を持たない |
| I1-9 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | PR 本文の挙動の変化に、方式転換・ほかの上限・推奨の優先・選んだ後の進み方が無い。commit: なし（PR 本文） |
| I1-10 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 断片が方式転換とほかの上限に触れていない。commit: 3cbf3910 |
| I1-11 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | PR 本文の測定の説明が基準と到達の未測を省いている。commit: なし（PR 本文） |
| I1-12 | 独立-1 | low | no | self-inflicted | doc-claim | fixed | 目的の節に当たる件数が無い。commit: なし（PR 本文） |
| I1-13 | 独立-1 | low | no | self-inflicted | fragment-type | accepted | 断片の type が patch で、選択肢と経路を足す変更は minor の読みもある |
| I1-14 | 独立-1 | low | no | inherited | limit-option-route | accepted | design の Round 上限に回答の合流先が無い（元の 3 つでも同じ） |
| I1-15 | 独立-1 | advisory | no | self-inflicted | limit-option-menu | fixed | 戻す条件を読む時機に追跡先が無い。PR 本文の限界に条件と場所を書いた。commit: なし（PR 本文） |
| I2-1 | 独立-2 | high | yes | self-inflicted | limit-option-route | fixed | 設計: 変える（案の行き先を修正指示の分類に任せた決定をやめ、差し戻しと gate への再入の 2 本にする）。requirements の上限で案を選ぶと、承認も残った blocking の確認も無いまま design gate へ進む。commit: 9947b045 |
| I2-2 | 独立-2 | medium | yes | self-inflicted | limit-option-route | fixed | 設計: 変える（方式転換に案を足した決定をやめ、再設計の案で名指しする）。案名の無い返答の確認が上限 6 種のうち 4 種にしか効かない。案を足さないので、返答の分岐は requirements・design の一括提示だけになる。commit: 9947b045 |
| I2-3 | 独立-2 | medium | no | self-inflicted | limit-option-route | fixed | 4 択の行の語が一括提示にも当たり先に一致する。行に completion-check と書いた。commit: 9947b045 |
| I2-4 | 独立-2 | medium | no | self-inflicted | limit-option-route | fixed | 案を名指しした返答が Step 8 に届かない。名指しも Step 8 へ送る。commit: 9947b045 |
| I2-5 | 独立-2 | medium | no | self-inflicted | limit-option-route | fixed | 「分類 1」が返答を処理する側の番号と逆に読める。番号の参照をやめた。commit: 9947b045 |
| I2-6 | 独立-2 | medium | no | self-inflicted | doc-claim | fixed | 正本と指した節に規定が無い。Step 8 に書き、gdd-dev から Steps 8 を指す。commit: 9947b045 |
| I2-7 | 独立-2 | medium | no | self-inflicted | limit-option-menu | fixed | 断片の方式転換の記述が正本と合わない。案の数を増やさない形に直した。commit: 9947b045 |
| I2-8 | 独立-2 | low | no | self-inflicted | limit-option-menu | fixed | 時間超過を外す理由が成り立たない場合がある。理由を「レビューが成立していない」に直した。返ってきた blocking を持つ timeout の Round の扱いは今までどおりで、足していない。commit: 9947b045 |
| I2-9 | 独立-2 | low | no | self-inflicted | limit-option-route | fixed | 依頼に無い確認を足していて、案内の「OK で承認」と合わない。確認をやめ、推奨を選んだものとして扱う。commit: 9947b045 |
| I2-10 | 独立-2 | low | no | self-inflicted | doc-claim | fixed | PR 本文に依頼が決めた語と害の 4 種が無い。commit: なし（PR 本文） |
| I2-11 | 独立-2 | low | no | self-inflicted | budget | fixed | gdd-dev の追加で token の予算を超えるかが未確認。実際に 13 超えたので 2 行を詰めた。commit: 9947b045 |
| I2-12 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 返答の分岐は RED-GREEN の対象に入っていない。PR 本文の限界に未測と書いた |
| I2-13 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | PR 本文の 109 本中 56 本の根拠が review-log に無い。根拠はリポジトリ外の測定記録にある |
| I2-14 | 独立-2 | advisory | no | inherited | limit-option-route | accepted | design の Round 上限の一括提示は遷移表と design-gating に行が無い |
| I2-15 | 独立-2 | advisory | no | inherited | limit-option-route | accepted | 修正指示の分類が 3 分類と 4 分類で食い違ったまま |
| I3-1 | 独立-3 | medium | yes | self-inflicted | limit-option-route | fixed | 設計: 変える（承認の経路を人の返答だけに分けた決定をやめ、委任で採った案も Steps 8 に合流させる）。委任で原因を変える案を採ると STEP 2 に通り、残った blocking が消える。commit: f7c44495 |
| I3-2 | 独立-3 | medium | yes | self-inflicted | limit-option-route | fixed | 設計: 変える（requirements の組だけで design も受けた決定をやめる）。design の一括提示の state の組が無い。止まる行を表に足し、4 案の行き先を Steps 8 に書いた。commit: f7c44495 |
| I3-3 | 独立-3 | medium | no | self-inflicted | limit-option-route | fixed | AC の変更が差し戻しの条件に名前が無く、再入に入りうる。条件に AC を足した。commit: f7c44495 |
| I3-4 | 独立-3 | medium | yes | self-inflicted | limit-option-route | fixed | 設計: 変える（案ごとに返答を分けた決定をやめ、一括提示への返答をすべて Steps 8 に送る）。推奨が修正・差し戻しのときの「OK」が承認に流れる。commit: f7c44495 |
| I3-5 | 独立-3 | medium | no | self-inflicted | limit-option-menu | fixed | 依頼の「上限の停止で観点が入る」を、ほかの上限の文を消して狭めた。文を戻した。commit: f7c44495 |
| I3-6 | 独立-3 | medium | no | self-inflicted | limit-option-menu | fixed | 依頼の「文は再生で測ったまま入れる」に反して契約の 1 の文を変えた。測った文に戻し、足した文を分けて notes に書いた。commit: f7c44495 |
| I3-7 | 独立-3 | low | no | self-inflicted | limit-option-route | fixed | 新しい行の語が「再入」で lint の entry の読みと食い違う。行の語を「開始」に直した。commit: f7c44495 |
| I3-8 | 独立-3 | low | no | self-inflicted | doc-claim | fixed | 見出しの一括提示の ID に定義が無い。契約の 2 の語にそろえた。commit: f7c44495 |
| I3-9 | 独立-3 | low | no | self-inflicted | doc-claim | fixed | 文と行で Human Check の値が食い違う。行を — にした。commit: f7c44495 |
| I3-10 | 独立-3 | low | no | self-inflicted | doc-claim | accepted | § 承認後の即時継続 に一括提示の例外が無い。実際の分類は gdd-dev の STEP 1 が先に当たるので、害は読み違えに限られる |
| I3-11 | 独立-3 | low | no | inherited | limit-option-menu | accepted | 方式転換の 3 択で推奨の再設計に OK と答えると STEP 2 に進む。案を足さないので、この PR で変わらない元からの動き |
| I3-12 | 独立-3 | advisory | no | self-inflicted | doc-claim | accepted | PR 本文の 109 本中 56 本の数え方が notes に無い |
| I3-13 | 独立-3 | advisory | no | self-inflicted | doc-claim | accepted | 断片の Summary に時間超過の一括提示の扱いが無い |
| I4-1 | 独立-4 | high | yes | self-inflicted | limit-option-route | fixed | 設計: 変える（一括提示への返答を全部 Steps 8 に送った決定をやめ、原因を変える案の名指しと推奨への案名の無い承認だけにする）。requirements の accept as known risk が承認の記録に届かない。accept は STEP 2 に戻した。commit: abda432d |
| I4-2 | 独立-4 | medium | yes | self-inflicted | limit-option-route | fixed | 設計: 変える（一括提示への返答を全部 Steps 8 に送った決定をやめ、原因を変える案の名指しと推奨への案名の無い承認だけにする）。AC を変える修正指示が 3 分類を通らない。修正は 3 分類で進める。commit: abda432d |
| I4-3 | 独立-4 | medium | yes | self-inflicted | limit-option-route | fixed | 設計: 変える（一括提示への返答を全部 Steps 8 に送った決定をやめ、原因を変える案の名指しと推奨への案名の無い承認だけにする）。質問や条件つきの返答が推奨の案を選んだものと読める。条件なし・留保なしの承認だけにした。commit: abda432d |
| I4-4 | 独立-4 | medium | yes | self-inflicted | limit-option-route | fixed | 設計: 変える（一括提示への返答を全部 Steps 8 に送った決定をやめ、原因を変える案の名指しと推奨への案名の無い承認だけにする）。時間超過の一括提示への返答に行き先が無い。新しい経路から外したので、差し戻しの経路は元に戻る。commit: abda432d |
| I4-5 | 独立-4 | medium | yes | self-inflicted | limit-option-route | fixed | 設計: 変えない（route を残す規定ではなく、止まる行の値の抜け）。一括提示の state が resume の検証で不整合になる。止まる遷移で Route In Progress を none にした。commit: abda432d |
| I4-6 | 独立-4 | medium | no | self-inflicted | limit-option-route | accepted | design の一括提示の行を書く手順が gate runner につながっていない。design-gating に上限で止まる手順はもとから無い。PR 本文の限界に書いた |
| I4-7 | 独立-4 | low | no | self-inflicted | doc-claim | fixed | human-check-template の一括提示に requirements・design の限定が無い。commit: abda432d |
| I4-8 | 独立-4 | low | no | self-inflicted | doc-claim | accepted | OK を承認と読む別の規定に一括提示の例外が無い。分類は gdd-dev の STEP 1 が先に当たる |
| I4-9 | 独立-4 | low | no | self-inflicted | doc-claim | fixed | 断片が差分の挙動と合わない。commit: abda432d |
| I4-10 | 独立-4 | advisory | no | self-inflicted | doc-claim | accepted | state-machine の開始の行の値がほかの開始の行と違う |
| I5-1 | 独立-5 | medium | yes | self-inflicted | limit-option-route | fixed | 再設計: requirements の一括提示の修正が 3 分類の実装方針変更に入り、Human Check が evidence: none の approved になる。Approved Direction も書かれず、残った blocking も再度見られない。入口を state の 1 つの表にして閉じた。commit: d6054cb0 |
| I5-2 | 独立-5 | medium | no | self-inflicted | limit-option-route | fixed | 再設計: accept の返答が Steps 8 に届かず、design の accept の行き先に入口が無い。accepted-as-known-risk が書かれない。入口を state の 1 つの表にして閉じた。commit: d6054cb0 |
| I5-3 | 独立-5 | medium | yes | self-inflicted | limit-option-route | fixed | 再設計: 案名の無い承認の分岐が読む推奨がどこにも記録されない。compaction の後に判定できず STEP 2 に進む。入口を state の 1 つの表にして閉じた。commit: d6054cb0 |
| I5-4 | 独立-5 | medium | no | inherited | limit-option-route | fixed | 再設計: 時間超過の一括提示への OK が推奨によらず STEP 2 に進む。入口を state の 1 つの表にして閉じた。commit: d6054cb0 |
| I5-5 | 独立-5 | low | no | self-inflicted | doc-claim | fixed | 再設計: Steps 8 の案名無しの規則の範囲が gdd-dev と断片より広い。入口を state の 1 つの表にして閉じた。commit: d6054cb0 |
| I5-6 | 独立-5 | low | no | self-inflicted | limit-option-route | fixed | 再設計: 条件つきの名指しの行き先が無い。入口を state の 1 つの表にして閉じた。commit: d6054cb0 |
| I5-7 | 独立-5 | low | no | self-inflicted | doc-claim | fixed | 再設計: design の修正の行き先が入口で分かれ、PR 本文の今までどおりと合わない。入口を state の 1 つの表にして閉じた。commit: d6054cb0 |
| I5-8 | 独立-5 | low | no | self-inflicted | doc-claim | fixed | 再設計: Route In Progress のクリアの表が追随していない。入口を state の 1 つの表にして閉じた。commit: d6054cb0 |
| I5-9 | 独立-5 | low | no | self-inflicted | limit-option-menu | fixed | 再設計: 測った文の直後の未測の文が、方式転換で止まる上限について案を加える読みを打ち消す。依頼の「文は再生で測ったまま入れる」から効果の面で外れる。入口を state の 1 つの表にして閉じた。commit: d6054cb0 |
| I5-10 | 独立-5 | medium | no | self-inflicted | limit-option-route | fixed | 再設計: 案名の無い承認の読み替えが依頼の範囲より広い。元の修正・差し戻しへの OK の意味と委任の経路を変えている。completion の 4 択は復唱で確かめていて扱いが逆。入口を state の 1 つの表にして閉じた。commit: d6054cb0 |
| I5-11 | 独立-5 | advisory | no | self-inflicted | doc-claim | fixed | 再設計: 開始の行の status がほかの開始の行と違う。入口を state の 1 つの表にして閉じた。commit: d6054cb0 |
| I5-12 | 独立-5 | advisory | no | inherited | doc-claim | accepted | 修正指示の 3 分類と 4 分類の呼び名が違う |
| M1-1 | 方針メモ-1 | advisory | no | self-inflicted | limit-option-route | accepted | 再設計: 2 本とも、返答を承認と同じ入口に載せたまま形で例外を分けた決定が原因で、種類ごと消せると回答（止めるべきか no）。入口を state、出口を 3 本にし、案名の無い承認は復唱にした。分かれた点は、方式転換の文を runner に残す側と、足した開始の行を消す側を採った |
| I6-1 | 独立-6 | medium | yes | self-inflicted | limit-option-route | fixed | 設計: 変えない（表の外の、人に戻す条件の抜け）。時間超過で委任先がレビュー無しで承認を採ると、誰も見ないまま承認に進む。人に戻す条件に足した。commit: 403dce9b |
| I6-2 | 独立-6 | medium | no | self-inflicted | limit-option-route | accepted | 表の入口の state が Express の一括提示に届かない。PR 本文の限界に書いた |
| I6-3 | 独立-6 | medium | no | self-inflicted | limit-option-route | accepted | 一括提示の案内がまだ OK で承認のまま。案内どおりの OK は復唱で受ける |
| I6-4 | 独立-6 | medium | no | self-inflicted | limit-option-route | accepted | 確認待ち: 依頼に無かった 2 つの変更（OK の復唱、修正の回し直し）を本人に確かめる。PR 本文の限界に問いを書いた |
| I6-5 | 独立-6 | low | no | self-inflicted | doc-claim | accepted | 方式転換の除外が契約の 1 から消え、文の字義と案の数の規定がずれる。template と runner から届く |
| I6-6 | 独立-6 | low | no | self-inflicted | doc-claim | accepted | 節の冒頭の説明と STEP 2 の見出しの語が accept の行と合わない。表の行が明示している |
| I6-7 | 独立-6 | low | no | self-inflicted | doc-claim | fixed | 断片の Affected Files に rollback-patterns が無い。commit: 403dce9b |
| I6-8 | 独立-6 | low | no | inherited | limit-option-route | accepted | remediation-loop-limit の方式転換への案名の無い OK が STEP 2 に進む。元からの動き |
| I7-1 | 独立-7 | medium | no | self-inflicted | limit-option-route | fixed | 依頼に無い変更（委任で時間超過に当たると止まる）が PR 本文の問いから漏れている。commit: なし（PR 本文） |
| I7-2 | 独立-7 | medium | no | inherited | limit-option-route | accepted | 委任の再レビューに回数の上限が無い。誤った承認には進まず、時間と費用が増える。元からの動き |
| I7-3 | 独立-7 | low | no | self-inflicted | doc-claim | accepted | 表の accept の行が委任では採れないことを示していない。人に戻す条件が先に当たる |
| I7-4 | 独立-7 | low | no | self-inflicted | doc-claim | fixed | 断片に時間超過と新しい止まる条件が無い。断片だけを直した。commit: 8e7359bd |
| I7-5 | 独立-7 | low | no | inherited | doc-claim | accepted | 時間超過で書く事前回答の適用の 1 欄目が決まっていない。gate の判定は変わらない |
| I7-6 | 独立-7 | low | no | self-inflicted | doc-claim | fixed | 上限以外の停止は変わらないが差分と合わない。commit: なし（PR 本文） |
| I7-7 | 独立-7 | advisory | no | inherited | doc-claim | accepted | 状態遷移の行と Steps 7 に時間超過が無い |
