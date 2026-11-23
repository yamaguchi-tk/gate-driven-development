---
type: patch
---

#### Summary

- Stop hook と pre-push の reviewer の判定が、`TaskStop` を呼んだ background の dispatch を待ちから外すのを、host が「動いていない」と答えたときだけにした。外すのは、本文の JSON の `task_id`・`shell_id` が止めた id と同じ成功と、`No task found with ID: <id>`・`Task <id> is not running` のエラー（id が等しいときだけ）である。拒否（auto mode の分類器など）・ほかの文面のエラー・結果がまだ無い `TaskStop` では、その dispatch はまだ動いているかもしれないので、待ちに残す。期限 watchdog・loop state を消す停止の押し返し・継続の押し返し・pre-push の判定のどれも、この条件で外す
- 再開の後に前のプロセスの dispatch へ `TaskStop` を呼ぶと `No task found` で返るので、その dispatch は外れる
- `TaskStop` がほかの結果（拒否などのエラー、止めた id の無い成功）で返った dispatch は待ちに残るので、`TaskStop` を繰り返さず、loop state を保つ `<gdd-stop reason="clarification-needed">` で人に渡す。`blocked`・`cancelled` など loop state を消す停止は、dispatch が動いている間は押し返される。この出口を、`references/subagent-dispatch.md`（再開の手順と、reviewer の時間上限の超過）、`references/state-machine.md`、`references/human-check-template.md`（相談役の `TaskStop`）、`scripts/setup-gdd-loop.sh` の手順と、期限 watchdog・loop state を消す停止の押し返しの文面に書いた。`references/stop-hook-structured-markers.md` の待ちの定義も、host が動いていないと答えた `TaskStop` の結果に書き換えた

#### Affected Files

- `hooks/scripts/lib/transcript.py`・`hooks/scripts/lib/wait_watchdog.py`（コメントと押し返しの文面）・`references/subagent-dispatch.md`・`references/state-machine.md`・`references/human-check-template.md`・`references/stop-hook-structured-markers.md`・`scripts/setup-gdd-loop.sh`
- `tests/test_stop_hook_validate.py`・`tests/test_wait_watchdog.py`・`tests/test_stop_hook_resumed_agent_wait.py`・`tests/test_push_review_log_only.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- `python3 scripts/light-lane-related-tests.py --run . origin/main`・`bash plugins/gate-driven-development/tests/validate-plugin.sh`
- 直近 30 日の transcript で、変更の前と後の parser の in-flight の判定を比べた
