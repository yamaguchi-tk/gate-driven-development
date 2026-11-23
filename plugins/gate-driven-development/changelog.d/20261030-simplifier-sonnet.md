---
type: patch
---

#### Summary

簡素化パスの agent（`gdd-code-simplifier`）を、Opus から Sonnet（effort は medium のまま）に下げた。直近 30 日の 39 本の実測で費用は GDD の agent 全体の 0.09% と小さく、Sonnet で 1 本あたり約 0.4 倍になる（alias `sonnet` が最新の Sonnet に解決されるとき）。過去の 8 件の当て直しでは、振る舞いを変えた差分は Opus・Sonnet とも 0 件で、採点は Opus 58・Sonnet 54（64 点満点）だった。

#### Changed

- `agents/gdd-code-simplifier.md` の `model` を `sonnet` にした
- dispatch model gate（`hooks/scripts/lib/agent_dispatch_gate.py`）の固定 model の表も `sonnet` にした。実装の工程から model を省略して起動すると黙り、opus 必須の工程から起動すると警告する。model を明示した起動は、定義の model を上書きするという警告（overrides_fixed）ではなく、工程の model の判定で警告するようになった
- `references/fixed-models.md` に簡素化パスの段落を足した

#### Affected Files

- `plugins/gate-driven-development/agents/gdd-code-simplifier.md`
- `plugins/gate-driven-development/hooks/scripts/lib/agent_dispatch_gate.py`
- `plugins/gate-driven-development/references/fixed-models.md`
- `plugins/gate-driven-development/tests/test_implementation_worker_agents.py`

#### User Action Required

- なし

#### Validation / Eval Impact

- `python3 -m pytest plugins/gate-driven-development/tests/test_implementation_worker_agents.py plugins/gate-driven-development/tests/test_agent_dispatch_model_gate_contract.py`
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
