---
type: minor
---

#### Summary

独立レビュー用の agent 定義 `agents/gdd-independent-reviewer.md`（Opus・`effort: xhigh`・Read / Grep / Glob）を足した。Claude Code では `references/independent-review.md` の契約 4 のとおり、この定義で起動し `model` を渡さない。これまで独立レビューは effort を固定する定義が無く、main の effort を継承して動いていた。この定義で起動すると、`independent_review` tier の effort（`xhigh`）で動く。main が `xhigh` より低い effort のときは、独立レビューの時間と費用が増える。

#### Affected Files

- `plugins/gate-driven-development/agents/gdd-independent-reviewer.md`
- `plugins/gate-driven-development/references/independent-review.md`
- `plugins/gate-driven-development/references/fixed-models.md`
- `plugins/gate-driven-development/hooks/scripts/lib/agent_dispatch_gate.py`
- `plugins/gate-driven-development/tests/checks/agent-effort-schema.sh`
- `plugins/gate-driven-development/tests/test_independent_review_host_route_contract.py`
- `plugins/gate-driven-development/tests/test_agent_tool_allowlist_contract.py`

#### User Action Required

- 定義はセッションの開始時に読み込まれる。動いているセッションでは、開き直すまでこの定義を使えない

#### Validation / Eval Impact

- `python3 -m pytest plugins/gate-driven-development/tests/test_independent_review_host_route_contract.py plugins/gate-driven-development/tests/test_agent_tool_allowlist_contract.py -q`（定義の model・effort が resolver の値と、Agent の model を検査する hook の固定 model と一致し、tool が read-only であることを固定する）
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
