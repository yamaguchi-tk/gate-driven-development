#!/usr/bin/env bash
set -euo pipefail
: "${ROOT:?}" "${PYTHON_BIN:?}"

echo "BLOCK: express-promotion-transition"
"$PYTHON_BIN" - "$ROOT" <<'PY'
"""Verify Express → standard promotion transition rules are consistent.

Checks:
1. state-machine.md rollback table has all required fields
2. task-sizing.md promotion steps match state-machine.md
3. phase-progression.md promotion steps match state-machine.md
4. Phase Gate Pre-check in build skills accepts the post-promotion state
"""
import pathlib
import re
import sys

root = pathlib.Path(sys.argv[1])
errors = []

# 1. Check state-machine.md has Express promotion rollback table
sm = (root / "references" / "state-machine.md").read_text(encoding="utf-8")
if "Express 昇格時の state ロールバック規則" not in sm:
    errors.append("state-machine.md: Express promotion rollback section missing")
else:
    # Required fields in rollback table
    required_fields = [
        "Task Size",
        "Requirements Review Status",
        "Design Review Status",
        "Human Check Status",
        "Resume From",
        "Approved Direction",
        "Planning Reviewer Selection",
        "Implementation Reviewer Selection",
    ]
    for field in required_fields:
        if field not in sm.split("Express 昇格時の state ロールバック規則")[1].split("##")[0]:
            errors.append(f"state-machine.md: rollback table missing field '{field}'")

# 2. Check task-sizing.md has promotion steps
ts = (root / "references" / "task-sizing.md").read_text(encoding="utf-8")
if "Express 昇格条件" not in ts:
    errors.append("task-sizing.md: Express promotion section missing")
else:
    promotion_section = ts.split("Express 昇格条件")[1].split("##")[0]
    # Must mention key state changes
    for key in ["Requirements Review Status=pending", "Design Review Status=pending",
                 "Human Check Status", "Planning Reviewer Selection", "Implementation Reviewer Selection"]:
        if key not in promotion_section:
            errors.append(f"task-sizing.md: promotion steps missing '{key}'")

# 3. Check phase-progression.md has matching promotion rules
pp = (root / "references" / "phase-progression.md").read_text(encoding="utf-8")
if "Express → standard 昇格" not in pp:
    errors.append("phase-progression.md: Express promotion section missing")
else:
    pp_section = pp.split("Express → standard 昇格")[1].split("##")[0]
    for key in ["Requirements Review Status=pending", "Design Review Status=pending",
                 "Planning Reviewer Selection=pending", "Implementation Reviewer Selection"]:
        if key not in pp_section:
            errors.append(f"phase-progression.md: promotion section missing '{key}'")

# 4. Verify post-promotion state passes Phase Gate Pre-check logic
# After promotion: Req=pending, Design=pending, Human=approved, Resume=gdd-requirements-gating
# requirements-gating should accept this (it checks Req status internally, not as pre-check)
# task-breakdown Pre-check requires all 3 approved — so it should NOT be reachable until gates pass
# This is correct: promotion sets Resume=gdd-requirements-gating, which goes through gates first

# Check that task-breakdown's Pre-check explicitly blocks Express
tb_skill = (root / "skills" / "gdd-task-breakdown" / "SKILL.md").read_text(encoding="utf-8")
if "Express パスではこの skill に到達しない" not in tb_skill:
    tb_sections = tb_skill.split("Phase Gate Pre-check")
    if len(tb_sections) < 2:
        errors.append("gdd-task-breakdown: 'Phase Gate Pre-check' heading not found (SKILL.md may have been restructured)")
    elif "Express" not in tb_sections[1].split("##")[0]:
        errors.append("gdd-task-breakdown: Phase Gate Pre-check should block Express path")

if errors:
    for e in errors:
        print(f"EXPRESS-PROMO: {e}", file=sys.stderr)
    sys.exit(1)
print("OK")
PY

echo "VERDICT: express-promotion-transition: OK"
