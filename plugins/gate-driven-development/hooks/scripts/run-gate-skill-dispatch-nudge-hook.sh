#!/usr/bin/env bash
set -euo pipefail

# PreToolUse hook (Skill matcher): gate の skill（gdd-implementation-gating・gdd-completion-check）が
# Skill ツールで直接呼ばれたとき、references/subagent-dispatch.md の Template で
# gdd-formal-gate-runner に dispatch するよう additionalContext を 1 つ注入する（block ではなく nudge）。
#
# runner で回す規定は commands/gdd-dev.md・subagent-dispatch.md にだけあり、Stop hook の継続文言にも
# skill の本文にも無かった。自由文での再開や compact・resume の後に、main が Next Action の名前の skill を
# そのまま呼び、gate を main で回していた（2026-09-28〜30 の実測: GDD の reviewer の起動の一部が
# main から。handoff/ の記録が残らず、impl-gate の round 2 を飛ばした例もあった）。どの例も自動継続が
# 効いていない状態で起きていたので、GDD の loop が active かは問わない。
#
# runner は agent 定義の tools に Skill を持たず、手順を Read で読む。Skill ツールでの呼び出しは main からと
# 見なし、main と subagent を見分けない（文言で「runner の中ならこのまま続ける」と逃がす）。

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/kill-switch.sh"
gdd_kill_switch_active && exit 0

DISPATCH_DOC="$(cd "$SCRIPT_DIR/../.." && pwd)/references/subagent-dispatch.md"

python3 -c '
import json
import sys

try:
    payload = json.load(sys.stdin)
except Exception:
    raise SystemExit
if not isinstance(payload, dict):
    raise SystemExit
tool_input = payload.get("tool_input")
if not isinstance(tool_input, dict):
    raise SystemExit

name = ""
for key in ("name", "skill_name", "skill"):
    value = tool_input.get(key)
    if isinstance(value, str) and value.strip():
        name = value.strip()
        break

skill = name.rsplit(":", 1)[-1]
template = {
    "gdd-implementation-gating": "Implementation-Gating Template",
    "gdd-completion-check": "Completion-Check Template",
}.get(skill)
if template is None:
    raise SystemExit

message = (
    f"[gdd:gate-dispatch] `{skill}` は main セッションで回さない。main から呼んだなら、この skill の手順を"
    f"ここで実行せず、{sys.argv[1]} の `### {template}` を Read・置換して "
    "`gate-driven-development:gdd-formal-gate-runner` に dispatch する（Template の State Update Contract と "
    "handoff/ の記録は runner が書く）。runner の中で読んでいるなら、このまま続ける。"
)
print(json.dumps(
    {"hookSpecificOutput": {"hookEventName": "PreToolUse", "additionalContext": message}},
    ensure_ascii=False,
))
' "$DISPATCH_DOC" 2>/dev/null || true

exit 0
