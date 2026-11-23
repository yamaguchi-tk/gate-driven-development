#!/usr/bin/env bash
set -euo pipefail

# PreToolUse hook: /gdd-dev session 中の host Plan mode 移行を fail-closed にする。
# gdd-dev は自身のワークフロー内で要件整理・設計・実装を行うため、
# Plan mode への切り替えは contract 違反（gdd-dev.md §0, common-guardrails.md §Plan mode との分離）。

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/kill-switch.sh"
gdd_kill_switch_active && exit 0
# payload の cwd（セッションの cwd）へ移してから steering・marker を探す
# shellcheck source=lib/payload-cwd.sh
source "$SCRIPT_DIR/lib/payload-cwd.sh"
gdd_enter_payload_cwd
# shellcheck source=lib/detect-steering.sh
source "$SCRIPT_DIR/lib/detect-steering.sh"

# gdd-dev.local.md が active でこのセッションのもの、または判定できないときにブロック
# shellcheck source=lib/exact-path.sh
source "$SCRIPT_DIR/lib/exact-path.sh"
gdd_resolve_project_root
PROJECT_ROOT="$GDD_PROJECT_ROOT"

# payload の cwd の repo と、入口で移す前の repo のすべてで、このセッションの active な marker が
# 無いと言い切れたときだけ通す。判定できない（cwd を取れない・marker が読めないなど）ときは止める（lib/exact-path.sh）。
gdd_marker_allows && exit 0

# Cursor では Plan mode 遷移が SwitchMode(target_mode_id=plan) として届く。
# Agent へ戻す SwitchMode までブロックしないよう、SwitchMode は target_mode_id=plan の時だけ止める。
PAYLOAD="$(python3 -c '
import json
import sys

try:
    payload = json.load(sys.stdin)
except Exception:
    print("block")
    raise SystemExit

tool_name = str(payload.get("tool_name", ""))
tool_input = payload.get("tool_input", {})

if tool_name == "SwitchMode":
    target = ""
    if isinstance(tool_input, dict):
        target = str(tool_input.get("target_mode_id", ""))
    print("block" if target == "plan" else "allow")
elif tool_name in {"EnterPlanMode", "Plan"}:
    print("block")
else:
    # hooks.json should only route plan-mode tools here. If a host reports a
    # namespaced name, fail closed when it still clearly describes plan entry.
    print("block" if "PlanMode" in tool_name else "allow")
' 2>/dev/null || printf 'block')"

if [[ "$PAYLOAD" != "block" ]]; then
  exit 0
fi

# gdd-dev session が active なので host Plan mode をブロック
# JSON 文字列内で改行を表現するには \\n が必要（printf が \\n を \n に変換し、JSON パーサが改行として解釈する）
printf '{"decision":"block","reason":"⛔ /gdd-dev session が active です。Plan mode は使用できません。\\n\\nなぜ: Plan mode は host 固有の計画機能、GDD は state machine による計画・実行・再開の一本化を提供します。両方を同時に走らせると「どちらが計画の正本か」が曖昧になり、state 不整合で中断復帰が壊れます。\\n\\nどうする: ユーザーの後続依頼を GDD 内で分類してください。既存 AC 内の修正なら implementation_fix_only / debugging、AC 変更なら gdd-requirements-amendment、責任境界が変わるなら human_recheck_required です。タスクの複雑さは GDD の task sizing（trivial / quick / standard）で対応してください。\\n\\n参照: gdd-dev.md §0, references/phase-progression.md §Active Session Follow-up Classification, common-guardrails.md §Plan mode との分離"}\n'
