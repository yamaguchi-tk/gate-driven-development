#!/usr/bin/env bash
set -euo pipefail

# PreToolUse hook（matcher: Bash）: background の待ちのループ（until・while・for と sleep、--watch、
# gh run watch）を deny し、scripts/wait-until.py で待たせる。GDD active を問わず、全セッションで動く。
# 判定は hooks/scripts/lib/wait_loop_gate.py。型を読めない payload は通す（JSON として読めないものは
# state dir（~/.claude/.gdd-hook-state/。GDD_HOOK_STATE_DIR で変えられる）の wait-loop-gate.log に記録する。repo の中には書かない）。

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/kill-switch.sh"
gdd_kill_switch_active && exit 0

# payload は stdin で渡す（argv だと大きな command で ARG_MAX を超える）。background でない Bash は python を起動せずに通す。
PAYLOAD="$(cat 2>/dev/null || true)"
case "$PAYLOAD" in
  *run_in_background*) ;;
  *) exit 0 ;;
esac

# state dir は run-review-followup-nudge-hook.sh と同じ（HOME が無ければ記録しない）。
STATE_DIR="${GDD_HOOK_STATE_DIR:-}"
if [[ -z "$STATE_DIR" && -n "${HOME:-}" ]]; then
  STATE_DIR="${HOME}/.claude/.gdd-hook-state"
fi
LOG_FILE=""
if [[ -n "$STATE_DIR" ]]; then
  LOG_FILE="$STATE_DIR/wait-loop-gate.log"
fi

# -I で cwd（repo）の lib・json などが plugin の module を置き換えないようにする（-I は PYTHONUTF8 を読まないので -X utf8）。
printf '%s' "$PAYLOAD" | python3 -I -X utf8 -c '
import sys
sys.path.insert(0, sys.argv[2])
from lib.wait_loop_gate import main
main(sys.argv[1])
' "$LOG_FILE" "$SCRIPT_DIR" || true
