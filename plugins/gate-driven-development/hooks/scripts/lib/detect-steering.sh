#!/usr/bin/env bash
# Shared steering detection for GDD hooks.
# Source this file from hook scripts — do not execute directly.
#
# Exports:
#   gdd_detect_active_steering  — finds the single active (non-terminal) steering dir
#   gdd_check_3field_gate       — checks if tasklist.md is canonical (3 gate approvals)
#
# After gdd_detect_active_steering succeeds:
#   GDD_STEERING_DIR  — path to the steering directory (e.g. /path/.steering/20260416-task)
#   GDD_STEERING_WT   — path to the worktree containing the steering
#
# After gdd_check_3field_gate:
#   GDD_TASKLIST_CANONICAL — "true" or "false"
#   GDD_GATE_FILE          — path to state.md or design.md used for the check
# After gdd_validate_active_state_fields:
#   GDD_ACTIVE_STATE_VALID              — "true" or "false"
#   GDD_ACTIVE_STATE_ERROR              — fail-closed message for hooks
#   GDD_ACTIVE_STATE_MISSING            — comma-separated missing field names
#   GDD_ACTIVE_STATE_REFERENCES         — canonical files that were inspected
#   GDD_ACTIVE_STATE_ROUTE_IN_PROGRESS  — the `Route In Progress` value it already
#     read from state.md (raw, not "none"-normalized — callers do that comparison
#     themselves). Callers whose gate file is state.md should reuse this instead of
#     calling `gdd_extract_route_in_progress` again, which would spawn a second
#     python3 subprocess to re-parse the same file (independent review finding,
#     2026-09-04). Only valid when `GDD_ACTIVE_STATE_VALID="true"`.

_GDD_DS_LIB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

GDD_STEERING_DIR=""
GDD_STEERING_WT=""
GDD_STEERING_STATUS=""        # "found" | "none" | "multiple"
GDD_STEERING_CANDIDATES=()    # diagnostic: all candidate paths (populated on multiple)
GDD_TASKLIST_CANONICAL="false"
GDD_GATE_FILE=""
GDD_ACTIVE_STATE_VALID="true"
GDD_ACTIVE_STATE_ERROR=""
GDD_ACTIVE_STATE_MISSING=""
GDD_ACTIVE_STATE_REFERENCES=""
GDD_ACTIVE_STATE_ROUTE_IN_PROGRESS=""

gdd_iso_to_epoch() {
  local _iso="$1"
  [[ -n "$_iso" ]] || return 1
  if date -j -f "%Y-%m-%dT%H:%M:%S" "${_iso%%[Z+]*}" +%s >/dev/null 2>&1; then
    date -j -f "%Y-%m-%dT%H:%M:%S" "${_iso%%[Z+]*}" +%s 2>/dev/null
    return 0
  fi
  if date -d "$_iso" +%s >/dev/null 2>&1; then
    date -d "$_iso" +%s 2>/dev/null
    return 0
  fi
  return 1
}

gdd_extract_doc_field() {
  local _file="$1"
  local _field="$2"
  [[ -f "$_file" ]] || return 0
  awk -v field="$_field" '
    # fenced code block の中は「書式の記入例」であって現在値ではない。fence を
    # 追跡しないと、state.md に記入例を 1 つ置いただけで証跡が成立する
    # （merge gate の `Merge Approval` が実測でこの形で通っていた）。
    # 規約の正本は lib/tasklist_parse.strip_fenced_blocks: 開き fence の**記号種別と
    # 長さ**を保持し、同種・同長以上で情報文字列の無い行でだけ閉じる（素朴なトグルは
    # 4 連バッククォートで包んだ ``` 入りブロックで反転する）。閉じ忘れは「fence 無し」
    # として扱う — そこから先を全部落とすと canonical field が 1 つも見えなくなる。
    # 判定はバッククォート除去より**前**に行う（除去後は fence 行が空行に化ける）。
    { lines[NR] = $0 }
    match($0, /^[ \t]*(`+|~+)/) {
      m = substr($0, RSTART, RLENGTH); sub(/^[ \t]*/, "", m)
      info = substr($0, RSTART + RLENGTH)
      if (length(m) >= 3) {
        if (open_marker == "") {
          if (!(substr(m, 1, 1) == "`" && index(info, "`") > 0)) {
            open_marker = m; open_at = NR
          }
        } else if (substr(m, 1, 1) == substr(open_marker, 1, 1) &&
                   length(m) >= length(open_marker) && info ~ /^[[:space:]]*$/) {
          for (i = open_at; i <= NR; i++) fenced[i] = 1
          open_marker = ""
        }
      }
    }
    END {
      for (n = 1; n <= NR; n++) {
        if (fenced[n]) continue
        raw = lines[n]
        gsub(/`/, "", raw)
      # canonical field 行は**行頭から始まる**。許容する接頭辞は markdown bullet
      # marker 1 個 + 空白（`- Next Action: done`）だけで、`^-` に固定する。
      # 旧実装は `^[[:space:]-]*` を個数無制限で落としていたため、入れ子 bullet の
      # 履歴メモ（`  - `Next Action=...`（Attempt #2 へ再入場）`）やコードブロック内の
      # 記入例が canonical field と区別できず、最初の一致 = 履歴メモを現在値として
      # 返していた。インデント行はこの sub が効かず index() も 1 にならないので、
      # 追加のガードは置かない（tests/test_canonical_field_line_anchoring_contract.py が正本）。
        sub(/^-[[:space:]]+/, "", raw)
      # 区切り文字の後ろが trim 後に空の行は**現在値ではない**。書きかけの
      # `- Resume From:` が先頭にあるだけで後続の値付き行が見えなくなり、
      # presence 判定が「欠落」と誤って fail-closed で resume を塞いでいた
      # （2026-09-04 実機再現）。印字は従来どおり trim 前の substr、判定だけ
      # 前後空白を落とした値で行い、空なら exit せず次の canonical 行を見る。
      # `|` 分割はこの空判定に含めない（`- Field: | evidence: x` は値付き扱い）。
        if (index(raw, field "=") == 1) {
          v = substr(raw, length(field) + 2)
          t = v
          gsub(/^[[:space:]]+/, "", t)
          gsub(/[[:space:]]+$/, "", t)
          if (t != "") { print v; exit }
          continue
        }
        if (index(raw, field ":") == 1) {
          v = substr(raw, length(field) + 2)
          t = v
          gsub(/^[[:space:]]+/, "", t)
          gsub(/[[:space:]]+$/, "", t)
          if (t != "") { print v; exit }
          continue
        }
      }
    }
  ' "$_file" 2>/dev/null | sed 's/^[[:space:]]*//' | sed 's/[[:space:]]*$//'
}

# state field の値から先頭セグメント（ASCII `|` より前）を取り出し、前後の空白を落とす。
# 文法は references/state-machine.md § state field のフォーマット検証
# （`<value> | <key>: <detail>`）。`gdd_extract_doc_field` は `|` で切らない（PR URL の
# 読み手が依存する）ので、terminal 値との比較だけこれを通す。代入や空判定には
# 切り出す前の値を使う（空の先頭セグメントから別ファイルへ読み直す経路を作らない）。
# 全角の `｜`・`（` は文法外なので切らない。先頭セグメントの切り出しと ASCII 空白の trim は
# lint-resume-integrity.py の field_head と同じ（lint は大小文字や別名も正規化するが、ここは完全一致で比べる）。
gdd_value_head() {
  local _v="${1-}"
  _v="${_v%%|*}"
  _v="${_v#"${_v%%[![:space:]]*}"}"
  _v="${_v%"${_v##*[![:space:]]}"}"
  printf '%s' "$_v"
}

# `Route In Progress` の**現在値**（enum トークン）を返す。値が無ければ空文字。
#
# 汎用の `gdd_extract_doc_field` を使ってはいけない。あちらは最初の一致で `exit`
# するため、人間が `- Route In Progress: none | reason: 解除` を追記して route を
# 解除しても、古い route を返し続ける（session-start / user-prompt-submit が
# 解除済みの route を context に注入する誘導ズレ。2026-09-03 実測）。
#
# 値の選択規則の正本は `lib/tasklist_parse.select_route_in_progress()` 1 箇所。
# 規則は「fence 剥がし → 行頭アンカー → 正準形（`:`）優先 → 同形なら最終行 →
# enum トークンだけ抽出」の 5 段で、awk へ書き写すと規約が 2 実装に散って
# 片方だけ直す形の退行が戻る（実測で 7 形の差があった）。だから委譲する。
# 正本テスト: tests/test_route_in_progress_reader_contract.py
gdd_extract_route_in_progress() {
  local _file="$1"
  [[ -f "$_file" ]] || return 0
  local _out=""
  if command -v python3 >/dev/null 2>&1; then
    # path は argv で渡す（スクリプト本体へ連結しない）。
    # `errors="replace"` で開く: 独立レビューで実測確認 —— 厳格 UTF-8 decode だと
    # state.md に不正バイトが 1 つあるだけで `UnicodeDecodeError` が起き、
    # python3 は使える状態のまま非ゼロ終了になって下の退避（最初の一致）に
    # 落ちる。「python3 不在時のみの退避」という設計前提が壊れ、本 PR が閉じた
    # はずの「stale route が再注入される」欠陥がデータ起因で復活する
    # （2026-09-04 実測）。不正バイトは注記部分に混ざる想定で、フィールドの
    # 構造自体は保たれるため、置換文字化しても enum トークンの判定に影響しない。
    if _out="$(python3 -c '
import sys
sys.path.insert(0, sys.argv[1])
from tasklist_parse import select_route_in_progress
with open(sys.argv[2], encoding="utf-8", errors="replace") as fh:
    sys.stdout.write(select_route_in_progress(fh.read()))
' "$_GDD_DS_LIB_DIR" "$_file" 2>/dev/null)"; then
      printf '%s' "$_out"
      return 0
    fi
  fi
  # python3 不在時のみの退避。値の正規化（`route_value()` と同じ手順）は再現するが、
  # **行の選択（最終行採択）は再現しない**（既知の限界。理由は
  # `tests/test_route_in_progress_reader_contract.py` の
  # `test_multiple_matching_lines_return_the_first_not_the_last` を参照 ——
  # fence 追跡込みの選択規則をこのローカル関数へ複製すると、規約が再び 2 実装に
  # 散る。python3 の真の不在は環境要因で、同じ環境では他 field も同じ
  # 「最初の一致」規則のままなので、Route In Progress だけが劣化するわけではない）。
  local _raw _head
  _raw="$(gdd_extract_doc_field "$_file" "Route In Progress")"  # GDD_ROUTE_FALLBACK
  _raw="${_raw%%|*}"
  _raw="${_raw%"${_raw##*[![:space:]]}"}"
  # 装飾の除去は `route_value()` と同じ順序・同じ文字集合で行う（バッククォート→
  # アスタリスク→二重引用符→単一引用符、それぞれ前後の連続文字を丸ごと除去）。
  # 順序を変えると入れ子の装飾（例 `` `*none*` ``）で結果が変わるため固定する。
  # bash のパラメータ展開だけでは「前後の連続する同一文字を丸ごと剥がす」
  # （python `str.strip()`）を素直に書けないため sed を使う。
  _raw="$(printf '%s' "$_raw" | sed \
    -e 's/^`*//' -e 's/`*$//' \
    -e 's/^\**//' -e 's/\**$//' \
    -e 's/^"*//' -e 's/"*$//' \
    -e "s/^'*//" -e "s/'*\$//")"
  _raw="${_raw%"${_raw##*[![:space:]]}"}"
  # 識別子（先頭が英字/アンダースコア）で始まる場合だけ境界で切り詰める。
  # `route_value()` の `re.match(r"[A-Za-z_][A-Za-z0-9_-]*", body)` と同じ —— 先頭が
  # 識別子文字でなければ**値全体**を残す（数字始まりの壊れた値を切り捨てない）。
  # 文字クラスは ASCII 直書きにする。`[[:alnum:]]` は locale 依存で、UTF-8 ロケール
  # では `実装修正中` 全体に一致してしまい、`LC_ALL=C` とで挙動が割れる
  # （`gdd_truncate_chars` が閉じた locale 依存と同型）。
  if [[ "$_raw" == [A-Za-z_]* ]]; then
    _head="${_raw%%[!A-Za-z0-9_-]*}"
    [[ -n "$_head" ]] && _raw="$_head"
  fi
  printf '%s' "$_raw"
}

# additionalContext / systemMessage へ注入する前の長さ制限を「文字単位」で行う。
#
# `${var:0:N}` は locale 依存で、`LC_ALL=C` やロケール未設定では**バイト単位**になる。
# state.md の `Approved Direction` / `Last Handoff Summary` / `Next Action` は日本語の
# 自由記述で、512 バイト = 日本語約 170 文字なので超過は現実的。バイト境界で切ると
# UTF-8 シーケンスが途中で切れて注入先の JSON が壊れる（invalid continuation byte）。
#
# python3 が無い環境では multibyte を含む値を切らずに返す。列幅より値の完全性を優先する
# `scripts/find-stale-steerings.sh` と同じ「壊すより残す」方針。
gdd_truncate_chars() {
  local _value="$1"
  local _limit="$2"
  [[ -n "$_value" ]] || return 0
  if command -v python3 >/dev/null 2>&1; then
    printf '%s' "$_value" | python3 -c 'import sys
sys.stdout.write(sys.stdin.buffer.read().decode("utf-8", "ignore")[: int(sys.argv[1])])
' "$_limit"
    return 0
  fi
  # ASCII のみなら byte 切りでも文字境界は壊れない。範囲比較と substring の両方を
  # byte 単位に固定するため C locale の subshell で判定する。
  (
    export LC_ALL=C
    case $_value in
      *[!\ -~]*) printf '%s' "$_value" ;;
      *) printf '%s' "${_value:0:$_limit}" ;;
    esac
  )
}

# Print the leading ASCII word of a field value in lower case (`Done (merged)` → `done`).
_gdd_leading_word() {
  local _lower
  _lower="$(printf '%s' "${1:-}" | LC_ALL=C tr '[:upper:]' '[:lower:]')"
  if [[ "$_lower" =~ ^[[:space:]]*([a-z]+) ]]; then
    printf '%s' "${BASH_REMATCH[1]}"
  fi
  return 0
}

gdd_is_stale_brainstorming_candidate() {
  local _state_file="$1"
  [[ -f "$_state_file" ]] || return 1
  local _resume_from _started_at _started_epoch _now_epoch
  _resume_from="$(gdd_value_head "$(gdd_extract_doc_field "$_state_file" "Resume From")")"
  [[ "$_resume_from" == "gdd-brainstorming" ]] || return 1
  _started_at="$(gdd_extract_doc_field "$_state_file" "Started At")"
  _started_epoch="$(gdd_iso_to_epoch "$_started_at")" || return 1
  _now_epoch="$(date +%s)"
  [[ $((_now_epoch - _started_epoch)) -gt 864000 ]]
}

# Detect the single active (non-terminal) steering directory bound to the
# current git worktree. Task identity is resolved through `.gdd/tasks/*/binding.json`;
# plain `.steering` discovery is diagnostic-only and must not auto-color a
# new session with stale task context.
# Returns 0 if exactly one candidate found, 1 otherwise.
# `--recount-terminal-binding`: when the binding points to a terminal steering
# (Resume From done / cancelled, a stale brainstorming, or, only with this option,
# a steering the recount treats as ended: the Resume From or Next Action of state.md,
# or the Next Action of tasklist.md, whose leading ASCII word is done / cancelled /
# canceled in any case, or an unreadable / non-file tasklist.md), count the
# non-terminal steerings by the same fallback rule as when no binding resolves, never
# counting the bound steering itself as working. When a working one exists, the
# done / blocked steerings under `.steering/` and a bound steering the recount treats
# as ended (wherever it lives) are kept as candidates too; with no working steering,
# such a bound steering is returned, as before the recount. The pre-push /
# merge / pre-PR gates pass it so that a terminal binding cannot hide a working
# steering; the other callers keep treating a terminal binding as "no active task"
# (and a followup `Next Action: done` binding as the active task).
# Requires: git
gdd_detect_active_steering() {
  GDD_STEERING_DIR=""
  GDD_STEERING_WT=""
  GDD_STEERING_STATUS=""
  GDD_STEERING_CANDIDATES=()
  local _recount="false"
  if [[ "${1:-}" == "--recount-terminal-binding" ]]; then
    _recount="true"
  fi

  command -v git >/dev/null 2>&1 || return 1
  git rev-parse --is-inside-work-tree >/dev/null 2>&1 || return 1

  local _wt
  _wt="$(git rev-parse --show-toplevel 2>/dev/null)" || return 1
  local _branch=""
  _branch="$(git branch --show-current 2>/dev/null || true)"

  local _plugin_root="${GDD_PLUGIN_ROOT:-}"
  if [[ -z "$_plugin_root" ]]; then
    _plugin_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
  fi
  local _resolver="${_plugin_root}/scripts/gdd_task_binding.py"
  local _python_bin=""
  for _cmd in python3 python; do
    if command -v "$_cmd" >/dev/null 2>&1; then
      _python_bin="$_cmd"
      break
    fi
  done

  if [[ -z "$_python_bin" || ! -f "$_resolver" ]]; then
    GDD_STEERING_STATUS="none"
    return 1
  fi

  local _resolve_json=""
  _resolve_json="$("$_python_bin" "$_resolver" resolve \
    --repo-root "$_wt" \
    --cwd "$_wt" \
    --current-branch "$_branch" \
    --local-state-path "$_wt/.claude/gdd-dev.local.md" 2>/dev/null || true)"

  local _resolved_state=""
  if [[ -n "$_resolve_json" ]]; then
    _resolved_state="$(printf '%s' "$_resolve_json" | "$_python_bin" -c 'import json,sys
try:
    data=json.load(sys.stdin)
    if data.get("status") == "resolved":
        print(data.get("binding", {}).get("state_path", ""))
except Exception:
    pass
' 2>/dev/null || true)"
  fi

  local _recounting="false" _bound_recounted="false"
  if [[ -n "$_resolved_state" && -f "$_resolved_state" ]]; then
    local _resume_from="" _bound_terminal="false"
    if gdd_is_stale_brainstorming_candidate "$_resolved_state"; then
      _bound_terminal="true"
      # When recounting, a stale brainstorming binding stays a candidate like a
      # binding ended by the recount (leaving it idle must not drop it from the gates).
      if [[ "$_recount" == "true" ]]; then
        _bound_recounted="true"
      fi
    else
      _resume_from="$(gdd_value_head "$(gdd_extract_doc_field "$_resolved_state" "Resume From")")"
      if [[ "$_resume_from" == "done" || "$_resume_from" == "cancelled" ]]; then
        _bound_terminal="true"
      elif [[ "$_recount" != "true" \
        && "$(gdd_value_head "$(gdd_extract_doc_field "$_resolved_state" "Next Action")")" == "cancelled" ]]; then
        # 中止の規定（human check・completion-check の中止）は Next Action だけを cancelled にする。
        # 数え直さない呼び出し元（session-start など）には、中止した steering を作業中として渡さない。
        # Next Action の done は終端にしない（gdd-pr-review-followup の external-review-waiting の間の暫定値）。
        # 数え直す gate は下で、binding 先を候補に残す形で終端とみなす。
        _bound_terminal="true"
      elif [[ "$_recount" == "true" ]]; then
        # completion-check writes only `Next Action: done` (state.md or tasklist.md).
        # When recounting, treat that as ended too (the terminal set of
        # state-machine.md), comparing the leading word in lower case so that
        # `Done`, `done (merged)`, `done（…）` and `canceled` are ended as well.
        # A tasklist.md that exists but cannot be read as a file may hold `done`:
        # recount (fail-closed) instead of taking the binding as the working task.
        # A binding ended only here (or a stale brainstorming, above) stays a
        # candidate (below). An exact `Resume From: cancelled` is not kept; an exact
        # `Resume From: done` is kept as done (unchecked only outside `.steering/` with
        # no working steering). The peer-turn write guard stops `Resume From: cancelled`
        # / `done` only for writes under `.steering/`: Write / Edit / MultiEdit by the
        # value, ApplyPatch by the added lines (validate-steering-write.py).
        local _bound_word _bound_value _bound_tasklist
        _bound_tasklist="$(dirname "$_resolved_state")/tasklist.md"
        if [[ ( -e "$_bound_tasklist" || -L "$_bound_tasklist" ) && ! ( -f "$_bound_tasklist" && -r "$_bound_tasklist" ) ]]; then
          _bound_terminal="true"
          _bound_recounted="true"
        fi
        for _bound_value in \
          "$(gdd_extract_doc_field "$_resolved_state" "Resume From")" \
          "$(gdd_extract_doc_field "$_resolved_state" "Next Action")" \
          "$(if [[ -f "$_bound_tasklist" && -r "$_bound_tasklist" ]]; then gdd_extract_doc_field "$_bound_tasklist" "Next Action" || true; fi)"; do
          _bound_word="$(_gdd_leading_word "$_bound_value")"
          if [[ "$_bound_word" == "done" || "$_bound_word" == "cancelled" || "$_bound_word" == "canceled" ]]; then
            _bound_terminal="true"
            _bound_recounted="true"
          fi
        done
      fi
    fi
    if [[ "$_bound_terminal" == "false" ]]; then
      GDD_STEERING_STATUS="found"
      GDD_STEERING_DIR="$(cd "$(dirname "$_resolved_state")" && pwd)"
      GDD_STEERING_WT="$_wt"
      return 0
    fi
    if [[ "$_recount" != "true" ]]; then
      GDD_STEERING_STATUS="none"
      return 1
    fi
    _recounting="true"
  fi

  # Registry could not resolve the current worktree (or, with
  # `--recount-terminal-binding`, resolved it to a terminal steering). A single non-terminal
  # same-worktree steering is still a safe resume candidate: hooks must be able
  # to fail-closed on missing canonical fields before any workflow advances.
  # While recounting for a terminal binding, the done / blocked steerings under
  # `.steering/` (as the pre-push resolver's union picks them) and the bound one
  # wherever it lives are kept as candidates too (only when a working steering
  # exists): choosing the working one alone would check the push with its Task Size
  # (trivial passes unchecked) instead of the ended one's.
  local _candidates=() _terminal_candidates=()
  local _state_file _resume_from _next_action _bound_real=""
  if [[ "$_recounting" == "true" ]]; then
    _bound_real="$(cd "$(dirname "$_resolved_state")" 2>/dev/null && pwd -P || true)"
  fi
  if [[ -d "$_wt/.steering" ]]; then
    while IFS= read -r _state_file; do
      [[ -n "$_state_file" && -f "$_state_file" ]] || continue
      # The bound steering is classified once after the scan (its terminal value may
      # use a spelling this exact-match scan would count as working).
      if [[ -n "$_bound_real" \
        && "$(cd "$(dirname "$_state_file")" 2>/dev/null && pwd -P || true)" == "$_bound_real" ]]; then
        continue
      fi
      if gdd_is_stale_brainstorming_candidate "$_state_file"; then
        continue
      fi
      _resume_from="$(gdd_value_head "$(gdd_extract_doc_field "$_state_file" "Resume From")")"
      _next_action="$(gdd_value_head "$(gdd_extract_doc_field "$_state_file" "Next Action")")"
      if [[ "$_resume_from" == "done" || "$_next_action" == "done" \
        || "$_resume_from" == "blocked" || "$_next_action" == "blocked" ]]; then
        _terminal_candidates+=("$_state_file")
      fi
      if [[ "$_resume_from" == "done" || "$_resume_from" == "cancelled" || "$_resume_from" == "blocked" ]]; then
        continue
      fi
      if [[ "$_next_action" == "done" || "$_next_action" == "cancelled" || "$_next_action" == "blocked" ]]; then
        continue
      fi
      _candidates+=("$_state_file")
    done < <(find "$_wt/.steering" -mindepth 2 -maxdepth 2 -name state.md -type f 2>/dev/null | sort -r)
  fi
  # The bound steering (inside or outside `.steering/`) joins the ended candidates
  # when the recount ended it or it is done / blocked, never the working ones.
  if [[ "$_recounting" == "true" ]]; then
    _resume_from="$(gdd_value_head "$(gdd_extract_doc_field "$_resolved_state" "Resume From")")"
    _next_action="$(gdd_value_head "$(gdd_extract_doc_field "$_resolved_state" "Next Action")")"
    if [[ "$_bound_recounted" == "true" \
      || "$_resume_from" == "done" || "$_next_action" == "done" \
      || "$_resume_from" == "blocked" || "$_next_action" == "blocked" ]]; then
      _terminal_candidates+=("$_resolved_state")
    fi
  fi
  if [[ "$_recounting" == "true" && ${#_candidates[@]} -gt 0 && ${#_terminal_candidates[@]} -gt 0 ]]; then
    _candidates+=("${_terminal_candidates[@]}")
  fi
  # No working steering: a binding that only the recount treats as ended (its
  # `Next Action`, a non-canonical spelling, or an unreadable tasklist.md) is still
  # the task of this worktree, as before the recount (even outside `.steering/`).
  if [[ "$_recounting" == "true" && "$_bound_recounted" == "true" && ${#_candidates[@]} -eq 0 ]]; then
    GDD_STEERING_STATUS="found"
    GDD_STEERING_DIR="$(cd "$(dirname "$_resolved_state")" && pwd)"
    GDD_STEERING_WT="$_wt"
    return 0
  fi

  if [[ ${#_candidates[@]} -eq 1 ]]; then
    GDD_STEERING_STATUS="found"
    GDD_STEERING_DIR="$(cd "$(dirname "${_candidates[0]}")" && pwd)"
    GDD_STEERING_WT="$_wt"
    return 0
  fi
  if [[ ${#_candidates[@]} -gt 1 ]]; then
    # Candidates are collected one state.md per .steering/<slug>/ directory,
    # so 2+ candidates always have distinct slugs (same-slug duplication is
    # structurally unreachable here). Never auto-select via Started At;
    # always fail closed to multiple (don't inject, report count only).
    GDD_STEERING_STATUS="multiple"
    GDD_STEERING_CANDIDATES=()
    for _state_file in "${_candidates[@]}"; do
      GDD_STEERING_CANDIDATES+=("$(dirname "$_state_file")")
    done
    return 1
  fi

  GDD_STEERING_STATUS="none"
  return 1
}

# Check if tasklist.md is canonical (all 3 gate approvals present).
# Requires GDD_STEERING_DIR to be set.
gdd_check_3field_gate() {
  GDD_TASKLIST_CANONICAL="false"
  GDD_GATE_FILE=""

  if [[ -f "$GDD_STEERING_DIR/state.md" ]]; then
    GDD_GATE_FILE="$GDD_STEERING_DIR/state.md"
  elif [[ -f "$GDD_STEERING_DIR/design.md" ]]; then
    GDD_GATE_FILE="$GDD_STEERING_DIR/design.md"
  fi

  # 区切り文字は `=` と `:` の両方を受け付ける。gdd_extract_doc_field と同じ正規化に
  # 揃えることで、読み手ごとに認識できる書式が違う状態を解消する。
  # 旧実装は `Requirements Review Status=` を grep する `=` 限定で、実データの多数派
  # （`:` 形式）を静かに取りこぼし、GDD_TASKLIST_CANONICAL が
  # false のままになっていた（plan-reread hook がほとんど発火しなかった）。
  if [[ -f "$GDD_STEERING_DIR/tasklist.md" && -n "$GDD_GATE_FILE" ]]; then
    local _req_s _des_s _hum_s
    _req_s="$(gdd_extract_doc_field "$GDD_GATE_FILE" "Requirements Review Status" | sed 's/[[:space:]|].*//')" || true
    _des_s="$(gdd_extract_doc_field "$GDD_GATE_FILE" "Design Review Status" | sed 's/[[:space:]|].*//')" || true
    _hum_s="$(gdd_extract_doc_field "$GDD_GATE_FILE" "Human Check Status" | sed 's/[[:space:]|].*//')" || true
    if [[ "$_req_s" == "approved" && "$_des_s" == "approved" && "$_hum_s" == "approved" ]]; then
      GDD_TASKLIST_CANONICAL="true"
    fi
  fi
}

gdd_validate_active_state_fields() {
  GDD_ACTIVE_STATE_VALID="true"
  GDD_ACTIVE_STATE_ERROR=""
  GDD_ACTIVE_STATE_MISSING=""
  GDD_ACTIVE_STATE_REFERENCES=""
  GDD_ACTIVE_STATE_ROUTE_IN_PROGRESS=""

  [[ -n "$GDD_STEERING_DIR" ]] || return 0

  local _state_file="$GDD_STEERING_DIR/state.md"
  local _tasklist_file="$GDD_STEERING_DIR/tasklist.md"
  local _missing=()
  local _references=()

  if [[ ! -f "$_state_file" ]]; then
    GDD_ACTIVE_STATE_VALID="false"
    GDD_ACTIVE_STATE_MISSING="state.md"
    GDD_ACTIVE_STATE_REFERENCES="\`state.md\`"
    GDD_ACTIVE_STATE_ERROR="参照した正本: \`state.md\`。停止理由: active steering に canonical な \`state.md\` がありません。次の1アクション: \`state.md\` を復元し、\`Resume From\` / \`Human Check Status\` / \`Route In Progress\` を書き戻してください。"
    return 1
  fi

  _references+=("\`state.md\`")
  local _value=""
  # Tier 1 (Core) state.md fields — canonical: references/state-field-tiers.md
  # Keep in sync with hooks/scripts/validate-steering-write.py:STATE_REQUIRED_FIELDS.
  # `Started At` is required separately (transitive: enforced by write hook
  # when any of these fields are written). `Next Action` is required only
  # when tasklist is canonical (3 gates approved) — checked below.
  for _field in "Resume From" "Human Check Status" "Route In Progress"; do
    # 存在判定も値 reader と同じ規約で行う。`gdd_extract_doc_field`（awk）は R-1 で
    # 値の無い canonical 行をスキップして走査を継続するため、`Resume From` /
    # `Human Check Status` の presence 判定はこの汎用 reader 経由で正しくなった。
    # `Route In Progress` だけは引き続き専用 reader（`gdd_extract_route_in_progress`）
    # を使う——理由は R-1 の空値スキップではなく別次元（最終行採択・enum 抽出・
    # 装飾除去）。正本: tests/test_route_in_progress_reader_contract.py。
    if [[ "$_field" == "Route In Progress" ]]; then
      _value="$(gdd_extract_route_in_progress "$_state_file")"
      GDD_ACTIVE_STATE_ROUTE_IN_PROGRESS="$_value"
    else
      _value="$(gdd_extract_doc_field "$_state_file" "$_field")"
    fi
    if [[ -z "${_value// /}" ]]; then
      _missing+=("\`$_field\`")
    fi
  done

  # `Next Action` は tasklist.md / state.md のどちらにあってもよい。
  # 設計上の routing source は build phase では tasklist.md だが、実運用では
  # state.md 側に書かれることが多い（実測）。tasklist.md 限定で探すと、
  # 区切り文字の正規化で新たに canonical になった task が routing source を
  # 持っているのに fail-closed してしまう。どちらにも無い場合だけ止める。
  if [[ "$GDD_TASKLIST_CANONICAL" == "true" ]]; then
    _references+=("\`tasklist.md\`")
    _value="$(gdd_extract_doc_field "$_tasklist_file" "Next Action")"
    if [[ -z "${_value// /}" ]]; then
      _value="$(gdd_extract_doc_field "$_state_file" "Next Action")"
    fi
    if [[ -z "${_value// /}" ]]; then
      _missing+=("\`Next Action\`")
    fi
  fi

  if [[ ${#_missing[@]} -eq 0 ]]; then
    return 0
  fi

  local _missing_text=""
  local _refs_text=""
  local _item
  for _item in "${_missing[@]}"; do
    if [[ -n "$_missing_text" ]]; then
      _missing_text+=", "
    fi
    _missing_text+="$_item"
  done
  for _item in "${_references[@]}"; do
    if [[ -n "$_refs_text" ]]; then
      _refs_text+=", "
    fi
    _refs_text+="$_item"
  done

  local _next_step="\`state.md\` に欠落 field を書き戻してください。"
  if [[ "$_missing_text" == *"\`Next Action\`"* ]]; then
    _next_step+=" canonical な \`tasklist.md\` では \`Next Action=<current-phase>\` も復元してください。"
  fi

  GDD_ACTIVE_STATE_VALID="false"
  GDD_ACTIVE_STATE_MISSING="$_missing_text"
  GDD_ACTIVE_STATE_REFERENCES="$_refs_text"
  GDD_ACTIVE_STATE_ERROR="参照した正本: ${_refs_text}。停止理由: active steering の canonical state field が欠落しています (${_missing_text})。次の1アクション: ${_next_step}"
  return 1
}

# Cross-session guard helper used by UserPromptSubmit / PreToolUse / Stop-adjacent
# hooks to avoid acting on a `gdd-dev.local.md` that was created by a different
# session (the root cause behind GDD misfires when a stale state file is left on
# disk).
#
# Usage:
#   gdd_session_continuity_ok "/path/to/.claude/gdd-dev.local.md" || exit 0
#
# Returns 0 (continue normally) when:
#   - CLAUDE_CODE_SESSION_ID is empty (Cursor / non-Claude environment — fail-open
#     because the env var is not available to compare against)
#   - The state file does not exist (nothing to compare)
#   - The stored session_id matches the current env var
# Returns 1 (caller should treat this as a different session) when:
#   - The state file exists with a non-empty stored session_id that does NOT
#     match CLAUDE_CODE_SESSION_ID
#   - The state file exists with an EMPTY stored session_id while
#     CLAUDE_CODE_SESSION_ID is set (treated as stale — matches the
#     gdd_stop_hook.py guard introduced when fixing the URL paste misfire)
gdd_session_continuity_ok() {
  local _state_file="$1"
  local _current="${CLAUDE_CODE_SESSION_ID:-}"
  # No current session id (e.g. Cursor) → cannot compare, fail-open.
  [[ -n "$_current" ]] || return 0
  # No state file → nothing to compare, fail-open.
  [[ -f "$_state_file" ]] || return 0
  local _stored
  _stored="$(grep '^session_id:' "$_state_file" 2>/dev/null | head -1 | sed 's/^session_id:[[:space:]]*//' | sed 's/[[:space:]]*$//')" || true
  # Empty stored session_id while we have a current one → stale file from older
  # tooling or a crash. Treat as different session.
  [[ -n "$_stored" ]] || return 1
  [[ "$_stored" == "$_current" ]] || return 1
  return 0
}

# 毎ターンの注入（UserPromptSubmit・plan-reread）の前に、このセッションの GDD の印があるかを見る。
# 印は、marker が在り、active が true で、このセッションのもの。
# - `CLAUDE_CODE_SESSION_ID` があれば `gdd_session_continuity_ok` で比べる
# - 無いランタイム（Codex など）では、Stop hook の `_session_guard`（gdd_stop_hook.py）と同じく、
#   marker の session_id が空でなければ payload の session_id（入口が読んだ `GDD_HOOK_PAYLOAD`）と
#   比べる。marker の session_id が空なら（id の無いランタイムの setup が書く形）active かだけを見る
gdd_session_marker_present() {
  local _state_file="$1" _stored _sid
  [[ -f "$_state_file" ]] || return 1
  grep -Eqi '^active:[[:space:]]*true' "$_state_file" 2>/dev/null || return 1
  if [[ -n "${CLAUDE_CODE_SESSION_ID:-}" ]]; then
    gdd_session_continuity_ok "$_state_file"
    return
  fi
  _stored="$(grep '^session_id:' "$_state_file" 2>/dev/null | head -1 | sed 's/^session_id:[[:space:]]*//' | sed 's/[[:space:]]*$//')" || true
  [[ -n "$_stored" ]] || return 0
  _sid="$(printf '%s' "${GDD_HOOK_PAYLOAD:-}" | python3 -I -X utf8 -c '
import json, sys
try:
    sid = json.loads(sys.stdin.read()).get("session_id")
except Exception:
    sid = None
sys.stdout.write(sid if isinstance(sid, str) else "")
' 2>/dev/null)" || _sid=""
  [[ "$_sid" == "$_stored" ]]
}

# 既定ブランチの述語（Safe Resume が使う）。集合は scripts/lint-resume-integrity.py・
# scripts/lint-worktree-provenance.py の DEFAULT_BRANCHES と揃える（割れていると、lint は
# 「既定ブランチ上の steering」と警告するのに Safe Resume は通常の再開の案内を出す）。
gdd_is_default_branch() {
  case "${1:-}" in
    main|master|trunk|develop|development) return 0 ;;
  esac
  return 1
}
