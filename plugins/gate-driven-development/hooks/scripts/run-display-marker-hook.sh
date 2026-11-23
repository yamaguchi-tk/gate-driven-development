#!/usr/bin/env bash
set -euo pipefail

# Stop hook: human check の返事を受けたターンで、一次表示に出した `記録の場所: なし` の行に
# ` / 表示: 済み` の印が無ければ、systemMessage で知らせる（止めない）。判定は hooks/scripts/lib/display_marker.py。

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/kill-switch.sh"
gdd_kill_switch_active && exit 0

command -v python3 >/dev/null 2>&1 || exit 0
python3 "$SCRIPT_DIR/lib/display_marker.py" || true
