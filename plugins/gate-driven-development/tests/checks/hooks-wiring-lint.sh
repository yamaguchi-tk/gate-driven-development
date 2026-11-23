#!/usr/bin/env bash
set -euo pipefail
: "${ROOT:?}" "${PYTHON_BIN:?}"

echo "BLOCK: hooks-wiring-lint"
# hooks/scripts/run-*.sh のうち、hooks.json のいずれの event/command からも
# 参照されていない script があれば fail する（配線漏れ検知）。
"$PYTHON_BIN" - "$ROOT" <<'PY'
import glob
import json
import os
import re
import sys

root = sys.argv[1]
hooks_json_path = os.path.join(root, "hooks", "hooks.json")

with open(hooks_json_path, encoding="utf-8") as f:
    hooks_config = json.load(f)

referenced = set()
for _event, matchers in hooks_config.get("hooks", {}).items():
    for matcher in matchers:
        for hook in matcher.get("hooks", []):
            command = hook.get("command", "")
            referenced.update(re.findall(r"run-[a-zA-Z0-9-]+\.sh", command))

all_scripts = {
    os.path.basename(p)
    for p in glob.glob(os.path.join(root, "hooks", "scripts", "run-*.sh"))
}

unwired = sorted(all_scripts - referenced)

if unwired:
    for name in unwired:
        print(f"FAIL: hooks-wiring-lint: unwired script not referenced in hooks.json: {name}")
    sys.exit(1)

print(f"hooks-wiring-lint: OK ({len(all_scripts)} run-*.sh scripts all wired)")
PY
echo "VERDICT: hooks-wiring-lint: OK"
