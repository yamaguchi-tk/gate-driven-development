---
type: patch
---

#### Summary

Stop hook のマージ待ちの押し返し（宣言のある側）を、直近 2 時間 10 分に起動し、まだ終わっていない background の処理（`run_in_background` の Bash、Agent の dispatch）があるときは出さないようにした。終わったときの通知でセッションが起き、次の Stop で改めて見る。それより前に起動した処理、起動の時刻を読めない処理は数えないので、終わらない処理が残っていても押し返しが止まり続けない。約束の文の側の押し返しは変えない。

#### Affected Files

- `plugins/gate-driven-development/hooks/scripts/lib/autonomy_pushback.py`
- `plugins/gate-driven-development/hooks/scripts/lib/transcript.py`
- `plugins/gate-driven-development/hooks/scripts/lib/wait_watchdog.py`
- `plugins/gate-driven-development/hooks/hooks.json`
- `plugins/gate-driven-development/references/post-merge-qa.md`
- `plugins/gate-driven-development/references/state-machine.md`

#### User Action Required

- なし

#### Validation / Eval Impact

- `python3 -m pytest plugins/gate-driven-development/tests/test_stop_hook_autonomy_pushback.py plugins/gate-driven-development/tests/test_wait_watchdog.py`
