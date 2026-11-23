#!/usr/bin/env bash
set -euo pipefail

PLUGIN_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GDD_RUNTIME="${GDD_RUNTIME:-claude_code}"
GDD_STATE_FILE="${GDD_STATE_FILE:-$(pwd)/.claude/gdd-dev.local.md}"
FORWARD_ARGS=()
MODEL=""
TEXT=""
PYTHON_BIN=""

for cmd in python3 python; do
  if command -v "$cmd" >/dev/null 2>&1; then
    PYTHON_BIN="$cmd"
    break
  fi
done

if [[ -z "$PYTHON_BIN" ]]; then
  echo "MISSING: python3 or python is required" >&2
  exit 1
fi

if ! command -v claude >/dev/null 2>&1; then
  echo "MISSING: claude CLI is not available on PATH" >&2
  exit 1
fi

usage() {
  cat <<EOF
Usage: $0 [options] [claude arguments...]

Options:
  --runtime <claude_code|cursor>  Resolve the launch model for the chosen runtime
  --state-file <path>             gdd state file to inspect for a recommendation
  --text <prompt>                 Prompt text used when resolving a model
  --model <model>                 Explicit model override
  -h, --help                      Show this help

If --model is omitted, the script resolves one from the state file and prompt text.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help)
      usage
      exit 0
      ;;
    --runtime)
      GDD_RUNTIME="${2:-}"
      shift 2
      ;;
    --runtime=*)
      GDD_RUNTIME="${1#*=}"
      shift
      ;;
    --state-file)
      GDD_STATE_FILE="${2:-}"
      shift 2
      ;;
    --state-file=*)
      GDD_STATE_FILE="${1#*=}"
      shift
      ;;
    --text)
      TEXT="${2:-}"
      shift 2
      ;;
    --text=*)
      TEXT="${1#*=}"
      shift
      ;;
    --model)
      MODEL="${2:-}"
      FORWARD_ARGS+=("$1" "${2:-}")
      shift 2
      ;;
    --model=*)
      MODEL="${1#*=}"
      FORWARD_ARGS+=("$1")
      shift
      ;;
    *)
      FORWARD_ARGS+=("$1")
      if [[ -z "$TEXT" && "$1" != -* ]]; then
        TEXT="$1"
      fi
      shift
      ;;
  esac
done

if [[ -z "$MODEL" ]]; then
  MODEL="$(
    "$PYTHON_BIN" "$PLUGIN_ROOT/scripts/resolve-gdd-model.py" \
      --runtime "$GDD_RUNTIME" \
      --state-file "$GDD_STATE_FILE" \
      --text "$TEXT"
  )"
  FORWARD_ARGS=(--model "$MODEL" "${FORWARD_ARGS[@]}")
fi

exec claude --plugin-dir "$PLUGIN_ROOT" "${FORWARD_ARGS[@]}"
