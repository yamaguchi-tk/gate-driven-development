#!/usr/bin/env bash
set -euo pipefail

# PreToolUse hook: active GDD 中の `git push` を、セルフレビュー証跡を見て検査する
# runtime gate。design.md § pre-push gate の判定順（確定版）に従う。不足を見つけても
# 止めずに通し、実行後の通知と would-block の記録に残す（下の `block()`）。想定外エラーは
# 「通す + hook-error 記録」。

# hook が継承する `CDPATH` が非空だと、bash の `cd` は相対パスを CDPATH の先で解決し、
# 移った先の絶対パスを stdout に印字する。通知の JSON の前に行が付いて JSON が読めなくなり、
# 別の場所の steering を判定しうる。以降の `cd` は hook 内部の解決用なので外す（merge gate と
# 同じ。直下の SCRIPT_DIR の解決も `cd` を使うので、その前に置く）。
unset CDPATH
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/kill-switch.sh"
gdd_kill_switch_active && exit 0
# shellcheck source=lib/self-review-evidence.sh
source "$SCRIPT_DIR/lib/self-review-evidence.sh"
# shellcheck source=lib/gate-ledger.sh
source "$SCRIPT_DIR/lib/gate-ledger.sh"
# shellcheck source=lib/gate-notice.sh
source "$SCRIPT_DIR/lib/gate-notice.sh"

# 止めずに通す。不足は実行後の通知と would-block:<code> の記録に残す（lib/gate-notice.sh）。
# 呼び出しは `block <code> <本文>`。code は本文から切り出さずに宣言して渡す。
block() {
  gdd_gate_notice "pre-push-gate-suppressed.log" "$1" "実行後の通知: pre-push gate は止めずに通した。push が成功した場合は、次の不足を直してから次の push をしてください。push が失敗した場合は、次の不足を直してから再実行してください。$2"
}

# step 2: payload に push が含まれなければ最優先で即通過
PAYLOAD="$(cat 2>/dev/null || true)"
case "$PAYLOAD" in
  *push*) ;;
  *) exit 0 ;;
esac

PROCESS_CWD="$(pwd)"

# step 3〜4（+ step 6 の判定材料）: payload 解釈・push検出・候補root解決・opt-out・
# refspec を **python3 起動 1 回**にまとめる（design.md § hook の出力形式・失敗時の
# 挙動「step 1〜3 は python3 起動 1 回に収める」）。`push` を含むだけの無関係な Bash
# 呼び出しにも interpreter 起動コストが乗るため、値ごとに python3 を起こさない。
# 出力は 1 行 1 レコードの `<key>\t<value>`（root は複数行になりうる）。
# 解釈できない payload / 内部エラーは「出力なし」= 非 push 扱いで fail-open する。
IS_PUSH="false"
UNRESOLVABLE="false"
OPTOUT_ACCEPTED="false"
# REFSPEC_JSON は step 8（T-9 のスコープ）の入力。ここで一緒に取り出しておくことで
# T-9 は末尾へ追記するだけで済み、この parse ブロックを再編せずに済む。
REFSPEC_JSON=""
# `mapfile`/`readarray` は bash 4+ 専用（macOS 既定の /bin/bash は 3.2 系で
# 未対応・実測: `mapfile: command not found`）。既存 hook 群も bash 4+ 専用機能を
# 使っていないため、ここも while-read + 配列 append で bash 3.2 互換にする。
CANDIDATE_ROOTS=()
while IFS=$'\t' read -r _k _v; do
  # shellcheck disable=SC2034  # REFSPEC_JSON は T-9 が step 8 で参照する（T-8 時点では未使用）
  case "$_k" in
    is_push) IS_PUSH="$_v" ;;
    unresolvable) UNRESOLVABLE="$_v" ;;
    optout) OPTOUT_ACCEPTED="$_v" ;;
    refspec) REFSPEC_JSON="$_v" ;;
    root) CANDIDATE_ROOTS+=("$_v") ;;
  esac
done < <(printf '%s' "$PAYLOAD" | python3 -c '
import json, os, sys
sys.path.insert(0, sys.argv[2])
import push_command_parse as pcp
import hook_cwd

def emit(key, value):
    # UTF-8 に符号化できない lone surrogate（JSON の `\ud800`）で例外になると、残りの root
    # も fallback も出ずに通す。surrogateescape で往復する値（UTF-8 でない byte のパス）は
    # そのまま出し、それでも符号化できないものだけを文字化けさせる（ディレクトリに解決
    # できない root になり、下の fallback に落ちる）。
    line = "%s\t%s\n" % (key, value)
    try:
        data = line.encode("utf-8", "surrogateescape")
    except UnicodeEncodeError:
        data = line.encode("utf-8", "backslashreplace")
    sys.stdout.buffer.write(data)

def absolute_root(root, base):
    # `~`・`$HOME` を展開し（pre-PR gate と同じ関数）、process の cwd を基準に絶対パスに
    # する。相対パスのままだと、hook が root へ cd した後の resolver・`git -C`・`find` が
    # cd 先から解決して steering を見失う。`-P` のような root も cd の option に化けない。
    # 空の root（`--git-dir=` の空の値）は process の cwd に化けさせない。展開で例外に
    # なるもの（`~` の後の user 名に NUL など）は展開せずに絶対パスにし、ほかの root の
    # 判定を止めない。
    if not root:
        return root
    try:
        return os.path.abspath(os.path.join(base, os.path.expanduser(os.path.expandvars(root))))
    except Exception:
        return os.path.normpath(os.path.join(base, root))

try:
    payload = json.load(sys.stdin)
    tool_input = payload.get("tool_input", {})
    if not isinstance(tool_input, dict):
        tool_input = {}
    command = tool_input.get("command") or tool_input.get("cmd") or ""
    payload_cwd = tool_input.get("cwd") or tool_input.get("workdir") or ""
    if not isinstance(command, str):
        command = ""
    if not isinstance(payload_cwd, str):
        payload_cwd = ""
    if not command:
        raise SystemExit
    process_cwd = sys.argv[1]
    # Claude Code は cwd を payload の最上位に持つ。使えるなら、相対の root を絶対パスにする基準と
    # fallback の候補をそれにする（lib/hook_cwd.py）。lib は `cd "$PROJECT_ROOT"` の後に呼ぶので、
    # bash のプロセスの cwd は移さない。
    process_cwd = hook_cwd.toplevel_cwd(payload) or process_cwd
    # A-11 決着（T-4 Carry Forward）: opt-out 境界値は tokenize_with_boundary の
    # 第2戻り値（原文 token 列の長さ）を使う。len(tokens) は展開後の token 数を
    # 含むため、bash -c / eval 経由の opt-out を誤って受理する fail-open になる
    # （実測: `bash -c "true; GDD_SKIP_PRE_PUSH_GATE=1 git push"` 等）。
    tokens, raw_count = pcp.tokenize_with_boundary(command)
    is_push, git_index = pcp.is_git_push(tokens)
    if not is_push:
        raise SystemExit
    optout = pcp.find_optout(tokens, original_token_count=raw_count)
    roots = pcp.resolve_candidate_roots(tokens, git_index, payload_cwd, process_cwd)
    refspec = pcp.classify_refspec(tokens, git_index)
    emit("is_push", "true")
    emit("unresolvable", "true" if roots.get("unresolvable") else "false")
    emit("optout", "true" if optout.get("accepted") else "false")
    emit("refspec", json.dumps(refspec, ensure_ascii=False))
    resolved = [absolute_root(r, process_cwd) for r in roots.get("roots", [])]
    for r in resolved:
        emit("root", r)
    # 先頭の root（-C > cd）がディレクトリに解決できない（コマンド置換・未定義の変数・
    # 存在しないパス）ときは、hook はコマンドがどこで走るかを決められない。コマンド置換は
    # 作業ディレクトリから解決されうるし、`;` で続く push は作業ディレクトリで走る。その
    # root だけを見て通さないよう、優先順の残り（payload の cwd・process の cwd）も候補に足す。
    if resolved and not os.path.isdir(resolved[0]):
        for fallback in (absolute_root(payload_cwd, process_cwd), process_cwd):
            if fallback:
                emit("root", fallback)
except Exception:
    pass
' "$PROCESS_CWD" "$SCRIPT_DIR/lib" 2>/dev/null || true)

[[ "$IS_PUSH" == "true" ]] || exit 0

# block reason に必ず含める 3 要素（design.md § 復旧可能性）。実パス / steering slug は
# 一切埋め込まず、literal token `<steering-dir>/state.md` のみを使う（AC-18）。
# 定義は **最初の block（step 4 の unresolvable-root）より前** に置く。後段に置くと
# step 4 / step 6 の 2 本だけが手書きリテラルの重複になり、ドリフト源が残る。
# 要素 1・2 は lib の `GDD_SR_RECOVERY_CORE`（pre-PR gate と共有する唯一の正本）。
# 本 hook が足すのは要素 3（escape hatch）だけ — `GDD_SKIP_PRE_PUSH_GATE` の受理面は
# AC-4 により pre-push gate 限定であり、pre-PR gate 側には存在しない。
_PP_RECOVERY_SUFFIX="。${GDD_SR_RECOVERY_CORE}。緊急時は GDD_SKIP_PRE_PUSH_GATE=1 git push ...（git の直前に置く）"

# step 5: 候補 root 集合すべてに active GDD 判定を行う
ANY_ACTIVE="false"
ACTIVE_ROOT=""
# marker は repo の toplevel にある。サブディレクトリを指す root（`cd repo/sub`・`git -C sub`）
# も toplevel で判定する（pre-PR gate・merge gate と同じ）。toplevel を取れないとき（git の
# 外）と、root 自身に marker があるときに備えて、root そのものも見る。
for _cand in "${CANDIDATE_ROOTS[@]}"; do
  [[ -n "$_cand" && -d "$_cand" ]] || continue
  _top="$(git -C "$_cand" rev-parse --show-toplevel 2>/dev/null || true)"
  for _root in ${_top:+"$_top"} "$_cand"; do
    _local_state="$_root/.claude/gdd-dev.local.md"
    [[ -f "$_local_state" ]] || continue
    grep -q '^active: true' "$_local_state" 2>/dev/null || continue
    ANY_ACTIVE="true"
    ACTIVE_ROOT="$_root"
    break
  done
  [[ "$ANY_ACTIVE" == "true" ]] || continue
  if ! gdd_session_continuity_ok "$_local_state"; then
    gdd_sr_log_event "session-mismatch" "-" "$_root" "$(git -C "$_root" rev-parse HEAD 2>/dev/null || echo unknown)" "-" || true
    exit 0
  fi
  break
done

[[ "$ANY_ACTIVE" == "true" ]] || exit 0

if [[ "$UNRESOLVABLE" == "true" ]]; then
  block unresolvable-root "⛔ pre-push gate: git の --git-dir / --work-tree を伴う push は解決できません（reason code: unresolvable-root）${_PP_RECOVERY_SUFFIX}"
  exit 0
fi

PROJECT_ROOT="$ACTIVE_ROOT"
cd "$PROJECT_ROOT" 2>/dev/null || { gdd_sr_log_event "hook-error" "-" "$PROJECT_ROOT" "unknown" "-" || true; exit 0; }

HEAD_SHA="$(git -C "$PROJECT_ROOT" rev-parse HEAD 2>/dev/null || echo unknown)"

# step 6: escape hatch（プロセス env、または token 列の command-prefix）
OPTOUT_VIA=""
if [[ "${GDD_SKIP_PRE_PUSH_GATE:-}" == "1" ]]; then
  OPTOUT_VIA="process-env"
elif [[ "$OPTOUT_ACCEPTED" == "true" ]]; then
  OPTOUT_VIA="command-prefix"
fi

if [[ -n "$OPTOUT_VIA" ]]; then
  # ここは「記録できないなら不足として通知する」判定経路。継続経路（merge gate の
  # `( _mg_log_suppressed ... ) 2>/dev/null || true`）とは **意図が逆** なので `|| true` を付けない。
  # subshell にするのは、helper 内で将来 set -u 由来の即死要因が増えても、それを rc≠0 として
  # 受け取り直下の block() の通知へ倒すため（`if` は set -e を抑止するが set -u の即死は抑止しない）。
  # ただし捕捉できるのは set -u の即死と明示 exit のみ。errexit / pipefail 由来の中間失敗は
  # 条件位置では抑止されるため捕まらない。記録失敗の保証本体は helper の戻り値契約側にある。
  if ( gdd_sr_log_event "optout" "-" "$PROJECT_ROOT" "$HEAD_SHA" "$OPTOUT_VIA" ) 2>/dev/null; then
    exit 0
  fi
  block optout-log-write-failed "⛔ pre-push gate: escape hatch のログ記録に失敗しました（reason code: optout-log-write-failed）${_PP_RECOVERY_SUFFIX}"
  exit 0
fi

# 列挙から落ちる steering（symlink・一覧できない task dir・読めない state.md）は、resolver
# には「無い」に見える。none でも found でも、その steering の push を検査せずに通して
# しまうので、解決の結果によらず不足として通知する（merge gate の state-unreadable と同じ判定）。
# resolver より前に置く（FIFO の state.md などを resolver が開く前に、通知して終える）。
if gdd_steering_unreadable "$PROJECT_ROOT"; then
  block steering-unreadable "⛔ pre-push gate: ステアリングの中に、シンボリックリンク・一覧できないディレクトリ・読めない状態ファイルがあり、どのステアリングの push かを確かめられません。権限を直すか、シンボリックリンクを実体のディレクトリ・ファイルに置き換えてください（reason code: steering-unreadable）${_PP_RECOVERY_SUFFIX}"
  exit 0
fi
# step 7: active steering の一意解決（design.md § steering resolver の設計・AC-25）。
# hook プロセス自身が既に `cd "$PROJECT_ROOT"` 済み（非 subshell）なので、そのまま
# 呼べる（gdd_pre_push_resolve_steering の呼び出し規約どおり）。
gdd_pre_push_resolve_steering "$PROJECT_ROOT"
# 検査する steering を 1 件に決められない（候補が 2 件以上の）`multiple` は、step 8 で
# push 対象の tip を決めた後に、tip の証跡を持つ steering で解く（下の step 8b）。
if [[ "$GDD_PP_STEERING_STATUS" != "found" && "$GDD_PP_STEERING_STATUS" != "multiple" ]]; then
  gdd_sr_log_event "unresolved-steering" "$GDD_PP_STEERING_REASON" "$PROJECT_ROOT" "$HEAD_SHA" "-" || true
  exit 0
fi

# step 8: push 対象 ref の tip 解決（AC-16）。REFSPEC_JSON は step 1〜3 の python3
# 起動（本体冒頭）で既に解決済みの値なので、ここでは python3 を新規起動せず bash の
# 文字列展開だけで読む（design.md 115 行「step 1〜3 は python3 起動 1 回に収める」）。
REFSPEC_AMBIGUOUS="false"
case "$REFSPEC_JSON" in
  *'"ambiguous": true'*) REFSPEC_AMBIGUOUS="true" ;;
esac
EXPLICIT_REF=""
_REFSPEC_REST="${REFSPEC_JSON#*\"explicit_ref\":}"
_REFSPEC_REST="${_REFSPEC_REST# }"
case "$_REFSPEC_REST" in
  \"*)
    EXPLICIT_REF="${_REFSPEC_REST#\"}"
    EXPLICIT_REF="${EXPLICIT_REF%%\"*}"
    ;;
esac

if [[ "$REFSPEC_AMBIGUOUS" == "true" ]]; then
  block refspec-ambiguous "⛔ pre-push gate: push 対象 ref を一意に解決できません（reason code: refspec-ambiguous）${_PP_RECOVERY_SUFFIX}"
  exit 0
fi

TIP_SHA=""
if [[ -n "$EXPLICIT_REF" ]]; then
  TIP_SHA="$(git -C "$PROJECT_ROOT" rev-parse --quiet --verify "$EXPLICIT_REF" 2>/dev/null || true)"
else
  TIP_SHA="$HEAD_SHA"
fi
if [[ -z "$TIP_SHA" ]]; then
  block refspec-ambiguous "⛔ pre-push gate: push 対象 ref を一意に解決できません（reason code: refspec-ambiguous）${_PP_RECOVERY_SUFFIX}"
  exit 0
fi

# Task Size を取得し正規化する（AC-20）。requirements.md § Task Size 別の発火表どおり、
# trivial は無条件で通し、express だけ dry を要求しない。未知値・部分一致・読めない
# state.md は fail-closed 側の standard 扱いにする（design.md 132 行）。読めない state.md で
# awk が失敗しても、set -e で hook ごと落ちない（落ちると push が検査されずに通る）。

# step 8b: `multiple` のときは、全 steering（cancelled を含む）の Pre-Push Self Review を
# 読み、証跡の sha（大文字小文字は区別しない）が push 対象の tip の sha の先頭と一致する
# ものがちょうど 1 件なら、それを検査する（sha の解決は step 11 が行う）。証跡が valid で
# ないもの・読めない state.md は一致としない。0 件・2 件以上は、どのタスクの push かを決める材料が無いので
# 選ばずに不足として通知する（active が 2 件でも終端が 2 件でも同じ扱い。pre-PR gate も primary の
# multiple を不足として通知する）。
# - 選んだ steering の Task Size では検査を緩めない（trivial・quick の steering に tip の
#   証跡を書けば、候補の外の cancelled でも検査を省けてしまう）。parse も以降の検査も
#   standard で行う
# - 全件を parse すると hook の timeout（超えると無出力のまま素通り）に件数で届くので、
#   tip の sha の先頭 7 桁を含む state.md だけを 1 回の grep で先に絞る。一致する証跡の sha
#   は tip の先頭 7 桁以上を含むので、一致しうるものは落ちない（比較も先頭一致なので、
#   grep と比較で受理する集合が同じになる）
_PP_TIP_RESOLVED="false"
_PP_TIP_NOTE=""
if [[ "$GDD_PP_STEERING_STATUS" == "multiple" ]]; then
  _PP_TIP_MATCHES=()
  while IFS= read -r _pp_state; do
    [[ -n "$_pp_state" ]] || continue
    gdd_parse_self_review_field "$_pp_state" "Pre-Push Self Review" "standard"
    [[ "$GDD_SR_VALID" == "true" ]] || continue
    _pp_sha="$(printf '%s' "$GDD_SR_SHA" | LC_ALL=C tr '[:upper:]' '[:lower:]')"
    if [[ -n "$_pp_sha" && "$TIP_SHA" == "$_pp_sha"* ]]; then
      _PP_TIP_MATCHES+=("$_pp_state")
    fi
  done < <(find "$PROJECT_ROOT/.steering" -mindepth 2 -maxdepth 2 -name state.md -type f \
    -exec grep -Fil -- "${TIP_SHA:0:7}" {} + 2>/dev/null | sort || true)
  if [[ ${#_PP_TIP_MATCHES[@]} -ne 1 ]]; then
    block steering-multiple "⛔ pre-push gate: 作業中または完了済みのステアリングが複数あり、push 対象の tip の Pre-Push Self Review を記録したステアリングも一つに決まらないため、この push を検査する対象を一つに決められません。どれを終えるかユーザーに確認したうえで、使わないステアリング（プルリクエストが開いているものは除く）は、削除も移動もせず、references/self-review-lanes.md の「使わないステアリングの終え方」に従って終えてください（reason code: steering-multiple）${_PP_RECOVERY_SUFFIX}"
    exit 0
  fi
  STEERING_STATE="${_PP_TIP_MATCHES[0]}"
  _PP_TIP_RESOLVED="true"
  # 以降の block 文すべて（sha-mismatch・dry・Independent Review など）に、standard として
  # 検査した理由と復旧を添える（state.md の Task Size と食い違って見えるため）。steering を
  # 終える案内は、steering-multiple と同じ前提（ユーザーへの確認・手順の参照先）を持つ
  _PP_TIP_NOTE="。複数のステアリングから push 対象の tip の証跡で選んだため、Task Size は standard として検査しています（どれを終えるかユーザーに確認したうえで、使わないステアリング（プルリクエストが開いているものは除く）を、削除も移動もせず references/self-review-lanes.md の「使わないステアリングの終え方」に従って終え、作業中または完了済みのステアリングが一つになると、その Task Size で検査されます）"
  _PP_RECOVERY_SUFFIX="${_PP_RECOVERY_SUFFIX}${_PP_TIP_NOTE}"
else
  STEERING_STATE="$GDD_PP_STEERING_DIR/state.md"
fi

# step 9: Task Size で検査の範囲を決める（tip で解いたときは standard。step 8b）。
TASK_SIZE="standard"
if [[ "$_PP_TIP_RESOLVED" == "false" ]]; then
  TASK_SIZE="$(gdd_state_task_size "$STEERING_STATE")"
fi

if [[ "$TASK_SIZE" == "trivial" ]]; then
  exit 0
fi

REQUIRE_DRY="false"
if gdd_task_size_requires_dry "$TASK_SIZE"; then
  REQUIRE_DRY="true"
fi

# step 10〜12: 証跡 parse（AC-18）+ sha 一致（AC-3）。dry / consecutive_clean の
# 自己矛盾（design.md 104 行）は gdd_parse_self_review_field 内で既に invalid 判定
# されるため、hook 側では他の invalid 原因と同じ missing-evidence 分岐に合流する。
gdd_parse_self_review_field "$STEERING_STATE" "Pre-Push Self Review" "$TASK_SIZE"
if [[ "$GDD_SR_VALID" != "true" ]]; then
  # A-4 / A-7（T-2 Carry Forward）: `bash -c` / `eval` 越しの opt-out は「push と
  # しては検出されるが opt-out は受理されない」= ここへ落ちる。operator がその
  # 非対称を理解できるよう固定文言を 1 文足す（design.md 128 行 / 許可トークン
  # 集合の項目 1「固定メッセージカタログの文言」に収まる）。
  block missing-evidence "⛔ pre-push gate: Pre-Push Self Review が見つからないか不正です（reason code: missing-evidence）${_PP_RECOVERY_SUFFIX}。このステアリングを使わないなら、ユーザーに確認したうえで references/self-review-lanes.md の「使わないステアリングの終え方」に従って終えてください。bash -c / eval 経由の opt-out は受理されません"
  exit 0
fi

# step 11: 証跡 sha と tip の一致（AC-3）。書式検証（lib/self-review-evidence.sh）は
# 短縮 sha（7〜40 桁 hex）を valid とするため、hook 側でも full sha へ正規化してから
# 比較する。両者を突き合わせないと、書式上 valid な 12 桁証跡が恒久 sha-mismatch に
# なり AC-3 の「証跡 sha を更新すれば通る」が成立しない（契約の二重化は lib 側＝
# 7〜40 桁を正本として解消する）。解決不能・曖昧な prefix は空文字になり不足として通知する
# （fail-closed）向きは維持する。
if ! gdd_evidence_sha_matches "$PROJECT_ROOT" "$GDD_SR_SHA" "$TIP_SHA"; then
  block sha-mismatch "⛔ pre-push gate: Pre-Push Self Review の sha が push 対象 ref の tip と一致しません（reason code: sha-mismatch）${_PP_RECOVERY_SUFFIX}"
  exit 0
fi

# step 13: dry を要求する Task Size で dry: no → 不足として通知（dry 定義の正本は
# references/self-review-lanes.md § followup 周回時のレーン要求。2026-09-06 改訂で
# 「2 連続」要件は撤廃し、standard の自己周回は**内部整合 1 周**（consecutive_clean >= 1）
# で足りる。dry 値自体は証跡の自己申告をそのまま見る）。consecutive_clean == 0 を
# ここでも明示して落とすのは、lib 側の自己矛盾判定（dry: yes かつ 0）が緩んだときに
# hook 側だけで観測できる分岐を残すため。
if [[ "$REQUIRE_DRY" == "true" ]]; then
  if [[ "$GDD_SR_DRY" == "no" || "$GDD_SR_CONSECUTIVE_CLEAN" == "0" ]]; then
    block dry-not-reached "⛔ pre-push gate: Task Size: ${TASK_SIZE} は dry: yes への到達を要求します（reason code: dry-not-reached）${_PP_RECOVERY_SUFFIX}"
    exit 0
  fi
fi

# step 13b: standard は独立レビュー 1 回（high 0）の証跡を要求する（正本:
# references/independent-review.md、発火表は references/self-review-lanes.md）。
# 3 レーン自己周回は 2026-09-06 の reviewer recall 実測で確定欠陥を 1 件も
# 拾えず approved を出したため、接地・敵対レーンの検出責務を独立レビューへ移した。
# 証跡は merge gate と同一書式なので、パースは lib/merge-gate-evidence.sh の
# gdd_parse_merge_gate_field を流用する（self-review 用パーサは必須 key が違う）。
# 免除は step 9 の REQUIRE_DRY と同じ境界 — quick (standard) / quick (express) /
# trivial は従来どおり通す。
if [[ "$REQUIRE_DRY" == "true" ]]; then
  # shellcheck source=lib/merge-gate-evidence.sh
  source "$SCRIPT_DIR/lib/merge-gate-evidence.sh"
  gdd_parse_merge_gate_field "$STEERING_STATE" "Independent Review"
  # 復旧要素 2 は `Independent Review` 行の必要 key（正本: lib の GDD_IR_RECOVERY_CORE）。
  # self-review 側の key 一覧を出すと operator が書式を復元できない（R3 #7）。
  _PP_IR_RECOVERY_SUFFIX="。${GDD_IR_RECOVERY_CORE}。緊急時は GDD_SKIP_PRE_PUSH_GATE=1 git push ...（git の直前に置く）${_PP_TIP_NOTE}"
  if [[ "$GDD_MG_VALID" != "true" ]]; then
    block independent-review-missing "⛔ pre-push gate: Independent Review が見つからないか不正です（reason code: independent-review-missing）${_PP_IR_RECOVERY_SUFFIX}"
    exit 0
  fi
  # 証跡 sha は push 対象 ref の tip と一致させる（step 11 と同じく full sha へ正規化。
  # 解決不能・曖昧な prefix は空文字になり不足として通知する = fail-closed）。一致しなくても、tip が
  # レビュー済みの sha に default branch を merge しただけの commit で、gate が git から
  # 確かめられたら引き継ぐ（lib の gdd_ir_carry_matches。正本: references/self-review-lanes.md
  # § Independent Review の引き継ぎ）。
  if ! gdd_evidence_sha_matches "$PROJECT_ROOT" "$GDD_MG_SHA" "$TIP_SHA" \
    && ! gdd_ir_carry_matches "$PROJECT_ROOT" "$STEERING_STATE" "$GDD_MG_SHA" "$TIP_SHA"; then
    block independent-review-stale "⛔ pre-push gate: Independent Review の sha が push 対象 ref の tip と一致しません（reason code: independent-review-stale）。既定ブランチを取り込むだけのマージコミットなら、Independent Review Carry 行で引き継げます（正本: references/self-review-lanes.md）${_PP_IR_RECOVERY_SUFFIX}"
    exit 0
  fi
  # 受理集合は merge gate（`high == 0 && blocking == 0`）と一致させる。片側が high しか
  # 見ないと `high: 0 | blocking: 2`（「実害クラスは常時 High」規定と自己矛盾する行）が
  # push gate だけ素通りし、両 gate の受理集合が非対称になる（独立レビュー #6 / 2026-09-06）。
  if ! gdd_independent_review_clean; then
    block independent-review-high "⛔ pre-push gate: Independent Review に high / blocking が残っています（reason code: independent-review-high）${_PP_IR_RECOVERY_SUFFIX}"
    exit 0
  fi
fi

# step 14: それ以外 → 通す
exit 0
