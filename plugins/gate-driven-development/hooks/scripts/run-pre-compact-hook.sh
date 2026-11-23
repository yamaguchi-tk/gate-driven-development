#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/kill-switch.sh"
gdd_kill_switch_active && exit 0
# payload の cwd（セッションの cwd）へ移してから steering・marker を探す
# shellcheck source=lib/payload-cwd.sh
source "$SCRIPT_DIR/lib/payload-cwd.sh"
gdd_enter_payload_cwd

# env から渡された GDD_STEERING_DIR を source 前に保存する
# （detect-steering.sh の source により GDD_STEERING_DIR がリセットされるため）
_ENV_STEERING_DIR="${GDD_STEERING_DIR:-}"

source "$SCRIPT_DIR/lib/detect-steering.sh"

# GDD_STEERING_DIR が env から渡されていなければ detect する
STEERING_DIR="${_ENV_STEERING_DIR:-}"
if [[ -z "$STEERING_DIR" ]]; then
  gdd_detect_active_steering 2>/dev/null || true
  STEERING_DIR="${GDD_STEERING_DIR:-}"
fi

# 別 session の steering の状態は要約器へ渡さない（UserPromptSubmit・plan-reread と同じ
# gdd_session_continuity_ok。GDD_STEERING_DIR を env で渡したときは worktree が分からないので、照合せずに渡す）
if [[ -n "${GDD_STEERING_WT:-}" ]]; then
  gdd_session_continuity_ok "$GDD_STEERING_WT/.claude/gdd-dev.local.md" || exit 0
fi

# STEERING_DIR が空またはディレクトリでない場合は noop
if [[ -z "$STEERING_DIR" ]] || [[ ! -d "$STEERING_DIR" ]]; then
  exit 0
fi

# state.md が存在しない場合は noop（コンパクションをブロックしない）
STATE_FILE="$STEERING_DIR/state.md"
if [[ ! -f "$STATE_FILE" ]]; then
  exit 0
fi

# compaction の直前に、GDD の状態を要約器へ渡す。exit 0 の PreCompact hook の stdout は、
# compaction の要約器へ `Additional Instructions` として渡る（Claude Code 2.1.261 で確認）。
# subagent の compaction でもこの hook は走り、main と見分けられない。そのため、渡すのは役割を
# 問わない事実（state.md の場所・Resume From・Next Action）だけにし、「再開せよ」「委譲せよ」の
# ような指示は入れない。state.md には書かない。
# どちらの値も `|` 以降（evidence など）は落とす（SessionStart と同じ gdd_value_head）
RESUME_FROM="$(gdd_value_head "$(gdd_extract_doc_field "$STATE_FILE" "Resume From" || true)")"
# Next Action は、build 中（3 つの承認が揃った tasklist.md。判定は SessionStart・UserPromptSubmit と同じ
# gdd_check_3field_gate）は tasklist.md を先に読み、無ければ state.md（この順は
# gdd_validate_active_state_fields と同じ）
GDD_STEERING_DIR="$STEERING_DIR"
gdd_check_3field_gate
NEXT_ACTION=""
if [[ "$GDD_TASKLIST_CANONICAL" == "true" ]]; then
  NEXT_ACTION="$(gdd_extract_doc_field "$STEERING_DIR/tasklist.md" "Next Action" || true)"
fi
[[ -n "$NEXT_ACTION" ]] || NEXT_ACTION="$(gdd_extract_doc_field "$STATE_FILE" "Next Action" || true)"
NEXT_ACTION="$(gdd_value_head "$NEXT_ACTION")"
[[ -n "$RESUME_FROM" || -n "$NEXT_ACTION" ]] || exit 0

# 場所と値は外部入力として python の中で sanitize する（不正な UTF-8 は捨て、制御文字を除き、文字単位で
# 切り詰める）。python3 が無い、または実行時に失敗しても compaction をブロックしない（noop 方針）。
# set -e 下でも `if VAR=$(cmd); then` の形は非0終了を伝播させない。
if REMINDER_JSON=$(STATE_PATH="$STATE_FILE" RESUME_FROM="$RESUME_FROM" NEXT_ACTION="$NEXT_ACTION" python3 -I -X utf8 -c '
import json
import os
import sys
import unicodedata


def clean(name, limit):
    value = os.fsencode(os.environ[name]).decode("utf-8", "ignore")
    value = "".join(ch for ch in value if unicodedata.category(ch) != "Cc").strip()
    return value[:limit]


message = (
    "compaction 前の GDD の状態（" + clean("STATE_PATH", 512) + "）: "
    "Resume From = " + (clean("RESUME_FROM", 128) or "(なし)") + "、"
    "Next Action = " + (clean("NEXT_ACTION", 128) or "(なし)") + "。"
)
# 要約器が読む文なので、非 ASCII を \uXXXX にせず、ロケールに依らず UTF-8 のまま出す
sys.stdout.buffer.write((json.dumps({"systemMessage": message}, ensure_ascii=False) + "\n").encode("utf-8"))
' 2>/dev/null); then
  printf '%s\n' "$REMINDER_JSON"
fi

exit 0
