---
type: patch
---

#### Summary

- Stop hook と pre-push の判定は、エラーでない `TaskStop` の結果で dispatch を待ちから外すのを、本文の JSON に止めた相手の id（`task_id`・`shell_id`）が書かれているときだけにした。JSON でない・id が無い・別の id の本文では、その dispatch は待ちに残る
- `TaskStop` の input の `shell_id`（host の schema の古い名前）も、`task_id` と同じく止めた相手として読む。両方あるときは、`No task found`・`is not running` の文面の id がどちらかと同じなら外す
- 止めた相手があるのに待ちから外さなかった `TaskStop` の結果（決まった文面に当たらないエラー、止めた id の無い成功）を、`.gdd/hook-errors.log` に `task_stop_unaccepted` として、tool_use_id ごとに 1 回だけ書く。host の結果の形の変化に気づくための記録で、判定には使わない
- 期限 watchdog・loop state を消す停止の押し返しの文面と、`references/subagent-dispatch.md`・`references/state-machine.md`・`references/stop-hook-structured-markers.md`・`references/output-format.md`・`scripts/setup-gdd-loop.sh` の、待ちから外れる結果の書き方を「本文の JSON の `task_id`・`shell_id` が止めた id と同じ成功・`No task found`・`is not running`」にそろえた。それ以外の結果（拒否、止めた id の無い成功など）では、`TaskStop` を繰り返さず `clarification-needed` で人に渡す

#### Affected Files

- `hooks/scripts/lib/transcript.py`・`hooks/scripts/lib/wait_watchdog.py`・`hooks/scripts/gdd_stop_hook.py`
- `references/subagent-dispatch.md`・`references/state-machine.md`・`references/stop-hook-structured-markers.md`・`references/output-format.md`・`scripts/setup-gdd-loop.sh`
- `tests/test_stop_hook_validate.py`・`tests/test_wait_watchdog.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- `python3 scripts/light-lane-related-tests.py --run . origin/main`・`bash plugins/gate-driven-development/tests/validate-plugin.sh`
- `tests/test_stop_hook_validate.py` に、止めた id の無い成功を待ちに残すこと、`shell_id` を読むこと、外さなかった結果を集めること、入口から hook-errors.log に 1 回だけ書くこと、書けなくても Stop hook が落ちないことのテストを足した
- 直近 30 日の transcript で、変更の前と後の読む側の出力（待ちの dispatch・background の Bash・再開した agent）を比べた
