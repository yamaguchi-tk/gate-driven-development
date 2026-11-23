#!/usr/bin/env python3
"""gate が共有する shell の字句解析の芯（行継続・語頭コメント・引用符をまたぐ改行・引用符の中の
演算子の退避・fd 番号・shlex・fallback）と、heredoc の所有 pipeline の判定。

`git_command_parse.py`（pre-push gate・root-branch guard・review-followup nudge）と
`gh_command_parse.py`（merge gate・pre-PR gate）がこの 1 つを読む。lib ごとに残すもの:
区切りの集合（git は `(` `)` を区切りにし、gh はしない）、入れ子の shell の展開、
コマンド置換の切り出し、heredoc の本文の落とし方。

読みの正解は実 shell（bash と zsh）。2 つの shell で読みが割れる形は、呼び出し側が止める側に倒す
（fd 番号の桁数は `lex` の `fd_digits` で選び、引用符が閉じない形は縮退として返す）。例外は
`$'…'` の中の行継続で、bash の読み（残す）に合わせる（引数の中身にしか効かない。実 transcript に
該当は無かった）。
"""
from __future__ import annotations

import itertools
import re
import shlex

# `shlex(punctuation_chars=True)` が独立 token として切り出す shell の制御・リダイレクト演算子。
COMMAND_OPERATOR_CHARS = frozenset("();<>|&")
# shlex（posix、punctuation_chars=True）が語の文字として特別扱いしない文字だけを退避先の候補に
# するための除外集合（shlex.py の whitespace / quotes / escape / punctuation_chars の和集合）。
SHLEX_SPECIAL_CHARS = frozenset(" \t\r\n'\"\\") | COMMAND_OPERATOR_CHARS
# 退避先の候補。1 段目は U+0001〜U+00FF のうち SHLEX_SPECIAL_CHARS 以外（1 byte 幅なら shlex の
# token 組み立てが速い）、2 段目は U+E000 から昇順で、打ち切らない。
OPERATOR_MASK_START = 0xE000
# 演算子文字ではないが、git・push の側が区切りと読む語（改行・`{`）。引用の中では退避し、戻した token が
# この語と等しければ `QuotedWord` にする（区切りの集合と等しい引用した語を、区切りと読ませない）。
QUOTED_SEPARATOR_CHARS = frozenset("\n{")
# 二重引用符の中のバッククォートの区間の中身で、エスケープする文字（`_backtick_interval`）。
INTERVAL_ESCAPED_CHARS = SHLEX_SPECIAL_CHARS | QUOTED_SEPARATOR_CHARS
MASKED_OPERATOR_CHARS = tuple(sorted(COMMAND_OPERATOR_CHARS | QUOTED_SEPARATOR_CHARS))
# bash で「語頭」を作る文字（この直後の `#` だけがコメント開始）。`$` `{` は含めない
# （`$#` / `${#a}` は特殊パラメータ）。`)` は、`$(` を閉じるときだけ語頭を作らない（`normalize`）。
WORD_BOUNDARY_CHARS = frozenset(" \t\n;&|<>()")
# shlex が割れない片の fallback。引用符を見ずに、空白と区切り記号の連で割る。区切り記号の連
# （`>|`・`2>&1|` の `>&` など）は 1 token に保ち、shlex の punctuation_chars と同じまとめ方にする。
FALLBACK_TOKEN_RE = re.compile(r"[();<>|&]+|[^\s();<>|&]+")
# heredoc の introducer。
HEREDOC_RE = re.compile(r"<<-?\s*([\x27\x22]?)([A-Za-z_][A-Za-z0-9_]*)\1")
# heredoc の所有 pipeline を切り出す境界。`|` は pipeline の内側なので境界に含めない
# （`cat <<EOF | bash` の本文は実行される）。`|&`・`&>`・`>&`・`<&` の中の `&` も境界にしない
# （`cat <<EOF |& bash`・`cat <<EOF 3<&0 | bash` の interpreter が走査範囲の外に落ちない）。
PIPELINE_BOUNDARY_RE = re.compile(r"&&|\|\||;|(?<![|&<>])&(?![&>])")
SHELL_INTERPRETERS = frozenset({"bash", "sh", "zsh", "dash", "ksh"})


class QuotedWord(str):
    """引用符・エスケープ由来の演算子文字だけから成る token であることの印。

    `is_operator` はこの型を演算子と見なさない。`str` 派生なので、等値比較・集合の所属・`join` は
    元の文字列と同じ（git の区切りの集合の判定は、引用符の中の `;` も区切りと読む）。
    """


def is_operator(token: str) -> bool:
    """token 全体が shell の制御・リダイレクト演算子だけで構成されるか（`QuotedWord` は除く）。"""
    if isinstance(token, QuotedWord):
        return False
    return bool(token) and all(ch in COMMAND_OPERATOR_CHARS for ch in token)


def normalize(text: str) -> str:
    """行継続と語頭コメントを bash の規則で落とす（1 パス）。

    - 行継続（エスケープされていない `\\` + 改行）は、引用符の外と二重引用符の中で消す。単引用符・
      `$'…'` の中では残す（bash の読み。zsh は `$'…'` の中では消す。引数の中身にしか効かない）
    - 語頭の `#` から行末までを落とす（改行は残す）。語頭は行頭・空白・制御とリダイレクトの演算子・
      括弧の直後。ただし `$(`・`$((` を閉じる `)` の直後は語の途中（`echo $(date)#x; git push` の
      `#x` はコメントではない）。コメントの末尾の `\\` は次の行をつながない
    - 引用符の中・`${…}` の中と `\\#` はコメントではない
    - バッククォートは、bash と同じく、エスケープされていない次の `` ` `` までを区間として先に確定する
      （引用符の外でも二重引用符の中でも。`_backtick_interval`）。区間はスタックに積まず、中身にこの
      関数を再帰でかける（中の語頭の `#` から閉じの手前まではコメント）。引用符の外の区間の中の引用は、
      後の段がトップレベルと同じく対にして読む。二重引用符の中の区間（スタックのどこかに `"` がある）
      の中身は、全部を外の二重引用符の中の 1 語として読ませる
    - 引用の文脈はスタックで追う。二重引用符の中の `$(`・`${` は新しい文脈を積み、対応する閉じで
      二重引用符の中に戻る（`"$(printf "fix #12")"` の中の `"` は外の引用を閉じない）

    heredoc の本文は見ない。引用した heredoc の本文の行継続を残すため、呼び出し側は本文を先に
    取り除く（各 lib の heredoc の落とし方）。
    """
    out: list[str] = []
    quote = ""
    after_dollar = False
    at_word_start = True
    # 開いている文脈: `"`・`${`・`(`（サブシェル）・`$(`。空ならトップレベル。
    stack: list[str] = []
    index = 0
    length = len(text)
    while index < length:
        char = text[index]
        nxt = text[index + 1] if index + 1 < length else ""
        if quote:
            out.append(char)
            if char == "\\" and quote == "$'" and nxt:
                out.append(nxt)
                index += 1
            elif char == "'":
                quote = ""
            index += 1
            continue
        if char == "\\" and nxt == "\n":
            # bash は `$` の次の文字を読む前に行継続を消すので、after_dollar と語頭は保つ。
            index += 2
            continue
        if char == "\\" and nxt:
            out.append(char + nxt)
            at_word_start = after_dollar = False
            index += 2
            continue
        if char == "`":
            interval, index = _backtick_interval(text, index, '"' in stack)
            out.append(interval)
            at_word_start = after_dollar = False
            continue
        top = stack[-1] if stack else ""
        if top in ('"', "${"):
            out.append(char)
            if char == ("}" if top == "${" else '"'):
                stack.pop()
            elif char == '"':
                stack.append(char)
            elif char == "'" and top == "${" and (len(stack) < 2 or stack[-2] != '"'):
                quote = "$'" if after_dollar else "'"
            elif after_dollar and char in "({":
                stack.append("$" + char)
            at_word_start = char == "(" and after_dollar
            after_dollar = char == "$" and not after_dollar
            index += 1
            continue
        if char in "'\"":
            # `$'…'`（ANSI-C 引用）の中では `\\'` がエスケープで、引用は閉じない。
            if char == "'":
                quote = "$'" if after_dollar else "'"
            else:
                stack.append('"')
            out.append(char)
            at_word_start = after_dollar = False
            index += 1
            continue
        if char == "#" and at_word_start:
            newline = text.find("\n", index)
            if newline == -1:
                break
            index = newline
            after_dollar = False
            continue
        out.append(char)
        if char == "(":
            stack.append("$(" if after_dollar else "(")
            at_word_start = True
        elif char == ")":
            # `$(`・`$((` を閉じる `)` の直後は語の途中。サブシェル・case のパターンの `)` の直後は語頭。
            at_word_start = top != "$("
            if top in ("(", "$("):
                stack.pop()
        elif char == "{" and after_dollar:
            stack.append("${")
            at_word_start = False
        else:
            at_word_start = char in WORD_BOUNDARY_CHARS
        # `$$`（PID）は 2 文字まとめて読む。後ろの単引用符は通常の引用になる。
        after_dollar = char == "$" and not after_dollar
        index += 1
    return "".join(out)


def _backtick_interval(text: str, start: int, in_double_quote: bool) -> tuple[str, int]:
    """`text[start]` の `` ` `` から、エスケープされていない次の `` ` `` までの区間を書き直して返す。

    返り値は `(書き直した区間, 区間の次の index)`。閉じなければ末尾までを区間にする（bash・zsh は構文
    エラー。中を読んで止める側に倒す）。中身は `normalize` で行継続とコメントを落とす（中身には
    エスケープされていない `` ` `` が無いので、再帰は 1 段で終わる）。引用符の外の区間の中身は、それ以上
    書き直さない（中の引用は後の段がトップレベルと同じく対にして読む）。二重引用符の中の区間
    （`in_double_quote`）の中身は、shlex が特別に扱う文字と `{` を全部 `\\` でエスケープし、後の段が
    引用の中と外のどちらにいると読んでも、外の二重引用符の中の 1 語の一部として読ませる。
    """
    length = len(text)
    end = start + 1
    while end < length and text[end] != "`":
        end += 2 if text[end] == "\\" else 1
    end = min(end, length)
    inner = normalize(text[start + 1 : end])
    if in_double_quote:
        inner = "".join("\\" + char if char in INTERVAL_ESCAPED_CHARS else char for char in inner)
    if end < length:
        return "`" + inner + "`", end + 1
    return "`" + inner, length


def split_unquoted_newlines(text: str) -> list[str]:
    """引用符の外の改行で分ける（引用符は行をまたいで追う）。`normalize` の後に使う。"""
    pieces: list[str] = []
    current: list[str] = []
    quote = ""
    index = 0
    length = len(text)
    while index < length:
        char = text[index]
        if quote == "'":
            quote = "" if char == "'" else quote
        elif char == "\\" and index + 1 < length and quote != "'":
            current.append(text[index : index + 2])
            index += 2
            continue
        elif quote:
            quote = "" if char == quote[-1] else quote
        elif char == "'" and index and text[index - 1] == "$":
            quote = "$'"
        elif char in "'\"":
            quote = char
        elif char == "\n":
            pieces.append("".join(current))
            current = []
            index += 1
            continue
        current.append(char)
        index += 1
    pieces.append("".join(current))
    return pieces


def pick_operator_masks(text: str) -> dict[str, str]:
    """演算子文字 7 種と改行・`{`（`MASKED_OPERATOR_CHARS`）それぞれに、`text` に現れない退避先の文字を割り当てる。

    候補を使い切ると `chr(0x110000)` が `ValueError` を投げる（呼び出し元へ伝える。縮退に
    変えると、heredoc を含む形で縮退の標識が立たずに merge gate が通す）。
    """
    used = set(text) | SHLEX_SPECIAL_CHARS
    candidates = (
        chr(point)
        for point in itertools.chain(range(1, 0x100), itertools.count(OPERATOR_MASK_START))
        if chr(point) not in used
    )
    return dict(zip(MASKED_OPERATOR_CHARS, candidates))


def mask_quoted_operators(text: str, masks: dict[str, str]) -> str:
    """引用符の中・バックスラッシュの直後（単引用符の外）の演算子文字・改行・`{` を退避先へ置き換える。"""
    out: list[str] = []
    quote = ""
    index = 0
    length = len(text)
    while index < length:
        char = text[index]
        if quote != "'" and char == "\\" and index + 1 < length:
            out.append(char)
            out.append(masks.get(text[index + 1], text[index + 1]))
            index += 2
            continue
        if quote and char != quote:
            out.append(masks.get(char, char))
        else:
            if char == quote:
                quote = ""
            elif char in "'\"":
                quote = char
            out.append(char)
        index += 1
    return "".join(out)


def restore_token(token: str, restore: dict[int, str]) -> str:
    """退避先を元の文字へ戻す。戻して演算子文字だけ、または改行・`{` だけになった token は `QuotedWord` にする。"""
    restored = token.translate(restore)
    if restored != token and (is_operator(restored) or restored in QUOTED_SEPARATOR_CHARS):
        return QuotedWord(restored)
    return restored


_FD_PREFIX_RES: dict[int, re.Pattern[str]] = {}


def strip_fd_prefixes(text: str, digits: int) -> str:
    """リダイレクトに空白なしで密着した `digits` 桁までの fd 番号（`2>&1` の `2`）を落とす。

    `7 </dev/null` の `7` は残す。bash は int に収まる並び（`12>x`）も fd 番号に、zsh は 1 桁だけを
    fd 番号に読む。
    """
    pattern = _FD_PREFIX_RES.get(digits)
    if pattern is None:
        pattern = _FD_PREFIX_RES[digits] = re.compile(r"(^|\s)(\d{1,%d})(?=[<>])" % digits)
    return pattern.sub(r"\1", text)


def split_words(text: str) -> tuple[list[str], bool]:
    """shlex（posix、punctuation_chars、コメントなし）で割る。割れなければ fallback と縮退を返す。"""
    try:
        lexer = shlex.shlex(text, posix=True, punctuation_chars=True)
        lexer.whitespace_split = True
        lexer.commenters = ""
        return list(lexer), False
    except ValueError:
        return FALLBACK_TOKEN_RE.findall(text), True


def _lex_piece(piece: str, fd_digits: int) -> tuple[list[str], bool]:
    masks = pick_operator_masks(piece)
    restore = {ord(masked): original for original, masked in masks.items()}
    words, degraded = split_words(strip_fd_prefixes(mask_quoted_operators(piece, masks), fd_digits))
    if degraded:
        return FALLBACK_TOKEN_RE.findall(strip_fd_prefixes(piece, fd_digits)), True
    return [restore_token(word, restore) for word in words], False


def lex(text: str, newline_token: str | None, fd_digits: int) -> tuple[list[str], bool]:
    """`text` を token に割り、`(tokens, 縮退したか)` を返す。

    行継続と語頭コメントを落とし（`normalize`）、引用符の外の改行で分けて、各片を割る。片の間には
    `newline_token` を置く（None なら置かない。最初の token より前には置かない）。引用符の中の演算子文字・改行・`{` だけの token は `QuotedWord` になる。
    密着した fd 番号は `fd_digits` 桁まで落とす。shlex が割れない片（引用符が末尾まで閉じない）は
    引用符を見ずに割り、縮退として返す。退避先を使い切ったときの `ValueError` は伝える。
    """
    tokens: list[str] = []
    degraded = False
    for number, piece in enumerate(split_unquoted_newlines(normalize(text))):
        if number and newline_token is not None and tokens:
            tokens.append(newline_token)
        piece_tokens, piece_degraded = _lex_piece(piece, fd_digits)
        tokens.extend(piece_tokens)
        degraded = degraded or piece_degraded
    return tokens, degraded


def heredoc_owner_scope(line: str, at: int) -> tuple[str, int]:
    """位置 `at` の heredoc を所有する走査範囲と、その範囲内での位置を返す。

    `<<` がクォートの内側なら、その中身（`bash -lc '… <<MSG …'` の入れ子 script）だけを範囲にする。
    クォートの外なら、行からクォート内容を伏せたものを範囲にする（`git commit -m "… bash …" <<MSG`
    の散文で実行形へ化けないため）。
    """
    masked = list(line)
    quote = ""
    start = 0
    for index, char in enumerate(line):
        if quote:
            masked[index] = " "
            if char == quote:
                if start <= at < index:
                    return line[start:index], at - start
                quote = ""
        elif char in "'\"":
            quote = char
            start = index + 1
            masked[index] = " "
    if quote and start <= at:
        return line[start:], at - start
    return "".join(masked), at


def feeds_shell_interpreter(line: str, at: int) -> bool:
    """位置 `at` の heredoc 本文が **実行される** 形か（`bash <<EOF` / `cat <<EOF | bash`）。

    判定範囲は、その heredoc を **所有する** pipeline に限る（制御演算子で区切られた別コマンドの
    interpreter が、後続のデータ heredoc を実行形へ格上げしない）。本文は見ない。
    """
    scope, offset = heredoc_owner_scope(line, at)
    lo, hi = 0, len(scope)
    for match in PIPELINE_BOUNDARY_RE.finditer(scope):
        if match.end() <= offset:
            lo = match.end()
        else:
            hi = match.start()
            break
    words, _degraded = split_words(normalize(scope[lo:hi]))
    return any(word.rsplit("/", 1)[-1] in SHELL_INTERPRETERS for word in words)
