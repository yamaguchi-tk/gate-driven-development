#!/usr/bin/env bash
# `set -e` は使わない（独立レビュー R4 #2）。この wrapper は rc を自前で受けて deny(exit 2)
# へ倒すのが役目なので、stderr 中継や rm の失敗で `set -e` が別 rc の途中終了 =
# PreToolUse の**非 block** を起こすと、fail-closed の正本そのものが fail-open になる。
# `source` の失敗で exit 1（非 block）に落ちていた経路も同時に閉じる。
set -uo pipefail
_KS_DIR="${BASH_SOURCE[0]%/*}"
[[ "$_KS_DIR" == "${BASH_SOURCE[0]}" ]] && _KS_DIR="."
source "$_KS_DIR/lib/kill-switch.sh"
gdd_kill_switch_active && exit 0

# fail-closed の正本はこの wrapper（独立レビュー R3 #1）。
# Python 側の top-level guard は `main()` の中でしか効かず、module import 段階の例外
# （`lib/steering_size.py` 等の欠落・部分更新・`sys.modules["lib"]` 衝突）は exit 1 =
# PreToolUse の**非 block** になり、email / secret / peer-turn の既存 deny が
# 1 件も走らないまま write が通る。ここで rc を受けて 0 / 2 以外を deny + exit 2 に倒す。
GUARD_DENY_JSON='{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny"},"systemMessage":"Blocked write to .steering: the steering safety hook could not run to completion and fails closed. Retry after checking the Python runtime; to bypass a hook defect, disable GDD hooks via ~/.claude/gdd-hooks-disabled."}'

PYTHON_BIN=""

for candidate in python3 python; do
  if command -v "$candidate" >/dev/null 2>&1; then
    PYTHON_BIN="$candidate"
    break
  fi
done

if [[ -z "$PYTHON_BIN" ]]; then
  # Python 不在も同じ fail-closed 経路（本文だけ原因を具体化する）。
  echo '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny"},"systemMessage":"Blocked write to .steering because no Python runtime is available for the steering safety hook."}' >&2
  exit 2
fi

# python の stderr は一旦退避する。異常終了時の traceback には path / content の生値が
# 載りうるため、固定文 deny に差し替えるときは捨てる（Python 側 guard と同じ方針）。
# 退避ファイルは harness の timeout / Ctrl-C で kill されても残さない（R4 #4）。
ERR_FILE=""
trap 'rm -f "$ERR_FILE"' EXIT INT TERM HUP
ERR_FILE="$(mktemp "${TMPDIR:-/tmp}/gdd-steering-hook.XXXXXX" 2>/dev/null || true)"
RC=0
if [[ -n "$ERR_FILE" ]]; then
  "$PYTHON_BIN" "${CLAUDE_PLUGIN_ROOT}/hooks/scripts/validate-steering-write.py" 2>"$ERR_FILE"
  RC=$?
else
  # mktemp 失敗（TMPDIR が書き込み不可等）。ここで 2>/dev/null にすると rc 2 の deny 本文
  # まで捨てて「理由なし block」になるので、stderr はそのまま通し rc 変換だけ行う。
  # 縮退経路として、異常終了時に traceback が利用者に見えることは許容する（R4 #2）。
  "$PYTHON_BIN" "${CLAUDE_PLUGIN_ROOT}/hooks/scripts/validate-steering-write.py"
  RC=$?
fi

# 1 = 未捕捉例外 / import 失敗、124 = timeout、126 / 127 = 起動失敗。いずれも非 block。
# 以降は stderr 中継や rm が失敗しても必ず deny 側（exit 2）で終える。
if [[ "$RC" -ne 0 && "$RC" -ne 2 ]]; then
  printf '%s\n' "$GUARD_DENY_JSON" >&2 || true
  exit 2
fi

if [[ -n "$ERR_FILE" ]]; then
  cat "$ERR_FILE" >&2 || true
fi
exit "$RC"
