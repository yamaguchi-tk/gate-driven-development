#!/usr/bin/env bash
set -euo pipefail

# PreToolUse hook（matcher: Agent）: /gdd-dev が active の間、main からの
# gdd-formal-gate-runner の同期起動を deny し、background と期限 timer で起動させる。
# 判定は hooks/scripts/lib/background_dispatch_gate.py。型を読めない payload は通す（JSON として読めないものは記録する）。

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/kill-switch.sh"
gdd_kill_switch_active && exit 0
# payload の cwd（セッションの cwd）へ移してから steering・marker を探す
# shellcheck source=lib/payload-cwd.sh
source "$SCRIPT_DIR/lib/payload-cwd.sh"
gdd_enter_payload_cwd
# shellcheck source=lib/detect-steering.sh
source "$SCRIPT_DIR/lib/detect-steering.sh"
# shellcheck source=lib/exact-path.sh
source "$SCRIPT_DIR/lib/exact-path.sh"
gdd_resolve_project_root
PROJECT_ROOT="$GDD_PROJECT_ROOT"

# payload の cwd の repo と、入口で移す前の repo のすべてで、このセッションの active な marker が
# 無いと言い切れたときだけ通す。判定できない（cwd を取れない・marker が読めないなど）ときは止める（lib/exact-path.sh）。
gdd_marker_allows && exit 0

# python3 が 0 以外で終わった（無い・落ちた）ときは、通すと答えたことにならないので deny する。
# payload は stdin で渡す（argv だと大きな prompt で ARG_MAX を超える）。
# -I で cwd（repo）の lib・json などが plugin の module を置き換えないようにする（-I は PYTHONUTF8 を読まないので -X utf8）。
python3 -I -X utf8 -c '
import sys
sys.path.insert(0, sys.argv[2])
from lib.background_dispatch_gate import main
main(sys.argv[1])
' "$PROJECT_ROOT" "$SCRIPT_DIR" || printf '%s\n' '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"⛔ active GDD workflow の marker がある repo で、python3 を起動できず判定できないので止めました。\n\nどうする: python3 を直してください。一時的に GDD の hook を止めるなら ~/.claude/gdd-hooks-disabled を作ってください。"}}'
