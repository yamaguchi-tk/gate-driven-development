---
type: patch
---

#### Summary

- human check の表示を、相談役（`gdd-opus-advisor` 2 本）の返りで止めない。main は表示と同じターンで相談役を background で起動し、返りを待たずに確認を出す。判断ポイントの行は `相談役の推奨: 確認中（届いたら全文を出し直す）` と書き、2 本が返ったら推奨を書いた確認の全文を出し直して止まり直す（相談役は起動し直さない）。人が先に返事をしたら相談役を止め、セッションが終わって返らなかった相談役は起動し直さない。相談役（判断の委任の相談も同じ）には、main が書き出した判断ポイントと案ではなく、人に見せる確認の文面をそのままファイルに書いて渡し、steering と依頼の原文（`request.md`）もパスで渡す。確認の中の案は参考で、相談役は依頼の原文から、そもそもどうあるべきかを先に問う
- セッションが終わって background の dispatch が返らなかったときの再開の手順を足した。完了通知も、host が動いていないと答えた `TaskStop` の結果も無い dispatch に `TaskStop` を 1 回呼んでから、`state.md` と `reviews.md` の最新 Round を読み、同じ Template で起動し直す（記録の済んだ Round の次から始まる）。期限 watchdog が上限超過で block しても、前のプロセスの dispatch なら再開の手順に従う
- Stop hook の継続の押し返しは、`TaskStop` に host が動いていないと答えた dispatch（本文の JSON の `task_id`・`shell_id` が止めた id と同じ成功に加えて "No task found"・"is not running" のエラー）を待たない。成功したときだけ外すと、再開の手順で前のプロセスの dispatch を止めても外れず、その後ずっと継続の押し返しが出ない。pre-push の記録では、止めた reviewer の理由が `reviewer-incomplete` から `reviewer-failed` に変わる（判定は変わらない）
- requirements-gating に時間の目安を足した。`state.md` の `Started At` から測り、reviewer を起動・再実行する前ごとに経過を確かめ、20 分を超えていたら新しい起動をせず、Round 上限到達と同じ扱いで途中の結果を人に見せる（Round 1 の初回の起動は必ず回す。Round 1 が返らないまま打ち切ったら `Round 1: 未完（timeout）` と書く）
- 要件を固める確認を足した。着手前の突き合わせの直後、`requirements.md` を書く前に、`既存とぶつかる` の上位と、範囲を決める `原文だけでは決まらない` の行を 3 問以内にまとめて人に聞き、`clarification-needed` で止まる（state.md は保つ）。返事を `request.md` に足してから要件を書く。聞く行が無いときは止まらない。委任（事前回答）があっても止まる。表示する質問は `worklog.md` にも写し、毎回「残りは推奨で任せる」の返し方を載せる。返事の無いまま再開したら、写した質問を出し直す。返事を受けたら残りを洗い直し、答えから新しく分かれた点や範囲を決める行が残れば、前の答えを前提にした次の問いで止まる（曖昧な点を徐々に狭める）。答えから新しく分かれた点は突き合わせの記録に行として足す。聞くのは 3 回までで、残った行は一つ前の突き合わせに戻って 1 回だけ見直す。人が残りを任せたら要件を書く。返事は、表示した質問を引用して `request.md` に残す。時間の目安は返事を受けた時刻から測る
- 着手前の突き合わせで `原文だけでは決まらない` とした語を AI が具体化するとき、原文の語が指しうる範囲を狭めない。一部に絞る仮決定は、質問にするか、全体を対象にした具体化にする。requirements の観点の reviewer は、突き合わせの行と行き先を読み、範囲を狭めた具体化を blocking にする（human check の前に止める）
- human check の一次表示を、判断ポイントと OK の範囲（どこまで自走するか・許可しないこと・人間に戻す条件・延期・削除）だけにした。なぜやるか・整理した要件・作り方・変更予定ファイル・検証・現在地は `requirements.md`・`state.md` に書き、一次表示は `詳細:` の 1 行で場所を指す。ズレ確認は、人に残った行があるときだけ書き、無ければ `<gdd-hitl-fields>` に `zure="none"` を宣言する（lint は `stage="none"` と同じくズレ確認を求めない）

#### Affected Files

- `references/human-check-template.md`、`references/autonomy.md`、`references/human-check-template-compact.md`、`references/subagent-dispatch.md`、`references/requirements-gating-steps.md`、`references/brainstorming-steps.md`、`references/state-machine.md`、`references/rollback-patterns.md`、`commands/gdd-dev.md`、`skills/gdd-brainstorming/SKILL.md`、`agents/gdd-opus-advisor.md`、`agents/gdd-planning-reviewer.md`、`hooks/scripts/lib/transcript.py`、`hooks/scripts/lib/wait_watchdog.py`、`scripts/lib/hitl_fields.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- Stop hook の in-flight の判定（`inflight_dispatch_ids`）と、HITL の lint の必須語（`required_words`）を変えた。human-check-waiting は state を保つ停止なので、相談役が background で動いていても押し返されない
