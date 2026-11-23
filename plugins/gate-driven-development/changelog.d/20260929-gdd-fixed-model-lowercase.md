---
type: patch
---

#### Summary

skill の `## Fixed Model` 節などで、Claude Code の起動モデルを大文字の `Sonnet`・`Opus` と書いていた箇所を、tier 表と同じ小文字の alias（`sonnet`・`opus`）に揃えた。`gdd-requesting-code-review` の Claude Code のモデルを、resolver と `gdd-model-routing` の表に合わせて general_heavy tier（`opus` + `effort=high`）にした。

#### Changed

- 13 本の skill の `## Fixed Model` 節の `Sonnet` を `sonnet` にした
- `skills/gdd-model-routing` の Claude Code のモデル使い分けと既定の節、`skills/gdd-pr-review`、`references/fixed-models.md` の `implementation` tier の説明、`references/phase-gate-prechecks.md` の Model Tier の照合で、Claude Code のモデルを小文字の alias にした。Cursor のモデル名の `Opus` は変えていない
- `skills/gdd-requesting-code-review` の Claude Code のモデルを `sonnet` + `effort=medium` から `opus` + `effort=high` にした。これまでは dispatcher として軽いモデルを既定にしていたが、resolver（`scripts/resolve-gdd-model.py`）と Cursor・Codex の列は general_heavy tier だった

#### Affected Files

- `plugins/gate-driven-development/skills/gdd-ac-verification/SKILL.md`
- `plugins/gate-driven-development/skills/gdd-metrics/SKILL.md`
- `plugins/gate-driven-development/skills/gdd-model-routing/SKILL.md`
- `plugins/gate-driven-development/skills/gdd-next-plan/SKILL.md`
- `plugins/gate-driven-development/skills/gdd-pr-review/SKILL.md`
- `plugins/gate-driven-development/skills/gdd-pr-review-followup/SKILL.md`
- `plugins/gate-driven-development/skills/gdd-pre-workflow-brainstorming/SKILL.md`
- `plugins/gate-driven-development/skills/gdd-receiving-code-review/SKILL.md`
- `plugins/gate-driven-development/skills/gdd-requesting-code-review/SKILL.md`
- `plugins/gate-driven-development/skills/gdd-status/SKILL.md`
- `plugins/gate-driven-development/skills/gdd-subagent-driven-implementation/SKILL.md`
- `plugins/gate-driven-development/skills/gdd-task-breakdown/SKILL.md`
- `plugins/gate-driven-development/skills/gdd-test-driven-development/SKILL.md`
- `plugins/gate-driven-development/skills/gdd-test-failure-debug-pack/SKILL.md`
- `plugins/gate-driven-development/skills/gdd-using-git-worktrees/SKILL.md`
- `plugins/gate-driven-development/references/fixed-models.md`
- `plugins/gate-driven-development/references/phase-gate-prechecks.md`

#### User Action Required

- なし。`gdd-requesting-code-review` を Claude Code で起動するときは、`opus` + `effort=high` を使う

#### Validation / Eval Impact

- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
