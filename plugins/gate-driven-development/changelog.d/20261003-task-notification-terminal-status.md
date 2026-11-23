---
type: patch
---

#### Summary

Stop hook が background の subagent を「実行中」と判定する条件を直した。これまでは `<task-notification>` の `<status>completed</status>` だけを終わりとしていたので、reviewer が `failed`（stream watchdog の停止など）で返ったときや、`TaskStop` で止めたときに、その subagent がセッションの終わりまで実行中のままになり、継続の nudge が出なかった。`<status>` を持つ通知は、終わっていない status（`in_progress`・`running`・`pending`）を除いて終わりとして扱い（`failed`・`killed`・`stopped` を含む）、`TaskStop` の成功結果（本文の JSON の `task_id`・`shell_id` が input で止めた id と同じもの）と、host が動いていないと答えたエラー（`No task found`・`is not running`。id が input と同じときだけ）も終わりとして扱う。前のセッションの孤児をまとめた通知に並ぶ複数の `<task-id>` も全部拾う。id と status は通知のヘッダ（`<summary>`・`<result>`・`<event>` より前）からだけ拾い、subagent の本文に引用された id では終わりにしない。`<status>` を持たない Monitor のイベント通知は終わりにしない。

#### Affected Files

- `plugins/gate-driven-development/hooks/scripts/lib/transcript.py`
- `plugins/gate-driven-development/tests/test_stop_hook_validate.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- `tests/test_stop_hook_validate.py` の `TestSubagentInFlightUnit`・`TestHookInflightSubagent` にテストを足した
- `bash tests/validate-plugin.sh`
