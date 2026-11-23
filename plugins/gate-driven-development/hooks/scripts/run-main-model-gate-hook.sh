#!/usr/bin/env bash
set -euo pipefail

# PreToolUse（Skill・Write・Edit・MultiEdit）・Stop・SessionStart hook:
# main が Sonnet・Haiku のときに Skill の gdd-dev・gdd-resume と、手動の手順で run を始める
# `.claude/gdd-dev.local.md` への書き込みを止め、相談の段（返事の後の Stop）でセッションにつき
# 1 回知らせる（SessionStart は payload の model だけで判定する）。setup-gdd-loop.sh の実行は script の中で同じ判定を呼ぶ。
# 判定の根拠は hooks/scripts/lib/main_model_gate.py。

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/kill-switch.sh"
gdd_kill_switch_active && exit 0

command -v python3 >/dev/null 2>&1 || exit 0
payload="$(cat)"
# 書き込みのたびに python を起こさない。判定する入力は、どれもこの語のどれかを含む（大文字小文字は問わない）
shopt -s nocasematch
case "$payload" in
  *gdd-dev.local.md*|*Skill*|*Stop*|*SessionStart*) ;;
  *) exit 0 ;;
esac
printf '%s' "$payload" | python3 "$SCRIPT_DIR/lib/main_model_gate.py" || true
