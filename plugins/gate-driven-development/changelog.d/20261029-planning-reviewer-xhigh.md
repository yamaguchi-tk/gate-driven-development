---
type: patch
---

#### Summary

requirements・design gate の reviewer `gdd-planning-reviewer` の effort を `max` から `xhigh` に下げた。過去の設計成果物（正解 12 件）に当て直すと、xhigh は 2 回で 7.5 件・10.5 件、max は 1 回で 9.5 件を当て、1 回の費用と時間は xhigh が max の半分以下だった。model（Opus）と観点レーンは変わらない。

#### Affected Files

- `plugins/gate-driven-development/agents/gdd-planning-reviewer.md`
- `plugins/gate-driven-development/references/fixed-models.md`
- `plugins/gate-driven-development/skills/gdd-model-routing/SKILL.md`
- `plugins/gate-driven-development/tests/checks/agent-effort-schema.sh`

#### User Action Required

- なし

#### Validation / Eval Impact

- `bash plugins/gate-driven-development/tests/validate-plugin.sh`（`agent-effort-schema` が定義の effort を固定する）
