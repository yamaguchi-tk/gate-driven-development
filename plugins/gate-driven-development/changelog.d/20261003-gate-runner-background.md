---
type: minor
---

#### Summary

`/gdd-dev` が active の間、main セッションからの `gdd-formal-gate-runner` の同期起動を PreToolUse hook が deny するようになった。`references/subagent-dispatch.md` の 4 つの formal gate の Template（planning・design-gating・implementation-gating・completion-check）は `run_in_background=True` で起動し、起動の後に期限 timer（`sleep 3660`）を置いて、gate-runner 自身の完了通知の result で Post-Return Routing に進む。これで、Stop hook の期限 watchdog が gate-runner の待ちに当たる。subagent の中からの起動（payload に `agent_id` がある）、reviewer などほかの type、JSON として読めない payload（`.gdd/hook-errors.log` に記録する）は deny しない。

background の dispatch の完了通知を待つときは、`<gdd-stop>` を書かずに turn を終える（停止ではなく待ち）。継続契約、`references/state-machine.md` § Autonomous Continuation、`commands/gdd-dev.md`、`skills/gdd-brainstorming/SKILL.md` の No Manual Polling（これまでは `blocked` で止まって待つと書いていた）を、この形に直した。

Stop hook は、background の dispatch（type を問わない。起動応答の agentId があり、完了通知も、host が動いていないと答えた `TaskStop` の結果（本文の JSON の `task_id`・`shell_id` が止めた id と同じ成功・`No task found`・`is not running`）もまだのもの）が動いている間、loop state（`.claude/gdd-dev.local.md`）を消す停止（`done`・`blocked`・`cancelled`・`staging-verification-blocked`）を、state を消す直前に block する。停止理由が本文の marker、tool result の marker、`external-review-waiting` のポーリング上限での `blocked` への昇格のどれで決まっても当たり、`done` では post-merge の seed を書く前に当たる。連続 block の上限・直近のターンが peer・判定の例外のときは通す（期限 watchdog と同じ）。

#### Affected Files

- `plugins/gate-driven-development/hooks/scripts/lib/background_dispatch_gate.py`
- `plugins/gate-driven-development/hooks/scripts/run-background-dispatch-gate-hook.sh`
- `plugins/gate-driven-development/hooks/hooks.json`
- `plugins/gate-driven-development/hooks/scripts/lib/wait_watchdog.py`
- `plugins/gate-driven-development/hooks/scripts/lib/constants.py`
- `plugins/gate-driven-development/hooks/scripts/gdd_stop_hook.py`
- `plugins/gate-driven-development/scripts/setup-gdd-loop.sh`
- `plugins/gate-driven-development/references/subagent-dispatch.md`
- `plugins/gate-driven-development/references/state-machine.md`
- `plugins/gate-driven-development/commands/gdd-dev.md`
- `plugins/gate-driven-development/skills/gdd-brainstorming/SKILL.md`
- `plugins/gate-driven-development/README.md`
- `plugins/gate-driven-development/tests/test_background_dispatch_gate.py`
- `plugins/gate-driven-development/tests/test_wait_watchdog.py`

#### User Action Required

- Template を使わずに main から `gdd-formal-gate-runner` を起動するときも、`run_in_background: true` で起動し、続けて `sleep 3660` の timer を置く（同期で起動すると deny される）
- background の dispatch を待つときは `<gdd-stop>` を書かずに turn を終える。動いている間に `blocked`・`cancelled`・`done` などで止まるなら、先に `TaskStop` で止める
- 継続契約の本文は `/gdd-dev` の開始時に書かれるので、この版の前から動いている `/gdd-dev` には待ちの規定が届かない。開き直す

#### Validation / Eval Impact

- `tests/test_background_dispatch_gate.py` を足した（判定の単体、入口からの deny と通すもの、読めない payload の記録、hooks.json への登録、規定の timer の秒数）
- `tests/test_wait_watchdog.py` に、background の dispatch の実行中に state を消す停止を、本文・tool result の marker・ポーリング上限の昇格・done のそれぞれで入口から押し返し、state が残ることと、host が動いていないと答えた `TaskStop` の後・連続 block の上限・peer のターン・判定の例外では通すことを足した
- `bash tests/validate-plugin.sh`
