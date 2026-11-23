---
type: minor
---

#### Summary

brainstorming（quick (standard)・standard。Direct Intent で Problem Discovery を縮めたときも含む）で、requirements.md を書く前に、依頼の原文と既存コードを突き合わせるようにした。ユーザーの発言を言い換えずに `.steering/<task>/request.md` に写し、新しい agent `gdd-request-code-crosscheck`（Opus・high、read-only）が、依頼の語ごとに「既存で満たす／足せば満たす／既存とぶつかる／原文だけでは決まらない」を判定する。出力は `request-crosscheck.md` に置き、`既存とぶつかる` の上位 3 件を human check の § ズレ確認 に載せる（`Human Check Questions` の 2 個の上限には数えない）。`原文だけでは決まらない` を AI が仮決定したときは、仮決定を AC 本文と「完了条件の変換」表に書く。requirements-gating は、2 つのファイルがあることを blocking で確かめる。express から昇格したタスクは、昇格のときに行う。trivial と quick (express) は対象外。

#### Affected Files

- `plugins/gate-driven-development/agents/gdd-request-code-crosscheck.md`
- `plugins/gate-driven-development/hooks/scripts/lib/agent_dispatch_gate.py`
- `plugins/gate-driven-development/references/brainstorming-steps.md`
- `plugins/gate-driven-development/references/human-check-template.md`
- `plugins/gate-driven-development/references/human-check-template-compact.md`
- `plugins/gate-driven-development/references/task-sizing.md`
- `plugins/gate-driven-development/references/fixed-models.md`
- `plugins/gate-driven-development/skills/gdd-brainstorming/SKILL.md`
- `plugins/gate-driven-development/skills/gdd-requirements-gating/SKILL.md`
- `plugins/gate-driven-development/README.md`
- `plugins/gate-driven-development/tests/test_request_crosscheck_agent.py`
- `plugins/gate-driven-development/tests/test_agent_tool_allowlist_contract.py`
- `plugins/gate-driven-development/tests/checks/agent-effort-schema.sh`

#### User Action Required

- なし

#### Validation / Eval Impact

- 足したテスト: `tests/test_request_crosscheck_agent.py`（agent の model・effort・tools の固定と、dispatch の gate が model 省略の起動を警告せず、model を下げた起動は警告すること）
- `python3 -m pytest` で上の Affected Files のテスト 2 本と、`agent_dispatch_gate` を参照するテスト
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
