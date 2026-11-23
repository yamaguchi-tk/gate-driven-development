#!/usr/bin/env bash
# marker の中身を読む Python（lib/state_io.py）の import 元。hooks/scripts（この lib の親）
_GDD_EXACT_PATH_SCRIPTS="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." 2>/dev/null && pwd)"
# repo の toplevel を末尾の改行まで正しく取る。`$(pwd)`・`$(git rev-parse --show-toplevel)`
# は末尾の改行を全部落とすので、名前が改行で終わる repo（`<repo>\n`）が別のパス
# （`<repo>`）になり、active な GDD の marker を見落とす。`printf x` を番兵にして、
# 最後の改行 1 つだけを落とす（merge gate と同じ読み方）。
#
# 結果は `GDD_PROJECT_ROOT` に入れる（呼び出し側で `$()` を通すと、また削られる）。
# git が無い・git の外なら cwd のまま。
#
# marker（`.claude/gdd-dev.local.md`）の書き手 `scripts/setup-gdd-loop.sh` は、まだ
# 改行を落としたパスに書く。block gate は、値が改行で終わるなら marker で判定できない
# ものとして止める側に倒す（`gdd_marker_state_at`）。
#
# cwd を取れない（消えたディレクトリなど）ときは空にする。block gate はそれも判定できない
# root として止める側に倒す（`gdd_marker_state_at`）。
gdd_resolve_project_root() {
  local _v
  GDD_PROJECT_ROOT=""
  _v="$(pwd 2>/dev/null && printf x)" || return 0
  gdd_toplevel_of "${_v%$'\n'x}"
  GDD_PROJECT_ROOT="$GDD_TOPLEVEL"
  return 0
}

# ディレクトリ $1 の toplevel を `GDD_TOPLEVEL` に入れる（読み方は上と同じ。git が無い・git の外なら $1 のまま）。
gdd_toplevel_of() {
  local _v
  GDD_TOPLEVEL="$1"
  command -v git >/dev/null 2>&1 || return 0
  if _v="$(git -C "$1" rev-parse --show-toplevel 2>/dev/null && printf x)" && [[ "$_v" == *$'\n'x ]]; then
    GDD_TOPLEVEL="${_v%$'\n'x}"
  fi
  return 0
}

# 述語 $1（root を 1 つ受ける関数）を、今の cwd の toplevel（入口で payload の cwd へ移した後なら
# そちら）と、入口で移す前の cwd の toplevel（`GDD_ORIGIN_CWD`。lib/payload-cwd.sh）の両方に当て、
# どちらかで真なら真。root を 1 つ選ばずに同じ述語を当てるので、移す前だけを見ていた頃より
# 止める側が狭くなることはない。`GDD_PROJECT_ROOT` は今の cwd の toplevel のまま残す。
gdd_any_project_root() {
  gdd_resolve_project_root
  "$1" "$GDD_PROJECT_ROOT" && return 0
  [[ -n "${GDD_ORIGIN_CWD:-}" ]] || return 1
  gdd_toplevel_of "$GDD_ORIGIN_CWD"
  [[ "$GDD_TOPLEVEL" != "$GDD_PROJECT_ROOT" ]] || return 1
  "$1" "$GDD_TOPLEVEL"
}

# block gate の、root 1 つの判定。0 = このセッションの active な marker が在る、1 = 無いと言い切れる、
# 2 = 判定できない。1 を返すのは正の証拠があるときだけで、ほかは既定で 2（止める側）になる。
# - 在不在: marker が無く（宙に浮いた symlink も無い）、親のディレクトリを検索できたときだけ「無い」
# - 中身: marker が在るときは、Stop hook と同じ Python のコード（state_io.py の marker_state。
#   parse_state と同じ行の分け方で読む）に任せる。`active` が false なら「無い」。`active` が true でも、
#   session_id が空か、許す文字（英数字・`.`・`_`・`:`・`-`）だけで今の `CLAUDE_CODE_SESSION_ID` と
#   違うなら、別のセッションのものとして「無い」。今の id が無ければ比べない
# - `active` の値が無い・true でも false でもない、session_id が許す文字の外、frontmatter が無い・
#   閉じていない、`active`・session_id が frontmatter に 2 行以上ある（どの行を採るかで読み手の結論が
#   割れる）、python3 が無い・例外、root が空（cwd を取れない）・改行で終わるときは 2
gdd_marker_state_at() {
  local _state="$1/.claude/gdd-dev.local.md" _v _current="${CLAUDE_CODE_SESSION_ID:-}"
  [[ -n "$1" && "$1" != *$'\n' ]] || return 2
  if [[ ! -e "$_state" && ! -L "$_state" ]]; then
    if [[ -d "$1/.claude" ]]; then
      [[ -x "$1/.claude" ]] || return 2
    fi
    [[ -d "$1" && -x "$1" ]] && return 1
    return 2
  fi
  [[ -f "$_state" && -r "$_state" ]] || return 2
  _v="$(python3 -I -X utf8 -c '
import sys
sys.path.insert(0, sys.argv[1])
from lib.state_io import marker_state
print(marker_state(__import__("pathlib").Path(sys.argv[2]), sys.argv[3]))
' "$_GDD_EXACT_PATH_SCRIPTS" "$_state" "$_current" 2>/dev/null)" || return 2
  case "$_v" in
    0) return 0 ;;
    1) return 1 ;;
    *) return 2 ;;
  esac
}

# block gate が通してよいか。今の cwd の toplevel と、入口で移す前の cwd の toplevel（`GDD_ORIGIN_CWD`）の
# すべてで「このセッションの active な marker が無い」と言い切れたときだけ 0。判定できないときは止める側。
# 入口（lib/payload-cwd.sh）は `pwd` が成功すれば `GDD_ORIGIN_CWD` を埋めるので、空なのは移す前の cwd を
# 取れなかったとき（判定できない）だけである。
gdd_marker_allows() {
  local _s=0
  gdd_resolve_project_root
  gdd_marker_state_at "$GDD_PROJECT_ROOT" || _s=$?
  [[ $_s -eq 1 ]] || return 1
  [[ -n "${GDD_ORIGIN_CWD:-}" ]] || return 1
  gdd_toplevel_of "$GDD_ORIGIN_CWD"
  [[ "$GDD_TOPLEVEL" != "$GDD_PROJECT_ROOT" ]] || return 0
  _s=0
  gdd_marker_state_at "$GDD_TOPLEVEL" || _s=$?
  [[ $_s -eq 1 ]]
}
