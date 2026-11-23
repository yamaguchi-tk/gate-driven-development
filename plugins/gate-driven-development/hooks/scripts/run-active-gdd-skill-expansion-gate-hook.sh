#!/usr/bin/env bash
set -euo pipefail

# UserPromptExpansion hook: direct `/superpowers:...` skill invocations bypass
# PreToolUse Skill hooks, so active GDD needs a prompt-level backstop too.

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

# payload を読む python3 が 0 以外で終わった（無い・落ちた）ときは、通すと答えたことにならないので止める
if ! DIRECT_SKILL="$(python3 -c '
import json
import re
import sys

try:
    payload = json.load(sys.stdin)
except Exception:
    raise SystemExit

prompt = payload.get("prompt", "")
if not isinstance(prompt, str):
    raise SystemExit

match = re.search(
    r"(?m)^\s*/(superpowers:(?:writing-plans|executing-plans|brainstorming))\b",
    prompt,
)
if match:
    print(match.group(1))
' 2>/dev/null)"; then
  printf '%s\n' '{"decision":"block","reason":"⛔ active GDD workflow の marker がある repo で、python3 を起動できず判定できないので止めました。\n\nどうする: python3 を直してください。一時的に GDD の hook を止めるなら ~/.claude/gdd-hooks-disabled を作ってください。"}'
  exit 0
fi

[[ -n "$DIRECT_SKILL" ]] || exit 0

printf '%s\n' '{"decision":"block","reason":"⛔ UserPromptExpansion: active GDD workflow では direct /superpowers planning/execution skill invocation を開始できません。\n\nどうする: active GDD の state を正本にしてください。要件・AC・計画途中の変更は gdd-requirements-amendment、承認済み設計からの task 再分解は gdd-task-breakdown、要件前提の再整理は gdd-brainstorming に戻してください。\n\n対象 skill: '"$DIRECT_SKILL"'"}'
