---
type: patch
---

#### Summary

実装の worker 3 つ（`gdd-implementation-worker`・`-heavy`・`gdd-remediation-worker`）、簡素化パス（`gdd-code-simplifier`）、マージ後の QA（`gdd-qa-runner`）の定義に、advisor ツールを呼ばない規定を足した。これで、定義を持つ GDD の agent はすべて、advisor ツールを呼ばないよう定義に書いた（散文の指示で、仕組みでは止めない。定義を持たない `Plan`・`Explore`・`general-purpose` の起動は含まない）。公式の資料では、Opus（high）に Fable の advisor を付けた構成は、単独より 1.7 点（ぶれの境目）上がり、費用は約 2.1 倍だった。GDD の実測では、advisor が heavy の費用の約 36% を占めていた。

#### Changed

- 実装の worker 3 つ：「実装の後の最後の確認では呼ばない」を「呼ばない」にした
- `gdd-code-simplifier`・`gdd-qa-runner`：「advisor ツールを呼ばない」を足した

#### Affected Files

- `plugins/gate-driven-development/agents/gdd-implementation-worker.md`
- `plugins/gate-driven-development/agents/gdd-implementation-worker-heavy.md`
- `plugins/gate-driven-development/agents/gdd-remediation-worker.md`
- `plugins/gate-driven-development/agents/gdd-code-simplifier.md`
- `plugins/gate-driven-development/agents/gdd-qa-runner.md`

#### User Action Required

- なし。main セッションの advisor は、利用者の設定（`/advisor`）のままで、この変更では変わらない。plugin を更新する前から動いているセッションは、開き直すまで古い定義で動く

#### Validation / Eval Impact

- `python3 -m pytest plugins/gate-driven-development/tests/test_implementation_worker_agents.py`（3 つの worker の本文が同じであることを固定する）
- advisor を agent ごとに切る設定が無いことは、Claude Code の advisor の資料（https://code.claude.com/docs/en/advisor 。subagent は設定した advisor を受け継ぐ、切るのは `/advisor off` か `CLAUDE_CODE_DISABLE_ADVISOR_TOOL=1` で、どちらもセッション全体）で確かめた（2026-10-30）
- 効いたかは、マージ後の次の週次分析で、subagent の transcript の usage の `iterations` に `advisor_message` が出た回数を、この 5 つの agent ごとに数えて確かめる（0 回が目標）
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
