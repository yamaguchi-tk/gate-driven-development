---
lane: L1
pr: 444
follow_up_of: 437
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 829ae735 | 0 | 2 | 0 | 2026-10-12 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: opus | dd27ce6f | 0 | 3 | 0 | 2026-10-12 |
| 独立-3 | light-lane-independent-reviewer-xhigh, 差分, model: opus | c38e14c3 | 1 | 1 | 1 | 2026-10-13 |
| 独立-4 | light-lane-independent-reviewer-xhigh, 差分（無効化後）, model: opus | b4393305 | 1 | 0 | 1 | 2026-10-13 |
| 独立-5 | light-lane-independent-reviewer-xhigh, 差分（無効化後）, model: opus | 6f7d7f6c | 1 | 0 | 1 | 2026-10-13 |
| 独立-6 | light-lane-independent-reviewer, 全差分（無効化後）, model: opus | 1839a7fe | 1 | 2 | 1 | 2026-10-13 |
| 独立-7 | light-lane-independent-reviewer, 全差分（無効化後）, model: opus | 385eddcb | 0 | 1 | 0 | 2026-10-13 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| H1-1 | 独立-1 | medium | no | self-inflicted | request-drift | fixed | 依頼の行は「completion の超過は Round を消費する」を前提にしていたが、差分は確かめずに「Round を進めず blocked で止める」にした。ユーザーに確かめ、Fable の推奨を見て A（blocked）を選んだ発言を .request.md に足した。commit: dd27ce6f |
| H1-2 | 独立-1 | medium | no | self-inflicted | wiring | fixed | completion-check の Step 13 が § Reviewer Input and Time Budget を指さず、gate runner の中では新しい出口に届かない。Step 13 から指した。commit: dd27ce6f |
| H1-3 | 独立-1 | low | no | self-inflicted | wiring | fixed | 時間超過で止まったのに main が「外部前提不足」と表示する。State Update Contract と Post-Return Routing に行を足した。commit: dd27ce6f |
| H1-4 | 独立-1 | low | no | self-inflicted | product | fixed | completion の再実行で入力の狭め方が決まっていない。「completion は入力を変えない」と書いた。commit: dd27ce6f |
| H1-5 | 独立-1 | low | no | self-inflicted | doc-claim | accepted | 「その回は消費済みとする」が Round を進めない 3 gate にもかかる。PR 本文の限界に書いた |
| H1-A1 | 独立-1 | advisory | no | self-inflicted | doc-claim | fixed | 断片が書く出口の条件が、実際に入る条件と違う。断片を直した。commit: dd27ce6f |
| H1-A2 | 独立-1 | advisory | no | self-inflicted | product | accepted | completion の blocked が性質の違う停止をまとめ、時間超過だけを数えられない。PR 本文の限界に書いた |
| H1-A3 | 独立-1 | advisory | no | self-inflicted | bookkeeping | fixed | Skill RED-GREEN Evidence の記録を確かめられない。断片と PR 本文に書いた。commit: dd27ce6f |
| H2-1 | 独立-2 | medium | no | self-inflicted | request-drift | fixed | A を選んだユーザーの発言が依頼の原文に無い。ユーザーに確かめ、選んだラベル（A＋F2・F3 も直す）を .request.md に足した。commit: c38e14c3 |
| H2-2 | 独立-2 | medium | no | self-inflicted | wiring | fixed | レビュー不成立と外部前提不足の見分けが自由文頼みで、main が gate runner を止めた経路も覆われない。`result: review_unavailable` を登録し、:73 に main の停止理由を書いた（ユーザーの指示で直した）。commit: c38e14c3 |
| H2-3 | 独立-2 | medium | no | self-inflicted | product | fixed | `Completion Rounds` に数えない経路を挙げる別の箇所が追随していない。Checklist E に「+1 は差し戻しのときだけ」と書き、3 か所をそろえた（ユーザーの指示で直した）。commit: c38e14c3 |
| H2-4 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | `Next Action=gdd-completion-check` の用途・`Blocked Since` の定義・SessionStart の警告文が「外部前提不足」のまま。PR 本文の限界に書いた |
| H2-5 | 独立-2 | low | no | self-inflicted | doc-claim | re-reported | 「その回は消費済みとする」が 3 gate にもかかる（H1-5 と同じ） |
| H2-6 | 独立-2 | low | no | self-inflicted | bookkeeping | accepted | Step 13 が指す時間上限の記録先（reviews.md の Round）が completion に無い。PR 本文の限界に書いた |
| H2-7 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | 断片の User Action Required が「なし」のままで、type の見直しもしていない。PR 本文の限界に書いた |
| H2-8 | 独立-2 | low | no | self-inflicted | doc-claim | accepted | PR 本文の「計れないことがある」が規定より弱い。PR 本文の限界に書いた |
| H2-A1 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | 再実行で completion の入力を変えない理由と、それが gate runner の再実行にかかるかが書かれていない |
| H3-1 | 独立-3 | high | yes | self-inflicted | fail-open | fixed | 停止の後の再実行で Baseline があると差分スコープになり、Step 13 が見ていないコードへの指摘が advisory に落ちて done に届く。`Completion Rounds` が 0 なら全量を再検証するとした。commit: b4393305 |
| H3-2 | 独立-3 | medium | no | self-inflicted | product | accepted | 手順 5 の書き換えで、`diff_base_mismatch` のときの `<gdd-stop reason="blocked">` の指示が文の上で消えた。PR 本文の限界に書いた |
| H3-3 | 独立-3 | low | no | self-inflicted | product | accepted | 「+1 は Next Action=gdd-systematic-debugging のときだけ」と手順 2・field 定義の「blocker を出して差し戻すとき」が別の条件になった。PR 本文の限界に書いた |
| H3-4 | 独立-3 | low | no | self-inflicted | doc-claim | re-reported | `gdd-completion-check` の値の定義と Blocked Since の警告が外部前提不足だけを前提にしている（H2-4 と同じ） |
| H3-A1 | 独立-3 | advisory | no | self-inflicted | doc-claim | accepted | 手順 5 が return の `result:` で停止理由を分け、:35 の「return text 不使用」と食い違う |
| H3-A2 | 独立-3 | advisory | no | self-inflicted | doc-claim | accepted | main が gate runner を止めたときの再実行の単位と、途中の書き込みの扱いが決まっていない |
| H3-A3 | 独立-3 | advisory | no | self-inflicted | bookkeeping | fixed | テンプレート外の記述あり（PR 本文の抜粋に決め方の経緯）。次の巡の抜粋から除いた。commit: なし（PR 本文） |
| H4-1 | 独立-4 | high | yes | self-inflicted | fail-open | accepted | Step 13 より前（Part A）で差し戻すと Rounds が 1 になり Baseline も進むので、次の Round は completion reviewer が一度も見ていないコードを差分スコープで素通りさせる（origin: pre-existing）。Opus 設計レビュー（gdd-opus-advisor）の推奨どおり、Baseline を Step 13 が判定を返した Round の差し戻しのときだけ書くようにし、「Rounds が 0 なら全量」の句は取り除いた。commit: 6f7d7f6c。後に 6f7d7f6c を revert したため、この穴（main にもある）は残り、PR 本文の限界に書いた |
| H4-2 | 独立-4 | low | no | self-inflicted | doc-claim | accepted | 手順 6 の括弧書き（Step 10・13・19）と理由が、Rounds が 0 で止まる実際の経路と合っていない。句ごと取り除き、Baseline が無いときの説明に替えた。commit: 6f7d7f6c。後に 6f7d7f6c を revert したため文が戻り、PR 本文の限界に書いた |
| H5-1 | 独立-5 | high | yes | self-inflicted | fail-open | fixed | 前の規定で Round 開始時に書かれた `Completion Baseline` 行が進行中の tasklist に残ると、`Completion Rounds: 0` の再実行が差分スコープになり、Step 13 が見ていない範囲が done に届く（main にもある穴）。確かめの差分巡 2 回の後のため直さず、PR 本文の限界の先頭に「直していない常時 High・実害クラス」として書き、断片の User Action Required に移行の手順を書いた。前提の 6f7d7f6c を revert して原因ごと取り除いた。commit: cdb6343f |
| H5-2 | 独立-5 | low | no | self-inflicted | request-drift | fixed | Baseline を書く時点の変更が、時間超過の出口の範囲を超えてすべての completion-check の経路に効くことを、ユーザーが確かめた記録が無い。確かめの差分巡 2 回の後のため、PR 本文の限界に依頼から外れたままとして書いた。前提の 6f7d7f6c を revert して原因ごと取り除いた。commit: cdb6343f |
| H5-3 | 独立-5 | low | no | self-inflicted | product | fixed | Step 13 が判定を返すまで Baseline が無いので、その間に Rounds の行が消えると初回と見分けられない。PR 本文の限界に書いた。前提の 6f7d7f6c を revert して原因ごと取り除いた。commit: cdb6343f |
| H5-4 | 独立-5 | low | no | self-inflicted | doc-claim | fixed | 手順 4 の Why と state-machine の「直前 Round の修正だけに絞られる」が、Part A・B の差し戻しで Baseline が動かなくなった後の実際と合わない。PR 本文の限界に書いた。前提の 6f7d7f6c を revert して原因ごと取り除いた。commit: cdb6343f |
| H5-5 | 独立-5 | low | no | self-inflicted | doc-claim | fixed | 断片と PR 本文が「停止の後の再実行は全量」と条件を付けずに書いている（前に Step 13 が判定を返した差し戻しがあれば差分スコープ）。PR 本文の限界に書いた。前提の 6f7d7f6c を revert して原因ごと取り除いた。commit: cdb6343f |
| H5-6 | 独立-5 | low | no | self-inflicted | doc-claim | fixed | 断片の User Action Required が「なし」のまま。移行の手順を断片に書いた（断片だけの変更で、巡は回していない）。revert に合わせて「なし」に戻した。commit: 385eddcb |
| I6-1 | 独立-6 | high | yes | self-inflicted | fail-open | fixed | Round 開始時に Baseline を書かなくなったため、Step 13 の判定つきの差し戻しより前に Rounds の行が欠けると、上限超過の fail-closed が効かない。Opus 設計レビュー（gdd-opus-advisor）の推奨どおり 6f7d7f6c を revert した。commit: cdb6343f |
| I6-2 | 独立-6 | medium | no | self-inflicted | request-drift | fixed | Baseline の記録時点の変更・Part A/B での非更新・手での移行は依頼に無い。6f7d7f6c を revert して依頼の範囲に戻した。commit: cdb6343f |
| I6-3 | 独立-6 | medium | no | self-inflicted | product | accepted | main が gate runner を止めたときの停止理由を、止めた時点の state を見ずに決め打ちしている（PR フローの途中で止めると事実と違う）。PR 本文の限界に書いた |
| I6-4 | 独立-6 | low | no | self-inflicted | doc-claim | fixed | 断片と PR 本文が「停止の後の再実行は全量」と条件なしに書いている。revert で該当の文が無くなった。commit: cdb6343f |
| I6-5 | 独立-6 | low | no | self-inflicted | doc-claim | accepted | 手順 4 の Why の「直前 Round の修正のみ」が実際と合わない。PR 本文の限界に書いた |
| I6-6 | 独立-6 | low | no | self-inflicted | doc-claim | accepted | rollback-patterns.md の「次の Round で blocker が 1 件出ればまたこの確認に戻る」が、Rounds を増やさない停止に合わない。PR 本文の限界に書いた |
| I6-7 | 独立-6 | low | no | self-inflicted | doc-claim | re-reported | `Next Action=gdd-completion-check` の用途が外部前提不足だけのまま（H2-4 と同じ） |
| I6-8 | 独立-6 | low | no | self-inflicted | product | re-reported | 手順 5 で diff_base_mismatch のときの停止マーカーの指示が文の上で消えた（H3-2 と同じ） |
| I6-9 | 独立-6 | low | no | self-inflicted | doc-claim | fixed | 断片の移行手順が条件の確かめ方を書いていない。revert に合わせて移行手順ごと消した。commit: 385eddcb |
| I6-10 | 独立-6 | low | no | self-inflicted | doc-claim | accepted | 断片の type が patch のまま（停止の条件を変える）。PR 本文の限界に書いた |
| I6-11 | 独立-6 | low | no | self-inflicted | doc-claim | fixed | 断片の移行手順が PR 本文に無い。revert で移行手順が無くなった。commit: 385eddcb |
| I6-A1 | 独立-6 | advisory | no | self-inflicted | doc-claim | accepted | :73 の主節「入力を狭めて」と括弧の「completion は入力を変えない」が 1 文の中で食い違う |
| I6-A2 | 独立-6 | advisory | no | inherited | doc-claim | accepted | § Reviewer Input and Time Budget の冒頭の対象に gdd-completion-reviewer が入っていない |
| I6-A3 | 独立-6 | advisory | no | inherited | product | accepted | Step 4b・4c で impl-gating に戻すものに bounce log の上限が無い |
| I7-1 | 独立-7 | medium | no | self-inflicted | product | accepted | Step 13 の指し先が、completion の毎回の起動に「計れないとき」の句（入力は 1 枚・blocking の条件・reviews.md への記録）を当てるように読める。PR 本文の限界に書いた |
| I7-2 | 独立-7 | low | no | self-inflicted | request-drift | accepted | `Completion Rounds` が 0 のときの全量再検証が、Step 10・19 の外部前提不足の停止の後の再実行にも及ぶ（費用が増える）ことを、ユーザーが確かめた記録が無い。無効化後の巡 2 回の後のため、PR 本文の限界に依頼から外れたままとして書いた |
| I7-3 | 独立-7 | low | no | self-inflicted | doc-claim | accepted | 全量再検証の理由が Step 19 では成り立たず、停止の列挙（Step 10・13・19）も足りない。PR 本文の限界に書いた |
| I7-4 | 独立-7 | low | no | self-inflicted | doc-claim | re-reported | `Next Action=gdd-completion-check` の用途が外部前提不足だけのまま（H2-4 と同じ） |
| I7-5 | 独立-7 | low | no | inherited | product | accepted | Post-Return Routing 手順 5 が列挙型で、worktree_mismatch や報告行の欠落を「不足 evidence」に送る。PR 本文の限界に書いた |
| I7-A1 | 独立-7 | advisory | no | self-inflicted | bookkeeping | accepted | 新しい出口で `gdd-completion-reviewer.status` の in_review をどう残すかが書かれていない |
| I7-A2 | 独立-7 | advisory | no | self-inflicted | product | accepted | main が runner を止めたときの再実行は Template 全体の再 dispatch で、人に渡るまで最大約 2 時間かかる |
| I7-A3 | 独立-7 | advisory | no | self-inflicted | product | accepted | 渡された後に人が取れる次の手（再実行・差分の分割・cancelled など）が無い |
| I7-A4 | 独立-7 | advisory | no | self-inflicted | bookkeeping | accepted | Skill RED-GREEN Evidence を抜粋から確かめられない（PR 本文の該当の節にある） |
