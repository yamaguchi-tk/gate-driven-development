#!/usr/bin/env bash
# PreToolUse hook（matcher: Bash）: state.md の `Human Check Status` を approved にする Bash を、提示を読まずに
# Write・Edit へ付け替える。承認の照合（直前の human check の提示の `依頼との差:`）は
# Write・Edit の検査（validate-steering-write.py）の 1 か所だけで行う。shell は解析しない。
# 通すのは「payload に `Human Check Status` と `approved` の両方が無い」と「kill switch が有効」の 2 つだけで、
# それ以外（kill-switch.sh を読めないときを含む）は deny で終える。`set -e` は使わない（途中の失敗で exit 1 に
# 落ちると、PreToolUse は通してしまう。run-steering-write-hook.sh と同じ）。python は起動しない。
set -u

PAYLOAD="$(cat 2>/dev/null)"
case "$PAYLOAD" in
  *"Human Check Status"*) ;;
  *) exit 0 ;;
esac
case "$PAYLOAD" in
  *approved*) ;;
  *) exit 0 ;;
esac

_DIR="${BASH_SOURCE[0]%/*}"
[[ "$_DIR" == "${BASH_SOURCE[0]}" ]] && _DIR="."
if source "$_DIR/lib/kill-switch.sh" 2>/dev/null && gdd_kill_switch_active; then
  exit 0
fi

printf '%s\n' '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"state.md の `Human Check Status` を approved にする書き込みは、Bash ではなく Edit・Write のツールで行ってください（直前の human check の提示の `依頼との差:` を、その検査が照らします）。state.md を読むだけなら Read・Grep のツールを使ってください。"}}'
exit 0
