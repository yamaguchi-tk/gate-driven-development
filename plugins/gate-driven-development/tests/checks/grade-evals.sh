#!/usr/bin/env bash
set -euo pipefail
: "${ROOT:?}" "${PYTHON_BIN:?}"

echo "BLOCK: grade-evals"
"$PYTHON_BIN" - "$ROOT" <<'PY'
import json
import os
import pathlib
import re
import subprocess
import tempfile
import sys

root = pathlib.Path(sys.argv[1])
manifest_paths = [
    root / ".claude-plugin" / "plugin.json",
    root / ".cursor-plugin" / "plugin.json",
    root / ".codex-plugin" / "plugin.json",
]
manifest_data = []

for manifest_path in manifest_paths:
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    for key in ["name", "version", "description"]:
        if not data.get(key):
            raise SystemExit(
                f"{manifest_path.relative_to(root)} manifest field is missing: {key}"
            )
    if manifest_path.parent.name != ".codex-plugin" and data.get("hooks") == "./hooks/hooks.json":
        raise SystemExit(
            f"{manifest_path.relative_to(root)} manifest must not redundantly declare standard hooks/hooks.json"
        )
    manifest_data.append(data)

if manifest_data[0] != manifest_data[1]:
    raise SystemExit(
        "plugin manifests differ: .claude-plugin/plugin.json vs .cursor-plugin/plugin.json"
    )

for key in ["name", "version", "description", "author", "keywords"]:
    if manifest_data[0].get(key) != manifest_data[2].get(key):
        raise SystemExit(
            f"plugin manifests differ in shared field {key}: .claude-plugin/plugin.json vs .codex-plugin/plugin.json"
        )
if manifest_data[2].get("skills") != "./skills/":
    raise SystemExit(".codex-plugin/plugin.json must expose ./skills/")
PY

echo "OK"

echo "VERDICT: grade-evals: OK"
