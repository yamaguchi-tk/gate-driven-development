---
type: patch
---

#### Summary

- 自律継続の loop の prompt は、止まってよい条件に、ほかの reason の用途に当たるとき（`external-review-waiting` など）を足した。`blocked` の指示は、`auth-waiting` などの用途に当たるときを除く。Codex の Goal は、`done` 以外のどの reason でも完了にしない。起動時の表示は、止まる条件を Stop hook の判定（`references/state-machine.md`）で示す
- 記録の場所の無い規則・方針の `既存とぶつかる` は、「推奨で進めて」と任されたときも依頼の原文どおりの側に仮決定する。fetch できない、または `origin/<既定のブランチ>` を解決できないときは、`CLAUDE.md`・`AGENTS.md` の行を記録の場所に数えない。`記録の場所: なし` は、requirements の reviewer が記録の場所を添えた仮決定に数えない
- `記録の場所: なし` の行を本人に届ける手順を、`references/post-completion-pr-flow.md` の Step 4（`done` の直前の発言。completion-check を subagent で回したときは main の完了サマリー）と、PR 本文の Autonomy Decisions Check にまとめた
- brainstorming の fail-closed の停止は、`<gdd-stop reason="blocked">` に `## 👤 次にすること` を付ける。state.md を作る前の停止の例外に、この停止を足した
- compact 503 のとき進めない先を、loop state を消す停止と書いた。自然文から推定しないのは停止の reason だと書き、scenario eval の fixture をその文に合わせた

#### Affected Files

- `agents/gdd-planning-reviewer.md`・`commands/gdd-dev.md`・`evals/gdd-scenario-fixtures.json`・`references/brainstorming-steps.md`・`references/common-guardrails.md`・`references/context-budget.md`・`references/gate-status-schema.md`・`references/human-check-template.md`・`references/output-format.md`・`references/post-completion-pr-flow.md`・`references/requirements-gating-steps.md`・`references/state-machine.md`・`references/stop-hook-structured-markers.md`・`references/subagent-dispatch.md`・`scripts/setup-gdd-loop.sh`・`skills/gdd-brainstorming/SKILL.md`・`skills/gdd-status/SKILL.md`

#### User Action Required

- なし

#### Validation / Eval Impact

- `python3 scripts/light-lane-related-tests.py --run . origin/main`・`bash plugins/gate-driven-development/tests/validate-plugin.sh`
