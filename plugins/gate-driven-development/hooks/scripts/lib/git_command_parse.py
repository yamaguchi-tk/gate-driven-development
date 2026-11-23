#!/usr/bin/env python3
"""汎用 git コマンド解析: token化・セグメント分割・global option の arity 解決。

design.md § 変更点の要約 item 1（ADR-1 / ADR-2）により、
`push_command_parse.py`（pre-push gate 固有ロジック）と
`validate-worktree-command.py`（root branch / GDD worktree guard）の
双方が import する git コマンド解析の正本。

import は flat（`from git_command_parse import ...`）に固定する（ADR-2）。
`hooks/scripts/lib` と `scripts/lib` は同名パッケージ `lib` であり、
`from lib.X import` は import 順序に依存して落ちることが本 repo で
実測記録済みのため、この module を `from lib.git_command_parse import`
で読もうとしないこと。
"""
from __future__ import annotations

import bisect
import os
import sys
from pathlib import Path

try:
    from . import shell_lexer
except ImportError:  # hook と多くのテストは lib を sys.path に入れて top-level の module として読む
    _DIR = str(Path(__file__).resolve().parent)
    sys.path.insert(0, _DIR)
    try:
        import shell_lexer
    finally:
        sys.path.remove(_DIR)

#: 生の改行に対応する token。design.md § opt-out 受理面の機械定義 item 1 の
#: 「改行 token」はこれを指す（行継続由来の改行は token を残さず除去される）。
NEWLINE_TOKEN = "\n"

#: コマンドの切れ目を作る token。`shlex(punctuation_chars=True)` は隣接する
#: punctuation を 1 token に集約するため `&&` / `||` もそのまま現れる。
COMMAND_SEPARATOR_TOKENS = frozenset(
    {NEWLINE_TOKEN, ";", ";;", "&", "&&", "|", "||", "|&", "(", ")"}
)

#: `shlex(punctuation_chars=True)` が 1 token に集約する対象文字（`shlex` の
#: 既定 `punctuation_chars` 値そのもの）。この文字だけで構成される token は
#: `token_ends_with_separator` の判定でだけ、実 bash の演算子境界まで
#: 再分割して解釈する（token 列そのものは一切変更しない。理由は同関数の
#: docstring を参照）。
_PUNCTUATION_CHARS = frozenset("();<>|&")

#: 2 文字演算子。ここに無い組み合わせは 1 文字ずつの演算子として切り出す
#: （tuple だが membership 判定にしか使わないため順序自体に意味は無い）。
#: **完全性には依存しない**設計にしている:
#: `token_ends_with_separator` は「コマンド先頭判定」専用の局所的な再解釈
#: であり、その唯一の呼び出し元 `push_command_parse.is_git_push_at_command_start`
#: は nudge hook 専用（block しない）。ここに無い演算子（`&>>`/`>|` 等）を
#: 誤って 1 文字ずつに割ってしまっても、影響は「push 検出（nudge）が過剰/
#: 過小に反応しうる」だけに留まる（token 列そのものは `_lex_segment` で
#: 変わらないため、segment 分割や refspec 走査など block する guard 側、
#: および `find_optout`/`_find_cd_root`（pre-push gate と共有、`token in
#: separators` の完全一致のみ使う）は無傷。PR #88 独立レビュー round 7
#: 指摘 High: 当初この分割を `_lex_segment` で token 列全体に適用しており、
#: `&>` が `&`+`>` に割れて `validate-worktree-command.py` の segment 分割
#: （block する guard）が退行していた。PR #88 人間レビュー round 6 指摘
#: High: round 7 の是正コミットは docstring 上「token 列は変更しない」と
#: 主張しながら実装は変更しておらず、同じ退行が残っていた。是正は
#: `_lex_segment` を実際に無変更へ戻し、`find_optout`/`_find_cd_root` を
#: 本関数から切り離すことで、pre-push gate 側は本定数の完全性に一切依存しない
#: 設計にした）。
_TWO_CHAR_OPERATORS = ("&&", "||", ";;", "|&", "<<", ">>", "<&", ">&", "<>", "&>")


def _split_glued_punctuation(token: str) -> list[str]:
    """`token` が punctuation だけで構成されるなら、実 bash の演算子境界まで
    貪欲に再分割する。それ以外（通常の word token）はそのまま 1 要素で返す。

    呼び出し元は `token_ends_with_separator` に限定する（token 列全体には
    適用しない。理由は同関数の docstring を参照）。
    """
    if not token or any(ch not in _PUNCTUATION_CHARS for ch in token):
        return [token]
    result: list[str] = []
    index = 0
    while index < len(token):
        pair = token[index : index + 2]
        if pair in _TWO_CHAR_OPERATORS:
            result.append(pair)
            index += 2
        else:
            result.append(token[index])
            index += 1
    return result


def token_ends_with_separator(token: str, separators: frozenset[str]) -> bool:
    """`token` が（単体か、末尾の分割後演算子として）`separators` に属するか。

    `shlex(punctuation_chars=True)` は `)` と `;` が空白無しで隣接すると
    `");"` という 1 token に無条件で集約する。`separators` との完全一致
    だけを見ると、`(cd /repo); git push` のように区切りが空白無しで連続
    する形は「区切りではない未知 token」として扱われ、直後の `git push`
    が command-start と判定されなくなる（PR #88 人間レビュー round 5
    指摘 Medium: nudge の取りこぼし＝fail-open）。

    この判定は `push_command_parse._at_true_command_start`（呼び出し元は
    `is_git_push_at_command_start` に限定。nudge hook 専用、block しない）
    の「コマンド先頭」判定**専用**に token の末尾だけを局所的に再解釈する
    ものであり、`_lex_segment` の token 列そのものは変更しない。

    token 列全体を再分割すると、`&>` のような複合 redirection 演算子が
    `&`（区切り）+ `>` に割れ、segment 分割に依存する block する guard
    （root-branch guard 等）まで巻き込んで受理集合を緩めてしまう（PR #88
    独立レビュー round 7 指摘 High/blocking で実測: `git switch
    &>/dev/null -c <branch>` が deny → allow に退行した）。

    同じ理由で `find_optout` / `_find_cd_root`（pre-push gate である
    run-pre-push-gate-hook.sh と共有）もこの関数を使わない: 過検出（実際
    には立っていない opt-out を受理する、実在しない cd 先を root candidate
    にする）がそのまま pre-push gate の fail-open に直結するため、`token in
    separators` の完全一致に留める（PR #88 人間レビュー round 6 指摘 High:
    `>|GDD_SKIP_PRE_PUSH_GATE=1 git push` は実 bash では `>|` が redirect
    演算子としてファイル名 `GDD_SKIP_PRE_PUSH_GATE=1` を消費するだけで
    環境変数は立たないが、この関数で `>|` を `>` + `|` に再分割すると
    末尾の `|` が区切りに一致し、立っていない opt-out を受理していた）。

    command-start 判定（nudge 検出）はもともと「過剰検出は fail-safe 側」
    という設計のため、ここだけ局所的に広げても block 側への影響は無い —
    ただしそれは **この関数の呼び出し元を nudge 専用に保つ場合に限る**。
    """
    if isinstance(token, shell_lexer.QuotedWord):
        # 引用符・エスケープ由来の演算子文字は区切りではない（bash の読み）。
        return False
    if token in separators:
        return True
    pieces = _split_glued_punctuation(token)
    return len(pieces) > 1 and pieces[-1] in separators

def is_unquoted_separator(token: str, separators: frozenset[str]) -> bool:
    """`token` が `separators` に完全一致し、引用符・エスケープ由来（`QuotedWord`）でないか。"""
    return token in separators and not isinstance(token, shell_lexer.QuotedWord)

#: nested shell 展開の対象。`-c <command-string>` を持つ POSIX 系 shell。
NESTED_SHELL_NAMES = shell_lexer.SHELL_INTERPRETERS

#: 展開の反復上限（`bash -c 'bash -c "..."'` のような多段を有限回で追う）。
_MAX_NESTED_SHELL_DEPTH = 5

#: git global option のうち、**分離引数を消費する**もの。
#: 用途は「`git <flag> push` の push を subcommand と誤認しない」精度確保だけであり、
#: この集合の**完全性には依存しない**（未知 flag は両 arity を候補にする）。
#: 各メンバが実 git でも分離引数を消費することは
#: `tests/test_push_command_parse.py::GitGlobalFlagArityTests` が実 git に
#: 問い合わせて検証する（synopsis のような二次情報を正本にしない）。
GIT_GLOBAL_FLAGS_WITH_ARGUMENT = frozenset(
    {
        "-C",
        "-c",
        "--git-dir",
        "--work-tree",
        "--namespace",
        "--config-env",
        "--attr-source",
        "--shallow-file",
    }
)


#: 密着した fd 番号のうち、落とす桁数。bash と zsh で読みが一致する 1 桁だけを落とす（`2>&1` の `2`）。
#: 2 桁以上（`12>x`）は bash が fd、zsh が語と読むので、語として残して止める側に倒す（root-branch
#: guard の候補に入る）。
_FD_DIGITS = 1


def _lex_segment(segment: str) -> list[str]:
    """1 行分を shlex で token 化する（失敗時は空白と区切り記号で割る fallback）。

    行ごとの読み（`_lex_by_line`）だけが使う。`commenters` は空（語中の `#` をコメントにしない）。
    fallback でも区切り記号の連を別の token に割る（`2>&1|tail` を 1 token に残すと、
    `classify_refspec` が 2 つ目の refspec と読んで ambiguous を返す）。
    """
    return shell_lexer.split_words(segment)[0]


def _strip_line_continuations(command: str) -> str:
    """行継続（**エスケープされていない** `\\` + 改行）だけを除去する（引用符は見ない）。

    行末の連続バックスラッシュが奇数個のときだけ行継続にする。偶数個ならすべてリテラルで、
    続く改行はコマンドの区切りとして残る。
    """
    result: list[str] = []
    index = 0
    while index < len(command):
        if command[index] != "\\":
            result.append(command[index])
            index += 1
            continue
        run = 0
        while index + run < len(command) and command[index + run] == "\\":
            run += 1
        if run % 2 == 1 and command.startswith("\n", index + run):
            result.append("\\" * (run - 1))
            index += run + 1
            continue
        result.append("\\" * run)
        index += run
    return "".join(result)


def _lex_by_line(command: str) -> list[str]:
    """改行ごとに分けて 1 行ずつ割る読み（引用符を行をまたいで追わず、語頭の `#` も落とさない）。

    縮退したとき（`_lex_checked` の縮退）に、push の検出の和を取るためだけに使う
    （`tokenize_with_boundary`）。行継続だけを処理する。
    """
    tokens: list[str] = []
    for index, segment in enumerate(_strip_line_continuations(command).split("\n")):
        if index:
            tokens.append(NEWLINE_TOKEN)
        tokens.extend(_lex_segment(segment))
    return tokens


#: heredoc の本文を別のコマンドとして読む再帰の上限。超えた本文は行ごとの読みに倒し、縮退を返す。
_MAX_HEREDOC_BODY_DEPTH = 32


def _lex_checked(command: str, depth: int = 0) -> tuple[list[str], bool]:
    """bash の読みで token 化し、`(tokens, 縮退したか)` を返す。

    heredoc の本文を先に取り出して、introducer の行とは別のコマンドとして末尾に足す（本文の
    アポストロフィで引用符を対にして、後ろの `git push` を飲まないため。本文はデータでも今までどおり
    読む）。残りは字句解析の芯（`shell_lexer.lex`）で割る: 行継続を bash の規則で消し、語頭コメントを
    落とし、引用符の外の改行を `NEWLINE_TOKEN` にし（複数行の commit メッセージの後ろの
    `&& git push` を引用符の中と読まない）、密着した 1 桁の fd 番号を落とす。退避先を使い切ったときは
    行ごとの読みに倒して縮退を返す（例外で guard を落とさない）。本文の入れ子が
    `_MAX_HEREDOC_BODY_DEPTH` を超えたら、その本文も行ごとの読みに倒して縮退を返す。
    """
    if depth > _MAX_HEREDOC_BODY_DEPTH:
        return _lex_by_line(command), True
    stripped, bodies = _extract_executed_heredoc_bodies(command, keep_data=True)
    try:
        tokens, degraded = shell_lexer.lex(stripped, NEWLINE_TOKEN, _FD_DIGITS)
    except ValueError:
        tokens, degraded = _lex_by_line(stripped), True
    for body in bodies:
        body_tokens, body_degraded = _lex_checked(body, depth + 1)
        tokens += [NEWLINE_TOKEN, *body_tokens]
        degraded = degraded or body_degraded
    return tokens, degraded


def _lex(command: str) -> list[str]:
    """`_lex_checked` の token 列。"""
    return _lex_checked(command)[0]


def find_git_subcommand(tokens: list[str], name: str) -> int:
    """`git` token（basename 一致）のうち、subcommand の候補に `name` があるものの index。無ければ -1。"""
    for index, token in enumerate(tokens):
        if is_git_token(token) and any(
            tokens[candidate] == name for candidate in subcommand_candidates(tokens, index + 1)
        ):
            return index
    return -1


def tokenize_with_boundary(command: str) -> tuple[list[str], int]:
    """`tokenize` と同じ token 列に加えて、原文 token 列の長さを返す。

    戻り値は `(tokens, original_token_count)`。`tokens[original_token_count:]`
    は nested shell 展開由来の token であり、design.md § opt-out 受理面の機械定義
    item 4（「原文 token 列の長さ以上の index は受理しない」）の境界値になる。
    受理面を別 tokenizer（`shlex.split`）の再計算に依存させないため、境界値は
    必ずこの関数から取得する（`shlex.shlex(punctuation_chars=True)` と
    `shlex.split` では `echo hi; git push` の token 数が 5 / 4 でずれる）。
    """
    try:
        tokens, degraded = _lex_checked(command)
    except Exception:  # noqa: BLE001 - 芯が読めない入力でも guard を落とさず、行ごとの読みに倒す
        tokens, degraded = _lex_by_line(command), True
    # 引用符が末尾まで閉じない（bash は前の行まで実行し、zsh は何も実行しない）ときは、行ごとの読みでも
    # push を探す。検出は 2 つの読みの和にし、opt-out・root・refspec は検出した側の読みで決める。
    if degraded and find_git_subcommand(_expand_nested_shell_tokens(tokens), "push") < 0:
        by_line = _lex_by_line(command)
        if find_git_subcommand(_expand_nested_shell_tokens(by_line), "push") >= 0:
            tokens = by_line
    return _expand_nested_shell_tokens(tokens), len(tokens)


def tokenize(command: str) -> list[str]:
    """shlex token化 + nested shell 展開（bash / sh / zsh / dash / ksh の `-c`、`eval`）。

    展開された token は末尾へ append する
    （既存 `run-pre-pr-gate-hook.sh:expand_nested_shell_tokens` と同じ位置規約）。
    原文 token 列の境界が必要な呼び出し側は `tokenize_with_boundary` を使う。
    """
    return tokenize_with_boundary(command)[0]


def _is_short_option_cluster(token: str) -> bool:
    """`-c` / `-lc` のような短 option cluster か（`--norc` 等の long option は除く）。"""
    return (
        len(token) > 1
        and token.startswith("-")
        and not token.startswith("--")
        and token[1:].isalpha()
    )


def _dash_c_argument_index(source_tokens: list[str], start: int) -> int | None:
    """`-c` を含む短 option cluster を探し、その引数の index を返す。無ければ None。

    long option（`--norc` / `--posix`）は `c` を含んでも対象外にする。含めると
    `bash --norc -c '<command>'` で `--norc` の次 token を command string と誤認し、
    本来の command string が展開されない。`-c -- '<command>'` の `--` は読み飛ばす。
    """
    for cursor in range(start, len(source_tokens)):
        token = source_tokens[cursor]
        if token in COMMAND_SEPARATOR_TOKENS:
            return None
        if not _is_short_option_cluster(token) or "c" not in token[1:]:
            continue
        argument = cursor + 1
        while argument < len(source_tokens) and source_tokens[argument] == "--":
            argument += 1
        return argument if argument < len(source_tokens) else None
    return None


def _nested_shell_commands(source_tokens: list[str]) -> list[str]:
    """`source_tokens` から nested shell / eval が実行するコマンド文字列を返す
    （`bash -c '<cmd>'` / `eval '<cmd>'` の `<cmd>`。`gh_command_parse` と同名）。

    `tokenize` 経路は `_expand_once_grouped` でこれを lex するだけだが、
    `split_segments` 経路は各文字列を独立コマンドとして再帰処理する（ADR-5）。
    """
    commands: list[str] = []
    for index, token in enumerate(source_tokens):
        name = os.path.basename(token)
        if name == "eval":
            argument = index + 1 if index + 1 < len(source_tokens) else None
        elif name in NESTED_SHELL_NAMES:
            argument = _dash_c_argument_index(source_tokens, index + 1)
        else:
            continue
        if argument is not None:
            commands.append(source_tokens[argument])
    return commands


def _expand_once_grouped(source_tokens: list[str]) -> list[list[str]]:
    """`source_tokens` から nested shell / eval の中身を **グループ単位** で返す。

    `_expand_once` は本関数の平坦化版（tokenize の挙動を変えないため）。
    """
    return [_lex(command) for command in _nested_shell_commands(source_tokens)]


def _expand_once(source_tokens: list[str]) -> list[str]:
    """`_expand_once_grouped` を平坦化する（`tokenize` の挙動を維持する）。"""
    produced: list[str] = []
    for group in _expand_once_grouped(source_tokens):
        produced.extend(group)
    return produced


def _expand_nested_shell_tokens(source_tokens: list[str]) -> list[str]:
    """多段の nested shell を有限回（`_MAX_NESTED_SHELL_DEPTH`）まで展開する。"""
    expanded = list(source_tokens)
    frontier = source_tokens
    for _ in range(_MAX_NESTED_SHELL_DEPTH):
        produced = _expand_once(frontier)
        if not produced:
            break
        expanded.extend(produced)
        frontier = produced
    return expanded


def is_redirection_operator(token: str) -> bool:
    """shell のリダイレクト演算子 token か（`>` `>>` `2>&1` の `>&` `&>` `<` 等）。

    `_lex` は `punctuation_chars=True` の shlex なので `<>&|` の連続を 1 token に
    まとめる。純粋な区切り（`|` `||` `&` `&&` `|&`）は COMMAND_SEPARATOR_TOKENS で
    先に処理されるため、ここへ来る punctuation token のうち `>` / `<` を含むものは
    リダイレクトに限られる。リダイレクトは push 対象 ref を変えないので、
    refspec の数え上げから除外する。

    公開契約（他 module から import してよい public symbol）: `push_command_parse.py`
    / `validate-worktree-command.py` はこの名前で import する。旧 `_is_redirection_operator`
    は後方互換のための薄い alias として残す。
    """
    return bool(token) and all(c in "<>&|" for c in token) and (">" in token or "<" in token)


#: 後方互換 alias（旧 private 名）。新規 import 先はこちらを使わないこと。
_is_redirection_operator = is_redirection_operator


def is_git_token(token: str) -> bool:
    """token が `git` 呼び出しか（basename 一致。`/usr/bin/git` 等も拾う）。"""
    return os.path.basename(token) == "git"


#: 分離引数を**消費しない**ことが実 git 2.50.1 への問い合わせで検証済みの
#: git global option。`tests/test_push_command_parse.py::
#: GitGlobalFlagsWithoutArgumentTests` が oracle。
GIT_GLOBAL_FLAGS_WITHOUT_ARGUMENT = frozenset(
    {
        "-p",
        "--paginate",
        "-P",
        "--no-pager",
        "--bare",
        "--no-replace-objects",
        "--literal-pathspecs",
        "--glob-pathspecs",
        "--noglob-pathspecs",
        "--icase-pathspecs",
        "--no-optional-locks",
        "--no-lazy-fetch",
    }
)


def subcommand_candidates(tokens: list[str], start: int) -> set[int]:
    """`git` token の直後から、subcommand が来うる index を**すべて**返す。

    `push_command_parse._subcommand_candidates`（旧・private）の public 版。
    ADR-3 の 2 点差分: (1) 値結合形（`=` を含む token）は既知・未知を問わず
    1 候補に確定する。(2) `GIT_GLOBAL_FLAGS_WITHOUT_ARGUMENT` に属する既知
    no-arg flag も 1 候補に確定する。未知の `-` 始まり token は依然として
    「引数を取る/取らない」両方を候補にする（fail-closed）。
    """
    candidates: set[int] = set()
    visited: set[int] = set()
    pending = [start]
    while pending:
        cursor = pending.pop()
        if cursor in visited or cursor >= len(tokens):
            continue
        visited.add(cursor)
        token = tokens[cursor]
        if not token.startswith("-"):
            candidates.add(cursor)
            continue
        argument = cursor + 1
        takes_argument = (
            argument < len(tokens)
            and not is_unquoted_separator(tokens[argument], COMMAND_SEPARATOR_TOKENS)
        )
        if "=" in token:
            if takes_argument:
                pending.append(argument)
            continue
        if token in GIT_GLOBAL_FLAGS_WITH_ARGUMENT:
            if takes_argument:
                pending.append(argument + 1)
            continue
        if token in GIT_GLOBAL_FLAGS_WITHOUT_ARGUMENT:
            if takes_argument:
                pending.append(argument)
            continue
        pending.append(argument)
        if takes_argument:
            pending.append(argument + 1)
    return candidates


#: heredoc の introducer と所有 pipeline の判定は字句解析の芯（shell_lexer）と共有する
#: （`gh_command_parse` と同じもの）。
_HEREDOC_RE = shell_lexer.HEREDOC_RE
_PIPELINE_BOUNDARY_RE = shell_lexer.PIPELINE_BOUNDARY_RE
_heredoc_owner_scope = shell_lexer.heredoc_owner_scope
_feeds_shell_interpreter = shell_lexer.feeds_shell_interpreter


def _find_heredoc_terminator(terminators: dict[str, list[int]], start: int, word: str) -> int | None:
    """`start` 以降で終端行（`.strip() == word`）を探し、その index を返す。

    `terminators` は行の `.strip()` から行番号の昇順の一覧への索引（`_terminator_index`）。
    見つからない場合は None を返す。呼び出し側はこれを「heredoc ではなかった」
    （クォート内文字列中の `<<WORD` 等への誤爆）とみなし、本文除去を行わない
    （Security Medium / Implementation Medium-1 remediation）。
    """
    candidates = terminators.get(word, [])
    position = bisect.bisect_left(candidates, start)
    return candidates[position] if position < len(candidates) else None


def _terminator_index(lines: list[str]) -> dict[str, list[int]]:
    """終端行を 1 回だけ索引にする（introducer ごとに後ろの行を全部走査すると、行数の 2 乗になる）。"""
    index: dict[str, list[int]] = {}
    for number, line in enumerate(lines):
        index.setdefault(line.strip(), []).append(number)
    return index


def _extract_executed_heredoc_bodies(command: str, keep_data: bool = False) -> tuple[str, list[str]]:
    """heredoc 本文を落とす（introducer 行は残す）。ただし **実行される** heredoc
    （`bash <<EOF` 等）の本文は落とさず、独立コマンド文字列として返す。

    戻り値は `(stripped_command, executed_bodies)`。`executed_bodies` の各要素は
    `split_segments` が独立セグメントとして再帰的に処理する（Security High /
    Medium remediation）。終端行が実在しないマッチ（クォート内文字列への誤爆）は
    heredoc として扱わず、該当行以降を一切消費しない。`keep_data` なら、実行されない本文も
    `executed_bodies` に入れる（push の経路は本文を別のコマンドとして読む）。
    """
    lines = command.split("\n")
    terminators = _terminator_index(lines)
    kept: list[str] = []
    executed: list[str] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        kept.append(line)
        index += 1
        for match in _HEREDOC_RE.finditer(line):
            word = match.group(2)
            terminator = _find_heredoc_terminator(terminators, index, word)
            if terminator is None:
                continue
            runs_body = _feeds_shell_interpreter(line, match.start())
            body = lines[index:terminator]
            index = terminator + 1
            if (runs_body or keep_data) and body:
                executed.append("\n".join(body))
    return "\n".join(kept), executed


COMMAND_SUBSTITUTION_PLACEHOLDER = "__gdd_cmd_subst__"


def _scan_command_substitution(command: str, index: int, length: int) -> tuple[str, int]:
    """`command[index]` が `$(` の開始位置であることを前提に、対応する閉じ
    `)` までをネスト深さを追跡してスキャンする（`_extract_command_substitutions`
    の複雑度分割。挙動は分割前と同一）。`(中身, 次に処理する index)` を返す。
    """
    depth = 1
    cursor = index + 2
    start = cursor
    while cursor < length and depth:
        if command[cursor] == "(":
            depth += 1
        elif command[cursor] == ")":
            depth -= 1
            if depth == 0:
                break
        cursor += 1
    inner = command[start:cursor]
    next_index = cursor + 1 if cursor < length else cursor
    return inner, next_index


def _scan_backtick_substitution(command: str, index: int, length: int) -> tuple[str, int]:
    """`command[index]` が開きバッククォートであることを前提に、閉じる
    バッククォートまでをスキャンする（`_extract_command_substitutions` の
    複雑度分割。挙動は分割前と同一）。`(中身, 次に処理する index)` を返す。
    """
    cursor = index + 1
    while cursor < length and command[cursor] != "`":
        cursor += 1
    inner = command[index + 1 : cursor]
    next_index = cursor + 1 if cursor < length else cursor
    return inner, next_index


def _extract_command_substitutions(command: str) -> tuple[str, list[str]]:
    """`$(...)` とバッククォート `` `...` `` の中身を切り出し、外側の文字列は
    プレースホルダ token に置き換える（Implementation High-1 remediation）。

    lex 前に適用することで、`git worktree add $(mktemp -d) -b codex/... HEAD`
    のような形が `(` / `)`（COMMAND_SEPARATOR_TOKENS）でセグメント分断され、
    `-b codex/... HEAD` が `git` token を含まないセグメントへ漏れ出す事故を防ぐ。
    置換対象の中身自体は戻り値の `inner_commands` として返し、`split_segments`
    が独立セグメントとして再帰的に処理する。

    クォート文脈を bash と同じ規則で追跡する（Round 2 Implementation Medium
    remediation。`_heredoc_owner_scope` と同型）。**シングルクォート内**は一切
    展開されないので `$(` / バッククォートを見ない（`git commit -m '… $(git
    switch -c …)'` は散文であり、実行形として deny しない: AC-8 FP-2）。
    **ダブルクォート内**は bash が展開するので切り出す。シングルクォート外の
    バックスラッシュは次の 1 文字をリテラルにする（`\\'` を開きクォート、
    `\\"` を閉じクォート、`\\$(` を置換開始と誤認しない）。
    """
    masked: list[str] = []
    inner_commands: list[str] = []
    quote = ""
    index = 0
    length = len(command)
    while index < length:
        char = command[index]
        if quote == "'":
            if char == "'":
                quote = ""
            masked.append(char)
            index += 1
            continue
        if char == "\\" and index + 1 < length:
            masked.append(command[index : index + 2])
            index += 2
            continue
        if char == quote:
            quote = ""
            masked.append(char)
            index += 1
            continue
        if not quote and char in "'\"":
            quote = char
            masked.append(char)
            index += 1
            continue
        if char == "$" and command.startswith("$(", index):
            inner, index = _scan_command_substitution(command, index, length)
            inner_commands.append(inner)
            masked.append(COMMAND_SUBSTITUTION_PLACEHOLDER)
            continue
        if char == "`":
            inner, index = _scan_backtick_substitution(command, index, length)
            inner_commands.append(inner)
            masked.append(COMMAND_SUBSTITUTION_PLACEHOLDER)
            continue
        masked.append(char)
        index += 1
    return "".join(masked), inner_commands


def _split_by_separator(tokens: list[str]) -> list[list[str]]:
    segments: list[list[str]] = []
    current: list[str] = []
    for token in tokens:
        if token in COMMAND_SEPARATOR_TOKENS:
            if current:
                segments.append(current)
            current = []
            continue
        current.append(token)
    if current:
        segments.append(current)
    return segments


def _split_segments(command: str, depth: int) -> list[list[str]]:
    """`split_segments` の本体。`depth` は nested shell の展開段数。"""
    stripped, executed_bodies = _extract_executed_heredoc_bodies(command)
    masked, inner_commands = _extract_command_substitutions(stripped)
    tokens, degraded = _lex_checked(masked)
    segments = _split_by_separator(tokens)
    if degraded:
        # 閉じない引用符で縮退したら、行ごとの読みのセグメントも足す（止める側。bash・zsh は実行しない）
        segments.extend(_split_by_separator(_lex_by_line(masked)))
    if depth < _MAX_NESTED_SHELL_DEPTH:
        for nested in _nested_shell_commands(tokens):
            segments.extend(_split_segments(nested, depth + 1))
    for inner in inner_commands:
        segments.extend(_split_segments(inner, depth))
    for body in executed_bodies:
        segments.extend(_split_segments(body, depth))
    return segments


def split_segments(command: str) -> list[list[str]]:
    """heredoc 本文除去 → コマンド置換の切り出し → lex → 区切り分割 →
    nested shell のコマンド文字列を独立セグメントとして追加する（ADR-5 + remediation）。

    nested shell / eval のコマンド文字列（`_nested_shell_commands`。深さ上限
    `_MAX_NESTED_SHELL_DEPTH`）、実行される heredoc 本文
    （`_extract_executed_heredoc_bodies`）、`$(...)` / バッククォートの中身
    （`_extract_command_substitutions`）は、それぞれ独立したコマンド文字列として
    同じ手順を再帰適用し、結果セグメントへ追加する。nested shell の文字列を
    lex だけで済ませず同じ入口に通すのは、外側ではシングルクォート内として
    見送った `$(...)` を、nested shell が実際に展開するため（`bash -c 'git
    worktree add $(mktemp -d) -b codex/… HEAD'` を `(` で分断させない）。
    heredoc 本文と置換の中身は元の文字列より必ず短くなるため、再帰は有限回で
    終了する。閉じない引用符で lex が縮退したら、行ごとの読み（`_lex_by_line`）の
    セグメントも足す（引用の中に見える branch の作成も止める側に倒す）。
    """
    return _split_segments(command, depth=0)
