---
type: patch
---

#### Summary

dispatch model gate は、`model: opus` に固定した agent（reviewer・相談役・worker など）に opus 以外の `model` を明示した起動を、工程の tier が sonnet でも警告するようにした。警告は、工程の model に変えるのではなく `model` を省略するよう案内する。これまでは sonnet の工程（task-breakdown・TDD・subagent-driven-implementation）で `model: sonnet` を明示して下げても警告せず、opus の工程では `model="opus"` の明示を勧めていた。

あわせて、自律モードの手順 3 の Fable を代わりの経路で起動したときの、effort の継承の書き方を `references/autonomy.md` の手順 5 に決めた。

#### Affected Files

- `plugins/gate-driven-development/hooks/scripts/lib/agent_dispatch_gate.py`
- `plugins/gate-driven-development/hooks/scripts/run-agent-dispatch-model-gate-hook.sh`
- `plugins/gate-driven-development/references/autonomy.md`
- `plugins/gate-driven-development/references/fixed-models.md`
- `plugins/gate-driven-development/tests/test_advisor_agents.py`
- `plugins/gate-driven-development/tests/test_agent_dispatch_model_gate_contract.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- `tests/test_advisor_agents.py` に、sonnet の工程で opus 固定の agent を下げた起動の警告と、opus を明示した起動が黙ることのテストを足した
- `bash tests/validate-plugin.sh`
