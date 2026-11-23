"""human check の判断ポイントの `依頼との差` を読む（依存なし。hook・lint・記録が同じ関数を呼ぶ）。

通すかどうかは、各マーカーの直前（空行だけを飛ばした最初の非空行）の `<gdd-hitl-fields ...>` タグの
`request-diff`（判断ポイントの順に `none`/`differs` をカンマで）だけで決める。件数も本文からは数えない
（引用・例示にある欄の形の行を、欠けた本物の欄と区別できないため）。本文の `依頼との差:` の欄は、止める向きにだけ使う。`依頼との差` を含む行は
（コードの中も含めて）全部が `<記号> 依頼との差: <値>` の 1 つの形でなければ読めないものとする。値は `なし` ちょうどか、
差を宣言する `あり: <依頼の原文の項目>` の 2 形だけを読み、ほかの値（`なし | X`・`なし。`・`ありません。` など）は
読めない形にする。値が `なし` でない欄を止める。本文の欄が欠けていても止めない。値の正しさは見ない（自己申告）。

- `format_problem`: 形の問題（欄の形が読めない・タグが無い・タグの値が読めない）。提示の時点の検査（Stop の出し直し・lint）が使う
- `field_problem`: 形の問題に加えて、`なし` 以外の点（本文の `あり:`・タグの `differs`）も問題にする。承認の書き込みの検査が使う
- `correction_problem`: 問題のある提示に人が答えた後に main が書く補正（欄とタグだけを直した版）を、承認の根拠に
  使えないならその理由。補正は提示と同じ `field_problem` で見て、狭める点かは分類せず、常に人の返事の引用（`decided`）を求める
"""
from __future__ import annotations

import re
import unicodedata

LABEL = "依頼との差"
_BULLET_RE = re.compile(r"[-+]|\d+[.)]")
VALUE_RE = re.compile(r"なし|あり[ \t]*:[ \t]*\S.*")
# 位置は `scripts/lib/hitl_fields.py` と同じ契約（同名パッケージ `lib` のため cross-import しない）。行の形は
# guard のほうが厳しく、引用符の対応を求める（値の中の `>` は許す）。
MARKER = '<gdd-stop reason="human-check-waiting">'
TAG_LINE_RE = re.compile(r'^<gdd-hitl-fields(?:\s(?:[^>"]|"[^"]*")*)?>$')
TAG_ATTR = "request-diff"
TAG_ATTR_RE = re.compile(r'(?<![A-Za-z0-9-])request-diff="([^"]*)"')
TAG_VALUE_RE = re.compile(r"(?:none|differs)(?:,(?:none|differs))*")
_FORMAT_CHARS = str.maketrans("", "", "`*_")
CORRECTION_ATTR_RE = re.compile(r"(?<![A-Za-z0-9-])correction(?![A-Za-z0-9=-])")
DECIDED_RE = re.compile(r'(?<![A-Za-z0-9-])decided="([^"]*)"')


def _normalize(line: str) -> str:
    return unicodedata.normalize("NFKC", line).translate(_FORMAT_CHARS)


def _field_value(line: str) -> str | None:
    """`[空白][> の引用…][- + 1. 1) の記号][空白]依頼との差[空白]:[空白]<値>[空白]` の値。形が違えば None。

    先頭から順に読む（正規表現の後戻りで、空白の長い行に長さの二乗の時間がかからないようにする。
    hook の上限 10 秒を超えると guard 全体が走らずに書き込みが通るため）。"""
    rest = line.lstrip(" \t>")  # `[ \t]*(?:>[ \t]*)*` と同じ集合を 1 回で外す
    bullet = _BULLET_RE.match(rest)
    if bullet:
        rest = rest[bullet.end():].lstrip(" \t")
    if not rest.startswith(LABEL):
        return None
    rest = rest[len(LABEL):].lstrip(" \t")
    if not rest.startswith(":"):
        return None
    return rest[1:].strip(" \t")


def _scan(presentation: str) -> tuple[list[str], list[str]]:
    """(欄の値, 読めない行)。"""
    values: list[str] = []
    unreadable: list[str] = []
    for line in presentation.splitlines():
        normalized = _normalize(line)
        if LABEL not in normalized:
            continue
        value = _field_value(normalized)
        if value is not None and VALUE_RE.fullmatch(value):
            values.append(value)
        else:
            unreadable.append(line.strip())
    return values, unreadable


def field_values(presentation: str) -> list[str]:
    """`依頼との差:` の値を書かれた順に返す。"""
    return _scan(presentation)[0]


def unreadable_lines(presentation: str) -> list[str]:
    """`依頼との差` を含むのに、欄の形で読めない行。"""
    return _scan(presentation)[1]


def _adjacent_tag(text: str) -> str | None:
    for line in reversed(text.split("\n")):
        stripped = line.strip()
        if stripped:
            return stripped if TAG_LINE_RE.match(stripped) else None
    return None


def tag_values(presentation: str) -> list[list[str] | None] | None:
    """マーカーごとの直前のタグの `request-diff` の値（マーカーが無ければ文書の末尾を 1 つ）。
    タグが無いマーカーがあれば None、属性が無い・2 つ以上・形が読めないタグは None の要素にする。"""
    parts = presentation.split(MARKER)
    heads = parts[:-1] if len(parts) > 1 else parts
    result: list[list[str] | None] = []
    for head in heads:
        tag = _adjacent_tag(head)
        if tag is None:
            return None
        found = TAG_ATTR_RE.findall(tag)
        ok = len(found) == 1 and TAG_VALUE_RE.fullmatch(found[0])
        result.append(found[0].split(",") if ok else None)
    return result


def format_problem(presentation: str) -> str | None:
    """欄かタグの形に問題があればその種類、無ければ None（`なし` 以外の点は問題にしない）。"""
    if _scan(presentation)[1]:
        return "欄の形が読めない"
    tags = tag_values(presentation)
    if tags is None:
        return "タグが無い"
    if any(tag is None for tag in tags):
        return "タグの値が読めない"
    return None


def field_problem(presentation: str) -> str | None:
    """承認として記録できない問題があればその種類、無ければ None。"""
    problem = format_problem(presentation)
    if problem:
        return problem
    if any(value != "なし" for value in _scan(presentation)[0]):
        return "なし以外の点がある"
    if any(v != "none" for tag in tag_values(presentation) or [] for v in tag or []):
        return "なし以外の点がある"
    return None


def correction_problem(presentation: str, correction: str, replies: list[str]) -> str | None:
    """補正を承認の根拠に使えないならその理由、使えるなら None。

    補正は、マーカーの無い発言の最後の非空行の `<gdd-hitl-fields correction request-diff="none,..." decided="...">`。
    補正の文全体が `field_problem` を通り（値はすべて `none`。本文の欄も読める形で `なし`）、提示のタグが読めれば
    その点の数と同じで、`decided` が提示の後の人の返事（`replies`）のどれかに含まれなければならない。"""
    tag = _adjacent_tag(correction)
    if tag is None or not CORRECTION_ATTR_RE.search(tag):
        return "補正が無い"
    problem = field_problem(correction)
    if problem:
        return f"補正の{problem}"
    tags = tag_values(presentation)
    if tags and all(t is not None for t in tags):
        if len(TAG_ATTR_RE.findall(tag)[0].split(",")) != sum(len(t) for t in tags):
            return "補正の点の数が提示と違う"
    decided = DECIDED_RE.findall(tag)
    if len(decided) != 1 or not decided[0].strip() or not any(decided[0] in reply for reply in replies):
        return "提示の後の人の返事の引用が無い"
    return None
