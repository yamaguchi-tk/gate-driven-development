#!/usr/bin/env bash
set -euo pipefail

# SessionStart hook: PR がある branch への push を、レビュー済みの tip かどうかで判定する
# git の pre-push hook を、この session の Bash に差し込む（log-only。push は止めない）。
#
# 差し込みは `$CLAUDE_ENV_FILE` に書く。Claude Code は、この file を main・background・subagent
# の Bash の前に読み込む（2026-10-07 に headless claude で実測）。コマンドの文面は変えない
# （PreToolUse の updatedInput で書き換えると、auto mode の classifier が `core.hooksPath`
# などの上書きを含む文面を見て止めうる。複数の hook が書き換えると最後の 1 つしか効かない）。
#
# git の hook は、設定による hook（`hook.gdd-push-review.event` / `.command`）を `GIT_CONFIG_*`
# で渡す。plugin の更新などで script が消えても push を止めないよう、script が無ければ何もしない。
# `core.hooksPath` を置き換えないので、repo の `.git/hooks` や husky の hook もそのまま動く
# （git 2.54 で実測。設定による hook に対応しない git では何も起きない）。
#
# 判定は git-pre-push-review-hook.sh が transcript を読んで行う。その transcript のパスを
# `GDD_PUSH_REVIEW_TRANSCRIPT` に入れる。compact・resume でも書き直す（matcher は `*`）。同じ
# shell で 2 回読み込まれても、git の hook は `GDD_PUSH_REVIEW_HOOKED` で 1 回だけ足す。

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/kill-switch.sh"
gdd_kill_switch_active && exit 0

[[ -n "${CLAUDE_ENV_FILE:-}" ]] || exit 0

# stdin を読むのは 1 回だけで、閉じなくても 1 秒で戻る（run-session-start-hook.sh と同じ）。
_payload=""
IFS= read -r -d '' -t 1 _payload 2>/dev/null || true
[[ -n "$_payload" ]] || exit 0

# 1 行目に source、2 行目に session（transcript の名前の sha1 の先頭 8 桁）、3 行目以降にパスを出す。
_parsed="$(printf '%s' "$_payload" | python3 -c '
import hashlib, json, os, sys
try:
    data = json.load(sys.stdin.buffer)
except Exception:
    raise SystemExit(0)
path = data.get("transcript_path") if isinstance(data, dict) else None
if isinstance(path, str) and path:
    source = data.get("source") if isinstance(data.get("source"), str) else ""
    stem = os.path.splitext(os.path.basename(path))[0]
    sys.stdout.write(source + "\n" + hashlib.sha1(stem.encode("utf-8", "replace")).hexdigest()[:8] + "\n" + path)
' 2>/dev/null || true)"
[[ -n "$_parsed" ]] || exit 0
_source="${_parsed%%$'\n'*}"
_rest="${_parsed#*$'\n'}"
_session="${_rest%%$'\n'*}"
_transcript="${_rest#*$'\n'}"

# env file は shell が source する。引用符・`$`・空白などを含むパスは書かない（書くと、
# source する shell でコマンドとして読まれうる）。書かなかったことは state dir のログに 1 行残す
# （log-only の期間に、差し込めなかった session を数えるため）。
_safe_path='^/[A-Za-z0-9._/@+-]+$'
# 同じ session の compact では、開いたときに書いた行を繰り返さない。
_not_installed() {
  local dir="${GDD_HOOK_STATE_DIR:-${HOME:+$HOME/.claude/.gdd-hook-state}}"
  [[ -n "$dir" && "$_source" != "compact" ]] || return 0
  (
    umask 077
    mkdir -p "$dir" &&
      printf '%s | verdict: not-installed | reason: %s | session: %s\n' \
        "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$1" "$_session" >> "$dir/push-review.log"
  ) 2>/dev/null || true
}
if [[ ! "$_transcript" =~ $_safe_path ]]; then
  _not_installed unsafe-path
  exit 0
fi
_git_hook="$SCRIPT_DIR/git-pre-push-review-hook.sh"
if [[ ! "$_git_hook" =~ $_safe_path ]]; then
  _not_installed unsafe-hook-path
  exit 0
fi

{
  printf '%s\n' "# gate-driven-development: push review (log-only)"
  printf "export GDD_PUSH_REVIEW_TRANSCRIPT='%s'\n" "$_transcript"
  printf '%s\n' 'if [ -z "${GDD_PUSH_REVIEW_HOOKED:-}" ]; then'
  printf '%s\n' '  case "${GIT_CONFIG_COUNT:-0}" in'
  printf '%s\n' '    ""|*[!0-9]*) ;;'
  printf '%s\n' '    *)'
  printf '%s\n' '      _gdd_n="${GIT_CONFIG_COUNT:-0}"'
  printf '%s\n' '      export "GIT_CONFIG_KEY_${_gdd_n}=hook.gdd-push-review.event" "GIT_CONFIG_VALUE_${_gdd_n}=pre-push"'
  printf '%s\n' '      _gdd_n=$((_gdd_n + 1))'
  printf '      export "GIT_CONFIG_KEY_${_gdd_n}=hook.gdd-push-review.command" "GIT_CONFIG_VALUE_${_gdd_n}=[ ! -f %s ] || bash %s"\n' "$_git_hook" "$_git_hook"
  printf '%s\n' '      export GIT_CONFIG_COUNT=$((_gdd_n + 1)) GDD_PUSH_REVIEW_HOOKED=1'
  printf '%s\n' '      unset _gdd_n'
  printf '%s\n' '      ;;'
  printf '%s\n' '  esac'
  printf '%s\n' 'fi'
} >> "$CLAUDE_ENV_FILE" 2>/dev/null || true
exit 0
