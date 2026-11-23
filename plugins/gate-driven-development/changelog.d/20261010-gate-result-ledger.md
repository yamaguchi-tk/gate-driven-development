---
type: patch
---

#### Summary

gate の phase（requirements-gating・design-gating・implementation-gating・completion-check）を実行した側（gate runner。inline 実行なら main。worker 経由なら結果を統合する main）が、Round ごとに `worklog.md` へ `gate結果: <phase> / Round <n> / 判定: … / 件数: high=<n> medium=<n> low=<n> blocking=<n>` の 1 行を追記するようにした。gate がどれだけ指摘を出したかを、後から steering の記録で数えられるようにする。routing と Round のカウンタは、この行を読まない。

#### Affected Files

- `plugins/gate-driven-development/references/subagent-dispatch.md`（§ Subagent Return Output Contract と、gate が reviewer を起動するときに読む § Reviewer Input and Time Budget）
- `plugins/gate-driven-development/agents/gdd-formal-gate-runner.md`（本文の一致を保つため `gdd-light-task-runner.md` にも同じ文）
- `plugins/gate-driven-development/skills/gdd-implementation-gating/SKILL.md`
- `plugins/gate-driven-development/skills/gdd-completion-check/SKILL.md`
- `plugins/gate-driven-development/references/requirements-gating-steps.md`（requirements の gate が読むレビューループの契約。design の gate には subagent-dispatch.md の時間上限の項から届く）

#### User Action Required

- なし

#### Validation / Eval Impact

- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
