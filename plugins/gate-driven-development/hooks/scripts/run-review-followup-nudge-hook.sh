#!/usr/bin/env bash
set -euo pipefail

# PreToolUse hook (Bash matcher): git push を検知し、push 先 branch に PR が
# 既にあるなら `pr-review-followup` skill の手順に従うよう additionalContext を
# 1 行注入する（block ではなく nudge）。
#
# 既存の run-pre-push-gate-hook.sh（active GDD 限定・証跡なし push を不足として実行後に
# 通知する runtime gate）とは独立に動く。過去の transcript を調べると、followup の push に
# セルフレビューと独立レビューの証跡がほとんど残っておらず、原因は
# 「軽いレーンでは pre-push gate が発火しない」「汎用 skill を作っても自発発火は
# 少ない（散文の規定はさらに少ない）」の 2 つだった。hook 発火 + skill 手順という
# 2 層に分け、本 hook は発火（skill 呼び出しへのポインタ注入）だけを担う。
#
# 発火範囲: Opus advisory 実測（run-pre-push-gate-hook.sh の全 exit 0 分岐を
# 精査 + 直近30日のログ集計）により、「active: true なら既存の pre-push gate が必ず
# reason 文言を出す」という前提は成立しない（session-mismatch・optout・
# unresolved-steering の分岐が active 判定後に無言 exit 0 している。ログに残らない
# trivial 通過を含めると、無言通過はさらに多い）。したがって本 hook は
# active/非 active を問わず常に発火する。ただし kill switch と
# GDD_SKIP_PRE_PUSH_GATE の opt-out（process-env / command-prefix）は既存 gate と
# 同じ受理面で尊重し、運用者の明示的な抑制手段を残す。
#
# PR 有無の判定は `gh pr view <branch> --json state --jq '.state'` に依存する
# （ローカル情報だけでは「PR があるか」を正確に示す材料がない）。OPEN だけを
# "yes" とする（`--json number,url` の有無だけだと MERGED/CLOSED でも exit 0
# で "number" を返し誤注入する。PR #88 人間レビュー指摘 Medium）。`--jq` で
# state だけを抜き出す（生 JSON を grep する案は `CLICOLOR_FORCE=1` 等の
# 環境で gh が色付き整形出力に切り替わり文字列一致が壊れる。独立レビュー
# round 4 で検出）。このリポジトリで直接測ると、PR 有無のどちらのケースも
# hooks.json の timeout より十分短く返った。
# ネットワーク障害・認証切れ・timeout は「PR なし」と誤判定せず「判定不能」
# として区別しログに残す（fail-safe = 注入しないだけで、block はしない）。
# 同一 root+branch の判定は短い TTL でキャッシュし、falling-back な繰り返し
# push での毎回のネットワーク呼び出しを避ける。
#
# 外部通信（認証付き `gh` 呼び出し）を伴う都合上、push 検出は
# `push_command_parse.is_git_push_at_command_start` による command-start 限定
# の狭い判定を使う（pre-push gate 向けの広い `is_git_push` は `echo git push` 等
# の過検出を意図的に許容しており、そのまま使うと実行されないコマンド文面でも
# ネットワーク I/O が走る。PR #88 人間レビュー指摘 High-2）。`-n/--dry-run`
# `-d/--delete` `-h/--help` を伴う push も同様に対象外にする。
#
# push 対象 branch は push_command_parse.classify_refspec の explicit_ref（無け
# れば現在の checked-out branch）で解決する。既知の限界（未対応）:
# `git push origin <local>:<remote>` の colon 付き refspec は local 側の名前を
# 使う（remote 側の branch 名には解決しない）。この形は稀なため、外れた場合は
# 「判定不能」ではなく単に branch 名を誤って解決し、誤った PR 有無で判定する。

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/kill-switch.sh"
gdd_kill_switch_active && exit 0

# `${HOME}` を直接展開すると set -u 下で HOME 未設定時にシェルごと即死する
# （独立レビューで検出。安全形は self-review-evidence.sh:487-491 / kill-switch.sh:5
# に揃える）。STATE_DIR が決まらない場合はログ・キャッシュとも no-op にし、
# gh は毎回呼ぶ（キャッシュ無しへ縮退するだけで injection 判定自体は継続する）。
STATE_DIR="${GDD_HOOK_STATE_DIR:-}"
if [[ -z "$STATE_DIR" && -n "${HOME:-}" ]]; then
  STATE_DIR="${HOME}/.claude/.gdd-hook-state"
fi
LOG_FILE=""
CACHE_DIR=""
if [[ -n "$STATE_DIR" ]]; then
  LOG_FILE="$STATE_DIR/review-followup-nudge.log"
  CACHE_DIR="$STATE_DIR/review-followup-pr-cache"
fi
GH_BIN="${GDD_REVIEW_FOLLOWUP_GH_BIN:-gh}"

# 数値 env は書式が壊れていても算術エラーで hook 全体を落とさないよう正規化する
# （plan-reread-hook.sh の dedup_window と同じ安全策）。
_normalize_uint() {
  local _v="${1:-}" _default="$2"
  if [[ "$_v" =~ ^[0-9]{1,7}$ ]]; then
    echo "$((10#$_v))"
  else
    echo "$_default"
  fi
}
GH_TIMEOUT_SECS="$(_normalize_uint "${GDD_REVIEW_FOLLOWUP_GH_TIMEOUT:-}" 5)"
CACHE_TTL="$(_normalize_uint "${GDD_REVIEW_FOLLOWUP_PR_CACHE_TTL:-}" 300)"
UNKNOWN_TTL="$(_normalize_uint "${GDD_REVIEW_FOLLOWUP_PR_UNKNOWN_TTL:-}" 30)"
# hooks.json の timeout は 8 秒固定。GH_TIMEOUT_SECS がそれ以上だと python3/git の
# 前処理より前に hook 自体が外部から kill され、undeterminable すら記録されずに
# 沈黙する（独立レビューで検出）。python3 起動・git 呼び出しの余裕を残し 6 秒で
# 頭打ちにする（`(( cond )) && stmt` は cond=false のとき set -e を発火させるため
# 明示 if 形にする）。
if (( GH_TIMEOUT_SECS > 6 )); then
  GH_TIMEOUT_SECS=6
fi

# additionalContext は PreToolUse を block しない場合、push 実行後（tool result
# と同じタイミング）でしかモデルに届かない（独立レビューで指摘）。過去形の
# 「push しました」は、command-start 限定でも塞ぎきれない残存ケース（design.md
# § Honest Limitations 由来の検出面の限界）では実際には push が起きていない
# ことがあり、断定になる（PR #88 人間レビュー指摘 Medium）。断定を避け「検知
# しました（成功した場合は…）」の条件法にする。
#
# hook は active/非active を問わず常に発火する（案B）が、文言が汎用
# `pr-review-followup` だけを指すと、GDD active session 下では証跡形式が
# state.md 側と食い違い、直後の pre-push gate で不足として通知されうる（PR #88 人間
# レビュー指摘 Medium）。両方の skill 名と使い分けを 1 行で示す（active 判定
# 自体を hook 側で新たに行うと session-mismatch 等で誤判定しうるため、判定は
# 呼び出し側=モデルに委ねる）。
NUDGE_MESSAGE='[review-followup] PR がある branch への push を検知しました。成功した場合はこの push 分について、GDD active session 下では gdd-pr-review-followup skill、それ以外では pr-review-followup skill の手順(内部整合レーン1周+横展開検索(規律A)+独立レビュー+証跡記録)に従ってください。'

_hash8() {
  # PATH 上の shasum/sha1sum が「無い」のではなく「非 0 終了する」場合、
  # `set -euo pipefail` 下ではパイプライン全体の失敗がこの関数の呼び出し元
  # （ROOT_HASH="$(_hash8 ...)" 等）へ伝播し、hook 全体を落としうる。PreToolUse
  # で終了コード 2 は block 扱いになるため、advisory のはずの hook が空の reason
  # で push を deny しうる（PR #88 人間レビュー指摘 High-1。run-merge-gate-hook.sh
  # が既に同型を警告済み）。各コマンドの失敗を `|| true` で個別に無害化し、
  # 空文字なら次の手段へフォールバックする（"無い" と "壊れている" を同じ
  # フォールバック経路で扱う）。
  local _out=""
  if command -v shasum >/dev/null 2>&1; then
    _out="$(printf '%s' "$1" | shasum -a 1 2>/dev/null | cut -c1-8 2>/dev/null || true)"
  fi
  if [[ -z "$_out" ]] && command -v sha1sum >/dev/null 2>&1; then
    _out="$(printf '%s' "$1" | sha1sum 2>/dev/null | cut -c1-8 2>/dev/null || true)"
  fi
  if [[ -z "$_out" ]]; then
    _out="unknown"
  fi
  printf '%s' "$_out"
}

# 可観測化ログ。絶対パスは残さず repo をハッシュにする
# （self-review-evidence.sh の gdd_sr_log_event と同じ秘匿方針。log file 自体は
# 独立にする — 既存 pre-push-optout.log に無関係な event を混ぜない）。
_log_event() {
  local _event="$1" _reason="${2:-}" _repo_root="${3:-}"
  # `[[ cond ]] && return` の bare 形は set -e 下で cond=false のとき非 0 終了して
  # 呼び出し元へ伝播する（self-review-evidence.sh 冒頭コメントと同型の落とし穴）。
  # 明示 if 形にする。
  if [[ -z "$LOG_FILE" ]]; then
    return 0
  fi
  local _repo_id _ts
  _repo_id="$(_hash8 "$_repo_root")"
  # `_hash8` と同じ理由（PR #88 人間レビュー指摘 High-1）で `|| true` を付ける。
  # `date` が非 0 終了すると `set -euo pipefail` 下でこの代入自体が非 0 で
  # 終了し、advisory な log 記録の失敗が hook 全体の終了コードへ伝播しうる
  # （PR #88 人間レビュー round 5 指摘 Medium。実 date ではまず起きないが、
  # 常時 High と同型の穴のため同じ push で吸収する）。失敗時は空文字のまま
  # ログへ出力するだけで、判定自体には使わない。
  _ts="$(date -u +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || true)"
  mkdir -p "$STATE_DIR" 2>/dev/null || true
  printf '%s | event: %s | reason: %s | repo: %s\n' "$_ts" "$_event" "$_reason" "$_repo_id" \
    >>"$LOG_FILE" 2>/dev/null || true
  chmod 600 "$LOG_FILE" 2>/dev/null || true
}

# step 1: payload に push が含まれなければ最優先で即通過（pre-push-gate-hook.sh
# と同じ短絡）。
PAYLOAD="$(cat 2>/dev/null || true)"
case "$PAYLOAD" in
  *push*) ;;
  *) exit 0 ;;
esac

PROCESS_CWD="$(pwd)"

# step 2: push 検出・opt-out・候補 root 解決を python3 起動 1 回にまとめる
# （push_command_parse.py を再利用。run-pre-push-gate-hook.sh と同じ設計方針）。
IS_PUSH="false"
OPTOUT_ACCEPTED="false"
UNRESOLVABLE="false"
REFSPEC_AMBIGUOUS="false"
EXPLICIT_REF=""
HOOK_CWD=""
CANDIDATE_ROOTS=()
while IFS=$'\t' read -r _k _v; do
  case "$_k" in
    is_push) IS_PUSH="$_v" ;;
    optout) OPTOUT_ACCEPTED="$_v" ;;
    unresolvable) UNRESOLVABLE="$_v" ;;
    refspec_ambiguous) REFSPEC_AMBIGUOUS="$_v" ;;
    explicit_ref) EXPLICIT_REF="$_v" ;;
    root) CANDIDATE_ROOTS+=("$_v") ;;
    hook_cwd) HOOK_CWD="$_v" ;;
  esac
done < <(printf '%s' "$PAYLOAD" | python3 -c '
import json, sys
sys.path.insert(0, sys.argv[2])
import push_command_parse as pcp
import hook_cwd

def emit(key, value):
    # 書けない lone surrogate（`\ud800`）で例外になると後の key（root）が出ないので、pre-push gate と同じ形で書く。
    line = "%s\t%s\n" % (key, value)
    try:
        data = line.encode("utf-8", "surrogateescape")
    except UnicodeEncodeError:
        data = line.encode("utf-8", "backslashreplace")
    sys.stdout.buffer.write(data)

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
    # Claude Code は cwd を payload の最上位に持つ。使えるならそれを基準にする（lib/hook_cwd.py）。
    top_cwd = hook_cwd.toplevel_cwd(payload)
    if top_cwd:
        process_cwd = top_cwd
        emit("hook_cwd", top_cwd)
    tokens, raw_count = pcp.tokenize_with_boundary(command)
    # `is_git_push`（pre-push gate 向け、token 列全体を fail-closed で走査）を
    # そのまま使うと、実行されないコマンド文面（`echo git push` / `# git push`
    # / heredoc 内の非行頭出現）でも認証付き `gh pr view` が呼ばれる
    # （PreToolUse は許可ダイアログより前なので、拒否した push でも問い合わせ
    # が走る。PR #88 人間レビュー指摘 High-2）。この hook は外部通信を伴うため
    # command-start 限定の狭い判定を使う。
    #
    # command-start な一致が「除外対象の flag（--dry-run 等）を伴う push」
    # だった場合、その一致だけで諦めずに続きを探す（`git push --dry-run
    # origin main && git push origin main` のように、除外対象の後に本物の
    # push が続く形を取りこぼさないため。独立レビュー round 4 で検出）。
    search_from = 0
    is_push = False
    git_index = -1
    while True:
        found, idx = pcp.is_git_push_at_command_start(tokens, raw_count, start=search_from)
        if not found:
            break
        if pcp.push_has_side_effect_excluded_flag(tokens, idx):
            search_from = idx + 1
            continue
        is_push, git_index = True, idx
        break
    if not is_push:
        raise SystemExit
    # 検出（is_git_push_at_command_start）は `{` / `)` / `;;` まで command-start
    # に含めて広げているのに、opt-out 判定と cd 解決を既定の狭い集合のまま
    # 呼ぶと、brace/case 腕の中では「push とは判定するが opt-out は無視する」
    # 「push とは判定するが誤った root で gh を呼ぶ」非対称が生まれる（PR #88
    # 人間レビュー round 5 指摘 Medium）。この hook の呼び出しだけ widened な
    # 集合を明示して渡す（既定値＝run-pre-push-gate-hook.sh の受理面は不変）。
    optout = pcp.find_optout(
        tokens,
        original_token_count=raw_count,
        separators=pcp.PUSH_DETECTION_COMMAND_START_SEPARATORS,
    )
    roots = pcp.resolve_candidate_roots(
        tokens,
        git_index,
        payload_cwd,
        process_cwd,
        cd_separators=pcp.PUSH_DETECTION_CD_SEPARATORS,
    )
    refspec = pcp.classify_refspec(tokens, git_index)
    emit("is_push", "true")
    emit("optout", "true" if optout.get("accepted") else "false")
    emit("unresolvable", "true" if roots.get("unresolvable") else "false")
    emit("refspec_ambiguous", "true" if refspec.get("ambiguous") else "false")
    if refspec.get("explicit_ref"):
        emit("explicit_ref", refspec["explicit_ref"])
    for r in roots.get("roots", []):
        emit("root", r)
except Exception:
    pass
' "$PROCESS_CWD" "$SCRIPT_DIR/lib" 2>/dev/null || true)

# 最上位の cwd が使えたら（lib/hook_cwd.py）、プロセスの cwd をそこへ移す。後の `-d`・
# `git -C`・lib の暗黙の cwd も、セッションの cwd から解決するようにする。移れないときは、
# 今までどおりプロセスの cwd に残る。
if [[ -n "$HOOK_CWD" ]] && cd "$HOOK_CWD" 2>/dev/null; then
  PROCESS_CWD="$(pwd)"
fi

[[ "$IS_PUSH" == "true" ]] || exit 0
# --git-dir/--work-tree を伴う push は本 hook の対象外（block ではなく nudge な
# ので、pre-push-gate-hook.sh と違い unresolvable でも黙って抜けるだけでよい）。
[[ "$UNRESOLVABLE" == "true" ]] && exit 0
# `--all` / `--mirror` / 複数 refspec 等の ambiguous push は判定不能として抜ける
# （独立レビューで検出: HEAD の現在ブランチ名だけで判定すると `git push origin
# other-branch` のような明示 refspec 付き push を取り違える。既存
# run-pre-push-gate-hook.sh と同じ classify_refspec を再利用して push 対象を解決する）。
[[ "$REFSPEC_AMBIGUOUS" == "true" ]] && exit 0
# `-n/--dry-run` `-d/--delete` `-h/--help` を伴う push は python 側
# （is_git_push_at_command_start の反復走査）で既に除外済みで、この時点の
# IS_PUSH="true" は「除外対象ではない command-start push が見つかった」こと
# を意味する（PR #88 人間レビュー指摘 Medium。独立レビュー round 4 で、除外
# 対象の後に本物の push が続く形を取りこぼす指摘を受け、除外判定を python
# 側の反復に統合した）。

# step 3: opt-out（既存 pre-push gate と同じ受理面 — process-env / command-prefix）
if [[ "${GDD_SKIP_PRE_PUSH_GATE:-}" == "1" || "$OPTOUT_ACCEPTED" == "true" ]]; then
  _log_event "skipped" "optout" "$PROCESS_CWD"
  exit 0
fi

# step 4: 候補 root のうち実在する最初の 1 つを使う
ROOT=""
for _root in "${CANDIDATE_ROOTS[@]+"${CANDIDATE_ROOTS[@]}"}"; do
  [[ -n "$_root" && -d "$_root" ]] || continue
  ROOT="$_root"
  break
done
[[ -n "$ROOT" ]] || exit 0

# push 対象 branch: 明示 refspec があればそれを使い、無ければ現在の checked-out
# branch を使う（`git push origin` / `git push` の暗黙形）。`git push origin HEAD`
# / `git push -u origin HEAD` は explicit_ref="HEAD" になる常用形なので、branch
# 名ではなく現在の checked-out branch へ解決し直す（独立レビュー 2 巡目で検出:
# 未解決のまま使うと全 branch が同一キャッシュキー "HEAD" を共有し、branch を
# 跨いで誤った PR 有無が再利用されていた）。detached HEAD で branch 名に解決
# できない場合（明示 refspec 無し、または明示 refspec が "HEAD" で detached）は
# 対象外。`<local>:<remote>` 形は local 側のみ扱う（remote 側の解決は未対応。既知
# の限界として changelog に明記する）。
if [[ -n "$EXPLICIT_REF" && "$EXPLICIT_REF" != "HEAD" ]]; then
  BRANCH="$EXPLICIT_REF"
else
  BRANCH="$(git -C "$ROOT" rev-parse --abbrev-ref HEAD 2>/dev/null || true)"
  [[ -n "$BRANCH" && "$BRANCH" != "HEAD" ]] || exit 0
fi
# `gh pr view <arg>` は <arg> が全桁数字だと branch 名ではなく PR 番号として解決
# する（独立レビュー 3 巡目で検出。`git push origin 1234` のような数字だけの
# branch 名で、無関係な PR 番号 1234 の有無に基づいて誤注入されうる）。判定不能
# として抜ける。
if [[ "$BRANCH" =~ ^[0-9]+$ ]]; then
  exit 0
fi

# step 5: PR 有無をキャッシュ付きで判定する
ROOT_HASH="$(_hash8 "$ROOT")"
# branch 名もログと同じ秘匿方針でハッシュ化する（独立レビューで検出: log は
# repo をハッシュ化する一方、cache ファイル名だけ branch を平文で残していた
# 非対称）。
BRANCH_HASH="$(_hash8 "$BRANCH")"
# shasum/sha1sum がどちらも無い環境では _hash8 が固定文字列 "unknown" を返し、
# 全 repo・全 branch でキャッシュキーが衝突する（独立レビューで検出）。その場合は
# キャッシュを無効化し、gh を毎回呼ぶ縮退にする。CACHE_FILE も併せて空にする
# （独立レビュー 3 巡目で検出: CACHE_DIR="" のままだと CACHE_FILE がファイル
# システムルート直下のパスになり、下流のガードが 1 つでも外れると危険なため）。
CACHE_FILE=""
if [[ "$ROOT_HASH" == "unknown" || "$BRANCH_HASH" == "unknown" ]]; then
  CACHE_DIR=""
fi
if [[ -n "$CACHE_DIR" ]]; then
  CACHE_FILE="$CACHE_DIR/${ROOT_HASH}__${BRANCH_HASH}"
fi

STATUS=""
_FRESH_NO_PR="false"
NOW_EPOCH="$(date +%s 2>/dev/null || echo 0)"
# `date` 失敗時の `NOW_EPOCH="0"` をそのまま TTL 比較に使うと、
# `0 - _cached_epoch`（大きな負数）は常に `<= _ttl` を満たし、既存キャッシュが
# 期限切れにならなくなる（PR #88 人間レビュー round 3 指摘 Low）。
# `NOW_EPOCH="0"` はキャッシュ読みを無効化し、毎回 fresh に `gh` を呼ぶ
# 縮退にする。cache 書き込み自体は行うが、そのエントリの epoch は `0` に
# なるため、`date` が正常に戻った後の比較（`now - 0` は常に巨大な値）で
# 常に期限切れ扱いになり、書き込んだ値がそのまま再利用されることはない
# （独立レビューで指摘。この修正時点のコメント・changelog がここを
# 「date が正常に戻ればそのキャッシュが有効に使われる」と誤って書いていた
# ため訂正した）。
#
# 同じ根本原因（TTL 比較が負数側に倒れると常に「期限内」になる）は、
# cache に書き込まれた epoch が**未来**の場合にも起きる（実 `date` が
# システムクロックのずれ — RTC 復旧直後の VM/container 等 — で一時的に
# 未来の時刻を返した場合）。`NOW_EPOCH` が cache の epoch より小さければ、
# その cache は無条件に無効（未来日付＝壊れている）として扱う（独立レビューで
# 指摘）。
if [[ -n "$CACHE_DIR" && -f "$CACHE_FILE" && "$NOW_EPOCH" != "0" ]]; then
  _cached_epoch="$(sed -n '1p' "$CACHE_FILE" 2>/dev/null || true)"
  _cached_status="$(sed -n '2p' "$CACHE_FILE" 2>/dev/null || true)"
  if [[ "$_cached_epoch" =~ ^[0-9]+$ && "$NOW_EPOCH" =~ ^[0-9]+$ ]] \
    && (( 10#$NOW_EPOCH >= 10#$_cached_epoch )); then
    _ttl="$CACHE_TTL"
    [[ "$_cached_status" == "unknown" ]] && _ttl="$UNKNOWN_TTL"
    if (( 10#$NOW_EPOCH - 10#$_cached_epoch <= 10#$_ttl )); then
      STATUS="$_cached_status"
    fi
  fi
fi

if [[ -z "$STATUS" ]]; then
  # `command -v` はこの hook 自身の cwd（PROCESS_CWD）で解決する。実行は
  # `( cd "$ROOT" && ... )` で untrusted な push 対象 repo に cwd を移してから
  # 行うため、`$GH_BIN` が相対名（`gh` 等）かつ PATH に `.`（カレント
  # ディレクトリ）を含む環境だと、存在確認した実体と実際に実行される実体が
  # 別物になりうる（cd 後の再解決は cd 後の cwd を基準にするため。PR #88
  # 人間レビュー round 5 指摘 Medium）。ここで一度だけ絶対パスへ解決し、
  # 以後は解決済みの絶対パスだけを実行する（cd 後の再解決を発生させない）。
  # `command -v` は PATH 要素を単に前置して返すだけなので、PATH に `.` /
  # 空要素 / 相対ディレクトリを含む環境では絶対パスではなく相対パス
  # （`./gh` / `bin/gh` 等）を返す（実測確認済み）。相対パスのまま
  # `( cd "$ROOT" && "$GH_RESOLVED" ... )` で実行すると、"一度だけ絶対パスへ
  # 解決した" という前段の意図に反して、実行時点の cwd（= 実行後の `$ROOT`）
  # を基準に再解決され、push 対象 repo（untrusted）側に置かれた同名ファイルが
  # 動きうる（PreToolUse はユーザーが push を承認する前に実行されるため、
  # ユーザーの承認なしに untrusted repo 由来のバイナリが実行される。PR #88
  # 人間レビュー round 3 指摘 High。実 gh 2.95.0 で確認済み）。解決結果が
  # 絶対パスでなければ「見つからない」と同じ fail-safe 側（`gh` を呼ばず
  # 判定不能）に倒す。
  GH_RESOLVED="$(command -v "$GH_BIN" 2>/dev/null || true)"
  if [[ -z "$GH_RESOLVED" ]]; then
    STATUS="unknown"
    _log_event "undeterminable" "gh-not-found" "$ROOT"
  elif [[ "$GH_RESOLVED" != /* ]]; then
    STATUS="unknown"
    _log_event "undeterminable" "gh-not-absolute" "$ROOT"
  else
    # mktemp 自体の失敗（TMPDIR 書き込み不可等、run-steering-write-hook.sh:39-45
    # と同種の状況）を予測可能な固定パスへフォールバックすると symlink 攻撃面に
    # なる（独立レビューで検出）。mktemp が失敗したら判定不能へ fail-safe し、
    # 予測可能パスは一切使わない。
    GH_OUT="$(mktemp "${TMPDIR:-/tmp}/gdd-rfn-out.XXXXXX" 2>/dev/null || true)"
    GH_ERR="$(mktemp "${TMPDIR:-/tmp}/gdd-rfn-err.XXXXXX" 2>/dev/null || true)"
    GH_RC="$(mktemp "${TMPDIR:-/tmp}/gdd-rfn-rc.XXXXXX" 2>/dev/null || true)"
    if [[ -z "$GH_OUT" || -z "$GH_ERR" || -z "$GH_RC" ]]; then
      rm -f "$GH_OUT" "$GH_ERR" "$GH_RC" 2>/dev/null || true
      STATUS="unknown"
      _log_event "undeterminable" "mktemp-failed" "$ROOT"
    else
      # `wait` の戻り値そのものを bare 文で受けると、gh が非 0 終了したときに
      # `set -e` が即座に発火して以降の分岐（no-pr / undeterminable の区別）に
      # 到達できない。子プロセス自身に終了コードをファイルへ書かせ、`wait` 自体は
      # `|| true` で無害化する（`wait` の戻り値は使わない）。
      # `$BRANCH` を明示で渡す（独立レビュー 2 巡目で検出: 省略すると gh は
      # current checked-out branch を見るため、明示 refspec で別 branch へ push
      # する形と食い違っていた）。`--json state --jq '.state'` で state だけを
      # 抜き出す（PR #88 人間レビュー指摘 Medium: MERGED / CLOSED でも exit 0
      # で "number" を返すため、state を見ないと決着済み PR にまで誤注入する。
      # `--json` の生 JSON を `grep` で文字列一致させる案は、`CLICOLOR_FORCE=1`
      # 等が設定された環境では gh がリダイレクト先でも色付き・整形出力に
      # 切り替わり `"state":"OPEN"` の連続一致が壊れる（独立レビュー round 4
      # で実測確認。gh 自身の `--jq` はこの整形より前の生 API レスポンスに
      # 対して評価されるため影響を受けない）。
      # branch 名は先頭 `-` を弾いていない（全桁数字は弾く。289 行付近）。
      # `"$BRANCH"` を素のままフラグ位置に置くと、`--repo=attacker/repo` の
      # ような branch 名（hostile clone の HEAD がこの ref 名を指す形）が gh
      # 自身のグローバル flag として解釈され、認証付き問い合わせの宛先を
      # push 対象 repo の作者が選べてしまう（PR #88 人間レビュー round 5
      # 指摘 High）。全 flag の後に `--` を置き、`$BRANCH` を明示的に
      # positional 引数だけとして渡す（実 gh で実測確認: `--` より前の
      # `--json`/`--jq` は通常どおり flag として解釈され、`--` の後の
      # `$BRANCH` は先頭が `-` でも常に literal な branch 名として扱われる。
      # `--` の位置は `--json`/`--jq` より後でなければならない — `--` 以降は
      # 全て positional 扱いになり、`--json` 自体が branch 名の一部として
      # 誤解釈されるため）。
      ( cd "$ROOT" && "$GH_RESOLVED" pr view --json state --jq '.state' -- "$BRANCH" >"$GH_OUT" 2>"$GH_ERR"; echo $? >"$GH_RC" ) &
      _gh_pid=$!
      _elapsed=0
      while kill -0 "$_gh_pid" 2>/dev/null; do
        if (( _elapsed >= GH_TIMEOUT_SECS )); then
          break
        fi
        sleep 1
        _elapsed=$((_elapsed + 1))
      done
      if kill -0 "$_gh_pid" 2>/dev/null; then
        # `( cd ... && gh ...; echo $? > rc ) &` のため `$_gh_pid` は subshell
        # の pid で、`gh` 本体はその子。subshell だけを殺すと `gh` は init に
        # 引き取られて残り続ける（PR #88 人間レビュー指摘 Medium）。直接の子
        # （`gh` 本体）を先に辿って殺してから subshell を殺す。
        for _gh_child in $(pgrep -P "$_gh_pid" 2>/dev/null || true); do
          kill -9 "$_gh_child" 2>/dev/null || true
        done
        kill -9 "$_gh_pid" 2>/dev/null || true
        wait "$_gh_pid" 2>/dev/null || true
        STATUS="unknown"
        _log_event "undeterminable" "gh-timeout" "$ROOT"
      else
        wait "$_gh_pid" 2>/dev/null || true
        _gh_exit="$(cat "$GH_RC" 2>/dev/null || echo 1)"
        if [[ "$_gh_exit" == "0" ]]; then
          _pr_state="$(tr -d '[:space:]' <"$GH_OUT" 2>/dev/null || true)"
          # exit 0 は「gh が失敗しなかった」ことしか意味しない。state が
          # GitHub の PR state enum（OPEN/MERGED/CLOSED）のいずれでもない
          # 場合（空文字列・想定外の値。`--jq` の出力が壊れた、API 応答が
          # 想定外だった等）まで「OPEN ではない」＝no-pr と断定すると、
          # 判定不能な出力を「PR なし」として 300 秒キャッシュしてしまう
          # （fail-safe の契約「判定不能は undeterminable」が非 0 終了時
          # にしか効いていなかった。PR #88 人間レビュー round 6 指摘
          # Medium、実害の方向: 誤って skip=no-pr に倒れ nudge を取りこぼす）。
          # 既知の3値だけを確信を持った分岐にし、それ以外は undeterminable
          # に倒す。
          case "$_pr_state" in
            OPEN)
              STATUS="yes"
              ;;
            MERGED | CLOSED)
              STATUS="no"
              _FRESH_NO_PR="true"
              ;;
            *)
              STATUS="unknown"
              _log_event "undeterminable" "gh-unexpected-state" "$ROOT"
              ;;
          esac
        elif grep -qiE "no (open )?pull requests? found" "$GH_ERR" 2>/dev/null; then
          STATUS="no"
          _FRESH_NO_PR="true"
        else
          STATUS="unknown"
          _log_event "undeterminable" "gh-error" "$ROOT"
        fi
      fi
      rm -f "$GH_OUT" "$GH_ERR" "$GH_RC" 2>/dev/null || true
    fi
  fi
  if [[ -n "$CACHE_DIR" ]]; then
    mkdir -p "$CACHE_DIR" 2>/dev/null || true
    # directory 0755 / file 0644 が既定だと、同じ state dir 内の log（600）と
    # 非対称になる（PR #88 人間レビュー指摘 Medium）。近傍の state dir 契約
    # （merge-gate / self-review-evidence / stop-failure-record）に揃える。
    chmod 700 "$CACHE_DIR" 2>/dev/null || true
    printf '%s\n%s\n' "$NOW_EPOCH" "$STATUS" >"$CACHE_FILE" 2>/dev/null || true
    chmod 600 "$CACHE_FILE" 2>/dev/null || true
  fi
fi

# step 6: PR がある場合だけ注入する。`injected` は注入のたびに記録する
# （キャッシュ命中でも毎回記録する。再計測手順 1 が注入回数を数えるため）。
# `skipped`(no-pr) は独立レビューで検出した観測性ギャップの是正で、fresh に gh を
# 呼んで STATUS="no" と判定できた回だけ記録する（キャッシュ命中時の "no" は
# 記録しない。判定不能 → 判定成立の遷移が分かれば十分で、以後のキャッシュ命中は
# ログ量を増やすだけのため）。
if [[ "$STATUS" == "yes" ]]; then
  _log_event "injected" "-" "$ROOT"
  MSG="${NUDGE_MESSAGE//\\/\\\\}"
  MSG="${MSG//\"/\\\"}"
  printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","additionalContext":"%s"}}\n' "$MSG"
elif [[ "$_FRESH_NO_PR" == "true" ]]; then
  _log_event "skipped" "no-pr" "$ROOT"
fi

exit 0
