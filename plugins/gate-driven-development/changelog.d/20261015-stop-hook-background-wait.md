---
type: patch
---

#### Summary

Stop hook は、待ちの background の Bash（期限 watchdog の timer、`wait-until.py`）がまだ終わっていない間も、`/gdd-dev` の継続（`Continue the active /gdd-dev run.`）を押し返さないようにした。今までは subagent の dispatch の待ちだけを見ていたので、background の Bash を待って止まった停止を押し返し、agent が同じ待ちを言い直していた。

- 待ちに数えるのは、単独の `sleep <秒>` と、`scripts/wait-until.py` を起動するコマンドだけ。ほかの background の Bash（テストの実行、`until … sleep` の loop など）を待って止まると、今までどおり押し返す
- 起動の時刻の窓は、マージ待ちの押し返しと同じ（直近 2 時間 10 分に起動し、完了通知も、host が動いていないと答えた `TaskStop` の結果（本文の JSON の `task_id`・`shell_id` が止めた id と同じ成功・`No task found`・`is not running`）もまだのもの。起動の時刻か shell の id を読めないものは数えない）
- 判定で例外が起きたら、hook-errors に記録して今までどおり押し返す

#### Affected Files

- `plugins/gate-driven-development/hooks/scripts/gdd_stop_hook.py`
- `plugins/gate-driven-development/hooks/scripts/lib/transcript.py`（`any_background_wait_running`）
- `plugins/gate-driven-development/references/stop-hook-structured-markers.md`
- `plugins/gate-driven-development/tests/test_stop_hook_background_wait.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- `tests/test_stop_hook_background_wait.py`（入口から: 走っている待ちの Bash〔単独の `sleep <秒>`・`wait-until.py`〕で押し返さない。許可リストの外の Bash・終わった・窓より古い・時刻が読めない・shell の id が無い・background の処理が無いときは押し返す。判定の例外で押し返し、記録する）
