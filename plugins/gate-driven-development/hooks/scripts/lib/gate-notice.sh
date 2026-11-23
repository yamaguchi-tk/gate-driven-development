# shellcheck shell=bash
# 止めない gate（pre-push gate・pre-PR gate・merge gate）の「実行後の通知」と would-block の記録。
#
# gdd_gate_notice <log-file-name> <code>[,<code>...] <text>
#   - <text> を systemMessage と hookSpecificOutput.additionalContext に入れて stdout に 1 行で返す。
#     止めない hook の additionalContext は、コマンドの実行後に agent に届く
#   - state dir の <log-file-name> に `<時刻> | event: would-block:<code> | repo: <hash>` を 1 行足す。
#     code は呼び出し側が渡す。pre-push gate・pre-PR gate は宣言して渡し（本文から切り出さない）、
#     merge gate は呼び出し側の block() が本文の `不足条件:` か `reason code:` から切り出して渡す。
#     記録は best-effort で、書けなくても通知は返す
#   - python3 に依存しない（解析が失敗する環境でも通知を返す）。エスケープは `\` `"` と、
#     値に残りうる tab / 改行 / CR にする
gdd_gate_notice() {
  local _log_name="$1" _code="$2" _text="$3"
  _text="${_text//\\/\\\\}"; _text="${_text//\"/\\\"}"
  _text="${_text//$'\t'/\\t}"; _text="${_text//$'\n'/\\n}"; _text="${_text//$'\r'/\\r}"
  printf '{"systemMessage": "%s", "hookSpecificOutput": {"hookEventName": "PreToolUse", "additionalContext": "%s"}}\n' "$_text" "$_text"
  ( _gdd_gate_notice_log "$_log_name" "would-block:${_code//[^a-z0-9,-]/}" ) 2>/dev/null || true
}

# repo は非可逆 ID（絶対パス全体の sha1 先頭 8 桁）にし、絶対パス・repo 名は残さない。
# merge gate の `_mg_log_suppressed`（merge-gate-suppressed.log）もこの関数で書く。
_gdd_gate_notice_log() {
  local _log_name="$1" _event="$2"
  local _state_dir="${GDD_HOOK_STATE_DIR:-${HOME:-}/.claude/.gdd-hook-state}"
  [[ -n "$_state_dir" && "$_state_dir" != "/.claude/.gdd-hook-state" ]] || return 0
  local _logfile="$_state_dir/$_log_name" _repo_id
  if command -v shasum >/dev/null 2>&1; then
    _repo_id="$(printf '%s' "${PROJECT_ROOT:-}" | shasum -a 1 | cut -c1-8)"
  else
    _repo_id="$(printf '%s' "${PROJECT_ROOT:-}" | sha1sum | cut -c1-8)"
  fi
  mkdir -p "$_state_dir" 2>/dev/null || return 0
  # 在るのに通常ファイルでないログ（FIFO など）は開かない。FIFO への `>>` は読み手が来るまで戻らない
  if [[ -e "$_logfile" || -L "$_logfile" ]]; then
    [[ -f "$_logfile" && -w "$_logfile" ]] || return 0
  fi
  printf '%s | event: %s | repo: %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$_event" "$_repo_id" >>"$_logfile" 2>/dev/null || true
  chmod 600 "$_logfile" 2>/dev/null || true
}
