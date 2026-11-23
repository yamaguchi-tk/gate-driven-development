#!/usr/bin/env bash
set -euo pipefail

# PreToolUse（Agent）hook: 突き合わせ agent の起動のときに、request.md がまだ無ければ、main の transcript の
# ユーザーの発言の節で作る。既にある request.md には触らない。起動は止めない。
# 判定と書き方は hooks/scripts/lib/request_capture.py。

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/kill-switch.sh"
gdd_kill_switch_active && exit 0

command -v python3 >/dev/null 2>&1 || exit 0
python3 "$SCRIPT_DIR/lib/request_capture.py" || true
