---
type: patch
---

#### Summary

- learned-patterns.md を読む側を、書く側（completion-check）と同じ worktree 直下の `docs/learned-patterns.md`（正本: `references/cross-task-learning.md`）に揃えた。implementation-gating の Step 5 と `scripts/impl-gate-context.py`、subagent-driven-implementation、`scripts/collect-gdd-telemetry.py` と gdd-metrics の AI で集計する手順は、これまで `.steering/` の中を探していて、書いた記録を読めていなかった
- implementation-gating Step 5 の Reviewer Calibration（false positive が記録された checklist 項目の finding の severity を 1 段階下げる）は、`docs/learned-patterns.md` の `Rejected Alternatives` に記録がある repo で、実際に効くようになる。下げたときは evidence に `calibration: learned-patterns` を付ける規定は変えていない
- telemetry の `learned_patterns_entries` は、`docs/learned-patterns.md` の箇条の数になる（これまでは `.steering/learned-patterns.md` を数えていて、多くは 0）
- `docs/SECURITY.md` の、skill が `.steering/<task>/learned-patterns.md` に書く、SessionStart hook が learned-patterns.md を読む、という記述を実物に合わせて直した（hook は読んでいない）

#### Affected Files

- `scripts/impl-gate-context.py`
- `scripts/collect-gdd-telemetry.py`
- `skills/gdd-implementation-gating/SKILL.md`（Step 5）
- `skills/gdd-subagent-driven-implementation/SKILL.md`（Step 1a、観察 concern）
- `skills/gdd-metrics/SKILL.md`（AI dispatch の手順 2）
- `references/cross-task-learning.md`（参照元・読み取りタイミング）
- `docs/SECURITY.md`

#### User Action Required

なし。learned-patterns を `.steering/` の中に置いていた repo は、`docs/learned-patterns.md` へ移す（書く側は以前から `docs/` に書いている）

#### Validation / Eval Impact

- `tests/test_learned_patterns_location.py`（新規）
- `tests/test_impl_gate_context.py`（fixture の置き場）
- `bash plugins/gate-driven-development/tests/validate-plugin.sh`
