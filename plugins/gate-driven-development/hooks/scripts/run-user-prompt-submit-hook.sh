#!/usr/bin/env bash
set -euo pipefail

# UserPromptSubmit hook for gate-driven-development.
# Active steering がある場合、Current Task と Next Action を additionalContext に注入する。
# planning-with-files の UserPromptSubmit hook に相当し、session 途中のコンテキスト喪失を防ぐ。

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/kill-switch.sh"
gdd_kill_switch_active && exit 0
# payload の cwd（セッションの cwd）へ移してから steering・marker を探す
# shellcheck source=lib/payload-cwd.sh
source "$SCRIPT_DIR/lib/payload-cwd.sh"
gdd_enter_payload_cwd

# detect-steering.sh の source 前に GDD_STEERING_DIR を退避する。
# detect-steering.sh はグローバルスコープで GDD_STEERING_DIR="" を実行するため
# 環境変数が消去される。review cue チェック用に先に値を確保する。
_GDD_UPS_STEERING_DIR="${GDD_STEERING_DIR:-}"

# shellcheck source=lib/detect-steering.sh
source "$SCRIPT_DIR/lib/detect-steering.sh"
# shellcheck source=lib/classify-intent.sh
source "$SCRIPT_DIR/lib/classify-intent.sh"

# UserPromptSubmit payload を stdin から読む（prompt が無ければ空文字にフォールバック）
STDIN_JSON="$(cat 2>/dev/null || true)"
USER_PROMPT=""
if [[ -n "$STDIN_JSON" ]] && command -v python3 >/dev/null 2>&1; then
  USER_PROMPT="$(printf '%s' "$STDIN_JSON" | python3 -c 'import json,sys
try:
    print(json.load(sys.stdin).get("prompt",""), end="")
except Exception:
    pass
' 2>/dev/null || true)"
fi
# テスト環境では CLAUDE_USER_PROMPT 環境変数からフォールバック
[[ -z "$USER_PROMPT" ]] && USER_PROMPT="${CLAUDE_USER_PROMPT:-}"

# Manual merge continuation: PR 作成で GDD が done に到達した後でも、
# ユーザーの「mergeした」を post-merge / post-apply verification の再開 cue として扱う。
POST_MERGE_CONTINUATION_FILE=".claude/gdd-post-merge-continuation.json"
if [[ -f "$POST_MERGE_CONTINUATION_FILE" ]]; then
  if [[ "$USER_PROMPT" == *"mergeした"* || "$USER_PROMPT" == *"マージした"* || "$USER_PROMPT" == *"merged"* ]]; then
    continuation_context="[gdd:post-merge-continuation] Manual merge detected. Read ${POST_MERGE_CONTINUATION_FILE}, identify the merged PR and main workflows, respect Approved Direction/autonomy ceiling, wait for deploy/apply/CI, run read-only post-merge/post-apply verification, re-read state.md/tasklist.md if paths are available, and check remaining work before final. This cue authorizes read-only monitoring/verification only; do not perform new write operations without explicit approval."
    continuation_context="${continuation_context//\\/\\\\}"
    continuation_context="${continuation_context//\"/\\\"}"
    printf '{"hookSpecificOutput":{"hookEventName":"UserPromptSubmit","additionalContext":"%s"}}\n' "$continuation_context"
    exit 0
  fi
fi

# ---------------------------------------------------------------------------
# Review cue 検出: PR レビューコメントへの応答を自動起動する。
# 前提条件:
#   1. active steering が存在する（GDD_STEERING_DIR が確定している）
#   2. Resume From が対象 phase (gdd-implementation-gating / gdd-receiving-code-review / done)
#   3. USER_PROMPT がレビュー関連パターンにマッチする
# ---------------------------------------------------------------------------
REVIEW_CUE_HINT=""

_gdd_review_cue_check() {
  local _sdir="$1"
  [[ -n "$_sdir" ]] || return 1
  local _state="${_sdir}/state.md"
  [[ -f "$_state" ]] || return 1

  # Resume From が対象 phase かチェック（誤検出防止）
  local _resume_from
  _resume_from="$(gdd_extract_doc_field "$_state" "Resume From")"
  case "$_resume_from" in
    gdd-implementation-gating|gdd-receiving-code-review|done|external-review-waiting) ;;
    *) return 1 ;;
  esac

  # review cue パターン（日本語・英語）
  if printf '%s' "$USER_PROMPT" | grep -qiE '(レビュー).*(コメント|指摘|修正)|(コメント|指摘|修正).*(レビュー)'; then
    :
  elif printf '%s' "$USER_PROMPT" | grep -qiE '(PR|pull[._ -]request).*(comment|approved|changes[._ -]requested|review)|(review).*(comment)'; then
    :
  else
    return 1
  fi

  # フラグをセットするのみ。exit はしない（既存 OT-F3 B1 ロジックに合流させる）
  REVIEW_CUE_HINT="[gdd:review-cue-detected] PR レビューコメントへの対応を開始します。gdd-pr-review-followup を使ってください。"
  return 0
}

# _GDD_UPS_STEERING_DIR が環境変数で渡された場合の早期 review cue チェックパス。
# テスト環境用（gdd_detect_active_steering は git に依存するため）。
if [[ -n "$_GDD_UPS_STEERING_DIR" ]]; then
  _gdd_review_cue_check "$_GDD_UPS_STEERING_DIR" || true
  if [[ -n "$REVIEW_CUE_HINT" ]]; then
    _cue_msg="${REVIEW_CUE_HINT//\\/\\\\}"
    _cue_msg="${_cue_msg//\"/\\\"}"
    printf '{"hookSpecificOutput":{"hookEventName":"UserPromptSubmit","additionalContext":"%s"}}\n' "$_cue_msg"
    exit 0
  fi
fi

# 毎ターンの注入（`[gdd:blocked]`・複数 steering の警告を含む）は、このセッションの GDD の印が
# cwd の repo にあるときだけにする（`gdd_session_marker_present`）。印の無いセッション（root checkout
# で別の作業をしているなど）に、残った steering から毎ターン注入しない。上の post-merge と
# review cue の経路は、残った steering の注入ではないので前に置いたまま。
if ! gdd_session_marker_present "$(git rev-parse --show-toplevel 2>/dev/null)/.claude/gdd-dev.local.md"; then
  exit 0
fi

# active steering を検出（なければ何も注入しない）
if ! gdd_detect_active_steering; then
  # 複数 steering 検出時は intent を見て警告を分岐
  if [[ "$GDD_STEERING_STATUS" == "multiple" ]]; then
    count="${#GDD_STEERING_CANDIDATES[@]}"
    intent="$(gdd_classify_intent "$USER_PROMPT")"
    case "$intent" in
      new)
        warning="[gdd:info] Active steering が ${count} 件ありますが、入力は新規タスクと判定しました。既存を再開する場合は 再開/続き/resume を指示に含めてください。"
        ;;
      resume)
        warning="[gdd:warning] Resume 指示を検出。Active steering が ${count} 件あるため、/gdd-dev resume <対象> で対象を 1 つに絞ってください。"
        ;;
      *)
        warning="[gdd:warning] Active steering が ${count} 件あり、指示が新規/再開のどちらか曖昧です。/gdd-dev <新規タスク> または /gdd-dev resume <対象> を明示してください。"
        ;;
    esac
    warning="${warning//\\/\\\\}"
    warning="${warning//\"/\\\"}"
    printf '{"hookSpecificOutput":{"hookEventName":"UserPromptSubmit","additionalContext":"%s"}}\n' "$warning"
  fi
  exit 0
fi

# Cross-session guard: do not inject GDD context for `.claude/gdd-dev.local.md`
# files created in a different Claude Code session. Without this check, a stale
# state file (e.g. from a prior session that crashed before terminal cleanup)
# causes every user prompt — even unrelated URLs or chit-chat — to receive
# `[gdd] Goal/Current Task/AC` context. That coloring is the second-order cause
# of GDD misfires.
if ! gdd_session_continuity_ok "${GDD_STEERING_WT}/.claude/gdd-dev.local.md"; then
  exit 0
fi

# 3-field gate check（tasklist が canonical かどうか）
gdd_check_3field_gate
if ! gdd_validate_active_state_fields; then
  blocked_context="[gdd:blocked] ${GDD_ACTIVE_STATE_ERROR} Do NOT continue the active /gdd-dev run until the canonical fields are restored."
  blocked_context="${blocked_context//$'\n'/ }"
  blocked_context="${blocked_context//\\/\\\\}"
  blocked_context="${blocked_context//\"/\\\"}"
  printf '{"hookSpecificOutput":{"hookEventName":"UserPromptSubmit","additionalContext":"%s"}}\n' "$blocked_context"
  exit 0
fi

# 通常フロー: active steering 検出後の review cue チェック
# （早期パスで処理済みの場合は _GDD_UPS_STEERING_DIR が非空なので既に exit 済み）
if [[ -z "$_GDD_UPS_STEERING_DIR" ]]; then
  _gdd_review_cue_check "$GDD_STEERING_DIR" || true
fi

# Current Task, AC, Next Action を抽出
current_task=""
current_ac=""
current_task_ac_ids=""
next_action=""
goal=""
ac_coverage_health=""

if [[ "$GDD_TASKLIST_CANONICAL" == "true" ]]; then
  current_task="$(awk '/^## Current Task/{found=1;next} found && /^### Task:/{print; exit} found && /^##/{exit}' "$GDD_STEERING_DIR/tasklist.md" 2>/dev/null | sed 's/^### Task:[[:space:]]*//')" || true
  next_action="$(gdd_extract_doc_field "$GDD_STEERING_DIR/tasklist.md" "Next Action")"; next_action="${next_action%%[ |]*}"
  current_task_ac_ids="$(awk '/^## Current Task/{found=1;next} found && /^## /{exit} found {print}' "$GDD_STEERING_DIR/tasklist.md" 2>/dev/null | grep -Eo 'AC-[A-Za-z]?[0-9]+[a-z]?' | sort -u | tr '\n' ',' | sed 's/,/, /g;s/, $//')" || true
  # AC 詳細を全行収集
  current_ac="$(awk '/^## Current Task/{found=1;next} found && /^## /{exit} found && /^- *AC-[0-9]+/{sub(/^- */, ""); printf "%s; ", $0}' "$GDD_STEERING_DIR/tasklist.md" 2>/dev/null | sed 's/; $//')" || true
  # 旧形式フォールバック
  if [[ -z "$current_ac" ]]; then
    current_ac="$(awk '/^## Current Task/{found=1;next} found && /^## /{exit} found && /^- AC:/{sub(/^- AC: */, ""); print; exit}' "$GDD_STEERING_DIR/tasklist.md" 2>/dev/null)" || true
  fi
  # Covers AC / Planned RED / E2E などに AC ID があるが `- AC:` 行が無い場合の fallback。
  # context compact 後に AC が削れて見えるのを防ぐため、Current Task 内の AC ID set を注入する。
  if [[ -n "$current_task_ac_ids" ]]; then
    current_ac="$current_task_ac_ids"
  fi
fi

# Next Action の fallback: state.md の Resume From（`=` / `: ` 両形式・箇条書きに対応するため helper を使う）
if [[ -z "$next_action" && -n "$GDD_GATE_FILE" ]]; then
  next_action="$(gdd_extract_doc_field "$GDD_GATE_FILE" "Resume From")"
  next_action="${next_action%%[ |]*}"
fi

# Route In Progress（差し戻し route の文脈）。
# `gdd_validate_active_state_fields`（上で既に成功済み）が同じ `state.md` から
# 読んだ値を再利用する。ここで改めて `gdd_extract_route_in_progress` を呼ぶと、
# 同じファイルに対して python3 をもう一度起動することになる（独立レビュー
# 実測、2026-09-04）。この再利用が成立するのは、validate が成功した時点で
# `state.md` の存在が確定しており、`GDD_GATE_FILE` もそのとき常に
# `state.md` を指すため（`gdd_check_3field_gate` は state.md を design.md より
# 優先する）。
route_in_progress="$GDD_ACTIVE_STATE_ROUTE_IN_PROGRESS"
[[ "$route_in_progress" == "none" ]] && route_in_progress=""

# context source field（state-field-tiers.md）。
# 新しいセッションで再開する場合、SessionStart の active steering パスは routing 指示しか出さず、
# state.md の中身を注入する場所はここだけ。routing だけでは「何をしていたか」「どの方針で
# 承認されたか」が復元されないため、context field の 2 つを注入する。compaction の後も、
# 次のユーザー入力でここから同じ 2 field が入る（compaction の直後の SessionStart は何も出さない）。
handoff_summary=""
approved_direction=""
if [[ -n "$GDD_GATE_FILE" ]]; then
  handoff_summary="$(gdd_extract_doc_field "$GDD_GATE_FILE" "Last Handoff Summary")"
  approved_direction="$(gdd_extract_doc_field "$GDD_GATE_FILE" "Approved Direction")"
  # sanitize: 自由記述なので長さ制限と制御文字除去（additionalContext の JSON 破損防止）。
  # 長さ制限は `${var:0:N}` ではなく gdd_truncate_chars を使う。`${var:0:N}` は locale 依存で
  # C ロケール／ロケール未設定ではバイト単位になり、日本語を途中で切って JSON を壊す。
  handoff_summary="$(gdd_truncate_chars "$handoff_summary" 512 | tr -d '[:cntrl:]')"
  approved_direction="$(gdd_truncate_chars "$approved_direction" 512 | tr -d '[:cntrl:]')"
fi

# OT-F3 B2: PR レビュー再レビュー待ちの状態で resume したら、planning でなく followup を継続させる。
# 抽出は既存 helper に統一（`=` / `: ` 両形式対応・行頭トリム済み）。本文中の誤ヒットも避けられる。
pr_followup_status=""
if [[ -n "$GDD_GATE_FILE" ]]; then
  pr_followup_status="$(gdd_extract_doc_field "$GDD_GATE_FILE" "PR Review Follow-up Status")"
  pr_followup_status="${pr_followup_status%%[ |]*}"  # 末尾メタ（| evidence: ...）と空白を除去
fi

# goal (Summary Brief の一言)
if [[ -f "$GDD_STEERING_DIR/requirements.md" ]]; then
  goal="$(grep -A1 '### 一言' "$GDD_STEERING_DIR/requirements.md" 2>/dev/null | tail -1 | sed 's/^[[:space:]]*//')" || true
  if [[ "$GDD_TASKLIST_CANONICAL" == "true" ]]; then
    req_ac_count="$(grep -Eo 'AC-[A-Za-z]?[0-9]+[a-z]?' "$GDD_STEERING_DIR/requirements.md" 2>/dev/null | sort -u | wc -l | tr -d ' ')" || req_ac_count="0"
    task_ac_count="0"
    if [[ -n "$current_task_ac_ids" ]]; then
      task_ac_count="$(printf '%s\n' "$current_task_ac_ids" | grep -Eo 'AC-[A-Za-z]?[0-9]+[a-z]?' | sort -u | wc -l | tr -d ' ')" || task_ac_count="0"
    fi
    if [[ "${req_ac_count:-0}" -gt 0 || "${task_ac_count:-0}" -gt 0 ]]; then
      ac_coverage_health="AC Coverage Health: requirements expected ${req_ac_count:-0}; current task injected ${task_ac_count:-0}."
    fi
  fi
fi

# 何も取れなければ注入不要
[[ -z "$current_task" && -z "$next_action" ]] && exit 0

# 直近のエラー（tasklist.md の Current Task 内 Attempts セクションから最新 1 件）
recent_error=""
if [[ "$GDD_TASKLIST_CANONICAL" == "true" ]]; then
  recent_error="$(awk '/^## Current Task/{ct=1;next} ct && /^## /{exit} ct && /^#### (Attempts|試行記録)/{at=1;next} at && /^(####|###)/{at=0} at && /^- /{last=$0} END{if(last) {sub(/^- /,"",last); print last}}' "$GDD_STEERING_DIR/tasklist.md" 2>/dev/null)" || true
fi

# findings.md 永続化リマインダー（findings.md の最終更新からの経過をチェック）
findings_reminder=""
if [[ -f "$GDD_STEERING_DIR/findings.md" ]]; then
  # cross-platform: macOS uses stat -f %m, Linux uses stat -c %Y
  if [[ "$(uname)" == "Darwin" ]]; then
    findings_mtime=$(stat -f %m "$GDD_STEERING_DIR/findings.md" 2>/dev/null || echo "$(date +%s)")
  else
    findings_mtime=$(stat -c %Y "$GDD_STEERING_DIR/findings.md" 2>/dev/null || echo "$(date +%s)")
  fi
  findings_age=$(( $(date +%s) - findings_mtime ))
  # 10〜30 分の間だけリマインダー（30 分超は調査終了とみなし発火停止）
  if [[ $findings_age -gt 600 ]] && [[ $findings_age -le 1800 ]]; then
    findings_reminder="調査結果があれば findings.md に書き出す"
  fi
fi

# OT-F3 B1: PR レビュー対応の発話を検知して gdd-pr-review-followup へ誘導するヒントを足す。
# PR 参照（pull URL / #番号 / PR・プルリク）とレビュー動詞（レビュー/指摘/review/feedback）の両方が揃ったときだけ発火。
pr_review_followup_hint=""
if printf '%s' "$USER_PROMPT" | grep -qiE '(github\.com/[^[:space:]]+/pull/[0-9]+|pull request|プルリク|#[0-9]+|(^|[^[:alnum:]_])PR([^[:alnum:]_]|$))' \
   && printf '%s' "$USER_PROMPT" | grep -qiE '(レビュー|指摘|review|feedback)'; then
  pr_review_followup_hint="[gdd:pr-review-followup] PR review feedback detected — gdd-pr-review-followup skill を使う（collect→classify→verify→route→fix→push→re-review 待ち）。"
fi

# additionalContext を組み立て（goal + task + AC + next action + error + reminder）
context="[gdd]"
[[ -n "$goal" ]] && context+=" Goal: ${goal}."
[[ -n "$current_task" ]] && context+=" Current Task: ${current_task}."
[[ -n "$current_ac" ]] && context+=" AC: ${current_ac}."
[[ -n "$ac_coverage_health" ]] && context+=" ${ac_coverage_health}"
[[ -n "$next_action" ]] && context+=" Next Action: ${next_action}."
[[ -n "$route_in_progress" ]] && context+=" Route In Progress: ${route_in_progress}."
[[ -n "$approved_direction" ]] && context+=" Approved Direction: ${approved_direction}."
[[ -n "$handoff_summary" ]] && context+=" Last Handoff Summary: ${handoff_summary}."
[[ -n "$recent_error" ]] && context+=" Last Error: ${recent_error}."
[[ -n "$findings_reminder" ]] && context+=" Reminder: ${findings_reminder}."
[[ -n "$REVIEW_CUE_HINT" ]] && context+=" ${REVIEW_CUE_HINT}"
[[ -n "$pr_review_followup_hint" ]] && context+=" ${pr_review_followup_hint}"
case "$pr_followup_status" in
  pushed_waiting_re_review|waiting_for_review|changes_requested)
    context+=" [gdd:pr-review-followup] PR Review Follow-up Status=${pr_followup_status} — planning でなく gdd-pr-review-followup を継続する。" ;;
esac

# Plan mode guard: 実装完了後の修正指示で Plan mode に遷移するのを防ぐ
# Next Action が terminal (done/gdd-completion-check) のとき、same-session correction を明示する
if [[ "$next_action" == "done" || "$next_action" == "gdd-completion-check" || "$next_action" == "cancelled" ]]; then
  context+=" [plan-mode-guard] GDD session がまだ active です。Plan mode・EnterPlanMode は使用禁止。修正は same-session correction (implementation_fix_only / gdd-requirements-amendment) で対応してください。"
fi

# JSON escape: strip newlines first (AC or error may contain them), then escape
context="${context//$'\n'/ }"
context="${context//\\/\\\\}"
context="${context//\"/\\\"}"

printf '{"hookSpecificOutput":{"hookEventName":"UserPromptSubmit","additionalContext":"%s"}}\n' "$context"
