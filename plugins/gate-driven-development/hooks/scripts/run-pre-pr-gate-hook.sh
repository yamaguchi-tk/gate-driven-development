#!/usr/bin/env bash
set -euo pipefail

# PreToolUse hook: active GDD 中の `gh pr create` を completion-check の
# runtime backstop にする。Bash 全体に挟まるので、非該当 command は最優先で即通過。
# 不足を見つけても止めずに通し、実行後の通知と would-block の記録に残す（下の `block()`）。

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/kill-switch.sh"
gdd_kill_switch_active && exit 0
# shellcheck source=lib/detect-steering.sh
source "$SCRIPT_DIR/lib/detect-steering.sh"
# shellcheck source=lib/self-review-evidence.sh
source "$SCRIPT_DIR/lib/self-review-evidence.sh"
# shellcheck source=lib/gdd-pr-roots.sh
source "$SCRIPT_DIR/lib/gdd-pr-roots.sh"
# shellcheck source=lib/gate-ledger.sh
source "$SCRIPT_DIR/lib/gate-ledger.sh"
# shellcheck source=lib/gate-notice.sh
source "$SCRIPT_DIR/lib/gate-notice.sh"

PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(cd "$SCRIPT_DIR/../.." && pwd)}"

# 止めずに通す。不足は実行後の通知と would-block:<code> の記録に残す（lib/gate-notice.sh）。
# 呼び出しは `block <code> <本文>`。code は本文から切り出さずに宣言して渡す。
# pre-PR gate は PR 1 本につき 1 回しか走らないので、最初の不足で終えずに集め、終わるときに
# 1 本の通知と 1 行の記録（code はカンマでつなぐ。merge gate と同じ形）にまとめる。
# 出すのは EXIT の trap なので、後段のコマンドが set -e で落ちても、集めた不足は消えない。
_PPR_CODES=()
_PPR_TEXTS=()
block() {
  _PPR_CODES+=("$1")
  _PPR_TEXTS+=("$2")
}
_ppr_flush() {
  [[ ${#_PPR_CODES[@]} -gt 0 ]] || return 0
  local _codes _text
  _codes="$(IFS=,; printf '%s' "${_PPR_CODES[*]}")"
  _text="$(printf '%s\n' "${_PPR_TEXTS[@]}")"
  _PPR_CODES=()
  gdd_gate_notice "pre-pr-gate-suppressed.log" "$_codes" "実行後の通知: pre-PR gate は止めずに通した。PR が作成された場合は、次の不足を直してから PR の差分と本文を更新してください。作成が失敗した場合は、次の不足を直してから再実行してください。${_text}"
  exit 0
}
trap _ppr_flush EXIT

resolve_base_ref() {
  gdd_resolve_base_ref "$PROJECT_ROOT" "$BASE_BRANCH"
}

PAYLOAD="$(cat 2>/dev/null || true)"
# 前段は payload 全体（command のほか cwd・description なども含む）の部分文字列 1 つで絞る
# （merge gate と同じ）。2 語の並びで絞ると、空白 2 つ・タブ・引用符・行継続をはさんだ
# `gh pr create` が python の判定まで届かない。部分文字列なので renew・created にも当たり、
# cwd に new・create を含む worktree では Bash の呼び出しごとに python が走る。
case "$PAYLOAD" in
  *create*|*new*|*pulls*) ;;
  *) exit 0 ;;
esac
# 解析の結果は、1 回の python3 が 1 行 1 レコードの `<key>\t<value>` で出す（merge gate・
# pre-push gate と同じ形）。値ごとに python3 を起こさない。cwd の展開と本文の機密検査も
# 同じ python3 の中で行い、本文は bash に渡さない。`parsed` は最後に出す。途中で終わって
# 届かなければ PARSED は false のまま（通知する側）になる。
IS_PR_CREATE="false"
PARSED="false"
HOOK_CWD=""
PAYLOAD_CWD=""
COMMAND_CWD=""
BASE_BRANCH=""
HEAD_BRANCH=""
STDIN_BODY_FILE="false"
SHELL_EXPANDED_BODY="false"
HAS_INSPECTABLE_BODY="false"
BODY_FINDINGS=""
PARSE_OUTPUT="$(printf '%s' "$PAYLOAD" | python3 -c '
import json
import os
import re
import sys

def emit(key, value):
    # 値の中のタブ・改行は空白にする（1 行 1 レコードを崩さない）。符号化は pre-push gate と同じで、
    # UTF-8 に符号化できない lone surrogate は文字化けさせて出す（例外で全体を落とさない）。
    value = str(value).replace("\t", " ").replace("\n", " ").replace("\r", " ")
    line = "%s\t%s\n" % (key, value)
    try:
        data = line.encode("utf-8", "surrogateescape")
    except UnicodeEncodeError:
        data = line.encode("utf-8", "backslashreplace")
    sys.stdout.buffer.write(data)

def not_pr_create():
    emit("is_pr_create", "false")
    emit("parsed", "true")
    raise SystemExit

def expand_path(value):
    # `~`・`$HOME` を展開する。展開で例外になるものは、そのままにする。
    try:
        return os.path.expanduser(os.path.expandvars(value))
    except Exception:
        return value

sys.path.insert(0, sys.argv[1])
import gh_command_parse as gcp

try:
    payload = json.load(sys.stdin)
except Exception:
    not_pr_create()

tool_input = payload.get("tool_input", {})
if not isinstance(tool_input, dict):
    not_pr_create()

command = tool_input.get("command") or tool_input.get("cmd") or ""
if not isinstance(command, str):
    not_pr_create()
payload_cwd = tool_input.get("cwd") or tool_input.get("workdir") or ""
if not isinstance(payload_cwd, str):
    payload_cwd = ""

# Claude Code は cwd を payload の最上位に持つ（lib/hook_cwd.py）。使えるなら、相対パスの
# 本文ファイルもそこから読むよう、この python の cwd を移す。移れたときだけ bash に返す。
hook_cwd_value = ""
try:
    import hook_cwd
    top_cwd = hook_cwd.toplevel_cwd(payload)
    if top_cwd:
        os.chdir(top_cwd)
        hook_cwd_value = top_cwd
except Exception:
    hook_cwd_value = ""

# 字句解析（heredoc 本文の除去・行継続・語頭のコメント・演算子の切り出し・fd 番号の
# 除去）と、gh の sub-command の探し方は、merge gate と同じ lib/gh_command_parse.py の関数を
# 使う（写しを持たない。Issue #246）。引数の読みの区切り（is_separator）は前と同じ語の集合の
# まま。入れ子の本体（bash -c・eval の中身）も同じ関数で割る。lib を import できない・解析が
# 例外で終わるときは、この python が 0 以外で終わり、hook は下の PARSED で扱う。
# **この埋め込み python は単一引用符を 1 つも含めてはならない**（全体が `python3 -c` の
# 単一引用符付き文字列の中にある）。

def strip_heredoc_bodies(text):
    return gcp._strip_heredoc_bodies(text)

def lex(text):
    return gcp._tokenize(text)

tokens = lex(strip_heredoc_bodies(command))

def is_separator(token):
    return token in {"&&", "&", ";", "||", "|"}

def has_shell_expansion(value):
    if value == "$":
        return True
    return bool(
        re.search(r"(?<!\\)(?:\$\(|`|\$\{|\$[A-Za-z_][A-Za-z0-9_]*)", value)
    )

def is_stdin_body_path(path):
    return (
        path == "-"
        or path == "/dev/stdin"
        or path.startswith("/dev/fd/")
        or path.startswith("/proc/self/fd/")
    )

def expand_nested_shell_tokens(source_tokens):
    expanded = list(source_tokens)
    for index, token in enumerate(source_tokens):
        if os.path.basename(token) == "eval" and index + 1 < len(source_tokens):
            # eval は後ろの語を空白でつないで実行する（区切りの手前まで）。
            end = index + 1
            while end < len(source_tokens) and not is_separator(source_tokens[end]):
                end += 1
            expanded.extend(lex(" ".join(source_tokens[index + 1:end])))
            continue
        if os.path.basename(token) not in {"bash", "sh", "zsh"}:
            continue
        cursor = index + 1
        while cursor < len(source_tokens):
            flag = source_tokens[cursor]
            if flag == "-c" or (flag.startswith("-") and "c" in flag[1:]):
                if cursor + 1 < len(source_tokens):
                    expanded.extend(lex(source_tokens[cursor + 1]))
                break
            cursor += 1
    return expanded

def resolve_body_path(path, command_cwd, payload_cwd):
    path = os.path.expanduser(os.path.expandvars(path))
    base_cwd = os.path.expanduser(os.path.expandvars(command_cwd or payload_cwd))
    if os.path.isabs(path) or not base_cwd:
        return path
    if not os.path.isabs(base_cwd):
        base_cwd = os.path.join(os.getcwd(), base_cwd)
    return os.path.join(base_cwd, path)

def combine_cd(current_cwd, target):
    if (
        not current_cwd
        or os.path.isabs(target)
        or target.startswith("~")
        or "$" in target
    ):
        return target
    return os.path.normpath(os.path.join(current_cwd, target))

tokens = expand_nested_shell_tokens(tokens)
def argv_words(words):
    """リダイレクトとそのオペランドを除く（argv に入らない）。"""
    kept = []
    cursor = 0
    while cursor < len(words):
        if gcp._is_redirect_operator(words[cursor]):
            cursor += 2
            continue
        kept.append(words[cursor])
        cursor += 1
    return kept

def is_pulls_post(args):
    method = ""
    has_post_field = False
    pulls_endpoint = False
    cursor = 0
    while cursor < len(args):
        token = args[cursor]
        if is_separator(token):
            break
        if token in {"--method", "-X"} and cursor + 1 < len(args):
            method = args[cursor + 1].upper()
            cursor += 2
            continue
        if token.startswith("--method="):
            method = token.split("=", 1)[1].upper()
            cursor += 1
            continue
        if token in {"--field", "-f", "--raw-field", "-F"} and cursor + 1 < len(args):
            has_post_field = True
            cursor += 2
            continue
        if token.startswith(("--field=", "--raw-field=", "-f", "-F")):
            has_post_field = True
            cursor += 1
            continue
        normalized = token.strip("\"")
        # PR 作成の endpoint は `POST /repos/<owner>/<repo>/pulls` **ちょうど**。
        # 部分一致（`"/pulls" in normalized`）で判定すると
        # `/pulls/<n>/requested_reviewers` `/pulls/<n>/comments` `/pulls/<n>/reviews`
        # `/pulls/<n>/merge` への POST まで「PR 作成」に化け、いずれも body を
        # 持たないため「PR body を検査できません」で原理的に通せなくなる。
        # `gdd-pr-review-followup` が規定する Copilot レビュー依頼とインライン返信が
        # まさにこの形で、**本 plugin の規定する運用が自分の gate に塞がれていた**。
        # query string と末尾スラッシュを落としたうえで末尾一致だけを見る。
        endpoint = normalized.split("?", 1)[0].rstrip("/")
        if endpoint.endswith("/pulls") or endpoint == "pulls":
            pulls_endpoint = True
        cursor += 1
    return pulls_endpoint and method != "GET" and (method == "POST" or has_post_field)

# gh の simple command ごとに、gh と同じ規則（リダイレクト・flag を読み飛ばす）で sub-command を
# 探す（merge gate の _find_sub_command）。引数は、見つけた sub-command の語とリダイレクトを除いた列。
command_index = None
command_kind = ""
args = []
for index, token in enumerate(tokens):
    if os.path.basename(token) != "gh":
        continue
    end = index + 1
    while end < len(tokens) and not gcp._is_control_operator(tokens[end]):
        end += 1
    segment = tokens[:end]
    pr_index = gcp._find_sub_command(segment, index + 1, "pr", {})
    if pr_index is not None:
        for name in ("create", "new"):
            sub_index = gcp._find_sub_command(segment, pr_index + 1, name, {})
            if sub_index is not None:
                command_index, command_kind = index, "pr"
                args = argv_words(tokens[index + 1:pr_index] + tokens[pr_index + 1:sub_index] + tokens[sub_index + 1:end])
                break
    else:
        api_index = gcp._find_sub_command(segment, index + 1, "api", {})
        if api_index is not None:
            api_args = argv_words(tokens[index + 1:api_index] + tokens[api_index + 1:end])
            if is_pulls_post(api_args):
                command_index, command_kind, args = index, "api_pulls", api_args
    if command_index is not None:
        break

is_pr_create = command_index is not None
body_parts = []
base_branch = ""
head_branch = ""
command_cwd = ""
stdin_body_file = False
has_inspectable_body = False
shell_expanded_body = False
if is_pr_create:
    prefix_cursor = 0
    while prefix_cursor < command_index:
        token = tokens[prefix_cursor]
        if token in {"&&", ";"}:
            prefix_cursor += 1
            continue
        if token == "cd" and prefix_cursor + 1 < command_index:
            command_cwd = combine_cd(command_cwd, tokens[prefix_cursor + 1])
            prefix_cursor += 2
            continue
        prefix_cursor += 1

    cursor = 0
    while cursor < len(args):
        token = args[cursor]
        if is_separator(token):
            break
        if command_kind == "api_pulls":
            field_value = ""
            if token in {"--field", "-f", "--raw-field", "-F"} and cursor + 1 < len(args):
                field_value = args[cursor + 1]
                cursor += 2
            elif token.startswith("--field=") or token.startswith("--raw-field="):
                field_value = token.split("=", 1)[1]
                cursor += 1
            elif token.startswith("-f") or token.startswith("-F"):
                field_value = token[2:]
                cursor += 1
            else:
                cursor += 1
            if field_value:
                key, _, value = field_value.partition("=")
                if key == "base":
                    base_branch = value
                elif key == "head":
                    head_branch = value
                elif key == "body":
                    body_parts.append(value)
                    has_inspectable_body = True
                    if has_shell_expansion(value):
                        shell_expanded_body = True
            continue
        if token in {"--base", "-B"} and cursor + 1 < len(args):
            base_branch = args[cursor + 1]
            cursor += 2
            continue
        if token.startswith("--base="):
            base_branch = token.split("=", 1)[1]
            cursor += 1
            continue
        if token in {"--head", "-H"} and cursor + 1 < len(args):
            head_branch = args[cursor + 1]
            cursor += 2
            continue
        if token.startswith("--head="):
            head_branch = token.split("=", 1)[1]
            cursor += 1
            continue
        if token in {"--template", "-T"} and cursor + 1 < len(args):
            try:
                with open(resolve_body_path(args[cursor + 1], command_cwd, payload_cwd), "r", encoding="utf-8", errors="ignore") as handle:
                    body_parts.append(handle.read())
                has_inspectable_body = True
            except OSError:
                body_parts.append("")
            cursor += 2
            continue
        if token.startswith("--template="):
            template_path = token.split("=", 1)[1]
            try:
                with open(resolve_body_path(template_path, command_cwd, payload_cwd), "r", encoding="utf-8", errors="ignore") as handle:
                    body_parts.append(handle.read())
                has_inspectable_body = True
            except OSError:
                body_parts.append("")
            cursor += 1
            continue
        if token in {"--body", "-b"} and cursor + 1 < len(args):
            body_parts.append(args[cursor + 1])
            has_inspectable_body = True
            if has_shell_expansion(args[cursor + 1]):
                shell_expanded_body = True
            cursor += 2
            continue
        if token.startswith("--body="):
            body_value = token.split("=", 1)[1]
            body_parts.append(body_value)
            has_inspectable_body = True
            if has_shell_expansion(body_value):
                shell_expanded_body = True
            cursor += 1
            continue
        if token in {"--body-file", "-F"} and cursor + 1 < len(args):
            if is_stdin_body_path(args[cursor + 1]):
                stdin_body_file = True
            else:
                try:
                    with open(resolve_body_path(args[cursor + 1], command_cwd, payload_cwd), "r", encoding="utf-8", errors="ignore") as handle:
                        body_parts.append(handle.read())
                    has_inspectable_body = True
                except OSError:
                    body_parts.append("")
            cursor += 2
            continue
        if token.startswith("--body-file="):
            body_path = token.split("=", 1)[1]
            if is_stdin_body_path(body_path):
                stdin_body_file = True
            else:
                try:
                    with open(resolve_body_path(body_path, command_cwd, payload_cwd), "r", encoding="utf-8", errors="ignore") as handle:
                        body_parts.append(handle.read())
                    has_inspectable_body = True
                except OSError:
                    body_parts.append("")
            cursor += 1
            continue
        cursor += 1

if not is_pr_create:
    not_pr_create()

# 本文の機密検査。NUL は除いてから見る（本文を bash に渡していたときは、bash が NUL を
# 落としてから検査していた。NUL をはさんだ数字の並びも同じく見つける）。
body = "\n".join(body_parts).replace("\x00", "")
findings = []
if re.search(r"\b[0-9]{12}\b", body):
    findings.append("12桁数字")
if re.search(r"-----BEGIN [A-Z ]*(?:PRIVATE )?KEY-----", body):
    findings.append("秘密鍵ヘッダ")
if re.search(r"(?i)\b(?:access[_-]?token|auth[_-]?token|refresh[_-]?token|id[_-]?token|token|api[_-]?key|access[_-]?key|secret[_-]?key|private[_-]?key|key|password|secret|credentials?)\b\s*[:=]", body):
    findings.append("token/key/password")

emit("is_pr_create", "true")
emit("hook_cwd", hook_cwd_value)
emit("payload_cwd", expand_path(payload_cwd))
emit("command_cwd", expand_path(command_cwd))
emit("base_branch", base_branch)
emit("head_branch", head_branch)
emit("stdin_body_file", "true" if stdin_body_file else "false")
emit("shell_expanded_body", "true" if shell_expanded_body else "false")
emit("has_inspectable_body", "true" if has_inspectable_body else "false")
emit("body_findings", ", ".join(findings))
emit("parsed", "true")
' "$SCRIPT_DIR/lib")" || PARSE_OUTPUT="$(printf '%s' "$PAYLOAD" | python3 -c '
import json
import os
import sys

# 上の python が 0 以外で終わった（lib/gh_command_parse.py を import できない・名前が変わった・
# 解析が例外で落ちた）。PR 作成かは分からないので、active GDD の判定に使う cwd だけを
# gh_command_parse を使わずに取り出す。parsed は出さない。
def emit(key, value):
    value = str(value).replace("\t", " ").replace("\n", " ").replace("\r", " ")
    line = "%s\t%s\n" % (key, value)
    try:
        data = line.encode("utf-8", "surrogateescape")
    except UnicodeEncodeError:
        data = line.encode("utf-8", "backslashreplace")
    sys.stdout.buffer.write(data)

sys.path.insert(0, sys.argv[1])
try:
    payload = json.load(sys.stdin)
    tool_input = payload.get("tool_input", {})
    payload_cwd = tool_input.get("cwd") or tool_input.get("workdir") or ""
    if isinstance(payload_cwd, str):
        try:
            payload_cwd = os.path.expanduser(os.path.expandvars(payload_cwd))
        except Exception:
            pass
        emit("payload_cwd", payload_cwd)
    import hook_cwd
    emit("hook_cwd", hook_cwd.toplevel_cwd(payload) or "")
except Exception:
    pass
' "$SCRIPT_DIR/lib" 2>/dev/null)" || PARSE_OUTPUT=""
# 行はリダイレクトを使わずに回す（here-string は一時ファイルで作られることがあり、作れないと
# ループを飛ばす）。配列は使わない（空の配列は bash 4.4 未満の set -u で hook を落とす）。
set -f
_ifs="$IFS"
IFS=$'\n'
for _l in $PARSE_OUTPUT; do
  _k="${_l%%$'\t'*}"
  _v="${_l#*$'\t'}"
  case "$_k" in
    is_pr_create) IS_PR_CREATE="$_v" ;;
    parsed) PARSED="$_v" ;;
    hook_cwd) HOOK_CWD="$_v" ;;
    payload_cwd) PAYLOAD_CWD="$_v" ;;
    command_cwd) COMMAND_CWD="$_v" ;;
    base_branch) BASE_BRANCH="$_v" ;;
    head_branch) HEAD_BRANCH="$_v" ;;
    stdin_body_file) STDIN_BODY_FILE="$_v" ;;
    shell_expanded_body) SHELL_EXPANDED_BODY="$_v" ;;
    has_inspectable_body) HAS_INSPECTABLE_BODY="$_v" ;;
    body_findings) BODY_FINDINGS="$_v" ;;
  esac
done
IFS="$_ifs"
set +f
# 解析に失敗したときは、merge gate と同じく active GDD の中なら不足として通知し、外なら
# 何もせず通す（下の STATE_FILE の判定の後で通知する）。
[[ "$PARSED" == "true" ]] || PARSED="false"
[[ "$IS_PR_CREATE" == "true" || "$PARSED" == "false" ]] || exit 0

# 最上位の cwd が使えたら（lib/hook_cwd.py）、プロセスの cwd をそこへ移す。移れないときは、
# 今までどおりプロセスの cwd に残る。
if [[ -n "$HOOK_CWD" ]]; then
  cd "$HOOK_CWD" 2>/dev/null || true
fi
PROJECT_ROOT="$(pwd)"
if [[ -n "$PAYLOAD_CWD" ]]; then
  if [[ "$PAYLOAD_CWD" == /* && -d "$PAYLOAD_CWD" ]]; then
    PROJECT_ROOT="$(cd "$PAYLOAD_CWD" && pwd)"
  elif [[ -d "$PROJECT_ROOT/$PAYLOAD_CWD" ]]; then
    PROJECT_ROOT="$(cd "$PROJECT_ROOT/$PAYLOAD_CWD" && pwd)"
  fi
fi
if [[ -n "$COMMAND_CWD" && "$COMMAND_CWD" != "-" ]]; then
  if [[ "$COMMAND_CWD" == /* ]]; then
    if [[ -d "$COMMAND_CWD" ]]; then
      PROJECT_ROOT="$(cd "$COMMAND_CWD" && pwd)"
    fi
  elif [[ "$COMMAND_CWD" != "~"* && -d "$PROJECT_ROOT/$COMMAND_CWD" ]]; then
    PROJECT_ROOT="$(cd "$PROJECT_ROOT/$COMMAND_CWD" && pwd)"
  fi
fi
if command -v git >/dev/null 2>&1; then
  if GIT_ROOT="$(git -C "$PROJECT_ROOT" rev-parse --show-toplevel 2>/dev/null)"; then
    PROJECT_ROOT="$GIT_ROOT"
  fi
fi
cd "$PROJECT_ROOT" 2>/dev/null || true

# 無条件 raw steering チェック: active GDD marker の有無に関わらず実行
# worktree では .claude/gdd-dev.local.md が gitignore されて伝播しないため、
# gate (A)(B) の前に置かないと worktree から raw steering が素通りする
_UC_BASE_REF=""
[[ "$PARSED" == "false" ]] || _UC_BASE_REF="$(resolve_base_ref)"
if [[ -n "$_UC_BASE_REF" ]]; then
  if ! _UC_RAW_OUTPUT="$(python3 "$PLUGIN_ROOT/scripts/check-no-raw-task-steering.py" \
      --root "$PROJECT_ROOT" --against "$_UC_BASE_REF" 2>&1)"; then
    block raw-steering-in-diff "⛔ gh pr create の不足を見つけました。raw task .steering が PR diff に含まれています。completion-check の Distill to ADR を通し、PR から raw steering を除外してください。Next Action=done / 不足ガード=raw task .steering\n${_UC_RAW_OUTPUT}"
  fi
fi
# _UC_BASE_REF が空（解決不能）のときは fail-open: ここでは何もせず通過

STATE_FILE="${PROJECT_ROOT}/.claude/gdd-dev.local.md"
if [[ ! -f "$STATE_FILE" ]]; then
  exit 0
fi
if ! grep -q '^active: true' "$STATE_FILE" 2>/dev/null; then
  exit 0
fi
if ! gdd_session_continuity_ok "$STATE_FILE"; then
  exit 0
fi
if [[ "$PARSED" == "false" ]]; then
  # shellcheck source=lib/merge-gate-evidence.sh
  source "$SCRIPT_DIR/lib/merge-gate-evidence.sh" 2>/dev/null || true
  block command-parse-error "⛔ active GDD: create・new・pulls を含む Bash の呼び出し（コマンド・cwd・説明などのどれか）を検査しました。pre-PR gate が使う lib/gh_command_parse.py を読めない（または解析が例外で終わった）ため、PR 作成かどうかを判定できません。plugin のファイルが壊れていないかを確認してください。${GDD_MG_KILL_SWITCH_HINT:-}。Next Action=unknown / 不足ガード=command parse"
  exit 0
fi
# GDD の PR 台帳へ root を登録する（merge gate が marker の無い場所からの merge を
# PR 単位で照合するため。best-effort で、この後の判定を変えない）。
( gdd_pr_roots_register "$PROJECT_ROOT" ) 2>/dev/null || true

# PR 本文の検査は steering に依らないので、steering を解決する前に行う（解決できない・
# completion-check の前でも、機密候補を通知に載せる）。
if [[ "$STDIN_BODY_FILE" == "true" ]]; then
  block body-stdin "⛔ active GDD: gh pr create の不足を見つけました。--body-file - の stdin PR body はhookから内容を検査できません。PR bodyを一時ファイルまたは --body で渡し、機密チェックを通してください。不足ガード=PR body confidentiality"
elif [[ "$SHELL_EXPANDED_BODY" == "true" ]]; then
  block body-shell-expansion "⛔ active GDD: gh pr create の不足を見つけました。shell expansion を含む PR body はhookから展開後の内容を検査できません。読み取り可能な --body-file を使い、機密チェックを通してください。不足ガード=PR body confidentiality"
elif [[ "$HAS_INSPECTABLE_BODY" != "true" ]]; then
  block body-unreadable "⛔ active GDD: gh pr create の不足を見つけました。PR body をhookで検査できません。--body または読み取り可能な --body-file を使い、機密チェックを通してください。不足ガード=PR body confidentiality"
elif [[ -n "$BODY_FINDINGS" ]]; then
  block body-secret-candidate "⛔ active GDD: gh pr create の不足を見つけました。PR body に機密候補があります (${BODY_FINDINGS})。PR が作成されていれば、本文はもう GitHub に出ています。ただちにユーザーに報告し、本文をマスクまたは抽象化してください（編集しても GitHub の編集履歴に残ります）。不足ガード=PR body confidentiality"
fi

# binding が終端（done・cancelled・stale な brainstorming、Next Action: done を含む）の steering を
# 指しても、pre-push・merge gate と同じく作業中の steering を数え直す（数えないと、別の done の
# steering で completion-check を判定して、作業中の steering を検査せずに PR を作らせる）。
if ! gdd_detect_active_steering --recount-terminal-binding; then
  # 作業中が 2 件以上（primary の multiple）でも、done が 2 件以上（completed の multiple）でも、
  # completion-check をやり直しては解けないので、使わない steering を cancelled にする手順を案内する。
  if [[ "$GDD_STEERING_STATUS" == "multiple" ]] || ! gdd_detect_completed_steering_for_pr; then
    if [[ "$GDD_STEERING_STATUS" == "multiple" ]]; then
      block steering-multiple "⛔ active GDD: gh pr create の不足を見つけました。steering が複数あり state.md / tasklist.md を一意に解決できません。どれを終えるかユーザーに確認したうえで、使わない steering（PR が open のものは除く）は、削除も移動もせず、state.md の Resume From と Next Action をどちらも cancelled にしてから PR を作成してください（手順: references/self-review-lanes.md § 使わないステアリングの終え方）。Next Action=unknown / 不足ガード=active steering resolution"
    else
      block steering-unresolved "⛔ active GDD: gh pr create の不足を見つけました。state.md / tasklist.md を一意に解決できません。completion-check を通してからPRを作成してください。Next Action=unknown / 不足ガード=active steering resolution"
    fi
    exit 0
  fi
fi

if ! gdd_session_continuity_ok "${GDD_STEERING_WT}/.claude/gdd-dev.local.md"; then
  exit 0
fi
( gdd_pr_roots_register "$GDD_STEERING_WT" ) 2>/dev/null || true

# 読めない state.md・tasklist.md を awk に渡すと、set -e で hook が無出力のまま終わる。
# 読む前に確かめて、理由つきで不足として通知する（数え直しは読めない state.md も作業中に数える）。
for _pp_doc in "$GDD_STEERING_DIR/state.md" "$GDD_STEERING_DIR/tasklist.md"; do
  if [[ -e "$_pp_doc" && ! -r "$_pp_doc" ]]; then
    block steering-unreadable "⛔ active GDD: gh pr create の不足を見つけました。steering の state.md / tasklist.md を読めません。読み取り権限を確認してから PR を作成してください。Next Action=unknown / 不足ガード=active steering resolution"
    exit 0
  fi
done

NEXT_ACTION="$(gdd_pr_next_action "$GDD_STEERING_DIR")"

if [[ "$(gdd_value_head "$NEXT_ACTION")" != "done" ]]; then
  [[ -n "$NEXT_ACTION" ]] || NEXT_ACTION="unknown"
  block completion-check-missing "⛔ active GDD: gh pr create の不足を見つけました。completion-check を通してからPRを作成してください（このステアリングを使わないなら、ユーザーに確認したうえで references/self-review-lanes.md の「使わないステアリングの終え方」に従って終える）。Next Action=${NEXT_ACTION} / 不足ガード=completion-check pass"
fi


if [[ -n "$HEAD_BRANCH" ]]; then
  CURRENT_BRANCH="$(git -C "$PROJECT_ROOT" branch --show-current 2>/dev/null || true)"
  HEAD_BRANCH_NAME="${HEAD_BRANCH##*:}"
  if [[ "$HEAD_BRANCH_NAME" != "$CURRENT_BRANCH" ]]; then
    block head-branch-mismatch "⛔ active GDD: gh pr create の不足を見つけました。--head ${HEAD_BRANCH} は現在ブランチ ${CURRENT_BRANCH:-unknown} と一致しないため、PR diff gates の対象を保証できません。現在ブランチからPRを作成してください。Next Action=${NEXT_ACTION} / 不足ガード=PR head branch validation"
  fi
fi

BASE_REF="$(resolve_base_ref)"
if [[ -z "$BASE_REF" ]]; then
  block base-unresolvable "⛔ active GDD: gh pr create の不足を見つけました。PR diff のbase branchを解決できません。completion-check を通してからPRを作成してください。Next Action=${NEXT_ACTION} / 不足ガード=base branch resolution"
  exit 0
fi

STATE_CANONICAL="$GDD_STEERING_DIR/state.md"
ADR_DISTILLED=""
ADR_REASON=""
TASK_SIZE=""
if [[ -f "$STATE_CANONICAL" ]]; then
  ADR_DISTILLED="$(gdd_extract_doc_field "$STATE_CANONICAL" "ADR distilled")"
  ADR_REASON="$(gdd_extract_doc_field "$STATE_CANONICAL" "ADR distillation reason")"
  TASK_SIZE="$(gdd_extract_doc_field "$STATE_CANONICAL" "Task Size")"
fi
ADR_STATUS="$(gdd_adr_status "$ADR_DISTILLED")"
ADR_REASON="$(gdd_adr_reason "$ADR_REASON" "$ADR_DISTILLED")"
if [[ "$ADR_STATUS" == "yes" ]]; then
  if ! gdd_pr_diff_has_adr "$PROJECT_ROOT" "$BASE_REF"; then
    block adr-missing-in-diff "⛔ active GDD: gh pr create の不足を見つけました。ADR distilled=yes ですが docs/adr/ のADRがPR diffに含まれていません。raw steering をPRから除外する前に Distill to ADR を作成してpushしてください。Next Action=${NEXT_ACTION} / 不足ガード=ADR presence in PR diff"
  fi
elif [[ "$ADR_STATUS" == "not_applicable" ]]; then
  if ! gdd_adr_not_applicable_allowed "$TASK_SIZE" "$ADR_REASON" "$STATE_CANONICAL"; then
    if [[ "${GDD_ADR_NA_REASON:-}" == "handoff" ]]; then
      block adr-na-with-decision-handoff "⛔ active GDD: gh pr create の不足を見つけました。state.md に Decision Handoff（(3-f) で後続の test の要件を Issue に申し送った Decision）があるので、Task Size・理由によらず ADR distilled=not_applicable にできません。docs/adr/ に ADR を作り、Consequences に Issue 参照を書いて ADR distilled: yes を記録してください（references/independent-review.md の (3-f)）。Next Action=${NEXT_ACTION} / 不足ガード=ADR not_applicable with Decision Handoff"
    else
      block adr-na-reason-missing "⛔ active GDD: gh pr create の不足を見つけました。ADR distilled=not_applicable の理由が不足しています。trivial / quick express / 重要判断なし のように適用除外理由を state.md に記録するか、docs/adr/ にADRを作成してください。Next Action=${NEXT_ACTION} / 不足ガード=ADR not_applicable reason"
    fi
  fi
else
  block adr-status-unknown "⛔ active GDD: gh pr create の不足を見つけました。standard task のADR蒸留状況を確認できません。docs/adr/ にADRを作成し ADR distilled: yes を記録するか、trivial/express の場合のみ理由付きで ADR distilled: not_applicable を記録してください。Next Action=${NEXT_ACTION} / 不足ガード=ADR presence"
fi

HEALTH_OUTPUT=""
if ! HEALTH_OUTPUT="$(python3 "$PLUGIN_ROOT/scripts/gdd-codebase-health.py" --repo-root "$PROJECT_ROOT" --mode changed --base-ref "$BASE_REF" --fail-on high 2>&1)"; then
  block health-high "⛔ active GDD: gh pr create の不足を見つけました。Codebase Health Gate で High finding が残っています。completion-check を通してからPRを作成してください。Next Action=${NEXT_ACTION} / 不足ガード=Codebase Health Gate High\n${HEALTH_OUTPUT}"
fi

# --- Pre-PR dry gate（独立ブロック。revert は本ブロックのみで完結する）---
# block reason の復旧 3 要素（design.md § block reason に必ず含める 3 要素）。
# 要素 1・2 は lib の `GDD_SR_RECOVERY_CORE` を共有する（pre-push gate と同じ 1 本を
# 使い、手書きリテラルの重複＝ドリフト源を作らない）。
# 要素 3（逃げ道）だけは hook ごとに受理面が違う: design.md § Route / Ownership Matrix が
# pre-PR gate を **kill-switch のみ** と確定させているため、`GDD_SKIP_PRE_PUSH_GATE=1
# git push ...` の 1 行はここには載せられない（pre-PR 側に受理面が無く、載せると
# 効かないバイパスを教示することになる）。したがって pre-PR 側の要素 3 は
# 「本来の導線（セルフレビューを回して証跡を書く）+ 正本パス」で代替する。
_PPR_RECOVERY_SUFFIX="。${GDD_SR_RECOVERY_CORE}。復旧は kill-switch ではなくセルフレビューを回して証跡を書く導線です"
# 未知値は pre-push gate step 9 と同じ規則（lib の 1 本）で fail-closed 側の `standard` へ畳む。
# 生値のまま parser へ渡すと、未知値の state.md で pre-PR だけが独立レビューを要求
# しつつ委譲記録形を invalid にする自己矛盾になる（R4 #7）。
PP_TASK_SIZE_NORMALIZED="$(gdd_normalize_task_size "$TASK_SIZE")"
PP_REQUIRES_DRY="false"
if gdd_task_size_requires_dry "$PP_TASK_SIZE_NORMALIZED"; then
  PP_REQUIRES_DRY="true"
fi
if [[ "$PP_REQUIRES_DRY" == "true" ]]; then
  gdd_parse_self_review_field "$STATE_CANONICAL" "Pre-PR Self Review" "$PP_TASK_SIZE_NORMALIZED"
  if [[ "$GDD_SR_VALID" != "true" ]]; then
    # `GDD_SR_MISSING_KEYS` は「不足 key 名」だけでなく検出理由 token
    # （`dry-consecutive-clean-contradiction` 等）も載るため、ラベルは `検出` にする。
    # 既定値（`:-` フォールバック）は置かない: invalid 経路はすべて非空値を設定するので
    # 到達不能な dead code になり、必要 key の全列挙は上の suffix が常に担う。
    block missing-evidence "⛔ active GDD: gh pr create の不足を見つけました。Pre-PR Self Review が見つからないか書式不正です（reason code: missing-evidence / 検出: ${GDD_SR_MISSING_KEYS}）${_PPR_RECOVERY_SUFFIX}。Next Action=${NEXT_ACTION} / 不足ガード=Pre-PR Self Review evidence"
  elif [[ "$GDD_SR_DRY" != "yes" ]]; then
    block dry-not-reached "⛔ active GDD: gh pr create の不足を見つけました。Pre-PR Self Review の dry: yes に到達していません（reason code: dry-not-reached）${_PPR_RECOVERY_SUFFIX}。内部整合レーンを 1 周して「新規 high / blocking ゼロ」にし、standard は独立レビュー 1 回（high 0 / blocking 0）も記録してから再実行してください。Next Action=${NEXT_ACTION} / 不足ガード=dry convergence"
  fi
  # standard は独立レビュー 1 回（HEAD sha / high 0 / blocking 0）の証跡も要求する。
  # 上の dry-not-reached 文言が独立レビューを要求している以上、機械強制できる述語を
  # 自己申告のまま残さない（独立レビュー #5 / 2026-09-06）。述語・パーサは pre-push
  # gate step 13b と同一（正本: references/independent-review.md）。pre-PR は push 済み
  # ref ではなく HEAD を見る（merge gate と同じ基準）。
  # shellcheck source=lib/merge-gate-evidence.sh
  source "$SCRIPT_DIR/lib/merge-gate-evidence.sh"
  gdd_parse_merge_gate_field "$STATE_CANONICAL" "Independent Review"
  # 復旧要素 2 は `Independent Review` 行の必要 key（正本: lib の GDD_IR_RECOVERY_CORE）。
  _PPR_IR_RECOVERY_SUFFIX="。${GDD_IR_RECOVERY_CORE}。復旧は kill-switch ではなくセルフレビューと独立レビューを回して証跡を書く導線です"
  if [[ "$GDD_MG_VALID" != "true" ]]; then
    block independent-review-missing "⛔ active GDD: gh pr create の不足を見つけました。Independent Review が見つからないか不正です（reason code: independent-review-missing）${_PPR_IR_RECOVERY_SUFFIX}。Next Action=${NEXT_ACTION} / 不足ガード=Independent Review evidence"
  else
    PPR_HEAD_SHA="$(git -C "$PROJECT_ROOT" rev-parse --quiet --verify HEAD 2>/dev/null || true)"
    # 一致しなくても、HEAD が main を取り込むだけの merge commit なら引き継ぐ（pre-push gate と同じ述語）。
    if ! gdd_evidence_sha_matches "$PROJECT_ROOT" "$GDD_MG_SHA" "$PPR_HEAD_SHA" \
      && ! gdd_ir_carry_matches "$PROJECT_ROOT" "$STATE_CANONICAL" "$GDD_MG_SHA" "$PPR_HEAD_SHA"; then
      block independent-review-stale "⛔ active GDD: gh pr create の不足を見つけました。Independent Review の sha が HEAD と一致しません（reason code: independent-review-stale）。既定ブランチを取り込むだけのマージコミットなら、Independent Review Carry 行で引き継げます（正本: references/self-review-lanes.md）${_PPR_IR_RECOVERY_SUFFIX}。Next Action=${NEXT_ACTION} / 不足ガード=Independent Review freshness"
    elif ! gdd_independent_review_clean; then
      block independent-review-high "⛔ active GDD: gh pr create の不足を見つけました。Independent Review に high / blocking が残っています（reason code: independent-review-high）${_PPR_IR_RECOVERY_SUFFIX}。Next Action=${NEXT_ACTION} / 不足ガード=Independent Review high"
    fi
  fi
fi

exit 0
