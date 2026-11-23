#!/usr/bin/env bash
# merge gate: 対象 PR を記録した GDD worktree の steering を、repo の binding から引く。
#
# binding（`.gdd/tasks/<task_id>/binding.json`。書き手は scripts/gdd_task_binding.py）は
# `worktree_path` と `state_path` で GDD worktree の steering を指す。`.gdd/` は gitignore なので、
# registry は root checkout と各 worktree に分かれて置かれる。steering の解決（lib/detect-steering.sh）は
# 今の worktree の registry から `worktree_path == cwd` で引くので、root や別の worktree から打った
# merge は GDD worktree の steering を見つけられなかった（2026-10-13、GDD を使う別の
# repo の PR: root では untrusted-root-unverified で止まり、marker の無い GDD worktree では PR 台帳の
# 照合が外れて証跡を見ずに通った）。
#
# `gh pr view` の headRefName は使わない（hook の中のネットワークと timeout は素通りになる）。
# binding の state.md の宣言フィールド `PR URL` を対象 PR と照合する。PR URL を記録していない
# steering は当たらない（限界）。
#
# run-merge-gate-hook.sh から source する。hook の変数（PR_NUMBER・PR_URL_ARG・PR_URL_NUMBER・
# REPO_FLAG・UNRESOLVABLE・ENV_REPO_CONFLICT・PROJECT_ROOT・_MG_EXPLICIT_REPO_RE・_MG_URL_MAX・
# GDD_MG_KILL_SWITCH_HINT）と関数（_mg_owner_repo・_mg_equals_ci・_mg_url_matches_number・
# gdd_extract_doc_field・block・_mg_action・_mg_match_steering_by_target・gdd_pre_push_resolve_steering・
# _mg_exec_root・_mg_explicit_target、CD_TARGET・PAYLOAD_CWD_RAW・_MG_CAND_COMMON）を使う。

_MG_VIA_BINDING="false"

# $1 の repo（gh の実行先の repo）の全 worktree の registry の binding のうち、state.md の `PR URL` が
# 対象 PR に当たり、worktree が同じ repo（git の共通ディレクトリが同じ）のものを、state.md の実パスで
# 重複を除いて数える。同じ state.md を指す binding のうち、state.md をその worktree の
# `.steering/<slug>/state.md` に持つものを先に採る。
#   _MG_BINDING_STATUS = one | many | none（読めない・決められないときも none = 呼び出し側の今の判定）
#   one のとき _MG_BINDING_WT（worktree）と、_MG_BINDING_IN_STEERING（state.md が worktree の
#   `.steering/<slug>/state.md` なら true）
gdd_mg_binding_lookup() {
  local _dir="${1:-}" _repo="" _common _wt _sp _real _url _wtc _resolved _remotes _line _held _hits=0 _seen=$'\n'
  local -a _registries=()
  _MG_BINDING_STATUS="none"
  _MG_BINDING_WT=""
  _MG_BINDING_IN_STEERING="false"
  [[ -n "$_dir" && -n "$PR_NUMBER$PR_URL_ARG" ]] || return 0
  [[ "$UNRESOLVABLE" != "true" && "$ENV_REPO_CONFLICT" != "true" ]] || return 0
  _common="$(git -C "$_dir" rev-parse --path-format=absolute --git-common-dir 2>/dev/null)" || return 0
  [[ "$_common" == /* ]] || return 0
  # 照合する repo。URL・`-R` が名指しした repo、無ければ gh が選ぶ repo（origin）。番号だけの merge は、
  # gh が origin を選ぶと決まるとき（remote が origin だけで set-default が無い、または origin が
  # set-default）だけ引く。ほかの remote（upstream など）を gh が選びうるときは引かない（GH_REPO・GH_HOST は
  # ENV_REPO_CONFLICT で上で戻る）。
  if [[ -n "$PR_URL_ARG" ]]; then
    _repo="$(_mg_owner_repo "${PR_URL_ARG%/pull/*}")"
  elif [[ -n "$REPO_FLAG" ]]; then
    [[ "$REPO_FLAG" =~ $_MG_EXPLICIT_REPO_RE ]] || return 0
    _repo="$REPO_FLAG"
  else
    _remotes="$(git -C "$_dir" remote 2>/dev/null || true)"
    _resolved="$(git -C "$_dir" config --get-regexp '^remote\..*\.gh-resolved$' 2>/dev/null || true)"
    [[ "$_resolved" == "remote.origin.gh-resolved base" \
      || ( -z "$_resolved" && "$_remotes" == "origin" ) ]] || return 0
    _repo="$(_mg_owner_repo "$(git -C "$_dir" remote get-url origin 2>/dev/null || true)")"
  fi
  [[ -n "$_repo" ]] || return 0
  while IFS= read -r _line; do
    [[ "$_line" == "worktree /"* ]] && _registries+=("${_line#worktree }/.gdd/tasks")
  done < <(git -C "$_dir" worktree list --porcelain 2>/dev/null || true)
  [[ ${#_registries[@]} -gt 0 ]] || return 0
  while IFS=$'\t' read -r _held _wt _sp _real; do
    [[ "$_wt" == /* && -f "$_sp" && -r "$_sp" ]] || continue
    _url="$(gdd_extract_doc_field "$_sp" "PR URL" 2>/dev/null || true)"
    # 長すぎる URL は `_mg_url_matches_number` が一致として扱うので、ここでは当たりにしない。
    [[ -n "$_url" && "${#_url}" -le "$_MG_URL_MAX" ]] || continue
    _mg_url_matches_number "$_url" "$PR_URL_NUMBER" || _mg_url_matches_number "$_url" "$PR_NUMBER" || continue
    _mg_equals_ci "$_repo" "$(_mg_owner_repo "${_url%/pull/*}")" || continue
    _wtc="$(git -C "$_wt" rev-parse --path-format=absolute --git-common-dir 2>/dev/null)" || continue
    [[ "$_wtc" == "$_common" ]] || continue
    # 同じ state.md を指す binding は 1 件に数える。検査を通った後に除く（先に除くと、検査に落ちる
    # binding が先に並んだときに正しい方を落とす）。
    [[ "$_seen" != *$'\n'"$_real"$'\n'* ]] || continue
    _seen+="$_real"$'\n'
    _hits=$((_hits + 1))
    _MG_BINDING_WT="$_wt"
    _MG_BINDING_IN_STEERING="$_held"
  done < <(python3 -c '
import json, os, re, sys
sys.path.insert(0, sys.argv[1])
from regular_file import read_regular_text
# 下の照合（`_mg_url_matches_number`）に当たりうる state.md だけを、state.md の実パスを添えて出す
# （binding ごとに awk を起動すると、binding が多い repo では hook の持ち時間の多くを使った）。当たりうるのは `/pull/0*<番号>` の後が
# 数字でない URL。通常のファイルだけを読む（FIFO で止まると hook が timeout して素通りになる）。
# 出力できない値（孤立サロゲートなど）は、その binding だけを飛ばす。state.md を worktree の
# `.steering/<slug>/state.md` に持つ binding を先に出す（bash 側は同じ state.md の最初の 1 件を採る）。
nums = [n for n in sys.argv[2].split(",") if n]
pull = re.compile(r"/pull/0*(%s)(?![0-9])" % "|".join(map(re.escape, nums)))
rows = []
for registry in sys.argv[3:]:
    try:
        names = sorted(os.listdir(registry))
    except OSError:
        continue
    for name in names:
        try:
            data = json.loads(read_regular_text(os.path.join(registry, name, "binding.json")) or "")
            wt, sp = data.get("worktree_path"), data.get("state_path")
            real = os.path.realpath(sp) if isinstance(sp, str) else ""
            if not all(isinstance(v, str) and v and not any(c in v for c in "\t\n\r") for v in (wt, sp, real)):
                continue
            if pull.search(read_regular_text(sp, errors="replace") or ""):
                held = (os.path.basename(real) == "state.md"
                        and os.path.dirname(os.path.dirname(real)) == os.path.join(os.path.realpath(wt), ".steering"))
                rows.append(("true" if held else "false", wt, sp, real))
        except Exception:
            continue
for row in sorted(rows, key=lambda r: r[0] != "true"):
    try:
        sys.stdout.write("%s\t%s\t%s\t%s\n" % row)
        sys.stdout.flush()
    except Exception:
        continue
' "${BASH_SOURCE[0]%/*}" "$PR_URL_NUMBER,$PR_NUMBER" "${_registries[@]}" 2>/dev/null || true)
  case "$_hits" in
    0) ;;
    1) _MG_BINDING_STATUS="one" ;;
    *) _MG_BINDING_STATUS="many" ;;
  esac
  return 0
}

# binding が対象 PR の steering を 1 件に決めたら、その worktree を root にする（以降の HEAD・remote・
# 証跡はその worktree のものを読む。gh は元の実行先で走るが、worktree は lookup の起点 $1 と同じ repo
# の worktree で、対象 PR は番号か URL で明示されているので、対象は変わらない）。2 件以上なら不足として通知する。
# $1（lookup の起点）は呼び出し元で違う。
#   - hook 本体の marker 不在の経路: gdd_mg_binding_exec_root の出力。実行先を決められない・信じない
#     ときは空で、binding を引かない。
#   - gdd_mg_binding_switch_when_unmatched: 同じ関数の出力。信じない（1 を返す）ときは呼ばず、空の
#     ときは root（PROJECT_ROOT）から引く。
#   対象を repo つきで明示した merge で実行先を決められないとき、marker のある root では root の repo の
#   binding を引き、marker の無い root では引かない（該当する merge は #454 の実測で無かった。限界）。
# $2 が in-steering なら、1 件に決まった binding の state.md が worktree の `.steering/<slug>/state.md`
# のときだけ切り替える（切り替えた後に steering の解決を通らない呼び出し元のため）。
gdd_mg_binding_switch() {
  gdd_mg_binding_lookup "${1:-}"
  case "$_MG_BINDING_STATUS" in
    one)
      [[ "${2:-}" != "in-steering" || "$_MG_BINDING_IN_STEERING" == "true" ]] || return 0
      cd "$_MG_BINDING_WT" 2>/dev/null || return 0
      PROJECT_ROOT="$_MG_BINDING_WT"
      _MG_VIA_BINDING="true"
      ;;
    many)
      block "⛔ merge gate（reason code: steering-ambiguous）: $(_mg_action steering-ambiguous-binding)。${GDD_MG_KILL_SWITCH_HINT}"
      exit 0
      ;;
  esac
  return 0
}

# binding を引く起点（gh の実行先）。cd 先は、対象を repo つきで明示した merge か、cd が無いときの
# 実行先と同じ repo のときだけ信じる（`cd X & gh pr merge`・`cd X | gh pr merge` では gh が元の cwd で
# 走り、番号は元の cwd の repo の PR を指す。hook 本体の AC-18 と同じ前提）。信じないときは 1 を返す。
gdd_mg_binding_exec_root() {
  local _i=0
  if [[ -n "$CD_TARGET" ]] && ! _mg_explicit_target; then
    [[ -z "$PAYLOAD_CWD_RAW" ]] || _i=1
    [[ -n "${_MG_CAND_COMMON[2]}" && "${_MG_CAND_COMMON[2]}" == "${_MG_CAND_COMMON[$_i]}" ]] || return 1
  fi
  _mg_exec_root
}

# root の steering に対象 PR が無く、判定材料も欠けていない（読めない・PR URL 未記録の steering が
# 無い）ときは、repo の binding が指す GDD worktree の steering で判定する。marker の無い実行先の
# 経路は、hook 本体で切り替え済み。ここでの切り替えは hook 本体の steering の解決より後なので、
# state.md を worktree の `.steering/<slug>/state.md` に持つ binding のときだけ切り替え、steering を
# 新しい root で求め直す（marker の所有は切り替え前の root のまま。marker 不在の経路と同じ）。
# 切り替えた後は、hook 本体の対象 PR の照合が新しい root の `.steering/` からその steering を選ぶ。
# binding は gh の実行先の repo から引く（実行先を決められないときは root から）。hook 本体の
# _mg_match_steering_by_target・gdd_pre_push_resolve_steering を使う。
gdd_mg_binding_switch_when_unmatched() {
  local _dir
  [[ "$_MG_VIA_BINDING" != "true" && -n "$PR_NUMBER$PR_URL_ARG" ]] || return 0
  _mg_match_steering_by_target "$PR_URL_NUMBER" "$PR_NUMBER"
  [[ "$_MG_MATCH_STATUS" == "none" && "$_MG_MATCH_UNREADABLE" != "true" \
    && "$_MG_MATCH_URL_MISSING" != "true" ]] || return 0
  _dir="$(gdd_mg_binding_exec_root)" || return 0
  gdd_mg_binding_switch "${_dir:-$PROJECT_ROOT}" in-steering
  [[ "$_MG_VIA_BINDING" != "true" ]] || gdd_pre_push_resolve_steering "$PROJECT_ROOT"
}
