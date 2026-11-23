---
type: minor
---

#### Summary

SessionStart hook の `[gdd:shadow-marker]`（現 worktree に有効な steering が無いとき、同じ repo の別 worktree や worktree の置き場にある非終端の steering を探し、`gdd-status` / `/gdd-dev resume <target>` を案内するもの）を撤去した。2026-09-17〜09-21 に 197 回注入され、その後に `gdd-status`・`/gdd-dev resume`・`gdd-resume` が起動された回数は 0 だった。指す先は放棄された古い steering だけだった。また、毎回すべての worktree と置き場を走査するため、worktree の多い repo（steering を持つ worktree 205 個）では走査だけで約 2.5 秒かかり、SessionStart の timeout（5 秒）で打ち切られる原因になっていた。

#### Removed

- SessionStart hook は、現 worktree の外（`git worktree list` の他の worktree、`~/.gdd/worktrees/<repo>`、`GDD_WORKTREES_ROOT`、`.gdd-config.md` の `Worktree Base:`、`<current>/.worktrees`）の steering の `state.md` を読まず、案内もしない（案内の文面を選ぶために、`git worktree list` の各 worktree に `.steering/` があるかだけは従来どおり見る）。有効な steering が無いときは、通常の案内（superpowers があれば `Routing reason: no active GDD marker detected ...`）だけを出す
- `gdd-status` skill の「Shadow Candidate Display」節（`[gdd:shadow-marker]` が出たときに候補を表示する手順）を削除した
- `docs/SUPERPOWERS_COEXISTENCE.md` の一時 workspace の節を、別 worktree の steering は案内しない（進めるときはユーザーが `/gdd-dev resume <target>` で対象を明示する）という記述に改めた

compact 自動復帰・Safe Resume・post-merge 継続・`[gdd:reboot]`・`[gdd:paused]`・複数 steering の警告（`[gdd:warning]`）の判定と出力は変えていない。

#### Affected Files

- `plugins/gate-driven-development/hooks/scripts/run-session-start-hook.sh`
- `plugins/gate-driven-development/skills/gdd-status/SKILL.md`
- `plugins/gate-driven-development/docs/SUPERPOWERS_COEXISTENCE.md`
- `plugins/gate-driven-development/evals/gdd-scenario-fixtures.json`（シナリオの前提文から shadow marker を外した）
- `plugins/gate-driven-development/tests/test_session_start_no_shadow_marker.py`（新規）
- `plugins/gate-driven-development/tests/test_session_start_shadow_marker_scope.py`（削除）
- `plugins/gate-driven-development/tests/test_session_start_context_json_control_chars.py`
- `plugins/gate-driven-development/tests/test_session_start_last_turn_failure_contract.py`
- `plugins/gate-driven-development/tests/test_superpowers_differentiation_contract.py`
- `plugins/gate-driven-development/tests/test_hook_injection_security_contract.py`（docstring の出力点の数を外した）

#### User Action Required

- なし。別 worktree の GDD task を再開したいときは、その worktree で `/gdd-dev resume <target>` を明示する（従来も shadow-marker は自動再開をしていない）
- plugin を更新すると、進行中のセッションでも次の SessionStart から案内が変わる

#### Validation / Eval Impact

- 新規 contract test: `tests/test_session_start_no_shadow_marker.py`（入口は SessionStart hook の実行。別の git worktree・`~/.gdd/worktrees/<repo>`・`<current>/.worktrees`・`.gdd-config.md` の `Worktree Base:`・`GDD_WORKTREES_ROOT` のどこに非終端の steering があっても、`[gdd:shadow-marker]` も steering のパスも `/gdd-dev resume` も出ず、通常の案内が出る。superpowers があるときは通常の `Routing reason` が出る）
- SessionStart の出力点が 7 から 6 になり、`test_every_shipped_output_point_is_wired` の期待値を 6 にした
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
