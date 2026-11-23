---
type: minor
---

#### Summary

実装の worker subagent を、task の複雑度で 3 つの agent 定義から選ぶようにした。これまでは model をその場で決めていて、effort は agent 定義が無いため main から継承されていた（`Agent` ツールは effort を引数で受けない）。

task-breakdown が各 task に `Complexity: standard | complex` を書き（Express の最小構成の tasklist にも書く）、`gdd-subagent-driven-implementation` の controller は worker を次のように選ぶ。

- `Gate Rounds` が 2 以上: `gdd-remediation-worker`（`opus` + `effort=max`。`remediation_loop` tier）
- `Complexity: standard`: `gdd-implementation-worker`（`sonnet` + `effort=medium`）
- それ以外（`complex`・未宣言・ほかの値）: `gdd-implementation-worker-heavy`（`opus` + `effort=high`。`general_heavy_risk` tier）

推論力の不足で `BLOCKED` になった worker は、1 段上の worker（standard → heavy → remediation）で再 dispatch する。`Gate Rounds` ≥ 2 の間は remediation worker より下げない。

`complex` の条件は、これまで risk として挙げていたもの（security-sensitive・large working-set・AC / scope / ownership が変わりうる・既存コードの読解が難しい）である。security-sensitive は `gdd-implementation-gating` Step 3 の security reviewer の適用条件（auth・secrets・untrusted input・shell/filesystem・permissions・LLM 呼び出し・エージェント実装）に揃えた。

呼び出し側は `Agent(model=...)` を省略し、model と effort は agent 定義の frontmatter に任せる。`## Worktree` に加えて `## Plugin Root` を渡し、worker は参照先をそこから読む。

Agent の model を検査する hook（`run-agent-dispatch-model-gate-hook.sh`）は、model を省略した型付きの agent を、agent 定義の model で工程に照らして判定する（opus の worker は免除と同じ結果になる。sonnet の worker を opus 必須の工程で起動すると警告する）。実装の工程で model 未指定の起動には、`model="sonnet"` の明示ではなく、3 つの worker を model 省略で使うよう案内する。main session で inline に実装するときは、これまでどおり main の model で動く。

worker の `tools:` は runner と同じ共通の許可リスト（Read・Grep・Glob・Bash・Edit・Write・Monitor・TaskStop）で、これまでの `general-purpose` の worker と違い、WebFetch・WebSearch・MCP・Skill を持たない。

#### Added

- `agents/` に `gdd-implementation-worker`・`gdd-implementation-worker-heavy`・`gdd-remediation-worker` を追加（本文は共通）

#### Changed

- `hooks/scripts/lib/agent_dispatch_gate.py` に、agent 定義で固定した model の表 `FIXED_MODEL_BY_SUBAGENT_TYPE` と `fixed_model()` を追加し、3 つの worker を足した。model 省略時の免除は opus に固定した agent だけにした
- `hooks/scripts/run-agent-dispatch-model-gate-hook.sh` で、model 省略の起動を agent 定義の model で判定し、実装の工程の案内を変えた
- `skills/gdd-task-breakdown/SKILL.md` と `references/task-breakdown-steps.md` の task の雛形に `Complexity:` を追加
- `skills/gdd-subagent-driven-implementation/SKILL.md` の手順 2a・3 で、worker の `subagent_type` を `Complexity:` と `Gate Rounds` で選ぶ。§ Implementer Status Handling の `BLOCKED` の再 dispatch は 1 段上の worker にする。§ Fixed Model に worker ごとの model・effort を書いた
- `references/task-breakdown-steps.md` § Task Self-Review で、`Complexity:` が `standard` か `complex` のどちらか 1 つかを確かめる
- `references/phase-progression.md` § Express と `skills/gdd-test-driven-development/SKILL.md` の最小構成の tasklist に `Complexity:` を足した
- `references/fixed-models.md` の `implementation` tier の段落を選び方の正本にし、`skills/gdd-model-routing/SKILL.md`・`skills/gdd-implementation-gating/SKILL.md`・`references/subagent-dispatch.md`・`commands/gdd-dev.md` の「risk 時」と remediation worker の起動の記述を揃えた。README と CONTRIBUTING の `agents/` の説明に worker を足した

#### Affected Files

- `plugins/gate-driven-development/agents/gdd-implementation-worker.md`
- `plugins/gate-driven-development/agents/gdd-implementation-worker-heavy.md`
- `plugins/gate-driven-development/agents/gdd-remediation-worker.md`
- `plugins/gate-driven-development/skills/gdd-task-breakdown/SKILL.md`
- `plugins/gate-driven-development/skills/gdd-subagent-driven-implementation/SKILL.md`
- `plugins/gate-driven-development/skills/gdd-model-routing/SKILL.md`
- `plugins/gate-driven-development/skills/gdd-implementation-gating/SKILL.md`
- `plugins/gate-driven-development/hooks/scripts/lib/agent_dispatch_gate.py`
- `plugins/gate-driven-development/hooks/scripts/run-agent-dispatch-model-gate-hook.sh`
- `plugins/gate-driven-development/references/phase-progression.md`
- `plugins/gate-driven-development/skills/gdd-test-driven-development/SKILL.md`
- `plugins/gate-driven-development/README.md`
- `plugins/gate-driven-development/CONTRIBUTING.md`
- `plugins/gate-driven-development/references/fixed-models.md`
- `plugins/gate-driven-development/references/subagent-dispatch.md`
- `plugins/gate-driven-development/references/task-breakdown-steps.md`
- `plugins/gate-driven-development/commands/gdd-dev.md`
- `plugins/gate-driven-development/tests/test_implementation_worker_agents.py`
- `plugins/gate-driven-development/tests/test_agent_tool_allowlist_contract.py`
- `plugins/gate-driven-development/tests/checks/agent-effort-schema.sh`

#### User Action Required

- 新しい agent 定義はセッションの開始時にしか読み込まれない。長く動いているセッションは開き直す（見つからないときは、1 回だけ `general-purpose` を agent 定義と同じ model を明示して起動し直す。effort は main から継承される）
- すでに tasklist.md がある steering には `Complexity:` が無いので、worker は heavy（`opus` + `effort=high`。`Gate Rounds` ≥ 2 なら remediation worker）で動く

#### Validation / Eval Impact

- `tests/test_implementation_worker_agents.py` を追加した。3 つの worker の frontmatter の model・effort を `scripts/resolve-gdd-model.py` の tier の値と突き合わせる。hook スクリプトに payload を流し、実装の工程で model を省略した worker の起動に警告が出ないこと、sonnet の worker を opus 必須の工程で起動すると警告が出ること、`general-purpose` には worker を案内することを固定する。`references/fixed-models.md` と手順 3 に書いた worker 名を agent 定義と突き合わせる
- `tests/test_agent_tool_allowlist_contract.py` と `tests/checks/agent-effort-schema.sh` に 3 つの worker を足した
