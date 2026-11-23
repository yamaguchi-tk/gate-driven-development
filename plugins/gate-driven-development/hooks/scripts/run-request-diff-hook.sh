#!/usr/bin/env bash
set -euo pipefail

# Stop hook: human check の提示の `依頼との差:` の欄の形が崩れていれば block して出し直させる。
# 形が正しければ依頼の発言に照らし、差があれば systemMessage で種類ごとに 1 行見せる（こちらは止めない）。
# 判定と書き方は hooks/scripts/lib/request_diff.py。

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/kill-switch.sh"
gdd_kill_switch_active && exit 0

command -v python3 >/dev/null 2>&1 || exit 0
python3 "$SCRIPT_DIR/lib/request_diff.py" || true
