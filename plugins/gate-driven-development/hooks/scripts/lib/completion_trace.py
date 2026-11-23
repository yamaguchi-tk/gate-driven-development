"""completion-check の Step 4c・4d と AC Trace Ledger Gate のうち、機械で判定できる部分。

scripts/check-completion-mechanical.py が呼ぶ。AC ID の文法は scripts/lint-ac.py を正本にするので、
AC ID の正規表現と requirements.md の AC ID は呼び出し側が lint-ac.py から渡す。
fence の中は記入例で現在値ではないので、strip_fenced_blocks の後の本文を読む。AC Trace Ledger は専用の
ファイル（ac-ledger.md）の全体を許可リストで読むので、fence の行も許可リストの外として gate に返す。
"""
from __future__ import annotations

import re

from lib.next_plan_check import _CHECKED_ITEM_RE, _STAGE_LANE_HEADING, _STAGE_LANE_SECTION_RE
from lib.tasklist_parse import NON_NEWLINE_LINE_BREAKS, classify_task_line, strip_fenced_blocks

# tasklist の task が満たす AC の欄。`AC:` が正本で `Covers AC:` は legacy alias（references/task-breakdown-steps.md）。
# 行頭か、`- Execution Status: ... | AC: AC-8` のように `|` で区切った欄の頭に置く。値は次の `|` か行末まで
_COVERS_LINE_RE = re.compile(r"(?:^|\|)[ \t]*(?:[-*][ \t]+)?(?:\*\*)?(?:Covers[ \t]+)?AC(?:\*\*)?[ \t]*[:：]([^|\n]*)",
                             re.MULTILINE)
# `AC-1..AC-5`・`AC-1〜AC-5` の範囲（数字だけの ID）。両端と間の ID を被覆に数える
_AC_RANGE_RE = re.compile(r"\bAC-(\d+)[ \t]*(?:\.\.|〜|~)[ \t]*AC-(\d+)\b")
_UNCHECKED_ITEM_RE = re.compile(r"^[ \t]*[-*+][ \t]+\[ \]", re.MULTILINE)
_CELL_SPLIT_RE = re.compile(r"(?<!\\)\|")
_SEPARATOR_CELL_RE = re.compile(r"^:?-+:?$")
_PLACEHOLDER_RE = re.compile(r"^<[^>]*>$")
# Lane の欄のうち、Step 4d が埋まっていることを求めるもの
LANE_FIELDS = ("Pending Stage ID", "Origin Steering", "Base Branch", "Next Planned Stage",
               "Tracking Destination", "Human Recheck")
_NONE_RE = re.compile(r"^none\b[\s+:：、,（(\-—]*", re.IGNORECASE)
_HEADING_RE = re.compile(r"^(#{1,6})[ \t]")
_AC_SECTION_RE = re.compile(r"^##[ \t]+(?:受入条件|Acceptance Criteria)[^\n]*(.*?)(?=^#{1,2}(?:[ \t]|$)|\Z)",
                            re.MULTILINE | re.DOTALL)
_PLAN_SECTION_RE = re.compile(r"^##[ \t]+Implementation Sequence Plan[^\n]*(.*?)(?=^#{1,2}(?:[ \t]|$)|\Z)",
                              re.MULTILINE | re.DOTALL)
# ac-ledger.md に置ける見出し。ほかの見出しは許可リストの外
_LEDGER_TITLE_RE = re.compile(r"^#{1,6}[ \t]+AC Trace Ledger[ \t]*$")
# tasklist.md・worklog.md に残った旧来の Ledger の見出し（階層・前後の語・大文字小文字・引用の中・
# ATX と setext の両方によらない。setext は次の行の = か - の列で見出しになる）
_QUOTE = r"(?:[ ]{0,3}>[ ]?)*"
# 変更前の読み手が Ledger の節として読んだ見出し（式をそのまま含め、受理集合をその上位集合にする。
# \s は全角スペース・NBSP・改行にも当たる）
_OLD_LEDGER_SECTION_HEADING = r"^#{2,3}\s+AC Trace Ledger[^\n]*"
_LEGACY_LEDGER_HEADING_RE = re.compile(
    rf"^{_QUOTE}[ ]{{0,3}}#{{1,6}}[ \t]+[^\n]*AC Trace Ledger[^\n]*"
    rf"|^{_QUOTE}[^\n]*AC Trace Ledger[^\n]*(?=\n{_QUOTE}[ ]{{0,3}}(?:=+|-+)[ \t]*$)"
    rf"|{_OLD_LEDGER_SECTION_HEADING}",
    re.MULTILINE | re.IGNORECASE)
LEDGER_FIELDS = ("AC ID", "検証コマンド/結果", "status")


def _one_line(text: str) -> str:
    return " ".join(text.split())


def _cells(line: str) -> list[str]:
    return [c.strip() for c in _CELL_SPLIT_RE.split(line.strip().strip("|"))]


def _tables(section: str) -> list[list[list[str]]]:
    """節の中の表を、区切り行を除いた行（先頭が見出し）のリストで返す。"""
    tables: list[list[list[str]]] = []
    current: list[list[str]] | None = None
    for line in section.splitlines():
        if line.strip().startswith("|"):
            cells = _cells(line)
            if current is None:
                current = []
                tables.append(current)
            if not all(_SEPARATOR_CELL_RE.match(c) for c in cells):
                current.append(cells)
        else:
            current = None
    return tables


def _ac_ids(value: str, ac_id_re: re.Pattern[str]) -> set[str]:
    ids = set(ac_id_re.findall(value))
    for lo, hi in _AC_RANGE_RE.findall(value):
        ids.update(f"AC-{n}" for n in range(int(lo), int(hi) + 1))
    return ids


def ac_source_errors(requirements_text: str, req_ids: set[str], ac_id_re: re.Pattern[str]) -> list[str]:
    """requirements.md の AC を閉じた形で読めないときの理由。空なら AC 集合を判定に使ってよい。

    閉じた形: 受入条件の節があり、定義が 1 件以上あり、節に出る AC ID がどれも定義として読める。
    読めない形はスクリプトが ok を出さず、gate が requirements.md を読んで判定する。
    """
    sections = _AC_SECTION_RE.findall(strip_fenced_blocks(requirements_text))
    if not sections:
        return ["requirements.md に `## 受入条件` の節が無い"]
    if not req_ids:
        return ["受入条件に `- AC-n:` の形の定義が無い（lint-ac.py が読める形でない）"]
    unread = sorted(set().union(*(ac_id_re.findall(sec) for sec in sections)) - req_ids)
    if unread:
        return [f"受入条件の節にあるが定義として読めない AC: {', '.join(unread)}"]
    return []


# PR Boundary の語彙（references/task-breakdown-steps.md）。後続の 2 値で始まる Stage の AC だけを除く。
# this-pr は実データにある current-pr の言い方。どちらでもない値（空・記入例・未知の語）は読めない
_FOLLOW_UP_BOUNDARY_RE = re.compile(r"^(?:follow-up-pr|post-merge-verification)\b")
_CURRENT_BOUNDARY_RE = re.compile(r"^(?:current-pr|this-pr)\b")


def deferred_acs(requirements_text: str, ac_id_re: re.Pattern[str]) -> tuple[set[str], list[str]]:
    """Implementation Sequence Plan で後続の Stage にだけ置いた AC と、PR Boundary を読めない行。

    `PR Boundary` の欄と、名前に `AC` を含む欄の両方がある表だけを読む。読めない Plan は何も除かない。
    current-pr の Stage にもある AC は除かない。
    """
    follow_up: set[str] = set()
    current: set[str] = set()
    errors: list[str] = []
    for section in _PLAN_SECTION_RE.findall(strip_fenced_blocks(requirements_text)):
        for table in _tables(section):
            header = table[0]
            ac_cols = [i for i, name in enumerate(header) if "AC" in name]
            if "PR Boundary" not in header or not ac_cols:
                continue
            boundary = header.index("PR Boundary")
            for row in table[1:]:
                if len(row) != len(header):
                    named = sorted(set().union(*(_ac_ids(c, ac_id_re) for c in row)))
                    if named:
                        errors.append(f"Plan の行の欄の数が見出しと合わない（{', '.join(named)}）: {_one_line(' | '.join(row))[:120]}")
                    continue
                value = row[boundary].strip("`* ")
                ids = set().union(*(_ac_ids(row[i], ac_id_re) for i in ac_cols))
                if _FOLLOW_UP_BOUNDARY_RE.match(value):
                    follow_up |= ids
                elif _CURRENT_BOUNDARY_RE.match(value):
                    current |= ids
                elif ids:
                    errors.append(f"PR Boundary を読めない: {value or '（空）'}（{', '.join(sorted(ids))}）")
    return follow_up - current, errors


_TASK_LIST_SECTION_RE = re.compile(r"^##[ \t]+(?:Current Task|Pending Tasks|Completed Tasks)\b")


def _task_section_lines(text: str):
    """task の範囲の行。tasklist.md の Current Task・Pending Tasks・Completed Tasks の節と、task の見出し
    （tasklist_parse.classify_task_line。worklog.md へ退避したもの）から、同じか上の階層の次の見出しまで。"""
    in_list = False
    level = 0  # task の見出しの階層。0 は task の外
    for line in strip_fenced_blocks(text).splitlines():
        stripped = line.strip()
        heading = _HEADING_RE.match(stripped)
        if heading and len(heading.group(1)) <= 2:
            in_list = bool(_TASK_LIST_SECTION_RE.match(stripped))
        if classify_task_line(stripped) == "task":
            level = len(heading.group(1)) if heading else 6
        elif heading and len(heading.group(1)) <= level:
            level = 0
        if in_list or level:
            yield line


def uncovered_acs(req_ids: set[str], texts: list[str], ac_id_re: re.Pattern[str]) -> list[str]:
    """requirements.md の AC のうち、どの task の節の `AC:`・`Covers AC:` 欄にも無いもの。

    texts は tasklist.md と worklog.md（完了タスクは容量の上限で worklog.md へ退避される）。
    """
    covered: set[str] = set()
    for text in texts:
        for m in _COVERS_LINE_RE.finditer("\n".join(_task_section_lines(text))):
            covered |= _ac_ids(m.group(1), ac_id_re)
    return sorted(req_ids - covered)


def follow_up_stage_errors(requirements_text: str) -> list[str]:
    """Planned Follow-up Stage Lane の欄の不備。Lane が無い・済みの Stage だけなら空。"""
    if _STAGE_LANE_HEADING in requirements_text and any(ch in requirements_text for ch in NON_NEWLINE_LINE_BREAKS):
        return ["LF・CR 以外の行区切りがあり、Lane の行を読めない"]
    errors: list[str] = []
    for m in _STAGE_LANE_SECTION_RE.finditer(strip_fenced_blocks(requirements_text)):
        section = m.group(1)
        if _UNCHECKED_ITEM_RE.search(section):
            errors.append("Lane に未完の項目（`- [ ]`）があり、欄を読めない")
            continue
        # 字下げの行は直前の項目の続き。字下げしていない行がどれも `- [x]` なら、済みの Stage だけの Lane
        heads = [ln for ln in section.splitlines() if ln.strip() and not ln[:1].isspace()]
        if heads and all(_CHECKED_ITEM_RE.match(ln) for ln in heads):
            continue
        tables = _tables(section)
        if not tables:
            errors.append("Lane が表でない（欄を読めない）")
            continue
        for table in tables:
            header, rows = table[0], table[1:]
            absent = [f for f in LANE_FIELDS if f not in header]
            if absent:
                errors.append(f"Lane の表に欄が無い: {', '.join(absent)}")
                continue
            for row in rows:
                if len(row) != len(header):
                    errors.append(f"Lane の行の欄の数が見出しと合わない: {' | '.join(row)}")
                    continue
                values = dict(zip(header, row))
                stage = values["Pending Stage ID"] or "?"
                empty = [f for f in LANE_FIELDS if not values[f] or _PLACEHOLDER_RE.match(values[f])]
                if empty:
                    errors.append(f"{stage}: 欄が埋まっていない: {', '.join(empty)}")
                tracking = values["Tracking Destination"]
                if _NONE_RE.match(tracking) and not _NONE_RE.sub("", tracking).strip():
                    errors.append(f"{stage}: Tracking Destination=none に理由が無い")
    return errors


def _is_separator(line: str) -> bool:
    return line.strip().startswith("|") and all(_SEPARATOR_CELL_RE.match(c) for c in _cells(line))


_BROKEN_HEADER: list[str] = []  # 欄が欠けた Ledger の見出し。見出しの不備で止まるので、下の行は読まない


def _is_ledger_header(cells: list[str], line: str, ac_core_re: re.Pattern[str]) -> bool:
    return "AC ID" in cells and not ac_core_re.search(line)


def legacy_ledger_headings(text: str) -> list[str]:
    """tasklist.md・worklog.md の、閉じた fence の外にある Ledger の見出し（旧来の置き場所）。"""
    return [_one_line(m.group(0))[:120] for m in _LEGACY_LEDGER_HEADING_RE.finditer(strip_fenced_blocks(text))]


def ledger_errors(req_ids: set[str], text: str, ac_id_re: re.Pattern[str], ac_core_re: re.Pattern[str],
                  known_ids: set[str]) -> tuple[list[str], list[str]]:
    """ac-ledger.md（AC Trace Ledger の専用ファイル）の (不備, 読めない行)。

    append-only なので AC ごとに最後の行で判定する。status は `verified`（`status=verified` の接頭辞つきを
    含む）だけを通す。ファイルで受け付ける行は、空行・`AC Trace Ledger` の見出し・表の区切り・Ledger の見出し
    （区切りが続き、`AC ID` の欄があり、行に AC ID〔ac_core_re。境界なし〕が無い）・Ledger の行（欄の数が
    見出しと同じで、AC ID の欄が requirements.md で定義された AC で、ほかの欄に別の AC ID が無い）だけにする。
    それ以外の行（注記・ほかの見出し・箇条書き・別の表・fence の行など）は「読めない行」として返し、
    呼び出し側は gate に読ませる。
    """
    errors: list[str] = []
    unreadable: list[str] = []
    last: dict[str, dict[str, str]] = {}
    header: list[str] | None = None
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if not line.strip() or _is_separator(line):
            continue  # 表の続きは同じ見出しで読む
        if _LEDGER_TITLE_RE.match(line):
            header = None  # 見出しの後の表は、その表の見出しで読む
            continue
        cells = _cells(line) if line.strip().startswith("|") else []
        if i + 1 < len(lines) and _is_separator(lines[i + 1]):  # 区切りが続く行は表の見出し
            if _is_ledger_header(cells, line, ac_core_re):
                absent = [f for f in LEDGER_FIELDS if f not in cells]
                if absent:
                    errors.append(f"Ledger の表に欄が無い: {', '.join(absent)}")
                header = _BROKEN_HEADER if absent else cells
            else:
                unreadable.append(_one_line(line)[:120])
                header = None  # 別の表の見出し。その下の行を前の Ledger の見出しで読まない
            continue
        if header is _BROKEN_HEADER and cells:
            continue
        if header and len(cells) == len(header):
            values = dict(zip(header, cells))
            ac = values["AC ID"]
            others = " ".join(v for k, v in values.items() if k != "AC ID")
            if ac_id_re.fullmatch(ac) and ac in known_ids \
                    and all(found_id == ac for found_id in ac_core_re.findall(others)):
                last[ac] = values
                continue
        unreadable.append(_one_line(line)[:120])
    for ac in sorted(req_ids):
        if ac not in last:
            errors.append(f"{ac}: Ledger の行が無い")
            continue
        values = last[ac]
        status = re.sub(r"^status\s*=\s*", "", values["status"], flags=re.IGNORECASE).strip().lower()
        if status != "verified":
            errors.append(f"{ac}: 最後の行の status が verified でない: {values['status']}")
        if not values["検証コマンド/結果"]:
            errors.append(f"{ac}: 最後の行の検証コマンド/結果が空")
    return errors, unreadable
