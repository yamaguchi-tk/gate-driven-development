#!/usr/bin/env bash
# shellcheck source=exact-path.sh
source "${BASH_SOURCE[0]%/*}/exact-path.sh"

# 今の cwd の repo と、入口で移す前の repo のどちらかで marker が active なら真
# （lib/exact-path.sh の `gdd_any_project_root`）。python/git 実行に依存しない active 判定。
gdd_local_state_active() {
  gdd_any_project_root _gdd_local_state_active_at
}

# root 1 つでの判定（Stop の bash 側）。toplevel が改行で終わるなら marker で判定できないので
# active として扱う（止める側）。
_gdd_local_state_active_at() {
  [[ "$1" == *$'\n' ]] && return 0
  local state="$1/.claude/gdd-dev.local.md"
  [[ -f "$state" ]] || return 1
  grep -Eqi '^active:[[:space:]]*true' "$state"
}

# stdin JSON payload に stop_hook_active:true が含まれるか（純 bash grep）。
gdd_stop_hook_already_active() {
  local payload="$1"
  printf '%s' "$payload" | grep -Eq '"stop_hook_active"[[:space:]]*:[[:space:]]*true'
}
