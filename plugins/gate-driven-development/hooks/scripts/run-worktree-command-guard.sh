#!/usr/bin/env bash
set -euo pipefail
_KS_DIR="${BASH_SOURCE[0]%/*}"
[[ "$_KS_DIR" == "${BASH_SOURCE[0]}" ]] && _KS_DIR="."
source "$_KS_DIR/lib/kill-switch.sh"
gdd_kill_switch_active && exit 0

PYTHON_BIN=""
for candidate in python3 python; do
  if command -v "$candidate" >/dev/null 2>&1; then
    PYTHON_BIN="$candidate"
    break
  fi
done

if [[ -z "$PYTHON_BIN" ]]; then
  exit 0
fi

# exec は kill-switch.sh の python3 関数（-I で起動する）を通らないので使わない
"$PYTHON_BIN" "${CLAUDE_PLUGIN_ROOT}/hooks/scripts/validate-worktree-command.py"
