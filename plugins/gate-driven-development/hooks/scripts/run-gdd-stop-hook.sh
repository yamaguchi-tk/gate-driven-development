#!/usr/bin/env bash
set -euo pipefail

_KS_DIR="${BASH_SOURCE[0]%/*}"
[[ "$_KS_DIR" == "${BASH_SOURCE[0]}" ]] && _KS_DIR="."
source "$_KS_DIR/lib/kill-switch.sh"
gdd_kill_switch_active && exit 0

# payload の cwd（セッションの cwd）へ移してから marker を探す。移った後も lib を読めるよう、先に絶対パスにする
_KS_DIR="$(cd "$_KS_DIR" && pwd)"
# shellcheck source=lib/payload-cwd.sh
source "$_KS_DIR/lib/payload-cwd.sh"
gdd_enter_payload_cwd

HOOK_INPUT="$(cat)"
source "$_KS_DIR/lib/gdd-active-check.sh"

should_block() {
  # active でなければ fail-open
  gdd_local_state_active || return 1
  # 既に stop_hook_active なら二重 block しない（無限ループ防止）
  gdd_stop_hook_already_active "$HOOK_INPUT" && return 1
  return 0
}

PYTHON_BIN=""
PLUGIN_ROOT="$(cd "$_KS_DIR/../.." && pwd)"
SCRIPT_DIR="$_KS_DIR"
for cmd in python3 python; do
  if command -v "$cmd" >/dev/null 2>&1; then
    PYTHON_BIN="$cmd"
    break
  fi
done

if [[ -z "$PYTHON_BIN" ]]; then
  echo "GDD Stop hook requires python3 or python." >&2
  # GDD active な場合のみ block（fail-open）。JSON payload で AI に警告を伝える
  if should_block; then
    cat <<'JSON'
{"decision":"block","reason":"GDD Stop hook continuation prompt","systemMessage":"[GDD Stop hook 不全] python3/python が見つかりません。GDD の自律継続・done guard・progress 表示が機能しません。python3 をインストールしてください。"}
JSON
  fi
  exit 0
fi

# Check git availability (required for worktree operations, tasklist lookup, etc.)
if ! command -v git >/dev/null 2>&1; then
  echo "GDD Stop hook: git not found." >&2
  if should_block; then
    cat <<'JSON'
{"decision":"block","reason":"GDD Stop hook continuation prompt","systemMessage":"[GDD Stop hook 不全] git が見つかりません。GDD の worktree 操作・tasklist 検索・done guard が機能しません。git をインストールしてください。"}
JSON
  fi
  exit 0
fi

export GDD_HOOK_INPUT="$HOOK_INPUT"
export GDD_PLUGIN_ROOT="$PLUGIN_ROOT"

# Temporarily disable errexit so we can capture Python exit code for fail-closed handling
set +e
"$PYTHON_BIN" "$SCRIPT_DIR/gdd_stop_hook.py"
PYTHON_EXIT=$?
if [[ $PYTHON_EXIT -ne 0 ]]; then
  echo "GDD Stop hook: Python script exited with code $PYTHON_EXIT" >&2
  if should_block; then
    echo "{\"decision\":\"block\",\"reason\":\"GDD Stop hook continuation prompt\",\"systemMessage\":\"[GDD Stop hook 不全] Python スクリプトがエラーで終了しました (exit='$PYTHON_EXIT')。GDD の自律継続・done guard・progress 表示が不完全です。ログを確認してください。\"}"
  fi
fi
exit 0
