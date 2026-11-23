---
type: patch
---

#### Summary

`remediation_loop` tier（同じ task で `changes_requested` が 2 回目になった後の route 判断・再レビュー・修正）の Claude Code の effort を `max` から `xhigh` に下げた。`gdd-remediation-worker` の定義の effort も `xhigh` になる。max の worker は 1 本の中央値が約 26 分・約 $7.5 かかっていたため。過去の worker 4 件の当て直しでは、max が後の gate の指摘を先に避けた分だけ点が高かったが、往復は減らしていなかった。

#### Changed

- `agents/gdd-remediation-worker.md`：`effort: max` → `effort: xhigh`
- `scripts/resolve-gdd-model.py`：Claude Code の `remediation_loop` の effort を `xhigh` に
- `references/fixed-models.md`・`skills/gdd-model-routing`・`skills/gdd-systematic-debugging`・`skills/gdd-subagent-driven-implementation`：`remediation_loop` の effort の記述を `xhigh` に合わせ、下げた理由を書いた

#### Affected Files

- `plugins/gate-driven-development/agents/gdd-remediation-worker.md`
- `plugins/gate-driven-development/scripts/resolve-gdd-model.py`
- `plugins/gate-driven-development/references/fixed-models.md`
- `plugins/gate-driven-development/skills/gdd-model-routing/SKILL.md`
- `plugins/gate-driven-development/skills/gdd-systematic-debugging/SKILL.md`
- `plugins/gate-driven-development/skills/gdd-subagent-driven-implementation/SKILL.md`
- `plugins/gate-driven-development/tests/checks/agent-effort-schema.sh`
- `plugins/gate-driven-development/tests/test_remediation_loop_model_routing_contract.py`

#### User Action Required

- なし。CLI を更新しなくても、plugin を更新した後に始めたセッションから効く。Cursor・Codex の写像（`reasoning.effort=high`）は変わらない

#### Validation / Eval Impact

- `tests/checks/agent-effort-schema.sh`
- `tests/test_remediation_loop_model_routing_contract.py`・`tests/test_implementation_worker_agents.py`
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
