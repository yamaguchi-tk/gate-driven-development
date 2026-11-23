#!/usr/bin/env bash
set -euo pipefail

# PreToolUse hook: active GDD 中の `gh pr merge` を実行時に検査する。止めずに通し、不足を
# 実行後の通知と would-block の記録に残す（下の `block()`。判定順は design.md § 主要フロー）。

# hook が Claude Code プロセスから継承する `CDPATH` が非空（`.` だけでも）だと、bash の
# `cd` は相対パスを解決したあと絶対パスを stdout に印字するため、後段の
# `$(cd "$PAYLOAD_CWD" && pwd)` が 2 行になり payload cwd 候補が `-d` 判定で脱落する
# （impl-gate Round 4 IG-13）。以降の `cd` はすべて hook 内部の解決用なので、ここで
# 外して影響を断つ（`tool_input` からは制御できない env だが、結果は無検査 exit 0）。
# 直下の `SCRIPT_DIR` 解決も同じ `cd` を使うので、source より前に外す（後ろに置くと
# lib の読み込みに失敗して block 関数を持たないまま終了しうる）。
unset CDPATH
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/kill-switch.sh"

# shellcheck source=lib/gate-notice.sh
source "$SCRIPT_DIR/lib/gate-notice.sh"

# 止めずに通す。不足は実行後の通知（additionalContext。止めない hook の文脈は実行後に届く）と
# systemMessage で返し、would-block:<code> を記録する（lib/gate-notice.sh。pre-push gate・pre-PR gate と同じ）。
# code は本文の `不足条件: <codes>。` か `reason code: <code>）` から切り出す。
block() {
  local _code="unknown"
  if [[ "$1" == *"不足条件: "* ]]; then _code="${1#*不足条件: }"; _code="${_code%%。*}"
  elif [[ "$1" == *"reason code: "* ]]; then _code="${1#*reason code: }"; _code="${_code%%）*}"; fi
  gdd_gate_notice "merge-gate-suppressed.log" "$_code" "実行後の通知: merge gate は止めずに通した。merge が成功した場合は、次の不足をユーザーに報告するだけにし、承認や証跡を後から書き足さないでください。merge が失敗した場合だけ、次の手順で直してから再実行してください。$1"
}

# step 1: payload に merge を含まなければ最優先で即通過（AC-6c）。
#
# ここを「コマンドの値だけ」に絞れれば、cwd / transcript_path に merge を含む環境
# （`.../20260901-pr-w17-merge-gate/` のような worktree）で全 Bash 呼び出しが python3 を
# 起動する面（1 回ごとに python3 の起動の分だけ遅くなる）を閉じられる。だが bash でその
# 絞り込みは成立しない:
#   - JSON の値を切り出すには値の終端（エスケープされていない `"`）を探す必要があり、
#     `${v%%\"*}` / `${v#*\"}` はどちらも値長に対して二乗で効く。payload を 2 倍にすると
#     所要時間は約 4 倍になり、数百 KB の payload で hooks.json の timeout（10 秒）を超える。
#     timeout で kill されると通知を返せない = 素通りなので、python3 の起動より高くつく。
#   - `gh` の共起を足して絞る案は、解析側が shlex の**クォート除去後**の token を見るため
#     不成立。`g\h pr merge 7` / `'g''h' pr merge 7` は解析側では is_merge=true になるのに
#     payload に literal `gh` が現れず、gate ごと素通りする（実測）。
# よって粗いフィルタは `merge` 1 語に留め、精密判定は step 2 の python 側
# （`tool_input.command` だけを見る）に委ねる。
PAYLOAD="$(cat 2>/dev/null || true)"
case "$PAYLOAD" in
  *merge*) ;;
  *) exit 0 ;;
esac

# 末尾の改行を `$()` で落とさないよう番兵 `x` で取る。
PROCESS_CWD="$(pwd && printf x)"
PROCESS_CWD="${PROCESS_CWD%$'\n'x}"

# step 2: python3 起動 1 回で gh pr merge かを判定する。
IS_MERGE="false"
# コマンド解析そのものが完走したか。python3 不在・不正 JSON・import 失敗では
# `is_merge` が false のまま残るため、「merge ではない」と「判定できなかった」を
# この sentinel で分ける（分けないと解析失敗が無検査の素通りになる）。
PARSED="false"
PR_NUMBER=""
PR_URL_ARG=""
REPO_FLAG=""
# merge ごとの組（-R・番号・URL）。組の区切りは \x1e、欄の区切りは \x1f（lib/gh_command_parse.py の ledger_targets）。
LEDGER_TARGETS=""
UNRESOLVABLE="false"
ENV_REPO_CONFLICT="false"
IS_ADMIN="false"
CD_TARGET=""
CD_INTENT="false"
# shlex がクォート解析に失敗して `text.split()` へ縮退したか。縮退した token 列は
# 演算子と密着した token を割らないので、`;gh` が token `gh` にならず `is_merge` が
# 落ちる（chdir 語彙も同様）。`PARSED` と同じく「merge ではない」と「判定できな
# かった」を分けるための sentinel で、解析未完走と同じ family へ倒す。
DEGRADED="false"
HOOK_CWD=""
PAYLOAD_CWD=""
# key -> shell 変数の対応。`gh_command_parse.HOOK_CONSUMED_SIGNALS` に載る signal は
# すべてこの case に branch を持ち、かつ **この case の外で読まれる**必要がある
# （代入するだけで一度も読まない変数は fail-open を生む）。機械検査は
# tests/test_merge_gate_hook_contracts.py の HookSignalConsumptionContractTests。
while IFS=$'\t' read -r _k _v; do
  case "$_k" in
    parsed) PARSED="$_v" ;;
    is_merge) IS_MERGE="$_v" ;;
    pr_number) PR_NUMBER="$_v" ;;
    pr_url) PR_URL_ARG="$_v" ;;
    repo_flag) REPO_FLAG="$_v" ;;
    ledger_targets) LEDGER_TARGETS="$_v" ;;
    unresolvable) UNRESOLVABLE="$_v" ;;
    env_repo_conflict) ENV_REPO_CONFLICT="$_v" ;;
    admin) IS_ADMIN="$_v" ;;
    cd_target) CD_TARGET="$_v" ;;
    cd_intent) CD_INTENT="$_v" ;;
    degraded) DEGRADED="$_v" ;;
    hook_cwd) HOOK_CWD="$_v" ;;
    # bash 3.2 の `printf -v` は、結果が空だと変数を消す（`set -u` で落ちる）ので、番兵 `x` を付けて受ける。
    payload_cwd) printf -v PAYLOAD_CWD '%bx' "$_v"; PAYLOAD_CWD="${PAYLOAD_CWD%x}" ;;
  esac
done < <(printf '%s' "$PAYLOAD" | python3 -c '
import json, sys

def emit(k, v):
    # `\t`/`\n` は偽の行の注入になる。書けない lone surrogate（`\ud800`）は例外で後の key が出ず通るので pre-push gate と同じ形で書く。
    line = "%s\t%s\n" % (k, str(v if v is not None else "").replace("\t", " ").replace("\n", " ").replace("\r", " "))
    try: data = line.encode("utf-8", "surrogateescape")
    except UnicodeEncodeError: data = line.encode("utf-8", "backslashreplace")
    sys.stdout.buffer.write(data)

def emit_cwd(v):
    # tool_input の cwd は改行で終わる名前（`<root>\n`）も root と分けるため、値をそのまま渡す。`\`・tab・改行・CR を
    # 8 進の `\0NNN`（3 桁で固定）にし、bash が `printf %b` で戻す（ほかの `\` の並びは作らない）。NUL は bash の変数に入らないので落とす。
    try: data = str(v).encode("utf-8", "surrogateescape")
    except UnicodeEncodeError: data = str(v).encode("utf-8", "backslashreplace")
    for b, e in ((b"\\", b"\\0134"), (b"\t", b"\\0011"), (b"\n", b"\\0012"), (b"\r", b"\\0015"), (b"\0", b"")):
        data = data.replace(b, e)
    sys.stdout.buffer.write(b"payload_cwd\t" + data + b"\n")

def ledger_target(repo, number, url):
    # 長い値は bash の展開が 2 乗に効き timeout（= 素通り）になる。512 文字を超える repo は番号だけの照合の印
    # `*` に、URL は番号を残した組に替える。gh が読めない桁数の番号（Atoi の上限を超える）は落とす。
    if url and len(url) > 512:
        repo, number, url = "*", url.rsplit("/pull/", 1)[-1], None
    return ("*" if repo and len(repo) > 512 else repo), (number if number and len(number) <= 19 else None), url

try:
    payload = json.load(sys.stdin)
    tool_input = payload.get("tool_input", {})
    if not isinstance(tool_input, dict):
        tool_input = {}
    command = tool_input.get("command") or tool_input.get("cmd") or ""
    payload_cwd = tool_input.get("cwd") or tool_input.get("workdir") or ""
    # 実行先（payload の cwd と最上位の cwd）は、解析の lib（gh_command_parse）を import する前に渡す。
    # lib が壊れていても実行先の repo の GDD で不足を通知できるようにする（通知するのは parsed が出ないときの bash 側）。
    emit_cwd(payload_cwd)
    sys.path.insert(0, sys.argv[1])
    try:
        # Claude Code は cwd を payload の最上位に持つ。使えるなら bash がプロセスの cwd を移す
        # （lib/hook_cwd.py）。
        import hook_cwd
        top_cwd = hook_cwd.toplevel_cwd(payload)
        if top_cwd:
            emit("hook_cwd", top_cwd)
    except Exception:
        pass
    import gh_command_parse as gcp
    result = gcp.parse_gh_pr_merge(command, payload_cwd, sys.argv[2])
    emit("is_merge", "true" if result["is_merge"] else "false")
    # gh は番号を `strconv.Atoi` で読むので、先頭の 0 は同じ PR を指す（`007` は #7）。
    # 文字列で比べる照合（本体の steering・台帳）がすり抜けないよう、ここで 1 回だけ
    # 落とす。bash の展開で落とすと 0 の個数に二乗で効き、timeout は素通りになる。
    # 全部 0 なら `0`（存在しない PR）にする。
    pr = result["pr_number"]
    emit("pr_number", (pr.lstrip("0") or "0") if pr else pr)
    emit("pr_url", result["pr_url"])
    emit("repo_flag", result["repo_flag"])
    emit("unresolvable", "true" if result["unresolvable"] else "false")
    emit("env_repo_conflict", "true" if result["env_repo_conflict"] else "false")
    emit("admin", "true" if result["admin"] else "false")
    emit("cd_target", result["cd_target"] or "")
    emit("cd_intent", "true" if result["cd_intent"] else "false")
    emit("degraded", "true" if result["degraded"] else "false")
    emit("ledger_targets", "\x1e".join(dict.fromkeys(
        "\x1f".join(str(v or "").replace("\x1e", " ").replace("\x1f", " ") for v in ledger_target(*t))
        for t in result["ledger_targets"])))
    # 解析完走の標識は必ず最後に出す（途中で例外が出たら立たない）。
    emit("parsed", "true")
except Exception:
    pass
' "$SCRIPT_DIR/lib" "$PROCESS_CWD" 2>/dev/null || true)

# 最上位の cwd が使えたら（lib/hook_cwd.py）、trusted の候補であるプロセスの cwd をそこへ移す。
# 値を書くのは harness で、モデルが書く tool_input ではない。前の Bash 呼び出しの `cd` には
# 追従するが、CLI ではプロセスの cwd も同じ値で一緒に動く（2026-10-11、headless の claude で
# `cd sub` の後と、project の外への `cd` で戻された後の 4 回とも同じ値だった）。desktop の
# worktree のセッションではプロセスの cwd が root checkout に残る。後の `-d`・`git -C`・相対の
# payload cwd も、セッションの cwd から解決するようにする。
# 移れないときは、今までどおりプロセスの cwd に残る。
if [[ -n "$HOOK_CWD" ]] && cd "$HOOK_CWD" 2>/dev/null; then
  PROCESS_CWD="$(pwd && printf x)"
  PROCESS_CWD="${PROCESS_CWD%$'\n'x}"
fi
# URL の形の対象 PR の番号（パーサは正準形の URL だけを pr_url にする）。記録との照合は、
# URL の形でも番号の形と同じく番号で行う（文字列全体で比べると、正準形でない記録
# 〔`<…>`・`| 注記`・リンクの形・`/files`・先頭の 0〕を照合できない）。repo の違いは
# 3 組解決の (d) が不足として通知する。
PR_URL_NUMBER=""
[[ -z "$PR_URL_ARG" ]] || PR_URL_NUMBER="${PR_URL_ARG##*/pull/}"

# step 4（定義のみ前倒し）: lib を source する（関数・定数定義のみで副作用なし）。
# 解析失敗の fail-closed（step 2b）が action カタログと復旧要素の定数を必要と
# するため、定義だけを step 3a より前へ出す。実行順の意味は変えていない。
source "$SCRIPT_DIR/lib/detect-steering.sh"
source "$SCRIPT_DIR/lib/self-review-evidence.sh"
source "$SCRIPT_DIR/lib/merge-gate-evidence.sh"
source "$SCRIPT_DIR/lib/gdd-pr-roots.sh"
source "$SCRIPT_DIR/lib/merge-gate-binding.sh"
source "$SCRIPT_DIR/lib/gate-ledger.sh"

# design.md § reason code カタログ（確定版）の「次の 1 アクション」列の正本。
# 語順原則（design.md § Delivery Channel Rendering Check）:
# `<命令形の次の 1 アクション>。<観測値>。<復旧要素>`。日本語は述語末尾言語なので、
# 末尾から切り詰められたときに最初に失われるのが動詞 = アクションにならないよう、
# アクションを先頭へ置く。code ごとに文面が異なる（1 文へ潰さない）。
_mg_action() {
  case "${1:-}" in
    approval-missing)          printf '%s' 'ユーザーにマージ可否を確認し、承認を得たうえで Merge Approval を記録してから再実行してください' ;;
    approval-pr-mismatch)      printf '%s' '対象 PR を明示して承認を取り直し、Merge Approval を更新してください' ;;
    approval-sha-mismatch)     printf '%s' '現在の HEAD で承認を取り直してください（承認後に push しています）' ;;
    approval-stale)            printf '%s' '承認を取り直してください（鮮度上限を超過しています）' ;;
    pr-target-unresolvable)    printf '%s' 'root の repo 内のディレクトリで実行するか、実在する repo を cd に指定する形（絶対パスの cd をコマンドの先頭に 1 つだけ書き、コマンド全体に $・バッククォート・env を含めない）で実行してください（URL か -R owner/repo <番号> での明示も可、GH_REPO / gh repo set-default は外す。cd を先頭に書かないなら、chdir は別のコマンドに分ける）' ;;
    pr-url-unrecorded)         printf '%s' 'state.md に PR URL を記録してから再実行してください（このステアリングを使わないなら、ユーザーに確認したうえで references/self-review-lanes.md の「使わないステアリングの終え方」に従って終える）' ;;
    steering-ambiguous)        printf '%s' '対象 PR を URL か番号で明示するか、完了済み steering を 1 件に整理してから再実行してください' ;;
    steering-outside-binding)  printf '%s' 'ユーザーに確認して、binding を作業中の steering に付け直すか、使わない steering を終えてから再実行してください。worktree の binding が .steering/ の外の steering を指し、対象 PR を記録した steering を照合できません' ;;
    steering-ambiguous-binding) printf '%s' 'ユーザーに確認して、使わない steering の binding（.gdd/tasks/*/binding.json）を消すか、その state.md の PR URL を直してから再実行してください。対象 PR を記録した steering を指す binding が 2 件以上あります' ;;
    recheck-missing)           printf '%s' 'review/checks を再 fetch して証跡を記録してください' ;;
    recheck-sha-mismatch)      printf '%s' '現在の HEAD で再 fetch し証跡を更新してください' ;;
    recheck-stale)             printf '%s' '再 fetch を取り直してください' ;;
    recheck-blocking)          printf '%s' 'マージせず修正ループへ戻ってください' ;;
    review-push-missing)       printf '%s' 'PR head を更新した push の時刻と sha を記録してください' ;;
    bot-review-flag-missing)   printf '%s' 'bot レビューの受信状況を再取得して記録してください' ;;
    review-wait-not-elapsed)   printf '%s' 'HEAD で high 0 の独立レビューを記録するか、残り分だけ待つ（ScheduleWakeup を再武装する）か、bot レビューの着弾を確認してください' ;;
    independent-review-missing) printf '%s' '実装文脈を渡さない独立レビューを 1 回実行し、結果を記録してください' ;;
    medium-disposition-missing) printf '%s' 'medium ゼロでない場合の処遇を Medium Disposition に記録してから再実行してください（HEAD sha / count / follow-up PR・issue の参照または accepted + 理由 1 行）' ;;
    parse-error)               printf '%s' 'コマンドのクォートが閉じているかを確認し、解消しなければ python3 が実行できるか・hook へ渡る入力が壊れていないかを確認してから再実行してください' ;;
    state-unreadable)          printf '%s' 'state.md の所在と読み取り権限と、ステアリングの下のシンボリックリンク（実体のディレクトリ・ファイルに置き換える）を確認してください' ;;
    evidence-unparsable)       printf '%s' '該当証跡行の書式を確認してください' ;;
    evidence-malformed)        printf '%s' '該当証跡行の値ドメインを確認してください' ;;
    head-unresolvable)         printf '%s' 'git repo の状態を確認してください' ;;
    repo-root-unresolvable)    printf '%s' 'repo 内のディレクトリを cwd にしたセッションから、対象 PR を URL か -R owner/repo <番号> で明示して実行してください。GDD の worktree に marker〔.claude/gdd-dev.local.md〕があるなら、cd <worktree の絶対パス> && gh pr merge の形でもよい（cd はコマンドの先頭に 1 つだけ書き、コマンド全体に $・バッククォート・env を含めない。cwd が git の外のセッションからは、marker の無い GDD worktree へ cd しても root が決まらず binding を引かない。hook が root を決められ〔セッションの cwd が repo の中、または cd 先に marker がある〕、対象 PR を番号か URL で明示した merge は、対象 PR の steering を指す binding〔.gdd/tasks/*/binding.json〕があれば、その GDD worktree の証跡で判定する。binding が無く、台帳に載った GDD worktree に marker〔.claude/gdd-dev.local.md〕も無いと、cd しても同じ照合で止まり続けるので、そのときは人が merge する）' ;;
    untrusted-root-unverified) printf '%s' 'repo 内のディレクトリでセッションを起動して実行するか、対象 PR の承認証跡を steering に記録してから再実行してください' ;;
    *)                         printf '%s' '不足している検証を解消してから再実行してください' ;;
  esac
}

# `PR URL` 未記録（= 判定材料の欠落）の block reason。単一 steering 経路と
# `multiple` 経路の両方から呼ぶ（文面が 2 箇所に分かれると、片方だけ
# 直したときに steering 件数で判定が割れる）。
_mg_block_pr_url_unrecorded() {
  block "⛔ merge gate（reason code: pr-url-unrecorded）: $(_mg_action pr-url-unrecorded)。不足 key: PR URL。${GDD_MG_RECOVERY_CORE}。${GDD_MG_KILL_SWITCH_HINT}"
}

# untrusted 由来 root（payload cwd / cd_target）で gate 起動根拠が無い経路の
# block（AC-13/AC-14）。observed には絶対パス・slug・repo 名を含めない。
_mg_block_untrusted_root_unverified() {
  local _observed="$1"
  block "⛔ merge gate（reason code: untrusted-root-unverified）: $(_mg_action untrusted-root-unverified)。${_observed}。${GDD_MG_RECOVERY_CORE}。${GDD_MG_KILL_SWITCH_HINT}"
}

# root 候補 3 段（trusted process cwd / untrusted payload cwd / untrusted cd_target）が全滅、
# または確定した候補への `cd` が失敗したときの block reason（AC-1/AC-2/AC-12）。候補ループの
# 2 呼び出し箇所で文面が分かれると、片方だけ訂正したときに経路で文言が割れる
# （`_mg_block_pr_url_unrecorded` と同じ理由で 1 箇所化する）。
_mg_block_repo_root_unresolvable() {
  block "⛔ merge gate（reason code: repo-root-unresolvable）: $(_mg_action repo-root-unresolvable)。${GDD_MG_KILL_SWITCH_HINT}"
}

# root（承認証跡の出所）と `gh` の実行先（payload cwd / `cd` 先）が別 repo、
# または実行先 signal は届いたのに repo として解決できないときの block reason
# （AC-18）。既存 code `pr-target-unresolvable` に合流させ、新 code は増やさない。
# 文面の構成は step 10-11 の集約 block と同じ語順（<アクション>。不足条件。
# <code → 観測値>。<復旧要素>）に揃える。観測値に絶対パスは出さない
# （masking policy）。
_mg_block_pr_target_mismatch() {
  block "⛔ merge gate（reason code: pr-target-unresolvable）: $(_mg_action pr-target-unresolvable)。不足条件: pr-target-unresolvable。pr-target-unresolvable → 実行先（cwd / cd 先）の repo が root と一致しない、または解決できない。${GDD_MG_RECOVERY_CORE}。${GDD_MG_KILL_SWITCH_HINT}"
}

# suppression 記録（best-effort。書き込み失敗で gate 判定を変えない）。形と秘匿（repo は絶対パス全体の
# sha1 先頭 8 桁、`chmod 600`、FIFO を開かない）は lib/gate-notice.sh の `_gdd_gate_notice_log` が正本。
_mg_log_suppressed() {
  _gdd_gate_notice_log "merge-gate-suppressed.log" "$1"
}

# epoch（parser が検証のときに変換した GDD_MG_*_EPOCH）から「今」までの経過秒数を返す（負値・数でなければ -1）。
# `Pre-Merge Review Recheck` の鮮度（10 分）と待機経過（40 分）はどちらもこの
# 1 関数で判定する。秒単位の整数で比較し、「今」を `date -u +%s` から読むのは
# `merge-gate-evidence.sh` の `gdd_mg_epoch_within_minutes` と同じ規約に揃えるため。
_mg_elapsed_seconds() {
  local _elapsed
  [[ "${1:-}" =~ ^-?[0-9]+$ ]] || { echo -1; return 0; }
  _elapsed=$(( $(date -u +%s) - $1 ))
  [[ "$_elapsed" -ge 0 ]] || _elapsed=-1
  echo "$_elapsed"
}

# step 2b: 解析が完走したうえで「merge ではない」と分かった場合だけ、ここで即通過する。
# 解析が完走しなかった場合（python3 不在 / 不正 JSON / import 失敗）は「merge ではない」
# と断定できない。承認も証跡も検査せずに通すと無出力素通りになるので、判定を打ち切らず
# GDD セッション判定（step 5）まで進めてから fail-closed にする（step 5b）。
# ここで即 block() で通知しないのは、gate が管轄しない repo の `gh` を含む無関係なコマンドまで
# 巻き込んで不足として通知しないため。
if [[ "$PARSED" == "true" && "$DEGRADED" != "true" && "$IS_MERGE" != "true" ]]; then
  exit 0
fi

# step 3a: root 候補の決定（design.md § 変更点の要約 2 / AC-2）。
# 候補順: hook プロセス cwd（trusted）-> payload cwd（untrusted）-> cd_target
# （untrusted）。untrusted 候補は解決先に GDD marker があるときだけ採用する
# （AC-11）。marker path は 1 箇所に正本化する（AC-15。step 5 でも再利用）。
_mg_marker_path() {
  printf '%s/.claude/gdd-dev.local.md' "$1"
}

# 大小文字を区別しない一致判定（GitHub は owner/repo の大小文字を区別しない）。
# URL の比較経路もここを通す — 通さないと
# `gh pr merge https://github.com/Acme/Widgets/pull/7` が gate 対象判定で外れ、
# `active: false`（または所有を確認できない marker。merge 時の既定状態）では
# 承認も証跡も見ずに素通りする。
#
# `| tr` は使わない。`set -euo pipefail` 下の代入で外部コマンドが失敗すると hook ごと
# 即死し、通知を返せずに素通りになる（実測: `tr` を exit 127 に差し替えると無出力）。
# fail-closed の判定本体に、通知を返せなくなる失敗モードを持つ依存を足さない。
# `nocasematch` は bash builtin なので fork も失敗モードも無い。
_mg_equals_ci() {
  local _saved _result=0
  # `shopt -p <name>` は option が**未設定のとき exit 1**（既定は未設定）。`|| true`
  # を落とすと、`set -euo pipefail` 下でこの代入が失敗し、`if` 条件の外に置いた
  # 呼び出しで hook が無出力 exit 1 になる（= 通知を返せず素通り）。
  _saved="$(shopt -p nocasematch || true)"
  shopt -s nocasematch
  [[ "${1:-}" == "${2:-}" ]] || _result=1
  eval "$_saved"
  return "$_result"
}

# `owner/repo` へ正規化する。`https://github.com/o/r(.git)` / `git@host:o/r.git` /
# `host/o/r` / `o/r` を受け、取れなければ空を返す（= 照合しない、ではなく
# 呼び出し側が解決不能として倒す材料にする）。
_mg_owner_repo() {
  local _v="${1:-}" _repo _rest _owner
  _v="${_v%.git}"
  _v="${_v%/}"
  case "$_v" in
    *://*) _v="${_v#*://}" ;;
    *:*)   _v="${_v##*:}" ;;
  esac
  [[ "$_v" == */* ]] || { printf ''; return 0; }
  _repo="${_v##*/}"
  _rest="${_v%/*}"
  _owner="${_rest##*/}"
  [[ -n "$_owner" && -n "$_repo" ]] || { printf ''; return 0; }
  # 正規化はしない。大小文字の差は照合側（`_mg_equals_ci`）が吸収する。
  printf '%s/%s' "$_owner" "$_repo"
}

# repo を名指しできる owner/name と PR の URL の形（許可リスト）。展開前の `$`・`*`・`{}` などを
# 含む値は、実シェルで別の文字列になるので、名指しした repo として扱わない。
# `set -u` の下で使う関数（`_mg_ledger_verdict`・`_mg_explicit_target`）より前に定義する。
_MG_EXPLICIT_URL_RE='^https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/pull/[0-9]+$'
_MG_EXPLICIT_REPO_RE='^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$'

# 対象を repo つきで明示した merge（PR の URL、リテラルの `-R owner/name <番号>`）は、gh が
# 操作する repo と PR が実行先に依存しない。実行先が root と違う・決められないときも
# pr-target-unresolvable として通知せず、root の証跡で検査する。root の steering に対象 PR が無い
# 素通りの exit では、共通ディレクトリの経路と同じく GDD の PR 台帳を引き、miss だけ通す
# （台帳に載っている別の GDD worktree の PR を、その証跡を見ずに通さない）。root を決められない
# 経路でも、cd の意図・cd 先・payload の cwd を見ずに台帳だけで決める。owner/name は
# 許可リストの文字だけを明示として受ける。`$`・`*`・host つきの `-R` などは明示に当たらず、
# 実行先を決められなければ今までどおり不足として通知する。
_mg_explicit_target() {
  [[ "$UNRESOLVABLE" != "true" && "$ENV_REPO_CONFLICT" != "true" ]] || return 1
  if [[ -n "$PR_URL_ARG" ]]; then
    [[ "$PR_URL_ARG" =~ $_MG_EXPLICIT_URL_RE ]] || return 1
    return 0
  fi
  [[ -n "$PR_NUMBER" && "$REPO_FLAG" =~ $_MG_EXPLICIT_REPO_RE ]] || return 1
  return 0
}

# 絶対パス $1 の論理パス・物理パスそれぞれの祖先（自身を含む）に marker があるか。
# git に頼らない: git 不在や `git rev-parse` 失敗（dubious ownership 等）で候補ループが
# marker repo を見落としても、ここで拾う。物理パスを解決できなければ「ある」側へ倒す。
_mg_marker_in_ancestors() {
  local _physical _d
  _physical="$(cd "$1" 2>/dev/null && pwd -P)" || return 0
  for _d in "$1" "$_physical"; do
    while :; do
      [[ -e "$(_mg_marker_path "$_d")" ]] && return 0
      [[ "$_d" != "/" ]] || break
      _d="${_d%/*}"
      [[ -n "$_d" ]] || _d="/"
    done
  done
  return 1
}

# root 未解決の merge が GDD の対象外だと判定できるか。判定できるのは、解析が
# 縮退なく完走し、実行先（プロセス cwd / payload cwd / cd 先）がすべて実在する
# 絶対パスで 1 つに確定し、そのどれの祖先にも marker が無いときだけ。曖昧な chdir
# （`pushd` / `(cd …)` / 2 つ目の `cd` 等）・相対や不在の実行先は判定できない側。
_mg_outside_gdd_merge() {
  local _d
  [[ "$PARSED" == "true" && "$DEGRADED" != "true" ]] || return 1
  [[ "$CD_INTENT" != "true" || -n "$CD_TARGET" ]] || return 1
  if [[ -n "$PAYLOAD_CWD_RAW" ]]; then
    [[ "$PAYLOAD_CWD_RAW" == /* && -n "$PAYLOAD_CWD" ]] || return 1
  fi
  if [[ -n "$CD_TARGET" ]]; then
    [[ "$CD_TARGET" == /* && -d "$CD_TARGET" ]] || return 1
  fi
  for _d in "$PROCESS_CWD" "$PAYLOAD_CWD" "$CD_TARGET"; do
    [[ -n "$_d" ]] || continue
    ! _mg_marker_in_ancestors "$_d" || return 1
  done
  return 0
}

# 対象を repo つきで明示した root 未解決の merge が GDD の対象外だと判定できるか。決められない
# 実行先（cd の意図だけの cd 先・相対や不在のパス）は見ず、決められる実行先の祖先に marker が
# あれば判定できない側（git が無い・`rev-parse` が失敗した GDD worktree を通さない）。
_mg_explicit_outside_gdd_merge() {
  local _d
  [[ "$PARSED" == "true" && "$DEGRADED" != "true" ]] || return 1
  _mg_explicit_target || return 1
  for _d in "$PROCESS_CWD" "$PAYLOAD_CWD" "$CD_TARGET"; do
    [[ -n "$_d" && "$_d" == /* && -d "$_d" ]] || continue
    ! _mg_marker_in_ancestors "$_d" || return 1
  done
  return 0
}

# `gh` の実行先 repo の root（cd 先 > payload cwd > プロセス cwd。候補ループが解決した
# toplevel を使う）。曖昧な chdir で実行先を 1 つに決められないときは空を返す。
_mg_exec_root() {
  if [[ -n "$CD_TARGET" ]]; then
    printf '%s' "${_MG_CAND_ROOT[2]}"
  elif [[ "$CD_INTENT" == "true" ]]; then
    return 0
  elif [[ -n "$PAYLOAD_CWD_RAW" ]]; then
    printf '%s' "${_MG_CAND_ROOT[1]}"
  else
    printf '%s' "${_MG_CAND_ROOT[0]}"
  fi
}

# `_mg_ledger_verdict` の照合の組 (repo, 番号) を足す（呼び出し元の local の配列に書く）。owner/repo が
# 許可リストの形でなければ（展開前の `$`・`*` など）、番号だけで照合する（展開前の文字列は台帳の
# repo と一致せず、miss で通ってしまう）。
_mg_ledger_pair() {
  if [[ "$1" =~ $_MG_EXPLICIT_REPO_RE ]]; then
    _repos+=("$1")
  else
    _repos+=("*"); _undetermined="true"
  fi
  _nums+=("$2")
}

# `_mg_ledger_verdict` の照合の組を、URL $1 から足す（呼び出し元の local に書く）。
_mg_ledger_add_url() {
  local _repo="$(_mg_owner_repo "${1%/pull/*}")"
  if [[ -n "$_repo" ]]; then _mg_ledger_pair "$_repo" "${1##*/pull/}"; else _undetermined="true"; fi
}

# 同じく番号 $1 と `-R` の値 $2 から足す。`-R` が無ければ実行先の origin から repo を決める（呼び出し元の
# `_exec_repo` に 1 回だけ求める）。`-R` の値が owner/repo に解決しなければ（未展開の `$REPO`、parser の印 `*`）、
# 番号だけで照合する。
_mg_ledger_add_number() {
  local _repo="" _num="${1%%[!0-9]*}" _exec="" _resolved="" _others=""
  if [[ -n "$2" ]]; then
    _repo="$(_mg_owner_repo "$2")"
    if [[ -z "$_repo" && -n "$_num" ]]; then _repos+=("*"); _nums+=("$_num"); _undetermined="true"; return 0; fi
  elif [[ -n "$_exec_repo" ]]; then
    _repo="${_exec_repo#*:}"; _exec="${_exec_repo%%:*}"
  else
    _exec="$(_mg_exec_root)"
    if [[ -n "$_exec" ]]; then
      _resolved="$(git -C "$_exec" config --get remote.origin.gh-resolved 2>/dev/null || true)"
      # set-default の値が origin と別の repo を指すときは特定できない（3 組解決 (c) と同じ）。
      _repo="$(_mg_owner_repo "$(git -C "$_exec" remote get-url origin 2>/dev/null || true)")"
      if [[ -n "$_resolved" && "$_resolved" != "base" ]] \
        && ! _mg_equals_ci "$(_mg_owner_repo "$_resolved")" "$_repo"; then
        _repo=""
      fi
      # origin 以外の remote（fork の upstream など）に set-default の値があると、gh は
      # そちらを対象にしうる。origin の値によらず特定できないとする。
      _others="$(git -C "$_exec" config --get-regexp '^remote\..*\.gh-resolved$' 2>/dev/null || true)"$'\n'
      while [[ -n "$_others" ]]; do
        case "${_others%%$'\n'*}" in ""|"remote.origin.gh-resolved "*) ;; *) _repo="" ;; esac; _others="${_others#*$'\n'}"
      done
    fi
    _exec_repo="${_exec:+x}:$_repo"
  fi
  if [[ -n "$_repo" && -n "$_num" ]]; then
    _mg_ledger_pair "$_repo" "$_num"
  elif [[ -z "$2" && -z "$_exec" && -n "$_num" ]]; then
    # 例外: 実行先を決められない（chdir・解決できない payload の cwd）番号形は、番号だけで照合する（外れたら unknown）。
    _repos+=("*"); _nums+=("$_num"); _undetermined="true"
  else
    _undetermined="true"
  fi
}

# marker が無いので通す経路で、対象 PR（owner/repo と番号の組）を GDD の PR 台帳（`lib/gdd-pr-roots.sh`）に載った
# root の `.steering/*/state.md`（ドットで始まる task dir を含む）の `PR URL` と照合し、結果を `_MG_LEDGER` に入れる
# （呼び出し前は `unreadable` を入れておく）。読めないものに当たっても全部を走査し、
# hit > unreadable > unknown > miss の順で決める（後ろの hit を隠さない）。
#   hit         = 台帳の PR と一致
#   miss        = 一致しない・台帳が無い
#   unknown     = 対象 PR を特定できない
#   unreadable  = 台帳の場所が決まらない。台帳が通常ファイルでない・壊れた symlink・読めない、台帳が無くて親が辿れない。
#                 root が辿れない、`.steering` の下に列挙から落ちるものがある（`gdd_path_kind`・`gdd_steering_unreadable`）
# 経路ごとの倒し方は呼び出し側が決める。root 未解決の経路と、共通ディレクトリで通した
# 実行先・対象を repo つきで明示した merge の経路（`_mg_ledger_check_at_exit`）は miss だけ通し、
# git cwd の marker 不在の経路と、trusted root の steering が対象 PR を記録していない出口（同じ関数）は
# hit だけ不足として通知する（unknown・unreadable は main の判定のまま）。
# 特定できない要素を「何にでも一致」にはしない。照合は (repo, 番号) の組で行う。例外は repo を決められない
# 番号（実行先を決められない `-R` 無しの番号、owner/repo に解決しない `-R`、位置引数 2 つ以上の merge）で、
# 番号だけで照合する（外れたら unknown）。`env_repo_conflict` は照合せず unknown。`unresolvable` でも読めた URL と
# 番号は照合し、台帳の PR に当たれば hit にする。git cwd の経路は unknown を通すので、hit を先に見ないと通る。
_mg_ledger_verdict() {
  local _file="" _repo="" _num="" _line="" _root="" _state=""
  local _url="" _rrepo="" _roots="" _rest="" _unreadable="false" _rc=0
  local _undetermined="false" _i=0 _exec_repo=""
  local -a _repos=() _nums=()
  _MG_LEDGER="unreadable"
  _file="$(gdd_pr_roots_file)"
  [[ -n "$_file" ]] || return 0
  gdd_path_kind "$_file" file || _rc=$?
  if [[ "$_rc" -eq 2 ]]; then
    # 台帳が無い。親が在るのに辿れなければ、無いのか読めないのか決められない。
    _rc=0
    gdd_path_kind "${_file%/*}" dir || _rc=$?
    [[ "$_rc" -ne 1 ]] || return 0
    _MG_LEDGER="miss"
    return 0
  fi
  [[ "$_rc" -eq 0 ]] || return 0
  _MG_LEDGER="unknown"
  [[ "$ENV_REPO_CONFLICT" != "true" ]] || return 0
  # 照合する (repo, 番号) の組。URL と番号の両方が見えるとき（対象を決められない merge）は
  # 両方を照合し、どちらかが台帳の PR に当たれば不足として通知する。組を作れない対象が 1 つでもあれば、
  # 当たらなかったときに miss ではなく unknown にする。組は merge ごと（1 本の merge は 1 組、連結した merge・
  # 位置引数 2 つ以上は読めた番号・URL の全部。lib/gh_command_parse.py の ledger_targets）。
  _rest="$LEDGER_TARGETS"
  while [[ -n "$_rest" ]]; do
    _line="${_rest%%$'\x1e'*}"
    if [[ "$_rest" == *$'\x1e'* ]]; then _rest="${_rest#*$'\x1e'}"; else _rest=""; fi
    _repo="${_line%%$'\x1f'*}"; _line="${_line#*$'\x1f'}"
    _num="${_line%%$'\x1f'*}"; _url="${_line#*$'\x1f'}"
    [[ -z "$_url" ]] || _mg_ledger_add_url "$_url"
    [[ -z "$_num" ]] || _mg_ledger_add_number "$_num" "$_repo"
  done
  [[ "${#_nums[@]}" -gt 0 ]] || return 0
  [[ "$UNRESOLVABLE" != "true" ]] || _undetermined="true"
  _MG_LEDGER="unreadable"
  # 中身は 1 回で読み、行はリダイレクトを使わずに回す（リダイレクトの失敗は loop を
  # 飛ばして miss に進むので、#128 と同じ型の fail-open になる）。
  _roots="$(cat -- "$_file" 2>/dev/null)" || return 0
  # 読めないものに当たっても返さず、全部を走査する（後ろの hit を隠さない）。
  # 決め方は hit > unreadable > unknown > miss。在るのに期待の種類でない・辿れないものは unreadable。
  _rest="$_roots"
  while [[ -n "$_rest" ]]; do
    _root="${_rest%%$'\n'*}"
    if [[ "$_rest" == *$'\n'* ]]; then _rest="${_rest#*$'\n'}"; else _rest=""; fi
    [[ -n "$_root" ]] || continue
    _rc=0
    gdd_path_kind "$_root" dir || _rc=$?
    [[ "$_rc" -eq 2 ]] && continue
    [[ "$_rc" -eq 0 ]] || { _unreadable="true"; continue; }
    gdd_steering_unreadable "$_root" && _unreadable="true"
    for _state in "$_root"/.steering/*/state.md "$_root"/.steering/.[!.]*/state.md \
      "$_root"/.steering/..?*/state.md; do
      [[ -f "$_state" && -r "$_state" ]] || continue
      _url="$(gdd_extract_doc_field "$_state" "PR URL")"
      for ((_i = 0; _i < ${#_nums[@]}; _i++)); do
        _mg_url_matches_number "$_url" "${_nums[_i]}" || continue
        # 長すぎて番号を比べなかった URL は repo も比べない（展開が長さに二乗で効く）。
        # 記録の repo を取り出せないときも比べない。どちらも照合したものとして通知する側に倒す。
        if [[ "${_repos[_i]}" != "*" && "${#_url}" -le "$_MG_URL_MAX" ]]; then
          _rrepo="$(_mg_owner_repo "${_url%/pull/*}")"
          [[ -z "$_rrepo" ]] || _mg_equals_ci "${_repos[_i]}" "$_rrepo" || continue
        fi
        _MG_LEDGER="hit"
        return 0
      done
    done
  done
  if [[ "$_unreadable" == "true" ]]; then
    _MG_LEDGER="unreadable"
  elif [[ "$_undetermined" == "true" ]]; then
    _MG_LEDGER="unknown"
  else
    _MG_LEDGER="miss"
  fi
}

# PR URL の `/pull/` の後の番号（先頭の 0 を落とす）が、正規化済みの番号 $2 と一致するか。
# `_MG_URL_MAX` を超える URL は、`##` などの展開が長さに二乗で効き timeout（= 素通り）に
# なるので比べず、一致したものとして扱う（呼び出し側が通知する側へ進む。本体の経路では
# PR URL の値の範囲の検査が malformed として通知し、台帳の照合では hit になる）。
_MG_URL_MAX=512
_mg_url_matches_number() {
  local _u="$1" _n="$2"
  [[ -n "$_u" && -n "$_n" ]] || return 1
  [[ "${#_u}" -le "$_MG_URL_MAX" ]] || return 0
  [[ "$_u" == */pull/* ]] || return 1
  _u="${_u##*/pull/}"
  [[ "$_u" =~ ^0*([0-9]+) ]] || return 1
  [[ "${BASH_REMATCH[1]}" == "$_n" ]]
}

# PAYLOAD_CWD は、コマンドの解析と同じ埋め込みの python が `payload_cwd` で渡す（値が無ければ空）。
# 改行で終わる名前の別 repo（`<root>\n`）が root と同じ文字列にならないよう、末尾の改行も残して受け取る。
# 抽出直後に 1 回だけ絶対化する（main と同じ `cd && pwd` 形）。相対パスのまま
# 持ち回ると、候補ループ（`cd "$PROJECT_ROOT"` 前 = プロセス cwd 基準）と後段
# （`cd` 後 = PROJECT_ROOT 基準）が同じ文字列を別ディレクトリに解決し、AC-18 が
# 比較対象を失って無検査 exit 0 へ抜ける（impl-gate Round 3 IG-12）。解決
# できない値（不在 / 非 dir / 権限なし）は root 候補からは外す（AC-12: `if` 条件内で
# 吸収し hook を落とさない）が、「無い」とはみなさない —— raw 値は保持し、
# AC-18 が「実行先 signal は届いたのに解決できない」として block() で通知する
# （impl-gate Round 4 IG-13。解決不能を無視すると、正規化差 1 つごとに untrusted
# 実行先が無検査 exit 0 へ抜ける面が再発する）。
PAYLOAD_CWD_RAW="$PAYLOAD_CWD"
if [[ -n "$PAYLOAD_CWD" ]]; then
  # `pwd` の出力も番兵で取る（`<root>\n/` のように `/` で終わる値は、`pwd` が改行で
  # 終わるパスを返す）。
  if PAYLOAD_CWD="$(cd "$PAYLOAD_CWD" 2>/dev/null && pwd && printf x)" \
      && [[ "$PAYLOAD_CWD" == *$'\n'x ]]; then
    PAYLOAD_CWD="${PAYLOAD_CWD%$'\n'x}"
  else
    PAYLOAD_CWD=""
  fi
fi

# kill-switch の best-effort ログ（`_mg_log_suppressed`）は $PROJECT_ROOT を
# 使うため、候補ループより前に暫定代入する。
PROJECT_ROOT="$PROCESS_CWD"
PROJECT_ROOT_UNTRUSTED="false"

# kill-switch は best-effort 記録してから通す（AC-6b）。git root 解決より前に
# 置く（design.md § 主要フロー step 3→4。既存順序を維持）。
if gdd_kill_switch_active; then
  _mg_log_suppressed "kill-switch-bypass"
  exit 0
fi

# step 3b: git による project root の確定（IG-8 修正後の AC-2: marker を持つ
# 候補を優先する）。候補を順に試し、marker（`.claude/gdd-dev.local.md`）を
# 持つ最初の候補を採用する（trusted/untrusted を問わない）。trusted 候補
# （プロセス cwd）が git repo として解決しても marker が無い場合は、そこで
# 打ち切らず untrusted 候補（payload cwd / cd_target）の評価を続ける
# —— そうしないと marker + PR URL を持つ untrusted 候補が一度も評価されず、
# 本来不足を通知すべき merge が step 5 の marker 検査で無出力 `exit 0` に抜ける
# （impl-gate Round 1 IG-8。旧実装は trusted 候補が git repo として解決した
# 時点で無条件に break していた）。**全候補**が marker を持たない場合だけ、
# 従来どおり trusted 候補（解決できていれば）を root として採用する
# （AC-6(a) の `exit 0` 経路を維持。AC-12: 各候補の失敗は `if` 条件内で吸収し
# hook を落とさない）。
# 各候補の toplevel は**このループで 1 回だけ**解決し `_MG_CAND_ROOT[i]` に
# 保持する（root が確定しても残りの候補の解決は打ち切らない）。AC-18（step 5
# 直後）はこの結果を再利用し、`git -C` で同じ候補を再評価しない —— 再評価は
# 「root の決定と実行先の検査を別基準で行う」評価差の温床であり（IG-12）、
# 最悪経路の `git rev-parse` も 2 回減る（design.md § 主要フロー 7b）。
_MG_ROOT_RESOLVED="false"
_MG_TRUSTED_ROOT=""
_MG_TRUSTED_COMMON=""
_MG_CAND_CLASS=("trusted" "untrusted" "untrusted")
_MG_CAND_DIR=("$PROCESS_CWD" "$PAYLOAD_CWD" "$CD_TARGET")
_MG_CAND_ROOT=("" "" "")
# 各候補の git の共通ディレクトリ（AC-18 で同じ repo の別 worktree を見分ける）。
# toplevel と同じ `rev-parse` 1 回で取り、出力がちょうど 2 行で両方が絶対パスの
# ときだけ採る。古い git（2.31 未満）は未知の `--path-format=absolute` をそのまま
# 出力し、共通ディレクトリを相対パスで返すので、行の位置で読むと全候補が同じ値に
# なる。パスが改行を含むときも 2 行にならない（最初の改行で切ると、別のパスが
# root と同じ文字列になる）。採れないときは、共通ディレクトリを空（= 一致しない
# 側）にし、toplevel は従来どおり `--show-toplevel` 単独の呼び出しで取り直す。
# どちらの呼び出しも、`$()` が落とす末尾の改行を番兵 `x` で保って取る（落とすと
# `<root>\n` の toplevel・共通ディレクトリが root のものと同じ文字列になる）。
_MG_CAND_COMMON=("" "" "")
_MG_ROOT_COMMON=""
_MG_NEWLINE_TARGET="false"
if command -v git >/dev/null 2>&1; then
  for _mg_i in 0 1 2; do
    _mg_cand="${_MG_CAND_DIR[$_mg_i]}"
    [[ -n "$_mg_cand" && -d "$_mg_cand" ]] || continue
    _mg_cand_root=""
    _mg_cand_common=""
    if _mg_rev="$(git -C "$_mg_cand" rev-parse --show-toplevel --path-format=absolute --git-common-dir 2>/dev/null && printf x)" \
        && [[ "$_mg_rev" == *$'\n'x ]] && _mg_rev="${_mg_rev%$'\n'x}" \
        && [[ "$_mg_rev" == /*$'\n'/* && "${_mg_rev#*$'\n'}" != *$'\n'* ]]; then
      _mg_cand_root="${_mg_rev%%$'\n'*}"
      _mg_cand_common="${_mg_rev#*$'\n'}"
    elif ! _mg_cand_root="$(git -C "$_mg_cand" rev-parse --show-toplevel 2>/dev/null && printf x)" \
        || [[ "$_mg_cand_root" != *$'\n'x ]]; then
      continue
    else
      _mg_cand_root="${_mg_cand_root%$'\n'x}"
      # 改行で終わる toplevel は root にも比較対象にもせず、merge なら下で不足として通知する
      # （後段の steering の解決は `cd "$PROJECT_ROOT"` の後に
      # `$(git rev-parse --show-toplevel)` で取り直し、末尾の改行を落とす。候補から
      # 外すだけだと、marker の無い root では台帳の照合に回って通る）。途中の改行は
      # 今どおり採る。
      if [[ "$_mg_cand_root" == *$'\n' ]]; then
        _MG_NEWLINE_TARGET="true"
        continue
      fi
    fi
    _MG_CAND_ROOT[$_mg_i]="$_mg_cand_root"
    _MG_CAND_COMMON[$_mg_i]="$_mg_cand_common"
    if [[ "${_MG_CAND_CLASS[$_mg_i]}" == "trusted" ]]; then
      _MG_TRUSTED_ROOT="$_mg_cand_root"
      _MG_TRUSTED_COMMON="$_mg_cand_common"
    fi
    [[ "$_MG_ROOT_RESOLVED" != "true" ]] || continue
    [[ -f "$(_mg_marker_path "$_mg_cand_root")" ]] || continue
    PROJECT_ROOT="$_mg_cand_root"
    _MG_ROOT_COMMON="$_mg_cand_common"
    [[ "${_MG_CAND_CLASS[$_mg_i]}" == "untrusted" ]] && PROJECT_ROOT_UNTRUSTED="true"
    _MG_ROOT_RESOLVED="true"
  done
  if [[ "$_MG_ROOT_RESOLVED" != "true" && -n "$_MG_TRUSTED_ROOT" ]]; then
    PROJECT_ROOT="$_MG_TRUSTED_ROOT"
    _MG_ROOT_COMMON="$_MG_TRUSTED_COMMON"
    _MG_ROOT_RESOLVED="true"
  fi
  # `cd` 先が root と同じ repo の別 worktree で marker を持つ（GDD の専用 worktree）
  # なら、`gh` が実際に走るその worktree を root にし、そこの証跡で判定する。対象 PR
  # を明示した merge に限る（省くと、`cd X & gh pr merge` のように `gh` がプロセス
  # cwd で走る形で、X の steering の PR を X の証跡で通してしまう）。steering の解決
  # は cwd に依存するので、下の `cd "$PROJECT_ROOT"` と marker の読み込みより前に置く。
  if [[ "$_MG_ROOT_RESOLVED" == "true" && "$UNRESOLVABLE" != "true" \
        && -n "$PR_NUMBER$PR_URL_ARG" && -n "$_MG_ROOT_COMMON" \
        && -n "${_MG_CAND_ROOT[2]}" && "${_MG_CAND_ROOT[2]}" != "$PROJECT_ROOT" \
        && "${_MG_CAND_COMMON[2]}" == "$_MG_ROOT_COMMON" \
        && -f "$(_mg_marker_path "${_MG_CAND_ROOT[2]}")" ]]; then
    PROJECT_ROOT="${_MG_CAND_ROOT[2]}"
    PROJECT_ROOT_UNTRUSTED="true"
  fi
fi
# toplevel が改行で終わる実行先は、`gh` が走る repo を root と照合できない。root の
# marker の有無を問わず不足として通知する（marker の無い root では、下の素通りの exit に届く）。
# merge でないと判定できた入力は step 2b で抜けているので、ここに来る入力は merge か、
# merge かを判定できない（解析の失敗・縮退）入力だけである。
if [[ "$_MG_NEWLINE_TARGET" == "true" ]]; then
  _mg_block_pr_target_mismatch
  exit 0
fi
if [[ "$_MG_ROOT_RESOLVED" != "true" ]]; then
  # 縮退のせいでここまで来ただけ（merge と判定できていない）の場合、root が
  # 解決できない = GDD セッションかどうかも決められないので、管轄外として通す。
  # ここで block() で通知すると、非 git ディレクトリで実行した **merge でもない** コマンドに
  # 「repo 内で実行してください」という無関係な理由で通知してしまう（AC-6(a) の
  # 管轄境界と矛盾する）。merge と判定できている場合は、下の GDD 対象外判定を
  # 通らなければ block() で通知する。
  # `PARSED != true`（python3 不在 / import 失敗 / 不正 JSON）は「merge ではない」
  # と断定できない family なので、ここでは通さない（通すと本物の
  # `gh pr merge -R owner/repo 7` が非 git ディレクトリで無出力素通りになる）。
  if [[ "$PARSED" == "true" && "$IS_MERGE" != "true" ]]; then
    exit 0
  fi
  # merge と判定できていても、GDD の対象ではないと判定できれば通す（非 git cwd から
  # marker の無い repo を `-R` / `cd` で merge する形。cwd が marker の無い git repo
  # なら step 5 の marker 不在の出口で、binding が当たらず台帳が hit でなければ通るので、それに揃える。
  # その出口では、対象を決めきれない形〔unresolvable・採らなかった cd 先〕は binding を引かずに通るが、
  # ここでは、採らなかった cd 先の形のうち URL・`owner/repo` の `-R` で対象を明示した merge だけを
  # 台帳の miss で通し、unresolvable の形は明示があっても不足として通知する。この非対称は docs/SECURITY.md の制限事項に書いた）。
  # ただし対象 PR が GDD の PR 台帳に載っていれば、GDD の worktree での実行へ誘導する（marker の
  # 無い worktree では、binding が対象 PR の steering を指さなければ同じ照合で通知の対象になる。lib/gdd-pr-roots.sh の限界）。
  # 対象 PR を特定できない（unknown）・台帳が読めない場合は main と同じく block() で通知する。
  # 対象を repo つきで明示した merge は、gh の対象が実行先に依存しないので、cd の意図や決められない
  # cd 先・payload の cwd があっても台帳で決める（`_mg_explicit_outside_gdd_merge`）。
  if _mg_outside_gdd_merge || _mg_explicit_outside_gdd_merge; then
    _MG_LEDGER="unreadable"
    _mg_ledger_verdict || true
    [[ "$_MG_LEDGER" != "miss" ]] || exit 0
  fi
  _mg_block_repo_root_unresolvable
  exit 0
fi
cd "$PROJECT_ROOT" 2>/dev/null || {
  _mg_block_repo_root_unresolvable
  exit 0
}

# step 5: active 判定（pre-push gate と同型の 2 段 + PR URL 一致の代替条件）。
# pre-push gate（run-pre-push-gate-hook.sh 107-122 行）と同型: `active: true`
# マーカーだけで gate 対象と分かる経路は、steering の解決を待たずに session
# continuity を検査する。不一致は block() の通知ではなく「起動根拠の除去（降格）」に倒す
# （他 gate 9 箇所と同じ管轄外＝ exit 0 系の扱いへ寄せる。通知にすると、示す復旧手順が
# 原理的に実行不能になるため。降格後も steering 解決・証跡検査は継続する）。
LOCAL_STATE="$(_mg_marker_path "$PROJECT_ROOT")"
# AC-6(a) の素通り面: このファイルは GDD セッション
# そのもののマーカーであり、不在 = 非 GDD セッション。`.steering/` が残っていても
# gate を起動しない。これを block() の通知に倒すと、steering を持ち込んだだけの repo の
# 正当な merge を全件不足として通知し、requirements § リスクの「誤爆による迂回の前例化」を
# 招く。マーカーを消して迂回できる面は「忘れは通知されるが偽りは通知されない」という
# 本 gate の強度モデル（requirements 77 行）の範囲内。
if [[ ! -f "$LOCAL_STATE" ]]; then
  if [[ "$PROJECT_ROOT_UNTRUSTED" == "true" ]]; then
    _mg_block_untrusted_root_unverified "起動根拠: セッションマーカー不在"
    exit 0
  fi
  # binding が対象 PR の steering を指せば、その worktree を root にして下の検査に進む（lib/merge-gate-binding.sh）。
  # 指さなければ、PR 台帳で hit の merge だけを不足として通知し、GDD の worktree へ誘導する（lib/gdd-pr-roots.sh の限界）。
  [[ "$IS_MERGE" != "true" || "$DEGRADED" == "true" ]] || gdd_mg_binding_switch "$(gdd_mg_binding_exec_root)"
  if [[ "$IS_MERGE" == "true" && "$_MG_VIA_BINDING" != "true" ]]; then
    _MG_LEDGER="unreadable"
    _mg_ledger_verdict || true
    [[ "$_MG_LEDGER" != "hit" ]] || { _mg_block_repo_root_unresolvable; exit 0; }
  fi
  [[ "$_MG_VIA_BINDING" == "true" ]] || exit 0
fi

# step 5b: ここから先は GDD セッションの管轄内。解析できていなければ fail-closed。
# gate 側の故障なので kill-switch を出口として案内する（kill-switch は step 4b で
# 評価済みなので、立っていればここへは到達しない）。
if [[ "$PARSED" != "true" || "$DEGRADED" == "true" ]]; then
  block "⛔ merge gate（reason code: parse-error）: $(_mg_action parse-error)。${GDD_MG_KILL_SWITCH_HINT}"
  exit 0
fi

# 対象を決められない merge（知らない flag・値の欠落・位置引数 2 つ以上・branch 名・名指しできない URL）は、
# 読めた番号・URL が記録の PR と違っても「別 PR の merge」とは言えない（gh は別の対象を
# 読むかもしれない。改行で続く別のコマンドの引数を位置引数に読んだ形もここに来る）。
# 番号・URL を空にして、対象を省いた merge と同じ経路に載せる（steering が 1 件に決まる
# found の経路は gate して、下の (a) で `pr-target-unresolvable`。複数・候補 0 件の経路は
# 対象を省いた merge と同じ `steering-ambiguous`）。台帳の経路（marker の無い checkout）は、
# 読めた番号・URL で照合する必要があるので、この行より前で終わっている。trusted root の
# 素通りの出口の台帳の照合（`_mg_ledger_check_at_exit`）も読めた値で行うので、空にする前に退避する。
_MG_READ_PR_NUMBER="$PR_NUMBER"
_MG_READ_PR_URL_ARG="$PR_URL_ARG"
_MG_READ_PR_URL_NUMBER="$PR_URL_NUMBER"
if [[ "$UNRESOLVABLE" == "true" ]]; then
  PR_NUMBER=""
  PR_URL_ARG=""
  PR_URL_NUMBER=""
fi

# step 5 の直後（AC-18）: root ≠ `gh` 実行先の遮断。untrusted 入力（payload cwd /
# cd_target）が示す実行先の toplevel が確定した PROJECT_ROOT と異なるなら、
# steering 解決より前にここで `pr-target-unresolvable` へ倒す（対象を repo つきで明示した merge は
# 倒さず、下の `_mg_explicit_target` のとおり root の証跡と台帳で決める）。
# 到達位置を marker 検査の直後に置く理由: trusted 候補（プロセス cwd）が marker を持つと候補ループは
# 候補 1 で確定し、marker + 対象 PR の steering を持つ payload cwd は評価されない。この位置より後ろには
# 「steering 未解決 / 対象 PR 不一致」の無検査 exit 0 が 3 面あり、そこへ抜けると main（payload
# cwd を root にしていた）が block していた入力が無出力 exit 0 になる
# （impl-gate Round 2 IG-9。旧設計は対象 PR 解決の後ろに置く予定だった）。
# 比較対象は step 3b の候補ループが 1 回だけ解決した toplevel
# （`_MG_CAND_ROOT[1]` = payload cwd / `[2]` = cd_target）を再利用し、ここで
# `git -C` を再評価しない（IG-12: `cd "$PROJECT_ROOT"` 後の再評価は候補ループと
# 別基準になり得る）。判定は「raw の実行先 signal が非空」を入口にし、解決した
# toplevel が PROJECT_ROOT と一致するとき、または下の共通ディレクトリの条件を
# 満たすときだけ通す。したがって非 git / 不在 /
# 権限なし等で候補ループが解決できなかった対象（`_MG_CAND_ROOT` が空）も通知する
# 側に倒れる（impl-gate Round 4 IG-13。解決不能を「無い」とみなす旧形は、
# marker 有無 / 相対パス / CDPATH と正規化差が崩れるたびに untrusted 実行先が
# 無検査 exit 0 へ抜けていた）。marker を検査するのは**確定した PROJECT_ROOT
# だけ**なので、「非 GDD の repo の merge を新たに不足として通知しない」が成り立つのは
# **全候補が marker を持たない**セッションに限る（requirements AC-18 の限定と同じ）。
# marker 付き repo のセッションから非 GDD の別 repo を `cd` して merge する形は、
# ここで新規に不足として通知される（CHANGELOG § User Action Required 3 番目）。
# toplevel が違っても、git の共通ディレクトリが同じ（同じ repo の別 worktree・root
# checkout）で marker の無い実行先なら、通常は `gh` の対象 repo も同じなので通す
# （ただし下のとおり GDD の PR 台帳を照合し、root 未解決の経路と同じく miss のときだけ
# 通す）。対象 PR を明示したときだけにする。省いた merge は実行先のブランチの PR を `gh` が選び、root の
# steering の PR と同じとは言えない。marker のある実行先は、上で root に切り替わって
# いなければ（payload cwd で指した形など）そこの証跡を見ていないので不足として通知する（対象を repo つきで
# 明示した merge は通知せず、下の `_mg_explicit_target` のとおり台帳を引く）。
# root の steering が対象 PR を記録していないと、下の素通りの exit（3 つ）に抜ける。そこでは
# `_mg_ledger_check_at_exit` で GDD の PR 台帳を照合する。共通ディレクトリの条件で通した実行先
# （root checkout など）と、対象を repo つきで明示した merge は、root 未解決の経路と同じく miss の
# ときだけ通す（hit のほか unknown・unreadable も不足として通知する。以前 AC-18 で止めていた形）。binding で
# 切り替えた root からここに来るのは、marker 不在の経路で新しい root の steering を解決できなかったとき
# で、hit だけで不足として通知する（root の steering に対象 PR が無いときの切り替えは、照合が当たる binding に限る）。それ以外の、対象 PR を名指しした merge は、
# git cwd の marker 不在の経路と同じく hit のときだけ不足として通知する（最上位の cwd へ移ると、root checkout の
# marker 不在の経路で通知していた別の worktree の GDD の PR が、marker のある worktree の素通りの exit に
# 来る）。照合は対象を決められない merge でも読めた番号・URL で行う（上で退避した値）。root の steering に
# 対象 PR があれば素通りの exit に来ないので、セッション自身の PR が台帳に載っていても通知しない。
_MG_EXEC_VIA_COMMON="false"
_mg_ledger_check_at_exit() {
  PR_NUMBER="$_MG_READ_PR_NUMBER"
  PR_URL_ARG="$_MG_READ_PR_URL_ARG"
  PR_URL_NUMBER="$_MG_READ_PR_URL_NUMBER"
  [[ -n "$PR_NUMBER$PR_URL_ARG$LEDGER_TARGETS" ]] || return 0
  _MG_LEDGER="unreadable"
  _mg_ledger_verdict || true
  if [[ "$_MG_EXEC_VIA_COMMON" == "true" ]]; then
    [[ "$_MG_LEDGER" != "miss" ]] || return 0
  else
    [[ "$_MG_LEDGER" == "hit" ]] || return 0
  fi
  _mg_block_repo_root_unresolvable
  exit 0
}
_MG_EXEC_RAW=("" "$PAYLOAD_CWD_RAW" "$CD_TARGET")
for _mg_i in 1 2; do  # binding で切り替えた root は、lib/merge-gate-binding.sh が repo を確かめ済み
  [[ "$_MG_VIA_BINDING" != "true" && -n "${_MG_EXEC_RAW[$_mg_i]}" ]] || continue
  [[ "${_MG_CAND_ROOT[$_mg_i]}" == "$PROJECT_ROOT" ]] && continue
  if [[ -n "$PR_NUMBER$PR_URL_ARG" && -n "$_MG_ROOT_COMMON" \
        && "${_MG_CAND_COMMON[$_mg_i]}" == "$_MG_ROOT_COMMON" \
        && ! -f "$(_mg_marker_path "${_MG_CAND_ROOT[$_mg_i]}")" ]]; then
    _MG_EXEC_VIA_COMMON="true"
    continue
  fi
  if _mg_explicit_target; then
    _MG_EXEC_VIA_COMMON="true"
    continue
  fi
  _mg_block_pr_target_mismatch
  exit 0
done
# (a‴) の拡張（impl-gate の High 指摘、人間承認済み案 (a)(1)）: 走査範囲に chdir
# intent（`cd` / `pushd` / `popd` / `chdir` / `env -C`）があるのに AC-4 の受理条件で
# `cd_target` を不採用にした形も「解決できない実行先」として同じ block() の通知へ倒す。
# 不採用 = 実行先を 1 つに確定できないだけで、実シェルは chdir している
# （`cd /A && cd /B`、`builtin cd /B`、`cd -- /B`、走査範囲に `$` / `env` を含む形、
# 語中 `#` で 2 つ目の `cd` を隠す形）。ここを「signal が無い」と同一視すると、
# AC-4 が不採用にするあらゆる形でプロセス cwd 由来 root の証跡により別 repo の
# merge が allow される（AC-4 × AC-18 の旧トレードオフ。design.md § Honest
# Limitations に既載だった面を、人間承認により通知する側へ閉じる）。対象を repo つきで明示した
# merge は gh の対象が実行先に依存しないので通知せず、`_mg_explicit_target` のとおり台帳で決める。
if [[ "$CD_INTENT" == "true" && -z "$CD_TARGET" ]]; then
  if _mg_explicit_target; then
    _MG_EXEC_VIA_COMMON="true"
  else
    _mg_block_pr_target_mismatch
    exit 0
  fi
fi

IS_OWNED_ACTIVE_MARKER="false"
# 切り替えた後は FIFO などの marker も届く（開くと止まる）
[[ -f "$LOCAL_STATE" ]] && grep -q '^active: true' "$LOCAL_STATE" 2>/dev/null && IS_OWNED_ACTIVE_MARKER="true"

# 自セッションが所有すると確認できない active marker は「起動根拠にしない」（降格）。
# 降格の理由は step 5 の見出しコメントに記載。
if [[ "$IS_OWNED_ACTIVE_MARKER" == "true" ]] && ! gdd_session_continuity_ok "$LOCAL_STATE"; then
  IS_OWNED_ACTIVE_MARKER="false"
  # ログ失敗で hook ごと落ちないよう subshell + `|| true` で二重に封じる。
  # `_mg_log_suppressed`（lib/gate-notice.sh の `_gdd_gate_notice_log`）は `HOME` 未設定なら
  # `${HOME:-}` で読んで 0 を返すので、即死しうるのは `shasum` / `sha1sum` の**両方**が無い・
  # あるいは実行に失敗する場合（pipefail）だけである。`exit 0` 直前の呼び出しは即死しても無害だが、
  # ここは**記録後も処理を継続する**位置で、即死すると証跡検査に到達せず無出力で終わる
  # （= silent fail-open）。同型の位置は `legacy-evidence-no-blocking-field` の呼び出しにもあり、
  # 同じ形にしている。
  ( _mg_log_suppressed "unowned-active-marker-demoted" ) 2>/dev/null || true
fi

gdd_pre_push_resolve_steering "$PROJECT_ROOT"

# `multiple` を **gate 対象判定より前** で無条件に block() で通知すると、
# done steering が 2 件ある checkout の **すべての** マージ（別 repo の無関係な PR を
# 含む）が不足として通知され、通知を消す手段は kill-switch か手動整理しかなくなる。到達性は高い
# （同一 checkout で GDD を 2 回完走した時点で `multiple`）。
# そこで「正本 state.md が決まらない」を、まず **対象 PR で解決** させる:
# コマンドが対象 PR を明示していれば、その PR URL を記録している steering が
# ちょうど 1 件のときに限りそれを正本にする。以下は `_MG_MATCH_STATUS` を返す。
#   one  = 正本が一意に決まる → 通常フローへ合流
#   none = 対象 PR を記録した steering が無く、**全候補が PR URL を記録済み**
#          （= 単一 steering 時の「PR URL が別 PR を指す」不一致と同じ素通り面。
#          ただし **自セッションが所有する** `active: true` marker は marker 単独で
#          gate 対象なので block() で通知する。所有を確認できない marker は step 5 で降格済みで、
#          ここには `IS_OWNED_ACTIVE_MARKER=false` として到達する）
#   many / unknown-target = AC-10 に従い fail-closed に block() で通知する
#
# URL 未記録の候補を **黙って落とす**と、`none` が「対象は別 PR
# （素通り面）」と「判定材料が無い（AC-10 の通知面）」の両方へ潰れる。単一
# steering 経路（下の `pr-url-unrecorded`）は同じ状況を block() で通知しているため、
# steering 件数だけで fail-closed が反転していた。落とした事実を
# `_MG_MATCH_URL_MISSING` で呼び出し側へ伝え、素通りは「全候補が記録済み」の
# ときだけに閉じる。

_mg_block_state_unreadable() {
  block "⛔ merge gate（reason code: state-unreadable）: $(_mg_action state-unreadable)。${GDD_MG_KILL_SWITCH_HINT}"
}

_mg_match_steering_by_target() {
  local _url_number="$1" _number="$2" _state _candidate_url _hits=0
  _MG_MATCH_STATUS="unknown-target"
  _MG_MATCHED_DIR=""
  _MG_MATCH_URL_MISSING="false"
  _MG_MATCH_URL_RECORDED="false"
  _MG_MATCH_UNREADABLE="false"
  # 対象 PR が無いときも列挙して、PR を記録した steering があるか（_MG_MATCH_URL_RECORDED）を伝える
  # （状態は unknown-target のまま）。
  # 読めない state.md・辿れない task dir は下の列挙から落ちるので、別に確かめて伝える
  # （対象 PR の steering が読めないだけなのに none で素通りさせない）。
  gdd_steering_unreadable "$PROJECT_ROOT" && _MG_MATCH_UNREADABLE="true"
  while IFS= read -r _state; do
    [[ -n "$_state" && -r "$_state" ]] || continue
    _candidate_url="$(gdd_extract_doc_field "$_state" "PR URL")"
    [[ -n "$_candidate_url" ]] || { _MG_MATCH_URL_MISSING="true"; continue; }
    _MG_MATCH_URL_RECORDED="true"
    [[ -n "$_url_number" || -n "$_number" ]] || continue
    if _mg_url_matches_number "$_candidate_url" "$_url_number" || _mg_url_matches_number "$_candidate_url" "$_number"; then
      _hits=$((_hits + 1))
      _MG_MATCHED_DIR="$(cd "$(dirname "$_state")" && pwd)"
    fi
  done < <(find "$PROJECT_ROOT/.steering" -mindepth 2 -maxdepth 2 -name state.md -type f 2>/dev/null | sort)
  [[ -n "$_url_number" || -n "$_number" ]] || return 0
  case "$_hits" in
    0) _MG_MATCH_STATUS="none" ;;
    1) _MG_MATCH_STATUS="one" ;;
    *) _MG_MATCH_STATUS="many" ;;
  esac
  return 0
}

gdd_mg_binding_switch_when_unmatched  # root の steering に対象 PR が無いとき（lib/merge-gate-binding.sh）
if [[ "$GDD_PP_STEERING_STATUS" == "multiple" ]]; then
  _mg_match_steering_by_target "$PR_URL_NUMBER" "$PR_NUMBER"
  if [[ "$_MG_MATCH_STATUS" == "one" ]]; then
    GDD_PP_STEERING_DIR="$_MG_MATCHED_DIR"
    GDD_PP_STEERING_STATUS="found"
  elif [[ "$_MG_MATCH_STATUS" == "none" && "$IS_OWNED_ACTIVE_MARKER" != "true" ]]; then
    # 判定材料の欠落（読めない steering・URL 未記録の候補がある）と、判定材料が
    # 揃ったうえでの不一致（別 PR）を分ける。前者は単一 steering 経路と同じ block() の通知へ倒す。
    if [[ "$_MG_MATCH_UNREADABLE" == "true" ]]; then
      _mg_block_state_unreadable
      exit 0
    fi
    if [[ "$_MG_MATCH_URL_MISSING" == "true" ]]; then
      _mg_block_pr_url_unrecorded
      exit 0
    fi
    # untrusted 由来 root には無検査 exit 0 を許さない（AC-13/AC-14）。
    if [[ "$PROJECT_ROOT_UNTRUSTED" == "true" ]]; then
      _mg_block_untrusted_root_unverified "起動根拠: 対象 PR を記録した steering なし"
      exit 0
    fi
    # 対象 PR の照合は `.steering/` だけを探す。数え直しで候補になった binding 先が `.steering/` の外に
    # あると、対象 PR を記録していても照合に載らないので不足として通知する（正規化できない候補も外として扱う）。
    _mg_steering_real="$(cd "$PROJECT_ROOT/.steering" 2>/dev/null && pwd -P || true)"
    if [[ ${#GDD_STEERING_CANDIDATES[@]} -gt 0 ]]; then
      for _mg_candidate in "${GDD_STEERING_CANDIDATES[@]}"; do
        _mg_candidate_real="$(cd "$_mg_candidate" 2>/dev/null && pwd -P || true)"
        if [[ -z "$_mg_steering_real" || -z "$_mg_candidate_real" \
          || "$(dirname "$_mg_candidate_real")" != "$_mg_steering_real" ]]; then
          block "⛔ merge gate（reason code: steering-ambiguous）: $(_mg_action steering-outside-binding)。${GDD_MG_KILL_SWITCH_HINT}"
          exit 0
        fi
      done
    fi
    _mg_ledger_check_at_exit
    _mg_log_suppressed "unresolved-steering-on-merge"
    exit 0
  else
    block "⛔ merge gate（reason code: steering-ambiguous）: $(_mg_action steering-ambiguous)。${GDD_MG_KILL_SWITCH_HINT}"
    exit 0
  fi
fi
# 候補 0 件でも、対象 PR を記録した steering（中止した steering を含む）は merge gate の対象に残す
# （中止した steering の PR を、承認の証跡なしに merge させない）。対象 PR を決められない merge は、
# PR を記録した steering があれば不足として通知する（multiple の経路と同じ）。
if [[ "$GDD_PP_STEERING_STATUS" != "found" ]]; then
  _mg_match_steering_by_target "$PR_URL_NUMBER" "$PR_NUMBER"
  if [[ "$_MG_MATCH_STATUS" == "one" ]]; then
    GDD_PP_STEERING_DIR="$_MG_MATCHED_DIR"
    GDD_PP_STEERING_STATUS="found"
  elif [[ "$_MG_MATCH_STATUS" == "many" \
    || ( "$_MG_MATCH_STATUS" == "unknown-target" && "$_MG_MATCH_URL_RECORDED" == "true" ) ]]; then
    block "⛔ merge gate（reason code: steering-ambiguous）: $(_mg_action steering-ambiguous)。${GDD_MG_KILL_SWITCH_HINT}"
    exit 0
  fi
fi
# それ以外の候補 0 件（`.steering/` 不在・対象 PR を記録した steering なし）は AC-6(a) の素通り面
# （trusted root のみ。untrusted 由来 root は AC-13/AC-14 で block() の通知へ倒す）。
if [[ "$GDD_PP_STEERING_STATUS" != "found" ]]; then
  if [[ "$PROJECT_ROOT_UNTRUSTED" == "true" ]]; then
    _mg_block_untrusted_root_unverified "起動根拠: steering 未解決"
    exit 0
  fi
  # 読めない steering は resolver の列挙から落ちて候補 0 件に見える。読める steering が
  # ほかにあると上の探し直しで通知されるので、件数で素通りに反転させない。
  if gdd_steering_unreadable "$PROJECT_ROOT"; then
    _mg_block_state_unreadable
    exit 0
  fi
  _mg_ledger_check_at_exit
  _mg_log_suppressed "unresolved-steering-on-merge"
  exit 0
fi
STEERING_STATE="$GDD_PP_STEERING_DIR/state.md"

# state.md の読み取り可否は、以降のあらゆる `gdd_extract_doc_field` 呼び出しより
# 前に確定させる。読み取り不能なファイルに対して awk を通すと `set -eo pipefail`
# 下でパイプが非 0 を返し、以降のコード（block() の呼び出しも含む）へ到達する前に
# hook プロセスごと無出力で落ちる（AC-10 の fail-closed を満たさない失敗モード）。
[[ -f "$STEERING_STATE" && -r "$STEERING_STATE" ]] || {
  _mg_block_state_unreadable
  exit 0
}

STEERING_PR_URL="$(gdd_extract_doc_field "$STEERING_STATE" "PR URL")"

# primary（gdd_detect_active_steering）は terminal でない steering を 1 件なら found で
# 返す。同じ checkout に対象 PR を記録した done の steering があっても、上の
# `multiple` の照合を通らない。コマンドが対象 PR を明示していて、found の steering の
# PR URL がそれと違う（または未記録の）ときは、対象 PR を記録した steering を全
# state.md から探し直し、ちょうど 1 件ならそれを正本にする。それ以外は今の正本のまま
# 下の判定へ進む。ただし所有 marker が無いときは、上の `multiple` 経路と同じく
# 対象 PR の steering が 2 件以上なら `steering-ambiguous`、対象 PR を記録した
# steering が無く URL 未記録の steering があれば `pr-url-unrecorded` で不足として通知する
# （steering の件数だけで fail-closed が反転しないようにする）。所有 marker が
# あるときは、found の steering の証跡で下の判定が不足として通知する。
if [[ -n "$PR_URL_ARG" || -n "$PR_NUMBER" ]] \
  && ! { [[ -n "$STEERING_PR_URL" ]] \
         && { _mg_url_matches_number "$STEERING_PR_URL" "$PR_URL_NUMBER" \
              || _mg_url_matches_number "$STEERING_PR_URL" "$PR_NUMBER"; }; }; then
  _mg_match_steering_by_target "$PR_URL_NUMBER" "$PR_NUMBER"
  if [[ "$_MG_MATCH_STATUS" == "one" ]]; then
    GDD_PP_STEERING_DIR="$_MG_MATCHED_DIR"
    STEERING_STATE="$GDD_PP_STEERING_DIR/state.md"
    STEERING_PR_URL="$(gdd_extract_doc_field "$STEERING_STATE" "PR URL")"
  elif [[ "$IS_OWNED_ACTIVE_MARKER" != "true" ]]; then
    if [[ "$_MG_MATCH_STATUS" == "many" ]]; then
      block "⛔ merge gate（reason code: steering-ambiguous）: $(_mg_action steering-ambiguous)。${GDD_MG_KILL_SWITCH_HINT}"
      exit 0
    fi
    if [[ "$_MG_MATCH_STATUS" == "none" && "$_MG_MATCH_UNREADABLE" == "true" ]]; then
      _mg_block_state_unreadable
      exit 0
    fi
    if [[ "$_MG_MATCH_STATUS" == "none" && "$_MG_MATCH_URL_MISSING" == "true" ]]; then
      _mg_block_pr_url_unrecorded
      exit 0
    fi
  fi
fi
PR_URL_MATCHES="false"
if [[ -n "$STEERING_PR_URL" ]]; then
  if [[ -z "$PR_URL_ARG" && -z "$PR_NUMBER" ]]; then
    # 引数省略 `gh pr merge`（design.md § 対象 PR の 3 組解決 が「最頻形」と呼ぶ形）
    # と、解決不能な位置引数（ブランチ名）。design.md § 対象 PR の 3 組解決 は
    # 「引数省略 → state.md の PR URL の PR を対象とみなす」と定めているので、
    # gate 対象判定（5c）でも PR URL 一致として扱う。ここを落とすと
    # `active: false`（または所有を確認できない marker。`<gdd-stop reason="done">`
    # 後の最頻状態）と組んだときに gate がまったく発火しない（実測した fail-open）。
    #
    # ここで `unresolvable != true` を条件に足すと、
    # `gh pr merge <branch>`（`gh pr merge --help` の USAGE が示す一級の呼び出し形）が
    # gate 対象外へ落ち、AC-1/AC-2/AC-3 が単一入力で同時に迂回される。解決不能な
    # 位置引数は「gate 対象ではない」ではなく「対象を決められない」なので、
    # gate 対象に含めたうえで下の TARGET_RESOLVE_FAILED（(a)）で
    # `pr-target-unresolvable` に倒す（AC-10 の fail-closed）。
    PR_URL_MATCHES="true"
  elif _mg_url_matches_number "$STEERING_PR_URL" "$PR_URL_NUMBER" || _mg_url_matches_number "$STEERING_PR_URL" "$PR_NUMBER"; then
    PR_URL_MATCHES="true"
  fi
fi

if [[ "$IS_OWNED_ACTIVE_MARKER" != "true" && "$PR_URL_MATCHES" != "true" ]]; then
  # `PR URL` が **未記録** の場合は gate 対象外ではなく「判定材料の欠落」（AC-10）。
  # merge 時の既定状態は `done` 後の `active: false`（または所有を確認できない
  # marker）で、その状態で gate を起動する唯一の signal が `PR URL` である以上、
  # 欠落したまま素通りさせると承認証跡も再 fetch 証跡も無い merge が通る。
  # AC-6 の 3 条件（steering 不在 / kill-switch / 非該当コマンド）のいずれでも
  # ないので block() の通知に倒す。stale な `.steering/` が残る
  # repo の正当な merge を誤爆した場合の逃がし口は kill-switch 1 本に閉じる
  # （current task 判定などの分岐は足さない）。`PR URL` が別 PR を指すだけの
  # 不一致は判定材料が揃っているので従来どおり素通りさせる（design.md 5c の境界）。
  if [[ -z "$STEERING_PR_URL" ]]; then
    _mg_block_pr_url_unrecorded
    exit 0
  fi
  # `PR URL` は記録済みだが対象 PR とは別（判定材料は揃っている）。trusted root
  # なら従来どおり素通りだが、untrusted 由来 root は gate 起動根拠にならないので
  # block() の通知へ倒す（AC-13/AC-14）。
  if [[ "$PROJECT_ROOT_UNTRUSTED" == "true" ]]; then
    _mg_block_untrusted_root_unverified "起動根拠: 対象 PR 不一致"
    exit 0
  fi
  _mg_ledger_check_at_exit
  exit 0
fi

# step 6 の入口: HEAD sha を解決する（以降の全証跡検査が必要とする）。
# `--verify -q` を使う（`rev-parse HEAD` 単体はコミット 0 件のリポジトリで解決失敗
# 時に stdout へ literal `HEAD` を吐くため、`-z` による空判定をすり抜けて
# unresolvable な参照がそのまま "sha" として下流の一致比較に流れ込む）。
HEAD_SHA="$(git -C "$PROJECT_ROOT" rev-parse --verify -q HEAD 2>/dev/null || true)"
if [[ -z "$HEAD_SHA" ]]; then
  block "⛔ merge gate（reason code: head-unresolvable）: $(_mg_action head-unresolvable)。${GDD_MG_KILL_SWITCH_HINT}"
  exit 0
fi

# 後続 step で見つかった不足条件をここへ積み、短絡せず全件評価する
# （design.md § 主要フロー 11）。承認判定・証跡検査はこの 2 配列へ
# FAILURES+=("<reason code>") / OBSERVED+=("<観測値・key 名>") を **必ず対で**
# 追加する（design.md § reason code カタログ の「出す観測値」「出す key」列）。
# 対で積む規律は tests/test_merge_gate_hook_contracts.py の
# `test_failures_and_observed_are_appended_in_lockstep` が source 上で固定する。
FAILURES=()
OBSERVED=()

# hooks/scripts/lib/constants.py の同名定数と値を揃える（design.md § 既定値の正本。
# python 側は test_merge_gate_hook_contracts.py が値を固定する。shell 側は既存 gate hook 群と
# 同じく python constants.py を都度 import せず literal で持つ既知の重複 —
# gh_command_parse.py の docstring と同型）。3 値とも観測値の「上限分」として
# block reason に出るため、裸の literal を式中に埋めない。
MERGE_GATE_APPROVAL_FRESHNESS_MINUTES=120
MERGE_GATE_REVIEW_WAIT_MINUTES=40
MERGE_GATE_RECHECK_FRESHNESS_MINUTES=10

# 対象 PR の 3 組解決（design.md § 対象 PR の 3 組解決。旧 条件 3、方式転換後も
# 不変）。state.md の PR URL は `PR URL` 分岐で値ドメインを検査済みの前提。
# ここが `parse_gh_pr_merge` の repo 決定要因（repo_flag / unresolvable /
# env_repo_conflict）の **唯一の消費点**。番号だけで照合すると
# `gh pr merge -R org/repoB 123` が repoA の #123 への承認で通る（design の Why）。
gdd_parse_merge_gate_field "$STEERING_STATE" "PR URL" ""
TARGET_RESOLVE_FAILED="false"
if [[ "$GDD_MG_VALID" != "true" ]]; then
  TARGET_RESOLVE_FAILED="true"
  STEERING_PR_NUMBER=""
  STEERING_OWNER_REPO=""
else
  STEERING_PR_NUMBER="$GDD_MG_PR_NUMBER"
  STEERING_OWNER_REPO="$GDD_MG_PR_OWNER/$GDD_MG_PR_REPO"
fi

# (a) 解決不能な位置引数（ブランチ名）。値そのものは masking policy により使わない。
[[ "$UNRESOLVABLE" == "true" ]] && TARGET_RESOLVE_FAILED="true"
# (b) GH_REPO / GH_HOST（token 列の command-prefix と hook プロセス env の両方）。
[[ "$ENV_REPO_CONFLICT" == "true" ]] && TARGET_RESOLVE_FAILED="true"

CMD_OWNER_REPO=""
if [[ -n "$PR_URL_ARG" ]]; then
  TARGET_PR_NUMBER="${PR_URL_ARG##*/pull/}"
  CMD_OWNER_REPO="$(_mg_owner_repo "${PR_URL_ARG%/pull/*}")"
elif [[ -n "$PR_NUMBER" ]]; then
  TARGET_PR_NUMBER="$PR_NUMBER"
  if [[ -n "$REPO_FLAG" ]]; then
    CMD_OWNER_REPO="$(_mg_owner_repo "$REPO_FLAG")"
    [[ -n "$CMD_OWNER_REPO" ]] || TARGET_RESOLVE_FAILED="true"
  else
    CMD_OWNER_REPO="$(_mg_owner_repo "$(git -C "$PROJECT_ROOT" remote get-url origin 2>/dev/null || true)")"
  fi
else
  # gh pr merge（引数省略）の最頻形。state.md の PR URL の PR を対象とみなす。
  TARGET_PR_NUMBER="$STEERING_PR_NUMBER"
  if [[ -n "$REPO_FLAG" ]]; then
    CMD_OWNER_REPO="$(_mg_owner_repo "$REPO_FLAG")"
    [[ -n "$CMD_OWNER_REPO" ]] || TARGET_RESOLVE_FAILED="true"
  fi
fi

# (c) `gh repo set-default` の結果（remote.origin.gh-resolved）が origin と異なる。
GH_RESOLVED="$(git -C "$PROJECT_ROOT" config --get remote.origin.gh-resolved 2>/dev/null || true)"
if [[ -n "$GH_RESOLVED" && "$GH_RESOLVED" != "base" ]]; then
  ORIGIN_OWNER_REPO="$(_mg_owner_repo "$(git -C "$PROJECT_ROOT" remote get-url origin 2>/dev/null || true)")"
  RESOLVED_OWNER_REPO="$(_mg_owner_repo "$GH_RESOLVED")"
  if [[ -z "$RESOLVED_OWNER_REPO" ]] || ! _mg_equals_ci "$RESOLVED_OWNER_REPO" "$ORIGIN_OWNER_REPO"; then
    TARGET_RESOLVE_FAILED="true"
  fi
fi

# (d) コマンド側で解決した owner/repo と state.md の PR URL の owner/repo の一致。
if [[ -n "$CMD_OWNER_REPO" && -n "$STEERING_OWNER_REPO" ]] && ! _mg_equals_ci "$CMD_OWNER_REPO" "$STEERING_OWNER_REPO"; then
  TARGET_RESOLVE_FAILED="true"
fi

if [[ "$TARGET_RESOLVE_FAILED" == "true" ]]; then
  FAILURES+=("pr-target-unresolvable")
  OBSERVED+=("key: PR URL")
fi

# step 7: 承認判定（design.md § 承認判定の設計・AC-2）。
# 判定材料は state.md + git rev-parse HEAD だけ（会話ログの類は一切読まない）。
gdd_parse_merge_gate_field "$STEERING_STATE" "Merge Approval" ""
if [[ "$GDD_MG_VALID" != "true" ]]; then
  case "$GDD_MG_REASON" in
    missing)     FAILURES+=("approval-missing")
                 OBSERVED+=("key: Merge Approval") ;;
    unparsable)  FAILURES+=("evidence-unparsable")
                 OBSERVED+=("不足 key: Merge Approval") ;;
    *)           FAILURES+=("evidence-malformed")
                 OBSERVED+=("不正 key: Merge Approval") ;;
  esac
else
  # (B) 対象一致: PR 番号（マージ対象 / PR URL 双方）と head sha
  if [[ "$GDD_MG_APPROVAL_PR" != "$TARGET_PR_NUMBER" || "$GDD_MG_APPROVAL_PR" != "$STEERING_PR_NUMBER" ]]; then
    FAILURES+=("approval-pr-mismatch")
    OBSERVED+=("承認宛 PR #${GDD_MG_APPROVAL_PR} / 実行対象 PR #${TARGET_PR_NUMBER:-未解決} / key: Merge Approval, PR URL")
  fi
  APPROVAL_SHA_FULL="$(git -C "$PROJECT_ROOT" rev-parse --quiet --verify "${GDD_MG_SHA}^{commit}" 2>/dev/null || true)"
  if [[ "$APPROVAL_SHA_FULL" != "$HEAD_SHA" ]]; then
    FAILURES+=("approval-sha-mismatch")
    OBSERVED+=("承認 sha ${GDD_MG_SHA:0:7} / HEAD ${HEAD_SHA:0:7} / key: Merge Approval")
  fi
  # (C) 鮮度: approved_at からの経過 <= MERGE_GATE_APPROVAL_FRESHNESS_MINUTES
  if ! gdd_mg_epoch_within_minutes "$GDD_MG_APPROVED_AT_EPOCH" "$MERGE_GATE_APPROVAL_FRESHNESS_MINUTES"; then
    APPROVAL_ELAPSED_SEC="$(_mg_elapsed_seconds "$GDD_MG_APPROVED_AT_EPOCH")"
    [[ "$APPROVAL_ELAPSED_SEC" -ge 0 ]] || APPROVAL_ELAPSED_SEC=0
    FAILURES+=("approval-stale")
    OBSERVED+=("経過 $((APPROVAL_ELAPSED_SEC / 60)) 分 / 上限 ${MERGE_GATE_APPROVAL_FRESHNESS_MINUTES} 分 / key: Merge Approval")
  fi
fi

# step 8-9: 証跡検査（design.md § 主要フロー step 8-9）。短絡せず全件評価する。
# $FAILURES は Step Group A1 が宣言し Step Group A2 の承認判定（step 7）が
# すでに積んでいる共有配列。ここでは再初期化せず追記する。

gdd_parse_merge_gate_field "$STEERING_STATE" "Pre-Merge Review Recheck" ""
if [[ "$GDD_MG_VALID" != "true" ]]; then
  # Merge Approval と同じ3分岐（missing / unparsable / malformed）へ揃える。
  case "$GDD_MG_REASON" in
    missing)     FAILURES+=("recheck-missing")
                 OBSERVED+=("key: Pre-Merge Review Recheck") ;;
    unparsable)  FAILURES+=("evidence-unparsable")
                 OBSERVED+=("不足 key: Pre-Merge Review Recheck") ;;
    *)           FAILURES+=("evidence-malformed")
                 OBSERVED+=("不正 key: Pre-Merge Review Recheck") ;;
  esac
else
  RECHECK_SHA="$GDD_MG_SHA"
  RECHECK_SHA_FULL="$(git -C "$PROJECT_ROOT" rev-parse --quiet --verify "${GDD_MG_SHA}^{commit}" 2>/dev/null || true)"
  if [[ -z "$RECHECK_SHA_FULL" || "$RECHECK_SHA_FULL" != "$HEAD_SHA" ]]; then
    FAILURES+=("recheck-sha-mismatch")
    OBSERVED+=("証跡 sha ${RECHECK_SHA:0:7} / HEAD ${HEAD_SHA:0:7} / key: Pre-Merge Review Recheck")
  fi
  RECHECK_AT_EPOCH="$GDD_MG_AT_EPOCH"
  RECHECK_NEW_BLOCKING="$GDD_MG_NEW_BLOCKING"
  if [[ "$RECHECK_NEW_BLOCKING" != "0" ]]; then
    FAILURES+=("recheck-blocking")
    OBSERVED+=("new_blocking ${RECHECK_NEW_BLOCKING} 件 / key: Pre-Merge Review Recheck")
  fi
  RECHECK_ELAPSED_SEC="$(_mg_elapsed_seconds "$RECHECK_AT_EPOCH")"
  if [[ "$RECHECK_ELAPSED_SEC" -lt 0 || "$RECHECK_ELAPSED_SEC" -gt $((MERGE_GATE_RECHECK_FRESHNESS_MINUTES * 60)) ]]; then
    RECHECK_ELAPSED_MIN=0
    [[ "$RECHECK_ELAPSED_SEC" -lt 0 ]] || RECHECK_ELAPSED_MIN=$((RECHECK_ELAPSED_SEC / 60))
    FAILURES+=("recheck-stale")
    OBSERVED+=("経過 ${RECHECK_ELAPSED_MIN} 分 / 上限 ${MERGE_GATE_RECHECK_FRESHNESS_MINUTES} 分 / key: Pre-Merge Review Recheck")
  fi
fi

# git log 失敗（committer date 取得不能）を先に検出し、空文字を
# gdd_parse_merge_gate_field へ渡して制約検査ごと skip させない。
HEAD_COMMITTER_DATE="$(git -C "$PROJECT_ROOT" log -1 --format=%cI HEAD 2>/dev/null || true)"
if [[ -z "$HEAD_COMMITTER_DATE" ]]; then
  FAILURES+=("review-push-missing")
  OBSERVED+=("key: Last Review Push At")
  LAST_PUSH_AT=""
else
  gdd_parse_merge_gate_field "$STEERING_STATE" "Last Review Push At" "$HEAD_COMMITTER_DATE"
  if [[ "$GDD_MG_VALID" != "true" ]]; then
    # Merge Approval と同じ3分岐（missing / unparsable / malformed）へ揃える。
    case "$GDD_MG_REASON" in
      missing)     FAILURES+=("review-push-missing")
                   OBSERVED+=("key: Last Review Push At") ;;
      unparsable)  FAILURES+=("evidence-unparsable")
                   OBSERVED+=("不足 key: Last Review Push At") ;;
      *)           FAILURES+=("evidence-malformed")
                   OBSERVED+=("不正 key: Last Review Push At") ;;
    esac
    LAST_PUSH_AT=""
  else
    LAST_PUSH_AT="$GDD_MG_AT"
    LAST_PUSH_AT_EPOCH="$GDD_MG_AT_EPOCH"
  fi
fi

gdd_parse_merge_gate_field "$STEERING_STATE" "Bot Review Received" ""
if [[ "$GDD_MG_VALID" != "true" ]]; then
  # Merge Approval と同じ3分岐（missing / unparsable / malformed）へ揃える。
  case "$GDD_MG_REASON" in
    missing)     FAILURES+=("bot-review-flag-missing")
                 OBSERVED+=("key: Bot Review Received") ;;
    unparsable)  FAILURES+=("evidence-unparsable")
                 OBSERVED+=("不足 key: Bot Review Received") ;;
    *)           FAILURES+=("evidence-malformed")
                 OBSERVED+=("不正 key: Bot Review Received") ;;
  esac
else
  BOT_SHA_FULL="$(git -C "$PROJECT_ROOT" rev-parse --quiet --verify "${GDD_MG_SHA}^{commit}" 2>/dev/null || true)"
  if [[ -z "$BOT_SHA_FULL" || "$BOT_SHA_FULL" != "$HEAD_SHA" ]]; then
    FAILURES+=("bot-review-flag-missing")
    OBSERVED+=("証跡 sha ${GDD_MG_SHA:0:7} / HEAD ${HEAD_SHA:0:7} / key: Bot Review Received")
  elif [[ "$GDD_MG_RECEIVED" == "no" && -n "$LAST_PUSH_AT" ]]; then
    PUSH_ELAPSED_SEC="$(_mg_elapsed_seconds "$LAST_PUSH_AT_EPOCH")"
    WAIT_ELAPSED="true"
    if [[ "$PUSH_ELAPSED_SEC" -lt 0 || "$PUSH_ELAPSED_SEC" -lt $((MERGE_GATE_REVIEW_WAIT_MINUTES * 60)) ]]; then
      WAIT_ELAPSED="false"
    fi
    # 待機の目的は「bot レビューが着弾する時間を与える」ことなので、独立レビューが
    # HEAD で high 0 / blocking 0 なら待つ意味がない（待機経過後に要求されるのは
    # 同じ Independent Review）。bot が恒久的に来ない repo（予算切れ等）で push の
    # たびに空待ちが発生するのを避けるため、この条件のときだけ待機を免除する。
    # Independent Review の parse は 1 回だけ行う（免除判定と本検査で共用する。
    # 2 回 parse すると legacy-no-blocking-field の監査記録が二重に出る）。
    gdd_parse_merge_gate_field "$STEERING_STATE" "Independent Review" ""
    IR_VALID="$GDD_MG_VALID"
    IR_REASON="$GDD_MG_REASON"
    IR_SHA_FULL=""
    [[ "$IR_VALID" != "true" ]] ||
      IR_SHA_FULL="$(git -C "$PROJECT_ROOT" rev-parse --quiet --verify "${GDD_MG_SHA}^{commit}" 2>/dev/null || true)"
    IR_CLEAN="false"; GDD_IR_CARRY_REASON=""; CARRY_NOTE=""
    if [[ "$IR_VALID" == "true" && -n "$IR_SHA_FULL" && "$IR_SHA_FULL" == "$HEAD_SHA" \
          && "$GDD_MG_HIGH" == "0" && "$GDD_MG_BLOCKING" == "0" ]]; then
      IR_CLEAN="true"
    elif [[ "$IR_VALID" == "true" && -n "$IR_SHA_FULL" && "$GDD_MG_HIGH" == "0" && "$GDD_MG_BLOCKING" == "0" ]] \
          && gdd_ir_carry_matches "$PROJECT_ROOT" "$STEERING_STATE" "$IR_SHA_FULL" "$HEAD_SHA"; then
      IR_CLEAN="true"  # 旧 sha の独立レビューを引き継ぐ（正本: references/self-review-lanes.md § Independent Review の引き継ぎ）
    elif [[ -n "$GDD_IR_CARRY_REASON" ]]; then  # 引き継ぎを試せた場面だけ
      CARRY_NOTE=" / Independent Review Carry: 引き継げない理由 ${GDD_IR_CARRY_REASON}（既定ブランチを取り込むだけのマージコミットなら Independent Review Carry 行で引き継げる。正本: references/self-review-lanes.md § Independent Review の引き継ぎ）"
    fi
    if [[ "$WAIT_ELAPSED" != "true" && "$IR_CLEAN" != "true" ]]; then
      PUSH_ELAPSED_MIN=0
      [[ "$PUSH_ELAPSED_SEC" -lt 0 ]] || PUSH_ELAPSED_MIN=$((PUSH_ELAPSED_SEC / 60))
      FAILURES+=("review-wait-not-elapsed")
      OBSERVED+=("経過 ${PUSH_ELAPSED_MIN} 分 / 待機上限 ${MERGE_GATE_REVIEW_WAIT_MINUTES} 分 / 残り $((MERGE_GATE_REVIEW_WAIT_MINUTES - PUSH_ELAPSED_MIN)) 分 / 独立レビューが HEAD で high 0 なら待機は不要${CARRY_NOTE} / key: Last Review Push At, Bot Review Received")
    elif [[ "$IR_VALID" != "true" ]]; then
      # Merge Approval と同じ3分岐（missing / unparsable / malformed）へ揃える。
      case "$IR_REASON" in
        missing)     FAILURES+=("independent-review-missing")
                     OBSERVED+=("key: Independent Review") ;;
        unparsable)  FAILURES+=("evidence-unparsable")
                     OBSERVED+=("不足 key: Independent Review") ;;
        *)           FAILURES+=("evidence-malformed")
                     OBSERVED+=("不正 key: Independent Review") ;;
      esac
    else
      # 旧書式（`blocking` key 欠落）を寛容側の既定で通した場合の監査記録（design.md § D5 /
      # references/self-review-lanes.md § 旧書式（`blocking` 欠落）の既定挙動 が唯一の可視化と明記。best-effort、gate 判定は
      # 変えない）。後続の Medium Disposition parse で GDD_MG_REASON が上書きされるため先に記録する。
      # subshell + `|| true` で隔離する: `_mg_log_suppressed` は `HOME` 未設定なら
      # `${HOME:-}` で読んで 0 を返すが、`shasum`/`sha1sum` 双方の不在・失敗（`pipefail`）で
      # シェルごと即死しうる。ここは記録後に証跡検査へ**進む**位置なので、
      # 即死すると hook が無出力で終わり、通知を返さないまま素通りになる
      # （不足の通知の消失）。
      if [[ "$IR_REASON" == "legacy-no-blocking-field" ]]; then
        ( _mg_log_suppressed "legacy-evidence-no-blocking-field" ) 2>/dev/null || true
      fi
      if [[ "$IR_CLEAN" != "true" ]]; then
        FAILURES+=("independent-review-missing")
        OBSERVED+=("high ${GDD_MG_HIGH} 件 / blocking ${GDD_MG_BLOCKING} 件 / medium ${GDD_MG_MEDIUM} 件${CARRY_NOTE} / key: Independent Review")
      else
        IR_MEDIUM_SAVED="$GDD_MG_MEDIUM"
        if [[ "$IR_MEDIUM_SAVED" != "0" ]]; then
          gdd_parse_merge_gate_field "$STEERING_STATE" "Medium Disposition" ""
          if [[ "$GDD_MG_VALID" != "true" ]]; then
            # Merge Approval と同じ3分岐（missing / unparsable / malformed）へ揃える。
            case "$GDD_MG_REASON" in
              missing)     FAILURES+=("medium-disposition-missing")
                           OBSERVED+=("medium ${IR_MEDIUM_SAVED} 件 / key: Medium Disposition") ;;
              unparsable)  FAILURES+=("evidence-unparsable")
                           OBSERVED+=("不足 key: Medium Disposition") ;;
              *)           FAILURES+=("evidence-malformed")
                           OBSERVED+=("不正 key: Medium Disposition") ;;
            esac
          else
            DISP_SHA_FULL="$(git -C "$PROJECT_ROOT" rev-parse --quiet --verify "${GDD_MG_SHA}^{commit}" 2>/dev/null || true)"
            if [[ -z "$DISP_SHA_FULL" || "$DISP_SHA_FULL" != "$HEAD_SHA" || "$GDD_MG_DISPOSITION_COUNT" != "$IR_MEDIUM_SAVED" ]]; then
              FAILURES+=("medium-disposition-missing")
              OBSERVED+=("medium ${IR_MEDIUM_SAVED} 件 / key: Medium Disposition")
            fi
          fi
        fi
      fi
    fi
  fi
fi

# step 10-11: 短絡しない。不足を全件列挙して 1 回の block reason にまとめる。
# 全条件成立なら allow。hook は何も書かない（one-shot 消費ログは方式転換で
# 廃止。書き込み失敗という失敗モードが allow 経路に存在しない）。
if [[ "${#FAILURES[@]}" -gt 0 ]]; then
  CODES="$(printf '%s, ' "${FAILURES[@]}")"
  CODES="${CODES%, }"
  # 語順: <命令形の次の 1 アクション>。<観測値>。<復旧要素>
  # （design.md § Delivery Channel Rendering Check）。アクションは先頭 code の
  # ものを使い、観測値は全 failure 分を code 付きで列挙する（code 15 と 16 の
  # ように「不足 key」「不正 key」で次の手が違うものが同一文面へ潰れないように）。
  OBS_TEXT=""
  for _i in "${!FAILURES[@]}"; do
    [[ -n "${OBSERVED[$_i]}" ]] || continue
    OBS_TEXT="${OBS_TEXT}${FAILURES[$_i]} → ${OBSERVED[$_i]}。"
  done
  ADMIN_NOTE=""
  if [[ "$IS_ADMIN" == "true" ]]; then
    # design.md § コマンド検出の設計:「--admin は保護ルールを迂回する」旨を 1 文。
    ADMIN_NOTE='--admin は branch protection を迂回するため、解除条件を満たさないままの実行は特に危険です。'
  fi
  block "⛔ merge gate（reason code: ${FAILURES[0]}）: $(_mg_action "${FAILURES[0]}")。不足条件: ${CODES}。${OBS_TEXT}${ADMIN_NOTE}${GDD_MG_RECOVERY_CORE}"
  exit 0
fi
exit 0
