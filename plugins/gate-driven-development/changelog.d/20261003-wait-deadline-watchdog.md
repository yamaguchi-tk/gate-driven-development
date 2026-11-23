---
type: minor
---

#### Summary

GDD の Stop hook が、background で起動した reviewer（`gdd-planning-reviewer`・`gdd-security-reviewer`・`gdd-completion-reviewer`・`gdd-implementation-reviewer`）と `gdd-formal-gate-runner` の待ちに期限を強制するようになった。上限は planning・security・completion 30 分、implementation 20 分、gate-runner 60 分（起動から）。実行中のこれらの dispatch（起動応答の agentId があるもの）に、期限を覆う期限 timer（`Bash` の `run_in_background: true` で起動した `sleep <秒>` だけ。起動応答を確かめられ、まだ終わっておらず、満了が期限から期限の 10 分後まで）が無いまま止まろうとすると block し、`sleep <残り秒+60>` を置かせる。上限を超えて実行中なら（起動時刻が読めないときも）block し、`TaskStop` で止めさせる。host が動いていないと答えた `TaskStop` の結果（本文の JSON の `task_id`・`shell_id` が止めた id と同じ成功・`No task found`・`is not running`）が来た dispatch、同期の dispatch、人間に渡す停止（`cancelled`・`human-check-waiting`・`blocked`・`clarification-needed`・`staging-verification-blocked`。本文の marker だけで見分ける）、直近の実会話ターンが peer のときには当てない。この block は継続の block と連続 block の上限（6）を共有し、超えるときは block せずに後段（done guard など）に任せる。判定が例外になったときは `.gdd/hook-errors.log` に記録して何もしない。`references/subagent-dispatch.md` の時間上限の規定もこの形に合わせ、`/loop` での `ScheduleWakeup` の代用はやめた。

#### Affected Files

- `plugins/gate-driven-development/hooks/scripts/lib/wait_watchdog.py`
- `plugins/gate-driven-development/hooks/scripts/lib/stop_block_ceiling.py`
- `plugins/gate-driven-development/hooks/scripts/lib/transcript.py`
- `plugins/gate-driven-development/hooks/scripts/gdd_stop_hook.py`
- `plugins/gate-driven-development/references/subagent-dispatch.md`
- `plugins/gate-driven-development/tests/test_wait_watchdog.py`

#### User Action Required

- background で reviewer・gate-runner を起動したら、続けて `sleep <上限の秒数+60>` を `run_in_background: true` の Bash で起動する（置かないと Stop hook が block して案内する）

#### Validation / Eval Impact

- `tests/test_wait_watchdog.py` を足した（判定の単体と、入口からの block・連続 block の上限）
- `bash tests/validate-plugin.sh`
