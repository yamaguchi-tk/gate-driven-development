#!/usr/bin/env bash
set -euo pipefail

# PreToolUse hook（判定 1）: Agent 起動時に、工程に対して model が
# 未指定、または工程が許容する model 集合に含まれない場合（軽量モデルへの
# ダウングレードを含む）に additionalContext で警告する。agent 定義で opus に
# 固定した agent に opus 以外の model を明示した起動も、工程の tier によらず
# model の省略を促す（judge_fixed_override）。warn のみで block はしない。許容集合の判定根拠は hooks/scripts/lib/agent_dispatch_gate.py。
#
# 判定材料は 5 つの閉じた入力に限定する:
#   1. tool_input.subagent_type（固定語彙）
#   2. tool_input.model（固定語彙 / 未指定）
#   3. .claude/gdd-dev.local.md の active
#   4. state.md の Resume From（planning phase 専用の正本）
#   5. tasklist.md の Next Action（build phase の正本。references/state-machine.md:199-208）
# description の自由文は使わない（PR #83 の失敗を繰り返さない）。

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/kill-switch.sh"
gdd_kill_switch_active && exit 0
# payload の cwd（セッションの cwd）へ移してから steering・marker を探す
# shellcheck source=lib/payload-cwd.sh
source "$SCRIPT_DIR/lib/payload-cwd.sh"
gdd_enter_payload_cwd
# shellcheck source=lib/detect-steering.sh
source "$SCRIPT_DIR/lib/detect-steering.sh"

PAYLOAD="$(cat)"

# shellcheck source=lib/exact-path.sh
source "$SCRIPT_DIR/lib/exact-path.sh"
gdd_resolve_project_root
PROJECT_ROOT="$GDD_PROJECT_ROOT"

# payload の cwd の repo と、入口で移す前の repo のすべてで、このセッションの active な marker が
# 無いと言い切れたときだけ通す。判定できない（cwd を取れない・marker が読めないなど）ときは止める（lib/exact-path.sh）。
gdd_marker_allows && exit 0

if ! gdd_detect_active_steering; then
  # steering が一意に定まらない（none / multiple）場合、判定 1 は fail-open せず
  # 何もしない。fail-closed で block すると warn-only の設計方針（判定1はwarn）と
  # 矛盾するため、材料が読めないケースは「工程不明」と同様に扱う。
  exit 0
fi

RESUME_FROM="$(gdd_extract_doc_field "$GDD_STEERING_DIR/state.md" "Resume From")"

# Next Action は 3 gate 承認済み（canonical）の tasklist.md でのみ routing source
# として有効。draft の tasklist.md に書かれた Next Action は仮置きの記載値でしか
# なく、それを phase 判定に使うと未承認段階の worker を誤って formal gate 扱い
# してしまう（独立レビューの指摘）。
NEXT_ACTION=""
gdd_check_3field_gate
if [[ "$GDD_TASKLIST_CANONICAL" == "true" ]]; then
  # tasklist.md → state.md の順で読む。設計上の routing source は tasklist.md だが、
  # 実運用では state.md 側に書かれることが多い（gdd_validate_active_state_fields の
  # コメントのとおり state.md 側が多い。同じフォールバック順に揃える）。
  NEXT_ACTION="$(gdd_extract_doc_field "$GDD_STEERING_DIR/tasklist.md" "Next Action")"
  if [[ -z "${NEXT_ACTION// /}" ]]; then
    NEXT_ACTION="$(gdd_extract_doc_field "$GDD_STEERING_DIR/state.md" "Next Action")"
  fi
fi

# $PAYLOAD を argv 経由で python3 に渡すと、大きな prompt を含む Agent 起動で
# ARG_MAX を超えて抽出自体が失敗し（model 未指定と誤認される）、かつ ps 等の
# プロセス一覧に prompt の内容まで露出しうる。既存の pre-push / merge gate hook
# と同じく stdin 経由で 1 回だけ parse する（PR #91 人間レビュー指摘、Medium）。
# subagent_type / model をまとめて 1 回の python3 呼び出しで抽出し、TSV 1 行で返す。
SUBAGENT_MODEL_TSV="$(printf '%s' "$PAYLOAD" | python3 -c '
import json
import sys

try:
    payload = json.loads(sys.stdin.read())
except Exception:
    payload = {}

tool_input = payload.get("tool_input", {})
if not isinstance(tool_input, dict):
    tool_input = {}

def _s(value):
    return value.strip() if isinstance(value, str) else ""

subagent_type = _s(tool_input.get("subagent_type"))
model = _s(tool_input.get("model"))
print(subagent_type + "\t" + model)
' 2>/dev/null || true)"

SUBAGENT_TYPE="${SUBAGENT_MODEL_TSV%%$'\t'*}"
MODEL="${SUBAGENT_MODEL_TSV#*$'\t'}"

FINDING_JSON="$(python3 -c '
import json
import sys

sys.path.insert(0, sys.argv[1])
import agent_dispatch_gate as gate

subagent_type = sys.argv[2]
model = sys.argv[3]
resume_from = sys.argv[4]
next_action = sys.argv[5]

if gate.is_exempt_from_phase_model_check(subagent_type, model):
    raise SystemExit
# model を省略した起動は、agent 定義の frontmatter の model で動く
from_agent = not model and bool(gate.fixed_model(subagent_type))
model = model or gate.fixed_model(subagent_type)

phase = gate.resolve_phase(resume_from, next_action)
if not phase:
    raise SystemExit

finding = gate.judge_fixed_override(phase, subagent_type, model) or gate.judge(phase, model)
if finding is None:
    raise SystemExit
finding["from_agent"] = from_agent
finding["simplifier"] = subagent_type.rpartition(":")[2] == "gdd-code-simplifier"

print(json.dumps(finding, ensure_ascii=False))
' "$SCRIPT_DIR/lib" "$SUBAGENT_TYPE" "$MODEL" "$RESUME_FROM" "$NEXT_ACTION" 2>/dev/null || true)"

if [[ -z "$FINDING_JSON" ]]; then
  exit 0
fi

MESSAGE="$(python3 -c '
import json
import sys

finding = json.loads(sys.argv[1])
reason = finding["reason"]
phase = finding["phase"]
required = finding["required"]
actual = finding["actual"]

if finding.get("from_agent") and finding.get("simplifier"):
    body = (
        f"工程 {phase} は model=\"{required}\" が必須ですが、"
        f"model を省略したこの agent は agent 定義の model（{actual}）で動きます。"
        "簡素化パスは、Next Action が gdd-subagent-driven-implementation のとき（REFACTOR の後）に起動します。"
        "先に Next Action を確かめてください。"
    )
elif finding.get("from_agent"):
    body = (
        f"工程 {phase} は model=\"{required}\" が必須ですが、"
        f"model を省略したこの agent は agent 定義の model（{actual}）で動きます。"
        "実装の worker は、Next Action が gdd-subagent-driven-implementation のときに起動するので、"
        "先に Next Action を確かめてください。この工程のまま worker を起動するなら、"
        "gate-driven-development:gdd-implementation-worker-heavy（Gate Rounds 2 以上は "
        "gdd-remediation-worker）を model 省略で起動し、## Worktree と ## Plugin Root を渡してください。"
    )
elif reason == "overrides_fixed":
    body = (
        f"この agent は agent 定義で model=\"{required}\" に固定していますが、"
        f"model=\"{actual}\" が指定されています。明示した model は定義より優先されるので、"
        "model を省略して起動してください。"
    )
elif reason == "unspecified" and phase == "gdd-subagent-driven-implementation":
    body = (
        f"工程 {phase} は model 未指定で起動されようとしています。"
        "実装の worker を起動するなら、gate-driven-development:gdd-implementation-worker"
        "（Complexity: standard）・gdd-implementation-worker-heavy（それ以外）・"
        "gdd-remediation-worker（Gate Rounds 2 以上）を model 省略で起動し、"
        "## Worktree と ## Plugin Root を渡してください"
        "（skills/gdd-subagent-driven-implementation/SKILL.md の手順 3）。"
        f"worker 以外の起動なら model=\"{required}\" か \"opus\" を明示してください。"
    )
elif reason == "unspecified":
    body = (
        f"工程 {phase} は model 未指定で起動されようとしています。"
        "未指定だと host 既定（main セッションの model）に落ちます"
        "（実際に、model を書かずに起動して main の model に落ちる例が多い）。"
        f"model=\"{required}\" を明示してください。"
    )
else:
    body = (
        f"工程 {phase} は model=\"{required}\" が必須ですが "
        f"model=\"{actual}\" が指定されています。"
        f"model=\"{required}\" に変更してください。"
    )

print("[agent-dispatch-model-gate] " + body)
' "$FINDING_JSON" 2>/dev/null || true)"

# warn-only の設計方針上、メッセージ生成に失敗しても hook 全体を落とさない
# （`set -e` 下で python3 が失敗すると additionalContext が出ないまま非0終了し、
# 本来 block しないはずの判定1がエラー扱いになりかねない。独立レビューの指摘）。
if [[ -z "$MESSAGE" ]]; then
  exit 0
fi

python3 -c '
import json
import sys

message = sys.argv[1]
print(json.dumps({
    "hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "additionalContext": message,
    }
}, ensure_ascii=False))
' "$MESSAGE" 2>/dev/null || true
