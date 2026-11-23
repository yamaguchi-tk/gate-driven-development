#!/usr/bin/env bash
# push・PR の前に、pre-PR gate・pre-push gate・completion-check Step 2a・独立レビュー（findings 行）が要求する
# 帳簿の行（state.md・tasklist.md・review-findings.md）がそろっているかを一覧する。読むだけで、何も書かない。
#
# 使い方:
#   bash scripts/check-gate-ledger.sh [--root <dir>] [--steering <dir>] [--tip <ref>] [--base <ref>]
#     --root      repo（既定: cwd の git toplevel）
#     --steering  検算する steering（既定: hook と同じ解決。解決が食い違えば steering 行は invalid）
#     --tip       pre-push の比較先（既定: HEAD）
#     --base      PR の base ref（既定: pre-PR gate と同じ候補）
#
# 出力は 1 行 1 要求で `状態<TAB>要求<TAB>gate<TAB>詳細`。状態は ok / missing（行が無い）/
# invalid（値が条件を満たさない）/ n/a（Task Size などで要求されない）。
# missing・invalid が 1 件でもあれば exit 1、引数の誤りは exit 2。
#
# 行の判定の述語は hook と共有する（hooks/scripts/lib/ の gate-ledger.sh・self-review-evidence.sh・
# merge-gate-evidence.sh、scripts/check-no-raw-task-steering.py）。述語をここに書き足さない
# （書き足すと、検算は通るのに hook の通知が出る、が起きる）。次はこのスクリプトだけのもの:
#   - どの Task Size でどの行を要求するかの制御の流れ（hook の分岐を写している）
#   - steering 行（pre-PR と pre-push の解決が同じ 1 件にそろうか。hook は別々に解く。gate 列は
#     解決がそろわない gate だけ）
#   - reviewed-by 行（completion-check Step 2a。pre-PR・pre-push の hook は見ない。lib/tasklist_parse.py。
#     完了タスクごとに 1 行。Step 2a を通る Task Size で完了タスクが 0 件なら missing）
#   - findings 行（Independent Review の指摘の行き先。hook は見ない。lib/finding_dispositions.py。
#     review-findings.md の、Independent Review 行と同じ sha の IR 節の件数が行と一致するか。gate 列は hook の
#     gate ではない independent-review。push・PR の前に直す行に入る〔references/self-review-lanes.md〕）
# 直すのは、これから走らせるコマンドの gate（pre-PR / pre-push / completion-check / independent-review）を
# gate 列に含む行だけでよい。ただし push の前は、steering 行の詳細が pre-push=multiple なら、
# gate 列と状態によらず詳細を読む（この行は pre-push を判定しない）。
# Codebase Health・PR 本文の機密検査・--head の検査は帳簿の行ではないので見ない。
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
GDD_PLUGIN_ROOT="$PLUGIN_ROOT"
LIB="$PLUGIN_ROOT/hooks/scripts/lib"
# 文字の扱いを hook と同じ UTF-8 にそろえる（LC_ALL・PYTHONUTF8。利用者のロケールで判定を割らない）
# shellcheck source=../hooks/scripts/lib/kill-switch.sh
source "$LIB/kill-switch.sh"
# shellcheck source=../hooks/scripts/lib/detect-steering.sh
source "$LIB/detect-steering.sh"
# shellcheck source=../hooks/scripts/lib/self-review-evidence.sh
source "$LIB/self-review-evidence.sh"
# shellcheck source=../hooks/scripts/lib/merge-gate-evidence.sh
source "$LIB/merge-gate-evidence.sh"
# shellcheck source=../hooks/scripts/lib/gate-ledger.sh
source "$LIB/gate-ledger.sh"

usage() {
  sed -n '5,10p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//' >&2
  exit 2
}

ROOT_ARG="" STEERING_ARG="" TIP_ARG="HEAD" BASE_ARG=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --root) [[ $# -ge 2 ]] || usage; ROOT_ARG="$2"; shift 2 ;;
    --steering) [[ $# -ge 2 ]] || usage; STEERING_ARG="$2"; shift 2 ;;
    --tip) [[ $# -ge 2 ]] || usage; TIP_ARG="$2"; shift 2 ;;
    --base) [[ $# -ge 2 ]] || usage; BASE_ARG="$2"; shift 2 ;;
    -h|--help) usage ;;
    *) usage ;;
  esac
done

FAILED=0
row() {
  # row <状態> <要求> <gate> <詳細>
  printf '%s\t%s\t%s\t%s\n' "$1" "$2" "$3" "$4"
  case "$1" in missing|invalid) FAILED=1 ;; esac
}

WANT=""
if [[ -n "$STEERING_ARG" ]]; then
  WANT="$(cd "$STEERING_ARG" 2>/dev/null && pwd -P)" || {
    echo "check-gate-ledger: --steering が無い: $STEERING_ARG" >&2
    exit 2
  }
fi
ROOT="$(git -C "${ROOT_ARG:-.}" rev-parse --show-toplevel 2>/dev/null)" || {
  echo "check-gate-ledger: git の repo ではありません: ${ROOT_ARG:-.}" >&2
  exit 2
}
cd "$ROOT" || exit 2
ROOT="$(pwd -P)"
HEAD_SHA="$(git rev-parse --quiet --verify HEAD 2>/dev/null || true)"
TIP_SHA="$(git rev-parse --quiet --verify "${TIP_ARG}^{commit}" 2>/dev/null || true)"
if [[ -z "$TIP_SHA" ]]; then
  echo "check-gate-ledger: --tip を commit に解決できません: $TIP_ARG" >&2
  exit 2
fi

# --- active marker（無ければ hook は検査しない。帳簿の行の検算は続ける）---
if grep -q '^active: true' "$ROOT/.claude/gdd-dev.local.md" 2>/dev/null; then
  row ok active pre-PR,pre-push ".claude/gdd-dev.local.md が active: true（hook が検査する）"
else
  row n/a active pre-PR,pre-push "active な GDD の marker が無い（hook は検査せずに通す）"
fi

# --- steering の解決（pre-PR と pre-push の両方の解決を呼ぶ）---
STEERING=""
if gdd_steering_unreadable "$ROOT"; then
  row invalid steering pre-push "読めない steering（symlink・一覧できない dir・読めない state.md）がある（reason code: steering-unreadable）"
else
  PR_STATUS="" PR_DIR=""
  if gdd_detect_active_steering --recount-terminal-binding; then
    PR_STATUS="found"; PR_DIR="$GDD_STEERING_DIR"
  elif [[ "$GDD_STEERING_STATUS" == "multiple" ]]; then
    PR_STATUS="multiple"
  elif gdd_detect_completed_steering_for_pr; then
    PR_STATUS="found"; PR_DIR="$GDD_STEERING_DIR"
  else
    PR_STATUS="${GDD_STEERING_STATUS:-none}"
  fi
  gdd_pre_push_resolve_steering "$ROOT"
  PP_STATUS="$GDD_PP_STEERING_STATUS" PP_DIR=""
  if [[ "$PP_STATUS" == "found" ]]; then
    PP_DIR="$(cd "$GDD_PP_STEERING_DIR" 2>/dev/null && pwd -P)"
  fi
  [[ -z "$PR_DIR" ]] || PR_DIR="$(cd "$PR_DIR" 2>/dev/null && pwd -P)"
  DETAIL="pre-PR=${PR_STATUS}${PR_DIR:+:${PR_DIR#"$ROOT"/}} pre-push=${PP_STATUS}${GDD_PP_STEERING_REASON:+(${GDD_PP_STEERING_REASON})}${PP_DIR:+:${PP_DIR#"$ROOT"/}}"
  # 解決がそろわない gate だけを gate 列に入れる。比べる先は --steering、無ければ pre-PR の解決。
  STEERING_GATES=""
  [[ "$PR_STATUS" == "found" && ( -z "$WANT" || "$PR_DIR" == "$WANT" ) ]] || STEERING_GATES="pre-PR"
  EXPECTED_DIR="${WANT:-$PR_DIR}"
  # pre-push の none は hook が検査せずに通し、multiple は tip の証跡で選ぶので、数えるのは found の食い違いだけ。
  # 限界: multiple で tip の証跡を持つ steering が 1 件に決まらないと hook は通知する（steering-multiple）が、
  # その選び方（hook の step 8b）はここに写していないので、この行は pre-push を挙げない（詳細で知らせる）。
  # 写すのは、tip で選ぶ処理を呼ぶ 2 つ目の実装が要るようになったときか、検算が pre-push を挙げなかった
  # 後に steering-multiple の通知を受けたと利用者が報告したとき（hook は通知と would-block:steering-multiple を pre-push-gate-suppressed.log に記録する）。
  PP_NOTE=""
  if [[ "$PP_STATUS" == "multiple" ]]; then
    PP_NOTE="。pre-push は、valid な Pre-Push Self Review の sha（大文字小文字は区別しない）が tip の sha の先頭と一致する steering（cancelled を含む）がちょうど 1 件ならそれを検査し、0 件・2 件以上なら通知する（steering-multiple。止めずに通す。この行は pre-push を判定しない。1 件に決まらないときは、どれを終えるかユーザーに確認したうえで、使わない steering（PR が open のものは除く）を references/self-review-lanes.md の「使わないステアリングの終え方」に従って終える）"
  fi
  if [[ "$PP_STATUS" == "found" && -n "$EXPECTED_DIR" && "$PP_DIR" != "$EXPECTED_DIR" ]]; then
    STEERING_GATES="${STEERING_GATES:+${STEERING_GATES},}pre-push"
  fi
  if [[ -z "$STEERING_GATES" ]]; then
    row ok steering pre-PR,pre-push "${DETAIL}${PP_NOTE}"
  else
    row invalid steering "$STEERING_GATES" "${DETAIL}（hook の解決が 1 件にそろわない。--steering で指定した steering の行は検算を続ける）${PP_NOTE}"
  fi
  STEERING="${WANT:-${PR_DIR:-$PP_DIR}}"
fi
if [[ -z "$STEERING" ]]; then
  exit 1
fi
STATE="$STEERING/state.md"
TASKLIST="$STEERING/tasklist.md"

# --- raw steering の除外（pre-PR。active marker が無くても検査する）---
BASE_REF="$(gdd_resolve_base_ref "$ROOT" "$BASE_ARG")"
if [[ -z "$BASE_REF" ]]; then
  row invalid raw-steering pre-PR "PR の base ref を解決できない（--base で commit に解決できる branch を指定する）"
elif RAW_OUT="$(python3 "$PLUGIN_ROOT/scripts/check-no-raw-task-steering.py" --root "$ROOT" --against "$BASE_REF" 2>&1)"; then
  row ok raw-steering pre-PR "${BASE_REF}...HEAD に .steering が無い"
else
  row invalid raw-steering pre-PR "${BASE_REF}...HEAD に .steering がある: $(printf '%s' "$RAW_OUT" | tr '\n' ' ')"
fi

# --- Next Action=done（pre-PR。tasklist.md を先に読む）---
NEXT_ACTION="$(gdd_pr_next_action "$STEERING")"
if [[ -z "$NEXT_ACTION" ]]; then
  row missing next-action-done pre-PR "tasklist.md・state.md に Next Action が無い"
elif [[ "$(gdd_value_head "$NEXT_ACTION")" != "done" ]]; then
  row invalid next-action-done pre-PR "Next Action=${NEXT_ACTION}（done でない）"
else
  row ok next-action-done pre-PR "Next Action=done"
fi

# --- Task Size ---
TASK_SIZE_RAW="$(gdd_extract_doc_field "$STATE" "Task Size" 2>/dev/null || true)"
TASK_SIZE="$(gdd_state_task_size "$STATE")"
row ok task-size pre-PR,pre-push "Task Size=${TASK_SIZE_RAW:-（無い）} → ${TASK_SIZE} として検査"
REQUIRES_DRY="false"
gdd_task_size_requires_dry "$TASK_SIZE" && REQUIRES_DRY="true"
# pre-push は解決が multiple のとき tip の証跡で選んだ steering を standard で検査する（hook の step 8b）。
PP_TASK_SIZE="$TASK_SIZE"
[[ "${PP_STATUS:-}" == "multiple" ]] && PP_TASK_SIZE="standard"
PP_REQUIRES_DRY="false"
gdd_task_size_requires_dry "$PP_TASK_SIZE" && PP_REQUIRES_DRY="true"

# --- ADR distilled（pre-PR）---
ADR_DISTILLED="$(gdd_extract_doc_field "$STATE" "ADR distilled" 2>/dev/null || true)"
ADR_REASON="$(gdd_adr_reason "$(gdd_extract_doc_field "$STATE" "ADR distillation reason" 2>/dev/null || true)" "$ADR_DISTILLED")"
ADR_STATUS="$(gdd_adr_status "$ADR_DISTILLED")"
if [[ -z "$ADR_DISTILLED" ]]; then
  row missing adr-distilled pre-PR "state.md に ADR distilled が無い"
elif [[ "$ADR_STATUS" == "yes" ]]; then
  if [[ -n "$BASE_REF" ]] && gdd_pr_diff_has_adr "$ROOT" "$BASE_REF"; then
    row ok adr-distilled pre-PR "yes（docs/adr/ が PR の diff にある）"
  else
    row invalid adr-distilled pre-PR "yes だが docs/adr/*.md が ${BASE_REF:-base}...HEAD の diff に無い"
  fi
elif [[ "$ADR_STATUS" == "not_applicable" ]]; then
  if gdd_adr_not_applicable_allowed "$TASK_SIZE_RAW" "$ADR_REASON" "$STATE"; then
    row ok adr-distilled pre-PR "not_applicable（理由: ${ADR_REASON:-Task Size}）"
  elif [[ "${GDD_ADR_NA_REASON:-}" == "handoff" ]]; then
    row invalid adr-distilled pre-PR "not_applicable だが state.md に Decision Handoff がある（Task Size・理由によらず docs/adr/ へ蒸留する）"
  else
    row invalid adr-distilled pre-PR "not_applicable の理由が足りない（trivial / quick express / 重要判断なし）"
  fi
else
  row invalid adr-distilled pre-PR "ADR distilled=${ADR_DISTILLED}（yes か not_applicable でない）"
fi

RECOVERY_CORE="レビューを回し直してから行を書く（sha だけを書き換えない）。worklog.md へ移しただけなら、その行をそのまま戻す"
RECOVERY="。証跡を直すときは、${RECOVERY_CORE}"

# self review の行を 1 本検算する。
# check_self_review <要求> <gate> <field> <Task Size> <dry を要求するか> <比較する sha（空なら比較しない）>
check_self_review() {
  local req="$1" gate="$2" field="$3" size="$4" need_dry="$5" expected="$6"
  if [[ -z "$(gdd_extract_doc_field "$STATE" "$field" 2>/dev/null || true)" ]]; then
    row missing "$req" "$gate" "state.md に ${field} が無い${RECOVERY}"
    return
  fi
  gdd_parse_self_review_field "$STATE" "$field" "$size"
  if [[ "$GDD_SR_VALID" != "true" ]]; then
    row invalid "$req" "$gate" "${field} の書式が不正（検出: ${GDD_SR_MISSING_KEYS}）"
  elif [[ -n "$expected" ]] && ! gdd_evidence_sha_matches "$ROOT" "$GDD_SR_SHA" "$expected"; then
    row invalid "$req" "$gate" "${field} の sha ${GDD_SR_SHA} が ${expected:0:12} と一致しない（default branch を取り込むだけの merge commit で Independent Review を引き継ぐときは、references/self-review-lanes.md § Independent Review の引き継ぎのとおり sha を merge sha に書き換えてよい。それ以外は、${RECOVERY_CORE}）"
  elif [[ "$need_dry" == "true" && ( "$GDD_SR_DRY" != "yes" || "$GDD_SR_CONSECUTIVE_CLEAN" == "0" ) ]]; then
    row invalid "$req" "$gate" "${field} が dry: yes に到達していない（dry: ${GDD_SR_DRY} / consecutive_clean: ${GDD_SR_CONSECUTIVE_CLEAN}）${RECOVERY}"
  else
    row ok "$req" "$gate" "${field}: ${GDD_SR_SHA} dry: ${GDD_SR_DRY}"
  fi
}

# --- Pre-PR Self Review（pre-PR。dry を要求する Task Size だけ。sha は比べない）---
if [[ "$REQUIRES_DRY" == "true" ]]; then
  check_self_review pre-pr-self-review pre-PR "Pre-PR Self Review" "$TASK_SIZE" true ""
else
  row n/a pre-pr-self-review pre-PR "Task Size=${TASK_SIZE} では要求しない"
fi

# --- Pre-Push Self Review（pre-push。trivial 以外。sha は push 対象の tip）---
if [[ "$PP_TASK_SIZE" == "trivial" ]]; then
  row n/a pre-push-self-review pre-push "Task Size=trivial では要求しない"
else
  check_self_review pre-push-self-review pre-push "Pre-Push Self Review" "$PP_TASK_SIZE" "$PP_REQUIRES_DRY" "$TIP_SHA"
fi

# --- Independent Review（dry を要求する Task Size。pre-PR は HEAD、pre-push は tip と比べる）---
IR_GATES=""
[[ "$REQUIRES_DRY" == "true" ]] && IR_GATES="pre-PR"
[[ "$PP_REQUIRES_DRY" == "true" ]] && IR_GATES="${IR_GATES:+${IR_GATES},}pre-push"
if [[ -z "$IR_GATES" ]]; then
  row n/a independent-review pre-PR,pre-push "Task Size=${TASK_SIZE} では要求しない"
elif [[ -z "$(gdd_extract_doc_field "$STATE" "Independent Review" 2>/dev/null || true)" ]]; then
  row missing independent-review "$IR_GATES" "state.md に Independent Review が無い${RECOVERY}"
else
  gdd_parse_merge_gate_field "$STATE" "Independent Review"
  # sha のずれは gate ごとに比較先が違う。gate 列には、ずれた gate だけを入れる。
  # 一致しなくても、main を取り込むだけの merge commit なら引き継ぐ（hook と同じ述語。
  # 正本: references/self-review-lanes.md § Independent Review の引き継ぎ）。検算には hook の
  # timeout が無いので、持ち時間は掛けない（判定の上限 5 秒は残る）。
  IR_STALE_GATES="" IR_STALE="" IR_CARRIED=""
  if [[ "$IR_GATES" == *pre-PR* ]] && ! gdd_evidence_sha_matches "$ROOT" "$GDD_MG_SHA" "$HEAD_SHA"; then
    if gdd_ir_carry_matches "$ROOT" "$STATE" "$GDD_MG_SHA" "$HEAD_SHA" 100000; then
      IR_CARRIED="（Independent Review Carry で引き継ぎ）"
    else
      IR_STALE_GATES="pre-PR"; IR_STALE="HEAD ${HEAD_SHA:0:12}（引き継げない理由: ${GDD_IR_CARRY_REASON}）"
    fi
  fi
  if [[ "$IR_GATES" == *pre-push* ]] && ! gdd_evidence_sha_matches "$ROOT" "$GDD_MG_SHA" "$TIP_SHA"; then
    if gdd_ir_carry_matches "$ROOT" "$STATE" "$GDD_MG_SHA" "$TIP_SHA" 100000; then
      IR_CARRIED="（Independent Review Carry で引き継ぎ）"
    else
      IR_STALE_GATES="${IR_STALE_GATES:+${IR_STALE_GATES},}pre-push"
      IR_STALE="${IR_STALE:+${IR_STALE}・}tip ${TIP_SHA:0:12}（引き継げない理由: ${GDD_IR_CARRY_REASON}）"
    fi
  fi
  if [[ "$GDD_MG_VALID" != "true" ]]; then
    row invalid independent-review "$IR_GATES" "Independent Review の書式が不正（理由: ${GDD_MG_REASON:-unknown}。${GDD_IR_RECOVERY_CORE}）${RECOVERY}"
  elif ! gdd_independent_review_clean; then
    row invalid independent-review "$IR_GATES" "Independent Review に high: ${GDD_MG_HIGH} / blocking: ${GDD_MG_BLOCKING} が残る（どちらも 0 が要る）${RECOVERY}"
  elif [[ -n "$IR_STALE" ]]; then
    row invalid independent-review "$IR_STALE_GATES" "Independent Review の sha ${GDD_MG_SHA} が ${IR_STALE} と一致しない${RECOVERY}"
  else
    row ok independent-review "$IR_GATES" "Independent Review: ${GDD_MG_SHA} high 0 / blocking 0${IR_CARRIED}"
  fi
fi

# --- 独立レビューの指摘の行き先（review-findings.md。正本: references/finding-dispositions.md）---
# Independent Review 行の sha の IR 節があり、件数が行の high・medium・blocking と一致するか。
# 行の値は上と同じパーサ（gdd_parse_merge_gate_field）で読み直す。行が無い・書式が不正なら上の行が不足を出す。
if [[ -z "$IR_GATES" ]]; then
  row n/a findings independent-review "Task Size=${TASK_SIZE} では Independent Review を要求しない"
else
  gdd_parse_merge_gate_field "$STATE" "Independent Review"
  if [[ "$GDD_MG_VALID" != "true" ]]; then
    row n/a findings independent-review "Independent Review 行が読めないので突き合わせない（independent-review 行を先に直す）"
  else
    FINDINGS="$(python3 -I -X utf8 - "$PLUGIN_ROOT/hooks/scripts" "$STEERING/review-findings.md" \
      "$GDD_MG_SHA" "$GDD_MG_HIGH" "$GDD_MG_MEDIUM" "${GDD_MG_BLOCKING:-0}" <<'PY'
import sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from lib.finding_dispositions import ir_count_errors
from lib.regular_file import read_regular_text

path = Path(sys.argv[2])
if not path.exists() and not path.is_symlink():
    print(f"missing\t{path.name} が無い（Independent Review の指摘の行き先を書く）")
    sys.exit(0)
text = read_regular_text(path)
if text is None:
    print(f"invalid\t{path.name} が通常のファイルでない")
    sys.exit(0)
status, errors = ir_count_errors(text, sys.argv[3], int(sys.argv[4]), int(sys.argv[5]), int(sys.argv[6]))
print(f"{status}\t" + ("; ".join(errors) if errors else f"IR の節が Independent Review の sha と件数に一致する"))
PY
)" || FINDINGS=$'invalid\treview-findings.md を解析できない'
    IFS=$'\t' read -r _status _detail <<< "$FINDINGS"
    [[ -n "$_status" ]] || { _status=invalid; _detail="review-findings.md の検査が何も出さなかった"; }
    row "$_status" findings independent-review "${_detail}（正本: references/finding-dispositions.md）"
  fi
fi

# --- 完了タスクごとの Reviewed by（completion-check Step 2a。quick (express) は Step 2a を飛ばす）---
if [[ "$TASK_SIZE" == "quick (express)" || "$TASK_SIZE" == "trivial" ]]; then
  row n/a reviewed-by completion-check "Task Size=${TASK_SIZE} では completion-check の Step 2a を通らない"
elif [[ ! -r "$TASKLIST" ]]; then
  row missing reviewed-by completion-check "tasklist.md を読めない"
else
  REVIEWED="$(python3 -I -X utf8 - "$LIB" "$TASKLIST" <<'PY'
import sys
sys.path.insert(0, sys.argv[1])
from tasklist_parse import reviewed_by_rows

with open(sys.argv[2], encoding="utf-8") as f:
    for status, detail in reviewed_by_rows(f.read()):
        print(f"{status}\t{detail}")
PY
)" || REVIEWED=$'invalid\ttasklist.md を解析できない'
  while IFS=$'\t' read -r _status _detail; do
    row "$_status" reviewed-by completion-check "$_detail"
  done <<< "$REVIEWED"
fi

exit "$FAILED"
