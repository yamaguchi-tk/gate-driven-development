---
type: patch
---

#### Summary

Stop hook は、SendMessage で再開した agent の完了通知がまだの間も、`/gdd-dev` の継続（`Continue the active /gdd-dev run.`）を押し返さないようにした。今までは Agent・Task の起動だけを見ていたので、再開した agent を待って止まった停止を押し返し、agent が同じ待ちを言い直していた。

- 再開は、host が SendMessage の結果の行に書く `toolUseResult`（`success` が true で、`resumedAgentId` が空でない str）だけで読む。本文は読まない
- 再開の後に、同じ agentId の終わりの通知か host が動いていないと答えた `TaskStop` の結果（本文の JSON の `task_id`・`shell_id` が止めた id と同じ成功・`No task found`・`is not running`）が来たら終わりとする。行の順で決めるので、前の実行の通知の後に再開したものは、まだ走っているとする
- 再開の時刻の窓は、マージ待ちの押し返しと同じ（直近 2 時間 10 分。時刻を読めないものは数えない）
- 判定で例外が起きたら、hook-errors に記録して今までどおり押し返す
- マージ待ちの押し返し、期限 watchdog（`lib/wait_watchdog.py`）、pre-push のレビューの判定は、再開した agent を数えない（今までどおり）

#### Affected Files

- `plugins/gate-driven-development/hooks/scripts/gdd_stop_hook.py`
- `plugins/gate-driven-development/hooks/scripts/lib/transcript.py`（`any_resumed_agent_running`）
- `plugins/gate-driven-development/references/stop-hook-structured-markers.md`
- `plugins/gate-driven-development/tests/test_stop_hook_resumed_agent_wait.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- `tests/test_stop_hook_resumed_agent_wait.py`（入口から: 再開して通知がまだの agent で押し返さない。前の通知の後の再開も数える。終わりの通知・host が動いていないと答えた TaskStop の後、窓より古い・時刻が読めない、success が true でない、resumedAgentId が無い・空・str でない、toolUseResult が dict でないときは押し返す。関数を直接呼んで: toolUseResult が変でも同じ行のほかの block は読む。判定の例外で押し返し、記録する）
