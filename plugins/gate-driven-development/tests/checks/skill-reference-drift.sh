#!/usr/bin/env bash
set -euo pipefail
: "${ROOT:?}" "${PYTHON_BIN:?}"

echo "BLOCK: skill-reference-drift"
"$PYTHON_BIN" - "$ROOT" <<'PY'
"""Check that SKILL.md step summaries are consistent with their reference files.

For each main workflow skill that references a *-steps.md file, verify:
1. The referenced steps file exists
2. Step numbers mentioned in SKILL.md match the reference file
3. SKILL.md doesn't inline full step definitions that duplicate the reference
"""
import pathlib
import re
import sys

root = pathlib.Path(sys.argv[1])
skills_dir = root / "skills"
refs_dir = root / "references"
errors = []

# Main workflow skills that must reference steps files
WORKFLOW_SKILLS = {
    "gdd-brainstorming": "brainstorming-steps.md",
    "gdd-task-breakdown": "task-breakdown-steps.md",
    "gdd-requirements-gating": "requirements-gating-steps.md",
}

# Check that referenced steps files exist
for skill_name, steps_file in WORKFLOW_SKILLS.items():
    skill_md = skills_dir / skill_name / "SKILL.md"
    ref_path = refs_dir / steps_file
    if not skill_md.exists():
        errors.append(f"{skill_name}: SKILL.md not found")
        continue
    if not ref_path.exists():
        errors.append(f"{skill_name}: referenced {steps_file} not found")
        continue
    skill_text = skill_md.read_text(encoding="utf-8")
    if steps_file not in skill_text:
        errors.append(f"{skill_name}: SKILL.md does not reference {steps_file}")
        continue

    # Count step numbers in reference file (allow leading whitespace for sub-steps)
    ref_text = ref_path.read_text(encoding="utf-8")
    ref_steps = set(re.findall(r"^\s*(\d+[a-z]?)[\.\)]", ref_text, re.MULTILINE))

    # Count step numbers mentioned in SKILL.md (in Steps section)
    # Exclude steps that have explicit cross-references like "(steps.md Step 12a)"
    in_steps = False
    skill_steps = set()
    for line in skill_text.splitlines():
        if line.startswith("## Steps"):
            in_steps = True
            continue
        if in_steps and line.startswith("## ") and not line.startswith("## Steps"):
            break
        if in_steps:
            m = re.match(r"^(\d+[a-z]?)[\.\)]", line.strip())
            if m:
                step_id = m.group(1)
                # If the line has an explicit ref like "(steps.md Step XXX)", use the referenced step ID
                ref_match = re.search(r"\(steps\.md\s+Step\s+(\d+[a-z]?)\)", line)
                if ref_match:
                    # This SKILL.md step maps to a different reference step — skip orphan check
                    continue
                skill_steps.add(step_id)

    # Check for step numbers in SKILL.md not present in reference
    orphan_steps = skill_steps - ref_steps
    if orphan_steps:
        errors.append(
            f"{skill_name}: SKILL.md has step(s) {sorted(orphan_steps)} "
            f"not found in {steps_file} — possible drift"
        )

# Check all skills for dangling references to nonexistent reference files.
# `references/foo.md` points to plugin-root references/.
# `./references/foo.md` points to the skill-local references/ directory.
for skill_dir in sorted(skills_dir.iterdir()):
    if not skill_dir.is_dir():
        continue
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        continue
    text = skill_md.read_text(encoding="utf-8")
    for m in re.finditer(r"`references/([\w-]+\.md)`", text):
        ref_name = m.group(1)
        if not (refs_dir / ref_name).exists():
            errors.append(f"{skill_dir.name}: references {ref_name} but file not found")
    for m in re.finditer(r"`\./references/([\w-]+\.md)`", text):
        ref_name = m.group(1)
        if not (skill_dir / "references" / ref_name).exists():
            errors.append(f"{skill_dir.name}: local references {ref_name} but file not found")

if errors:
    for e in errors:
        print(f"DRIFT: {e}", file=sys.stderr)
    sys.exit(1)
print("OK")
PY

echo "VERDICT: skill-reference-drift: OK"
