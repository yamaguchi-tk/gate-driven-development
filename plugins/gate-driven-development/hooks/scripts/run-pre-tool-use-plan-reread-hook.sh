#!/usr/bin/env bash
set -euo pipefail

# PreToolUse hook for gate-driven-development.
# Write/Edit/MultiEdit/ApplyPatch 実行前に Goal + Current Task + AC 詳細を再注入する。
# planning-with-files の preToolUse hook（先頭 30 行注入）と Manus の
# "Manipulate Attention Through Recitation" 原則に相当。
# ~50 tool calls 後の goal drift と AC 見失いを構造的に防ぐ。

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/kill-switch.sh"
gdd_kill_switch_active && exit 0
# payload の cwd（セッションの cwd）へ移してから steering・marker を探す
# shellcheck source=lib/payload-cwd.sh
source "$SCRIPT_DIR/lib/payload-cwd.sh"
gdd_enter_payload_cwd
# shellcheck source=lib/detect-steering.sh
source "$SCRIPT_DIR/lib/detect-steering.sh"

# active steering を検出（なければ何も注入しない）
gdd_detect_active_steering || exit 0

# Cross-session guard: skip context re-injection unless the active steering's
# repo has this session's GDD marker (`gdd_session_marker_present`). Without this
# check, every Write/Edit during an unrelated chat re-injects `[gdd:build]`
# context for a stale task — the same misfire pattern as UserPromptSubmit.
if ! gdd_session_marker_present "${GDD_STEERING_WT}/.claude/gdd-dev.local.md"; then
  exit 0
fi

# tasklist.md が無ければ build phase ではないので注入不要
[[ -f "$GDD_STEERING_DIR/tasklist.md" ]] || exit 0

# 3-field gate check（canonical でなければ注入不要）
gdd_check_3field_gate
[[ "$GDD_TASKLIST_CANONICAL" == "true" ]] || exit 0

# Goal（Summary Brief の一言）を抽出
goal=""
if [[ -f "$GDD_STEERING_DIR/requirements.md" ]]; then
  goal="$(grep -A1 '### 一言' "$GDD_STEERING_DIR/requirements.md" 2>/dev/null | tail -1 | sed 's/^[[:space:]]*//')" || true
fi

# Current Task セクション全体を抽出（タスク名 + 全 AC）
current_task=""
ac_lines=""

# 正準形は `### Task: <name>`（references/task-breakdown-steps.md のテンプレート）だが、
# 実データの Current Task 節にはこの形式が無く、`### Task <N>: <name>` と
# `- Task: <name>` が多数派だった。厳密一致では current_task が空になり
# hook 全体が silent exit するため、一度も注入されていなかった。
# 読み手は実在する形式を受理し、書き手は正準形に寄せる（gate 判定の区切りを `:` と `=` の両方で読むようにしたのと同じ方針）。
# bash の正規表現はコメント文字を含むためリテラルではなく変数で渡す。
_task_heading_re='^(#{2,4}|[-*])[[:space:]]*Task[[:space:]]*[0-9]*[[:space:]]*:[[:space:]]*(.+)$'
# `- AC: ...`（正準）と `- Covers AC: ...`（task-breakdown-steps.md が legacy alias として
# 読んでよいと明記している形式）の両方を受理する。
_ac_field_re='^[-*][[:space:]]*(Covers[[:space:]]+)?AC:[[:space:]]*(.+)$'

in_current=false
while IFS= read -r line; do
  if [[ "$line" == "## Current Task"* ]]; then
    in_current=true
    continue
  fi
  if [[ "$in_current" == true ]]; then
    if [[ "$line" == "## "* ]]; then
      break
    fi
    # 最初に見つかった task 見出しを採用する（後続の sub-heading で上書きしない）
    if [[ -z "$current_task" && "$line" =~ $_task_heading_re ]]; then
      current_task="${BASH_REMATCH[2]}"
    fi
    # AC-N 形式の行を全て収集（複数 AC 対応）
    if [[ "$line" =~ ^-\ *(AC-[0-9]+) ]]; then
      ac_line="${line#*- }"
      if [[ -n "$ac_lines" ]]; then
        ac_lines+="; ${ac_line}"
      else
        ac_lines="${ac_line}"
      fi
    fi
    # `- AC: ...` / `- Covers AC: ...`（legacy alias）のフォールバック
    if [[ -z "$ac_lines" && "$line" =~ $_ac_field_re ]]; then
      ac_lines="${BASH_REMATCH[2]}"
    fi
  fi
done < "$GDD_STEERING_DIR/tasklist.md"

# Current Task が無ければ注入不要
[[ -z "$current_task" ]] && exit 0

# 直近のエラー履歴を抽出（tasklist.md の Current Task 内 Attempts セクション）
recent_errors=""
in_current=false
in_attempts=false
while IFS= read -r line; do
  if [[ "$line" == "## Current Task"* ]]; then
    in_current=true
    continue
  fi
  if [[ "$in_current" == true ]]; then
    if [[ "$line" == "## "* && "$line" != "## Current Task"* ]]; then
      break
    fi
    if [[ "$line" == "#### Attempts"* || "$line" == "#### 試行記録"* ]]; then
      in_attempts=true
      continue
    fi
    if [[ "$in_attempts" == true ]]; then
      if [[ "$line" == "####"* || "$line" == "###"* ]]; then
        in_attempts=false
        continue
      fi
      if [[ "$line" =~ ^-\ .+ && ${#recent_errors} -lt 300 ]]; then
        if [[ -n "$recent_errors" ]]; then
          recent_errors+="; ${line#*- }"
        else
          recent_errors="${line#*- }"
        fi
      fi
    fi
  fi
done < "$GDD_STEERING_DIR/tasklist.md"

# findings.md の直近エントリを抽出（最新 3 件、各 1 行目のみ）
recent_findings=""
if [[ -f "$GDD_STEERING_DIR/findings.md" ]]; then
  recent_findings="$(awk '/^### /{count++; if(count>3) exit; sub(/^### /,""); printf "%s; ", $0}' "$GDD_STEERING_DIR/findings.md" 2>/dev/null | sed 's/; $//')" || true
fi

# Last Handoff Summary の記入状況を確認する。
# compaction や別セッションの後に作業内容を戻せる唯一の context source だが、reference と skill の
# 指示だけでは守られず、実運用ではほとんど書かれていなかった。既に build 中の注入が
# 走っているこの hook で、欠落時だけ一行促す（新しい hook は追加しない）。
handoff=""
if [[ -f "$GDD_STEERING_DIR/state.md" ]]; then
  handoff="$(gdd_extract_doc_field "$GDD_STEERING_DIR/state.md" "Last Handoff Summary")" || true
fi

# additionalContext を組み立て（goal + task + AC 詳細 + errors + findings）
context="[gdd:build]"
[[ -n "$goal" ]] && context+=" Goal: ${goal}."
context+=" Task: ${current_task}."
[[ -n "$ac_lines" ]] && context+=" AC: ${ac_lines}."
[[ -n "$recent_errors" ]] && context+=" Past Attempts: ${recent_errors}."
[[ -n "$recent_findings" ]] && context+=" Key Findings: ${recent_findings}."
[[ -z "$handoff" ]] && context+=" NOTE: state.md の Last Handoff Summary が未記入。次の phase 遷移時に「どこまで進み次に何をするか」を1行で書く（compaction や別セッションの後に「何をしていたか」を戻せる唯一の field）。"

# JSON escape
context="${context//\\/\\\\}"
context="${context//\"/\\\"}"
# 改行を除去（AC 行に改行が混入する場合の安全策）
context="${context//$'\n'/ }"

# Ctx-1: time-windowed dedup。compaction 後の再注入は残しつつ、同一内容の連続注入を抑制する。
# 同一 context かつ前回注入から WINDOW 秒以内なら skip。内容が変わるか WINDOW を超えたら再注入。
# WINDOW=0 は常に再注入（anti-compaction の安全弁）。内部エラーは fail-open（注入する）。
dedup_window="${GDD_PLAN_REREAD_DEDUP_WINDOW:-90}"
# 1〜7 桁の数字以外（例: "90s" / 極端に長い値）は算術エラーを避けるため既定値に正規化する。
[[ "$dedup_window" =~ ^[0-9]{1,7}$ ]] || dedup_window=90
# base-10 で正規化（"00"/"09" 等の先頭ゼロを 0/9 にし、下の 0 判定を文字列比較に依存させない）。
dedup_window=$((10#$dedup_window))
cache_file="${GDD_STEERING_WT}/.claude/.gdd-plan-reread-cache"
# date / cksum が失敗したら空にして、下のガード（整数判定 / 非空判定）で dedup を回避＝注入する（fail-open）。
now_epoch="$(date +%s 2>/dev/null || true)"
ctx_hash="$(printf '%s' "$context" | cksum 2>/dev/null | cut -d' ' -f1 || true)"
if [[ "$dedup_window" != "0" && -n "$ctx_hash" && -f "$cache_file" ]]; then
  last_epoch="$(sed -n '1p' "$cache_file" 2>/dev/null || true)"
  last_hash="$(sed -n '2p' "$cache_file" 2>/dev/null || true)"
  if [[ "$last_hash" == "$ctx_hash" && "$last_epoch" =~ ^[0-9]+$ && "$now_epoch" =~ ^[0-9]+$ ]]; then
    # base-10 を強制（先頭ゼロの値が 8 進数解釈されて算術エラーになるのを防ぐ）。
    # 「WINDOW 秒以内」は境界含む（<=）。
    if (( 10#$now_epoch - 10#$last_epoch <= 10#$dedup_window )); then
      exit 0  # identical context within window → dedup（再注入しない）
    fi
  fi
fi
# 注入してキャッシュを更新する。now_epoch / ctx_hash が有効なときだけ更新し、
# date / cksum が一時失敗したときに無効値で上書きして次回 dedup を壊さないようにする。
if [[ "$now_epoch" =~ ^[0-9]+$ && -n "$ctx_hash" ]]; then
  mkdir -p "$(dirname "$cache_file")" 2>/dev/null || true
  printf '%s\n%s\n' "$now_epoch" "$ctx_hash" > "$cache_file" 2>/dev/null || true
fi

printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","additionalContext":"%s"}}\n' "$context"
