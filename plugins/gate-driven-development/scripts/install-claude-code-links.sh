#!/usr/bin/env bash
set -euo pipefail

PLUGIN_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CLAUDE_HOME="${CLAUDE_HOME:-${HOME}/.claude}"
TARGET_HOME="$CLAUDE_HOME"
STATE_DIR="$CLAUDE_HOME/plugins/gate-driven-development"
STATE_FILE="$STATE_DIR/claude-code-links.tsv"
DRY_RUN=false

if [[ "${1:-}" == "--dry-run" ]]; then
  DRY_RUN=true
elif [[ -n "${1:-}" ]]; then
  echo "Usage: $0 [--dry-run]"
  exit 1
fi

# shellcheck source=_link-helpers.sh
source "$(dirname "${BASH_SOURCE[0]}")/_link-helpers.sh"

run_install "Claude Code"
