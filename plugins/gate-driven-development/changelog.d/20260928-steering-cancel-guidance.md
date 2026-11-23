---
type: patch
---

#### Summary

検査する steering を 1 件に決められないとき（pre-push gate の `steering-multiple`、pre-PR gate と SessionStart の複数 steering）の直し方の案内を、「使わない steering を削除せず別の場所へ移す」から「使わない steering（PR が open のものは除く）は、削除も移動もせず、`state.md` の `Resume From` と `Next Action` をどちらも `cancelled` にする」に変えた。どれを終えるかはユーザーに確認するよう添える。移す案内には次の穴があった。

- PR が open の steering を移すと、所有する marker が無い merge で、その PR が merge gate の PR URL 照合から外れて検査されずに通る
- `.steering/` の外へ移すと git の管理外に落ち、全量 commit で PR に混入しうる

`cancelled` は pre-push・pre-PR・SessionStart の steering 検出の候補から外れ、merge gate の PR URL 照合には残る。片方の field だけでは pre-push が done・blocked を拾い続けるので、両方を書く。PR が open の steering しか外せないときは、先にその PR を merge するか、新しいタスクを別の worktree で進める。

steering を終える方法として `tasklist.md` の `Next Action=cancelled` や worktree の削除を案内していた文書と、brainstorming の archive 手順（リネームだけでは `state.md` が検出の深さに残る）も、同じ手順にそろえた。

#### Changed

- `hooks/scripts/run-session-start-hook.sh`・`hooks/scripts/run-pre-pr-gate-hook.sh`・`hooks/scripts/run-pre-push-gate-hook.sh`: 複数 steering の案内文（止める条件は変えていない）。pre-push は手順の参照先として `references/self-review-lanes.md` の「使わないステアリングの終え方」を示す
- `references/self-review-lanes.md`: § 使わないステアリングの終え方 を足した（手順の正本）
- `references/abandon-and-pause.md`・`references/state-machine.md`・`references/faq.md`・`docs/TROUBLESHOOTING.md`: steering を終える手順を `state.md` の両 field に直した（TROUBLESHOOTING の早見表と、stale steering の片付けを含む）。`abandon-and-pause.md` の「SessionStart hook が cancelled を検出し Cancelled Cleanup に誘導する」は実装が無いので外した
- `skills/gdd-brainstorming/SKILL.md`・`skills/gdd-pre-workflow-brainstorming/SKILL.md`・`references/skill-responsibility-matrix.md`: archive の手順に、リネームした steering の `state.md` を両 field とも `cancelled` にすることを足した

#### Affected Files

- `plugins/gate-driven-development/hooks/scripts/run-session-start-hook.sh`
- `plugins/gate-driven-development/hooks/scripts/run-pre-pr-gate-hook.sh`
- `plugins/gate-driven-development/hooks/scripts/run-pre-push-gate-hook.sh`
- `plugins/gate-driven-development/references/self-review-lanes.md`
- `plugins/gate-driven-development/references/abandon-and-pause.md`
- `plugins/gate-driven-development/references/state-machine.md`
- `plugins/gate-driven-development/references/faq.md`
- `plugins/gate-driven-development/references/skill-responsibility-matrix.md`
- `plugins/gate-driven-development/docs/TROUBLESHOOTING.md`
- `plugins/gate-driven-development/skills/gdd-brainstorming/SKILL.md`
- `plugins/gate-driven-development/skills/gdd-pre-workflow-brainstorming/SKILL.md`
- `plugins/gate-driven-development/tests/test_steering_cancel_guidance_contract.py`（新規）
- `plugins/gate-driven-development/tests/test_steering_terminal_pipe_head_contract.py`

#### User Action Required

- 同じ checkout に使わない steering が残って複数 steering で止まったら、どれを終えるかをユーザーに確認し、その steering の `state.md` で `Resume From` と `Next Action` をどちらも `cancelled` にする。PR が open の steering は対象にしない
- PR URL の無い cancelled の steering が残ると、所有する marker の無い merge で対象 PR を記録した steering が見つからないとき、merge gate が `pr-url-unrecorded` で止める。対象 PR の worktree から merge するか、kill-switch を使う

#### Validation / Eval Impact

- `tests/test_steering_cancel_guidance_contract.py`: 3 つの入口の案内文（ユーザーへの確認を含む）、案内どおりに片方を `cancelled` にすると pre-push・pre-PR・SessionStart の複数 steering が解けること、片方の field だけでは pre-push が解けないこと、`cancelled` にした steering も merge gate の PR URL 照合で検査されること
- `tests/test_steering_terminal_pipe_head_contract.py`: 案内文の期待を更新
- 変更したファイルを参照するテスト、`tests/checks/skill-body-budget.sh`、`bash plugins/gate-driven-development/tests/validate-plugin.sh`
