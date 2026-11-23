#!/usr/bin/env bash
# hook の入口で、プロセスの cwd を payload の最上位の `cwd`（セッションの cwd）へ移す。
#
# desktop の worktree のセッションでは、hook のプロセスの cwd は root checkout になり、
# payload の `cwd` が worktree になる。cwd で steering・marker を探す lib（detect-steering.sh・
# exact-path.sh・gdd-active-check.sh）は、移さないと root checkout の古い steering を読む。
#
# - stdin の payload を 1 回読んで `GDD_HOOK_PAYLOAD` に入れ、同じ中身を stdin に戻す
#   （後ろの `$(cat)` などがそのまま読める）
# - 移す前の cwd を `GDD_ORIGIN_CWD` に残す（exact-path.sh が、移す前の repo にある
#   このセッションの marker も見るため）
# - 使える cwd の条件は `hook_cwd.toplevel_cwd` と同じ。使えない・読めないときは移さない
# - `--timeout` を渡すと、stdin を 1 秒だけ待つ（fd 0 が閉じない起動で止まらないため。
#   SessionStart の読み方と同じ）
_GDD_PAYLOAD_CWD_LIB="$(cd "${BASH_SOURCE[0]%/*}" && pwd)"

# 入口の失敗（cwd が消えていて `pwd` が取れないなど）で hook 全体を落とさないよう、本体は
# `|| true` の文脈で呼ぶ（その中では `set -e` が効かない）。失敗したら移さないだけになる。
gdd_enter_payload_cwd() {
  GDD_ORIGIN_CWD=""
  GDD_HOOK_PAYLOAD=""
  _gdd_enter_payload_cwd_body "$@" || true
  return 0
}

_gdd_enter_payload_cwd_body() {
  local _v _dir=""
  if _v="$(pwd 2>/dev/null && printf x)"; then
    GDD_ORIGIN_CWD="${_v%$'\n'x}"
  fi
  if [[ "${1:-}" == "--timeout" ]]; then
    IFS= read -r -d '' -t 1 GDD_HOOK_PAYLOAD 2>/dev/null || true
  else
    IFS= read -r -d '' GDD_HOOK_PAYLOAD 2>/dev/null || true
  fi
  exec 0< <(printf '%s' "$GDD_HOOK_PAYLOAD")
  command -v python3 >/dev/null 2>&1 || return 0
  _dir="$(printf '%s' "$GDD_HOOK_PAYLOAD" | python3 -I -X utf8 -c '
import json, sys
sys.path.insert(0, sys.argv[1])
from hook_cwd import toplevel_cwd
try:
    payload = json.loads(sys.stdin.read())
except Exception:
    payload = None
sys.stdout.write(toplevel_cwd(payload))
' "$_GDD_PAYLOAD_CWD_LIB" 2>/dev/null)" || return 0
  if [[ -n "$_dir" ]]; then
    cd "$_dir" 2>/dev/null || true
  fi
  return 0
}
