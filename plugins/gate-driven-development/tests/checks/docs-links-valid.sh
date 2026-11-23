#!/usr/bin/env bash
set -euo pipefail
: "${ROOT:?}" "${PYTHON_BIN:?}"

echo "BLOCK: docs-links-valid"
"$PYTHON_BIN" - "$ROOT" <<'PY'
"""Check that docs/*.md only references existing references/ and docs/ files.

For each docs/*.md file, extract references to `references/<name>.md` and
`docs/<name>.md` (in backticks) and verify the targets exist. Prevents drift
between human-facing docs/ and the plugin-internal references/ contract.
"""
import pathlib
import re
import sys

root = pathlib.Path(sys.argv[1])
docs_dir = root / "docs"
refs_dir = root / "references"
errors = []

if not docs_dir.exists():
    print("SKIP: docs/ not present")
    print("VERDICT: docs-links-valid: SKIP")
    sys.exit(0)

for doc_md in sorted(docs_dir.glob("*.md")):
    text = doc_md.read_text(encoding="utf-8")
    for m in re.finditer(r"`references/([\w-]+\.md)`", text):
        ref_name = m.group(1)
        if not (refs_dir / ref_name).exists():
            errors.append(f"{doc_md.name}: references/{ref_name} not found")
    for m in re.finditer(r"`docs/([\w-]+\.md)`", text):
        doc_name = m.group(1)
        if not (docs_dir / doc_name).exists():
            errors.append(f"{doc_md.name}: docs/{doc_name} not found")

if errors:
    for e in errors:
        print(f"DRIFT: {e}", file=sys.stderr)
    sys.exit(1)
print("OK")
print("VERDICT: docs-links-valid: OK")
PY

