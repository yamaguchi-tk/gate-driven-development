---
lane: L1+
pr: 659
---

## 巡

| 巡 | reviewer | sha | high | medium | blocking | at |
|---|---|---|---|---|---|---|
| 独立-1 | light-lane-independent-reviewer, 全差分, model: opus | 51a98078907a2653122a2a0287e9ba737acf624b | 0 | 7 | 0 | 2026-11-12 |
| 独立-2 | light-lane-independent-reviewer-xhigh, 差分, model: fable | ef35e0baaae0d6603d04de2b72a925416dd80ebb | 0 | 3 | 1 | 2026-11-12 |
| 独立-3 | light-lane-independent-reviewer-xhigh, 差分, model: fable | 98ff8afb86d63ffd1623d5d8a537c1ad932f1feb | 0 | 3 | 0 | 2026-11-12 |
| 独立-4 | light-lane-independent-reviewer-xhigh, 差分（無効化後）, model: fable | 138e7fb7527134b0b6a2059d797922f71193d506 | 0 | 3 | 0 | 2026-11-12 |
| 独立-5 | light-lane-independent-reviewer-xhigh, 差分, model: fable | d41facff84841328b1061bc18cc5c0c11d4c36f9 | 0 | 4 | 0 | 2026-11-12 |
| 独立-6 | light-lane-independent-reviewer-xhigh, 差分, model: fable | faa703c95a80413e497ce758b53d7542eb4ad459 | 0 | 1 | 0 | 2026-11-12 |
| 独立-7 | light-lane-independent-reviewer-xhigh, 差分, model: fable | 9a1c49573cc217d5f6cdca93fb25813eb24a4ca4 | 0 | 1 | 0 | 2026-11-12 |
| 独立-8 | light-lane-independent-reviewer-xhigh, 差分, model: fable | 1a06aac06b19a6bf036cf88426dba6d3d10919c5 | 0 | 1 | 0 | 2026-11-12 |
| 方針メモ | Opus 設計レビュー ×2 (gdd-opus-advisor, model: opus) + user | 03b6a2d0bb5778374aab4d45a2f5e2eb82e995eb | 0 | 5 | 0 | 2026-11-12 |
| 独立-9 | light-lane-independent-reviewer-xhigh, 差分（無効化後）, model: fable | cb34307477acb11022f5e9a5597213507020b79a | 0 | 2 | 0 | 2026-11-12 |
| 独立-10 | light-lane-independent-reviewer-xhigh, 差分（無効化後）, model: fable | ac6249842b1f9d6efdcb377ba60098c90884dc2b | 0 | 3 | 0 | 2026-11-12 |
| 独立-11 | light-lane-independent-reviewer-xhigh, 差分, model: fable | 026332191f82abbd9c31d07d5dfc46303d5c6a13 | 0 | 1 | 0 | 2026-11-12 |
| 独立-12 | light-lane-independent-reviewer-xhigh, 差分, model: fable | 6ca71df770b3687c64a9b722357be917785990f1 | 0 | 1 | 0 | 2026-11-12 |

## 指摘

| id | 巡 | severity | 実害 | 自己起因 | クラスタ | 対応 | 要約 |
|---|---|---|---|---|---|---|---|
| I1-1 | 独立-1 | medium | no | self-inflicted | hitl-advisor-append | accepted | 原則 7 の追記と § 判断の書き方 8・Invariant の食い違い（推奨案を変えるときの出し直し） |
| I1-2 | 独立-1 | medium | no | self-inflicted | planning-time-budget | accepted | 4b の起点（brainstorming の開始）を書く手順が無い |
| I1-3 | 独立-1 | medium | no | self-inflicted | hitl-length | fixed | compact:7 が必須の見出しを落とさせる。commit: ef35e0ba |
| I1-4 | 独立-1 | medium | no | self-inflicted | hitl-length | fixed | 依頼の 4 を条件つきに狭めていた。中身を判断ポイントと OK の範囲だけにした。commit: ef35e0ba |
| I1-5 | 独立-1 | medium | no | self-inflicted | request-depth | fixed | 要件の深掘りを 1 文に狭めていた。reviewer の 1 枚に突き合わせの行を写し、範囲の狭めを blocking にした。commit: ef35e0ba |
| I1-6 | 独立-1 | medium | no | self-inflicted | resume-inflight | fixed | 再開後の失敗した TaskStop を in-flight の判定が外さない。ユーザーの決定（問 2 案 B）で、inflight_dispatch_ids が TaskStop の target を結果を問わず外す。commit: f17282b1 |
| I1-7 | 独立-1 | medium | no | self-inflicted | planning-time-budget | fixed | 4b の発火条件の実測が無い。測れた 2 件とも 40 分超（52 分・約 58 分）を PR 本文に書く。commit: なし（PR 本文） |
| I1-8 | 独立-1 | low | no | self-inflicted | hitl-advisor-append | accepted | 追記のターンで HITL lint が誤った不通過を出す |
| I1-9 | 独立-1 | low | no | self-inflicted | planning-time-budget | accepted | 4b は Round の中では止まらず、起動し直しのときの起点が未定 |
| I1-10 | 独立-1 | low | no | self-inflicted | planning-time-budget | accepted | 4b の停止の上限到達の語と選択肢が未定 |
| I1-11 | 独立-1 | low | no | self-inflicted | watchdog-review | fixed | watchdog の見直し結果が無い。PR 本文と再開の手順に書いた。commit: ef35e0ba |
| I1-12 | 独立-1 | low | no | self-inflicted | watchdog-review | fixed | 期限切れの block と再開の手順が割れる。commit: ef35e0ba |
| I1-13 | 独立-1 | low | no | self-inflicted | test-power | accepted | human-check-waiting が押し返されないことを固定するテストが無い |
| I1-14 | 独立-1 | advisory | no | self-inflicted | budget | accepted | 予算の確認結果を PR 本文に書く |
| I1-15 | 独立-1 | advisory | no | self-inflicted | hitl-advisor-append | accepted | 相談役が動いている間に人が意見を求めたときの扱い |
| I1-16 | 独立-1 | advisory | no | self-inflicted | hitl-advisor-append | accepted | background の無い runtime での扱い |
| I1-17 | 独立-1 | advisory | no | self-inflicted | root-claudemd | out-of-diff | root CLAUDE.md の確認の前の相談役 2 本も同じ形 |
| I2-1 | 独立-2 | medium | yes | self-inflicted | hitl-length | fixed | 設計: 変える（一次表示の中身を依頼の語で無条件に絞った決定）。compact:7 を上位の正本と合う条件つきに戻した。決定: 依頼 4 を一次表示の組み替え（テンプレート・lint も変える）と読むか。commit: 007c4448 |
| I2-2 | 独立-2 | medium | no | self-inflicted | request-depth | fixed | 4c の規則が reviewer に届かない。reviewer の定義と 1 枚の中身に足した（依頼の深掘りに合わせる修正）。commit: 007c4448 |
| I2-3 | 独立-2 | medium | no | self-inflicted | watchdog-review | fixed | 依頼 2 の hook の変更はこの PR で行う（ユーザーの決定「Fableの推奨で進める」、問 2 案 B）。commit: f17282b1 |
| I2-4 | 独立-2 | low | no | self-inflicted | watchdog-review | accepted | hook が名指しする節に再開の例外が無い |
| I2-5 | 独立-2 | low | no | self-inflicted | watchdog-review | accepted | 前のプロセスの dispatch を見分ける条件が無い |
| I2-6 | 独立-2 | low | no | self-inflicted | request-depth | fixed | 「要件の深掘り」は HITL の前に人に聞く工程まで含む（ユーザー「HITLの前に人に聞く工程もこのPRで対応して」）。要件を固める確認を足した。commit: 37a4ed11 |
| I2-7 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | in-flight から外れないのは TaskStop が失敗したときだけ |
| I2-8 | 独立-2 | advisory | no | self-inflicted | doc-claim | accepted | watchdog の文の引用が実際の文と違う |
| I2-9 | 独立-2 | advisory | no | self-inflicted | doc-claim | fixed | 断片の Summary の「変えていない」を外した。commit: 633162b9 |
| I3-1 | 独立-3 | medium | no | self-inflicted | hitl-length | fixed | 依頼 4 は一次表示の組み替えと読む（ユーザーの決定、問 1 案 B）。判断ポイントと OK の範囲だけにした。commit: 68b9b620 |
| I3-2 | 独立-3 | low | no | self-inflicted | hitl-length | accepted | 数えて移すは express・quick (standard) の目安と必須の見出しが両立しない |
| I3-3 | 独立-3 | low | no | self-inflicted | request-depth | accepted | 1 枚に行が写っていないと範囲の狭めの観点が当たらない |
| I3-4 | 独立-3 | low | no | self-inflicted | request-depth | accepted | 「Step 4c の写し」が規則の文の写しとも読める |
| I3-5 | 独立-3 | low | no | self-inflicted | request-depth | accepted | 再入の advisory の規則と範囲の狭めの blocking のどちらが勝つかが無い |
| I3-6 | 独立-3 | low | no | self-inflicted | request-depth | accepted | ユーザーが狭めると決めた具体化の除外が reviewer 側に無い |
| I3-7 | 独立-3 | medium | no | self-inflicted | request-depth | fixed | I2-6 と同じ。commit: 37a4ed11 |
| I3-8 | 独立-3 | medium | no | self-inflicted | watchdog-review | fixed | I2-3 と同じ。ユーザーの決定で hook も直した。commit: f17282b1 |
| I3-9 | 独立-3 | low | no | inherited | bookkeeping | out-of-diff | 断片の Validation 欄に検証の種類が無い |
| I3-10 | 独立-3 | low | no | inherited | planning-time-budget | out-of-diff | 40 分の目安は Round を始めた後の超過を止めない |
| I4-1 | 独立-4 | medium | no | self-inflicted | planning-time-budget | accepted | 起点が Started At で、human check をまたいだ後の Round が必ず目安を超える |
| I4-2 | 独立-4 | medium | no | self-inflicted | planning-time-budget | accepted | 経過を確かめる位置が処置の後で、処置済みの blocking を一括提示に出す |
| I4-3 | 独立-4 | medium | no | self-inflicted | planning-time-budget | fixed | 経過の確認を reviewer の起動と再実行の前ごとに置き、Round 1 は初回だけ必ず回す（ユーザーの決定、問 3）。commit: 37a4ed11 |
| I4-4 | 独立-4 | low | no | self-inflicted | planning-time-budget | accepted | Started At が読めない・時差の表記が無いときの倒し方が無い |
| I4-5 | 独立-4 | low | no | self-inflicted | planning-time-budget | accepted | 実測が Round 2 以降で止まる分を示していない |
| I4-6 | 独立-4 | advisory | no | self-inflicted | planning-time-budget | accepted | 一括提示の出口を挙げるほかの箇所が時間の目安を挙げていない |
| I5-1 | 独立-5 | medium | no | self-inflicted | request-lockin | fixed | 入口の文書が質問で止まる例外を intake だけにしていた。gdd-dev.md 9 と SKILL.md に足した。commit: faa703c9 |
| I5-2 | 独立-5 | medium | no | self-inflicted | request-lockin | fixed | 2 種類の clarification-needed を見分ける条件が無い。worklog の最後の 要件確認: 行で見分ける。commit: faa703c9 |
| I5-3 | 独立-5 | medium | no | self-inflicted | request-lockin | fixed | 委任のときの扱いが事前回答の節と合わない。確認を行わず (5) に流す。commit: faa703c9 |
| I5-4 | 独立-5 | medium | no | self-inflicted | request-lockin | fixed | 発火件数が無い。手元の 3 件すべてで止まることを PR 本文に書く。commit: なし（PR 本文） |
| I5-5 | 独立-5 | medium | no | self-inflicted | hitl-length | re-reported | 確認待ちの 3 件に返事が無い（I2-1・I2-3・I4-3 の再掲） |
| I5-6 | 独立-5 | low | no | self-inflicted | request-lockin | accepted | 聞く対象を範囲を決める行と 3 問に絞っている |
| I5-7 | 独立-5 | low | no | self-inflicted | planning-time-budget | accepted | 返事の時刻から測ると質問を出すまでの時間も消える |
| I5-8 | 独立-5 | low | no | self-inflicted | request-lockin | accepted | 行き先 回答 が固定行の書式に無い |
| I5-9 | 独立-5 | low | no | self-inflicted | doc-claim | accepted | 断片の User Action Required と type |
| I5-10 | 独立-5 | low | no | self-inflicted | request-lockin | accepted | Direct Intent のときに確認を行うかが食い違う |
| I5-11 | 独立-5 | advisory | no | self-inflicted | bookkeeping | accepted | Skill RED-GREEN Evidence は notes にある |
| I5-12 | 独立-5 | advisory | no | self-inflicted | request-lockin | fixed | 待ちのまま終わったときの再入。同じ質問を出し直す。commit: faa703c9 |
| I6-1 | 独立-6 | medium | no | self-inflicted | request-lockin | fixed | 再開の判定に比べられる時刻が無い。main が 要件確認: 回答 を書き、runner は最後の行だけで決める。commit: 9a1c4957 |
| I6-2 | 独立-6 | low | no | self-inflicted | request-lockin | fixed | 委任で確認を飛ばすのが依頼に合わない。委任でも止める。commit: 9a1c4957 |
| I6-3 | 独立-6 | low | no | self-inflicted | request-lockin | fixed | runner の Template に確認の停止がつながっていない。実行手順 1 に足した。commit: 9a1c4957 |
| I6-4 | 独立-6 | low | no | self-inflicted | request-lockin | accepted | SKILL.md の :127・:223 に確認と食い違う文が残る |
| I6-5 | 独立-6 | low | no | self-inflicted | request-lockin | fixed | (5) に流す の対象の食い違い。委任の分岐を外して解消。commit: 9a1c4957 |
| I6-6 | 独立-6 | low | no | self-inflicted | request-lockin | fixed | 再開で出し直す挙動を断片と PR 本文に書いた。commit: 9a1c4957 |
| I6-7 | 独立-6 | advisory | no | self-inflicted | request-lockin | fixed | Post-Return Routing の文を 2 文に分けた。commit: 9a1c4957 |
| I7-1 | 独立-7 | medium | no | self-inflicted | request-lockin | accepted | 質問の本文が steering に残らず、起動し直した runner が返事を行に対応づけられない |
| I7-2 | 独立-7 | low | no | self-inflicted | request-lockin | accepted | gdd-dev.md 9 の 0 に返事の後の main の手順が無い |
| I7-3 | 独立-7 | low | no | self-inflicted | request-lockin | accepted | 確認と intake を worklog の状態で見分けている |
| I7-4 | 独立-7 | low | no | self-inflicted | request-lockin | accepted | 起動し直すときの Template の欄の埋め方が無い |
| I7-5 | 独立-7 | low | no | self-inflicted | request-lockin | accepted | 最後の行の値の なし・行なし の扱い |
| I7-6 | 独立-7 | low | no | self-inflicted | request-lockin | fixed | 3 問以内は保ち、聞くのは 3 回まで、残りは human check の質問に回す（ユーザーの決定、問 4）。commit: 37a4ed11 |
| I7-7 | 独立-7 | medium | no | self-inflicted | hitl-length | re-reported | 依頼 4 の読み替え（I2-1 の再掲） |
| I7-8 | 独立-7 | medium | no | self-inflicted | planning-time-budget | re-reported | 1 時間を超える経路が残る（I4-3 の再掲） |
| I7-9 | 独立-7 | low | no | self-inflicted | watchdog-review | re-reported | hook の穴を別の PR に回している（I2-3 の再掲） |
| I7-10 | 独立-7 | advisory | no | self-inflicted | doc-claim | accepted | next-plan 側に Stage ごとに止まることが書かれていない |
| I8-1 | 独立-8 | medium | no | self-inflicted | request-lockin | accepted | 新しく分かれた点に記録先が無く、範囲の狭めの検査に届かない |
| I8-2 | 独立-8 | low | no | self-inflicted | request-lockin | accepted | 繰り返しの終了条件が自由文の判定だけで、回数の上限が無い |
| I8-3 | 独立-8 | low | no | self-inflicted | request-lockin | accepted | 2 回目以降の質問の文面が steering に残らない |
| I8-4 | 独立-8 | low | no | self-inflicted | request-lockin | accepted | 行き先 回答 が固定行の書式に無い |
| I8-5 | 独立-8 | low | no | self-inflicted | doc-claim | fixed | 質問を引用して残す挙動と 1 回以上止まることを PR 本文に書いた。commit: なし（PR 本文） |
| I8-6 | 独立-8 | low | no | self-inflicted | doc-claim | fixed | 2 回目以降の停止は未測と PR 本文に書いた。commit: なし（PR 本文） |
| I8-7 | 独立-8 | medium | no | inherited | planning-time-budget | re-reported | 1 時間を超える経路が残る（I4-3 の再掲） |
| I8-8 | 独立-8 | medium | no | inherited | hitl-length | re-reported | 依頼 4 の読み替え（I2-1 の再掲） |
| I8-9 | 独立-8 | low | no | inherited | watchdog-review | re-reported | hook の修正を別の PR にしている（I2-3 の再掲） |
| I8-10 | 独立-8 | advisory | no | self-inflicted | style | accepted | 同じ文の重複と Why の引用 |
| M1 | 方針メモ | medium | no | self-inflicted | resume-inflight | fixed | 草案の事実の誤り（成功した TaskStop は今も外れる。残るのは is_error と読めない本文）を直し、PR 旧#334 の決定とテスト 3 件の反転を明記した。commit: a70057ad |
| M2 | 方針メモ | medium | no | self-inflicted | resume-inflight | fixed | 正本を 1 つにする: running_background_agent と wait_watchdog の TaskStop の重複条件を消した（別の commit）。commit: 7898715d |
| M3 | 方針メモ | medium | no | self-inflicted | resume-inflight | fixed | 読み手に any_background_running（マージ待ちの押し返し）と subagent_in_flight を足した（結果は変わらない）。commit: なし（方針メモ） |
| M4 | 方針メモ | medium | no | self-inflicted | resume-inflight | fixed | 文書の配線: subagent-dispatch.md の再開の手順、docstring、changelog の断片、lane を L1+ に。commit: f17282b1 |
| M5 | 方針メモ | medium | no | self-inflicted | resume-inflight | accepted | 限界: エラーで返った TaskStop の後も動く agent を外しうる。実測 81 件の is_error は全部 No task found か is not running、後で通知が来た 22 件は全部 completed。No task found の後に completed が来た 3 件は限界に書く |
| I9-1 | 独立-9 | medium | no | self-inflicted | hitl-length | fixed | 設計: 変えない（一次表示の規定の写しが skill に残っていただけ）。HITL を作る skill 2 本の一次表示の規定を新しい形に合わせた（依頼 4 が届かない run を防ぐ）。commit: 850c1421 |
| I9-2 | 独立-9 | medium | no | self-inflicted | hitl-length | fixed | 設計: 変えない（ズレ確認の置き場の規定を合わせるだけ）。ズレ確認の中身は requirements.md、一次表示は人に残った行だけ。要件を固める確認の残りは質問 2 個の上限に数えない。commit: 850c1421 |
| I9-3 | 独立-9 | low | no | self-inflicted | hitl-length | accepted | 延期・削除: の 1 行形を decision-quality の lint が受けない（hook に配線されていない lint） |
| I9-4 | 独立-9 | low | no | self-inflicted | test-power | accepted | decision-quality のテストが returncode を見ていない |
| I9-5 | 独立-9 | low | no | self-inflicted | hitl-length | accepted | zure="none" と書けばズレ確認を落とした表示を lint が見逃す（stage と同じ自己申告。PR 本文の限界に書いた） |
| I9-6 | 独立-9 | low | no | self-inflicted | request-lockin | accepted | 待ちの行 3 本の数え方が出し直しで狂いうる |
| I9-7 | 独立-9 | low | no | self-inflicted | request-lockin | accepted | 答えから分かれた点を突き合わせの記録に足す行の形が決まっていない |
| I9-8 | 独立-9 | low | no | self-inflicted | planning-time-budget | accepted | 時間の目安で再実行しなかったときの reviews.md の行と選択肢が subagent-dispatch.md と食い違う |
| I9-9 | 独立-9 | low | no | self-inflicted | doc-claim | accepted | 一次表示からリスクの段が消えたことが crosscheck agent の定義と非エンジニア向けガイドに無い |
| I9-10 | 独立-9 | low | no | self-inflicted | doc-claim | accepted | 断片の type: patch が足した仕組みと合わない |
| I9-11 | 独立-9 | low | no | self-inflicted | request-advisor-question | fixed | 決定: ユーザーが「原則7も変える」と返した。原則 7 で相談役に依頼の原文も渡し、選択肢と main の案は参考として渡す。commit: 02633219 |
| I10-1 | 独立-10 | medium | no | self-inflicted | requirements-template | accepted | requirements-template と express テンプレートに requirements.md の ### ズレ確認 の節が無い |
| I10-2 | 独立-10 | medium | no | self-inflicted | hitl-length | accepted | 一次表示に出ない具体化の行を、OK の返事で承認したものとして request.md に写す規定が残る（PR 本文の限界に書いた） |
| I10-3 | 独立-10 | medium | no | self-inflicted | hitl-length | accepted | 一次表示に出す人に残った行の集合が full と compact で違う（unavailable・判定できない） |
| I10-4 | 独立-10 | low | no | self-inflicted | doc-claim | accepted | 依頼の原文: なし の行の出し先が新しい列挙に無い |
| I10-5 | 独立-10 | low | no | self-inflicted | doc-claim | accepted | GDD Complexity Budget の正本と写像表が 8 項目を残すのまま |
| I10-6 | 独立-10 | low | no | self-inflicted | doc-claim | accepted | 一次表示に出すものの列挙が skill 2 本と正本で 3 通り |
| I10-7 | 独立-10 | low | no | inherited | doc-claim | accepted | gdd-resume の HITL の列挙が古い |
| I10-8 | 独立-10 | low | no | inherited | doc-claim | accepted | express 昇格の規定が human check のズレ確認で上位 3 件を聞くのまま |
| I10-9 | 独立-10 | low | no | inherited | doc-claim | accepted | worklog の固定行に行き先 回答 の欄が無い |
| I10-10 | 独立-10 | low | no | inherited | hitl-length | accepted | 記録だけの lint が新しい 延期・削除: の行で誤って失敗を記録する |
| I10-11 | 独立-10 | low | no | self-inflicted | doc-claim | accepted | ズレ確認の節の例と参照先が置き場の移動に追随していない |
| I10-12 | 独立-10 | low | no | self-inflicted | doc-claim | accepted | 断片の Affected Files に gdd-requirements-gating の SKILL.md が無い |
| I10-13 | 独立-10 | advisory | no | self-inflicted | bookkeeping | accepted | Skill RED-GREEN Evidence を reviewer は確かめていない |
| I11-1 | 独立-11 | medium | no | self-inflicted | request-advisor-question | fixed | 設計: 変える（相談役の材料を原則 7 と判断の委任で別々に定めていた）。依頼の「Fableへの問い」に当たる判断の委任の材料も、確認の文面・steering・request.md のパスにそろえた。commit: fcea4dad |
| I11-2 | 独立-11 | low | no | self-inflicted | request-advisor-question | fixed | 原則 7 の「同じ材料」が判断の委任の材料と合わない。I11-1 と同じ commit で材料を 1 つにした。commit: fcea4dad |
| I11-3 | 独立-11 | low | no | self-inflicted | request-advisor-question | fixed | request.md が無い・not-copied のときの扱い。その旨の 1 行を渡すと書いた（原則 7 の文を書き直す commit に含まれた）。commit: fcea4dad |
| I11-4 | 独立-11 | advisory | no | self-inflicted | doc-claim | fixed | Why の文を事実だけにした（原則 7 の文を書き直す commit に含まれた）。commit: fcea4dad |
| I12-1 | 独立-12 | medium | no | self-inflicted | request-advisor-question | accepted | 委任の経路で、相談役が確認に並んでいない案を推したときに止まる規定が無い |
| I12-2 | 独立-12 | low | no | self-inflicted | request-advisor-question | accepted | 「サブエージェントに…まるごと渡して」の範囲は相談役だけ（ユーザーの返事で決定） |
| I12-3 | 独立-12 | low | no | self-inflicted | request-advisor-question | accepted | 済ませた 1 本の推奨が draft に入り、もう 1 本の材料になる |
| I12-4 | 独立-12 | low | no | self-inflicted | doc-claim | accepted | not-copied のとき request.md のパスを渡さない読みができる |
| I12-5 | 独立-12 | low | no | self-inflicted | request-advisor-question | accepted | draft の書き込みが steering write guard に止められたときの扱いが無い |
| I12-6 | 独立-12 | low | no | self-inflicted | doc-claim | accepted | Handoff の材料の置き場が決まっていない |
| I12-7 | 独立-12 | low | no | self-inflicted | doc-claim | accepted | 相談役の定義の description と例が変更前の材料のまま |
| I12-8 | 独立-12 | low | no | self-inflicted | doc-claim | fixed | draft のファイル名と steering に残ることを PR 本文に書いた。commit: なし（PR 本文） |
| I12-9 | 独立-12 | low | no | self-inflicted | doc-claim | fixed | 材料の変更に読む時期と戻す条件を PR 本文に書いた。commit: なし（PR 本文） |
| I12-10 | 独立-12 | advisory | no | self-inflicted | request-advisor-question | accepted | draft に gdd-stop の marker が入る |
| I12-11 | 独立-12 | advisory | no | self-inflicted | bookkeeping | accepted | Skill RED-GREEN Evidence を reviewer は確かめていない |
| I12-12 | 独立-12 | advisory | no | self-inflicted | request-advisor-question | accepted | 確認の文面を 2 回出力する |
