---
type: patch
---

#### Summary

- 要件を固める確認（brainstorming の 9）の見直しで、リスクの段を前の判定より下げないようにした。見直しの突き合わせが起動できないか、出力の見出しがそろわないときは、上書きせずに、リスクの段を `高`（`判定できない: 見直しの突き合わせ unavailable`）に書き換えて未収束に進み、その理由を問いに書く。前の出力の写し（`request-crosscheck.before-revisit.md`）は 1 回だけ作る。見直しの前に、決まらなかった行の原文の語と聞いた問いを、`見直し <時刻>:` で始まる assistant の引用として `request.md` に足す。突き合わせ agent と completion reviewer は、この引用を依頼の原文に数えず、突き合わせ agent は判定し直す材料にする
- 答えから足す行は、原文の語の列に元の行の語と答えを引用し、根拠の列の先頭に `答えから` と書く。任された `既存とぶつかる` の行は、推奨を仮決定にして § ズレ確認 に書く。既存側がユーザーの決めた規則・方針なら、その側に仮決定して記録の場所を添える（requirements の観点の reviewer は、これを範囲の狭めとして止めない。この reviewer の範囲の狭めの検査は、`→ 仮決定:` の `既存とぶつかる` の行だけがあるときにも行う）
- 要件確認の再入は、最後の `要件確認:` 行（`回答` ならその前の行も）で決める。確認を行わない経路に、Direct Intent で 9 を縮めたときを足し、express から昇格したときは行わないと書き直した
- human check の一次表示の § ズレ確認 に `依頼の原文: なし` の行も出す。`具体化:` の行は扱い（具体化・追加・未解決）を先頭に書き、行数の目安を超えても落とさない。`worklog.md` の固定行に `回答:` の欄を足した
- 起動した相談役がまだ動いているターンは、確認を出し直さず、`human-check-waiting` の発言も出さずに終える。人が先に返事をしたときは、届いた推奨で全文を出し直さない
- requirements-gating の時間の目安（Step 4b）は、作業中の質問では起点を戻さず、事前回答の委任で一括提示の答えを適用したときは（行き先によらず）`要件ゲート再開:` の時刻から測る。skill の概要にも、処置の前に経過を確かめることを書いた
- completion reviewer は、一次表示に出したかを `human-check-draft.md` があればそれと照らす
- `requirements.md` のテンプレートで、`### ズレ確認` を Honest Limitations の後に置き、節一覧と quick の最小構成にも入れた
- `TaskStop` で待ちから外れる成功の書き方を、文書・押し返しの文面・未リリースの変更断片で「本文の JSON の `task_id`・`shell_id` が止めた id と同じ成功」にそろえた。`clarification-needed` の用途（`references/output-format.md`・`references/state-machine.md`）と `references/faq.md` の `blocked` の行に、`TaskStop` の受け渡しを書いた。`TaskStop` を繰り返さずに人に渡す押し返しの文面は、marker の後に要る見出しを含めて、書式を `references/stop-hook-structured-markers.md` と `references/output-format.md` で指す
- Stop hook と pre-push の判定は、エラーでない `TaskStop` の結果で dispatch を待ちから外すのを、本文の JSON（全部の text block）の `task_id`・`shell_id` が input で止めた id と同じときだけにした。今までは input と照らさずに JSON の `task_id` の dispatch を外していたので、input と違う id の dispatch が外れることがあった。input に id の無い `TaskStop` の成功は、何も外さない（待つ側に倒す）
- `TaskStop` の結果を待ちから外さなかった記録（`task_stop_unaccepted`）は、`.gdd/hook-errors.log` が読めないときも書き（読めない間は重複を確かめられないので、Stop のたびに書く）、本文に lone surrogate があっても 1 回だけ書く

#### Affected Files

- `references/brainstorming-steps.md`・`references/human-check-template.md`・`references/human-check-template-compact.md`・`references/requirements-gating-steps.md`・`references/requirements-template.md`・`references/state-machine.md`・`references/subagent-dispatch.md`・`references/stop-hook-structured-markers.md`・`references/output-format.md`・`references/faq.md`・`skills/gdd-requirements-gating/SKILL.md`・`agents/gdd-planning-reviewer.md`・`agents/gdd-completion-reviewer.md`・`agents/gdd-request-code-crosscheck.md`・`scripts/setup-gdd-loop.sh`
- `hooks/scripts/lib/wait_watchdog.py`（記録と押し返しの文面）・`hooks/scripts/lib/transcript.py`（成功の判定）
- `tests/test_wait_watchdog.py`・`tests/test_stop_hook_validate.py`・`tests/test_stop_hook_resumed_agent_wait.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- `python3 scripts/light-lane-related-tests.py --run . origin/main`・`bash plugins/gate-driven-development/tests/validate-plugin.sh`
- timer への `TaskStop` が `No task found`・`is not running` で返ったとき・ほかのエラーで返ったときと、`is not runnings` の文面のテストを足した。記録の、読めない log と lone surrogate のテストを足した。成功の JSON が input と違う id・input に id が無い・`shell_id` だけ・前の text block にあるときのテストを足した
