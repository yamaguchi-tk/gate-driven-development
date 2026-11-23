#!/usr/bin/env bash
set -euo pipefail
: "${ROOT:?}" "${PYTHON_BIN:?}"

echo "BLOCK: broken-reference-lint"
"$PYTHON_BIN" - "$ROOT" <<'PY'
"""Detect broken scripts/*.sh and references/*.md path references inside
skill/references body text (backtick-quoted inline paths only).

Scope (avoids double-reporting with existing lints):
  - source: skills/**/*.md and references/*.md only. docs/ is never scanned
    here (owned by docs-links-valid.sh); *-steps.md is excluded (owned by
    skill-reference-drift.sh).
  - reference syntax: backtick-quoted inline paths only. Paths inside fenced
    code blocks (``` ... ```) are ignored (illustrative examples, not real
    references).
  - resolution: for each referenced relative path, try in order:
      1) the referencing file's own skill directory (skills/<skill-name>/)
      2) the plugin root
      3) the plugin root after stripping a literal "${CLAUDE_PLUGIN_ROOT}/" prefix
    If any candidate is an existing file, the reference is valid. A reference
    containing a ".." path component is always treated as broken (no
    legitimate managed reference needs to traverse outside the plugin root).
"""
import pathlib
import re
import sys

root = pathlib.Path(sys.argv[1])
skills_dir = root / "skills"
refs_dir = root / "references"

FENCE = re.compile(r"```.*?```", re.DOTALL)
PATH_REF = re.compile(
    r"`(\$\{CLAUDE_PLUGIN_ROOT\}/(?:scripts|references)/[\w./-]+\.(?:sh|md)"
    r"|(?:scripts|references)/[\w./-]+\.(?:sh|md))`"
)


def strip_fences(text: str) -> str:
    return FENCE.sub("", text)


def skill_dir_for(path: pathlib.Path):
    try:
        rel = path.relative_to(skills_dir)
    except ValueError:
        return None
    return skills_dir / rel.parts[0]


def resolves(ref: str, source_path: pathlib.Path) -> bool:
    if ".." in pathlib.PurePosixPath(ref).parts:
        return False
    candidates = []
    skill_dir = skill_dir_for(source_path)
    if skill_dir is not None:
        candidates.append(skill_dir / ref)
    candidates.append(root / ref)
    if ref.startswith("${CLAUDE_PLUGIN_ROOT}/"):
        candidates.append(root / ref[len("${CLAUDE_PLUGIN_ROOT}/"):])
    return any(c.is_file() for c in candidates)


def iter_sources():
    if skills_dir.exists():
        for md in sorted(skills_dir.rglob("*.md")):
            if md.name.endswith("-steps.md"):
                continue
            yield md
    if refs_dir.exists():
        for md in sorted(refs_dir.glob("*.md")):
            if md.name.endswith("-steps.md"):
                continue
            yield md


errors = []
for src in iter_sources():
    text = strip_fences(src.read_text(encoding="utf-8"))
    for m in PATH_REF.finditer(text):
        ref = m.group(1)
        if not resolves(ref, src):
            errors.append(f"{src.relative_to(root)}: broken reference `{ref}`")

if errors:
    for e in errors:
        print(f"DRIFT: {e}", file=sys.stderr)
    sys.exit(1)
print("OK: no broken scripts/references path references found")
PY
echo "VERDICT: broken-reference-lint: OK"
