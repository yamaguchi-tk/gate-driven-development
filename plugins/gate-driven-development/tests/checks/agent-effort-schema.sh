#!/usr/bin/env bash
set -euo pipefail
: "${ROOT:?}" "${PYTHON_BIN:?}"

echo "BLOCK: agent-effort-schema"
"$PYTHON_BIN" - "$ROOT" <<'PYEOF'
import sys
from pathlib import Path

root = Path(sys.argv[1])
agents_dir = root / "agents"

EXPECTED = {
    "gdd-planning-reviewer.md": "xhigh",
    "gdd-implementation-reviewer.md": "high",
    "gdd-security-reviewer.md": "high",
    "gdd-completion-reviewer.md": "high",
    "gdd-code-simplifier.md": "medium",
    "gdd-formal-gate-runner.md": "high",
    "gdd-light-task-runner.md": "medium",
    "gdd-implementation-worker.md": "medium",
    "gdd-implementation-worker-heavy.md": "high",
    "gdd-remediation-worker.md": "xhigh",
    "gdd-qa-runner.md": "high",
    "gdd-opus-advisor.md": "high",
    "gdd-opus-advisor-max.md": "max",
    "gdd-fable-advisor.md": "medium",
    "gdd-request-code-crosscheck.md": "high",
    "gdd-finding-verifier.md": "high",
    "gdd-requirements-precheck.md": "high",
    "gdd-independent-reviewer.md": "xhigh",
}


def parse_frontmatter(path: Path) -> dict:
    content = path.read_text(encoding="utf-8")
    if not content.startswith("---\n"):
        raise SystemExit(f"FAIL: {path.name} has no frontmatter")
    end = content.find("\n---\n", 4)
    if end == -1:
        raise SystemExit(f"FAIL: {path.name} frontmatter not closed")
    block = content[4:end]
    data = {}
    for line in block.splitlines():
        if ":" not in line or line.startswith((" ", "\t")):
            continue
        key, _, value = line.partition(":")
        data[key.strip()] = value.strip()
    return data


errors = []
for filename, expected_effort in EXPECTED.items():
    path = agents_dir / filename
    if not path.exists():
        errors.append(f"{filename}: file not found")
        continue
    actual_effort = parse_frontmatter(path).get("effort")
    if actual_effort != expected_effort:
        errors.append(
            f"{filename}: effort={actual_effort!r} (expected {expected_effort!r})"
        )

if errors:
    print("FAIL: agent-effort-schema")
    for e in errors:
        print(f"  - {e}")
    sys.exit(1)

print(f"PASS: agent-effort-schema ({len(EXPECTED)}/{len(EXPECTED)} agents pinned)")
PYEOF
echo "VERDICT: agent-effort-schema: OK"
