---
type: patch
---

#### Summary

- 確認を出した Stop で request-diff の hook（`hooks/scripts/lib/request_diff.py`）が出し直させる対象を、欄とタグの形の崩れから、承認の書き込みの検査と同じ判定（`lib/request_diff_field.py` の `field_problem`）に広げた。`依頼との差` に `あり:`（タグ `differs`）の点がある確認も、ユーザーが答える前に出し直させる。今までは、ユーザーが OK した後に承認の書き込みで止まり、ユーザーは同じ判断にもう一度答えていた
- なし以外の出し直しの文は、推奨と無回答時のデフォルトを依頼より狭くせず、狭める案を `採用しない案:` に変わる AC を書いて並べるよう求める。ユーザーがその案を名指しで選んだ返事は承認に入れる（`commands/gdd-dev.md` #10 STEP 1、`references/human-check-template.md` § 止まり直さないもの 3。発言を `request.md` に足し、requirements.md に書き写して requirements-gating を 1 Round 回し、blocking の指摘で表示した案の中身が変わったときだけ再提示する）。今までは修正指示として扱い、もう一度確認を出していた
- 出し直させる上限（`MAX_FIELD_BLOCKS`）を、同じ人の発言のターンで 2 回から 3 回にした。形の崩れとなし以外が続いたときに、上限を使い切らないため
- 上限の後も答え直させない。3 回出し直させた後は止めずに、上の確認にそのまま答えてよいこと・依頼より狭い点を受け入れるならその点を名指しで答えることと、hook が見た行（読めない行と `なし` 以外の値）を人に知らせる。今までは上限の後は「答えないで」と知らせるだけで、問題のある確認に OK すると承認の書き込みで止まり、答え直させていた
- 上限の数えを記録（`request-diff.log`）ではなく、この hook が今のターンで block した回数で決める。block は記録に数えの行を書けたときだけ出し、main がマーカーの無い文で返しても数えは進む。記録を読めない・書けないときは、止めずに人へ知らせる（今までは問題のある確認の数を transcript から数え、main の書き方で上限が効かなくなることがあった）。`GDD_SKIP_REQUEST_DIFF` は `claude -p` の照合だけを切り、欄の検査は切らない（今までは両方を切っていた）
- 欄かタグに問題のある確認にユーザーが返事をした後は、確認を出し直さない。main がマーカーを付けない補正（最後の行の `<gdd-hitl-fields correction request-diff="none,…" decided="<返事の文>">`）を書けば、承認の書き込みの検査（`request_diff_approval.py`）は、補正の文全体を提示と同じ判定で見て、`decided` が提示の後のユーザーの返事に含まれれば承認を通す。依頼を狭める点は、返事がその点を名指しで選んだときだけ `none` にする。照らす返事は、人が打った・選んだ部分だけにする（host が足す `<system-reminder>` と、AskUserQuestion の質問文は外す）。人の発言の許可リストは `hooks/scripts/lib/human_reply.py` 1 つにまとめ、依頼の写し（`request_capture.py`）と同じ判定を読む。今までは、Stop の hook が動かなかった・記録を書けなかったときに、ユーザーは同じ判断にもう一度答えていた
- 表示の前の lint（`scripts/lint-hitl-decision-fields.py`）も同じ判定にし、`あり:` の点を落とす
- 欄の書き方の案内（`references/human-check-template.md`・`human-check-template-compact.md`・`rollback-patterns.md`・`requirements-gating-steps.md`・`README.md`）を、狭める案は採用しない案として並べ、`あり:` の点がある確認は出し直しになる形にそろえた。承認の書き込みの検査（`request_diff_approval.py`）の拒否の文の書き方の案内も同じ形にそろえ、補正の書き方を足した

#### Affected Files

- `hooks/scripts/lib/request_diff.py`・`hooks/scripts/lib/request_diff_approval.py`・`scripts/lint-hitl-decision-fields.py`
- `commands/gdd-dev.md`・`references/human-check-template.md`・`references/human-check-template-compact.md`・`references/rollback-patterns.md`・`references/requirements-gating-steps.md`・`README.md`
- `hooks/scripts/lib/request_diff_field.py`・`hooks/scripts/lib/human_reply.py`（新規）・`hooks/scripts/lib/request_capture.py`
- `tests/test_request_diff_hook.py`・`tests/test_request_diff_approval_gate.py`・`tests/test_lint_hitl_decision_fields.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- `python3 scripts/light-lane-related-tests.py --run . origin/main`・`bash plugins/gate-driven-development/tests/validate-plugin.sh`
- `tests/test_request_diff_hook.py` で、hook の入口から、`あり:` の点がある確認を読み手を起動せずに出し直させ、文が採用しない案に並べるよう求めること、形の崩れとなし以外が続いても 3 回まで出し直させ、その後は最後の発言の形によらず知らせだけにすること、マーカーの無い返事が続いても block が 3 回で終わること、main の文やほかの hook の feedback に目印の文字列があっても数えが変わらないこと、session ごとに数えること、記録を書けないときは止めずに知らせること、記録の付け足しの欄を組み立てられない・引いた行を書き出せない確認でも、`GDD_SKIP_REQUEST_DIFF` でも出し直させること、判定で例外が出たら止めないこと、知らせが hook の見た行を並べることを確かめた。`tests/test_request_diff_approval_gate.py` で、欄かタグに問題のある確認への返事の後の補正で承認が通ること（wrapper の入口からも）、返事の前の補正・引用の無い補正・返事に無い引用の補正・なし以外の補正・読めない補正・数の違う補正・本文に `あり:` のある補正は通らないことを確かめた。`tests/test_lint_hitl_decision_fields.py` で、lint が `あり:` の点を落とすことを確かめた
