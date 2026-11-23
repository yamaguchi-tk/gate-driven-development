#!/usr/bin/env python3
"""Block GDD task branch creation in the repository root checkout."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path


ALLOW = {"continue": True, "suppressOutput": True}

#: ブランチ名の接頭辞判定は OS/filesystem の case-sensitivity とは無関係に
#: 常に大文字小文字を無視する（`Codex/`/`CODEX/` も `codex/` と同じ意図の
#: 命名として扱う）。`re.IGNORECASE` 欠落により `looks_like_gdd_task_branch`
#: が大文字始まりの接頭辞で False を返し、`_worktree_creates_gdd_branch` /
#: `_creates_gdd_named_branch` の入り口ゲートごと guard を bypass できていた
#: （独立発見、実測確認済み）。
GDD_TASK_BRANCH_RE = re.compile(
    r"\b(?:codex|gdd|claude|cursor)/20[0-9]{6}[A-Za-z0-9._/\-]*\b", re.IGNORECASE
)

_NAMED_FD_TOKEN_RE = re.compile(r"\{[A-Za-z_][A-Za-z0-9_]*\}")


def _is_potential_fd_token(token: str) -> bool:
    """数字 fd（`2>...`）に加え、bash 4.1+ の可変 fd（`{name}>...`）候補も拾う。

    tokenizer は `2>/dev/null` と `2 > /dev/null`（空白の有無で fd 宣言か
    独立 positional かが変わる）を区別できないのと同様、`{name}>/dev/null`
    と `{name} > /dev/null` も区別できない。`{name}` が redirection operator
    に隣接する形を無条件に fd 候補として読み飛ばすと、独立引数だった場合は
    真の候補を取り違えて過剰 deny に倒れうるが、読み飛ばさない場合は
    bash 4.1+ 環境で `{name}` が実際に fd 宣言として消費され、後続の実引数
    （GDD 名になりうる）が候補から漏れて silent allow になる（実測: PR #34
    Copilot review 指摘）。安全側（fail-closed）に倒すため、常に fd 候補として
    読み飛ばす。
    """
    return bool(token.isdigit() or _NAMED_FD_TOKEN_RE.fullmatch(token))

_BRANCH_NON_CREATING_LONG_FLAGS = frozenset(
    {
        "--delete",
        "--move",
        # R2: 実測確認済み（git 2.50.1）。作成系flag併用でもrefを
        # 作らないため常にveto可（unconditional）。
        "--list",
        "--show-current",
        "--edit-description",
        "--set-upstream-to",
        "--unset-upstream",
        "--contains",
        "--no-contains",
        "--merged",
        "--no-merged",
        "--points-at",
    }
)
# R2: --all/--remotesは--copy/-c/-Cと併用されると実gitがbranchを
# 作成する（実測確認済み: git 2.50.1。-ca/-ac/-Cr/--copy --all 等）。
# 無条件veto は新規fail-openになるため、同一segmentに作成系flag
# （saw_creating）や未知flag（saw_unknown_flag）が無い場合にのみ
# vetoする（conditional）。
_BRANCH_CONDITIONAL_NON_CREATING_LONG_FLAGS = frozenset({"--all", "--remotes"})
_BRANCH_NON_CREATING_SHORT_LETTERS = "dDmM"
# 短letterのconditional veto（long版と同条件）。実測確認済み: git 2.50.1
# （`-a <名前>`/`-r <名前>`は単独では rc=128「does not take a branch
# name」でrefを作らないが、`-ca`/`-ac`/`-Cr`等copy併用時は作成する）。
# uは値結合形(-umain)と単独形で扱いが分かれるため
# _classify_branch_short_cluster内で個別処理。
_BRANCH_CONDITIONAL_NON_CREATING_SHORT_LETTERS = "ar"
# --track/--no-track/--create-reflog/--quietはいずれもbranch作成の
# 付随flag（実測確認済み: git 2.50.1）。--quietはR2でlong形追加
# （短letter qは[0.40.1]で既にcreating側。long形だけが残存fail-open）。
_BRANCH_CREATING_LONG_FLAGS = frozenset(
    {"--copy", "--force", "--track", "--no-track", "--create-reflog", "--quiet"}
)
# tは値を取り得る（-tdirect=--track=direct等）ため
# _classify_branch_short_cluster内で個別処理。ここには含めない。
# 実測確認済み: git 2.50.1（c/C/fは[0.40.1]で、qはR2でlong形と揃えて
# 短letterも既にcreating側と確認済み）。
_BRANCH_CREATING_SHORT_LETTERS = "cCfq"
# 既知の非modeletter（c/C/f/t/qに加えv/i）のうちvetoもcreatingも
# 行わない残り2文字。実測行を持たないletterは必ずunknown扱いにする
# ためこの集合を広げない。実測確認済み: git 2.50.1（`-v <名前>`/
# `-i <名前>`はいずれもrefを作成するが、その存在自体をveto/creatingの
# どちらにも紐づけない中立letterとして扱う。design.md D-1のdispatch表
# には明記が無かったため実装時に新設した区分）。
_BRANCH_KNOWN_NEUTRAL_SHORT_LETTERS = "vi"
# 値を取り得る短letter（残余があればattached valueと断定し走査を
# 打ち切る。実測確認済み: git 2.50.1）。
_BRANCH_VALUE_TAKING_SHORT_LETTERS = "tu"

# --color/--column/--abbrevは実gitではoptional argument
# （=<value>必須、空白区切りの次tokenは値として消費しない）。
# --sort/--formatは必須値で、空白区切りでも次tokenを値として消費する。
_BRANCH_OPTIONAL_VALUE_LONG_FLAGS = frozenset({"--color", "--column", "--abbrev"})
_BRANCH_MANDATORY_VALUE_LONG_FLAGS = frozenset({"--sort", "--format"})


def _short_cluster_has(token: str, letters: str) -> bool:
    """`-cC` のような短 option cluster に `letters` のいずれかが含まれるか。

    long option（`--create` 等）は対象外にする。値結合形（`-bcodex/...`）も
    含めて検出するため、`len(token) >= 2` であれば cluster とみなす。
    """
    if not token.startswith("-") or token.startswith("--"):
        return False
    return any(letter in token[1:] for letter in letters)


def _segment_creates_switch(segment: list[str], subcommand_index: int) -> bool:
    for token in segment[subcommand_index + 1 :]:
        if _short_cluster_has(token, "cC"):
            return True
        if token.split("=", 1)[0] in {"--create", "--force-create"}:
            return True
    return False


def _segment_creates_checkout(segment: list[str], subcommand_index: int) -> bool:
    return any(
        _short_cluster_has(token, "bB")
        for token in segment[subcommand_index + 1 :]
    )


def _classify_branch_short_cluster(
    token: str,
) -> tuple[bool, bool, bool, bool, bool, str | None]:
    """branch gate1専用の短option cluster分類（design.md D-3/D-4が正本）。

    `_short_cluster_has`（部分文字列一致）と異なり、値結合形
    （`-fcodex/20260903-a`等）をmode letterと誤読しない2段階判定を行う。
    1: bodyに英字以外を含めば「flag+結合値」と断定しletter単位走査
    をしない。2: bodyが全英字のときだけ先頭から1letterずつ分類する。

    戻り値: (unconditional_veto, conditional_veto, creating, unknown,
    recognized, positional)の6-tuple。
    - unconditional_veto: d/D/m/Mを含む（常にveto）
    - conditional_veto: a/r、または残余なしのuを含む（同一segmentに
      creating flagも未知flagも無いときだけveto。判定は呼び出し側が
      走査完了後にまとめて行う）
    - creating: c/C/f/q、またはt（残余の有無を問わない）を含む
    - unknown: 既知7letter（c f t q v i C）にもmode letterにも該当
      しないletterを含む（fail-closed側。この集合を広げない）
    - recognized: seen_recognized_flagにORしてよいか。unconditional
      vetoだけのtokenでは立てない（Round4/security MEDIUM-1: `-f --`
      等のdenyを維持するため）。ただしneutral letter（v/i）は「作成には
      無関係だが既知の flag として認識できた」ことを表すため recognized
      に寄与する（実測確認済み: `-v -- <名前>` は実 git が ref を作るが、
      neutral letter を recognized から除外すると `--` の bare carve-out
      に落ちて allow に退行する。unconditional veto letter と同時に
      現れた場合（`-dv` 等）は従来どおり veto を優先し recognized を
      立てない）。
    - positional: attached-value形のとき、そのtoken自身を返す
      （bool(positionals)の判定に使うだけなので中身は問わない）
    """
    body = token[1:]
    if not body.isalpha():
        return (False, False, False, False, True, token)

    unconditional_veto = False
    conditional_veto = False
    creating = False
    saw_neutral = False

    index = 0
    while index < len(body):
        letter = body[index]
        if letter in _BRANCH_VALUE_TAKING_SHORT_LETTERS:
            residual = body[index + 1 :]
            if residual:
                if letter == "t":
                    creating = True
                return (
                    unconditional_veto,
                    conditional_veto,
                    creating,
                    False,
                    True,
                    token,
                )
            if letter == "t":
                creating = True
            else:
                conditional_veto = True
            index += 1
            continue
        if letter in _BRANCH_NON_CREATING_SHORT_LETTERS:
            unconditional_veto = True
            index += 1
            continue
        if letter in _BRANCH_CONDITIONAL_NON_CREATING_SHORT_LETTERS:
            conditional_veto = True
            index += 1
            continue
        if letter in _BRANCH_CREATING_SHORT_LETTERS:
            creating = True
            index += 1
            continue
        if letter in _BRANCH_KNOWN_NEUTRAL_SHORT_LETTERS:
            saw_neutral = True
            index += 1
            continue
        # 未知letter: このtokenの走査だけを打ち切る（positionalは
        # 推定しない）。
        return (unconditional_veto, conditional_veto, creating, True, True, None)

    recognized = creating or conditional_veto or (saw_neutral and not unconditional_veto)
    return (unconditional_veto, conditional_veto, creating, False, recognized, None)


def _branch_long_flag_dispatch(
    flag: str, has_equals: bool, cursor: int
) -> tuple[bool, bool, bool, bool, bool, int]:
    """`--`始まり long option 1個の状態遷移とcursor更新（複雑度低減用）。

    D-1 分岐4（長 flag）の非作成（unconditional）→非作成（conditional）→
    作成→必須値→optional値→未知の順序をそのまま保つ。戻り値:
    (unconditional_veto, conditional_veto, creating,
    unknown, recognized, next_cursor)の6-tuple。呼び出し側はこれらを
    saw_*変数へORし、cursorをnext_cursorへ進める。
    """
    if flag in _BRANCH_NON_CREATING_LONG_FLAGS:
        return (True, False, False, False, False, cursor + 1)
    if flag in _BRANCH_CONDITIONAL_NON_CREATING_LONG_FLAGS:
        return (False, True, False, False, True, cursor + 1)
    if flag in _BRANCH_CREATING_LONG_FLAGS:
        return (False, False, True, False, True, cursor + 1)
    if flag in _BRANCH_MANDATORY_VALUE_LONG_FLAGS:
        # 空白区切りの値は次tokenを無条件に消費する（実gitは必須値flag
        # 直後のtokenを、見た目に関わらず値として消費する）。
        next_cursor = cursor + 1 if has_equals else cursor + 2
        return (False, False, False, False, True, next_cursor)
    if flag in _BRANCH_OPTIONAL_VALUE_LONG_FLAGS:
        # `=`無しの空白区切り値は消費しない（optional argument仕様）。
        return (False, False, False, False, True, cursor + 1)
    # 未知のlong flag（変更1）: 読み飛ばして継続する（fail-closed側へ倒す。
    # 実測確認済み: git 2.50.1で--gdd-probe-future-flag/-Zのような未知flag
    # はerrorになるだけでbranchを作らないが、将来gitが新設するflagは未知の
    # まま作成互換として扱う）。
    return (False, False, False, True, True, cursor + 1)


def _segment_creates_branch(segment: list[str], subcommand_index: int) -> bool:
    """`git branch`のsegmentが実際にbranchを作成する操作かを判定する。

    R2（design.md D-1〜D-7が正本）: PR #41の1パスcursor walkの骨格・
    `--`のcarve-out・value-takingテーブルは維持し、次の3点だけ変更する。
    1. 未知の`-`始まりtokenへの早期`return False`（fail-open本体）を
       撤去し、読み飛ばして継続する（saw_unknown_flag=True）。
    2. 非作成（mode）判定をunconditional（常時veto）とconditional
       （同一segmentに作成系flagも未知flagも無いときだけveto）の2区分
       にし、ループ末尾でまとめて評価する（pre-scanはしない。
       `--sort -committerdate -a <name>`のようなvalue token誤読を
       防ぐため）。
    3. 短option cluster判定を`_classify_branch_short_cluster`
       （letter単位走査、t/uのattached-value規則を含む）へ置き換える。
    """
    rest = _strip_redirections(segment[subcommand_index + 1 :])
    if not rest:
        return False
    if not rest[0].startswith("-"):
        return True

    positionals: list[str] = []
    saw_unconditional_veto = False
    saw_conditional_veto = False
    saw_creating = False
    saw_unknown_flag = False
    # `--`以前に少なくとも1つ既知flag（creating/conditional/
    # value-taking/neutral letter（v/i）/未知）を消費済みか。`git branch -- <name>`
    # （creating flag無しのbare形、既知limitation）は従来どおり
    # allowのまま維持する。
    seen_recognized_flag = False
    cursor = 0
    while cursor < len(rest):
        token = rest[cursor]
        if not token.startswith("-"):
            positionals.append(token)
            cursor += 1
            continue
        if token == "--":
            if not seen_recognized_flag:
                return False
            cursor += 1
            continue
        if not token.startswith("--"):
            (
                cluster_unconditional_veto,
                cluster_conditional_veto,
                cluster_creating,
                cluster_unknown,
                cluster_recognized,
                cluster_positional,
            ) = _classify_branch_short_cluster(token)
            saw_unconditional_veto |= cluster_unconditional_veto
            saw_conditional_veto |= cluster_conditional_veto
            saw_creating |= cluster_creating
            saw_unknown_flag |= cluster_unknown
            seen_recognized_flag |= cluster_recognized
            if cluster_positional is not None:
                positionals.append(cluster_positional)
            cursor += 1
            continue
        flag, has_equals, _inline_value = token.partition("=")
        (
            flag_unconditional_veto,
            flag_conditional_veto,
            flag_creating,
            flag_unknown,
            flag_recognized,
            cursor,
        ) = _branch_long_flag_dispatch(flag, bool(has_equals), cursor)
        saw_unconditional_veto |= flag_unconditional_veto
        saw_conditional_veto |= flag_conditional_veto
        saw_creating |= flag_creating
        saw_unknown_flag |= flag_unknown
        seen_recognized_flag |= flag_recognized

    if saw_unconditional_veto:
        return False
    if saw_conditional_veto and not (saw_creating or saw_unknown_flag):
        return False
    return bool(positionals)


_LIB_DIR = str(Path(__file__).resolve().parent / "lib")
sys.path.insert(0, _LIB_DIR)
try:
    from git_command_parse import (
        COMMAND_SUBSTITUTION_PLACEHOLDER,
        is_git_token,
        is_redirection_operator,
        split_segments,
        subcommand_candidates,
    )
    from regular_file import read_regular_text
except Exception:  # noqa: BLE001 - SyntaxError / top-level 例外も含めて捕捉する
    PARSER_AVAILABLE = False
else:
    PARSER_AVAILABLE = True
finally:
    sys.path.remove(_LIB_DIR)

_GIT_WORD_RE = re.compile(r"\bgit\b")


def emit_deny_parser_unavailable(command: str, cwd: Path) -> int:
    message = (
        "Blocked: the GDD root-branch guard could not parse this command "
        "because `lib/git_command_parse.py` or `lib/regular_file.py` failed to import.\n\n"
        f"cwd: {cwd}\ncommand: {command}\n\n"
        "Recovery (try in this order): "
        "(1) restore the shipped files with `git checkout -- "
        "plugins/gate-driven-development/hooks/scripts/lib/git_command_parse.py "
        "plugins/gate-driven-development/hooks/scripts/lib/regular_file.py` "
        "in the repository that owns this worktree, or "
        "(2) reinstall the gate-driven-development plugin. "
        "Only use the kill switch (`~/.claude/gdd-hooks-disabled`) as a last "
        "resort decided by a human — it disables every GDD guardrail hook on "
        "this machine, not just this one."
    )
    print(
        json.dumps(
            {
                "hookSpecificOutput": {"permissionDecision": "deny"},
                "systemMessage": message,
            },
            ensure_ascii=False,
        ),
        file=sys.stderr,
    )
    return 2


def emit_allow() -> int:
    print(json.dumps(ALLOW))
    return 0


def emit_deny_unresolved_cwd(command: str, error: Exception) -> int:
    message = (
        "Blocked: the GDD root-branch guard could not resolve the working directory "
        "(the tool_input `cwd`/`workdir`, else the payload `cwd`, else this hook's own cwd), "
        "so it cannot tell whether this command creates a branch or a GDD worktree in a "
        "repository root checkout.\n\n"
        f"error: {type(error).__name__}: {error}\ncommand: {command}\n\n"
        "Recovery: if the session's current directory was removed (for example its "
        "worktree was deleted), reopen the session in a directory that exists. Commands "
        "that do not create a branch or a GDD worktree (such as `git worktree prune`) "
        "still run. With Codex, pass an absolute `workdir` that exists."
    )
    print(
        json.dumps(
            {
                "hookSpecificOutput": {"permissionDecision": "deny"},
                "systemMessage": message,
            },
            ensure_ascii=False,
        ),
        file=sys.stderr,
    )
    return 2


def emit_deny(command: str, cwd: Path) -> int:
    message = (
        "Blocked GDD root branch creation. /gdd-dev must create task branches with "
        "`git worktree add -b <branch> <worktree-path> <default-branch>` and must not "
        "run `git switch -c`, `git checkout -b`, or root `git branch <name>` in the "
        f"repository root checkout.\n\ncwd: {cwd}\ncommand: {command}\n\n"
        "Why: creating the task branch in repo root leaves `.steering/` and later "
        "implementation state attached to the shared checkout, which reintroduces "
        "the task/worktree mixing GDD is designed to prevent. Create or repair the "
        "dedicated worktree first, then write GDD artifacts inside that worktree.\n\n"
        "This also blocks when the repository root has `.claude/gdd-dev.local.md` with "
        "`active: true` and the guard cannot tell that it belongs to another session: the "
        "state's `session_id` is empty, missing, repeated, or malformed, the state has no "
        "`---` frontmatter or no closing `---`, the payload `session_id` is missing, is not "
        "an id (such as `served:<id>`), or does not match `CLAUDE_CODE_SESSION_ID`, or the "
        "state belongs to this session. It also blocks when the state cannot be read (it "
        "is not a regular file, it has no read permission, or `.claude/` has no search "
        "permission, in which case it blocks even when no state exists). To see which "
        "applies, read the first lines of that file. A GDD-named branch is blocked "
        "regardless of the state.\n\n"
        "To release a readable state: ask the user whether the GDD session that wrote it "
        "is still running. If it is not, change `active: true` to `active: false` in that "
        "file and run the command again. Do not rewrite `session_id`. For a state that "
        "cannot be read, restore it as a regular file or fix the permissions of `.claude/` "
        "and the file."
    )
    print(
        json.dumps(
            {
                "hookSpecificOutput": {"permissionDecision": "deny"},
                "systemMessage": message,
            },
            ensure_ascii=False,
        ),
        file=sys.stderr,
    )
    return 2


def emit_deny_head_worktree(command: str, cwd: Path) -> int:
    message = (
        "Blocked GDD worktree creation from HEAD. A new /gdd-dev task must create "
        "its dedicated worktree from the default branch, not from the currently "
        "checked-out task branch.\n\n"
        f"cwd: {cwd}\ncommand: {command}\n\n"
        "Why: `git worktree add ... HEAD` copies the current branch's context into "
        "the new task and can carry prior task commits, dirty assumptions, and "
        "wrong-base steering state forward. Run `git fetch origin`, resolve the "
        "default branch, then create the task worktree with "
        "`git worktree add <path> -b <branch> origin/<default-branch>` or a recorded "
        "Base Commit."
    )
    print(
        json.dumps(
            {
                "hookSpecificOutput": {"permissionDecision": "deny"},
                "systemMessage": message,
            },
            ensure_ascii=False,
        ),
        file=sys.stderr,
    )
    return 2


def emit_deny_local_base_worktree(command: str, cwd: Path) -> int:
    message = (
        "Blocked GDD worktree creation from a local default branch. A new /gdd-dev "
        "task must create its dedicated worktree from a freshly fetched remote "
        "default branch or a recorded Base Commit, not from possibly stale local "
        "`main` / `master` / `develop`.\n\n"
        f"cwd: {cwd}\ncommand: {command}\n\n"
        "Why: local default branches can lag behind origin and silently start the "
        "task from an old base. Run `git fetch origin`, then use "
        "`git worktree add <path> -b <branch> origin/<default-branch>` or a recorded "
        "Base Commit SHA."
    )
    print(
        json.dumps(
            {
                "hookSpecificOutput": {"permissionDecision": "deny"},
                "systemMessage": message,
            },
            ensure_ascii=False,
        ),
        file=sys.stderr,
    )
    return 2


def extract_command(payload: dict) -> str:
    tool_input = payload.get("tool_input", {})
    if isinstance(tool_input, dict):
        for key in ("command", "cmd", "script"):
            value = tool_input.get(key)
            if isinstance(value, str):
                return value
    if isinstance(tool_input, str):
        return tool_input
    return ""


def extract_cwd(payload: dict) -> Path:
    tool_input = payload.get("tool_input", {})
    if isinstance(tool_input, dict):
        value = tool_input.get("cwd") or tool_input.get("workdir")
        if isinstance(value, str) and value:
            return Path(value).expanduser().resolve()
    # Claude Code の Bash は tool_input に cwd を持たず、payload の最上位に持つ。
    # hook のプロセスの cwd はセッションの cwd と違うことがある（desktop の worktree の
    # セッションで root checkout になる）。最上位の cwd が使えないとき（文字列でない・空・
    # 相対パス・存在しない）は、今までどおりプロセスの cwd で判定する。
    # `os.path.isdir` は OSError・ValueError（NUL など）を False にするので、版によらず戻る。
    # tool_input の値と違い `~` は展開しない（harness が入れる絶対パスだけを受ける）。
    # 受け入れの条件は、ほかの gate が使う `lib/hook_cwd.py` の `toplevel_cwd` と同じにする
    # （タブ・改行・CR を含む値と、中に入れない〔実行権の無い〕ディレクトリも受けない）。
    top = payload.get("cwd")
    if (
        isinstance(top, str)
        and top
        and os.path.isabs(top)
        and not any(ch in top for ch in ("\t", "\n", "\r"))
        and os.path.isdir(top)
        and os.access(top, os.X_OK)
    ):
        return Path(top).resolve()
    return Path.cwd().resolve()


SESSION_ID_SHAPE = re.compile(r"[A-Za-z0-9_-]+")


def session_id_or_empty(value: str) -> str:
    """id の形（英数字・`-`・`_`）の値だけを返す。それ以外は空（照合できない）。"""
    return value if SESSION_ID_SHAPE.fullmatch(value) else ""


def frontmatter_session_id(text: str) -> str:
    """frontmatter の `session_id` の値。行の分け方とキーの読み方は lib/state_io.py の parse_state にそろえる
    （`\n` だけで分け、行を strip してキーを読む）。

    区切りが無い・閉じの区切りが無い・`session_id` の行が無いか 2 行以上ある・値が id の形でないときは空。
    """
    lines = text.split("\n")
    if not lines or lines[0] != "---" or "---" not in lines[1:]:
        return ""
    frontmatter = lines[1 : lines.index("---", 1)]
    values = [
        line.strip().split(":", 1)[1].strip()
        for line in frontmatter
        if ":" in line and line.strip().split(":", 1)[0].strip() == "session_id"
    ]
    return session_id_or_empty(values[0]) if len(values) == 1 else ""


def payload_session_id(payload: dict) -> str:
    """今の session id。hook の payload の session_id を、hook のプロセスの環境変数 `CLAUDE_CODE_SESSION_ID` と
    一致するとき（Claude Code の hook）だけ返す。

    環境変数は Claude Code から開いた別の runtime にも継がれ、setup はそれを marker の持ち主として書く。
    その runtime の payload の id は環境変数と合わないので、空（照合できない）にして止める。
    どちらかが id の形でない（リモート呼び出しの `served:<id>` など）・環境変数が無いときも空。
    """
    value = payload.get("session_id")
    if not isinstance(value, str):
        return ""
    current = session_id_or_empty(value)
    return current if current and current == os.environ.get("CLAUDE_CODE_SESSION_ID") else ""


def root_state_blocks(cwd: Path, current_session: str = "") -> bool:
    """root の marker で止めるか。

    `active: true` の marker があっても、frontmatter の session_id が空でなく、今の session id と違う
    （別の session の marker）なら止めない。今の session id が取れないとき・marker の session_id が
    空か frontmatter に無いとき・marker があるのに通常のファイルでないか読めないときは、照合できないので止める。
    """
    repo_root = git_output(["git", "rev-parse", "--show-toplevel"], cwd)
    if not repo_root:
        return False
    state_file = Path(repo_root) / ".claude" / "gdd-dev.local.md"
    # lib/state_io.py の parse_state と同じ部品で読む。「無い」とするのはパスに何も無いとき
    # （ENOENT・ENOTDIR）だけで、通常のファイルでない（ディレクトリ・壊れた symlink・FIFO）・
    # 読めない（検索権の無いディレクトリの下を含む）ときは、照合できないので止める。
    # `errors="replace"`: 非 UTF-8 バイトで `UnicodeDecodeError`（`OSError` ではない）が
    # `main()` の try に落ち、真因と無関係な deny メッセージになるのを防ぐ。
    try:
        text = read_regular_text(state_file, errors="replace")
    except OSError:
        return True
    if text is None:
        return False
    if "active: true" not in text:
        return False
    owner = frontmatter_session_id(text)
    if current_session and owner and owner != current_session:
        return False
    return True


def git_output(command: list[str], cwd: Path) -> str:
    try:
        result = subprocess.run(
            command,
            cwd=str(cwd),
            capture_output=True,
            check=False,
        )
    except OSError:
        return ""
    if result.returncode != 0:
        return ""
    # bytes で読み、git が出す最後の改行だけを落とす。`.strip()` にすると、名前が
    # 空白・改行で終わる toplevel（`<repo> `）が別のパス（`<repo>`）になり、そこの
    # marker を見てしまう。text モードは CR を改行に置き換えるので使わない。
    out = result.stdout
    return os.fsdecode(out[:-1] if out.endswith(b"\n") else out)


def is_linked_worktree(cwd: Path) -> bool:
    git_dir = git_output(["git", "rev-parse", "--git-dir"], cwd)
    common_dir = git_output(["git", "rev-parse", "--git-common-dir"], cwd)
    if not git_dir or not common_dir:
        return False

    git_dir_path = Path(git_dir)
    common_dir_path = Path(common_dir)
    if not git_dir_path.is_absolute():
        git_dir_path = (cwd / git_dir_path).resolve()
    if not common_dir_path.is_absolute():
        common_dir_path = (cwd / common_dir_path).resolve()
    return git_dir_path != common_dir_path


def _root_branch_creation_sites(
    segments: list[list[str]],
) -> list[tuple[list[str], int, str]]:
    sites: list[tuple[list[str], int, str]] = []
    for segment in segments:
        for index, token in enumerate(segment):
            if not is_git_token(token):
                continue
            for candidate in sorted(subcommand_candidates(segment, index + 1)):
                subcommand = segment[candidate]
                if subcommand == "switch" and _segment_creates_switch(segment, candidate):
                    sites.append((segment, candidate, subcommand))
                if subcommand == "checkout" and _segment_creates_checkout(segment, candidate):
                    sites.append((segment, candidate, subcommand))
                if subcommand == "branch" and _segment_creates_branch(segment, candidate):
                    sites.append((segment, candidate, subcommand))
    return sites


def command_creates_root_branch(segments: list[list[str]]) -> bool:
    return bool(_root_branch_creation_sites(segments))


def _literal_path(token: str, base: Path) -> Path | None:
    """`cd`・`git -C` の引数を、変数・置換を含まないときだけパスにする（`~` は展開できるときだけ展開する）。"""
    if not token or token == "-" or _is_unexpanded_token(token):
        return None
    try:
        path = Path(token).expanduser()
    except RuntimeError:  # `~-`・`~+`・存在しないユーザーの `~name`
        return None
    return (path if path.is_absolute() else base / path).resolve()


def _cd_targets_before(segments: list[list[str]], limit: int, cwd: Path) -> list[Path]:
    """`limit` 番目のセグメントより前で、先頭が `cd` のセグメントの行き先（順に積む）。

    `cd` が効いたかは見ない。サブシェル・`&`・パイプの中の `cd`、失敗した `cd`、後の `cd` で置き換わった
    `cd` の行き先も候補に入り、次の相対 `cd` の基点にもなる。そのため本当の行き先が候補から落ちることも、
    実際には作らない場所で止めることもある。`then cd`・`{ cd`・`builtin cd` のように先頭にない `cd` は見ない。
    決められない `cd`（変数など）は基点を動かさず、その後の相対 `cd` は前の行き先で解く。
    """
    targets: list[Path] = []
    base = cwd
    for segment in segments[:limit]:
        if not segment or segment[0] != "cd":
            continue
        argument = next((token for token in segment[1:] if not token.startswith("-")), "")
        target = _literal_path(argument, base)
        if target is not None:
            targets.append(target)
            base = target
    return targets


def root_branch_exec_targets(segments: list[list[str]], cwd: Path) -> list[Path]:
    """ブランチを作るサイトごとの実行先の候補。

    先行する `cd` の行き先と、それぞれ（と payload cwd）を基点に `git -C` を順に解いた先。決められない
    `-C` は飛ばして前の基点を保つので、`-C` が全部決められないときは基点（payload cwd を含む）が入る。
    `push_command_parse.resolve_candidate_roots` は `push` まで走査するので、`git branch -C` を
    `git -C` と取り違える。ここでは git の語とサブコマンドの間だけを見る。
    """
    targets: list[Path] = []
    for segment, subcommand_index, _ in _root_branch_creation_sites(segments):
        position = next(index for index, part in enumerate(segments) if part is segment)
        cd_targets = _cd_targets_before(segments, position, cwd)
        targets += cd_targets
        git_index = max(index for index in range(subcommand_index) if is_git_token(segment[index]))
        dash_c = [
            segment[index + 1]
            for index in range(git_index + 1, subcommand_index - 1)
            if segment[index] == "-C"
        ]
        if not dash_c:
            continue
        for base in [cwd, *cd_targets]:
            target = base
            for argument in dash_c:
                # 決められない `-C` は `cd` と同じく飛ばし、前の基点を保つ。
                target = _literal_path(argument, target) or target
            targets.append(target)
    return targets


def _next_value_index(tokens: list[str], cursor: int) -> int | None:
    """flag の値位置を redirection operator / fd 番号を読み飛ばして決定する。

    非 redirection な token に到達するまで while ループで繰り返す。単発適用や
    「fd を 1 回 + redirection を 1 回」の 2 ステップ実装は、連続 redirection
    （`git switch -c >/dev/null 2>&1 codex/...` 等）で候補を取り違え、silent
    allow を再導入する（回帰テスト: tests/test_root_branch_name_candidates.py::test_hook_blocks_redirection_at_value_position）。
    """
    while cursor < len(tokens):
        token = tokens[cursor]
        if is_redirection_operator(token):
            cursor += 2
            continue
        if (
            _is_potential_fd_token(token)
            and cursor + 1 < len(tokens)
            and is_redirection_operator(tokens[cursor + 1])
        ):
            cursor += 1
            continue
        if token == "--":
            return None
        return cursor
    return None


def _take_flag_value(tokens: list[str], cursor: int) -> tuple[str | None, int]:
    """`-c BRANCH` のように分離した値 token を取り出し、`(値, 次の cursor)` を返す。

    値が無ければ `(None, cursor + 1)` を返して呼び出し側のループを 1 つ進める。
    """
    value_index = _next_value_index(tokens, cursor + 1)
    if value_index is None:
        return None, cursor + 1
    return tokens[value_index], value_index + 1


def _sanitize_candidates(names: set[str]) -> set[str]:
    """空文字列と `-` 始まり token は branch 名候補として採用しない。"""
    return {name for name in names if name and not name.startswith("-")}


def _is_unexpanded_token(token: str) -> bool:
    """`==` ではなく部分一致にする。`foo$(bar)baz` のような結合形も拾うため。"""
    return "$" in token or "`" in token or COMMAND_SUBSTITUTION_PLACEHOLDER in token


_SWITCH_CREATE_LONG_FLAGS = frozenset({"--create", "--force-create"})


def _switch_branch_names(segment: list[str], subcommand_index: int) -> set[str]:
    names: set[str] = set()
    rest = segment[subcommand_index + 1 :]
    cursor = 0
    while cursor < len(rest):
        # redirection の対象 token（`>-c` の `-c` 等）を 2 個目の flag と
        # 誤認しないよう、flag 判定の前に読み飛ばす（`_branch_names` /
        # `_has_unknown_branch_flag` と同じ扱い。PR #34 Copilot review 指摘）。
        skipped = _skip_redirection(rest, cursor)
        if skipped is not None:
            cursor = skipped
            continue
        token = rest[cursor]
        if token == "--":
            break
        cluster_value = _short_cluster_value(token, "cC")
        if cluster_value is not None:
            if cluster_value:
                names.add(cluster_value)
                cursor += 1
                continue
            value, cursor = _take_flag_value(rest, cursor)
            if value is not None:
                names.add(value)
            continue
        flag, has_equals, inline_value = token.partition("=")
        if flag in _SWITCH_CREATE_LONG_FLAGS:
            if has_equals:
                if inline_value:
                    names.add(inline_value)
                cursor += 1
                continue
            value, cursor = _take_flag_value(rest, cursor)
            if value is not None:
                names.add(value)
            continue
        cursor += 1
    return names


def _checkout_branch_names(segment: list[str], subcommand_index: int) -> set[str]:
    names: set[str] = set()
    rest = segment[subcommand_index + 1 :]
    cursor = 0
    while cursor < len(rest):
        # redirection の対象 token（`>-b` の `-b` 等）を 2 個目の flag と
        # 誤認しないよう、flag 判定の前に読み飛ばす（`_branch_names` /
        # `_has_unknown_branch_flag` と同じ扱い。PR #34 Copilot review 指摘）。
        skipped = _skip_redirection(rest, cursor)
        if skipped is not None:
            cursor = skipped
            continue
        token = rest[cursor]
        if token == "--":
            break
        cluster_value = _short_cluster_value(token, "bB")
        if cluster_value is not None:
            if cluster_value:
                names.add(cluster_value)
                cursor += 1
                continue
            value, cursor = _take_flag_value(rest, cursor)
            if value is not None:
                names.add(value)
            continue
        cursor += 1
    return names


_BRANCH_KNOWN_LONG_FLAGS = frozenset({"--copy", "--force"})
_BRANCH_KNOWN_SHORT_LETTERS = "cCfdDmM"


def _skip_redirection(tokens: list[str], cursor: int) -> int | None:
    """`tokens[cursor]` が redirection なら読み飛ばした後の cursor を返す。

    redirection でなければ `None`。`>` / `>&` 等の operator は右の対象 token ごと
    2 つ、`2>&1` の fd 番号（`2`）は operator を次に控える 1 つを進める。
    `_next_value_index` は同じ規則に `--` で打ち切る意味を重ねているため、
    `--` を end-of-options として読み飛ばす `branch` からは再利用できない。
    """
    token = tokens[cursor]
    if is_redirection_operator(token):
        return cursor + 2
    if (
        _is_potential_fd_token(token)
        and cursor + 1 < len(tokens)
        and is_redirection_operator(tokens[cursor + 1])
    ):
        return cursor + 1
    return None


def _strip_redirections(tokens: list[str]) -> list[str]:
    """redirection operator とその対象 token だけを取り除いた token 列を返す。

    gate 1 の site 判定（`_segment_creates_branch` 等）は raw token を直接
    走査するため、redirection の対象が flag と同じ見た目（例: `>-d`）だと
    実際には作成操作である segment を非作成と誤判定し、site 自体が収集
    されず guard を丸ごと迂回できる（`git branch codex/... >-d` は実 git が
    branch を作成するが `-d` が delete flag と誤認される。PR #34 Copilot
    review 指摘 Round 6、実測確認済み）。

    `_skip_redirection`（gate 2 用）が持つ「数字 fd（`2>...`）候補も読み飛ばす」
    ヒューリスティックはここでは使わない。gate 2 では token を読み飛ばすほど
    「真の候補に届く」ため fail-closed に働くが、gate 1 では token を読み飛ばす
    ほど `rest` が短くなり「作成操作ではない」判定に倒れるため方向が逆転する。
    `git branch 2 >/dev/null` のように branch 名そのものが数字だと、その唯一の
    positional を fd 宣言と誤認して除去すると site 収集自体が漏れる新規の
    fail-open regression になる（独立実装レビュー指摘、実測確認済み）。ここでは
    operator とその直後の対象 token のみを機械的に除去する。
    """
    result: list[str] = []
    cursor = 0
    while cursor < len(tokens):
        if is_redirection_operator(tokens[cursor]):
            cursor += 2
            continue
        result.append(tokens[cursor])
        cursor += 1
    return result


def _branch_names(segment: list[str], subcommand_index: int) -> set[str]:
    rest = segment[subcommand_index + 1 :]
    positionals: list[str] = []
    is_copy = False
    cursor = 0
    while cursor < len(rest):
        # redirection の fd 番号 / operator / 対象 file は positional ではない。
        # 読み飛ばさないと `git branch 2>/dev/null codex/...` の候補が `2` になり
        # sanitize / AC-7 のどれにも掛からず silent allow になる。
        skipped = _skip_redirection(rest, cursor)
        if skipped is not None:
            cursor = skipped
            continue
        token = rest[cursor]
        cursor += 1
        if token == "--":
            continue
        if token.startswith("-"):
            if _short_cluster_has(token, "cC") or token == "--copy":
                is_copy = True
            continue
        positionals.append(token)
    if not positionals:
        return set()
    return {positionals[-1]} if is_copy else {positionals[0]}


def _has_unknown_branch_flag(segment: list[str], subcommand_index: int) -> bool:
    rest = segment[subcommand_index + 1 :]
    cursor = 0
    while cursor < len(rest):
        # redirection の fd 番号 / operator / 対象 file は flag 判定の対象外。
        # 読み飛ばさないと、対象 file がたまたま `-` 始まり（`>-q` の `-q` 等）の
        # とき未知 flag と誤認し、AC-7(iii) の fallback を不要に発火させる
        # （`_branch_names` は既に `_skip_redirection` で同じ扱いをしている）。
        skipped = _skip_redirection(rest, cursor)
        if skipped is not None:
            cursor = skipped
            continue
        token = rest[cursor]
        cursor += 1
        # `--` は branch では end-of-options であり未知 flag ではない。
        if token == "--" or not token.startswith("-"):
            continue
        if token.startswith("--"):
            if token not in _BRANCH_KNOWN_LONG_FLAGS:
                return True
            continue
        if not all(letter in _BRANCH_KNOWN_SHORT_LETTERS for letter in token[1:]):
            return True
    return False


def _worktree_add_index(segment: list[str], git_index: int) -> int | None:
    for candidate in sorted(subcommand_candidates(segment, git_index + 1)):
        if segment[candidate] != "worktree":
            continue
        add_index = candidate + 1
        if add_index < len(segment) and segment[add_index] == "add":
            return add_index
    return None


def _short_cluster_value(token: str, letters: str) -> str | None:
    """短 option cluster から `letters` のいずれかより後ろの値を取り出す。

    `-fb<name>` のように他の短 option（`-f` 等）と結合していても、`letters`
    に含まれる最初の文字以降を値として扱う（`-fb codex/...` のように cluster
    内に値が無い場合は空文字列を返し、呼び出し側で次 token を値として扱う）。
    cluster 自体に該当文字が無ければ None を返す。long option（`--branch` 等）
    は対象外にする。`_short_cluster_has` と同じ cluster 判定基準を使う。
    """
    if not token.startswith("-") or token.startswith("--"):
        return None
    body = token[1:]
    for index, letter in enumerate(body):
        if letter in letters:
            return body[index + 1 :]
    return None


def _worktree_positionals_and_names(
    segment: list[str], add_index: int
) -> tuple[set[str], set[str]]:
    """`worktree add` 以降から positional（path / start-point）と `-b`/`-B` の値を抽出する。

    `switch`/`checkout`/`branch` 側の名前抽出（`_switch_branch_names` 等）と同じ
    `_skip_redirection` / `_take_flag_value` を再利用する。以前は `token.isdigit()`
    のみの簡易 fd 判定（named fd `{name}>...` 非対応）と、`-b` の分離値を
    redirection を読み飛ばさず次 token を無条件取得する自前実装を持っていたため、
    `git worktree add ... -b >/dev/null <name>` で `-b` の値が `>` に化けたり
    `git worktree add ... -b <name> {fd}>/dev/null` で `{fd}` が positional に
    混入したりして、implicit HEAD からの GDD worktree 作成が検出されない bypass に
    なっていた（独立実装レビュー指摘、実測確認済み）。
    """
    positionals: set[str] = set()
    names: set[str] = set()
    cursor = add_index + 1
    while cursor < len(segment):
        skipped = _skip_redirection(segment, cursor)
        if skipped is not None:
            cursor = skipped
            continue
        token = segment[cursor]
        cluster_value = _short_cluster_value(token, "bB")
        if cluster_value is not None:
            if cluster_value:
                names.add(cluster_value)
                cursor += 1
                continue
            value, cursor = _take_flag_value(segment, cursor)
            if value is not None:
                names.add(value)
            continue
        if not token.startswith("-"):
            positionals.add(token)
        cursor += 1
    return positionals, names


def _worktree_creates_gdd_branch(
    segment: list[str], git_index: int
) -> tuple[set[str], set[str]] | None:
    add_index = _worktree_add_index(segment, git_index)
    if add_index is None:
        return None
    positionals, names = _worktree_positionals_and_names(segment, add_index)
    if not names or not any(looks_like_gdd_task_branch(name) for name in names):
        return None
    return positionals, names


#: HEAD の bare 別名 revision（実測確認済み: git 2.50.1、いずれも HEAD と同一
#: コミットに解決する）。suffix 付きの形（`HEAD~0`/`HEAD^0`/`@{0}` 等）は
#: `_peel_noop_revision_suffixes` が正規化してからこの集合と照合するため、
#: ここには bare 形だけを持つ。
_HEAD_REVISION_ALIASES = frozenset({"HEAD", "@"})

_LOCAL_DEFAULT_BRANCH_NAMES = ("main", "master", "develop")

#: local default branch の bare 別名 revision（実測確認済み: git 2.50.1、いずれも
#: 対応する local branch と同一コミットに解決する）。suffix 付きの形
#: （`main@{0}` 等）は `_peel_noop_revision_suffixes` が正規化してから照合する。
_LOCAL_DEFAULT_BRANCH_REVISION_ALIASES = frozenset(
    alias
    for name in _LOCAL_DEFAULT_BRANCH_NAMES
    for alias in (name, f"refs/heads/{name}", f"heads/{name}")
)

#: git revision 構文の恒等（no-op）suffix 1 個分。`~<0 のみからなる桁列>`
#: （0 世代祖先 = 自分自身。git は `~00`/`~000` も `~0` と同じ整数 0 として
#: パースする。`~` 単体や `~1` 以降は親コミットへ移動するため対象外）、
#: `^<0 のみからなる桁列>`（0 番目の親 = 自分自身。同様に `^00` 等も対象。
#: `^1` 等は対象外）、`^{}`/`^{commit}`/`^{object}`（tag の recursive
#: dereference / type-peel。commit に対してはいずれも no-op。`^{tree}`/
#: `^{tag}` は別オブジェクトに解決するため対象外）、`@{<reflog 指定子>}`
#: （reflog エントリの参照。`@{0}`/`@{00}` のような数字だけでなく、
#: `@{now}`/`@{yesterday}`/`@{1.second.ago}` のような approxdate も
#: reflog が変化していなければ現在値と同一コミットに解決する
#: — gitrevisions(7) 参照）の 4 種類。ただし `@{upstream}`/`@{u}`/
#: `@{push}` は reflog の過去値ではなく**別 ref**（configured upstream /
#: push target）を指す特殊構文であり no-op ではないため、否定先読みで
#: 明示的に除外する（`main@{upstream}` を `main` の別名として誤分類すると、
#: 実際には `origin/main` 相当の安全な ref を local `main` として誤 deny
#: しうる）。この除外は大文字小文字を区別せずに行う（`(?i:...)` の
#: scoped inline flag）。git 自身が `@{upstream}`/`@{u}`/`@{push}` の
#: キーワードマッチを大文字小文字を区別せずに行うため（実測確認済み:
#: git 2.50.1、`git rev-parse 'main@{upstream}'` / `'main@{UPSTREAM}'` /
#: `'main@{U}'` / `'main@{Upstream}'` はいずれも同一の upstream 側コミットに
#: 解決する）、除外側を case-sensitive のままにすると `main@{UPSTREAM}` の
#: ような大文字小文字違いが除外に失敗して no-op として誤って剥がされ、
#: `main` に正規化された結果 local default branch 由来として誤って deny
#: される（独立レビュー指摘、マージ後の追加独立検証で発見）。scoped
#: inline flag を使うのは、`\^\{(?:commit|object)?\}` 側まで
#: 大文字小文字無視にしてしまわないため（`^{COMMIT}`/`^{Object}` は git が
#: 大文字小文字を区別してエラーにする、実測確認済み: git 2.50.1、rc=128）。
#: 実測確認済み: git 2.50.1、`git rev-parse HEAD` と `git rev-parse
#: 'HEAD~0~0'` / `git rev-parse 'HEAD~00'` / `git rev-parse 'HEAD^{}'` /
#: `git rev-parse 'HEAD^{commit}'` / `git rev-parse 'main~0'` /
#: `git rev-parse '@{now}'` はいずれも同一 SHA に解決し、`git worktree add
#: <path> -b <name> 'HEAD~0~0'`（`'HEAD~00'`/`'HEAD^{commit}'`/`main~0`/
#: `@{now}` も同様）は実際に成功して該当コミットへ checkout する。一方
#: `git rev-parse '@{upstream}'` は upstream 未設定なら別のエラーで失敗し、
#: 設定済みでも upstream 側のコミットに解決するため、local ref の no-op
#: suffix として扱ってはならない。
#:
#: 本リストはなお git revision 構文の**列挙**であり、ここに挙げていない
#: no-op 相当の構文（将来 git が追加しうる新しい別名構文を含む）を網羅する
#: ことは主張しない（独立セルフレビュー Round 2/3 指摘）。既知の bypass
#: （文字列リテラル一致 → suffix 1 個の有限集合 → suffix chain の有限集合
#: → reflog 数字限定の有限集合）が発見されるたびにこの集合を拡張する
#: 運用になる。
#:
#: `^{}`/`^{commit}`/`^{object}` は case-sensitive（git は `^{COMMIT}` を
#: 無効な revision として拒否する、実測確認済み: git 2.50.1、rc=128）。
_NOOP_CARET_BRACE_SUFFIXES = ("^{}", "^{commit}", "^{object}")

#: `@{...}` の中身がこれらのキーワード（大文字小文字を問わず）のとき、
#: reflog の過去値ではなく**別 ref**（configured upstream / push target）を
#: 指す特殊構文であり no-op ではないため、no-op suffix として剥がしては
#: ならない（`main@{upstream}` を `main` の別名として誤分類すると、実際には
#: `origin/main` 相当の安全な ref を local `main` として誤 deny しうる）。
#: git 自身がこのキーワードマッチを大文字小文字を区別せずに行うため
#: （実測確認済み: git 2.50.1、`git rev-parse 'main@{upstream}'` /
#: `'main@{UPSTREAM}'` / `'main@{U}'` / `'main@{Upstream}'` はいずれも同一の
#: upstream 側コミットに解決する）、比較も大文字小文字を区別せずに行う
#: （独立レビュー指摘、マージ後の追加独立検証で発見。修正前は case-sensitive
#: な比較だったため `main@{UPSTREAM}` が no-op として誤って剥がされ `main`
#: に正規化された結果、local default branch 由来として誤って deny されて
#: いた）。
_NOOP_REFLOG_EXCLUDED_KEYWORDS = frozenset({"upstream", "u", "push"})


def _peel_one_noop_suffix_end(token: str, end: int) -> int | None:
    """`token[:end]` 末尾の no-op suffix を高々 1 個だけ剥がした後の終端
    位置を返す。剥がせる suffix が無ければ `None` を返す。

    `token` 自体はスライスしない（呼び出し側が `end` を更新しながら
    ループすることで、chain 全体を剥がし切るまで文字列コピーを発生させ
    ない。過去に採用していた「正規表現の `atom+\\Z` を 1 回の `re.sub` で
    一括除去する」実装は、chain の**末尾**が `_NOOP_REFLOG_EXCLUDED_KEYWORDS`
    で除外される atom（`@{upstream}` 等）で終わる token に対して `\\Z` に
    到達できるマッチが存在せず、正規表現エンジンが全開始位置から
    バックトラックするため O(N^2) になることが独立レビューで発覚した
    （`"HEAD" + "@{0}" * 8000 + "@{U}"` と `"@{0}" * 16000 + "@{U}"` で測ると、
    どちらも数秒以上かかり、N を 2 倍で時間が約 4 倍になって O(N^2) と一致した）。suffix 種別ごとに文字列末尾からの直接インデックス
    走査で判定するこの実装は、1 回の呼び出しあたり剥がす（または剥がせ
    ないと判定する）suffix の長さに比例したコストのみで完了するため、
    chain 全体を通してのトータルコストは O(N) になる。
    """
    if end > 0 and token[end - 1] == "0":
        idx = end
        while idx > 0 and token[idx - 1] == "0":
            idx -= 1
        if idx > 0 and token[idx - 1] in "~^":
            return idx - 1

    for suffix in _NOOP_CARET_BRACE_SUFFIXES:
        suffix_len = len(suffix)
        if end >= suffix_len and token[end - suffix_len : end] == suffix:
            return end - suffix_len

    if end > 0 and token[end - 1] == "}":
        idx = end - 2
        while idx >= 0 and token[idx] not in "{}":
            idx -= 1
        if idx >= 1 and token[idx] == "{" and token[idx - 1] == "@":
            inner = token[idx + 1 : end - 1]
            if inner.lower() not in _NOOP_REFLOG_EXCLUDED_KEYWORDS:
                return idx - 1

    return None


def _peel_noop_revision_suffixes(token: str) -> str:
    """`token` 末尾の no-op suffix chain を剥がす。

    `~0`/`^0`/`^{}`/`@{0}`（桁違い・type-peel 変種を含む）は任意の順序・
    任意回数チェーンできる（`HEAD~0^0^{}@{0}~0` も HEAD と同一コミットに
    解決する）。有限個の suffix 付き文字列を alias 集合に列挙する設計は、
    この chaining が無限に文字列バリエーションを生成できるため原理的に
    塞ぎきれない（独立セルフレビュー指摘、PR #40 merge 後）。

    `@{0}` 系は他と異なり、先行 rev を省略できる（`@{0}` 単体で
    `HEAD@{0}` と同義、実測確認済み: git 2.50.1、rc=0 で HEAD と同一 SHA。
    一方 `~0`/`^0`/`^{}` は単体では無効な revision になる、実測確認済み:
    git 2.50.1、rc=1）。剥がした結果が空文字列になりうるのは `@{0}` 系を
    含む chain が token 全体を消費した場合であり、その場合は省略された
    rev の既定値である `@`（HEAD の別名）に読み替える（`~0`/`^0`/`^{}`
    のみの chain が token 全体を消費するのは、その token 自体がそもそも
    無効な revision だった場合に限るため、`@` への読み替えは deny 方向
    にしか作用しない = fail-closed で安全側）。
    """
    end = len(token)
    while True:
        new_end = _peel_one_noop_suffix_end(token, end)
        if new_end is None:
            break
        end = new_end
    peeled = token[:end]
    return peeled or "@"


def repo_core_ignorecase(cwd: Path) -> bool:
    """`git config --type=bool --get core.ignorecase` を読む。

    git はリポジトリ初期化時にファイルシステムの実際の大文字小文字区別性を検出して
    この値を自動設定する（macOS の既定 APFS や Windows の既定 NTFS では `true`）。
    `true` の場合のみ、base-ref の alias 比較を大文字小文字無視にする。`--type=bool`
    を付けずに `--get` だけで読むと、設定ファイルに書かれた値がそのまま返り git 自身の
    boolean 正規化を経由しない（実測確認済み: git 2.50.1、`git config core.ignorecase
    True` を設定したリポジトリで `git config --get core.ignorecase` は `"True"`
    （大文字のまま）を返すが、`git config --type=bool --get core.ignorecase` は
    正規化済みの `"true"` を返す）。`--type=bool` を使わないと、`True`/`1`/`yes`/`on`
    のような git 自身は truthy として扱う表記が `== "true"` の単純な文字列一致に
    掛からず、この gate が塞ごうとしている case-folding bypass を再び通してしまう
    （独立セルフレビュー指摘、実測確認済み）。`git config` が読めない・未設定の場合は
    case-sensitive な多数派環境を想定して `False` 扱いに倒す（他の `git_output` 呼び
    出し— `root_state_blocks` / `is_linked_worktree` —と同じ「読めなければ
    安全側のデフォルトに倒す」方針に揃える）。

    既知の限界（独立セルフレビュー指摘）: この判定は `core.ignorecase` という
    **設定値**を読むものであり、実行時にファイルシステムの実際の大文字小文字区別性を
    直接プローブするものではない。`core.ignorecase` は `git init` 時にファイルシステム
    の実際の挙動を検出して自動設定される値だが、その後に明示的に上書きされたり
    （`git config core.ignorecase false` 等）、リポジトリが異なる大文字小文字区別性の
    ファイルシステム間で移動された場合は、設定値と実際の挙動が乖離しうる。実際の
    プローブ（一時ファイルを作成し大文字化したパスで読めるか検査する等）は、この
    hook が Bash/Shell コマンドごとに同期実行される PreToolUse hook であることを
    踏まえるとコストが増すため採用しなかった。
    """
    return (
        git_output(
            ["git", "config", "--type=bool", "--get", "core.ignorecase"], cwd
        )
        == "true"
    )


def _positionals_match_alias_after_peeling(
    positionals: set[str], aliases: frozenset[str], *, ignorecase: bool
) -> bool:
    peeled = {_peel_noop_revision_suffixes(candidate) for candidate in positionals}
    if ignorecase:
        folded_aliases = {alias.casefold() for alias in aliases}
        return any(candidate.casefold() in folded_aliases for candidate in peeled)
    return any(candidate in aliases for candidate in peeled)


def command_creates_gdd_worktree_from_head(
    segments: list[list[str]], cwd: Path
) -> bool:
    # `repo_core_ignorecase` は `git config` を叩く subprocess 呼び出しであり、
    # このガードは Bash/Shell コマンドごとに同期実行される PreToolUse hook である
    # ため、alias 比較（`len(positionals) <= 1` の即 True 判定に掛からない場合）に
    # 実際に必要になるまで計算を遅延させ、計算後は同一呼び出し内でキャッシュする
    # （独立セルフレビュー指摘: 無条件に関数先頭で計算すると、worktree add 以外の
    # 大半の git コマンドでも無駄な subprocess 呼び出しが発生する。`git status` 相当の
    # コマンドで測ると、レイテンシがはっきり増えた）。
    ignorecase: bool | None = None
    for segment in segments:
        for index, token in enumerate(segment):
            if not is_git_token(token):
                continue
            result = _worktree_creates_gdd_branch(segment, index)
            if result is None:
                continue
            positionals, _names = result
            if len(positionals) <= 1:
                return True
            if ignorecase is None:
                ignorecase = repo_core_ignorecase(cwd)
            if _positionals_match_alias_after_peeling(
                positionals, _HEAD_REVISION_ALIASES, ignorecase=ignorecase
            ):
                return True
    return False


def command_creates_gdd_worktree_from_local_default(
    segments: list[list[str]], cwd: Path
) -> bool:
    # 遅延評価 + キャッシュの理由は `command_creates_gdd_worktree_from_head` と同じ。
    ignorecase: bool | None = None
    for segment in segments:
        for index, token in enumerate(segment):
            if not is_git_token(token):
                continue
            result = _worktree_creates_gdd_branch(segment, index)
            if result is None:
                continue
            positionals, _names = result
            if ignorecase is None:
                ignorecase = repo_core_ignorecase(cwd)
            if _positionals_match_alias_after_peeling(
                positionals, _LOCAL_DEFAULT_BRANCH_REVISION_ALIASES, ignorecase=ignorecase
            ):
                return True
    return False


def looks_like_gdd_task_branch(command: str) -> bool:
    return bool(GDD_TASK_BRANCH_RE.search(command))


def _site_branch_names(
    segment: list[str], subcommand_index: int, subcommand: str
) -> set[str]:
    if subcommand == "switch":
        return _switch_branch_names(segment, subcommand_index)
    if subcommand == "checkout":
        return _checkout_branch_names(segment, subcommand_index)
    return _branch_names(segment, subcommand_index)


def root_branch_name_candidates(segments: list[list[str]]) -> tuple[set[str], bool]:
    names: set[str] = set()
    fallback_required = False
    for segment, subcommand_index, subcommand in _root_branch_creation_sites(segments):
        raw_names = _site_branch_names(segment, subcommand_index, subcommand)
        site_names = _sanitize_candidates(raw_names)
        if (
            not site_names
            or any(_is_unexpanded_token(name) for name in site_names)
            or (
                subcommand == "branch"
                and _has_unknown_branch_flag(segment, subcommand_index)
            )
        ):
            fallback_required = True
        names |= site_names
    return names, fallback_required


def _creates_gdd_named_branch(segments: list[list[str]], command: str) -> bool:
    names, fallback_required = root_branch_name_candidates(segments)
    if fallback_required:
        return looks_like_gdd_task_branch(command)
    return any(looks_like_gdd_task_branch(name) for name in names)


def _creates_without_cwd(command: str) -> bool:
    """root branch の作成か GDD 名の worktree add を含むか（cwd を使わない。判定できなければ True）。

    parser が無いときは、`git` の語に当たるものすべてを作るものとみなす。
    """
    if not PARSER_AVAILABLE:
        return bool(_GIT_WORD_RE.search(command))
    try:
        segments = split_segments(command)
        if _root_branch_creation_sites(segments):
            return True
        return any(
            _worktree_creates_gdd_branch(segment, index) is not None
            for segment in segments
            for index, token in enumerate(segment)
            if is_git_token(token)
        )
    except Exception:  # noqa: BLE001
        return True


def main() -> int:
    # コマンドを取り出せない壊れた payload は、JSON でないときと同じく通す（harness は作らない）。
    try:
        payload = json.load(sys.stdin)
    except ValueError:  # JSONDecodeError と UnicodeDecodeError
        return emit_allow()
    if not isinstance(payload, dict):
        return emit_allow()

    tool_name = str(payload.get("tool_name", ""))
    if tool_name not in {"Bash", "Shell", "exec_command"}:
        return emit_allow()

    command = extract_command(payload)
    if not command:
        return emit_allow()

    if "git" not in command:
        return emit_allow()

    # 作業ディレクトリを解けないときは、cwd を使わずに決められる「作る」コマンドだけを止める。
    try:
        cwd = extract_cwd(payload)
    except Exception as exc:  # noqa: BLE001
        if _creates_without_cwd(command):
            return emit_deny_unresolved_cwd(command, exc)
        return emit_allow()

    if not PARSER_AVAILABLE:
        if _GIT_WORD_RE.search(command):
            return emit_deny_parser_unavailable(command, cwd)
        return emit_allow()

    try:
        segments = split_segments(command)

        if command_creates_gdd_worktree_from_head(segments, cwd):
            return emit_deny_head_worktree(command, cwd)
        if command_creates_gdd_worktree_from_local_default(segments, cwd):
            return emit_deny_local_base_worktree(command, cwd)

        if not command_creates_root_branch(segments):
            return emit_allow()

        gdd_named = _creates_gdd_named_branch(segments, command)
        current_session = payload_session_id(payload)
        # 実行先（`git -C`・先行する `cd`）も cwd と同じ条件で見る。どれか 1 つで止める。
        for target in (cwd, *root_branch_exec_targets(segments, cwd)):
            if (root_state_blocks(target, current_session) or gdd_named) and not is_linked_worktree(target):
                return emit_deny(command, target)
    except Exception:  # noqa: BLE001
        return emit_deny(command, cwd)

    return emit_allow()


if __name__ == "__main__":
    raise SystemExit(main())
