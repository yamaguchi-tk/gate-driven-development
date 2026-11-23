#!/usr/bin/env bash
set -euo pipefail

PLUGIN_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SNYK_PLUGIN_ROOT="${SNYK_PLUGIN_ROOT:-}"
KEEP_TEMP=0
TMP_DIR=""

usage() {
  cat <<EOF
Usage: $0 [--snyk-plugin-root <path>] [--keep-temp]

The verifier plugin root comes from --snyk-plugin-root or SNYK_PLUGIN_ROOT.

Create a temporary GDD tasklist and verify that an external verifier
can write a `security_evidence:code` row into `Verification`.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --snyk-plugin-root)
      SNYK_PLUGIN_ROOT="${2:-}"
      shift 2
      ;;
    --snyk-plugin-root=*)
      SNYK_PLUGIN_ROOT="${1#*=}"
      shift
      ;;
    --keep-temp)
      KEEP_TEMP=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "unknown argument: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

cleanup() {
  if [[ "$KEEP_TEMP" -eq 0 && -n "$TMP_DIR" && -d "$TMP_DIR" ]]; then
    rm -rf "$TMP_DIR"
  fi
}
trap cleanup EXIT

NODE_BIN=""
PYTHON_BIN=""

if command -v node >/dev/null 2>&1; then
  NODE_BIN="node"
fi

for cmd in python3 python; do
  if command -v "$cmd" >/dev/null 2>&1; then
    PYTHON_BIN="$cmd"
    break
  fi
done

if [[ -z "$NODE_BIN" ]]; then
  echo "MISSING: node runtime" >&2
  exit 1
fi

if [[ -z "$PYTHON_BIN" ]]; then
  echo "MISSING: python runtime (python3 or python)" >&2
  exit 1
fi

if [[ ! -f "$SNYK_PLUGIN_ROOT/hooks/scripts/update-snyk-scan-state.js" ]]; then
  echo "MISSING: snyk verifier hook script under $SNYK_PLUGIN_ROOT" >&2
  exit 1
fi

TMP_DIR="$(mktemp -d)"
PROJECT_DIR="$TMP_DIR/project"
mkdir -p "$PROJECT_DIR/.steering/20260406-example" "$PROJECT_DIR/src"
touch "$PROJECT_DIR/src/app.ts"

cat > "$PROJECT_DIR/.steering/20260406-example/tasklist.md" <<'EOF'
# tasklist

## Current Task

- T1 | AC-01 | wire external verifier

## Pending Tasks

- なし

## Completed Tasks

- なし

## Verification

| method | status | evidence | notes |
|---|---|---|---|
| method=security_evidence:code | pending | - | 初期値 |
EOF

printf '%s' '{"tool_name":"Write","tool_input":{"file_path":"'"$PROJECT_DIR"'/src/app.ts"}}' | \
  CLAUDE_PROJECT_DIR="$PROJECT_DIR" \
  "$NODE_BIN" "$SNYK_PLUGIN_ROOT/hooks/scripts/update-snyk-scan-state.js" >/tmp/gdd-snyk-edit.json

printf '%s' '{"tool_name":"mcp__snyk__snyk_code_scan","tool_input":{"path":"'"$PROJECT_DIR"'"},"tool_result":{"success":true}}' | \
  CLAUDE_PROJECT_DIR="$PROJECT_DIR" \
  "$NODE_BIN" "$SNYK_PLUGIN_ROOT/hooks/scripts/update-snyk-scan-state.js" >/tmp/gdd-snyk-scan.json

"$PYTHON_BIN" - "$PROJECT_DIR/.steering/20260406-example/tasklist.md" <<'PY'
import pathlib
import re
import sys

content = pathlib.Path(sys.argv[1]).read_text(encoding="utf-8")
if "security_evidence:code" not in content:
    raise SystemExit("external verifier smoke must write security_evidence:code row")
pattern = re.compile(
    r"- SECURITY-CODE \| security_evidence:code \| pass \| tool=mcp__snyk__snyk_code_scan; at=.*; files=src/app.ts \| updated by \S+ hook for code"
)
if not pattern.search(content):
    raise SystemExit(f"external verifier smoke row shape mismatch: {content}")
PY

echo "OK: external verifier wrote security_evidence:code"
if [[ "$KEEP_TEMP" -eq 1 ]]; then
  echo "TEMP_DIR=$TMP_DIR"
fi
