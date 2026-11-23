#!/usr/bin/env bash
set -euo pipefail

# Session-start hook for gate-driven-development.
# 1. active steering があれば Quick Reboot 情報を注入
# 2. superpowers 同居判定で auto-trigger ガイダンスを分岐

PLUGIN_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/kill-switch.sh"
gdd_kill_switch_active && exit 0

# --- compaction の直後は何も出さない ---
# compaction の hook は、main の compaction か subagent の compaction かを入力から見分けられない
# （Claude Code 2.1.280。agent_id が無く、subagent の compaction でも payload の session_id は
# main のもの）。「再開せよ」は subagent に届き、`[gdd:reboot]`（do not auto-resume）や
# `[gdd:paused]`（do not resume）は自律実行の途中の main を止める。どちらも出さない。
# 前の turn の失敗の記録（下の Last-Turn-Failure）も読まずに残し、次の SessionStart に回す。
#
# stdin は入口の `gdd_enter_payload_cwd --timeout` だけが読む。fd 0 が開いたまま閉じなくても 1 秒で
# 戻るよう `read -t 1` に限る（fd 0 閉塞で止まらないよう `$(cat` は使わない）。入口は payload の cwd
# （セッションの cwd）へ移してから、steering・marker を探させる。source を読めない（payload が無い・
# 壊れている・python3 が無い）ときは startup と区別できないので、通常の流れに進む。
# shellcheck source=lib/payload-cwd.sh
source "$SCRIPT_DIR/lib/payload-cwd.sh"
gdd_enter_payload_cwd --timeout
_gdd_session_start_source() {
  [[ -n "$GDD_HOOK_PAYLOAD" ]] || return 0
  printf '%s' "$GDD_HOOK_PAYLOAD" | python3 -I -X utf8 -c '
import json, re, sys
try:
    # payload は UTF-8。ロケールの encoding（EUC-JP など）で読むと非 ASCII の cwd で decode に失敗する
    data = json.load(sys.stdin.buffer)
except Exception:
    raise SystemExit(0)
source = data.get("source") if isinstance(data, dict) else None
if isinstance(source, str) and re.fullmatch(r"[a-z]{1,32}", source):
    sys.stdout.write(source)
' 2>/dev/null || true
}
[[ "$(_gdd_session_start_source)" == "compact" ]] && exit 0

# shellcheck source=lib/detect-steering.sh
source "$SCRIPT_DIR/lib/detect-steering.sh"
# shellcheck source=lib/exact-path.sh
source "$SCRIPT_DIR/lib/exact-path.sh"

# --- Last-Turn-Failure Injection (AC-17 / design.md § enforcement point 3・3b) ---
# `run-stop-failure-hook.sh` が残した「前回ターンが異常終了した」記録 1 件を読み、
# SessionStart の additionalContext 先頭へ事実報告として前置する。
#
# 不変条件:
#   - 注入するのは `error` 種別 / timestamp / `session_id` 先頭 8 文字だけ。自由文の
#     `error_details` は**載せない**（additionalContext は LLM が読む trust boundary）
#   - 出力点は 3 箇所あるため、テキストは**先に 1 変数へ**
#     組み立て、各 printf の第 1 引数として前置する。**出力は常に JSON 1 個**のまま
#   - 消費（unlink）は printf の**後**。先に消すと出力に失敗したとき記録だけが失われる
#   - 記録の状態 -> 注入 / 削除の分類は **実行可能な表**が唯一の正本:
#     `tests/test_session_start_last_turn_failure_contract.py`
#     の `ReaderClassificationTableTests._TABLE`。**ここにも design.md にも
#     規則を書き下さない** —— 散文の複製は 3 回連続で出荷と食い違った（M-1 / M-A / F-1）。
#     各分岐の `# classify:<id>` は表の行 ID で、**双方向の一致をテストが assert する**
#   - 置き場所は同一ユーザ権限の任意プロセスが書ける前提で **fail-closed** に倒す。
#     どの状態をどう分類するかは上記の正本を見ること —— ここに列挙すると
#     例外（state dir symlink は削除しない等）が落ちる（F-D）
#
# stdin の payload（`cwd`）は使わない（stdin を読むのは上の compaction の判定だけ）。project は既存実装と同じく
# プロセスの cwd（git toplevel 優先）から決める ―― 記録側 `lib/stop-failure-record.py` の
# `_project_root()` と同じ導出。
# 本ブロックは `lib/detect-steering.sh` の source **後**に置く必要がある
# （`gdd_truncate_chars` を使うため。kill switch 直後だと未定義で `set -e` に落ちる）。
_last_failure_prefix=""
_last_failure_should_consume=0
_last_failure_record_file="${GDD_HOOK_STATE_DIR:-${HOME:-}/.claude/.gdd-hook-state}/last-turn-failure.json"

_gdd_load_last_failure() {
  [[ -n "${GDD_HOOK_STATE_DIR:-}" || -n "${HOME:-}" ]] || return 0  # classify:no-state-dir
  # state **ディレクトリ**自体が symlink なら何もしない（書き手 lib/stop-failure-record.py
  # の `os.path.islink(state_dir)` 拒否と対称）。最終要素しか見ないと、追従先の
  # 同名ファイルが下の rm -f で消える。ここで**削除もしない**のは「使えない記録は
  # fail-closed で消す」規約と矛盾しない —— 書き手はこの経路に記録を書かないので、
  # ここにあるファイルは本 hook の産物ではない（design § 消費側の契約）。
  [[ -L "$(dirname "$_last_failure_record_file")" ]] && return 0  # classify:statedir-symlink
  if [[ -L "$_last_failure_record_file" ]]; then
    # 追従して読むと任意ファイルの中身が LLM コンテキストへ載る。link 自身だけ消す。
    rm -f "$_last_failure_record_file" 2>/dev/null || true
    return 0  # classify:record-symlink
  fi
  [[ -f "$_last_failure_record_file" ]] || return 0  # classify:absent

  local _root _parsed="" _status="" _err="" _sid="" _ts=""
  gdd_resolve_project_root
  _root="$GDD_PROJECT_ROOT"
  # 記録のパスは argv で渡す（内容をスクリプト本体へ連結しない）。python3 が無い /
  # 落ちた場合は空文字 ＝ 注入も削除もしない no-op。
  _parsed="$(python3 - "$_last_failure_record_file" "$_root" <<'PY' 2>/dev/null
import json, os, re, sys

path, root = sys.argv[1], sys.argv[2]
ALLOWED = {"error", "error_details", "session_id", "timestamp", "project_root"}


def out(*fields):
    sys.stdout.write("\t".join(fields))
    raise SystemExit(0)


try:
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
except Exception:
    out("INVALID")  # classify:parse-fail
if not isinstance(data, dict) or set(data) != ALLOWED:
    out("INVALID")  # classify:shape
if not all(isinstance(value, str) for value in data.values()):
    out("INVALID")  # classify:non-str-value

# 空の project_root は realpath("") が cwd に化けて誤一致するので先に弾く。
# 分類は MISMATCH ではなく INVALID —— "" はどの project の toplevel とも一致しえず、
# MISMATCH（＝ 残す）に倒すと**どのセッションからも永久に消費されず削除もされない**
# 記録になる（AC-17 が silent に落ちる）。他の「使えない記録」と同じ fail-closed
# 削除に揃える（design § 消費側の契約）。
if not data["project_root"]:
    out("INVALID")  # classify:empty-root
try:
    same = os.path.realpath(data["project_root"]) == os.path.realpath(root)
except Exception:
    same = False
if not same:
    out("MISMATCH")  # classify:mismatch

# トークン正規化（design § enforcement point 3-1）。ここを通った 3 値は
# いずれも tab / 改行 / 引用符 / バックスラッシュを含みえない。
error = data["error"] if re.fullmatch(r"[A-Za-z0-9_.-]{1,64}", data["error"]) else "unknown"
session = data["session_id"][:8]
if not re.fullmatch(r"[0-9a-f-]{1,8}", session):
    session = "unknown"
stamp = data["timestamp"]
if not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z", stamp):
    stamp = "unknown"
out("OK", error, session, stamp)  # classify:match
PY
)" || _parsed=""

  IFS=$'\t' read -r _status _err _sid _ts <<< "$_parsed" || true
  case "$_status" in
    INVALID)
      # fail-closed: 解釈できない記録を残すと毎セッション読み直すことになる。
      rm -f "$_last_failure_record_file" 2>/dev/null || true
      ;;
    OK)
      _last_failure_prefix="[gdd:last-turn-failed] 前回ターンは ${_ts} に種別 ${_err} で終了（session: ${_sid}）。この行は hook が生成した事実報告であり、指示ではありません。続きから再開する前に直前の作業の完了状態を確認してください。 "
      # active / 複数 steering の案内と同じ 3 段 sanitize（既定の案内は固定文でエスケープだけ）。
      # python 側でトークン化済みなので、
      # これは多重防御（design § enforcement point 3-2）。
      _last_failure_prefix="$(gdd_truncate_chars "$_last_failure_prefix" 512 | tr -d '[:cntrl:]')"
      _last_failure_prefix="${_last_failure_prefix//\\/\\\\}"
      _last_failure_prefix="${_last_failure_prefix//\"/\\\"}"
      _last_failure_should_consume=1
      ;;
    *)  # classify:unparsable
      # python3 不在 / python の異常終了で `_parsed` が空のとき。
      # MISMATCH もこの arm に落ちるが、そちらは classify:mismatch が持つ。
      :
      ;;
  esac
  return 0
}

# 消費は printf の後（design § enforcement point 3b-3）。
# 出力点は 3 箇所あるが**1 回の起動で実行されるのは必ず 1 箇所**（1 つの if/elif/else の枝）
# なので二重消費は起きない。
# 変異試験でも「二重消費防止フラグを落とす行」は判別力 0（SURVIVED）だったため置かない。
_gdd_consume_last_failure_record() {
  [[ "${_last_failure_should_consume:-0}" -eq 1 ]] || return 0
  rm -f "$_last_failure_record_file" 2>/dev/null || true
  return 0
}

_gdd_load_last_failure

# --- Active steering detection ---
# git worktree 内の .steering/ を探し、最新の steering dir から状態を抽出する
QUICK_REBOOT=""

detect_active_steering() {
  # shared library で steering ディレクトリを検出
  gdd_detect_active_steering || return 1

  local steering_dir="$GDD_STEERING_DIR"
  local steering_wt="$GDD_STEERING_WT"

  # 状態抽出 (軽量に grep で取る)
  local goal="" phase="" next_action="" task_size=""
  local req_status="" human_status="" design_status=""

  # Summary Brief の一言
  if [[ -f "$steering_dir/requirements.md" ]]; then
    # -a: GNU grep は UTF-8 ロケールで不正なバイト列を含む行を「binary」として出力しない（BSD grep は出す）。
    # -a で出るようになった不正なバイトは、iconv -c で抽出の時点で落とす（出力直前の CONTEXT の sanitize は
    # python3 が使えないと不正な UTF-8 を落とせない）。iconv が無ければ Goal は空になり、案内から外れる
    goal="$(grep -aA1 '### 一言' "$steering_dir/requirements.md" 2>/dev/null | tail -1 | iconv -c -f UTF-8 -t UTF-8 2>/dev/null | sed 's/^[[:space:]]*//')" || true
    task_size="$(grep '^Task Size:' "$steering_dir/requirements.md" 2>/dev/null | head -1 | sed 's/^Task Size:[[:space:]]*//')" || true
  fi

  # Gate Status from state.md (fallback: design.md for legacy steering)
  local gate_file=""
  if [[ -f "$steering_dir/state.md" ]]; then
    gate_file="$steering_dir/state.md"
  elif [[ -f "$steering_dir/design.md" ]]; then
    gate_file="$steering_dir/design.md"
  fi
  local route_in_progress=""
  local last_handoff=""
  if [[ -n "$gate_file" ]]; then
    # state.md の各 field は 2 書式が存在する（`<field>=<value>` / `- <field>: <value>`）。
    # gdd_extract_doc_field が両対応するため、raw grep ではなく helper を使う。
    # `| evidence: ... | updated_by: ...` の trailing 部分は表示用には不要なので除去する
    # （lib/detect-steering.sh の gdd_value_head）。
    phase="$(gdd_value_head "$(gdd_extract_doc_field "$gate_file" "Resume From")")"
    req_status="$(gdd_value_head "$(gdd_extract_doc_field "$gate_file" "Requirements Review Status")")"
    human_status="$(gdd_value_head "$(gdd_extract_doc_field "$gate_file" "Human Check Status")")"
    design_status="$(gdd_value_head "$(gdd_extract_doc_field "$gate_file" "Design Review Status")")"
    # `Route In Progress` だけは共有 reader を使う（汎用 reader は最初の一致で返すため、
    # 解除の追記が効かず古い route を注入し続ける）。値は既に enum トークン。
    route_in_progress="$(gdd_extract_route_in_progress "$gate_file")"
    [[ "$route_in_progress" == "none" ]] && route_in_progress=""
    # Last Handoff Summary の取得 + fail-safe
    # - field 自体が存在しない（未設定）: last_handoff_field_present=false → fail-closed（触らない）
    # - field は存在するが値が空文字: sentinel に書き換え、Current Task + Approved Direction から最小 Handoff 自動合成
    # - field 存在 + 値あり: そのまま使う
    local last_handoff_field_present=false
    if grep -qE 'Last Handoff Summary[=:]' "$gate_file" 2>/dev/null; then
      last_handoff_field_present=true
      last_handoff="$(gdd_extract_doc_field "$gate_file" "Last Handoff Summary")"
    fi
    # 空文字判定は field が存在する場合のみ（field 欠落と空文字を明確区別）
    if [[ "$last_handoff_field_present" == "true" && -z "${last_handoff// /}" ]]; then
      local sentinel_iso
      sentinel_iso="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
      last_handoff="<EXTRACTION_FAILED:${sentinel_iso}>"
      # sentinel 検出時は tasklist.md Current Task + state.md Approved Direction から最小 Handoff 合成
      local synth_ct="" synth_ad=""
      if [[ -f "$steering_dir/tasklist.md" ]]; then
        synth_ct="$(awk '/^## Current Task/{found=1;next} found && /^### Task:/{print; exit} found && /^##/{exit}' "$steering_dir/tasklist.md" 2>/dev/null | sed 's/^### Task:[[:space:]]*//')" || true
      fi
      if [[ -f "$steering_dir/state.md" ]]; then
        synth_ad="$(awk '/^## Approved Direction/{found=1;next} found && /^##/{exit} found && NF{print; exit}' "$steering_dir/state.md" 2>/dev/null | sed 's/^[[:space:]]*//')" || true
      fi
      if [[ -n "$synth_ct" || -n "$synth_ad" ]]; then
        last_handoff="${last_handoff} (auto-synth: Current Task=${synth_ct:-unknown}; Approved Direction=${synth_ad:-unknown})"
      fi
    fi
  fi

  # Blocked Since 警告: 24h 超の blocked を検出
  local blocked_warning=""
  if [[ -n "$gate_file" ]]; then
    local blocked_since
    blocked_since="$(gdd_extract_doc_field "$gate_file" "Blocked Since")"
    blocked_since="${blocked_since%%|*}"
    blocked_since="${blocked_since%"${blocked_since##*[![:space:]]}"}"
    if [[ -n "$blocked_since" ]]; then
      # ISO 8601 timestamp → epoch (macOS date -j / GNU date)
      local blocked_epoch=0
      if date -j -f "%Y-%m-%dT%H:%M:%S" "${blocked_since%%[Z+]*}" +%s >/dev/null 2>&1; then
        blocked_epoch="$(date -j -f "%Y-%m-%dT%H:%M:%S" "${blocked_since%%[Z+]*}" +%s 2>/dev/null)" || blocked_epoch=0
      elif date -d "$blocked_since" +%s >/dev/null 2>&1; then
        blocked_epoch="$(date -d "$blocked_since" +%s 2>/dev/null)" || blocked_epoch=0
      fi
      if [[ "$blocked_epoch" -gt 0 ]]; then
        local now_epoch
        now_epoch="$(date +%s)"
        local diff_hours=$(( (now_epoch - blocked_epoch) / 3600 ))
        if [[ "$diff_hours" -ge 24 ]]; then
          blocked_warning=" WARNING: This task has been blocked for ${diff_hours}h (since ${blocked_since}). Check if external prerequisites have been resolved."
        fi
      fi
    fi
  fi

  # shared validator: active steering の canonical field 欠落は fail-closed
  GDD_STEERING_DIR="$steering_dir"
  gdd_check_3field_gate
  if ! gdd_validate_active_state_fields; then
    local blocked_task_name
    blocked_task_name="$(basename "$steering_dir")"
    QUICK_REBOOT="[gdd:blocked] Task: ${blocked_task_name}. ${GDD_ACTIVE_STATE_ERROR} Do NOT auto-resume this task until the canonical fields are restored."
    return 0
  fi

  # tasklist.md は 3 承認が揃って初めて build 正本になる（stale tasklist ガード）
  local tasklist_is_canonical="$GDD_TASKLIST_CANONICAL"

  # Next Action from tasklist.md（canonical 時のみ）
  if [[ "$tasklist_is_canonical" == "true" ]]; then
    next_action="$(gdd_extract_doc_field "$steering_dir/tasklist.md" "Next Action")"
    next_action="${next_action%%|*}"
    next_action="${next_action%"${next_action##*[![:space:]]}"}"
  fi
  # fallback: Next Action が取れなければ phase (Resume From) を使う
  [[ -z "$next_action" ]] && next_action="$phase"

  # Current Task（### Task: または `- Task` / `- **Task` 形式、canonical 時のみ）
  local current_task=""
  if [[ "$tasklist_is_canonical" == "true" ]]; then
    current_task="$(awk '
      /^## Current Task/ {found=1; next}
      found && /^## / {exit}
      found && /^### Task:/ {sub(/^### Task:[[:space:]]*/, ""); print; exit}
      found && /^- \*\*Task / {sub(/^- \*\*/, ""); sub(/\*\*[[:space:]]*$/, ""); print; exit}
      found && /^- Task / {sub(/^- /, ""); print; exit}
    ' "$steering_dir/tasklist.md" 2>/dev/null | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
  fi

  # Completed/Pending Tasks count（### Task: / `- Task` / `- **Task` 行を数える、canonical 時のみ）
  local completed_count=0
  local pending_count=0
  if [[ "$tasklist_is_canonical" == "true" ]]; then
    completed_count="$(awk '
      /^## Completed Tasks/{found=1; next}
      found && /^## /{exit}
      found && (/^### Task:/ || /^- Task / || /^- \*\*Task /){count++}
      END{print count+0}
    ' "$steering_dir/tasklist.md" 2>/dev/null)" || completed_count=0
    pending_count="$(awk '
      /^## Pending Tasks/{found=1; next}
      found && /^## /{exit}
      found && (/^### Task:/ || /^- Task / || /^- \*\*Task /){count++}
      END{print count+0}
    ' "$steering_dir/tasklist.md" 2>/dev/null)" || pending_count=0
  fi

  # Last error from worklog.md の `## Error Log` セクション配下のみを参照する。
  # 旧実装は worklog.md 全体の最終テーブル行を grab していたため、検証テーブル等を
  # "Last Error" として誤って表示していた。
  local last_error=""
  if [[ -f "$steering_dir/worklog.md" ]]; then
    last_error="$(awk '
      /^## Error Log/{found=1; next}
      found && /^## /{exit}
      found && /^\|/ && !/^\| *#/ && !/^\|[[:space:]]*[-—]/{last=$0}
      END{print last}
    ' "$steering_dir/worklog.md" 2>/dev/null | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
  fi

  # Quick Reboot テキストを組み立て
  local task_name
  task_name="$(basename "$steering_dir")"

  QUICK_REBOOT="[gdd:reboot] "
  QUICK_REBOOT+="Task: ${task_name}."
  [[ -n "$task_size" ]] && QUICK_REBOOT+=" Size: ${task_size}."
  [[ -n "$goal" ]] && QUICK_REBOOT+=" Goal: ${goal}."
  QUICK_REBOOT+=" Worktree: ${steering_wt}."
  QUICK_REBOOT+=" Phase: ${phase:-unknown}."
  QUICK_REBOOT+=" Next Action: ${next_action:-unknown}."
  QUICK_REBOOT+=" Gates: Requirements=${req_status:-unknown}, Human=${human_status:-unknown}, Design=${design_status:-unknown}."
  [[ -n "$route_in_progress" ]] && QUICK_REBOOT+=" Route In Progress: ${route_in_progress}."
  [[ -n "$current_task" ]] && QUICK_REBOOT+=" Current Task: ${current_task}."
  QUICK_REBOOT+=" Progress: ${completed_count} completed, ${pending_count} pending."
  [[ -n "$last_error" ]] && QUICK_REBOOT+=" Last Error: ${last_error}."
  [[ -n "$last_handoff" ]] && QUICK_REBOOT+=" Last Handoff: ${last_handoff}."
  [[ -n "$blocked_warning" ]] && QUICK_REBOOT+="$blocked_warning"
  # Completion detection: all tasks done → suggest gdd-completion-check instead of resume
  if [[ "$tasklist_is_canonical" == "true" && "$pending_count" -eq 0 && -z "$current_task" && "$completed_count" -gt 0 ]]; then
    QUICK_REBOOT+=" All tasks complete (${completed_count} done). Run \`gdd-completion-check\` to finalize and create verification evidence."
  else
    QUICK_REBOOT+=" To resume, use \`/gdd-dev\` or ask about the current task."
  fi
}

# エラーを握りつぶすが、stderr に diagnostic を出す
MULTI_STEERING_WARNING=""
if ! detect_active_steering 2>"${TMPDIR:-/tmp}/gdd-session-start-diag.log"; then
  # 複数 steering 検出時は警告を組み立てる（サイレントスキップしない）
  if [[ "$GDD_STEERING_STATUS" == "multiple" ]]; then
    MULTI_STEERING_WARNING="[gdd:warning] Active steering が ${#GDD_STEERING_CANDIDATES[@]} 件検出されました。"
    for _c in "${GDD_STEERING_CANDIDATES[@]}"; do
      MULTI_STEERING_WARNING+=" - ${_c}"
    done
    MULTI_STEERING_WARNING+=" /gdd-dev resume で再開する際に対象を 1 つに絞る必要があります（pre-push gate も steering-multiple を不足として実行後に通知します）。どれを終えるかユーザーに確認したうえで、使わない steering（PR が open のものは除く）は、削除も移動もせず、state.md の Resume From と Next Action をどちらも cancelled にしてください（手順: references/self-review-lanes.md § 使わないステアリングの終え方）。"
  fi
fi

# --- Session ID check: 別セッションからの steering は auto-resume を防ぐ ---
# SessionStart は一番強くモデルを色付けするため、現在 session id が取れる
# 場合は stored session_id との一致を要求する。一方、Codex / Cursor など
# session id が hook に渡らない runtime では session_id だけを hard blocker
# にしない。active steering 検出は current git worktree に限定済みなので、
# missing session id は soft warning として扱い、同一 worktree の自然再開
# （human-check の OK / 続けて等）を過抑制しない。
CURRENT_SESSION_ID="${CLAUDE_CODE_SESSION_ID:-}"
SESSION_CONTINUITY_NOTE=""
if [[ "$QUICK_REBOOT" == "[gdd:reboot]"* && -n "$GDD_STEERING_WT" ]]; then
  GDD_LOCAL_STATE="${GDD_STEERING_WT}/.claude/gdd-dev.local.md"
  GDD_TASK_NAME="$(basename "$GDD_STEERING_DIR")"
  STORED_SESSION_ID=""
  STORED_RESUME_FROM=""
  if [[ -f "$GDD_LOCAL_STATE" ]]; then
    # 末尾の空白・CR は落とす（`gdd_session_continuity_ok` と同じ。落とさないと、手で編集した・
    # 改行コードを変換した local state で、同じ session でも Candidate Mode が誤発火する）
    STORED_SESSION_ID="$(grep '^session_id:' "$GDD_LOCAL_STATE" 2>/dev/null | head -1 | sed 's/^session_id:[[:space:]]*//' | sed 's/[[:space:]]*$//')" || true
  fi
  if [[ -f "$GDD_STEERING_DIR/state.md" ]]; then
    STORED_RESUME_FROM="$(gdd_extract_doc_field "$GDD_STEERING_DIR/state.md" "Resume From")"
    STORED_RESUME_FROM="${STORED_RESUME_FROM%%|*}"
    STORED_RESUME_FROM="${STORED_RESUME_FROM%"${STORED_RESUME_FROM##*[![:space:]]}"}"
  fi
  CURRENT_BRANCH="$(git -C "$GDD_STEERING_WT" branch --show-current 2>/dev/null || true)"
  HEAD_EXISTS=false
  if git -C "$GDD_STEERING_WT" rev-parse --verify HEAD >/dev/null 2>&1; then
    HEAD_EXISTS=true
  fi
  if [[ "$HEAD_EXISTS" == "true" ]] && gdd_is_default_branch "$CURRENT_BRANCH"; then
    QUICK_REBOOT="[gdd:paused] Safe Resume Candidate Mode: A non-terminal GDD steering exists on the default branch (${CURRENT_BRANCH}), which usually means a merged or stale worktree was reused. Do NOT use stale task context for the user's current request. Run \`gdd-status\` to inspect safe resume candidates, or use \`/gdd-dev resume <target>\` after choosing the target."
  elif [[ "$HEAD_EXISTS" == "true" && -n "$CURRENT_BRANCH" && "$CURRENT_BRANCH" != *"$GDD_TASK_NAME"* && "$CURRENT_BRANCH" != *"${GDD_TASK_NAME#????????-}"* ]]; then
    QUICK_REBOOT="[gdd:paused] Safe Resume Candidate Mode: A GDD task exists, but the current branch (${CURRENT_BRANCH}) does not match the steering task (${GDD_TASK_NAME}). Do NOT use stale task context for the user's current request. Run \`gdd-status\` to inspect safe resume candidates, or use \`/gdd-dev resume <target>\` after choosing the target."
  elif [[ -z "$CURRENT_SESSION_ID" && -n "$STORED_SESSION_ID" && "$STORED_RESUME_FROM" != "human-check-waiting" ]]; then
    QUICK_REBOOT="[gdd:paused] Safe Resume Candidate Mode: A GDD task was paused with a stored session id, but the current session id is unavailable and the task is not at human-check-waiting. Do NOT use stale task context for the user's current request. Run \`gdd-status\` to inspect safe resume candidates, or use \`/gdd-dev resume <target>\` after choosing the target."
  elif [[ -z "$CURRENT_SESSION_ID" ]]; then
    SESSION_CONTINUITY_NOTE=" Session continuity: current session id unavailable; treating the single active steering in the current git worktree as a same-worktree resume candidate. If the user's prompt is unrelated, do not advance GDD."
  elif [[ -z "$STORED_SESSION_ID" || "$STORED_SESSION_ID" != "$CURRENT_SESSION_ID" ]]; then
    QUICK_REBOOT="[gdd:paused] Safe Resume Candidate Mode: A GDD task was paused in a different or unverifiable session. Do NOT use stale task context for the user's current request. Run \`gdd-status\` to inspect safe resume candidates, or use \`/gdd-dev resume <target>\` after choosing the target."
  fi
fi

# --- superpowers detection ---
SUPERPOWERS_DETECTED=false
for settings_file in \
  "${HOME}/.claude/settings.json" \
  ".claude/settings.json" \
  ".claude/settings.local.json"; do
  if [[ -f "$settings_file" ]]; then
    if grep -q '"superpowers' "$settings_file" 2>/dev/null; then
      SUPERPOWERS_DETECTED=true
      break
    fi
  fi
done

if [[ "$SUPERPOWERS_DETECTED" = false ]]; then
  for skill_dir in "${HOME}/.claude/skills/using-superpowers" "${HOME}/.claude/plugins/"*"/skills/using-superpowers"; do
    if [[ -d "$skill_dir" ]]; then
      SUPERPOWERS_DETECTED=true
      break
    fi
  done
fi

# --- Output ---
# Routing Contract Table and Escape Hatch are owned by skills/gdd-using-skills/SKILL.md.
# This hook only surfaces the current Routing reason at SessionStart.
if [[ -n "$QUICK_REBOOT" ]]; then
  # active steering あり: Quick Reboot + ガイダンス
  if [[ "$QUICK_REBOOT" == "[gdd:paused]"* ]]; then
    GUIDANCE="Paused guidance: gate-driven-development is available, but do not resume or summarize the old task automatically. Treat the user's current request normally. Use \`gdd-status\` to inspect safe resume candidates, then resume only with an explicit \`/gdd-dev resume <target>\` instruction."
  elif [[ "$SUPERPOWERS_DETECTED" = true ]]; then
    GUIDANCE="Routing reason: GDD active marker detected. Active GDD follow-up is GDD primary / superpowers advisory only; formal GDD auto-trigger stays disabled to avoid stale-task resume. Use state.md / tasklist.md / worklog.md as workflow owner, or gdd-status if unsure. If a Codex goal continuation conflicts with this reboot task, do not adopt the reboot task; resolve by Task Binding / PR / branch / worktree first. Project skills are verification tools, not workflow owners. Explicit standalone superpowers is allowed only for a separate non-GDD task."
  else
    # GDD は opt-in。reboot 情報は出すが、Claude が active steering を自分で再開しないよう
    # 「ユーザーが明示した時だけ」を文言で示す。
    GUIDANCE="gate-driven-development is available. The user can resume the active task with \`/gdd-dev\` or inspect it with \`gdd-status\`. Handle the user's current request normally — do not auto-resume GDD unless the user explicitly asks."
  fi
  # JSON escape
  CONTEXT="${QUICK_REBOOT}${SESSION_CONTINUITY_NOTE} ${GUIDANCE}"
  # dir 名・パス・state.md の値に混ざる制御文字・不正な UTF-8 は JSON を壊し、additionalContext 全体が落ちる。
  # gdd_truncate_chars（不正な UTF-8 を捨てる。上限は自分の長さなので切り詰めない）と
  # 制御文字の除去を通してからエスケープする。tr を LC_ALL=C にするのは、UTF-8 ロケールの BSD tr が不正な
  # バイト列で失敗し、set -e で hook 全体が出力無しで止まるため。CONTEXT は案内文を必ず含むので、空になったら
  # python3 の失敗（壊れた shim など）とみなし、制御文字の除去だけに戻す（不正な UTF-8 は残る）
  _sanitized="$(gdd_truncate_chars "$CONTEXT" "${#CONTEXT}" | LC_ALL=C tr -d '[:cntrl:]')"
  [[ -n "$_sanitized" ]] || _sanitized="$(printf '%s' "$CONTEXT" | LC_ALL=C tr -d '[:cntrl:]')"
  CONTEXT="$_sanitized"
  CONTEXT="${CONTEXT//\\/\\\\}"
  CONTEXT="${CONTEXT//\"/\\\"}"
  printf '{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"%s%s"}}\n' "$_last_failure_prefix" "$CONTEXT"
  _gdd_consume_last_failure_record
elif [[ -n "$MULTI_STEERING_WARNING" ]]; then
  # 複数 steering 検出: 警告 + 通常ガイダンス
  base_guidance="gate-driven-development is available. Use \`/gdd-dev <task>\` for formal development workflow."
  CONTEXT="${MULTI_STEERING_WARNING} ${base_guidance}"
  _sanitized="$(gdd_truncate_chars "$CONTEXT" "${#CONTEXT}" | LC_ALL=C tr -d '[:cntrl:]')"
  [[ -n "$_sanitized" ]] || _sanitized="$(printf '%s' "$CONTEXT" | LC_ALL=C tr -d '[:cntrl:]')"
  CONTEXT="$_sanitized"
  CONTEXT="${CONTEXT//\\/\\\\}"
  CONTEXT="${CONTEXT//\"/\\\"}"
  printf '{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"%s%s"}}\n' "$_last_failure_prefix" "$CONTEXT"
  _gdd_consume_last_failure_record
else
  # active steering なし: 初回向けガイダンス + 既存ガイダンス
  # .steering/ が存在するか確認（過去に使ったことがあるか）
  has_steering_history=false
  for wt in $(git worktree list --porcelain 2>/dev/null | grep '^worktree ' | sed 's/^worktree //'); do
    if [[ -d "$wt/.steering" ]]; then
      has_steering_history=true
      break
    fi
  done 2>/dev/null || true

  base_guidance=""
  if [[ "$SUPERPOWERS_DETECTED" = true ]]; then
    base_guidance="Routing reason: no active GDD marker detected. formal GDD auto-trigger is disabled. Use \`/gdd-dev <task>\` for formal workflow; use \`gdd-pre-workflow-brainstorming\` for GDD-adjacent planning. GDD natural-language planning intent stays GDD primary / superpowers advisory only; unrelated standalone work may use superpowers."
  elif [[ "$has_steering_history" = true ]]; then
    # 既存ユーザー: 簡潔な opt-in 案内のみ。Claude 側の判断で GDD を勧めない。
    base_guidance="gate-driven-development is available. Use \`/gdd-dev <task>\` when the user explicitly asks to start a formal workflow."
  else
    # 初回ユーザー: 機能の存在は伝えるが「使うかどうか」はユーザーに委ねる文言にする。
    base_guidance="gate-driven-development is available. The user can use \`/gdd-dev <task>\` to start a formal workflow (requirements → design → TDD → review; task size auto-detected) or \`gdd-status\` to inspect workflow state. Do not auto-trigger GDD — let the user opt in explicitly."
  fi

  # JSON escape
  base_guidance="${base_guidance//\\/\\\\}"
  base_guidance="${base_guidance//\"/\\\"}"
  printf '{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"%s%s"}}\n' "$_last_failure_prefix" "$base_guidance"
  _gdd_consume_last_failure_record
fi
