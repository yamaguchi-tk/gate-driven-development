"""`<gdd-hitl-fields ...>` 宣言タグを位置契約で読む（scripts/lint-hitl-*.py が共有する）。

位置契約: `HITL_STOP_MARKER` の全ての出現それぞれについて、その直前を末尾から
遡り、空行だけを飛ばした最初の非空行が、ちょうどスタンドアロンな
`<gdd-hitl-fields ...>` 行であれば、それをその出現の宣言とする。markdown 構文
（フェンス・HTML コメント・`<pre>` など）は解釈しない。設計の経緯と既知の限界は
`scripts/lint-hitl-required-fields.py` の docstring にある。
"""
from __future__ import annotations

import re

# `hooks/scripts/lib/hitl_lint_gate.py` の `HITL_MARKER` と同じ文字列。
# `scripts/lib/` と `hooks/scripts/lib/` は同名パッケージ `lib` を持つため cross-import しない。
HITL_STOP_MARKER = '<gdd-stop reason="human-check-waiting">'

# タグ内部から `属性名="値"` のペアを緩く抽出する。
_FIELD_ATTR_RE = re.compile(r'([A-Za-z][A-Za-z0-9-]*)="([^"]*)"')
# 行全体がちょうど `<gdd-hitl-fields ...>` である行だけを候補にする。タグ名の直後は
# `>` か空白に限り、`<gdd-hitl-fieldsets ...>` のような接頭辞一致を弾く。
_STANDALONE_TAG_LINE_RE = re.compile(r'^<gdd-hitl-fields(?:\s[^>]*)?>$')

# 段階実装の節の語（`段階実装`・`段階実装サマリー`）はこの接頭辞で始まる。
STAGE_WORD_PREFIX = "段階実装"
# ズレ確認の節の語。`zure="none"` の宣言で外す（人に残った行が無い回は節ごと書かない）。
ZURE_WORD = "ズレ確認"


def hitl_check_points(text: str) -> list[int]:
    """`HITL_STOP_MARKER` の全ての開始位置を返す（universal quantification）。

    marker が無ければ文書末尾を 1 点だけ返す（文書末尾直前の非空行がタグ行なら
    その宣言を読む）。
    """
    positions: list[int] = []
    start = 0
    while True:
        idx = text.find(HITL_STOP_MARKER, start)
        if idx < 0:
            break
        positions.append(idx)
        start = idx + len(HITL_STOP_MARKER)
    return positions or [len(text)]


def adjacent_declaration_before(text: str, position: int) -> str | None:
    """`position` の直前で、空行だけを飛ばした最初の非空行がタグ行ならそれを返す。"""
    for line in reversed(text[:position].split("\n")):
        stripped = line.strip()
        if stripped == "":
            continue
        if _STANDALONE_TAG_LINE_RE.match(stripped):
            return stripped
        return None
    return None


def parse_hitl_fields_at(text: str, position: int) -> dict[str, str] | None:
    """`position` の直前に隣接するタグの属性名 → 値。タグが無ければ None。"""
    declaration = adjacent_declaration_before(text, position)
    if declaration is None:
        return None
    return dict(_FIELD_ATTR_RE.findall(declaration))


def declared_none(text: str, attr: str) -> bool:
    """全ての marker の隣接宣言で `attr` が `none` のときだけ True（それ以外は fail-closed）。"""
    for position in hitl_check_points(text):
        fields = parse_hitl_fields_at(text, position)
        if fields is None or fields.get(attr) != "none":
            return False
    return True


def stage_declared_none(text: str) -> bool:
    return declared_none(text, "stage")


def required_words(words: tuple[str, ...], text: str) -> tuple[str, ...]:
    """`stage="none"` なら段階実装の語を、`zure="none"` ならズレ確認を必須語から外す。"""
    skip_stage = stage_declared_none(text)
    skip_zure = declared_none(text, "zure")
    return tuple(
        word for word in words
        if not (skip_stage and word.startswith(STAGE_WORD_PREFIX)) and not (skip_zure and word == ZURE_WORD)
    )
