#!/usr/bin/env bash
# pre-PR gate・pre-push gate が要求する帳簿の行の判定（述語）。merge gate も引き継ぎの判定を使う。
#
# hook（run-pre-pr-gate-hook.sh・run-pre-push-gate-hook.sh・run-merge-gate-hook.sh）と、push・PR の前の検算
# スクリプト（scripts/check-gate-ledger.sh）の両方がここを呼ぶ。述語を二か所に書かない。
# 制御の流れ（どの Task Size でどの行を要求するか）と block 文言は hook に残す。
#
# source した時点で処理を走らせない（関数の定義だけ）。top-level の処理が失敗すると、
# PreToolUse の hook が無出力で終わり、検査をせずに通してしまう。
# gdd_extract_doc_field・gdd_value_head（lib/detect-steering.sh）を先に source しておくこと。

# Task Size の生の値を正規化する。未知値・部分一致は fail-closed 側の standard に畳む。
gdd_normalize_task_size() {
  local _size
  _size="$(printf '%s' "$1" | LC_ALL=C tr '[:upper:]' '[:lower:]' | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')"
  case "$_size" in
    trivial | "quick (express)" | "quick (standard)" | standard) ;;
    *) _size="standard" ;;
  esac
  printf '%s' "$_size"
}

# state.md の Task Size を読んで正規化する。読めない state.md で awk が失敗しても、
# set -e で hook ごと落ちない（落ちると検査されずに通る）。読めなければ standard。
gdd_state_task_size() {
  local _raw=""
  if [[ -r "$1" ]]; then
    _raw="$(gdd_extract_doc_field "$1" "Task Size" 2>/dev/null || true)"
  fi
  gdd_normalize_task_size "$_raw"
}

# 正規化した Task Size が dry（と standard の Independent Review）を要求するか。
gdd_task_size_requires_dry() {
  case "$1" in
    trivial | "quick (express)" | "quick (standard)") return 1 ;;
  esac
  return 0
}

# PR の前の Next Action。tasklist.md を先に、空なら state.md を読む（値はそのまま返す）。
gdd_pr_next_action() {
  local _dir="$1" _value=""
  if [[ -f "$_dir/tasklist.md" ]]; then
    _value="$(gdd_extract_doc_field "$_dir/tasklist.md" "Next Action")"
  fi
  if [[ -z "$_value" && -f "$_dir/state.md" ]]; then
    _value="$(gdd_extract_doc_field "$_dir/state.md" "Next Action")"
  fi
  printf '%s' "$_value"
}

# PR の diff の base ref を解決する。base_branch が空なら、current branch の
# gh-merge-base、それも無ければ既定の候補を順に見る。解決できなければ空を返す。
gdd_resolve_base_ref() {
  local root="$1" base_branch="$2" current_branch="" candidates=() candidate ref=""
  if [[ -z "$base_branch" ]]; then
    current_branch="$(git -C "$root" branch --show-current 2>/dev/null || true)"
    if [[ -n "$current_branch" ]]; then
      base_branch="$(git -C "$root" config --get "branch.${current_branch}.gh-merge-base" 2>/dev/null || true)"
    fi
  fi
  if [[ -n "$base_branch" ]]; then
    if [[ "$base_branch" == origin/* || "$base_branch" == refs/* ]]; then
      candidates=("$base_branch")
    else
      candidates=("origin/${base_branch}" "$base_branch")
    fi
  else
    candidates=(origin/HEAD origin/main origin/master origin/trunk main master trunk develop)
  fi
  for candidate in "${candidates[@]}"; do
    if git -C "$root" rev-parse --verify "${candidate}^{commit}" >/dev/null 2>&1; then
      ref="$candidate"
      break
    fi
  done
  printf '%s' "$ref"
}

# ADR distilled の値の先頭の語（小文字）。`yes` / `not_applicable` 以外は不足として扱う。
gdd_adr_status() {
  printf '%s' "$1" | sed 's/[|[:space:]].*$//' | LC_ALL=C tr '[:upper:]' '[:lower:]'
}

# ADR distillation reason が空なら、ADR distilled の値の `reason:` の後ろを理由にする。
gdd_adr_reason() {
  local reason="$1" distilled="$2"
  if [[ -z "$reason" && "$distilled" == *"reason:"* ]]; then
    reason="$(printf '%s' "$distilled" | sed 's/.*reason:[[:space:]]*//')"
  fi
  printf '%s' "$reason"
}

gdd_pr_diff_has_adr() {
  local root="$1" base_ref="$2"
  git -C "$root" diff --name-only --diff-filter=ACMRT "${base_ref}...HEAD" 2>/dev/null \
    | grep -Eq '^docs/adr/[^/]+\.md$'
}

# state.md に `Decision Handoff`（`references/independent-review.md` の (3-f) で後続の test の要件を
# Issue に申し送った印）があるか。値は使わない presence 専用で、fence・字下げ・大文字小文字を問わず
# 文字列があれば「ある」とする（値が空の行・子の行に書いた値も含む）。gdd_extract_doc_field の
# 空値・fence の規約は変えない。grep のエラー（rc >= 2）も「ある」側に倒す。
gdd_state_has_decision_handoff() {
  local state="$1" rc=0
  grep -qiF -- 'decision handoff' "$state" 2>/dev/null || rc=$?
  [[ "$rc" -ne 1 ]]
}

# not_applicable を許すか。第 3 引数は state.md のパス。パスが無い・読めない通常ファイルでないとき、
# または申し送りがあるときは、Task Size・理由によらず許さない。拒んだ理由は GDD_ADR_NA_REASON に置く
# （handoff / state-unreadable / reason）。
gdd_adr_not_applicable_allowed() {
  local task_size="${1:-}"
  local reason="${2:-}"
  local state="${3:-}"
  local size_normalized reason_normalized
  GDD_ADR_NA_REASON=""
  if [[ -z "$state" || ! -f "$state" || ! -r "$state" ]]; then
    GDD_ADR_NA_REASON="state-unreadable"
    return 1
  fi
  if gdd_state_has_decision_handoff "$state"; then
    GDD_ADR_NA_REASON="handoff"
    return 1
  fi
  size_normalized="$(printf '%s' "$task_size" | LC_ALL=C tr '[:upper:]' '[:lower:]' | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')"
  case "$size_normalized" in
    trivial|"quick (express)")
      return 0
      ;;
  esac
  reason_normalized="$(printf '%s' "$reason" | LC_ALL=C tr '[:upper:]' '[:lower:]' | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')"
  case "$reason_normalized" in
    "重要判断なし"|"trivial"|"quick express")
      return 0
      ;;
  esac
  GDD_ADR_NA_REASON="reason"
  return 1
}

# 証跡の sha（7〜40 桁）を commit に解決し、期待する full sha と一致するか。
# 解決できない・曖昧な prefix は一致としない（fail-closed）。
gdd_evidence_sha_matches() {
  local root="$1" evidence_sha="$2" expected="$3" resolved=""
  [[ -n "$evidence_sha" && -n "$expected" ]] || return 1
  resolved="$(git -C "$root" rev-parse --quiet --verify "${evidence_sha}^{commit}" 2>/dev/null || true)"
  [[ -n "$resolved" && "$resolved" == "$expected" ]]
}

# `Independent Review` の sha（$3）が比較先（$4。push 対象の tip か HEAD）と一致しないときに、
# `Independent Review Carry` 行で引き継げるか（正本: references/self-review-lanes.md
# § Independent Review の引き継ぎ）。行の書式を確かめた後、条件は lib/ir_merge_carry.py が
# git から計算し直す（`verified` の自己申告は判定に使わない）。引き継げないときの理由を
# GDD_IR_CARRY_REASON に置く。どの失敗も 1（引き継がない）を返す。$5 は shell の起動から
# 数えた持ち時間の秒数（既定 8。hook の timeout 10 秒から block の出力の分を引いた値）。
# timeout の無い検算は大きい値を渡す。
# gdd_parse_merge_gate_field（lib/merge-gate-evidence.sh）と _gdd_sr_top_value
# （lib/self-review-evidence.sh）を先に source しておくこと。
gdd_ir_carry_matches() {
  local root="$1" state="$2" ir_sha="$3" expected="$4" allowance="${5:-8}"
  local line="" carry_sha="" from="" verified="" at="" ir_full="" base_ref=""
  GDD_IR_CARRY_REASON=""
  line="$(gdd_extract_doc_field "$state" "Independent Review Carry" 2>/dev/null || true)"
  line="${line%%$'\n'*}"
  if [[ -z "$line" ]]; then
    GDD_IR_CARRY_REASON="Independent Review Carry が無い"
    return 1
  fi
  carry_sha="$(_gdd_sr_top_value "$line" sha)"
  from="$(_gdd_sr_top_value "$line" from)"
  verified="$(_gdd_sr_top_value "$line" verified)"
  at="$(_gdd_sr_top_value "$line" at)"
  if ! _gdd_mg_is_hex_sha "$carry_sha" || ! _gdd_mg_is_hex_sha "$from" \
    || [[ "$verified" != "diff-equal" ]] || ! _gdd_mg_iso_to_epoch "$at" >/dev/null; then
    GDD_IR_CARRY_REASON="Independent Review Carry の書式が不正"
    return 1
  fi
  if ! gdd_evidence_sha_matches "$root" "$carry_sha" "$expected"; then
    GDD_IR_CARRY_REASON="Independent Review Carry の sha が比較先と一致しない"
    return 1
  fi
  ir_full="$(git -C "$root" rev-parse --quiet --verify "${ir_sha}^{commit}" 2>/dev/null || true)"
  if [[ -z "$ir_full" ]] || ! gdd_evidence_sha_matches "$root" "$from" "$ir_full"; then
    GDD_IR_CARRY_REASON="Independent Review Carry の from が Independent Review の sha と一致しない"
    return 1
  fi
  # 第 2 親を照合する default branch は、審査済みの remote-tracking の ref に限る。
  # gdd_resolve_base_ref は gh-merge-base（積み PR では別の feature branch）や local の
  # branch まで落ちるので使わない。
  local candidate
  for candidate in origin/HEAD origin/main origin/master; do
    if git -C "$root" rev-parse --quiet --verify "refs/remotes/${candidate}^{commit}" >/dev/null 2>&1; then
      base_ref="refs/remotes/${candidate}"
      break
    fi
  done
  if [[ -z "$base_ref" ]]; then
    GDD_IR_CARRY_REASON="default branch を解決できない"
    return 1
  fi
  # hook の timeout（10 秒）を超えると hook は無出力で終わり、操作が通る。shell の起動から
  # の経過（SECONDS。秒の切り捨てなので 1 秒を足す）を持ち時間から引いた残りを渡す。
  local remaining=$(( allowance - SECONDS - 1 ))
  if [[ "$remaining" -lt 1 ]]; then
    GDD_IR_CARRY_REASON="時間内に確かめられない"
    return 1
  fi
  GDD_IR_CARRY_REASON="$(python3 -I -X utf8 "$(dirname "${BASH_SOURCE[0]}")/ir_merge_carry.py" \
    "$root" "$expected" "$ir_full" "$base_ref" "$remaining" 2>/dev/null)" && return 0
  GDD_IR_CARRY_REASON="${GDD_IR_CARRY_REASON:-判定できない}"
  return 1
}

# gdd_parse_merge_gate_field（lib/merge-gate-evidence.sh）の後に呼ぶ。high も blocking も 0 か。
# 受理集合は merge gate（`high == 0 && blocking == 0`）と同じ。
gdd_independent_review_clean() {
  [[ "${GDD_MG_HIGH:-}" == "0" && "${GDD_MG_BLOCKING:-}" == "0" ]]
}

# PR を作る steering（Next Action か Resume From が done のもの）を 1 件に決める。
# cwd の git toplevel を見る。PLUGIN_ROOT（または GDD_PLUGIN_ROOT）を先に設定しておくこと。
# 結果は GDD_STEERING_DIR・GDD_STEERING_WT・GDD_STEERING_STATUS に入れる（$(...) で呼ばない）。
gdd_detect_completed_steering_for_pr() {
  GDD_STEERING_DIR=""
  GDD_STEERING_WT=""
  GDD_STEERING_STATUS=""
  GDD_STEERING_CANDIDATES=()

  command -v git >/dev/null 2>&1 || return 1
  local wt=""
  wt="$(git rev-parse --show-toplevel 2>/dev/null)" || return 1
  [[ -d "$wt/.steering" ]] || return 1

  local plugin_root="${GDD_PLUGIN_ROOT:-$PLUGIN_ROOT}"
  local resolver="${plugin_root}/scripts/gdd_task_binding.py"
  local python_bin=""
  local branch=""
  for cmd in python3 python; do
    if command -v "$cmd" >/dev/null 2>&1; then
      python_bin="$cmd"
      break
    fi
  done
  branch="$(git -C "$wt" branch --show-current 2>/dev/null || true)"
  if [[ -n "$python_bin" && -f "$resolver" ]]; then
    local resolve_json="" resolved_state=""
    resolve_json="$("$python_bin" "$resolver" resolve \
      --repo-root "$wt" \
      --cwd "$wt" \
      --current-branch "$branch" \
      --local-state-path "$wt/.claude/gdd-dev.local.md" 2>/dev/null || true)"
    if [[ -n "$resolve_json" ]]; then
      resolved_state="$(printf '%s' "$resolve_json" | "$python_bin" -c 'import json,sys
try:
    data=json.load(sys.stdin)
    if data.get("status") == "resolved":
        print(data.get("binding", {}).get("state_path", ""))
except Exception:
    pass
' 2>/dev/null || true)"
    fi
    if [[ -n "$resolved_state" && -f "$resolved_state" ]]; then
      local resolved_tasklist resolved_resume resolved_next
      resolved_tasklist="$(dirname "$resolved_state")/tasklist.md"
      resolved_resume="$(gdd_extract_doc_field "$resolved_state" "Resume From")"
      resolved_next="$(gdd_extract_doc_field "$resolved_state" "Next Action")"
      if [[ -z "$resolved_next" && -f "$resolved_tasklist" ]]; then
        resolved_next="$(gdd_extract_doc_field "$resolved_tasklist" "Next Action")"
      fi
      # 比較は先頭セグメントで行う。空判定（上の tasklist への読み直し）は切り出す前の値のまま。
      if [[ "$(gdd_value_head "$resolved_resume")" == "done" || "$(gdd_value_head "$resolved_next")" == "done" ]]; then
        GDD_STEERING_STATUS="found"
        GDD_STEERING_DIR="$(cd "$(dirname "$resolved_state")" && pwd)"
        GDD_STEERING_WT="$wt"
        return 0
      fi
    fi
  fi

  local candidates=()
  local state_file tasklist_file resume_from next_action
  while IFS= read -r state_file; do
    [[ -n "$state_file" && -f "$state_file" ]] || continue
    if gdd_is_stale_brainstorming_candidate "$state_file"; then
      continue
    fi
    tasklist_file="$(dirname "$state_file")/tasklist.md"
    resume_from="$(gdd_extract_doc_field "$state_file" "Resume From")"
    next_action="$(gdd_extract_doc_field "$state_file" "Next Action")"
    if [[ -z "$next_action" && -f "$tasklist_file" ]]; then
      next_action="$(gdd_extract_doc_field "$tasklist_file" "Next Action")"
    fi
    resume_from="$(gdd_value_head "$resume_from")"
    next_action="$(gdd_value_head "$next_action")"
    if [[ "$resume_from" == "cancelled" || "$resume_from" == "blocked" || "$next_action" == "cancelled" || "$next_action" == "blocked" ]]; then
      continue
    fi
    if [[ "$resume_from" == "done" || "$next_action" == "done" ]]; then
      candidates+=("$state_file")
    fi
  done < <(find "$wt/.steering" -mindepth 2 -maxdepth 2 -name state.md -type f 2>/dev/null | sort -r)

  if [[ ${#candidates[@]} -gt 1 ]]; then
    GDD_STEERING_STATUS="multiple"
    return 1
  fi
  [[ ${#candidates[@]} -eq 1 ]] || return 1
  GDD_STEERING_STATUS="found"
  GDD_STEERING_DIR="$(cd "$(dirname "${candidates[0]}")" && pwd)"
  GDD_STEERING_WT="$wt"
  return 0
}
