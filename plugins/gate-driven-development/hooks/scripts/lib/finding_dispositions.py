"""steering の `review-findings.md`（reviewer の指摘の ID と行き先）を読む述語。読むだけで、何も書かない。

正本: references/finding-dispositions.md。値域・行き先の規則を変えるときは、正本とこのファイルを同時に変える。
入口は scripts/check-finding-dispositions.py（impl-gating Step 8 で、Round の判定を決める前）と scripts/check-gate-ledger.sh の
`findings` 行（push・PR の前。`Independent Review` 行の件数との突き合わせは ir_count_errors）。
自由文は解析しない。読めない形（見出し・表の形・欄の数が違う、表の外の行）は誤りとして返す。
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

# reviewer-common.md § finding category の 9 値と、実害クラス（is_blocking）。
CATEGORIES = (
    "security-boundary", "approval-path", "fail-open", "data-loss",
    "product", "test-power", "bookkeeping", "doc-claim", "style",
)
BLOCKING_CATEGORIES = ("security-boundary", "approval-path", "fail-open", "data-loss")
SEVERITIES = ("high", "medium", "low")
ADVISORY_REASONS = ("out_of_scope", "insufficient_evidence", "calibration", "unverified_file")
# 検証役（agents/gdd-finding-verifier.md）の verdict。`-` は検証役を通していない
VERDICTS = ("confirmed", "refuted", "unverifiable", "-")
# 検証役が refuted と言わないと付けられない行き先（high・実害クラスの advisory は calibration・unverified_file だけ。unverified_file は根拠が absent@<sha> の行を除く）
_NEEDS_REFUTE_SERIOUS = ("calibration", "unverified_file")
TABLE_HEADER = "| id | severity | category | file:line | 行き先 | 検証 | 根拠 |"
# 根拠の path が merge-base にも tip にも無いと CLI が判定した行（impl-gating Step 1c）。sha はその判定の時点（節の sha）
ABSENT_RE = re.compile(r"^absent@[0-9a-fA-F]{7,40}$")
# `path:行` か `path:行-行`（前後のバッククォートは可）。path は許可リストの文字だけで読む
LOCATION_RE = re.compile(r"`?([\w./@+~-]+):[1-9][0-9]*(?:-[0-9]+)?`?")

_SECTION_RE = re.compile(
    r"^## (?P<name>(?P<kind>IG|IR)[1-9][0-9]*) \| (?:task: (?P<task>[^|]*?[^|\s]) \| )?sha: (?P<sha>[^|]*?[^|\s])"
    r"(?: \| round: (?P<round>[^|]*?[^|\s]))? \| findings: (?P<n>0|[1-9][0-9]*)$"
)
_SHA_RE = re.compile(r"^[0-9a-fA-F]{7,40}$")
_ROUND_RE = re.compile(r"^(?:0|[1-9][0-9]*)$")
_SEPARATOR_RE = re.compile(r"^\|(?:\s*:?-+:?\s*\|){7}$")
_DEST_RE = re.compile(
    r"^(?:blocking|advisory(?::(?P<reason>[a-z_]+))?|rejected:refuted"
    r"|rejected:duplicate:(?P<dup>\S+)|re-reported:(?P<prior>\S+))$"
)


@dataclass
class Row:
    rid: str
    severity: str
    category: str
    location: str
    dest: str
    verify: str
    evidence: str


@dataclass
class Section:
    name: str
    kind: str
    tasks: tuple[str, ...]
    sha: str
    round: str | None
    count: int
    rows: list[Row] = field(default_factory=list)


def parse(text: str) -> tuple[list[Section], list[str]]:
    """巡の節の一覧と、形の誤りを返す。誤りがあっても読めた節は返す。"""
    sections: list[Section] = []
    errors: list[str] = []
    current: Section | None = None
    state = "top"  # top → (節の見出し) → head → (表の見出し) → sep → (区切り) → rows
    for lineno, line in enumerate(text.split("\n"), 1):
        stripped = line.strip()
        if not stripped:
            continue
        m = _SECTION_RE.match(stripped)
        if m:
            tasks = tuple(t.strip() for t in m["task"].split(",")) if m["task"] else ()
            current = Section(m["name"], m["kind"], tasks, m["sha"].strip(), m["round"], int(m["n"]))
            sections.append(current)
            state = "head"
            if (m["kind"] == "IG") != bool(tasks) or (m["kind"] == "IG") != (m["round"] is not None):
                errors.append(f"{lineno} 行: {m['name']} の見出しの欄が違う（IG は task:・sha:・round:、IR は sha: だけ）")
            elif not _SHA_RE.match(current.sha):
                errors.append(f"{lineno} 行: {m['name']} の sha が 7〜40 桁の hex でない")
            elif m["round"] is not None and not _ROUND_RE.match(m["round"]):
                errors.append(f"{lineno} 行: {m['name']} の round が 0 以上の整数でない")
            continue
        if state == "top" and stripped.startswith("# ") and not sections:
            continue
        if state == "head" and stripped == TABLE_HEADER:
            state = "sep"
            continue
        if state == "sep" and _SEPARATOR_RE.match(stripped):
            state = "rows"
            continue
        if state == "rows" and stripped.startswith("|") and stripped.endswith("|"):
            cells = [c.strip() for c in stripped[1:-1].split("|")]
            if len(cells) != 7:
                errors.append(f"{lineno} 行: 表の欄が 7 つでない")
                continue
            rid, severity, category, location, dest, verify, evidence = cells
            current.rows.append(Row(rid, severity, category, location, dest, verify, evidence))
            continue
        errors.append(f"{lineno} 行: 読めない行（巡の見出し・表の見出し・区切り・表の行のどれでもない）")
    return sections, errors


def same_sha(a: str, b: str) -> bool:
    """短い方が長い方の先頭と一致すれば同じ commit とみなす（どちらも 7 桁以上の hex）。"""
    if not (_SHA_RE.match(a) and _SHA_RE.match(b)):
        return False
    a, b = a.lower(), b.lower()
    return a.startswith(b) or b.startswith(a)


def location_path(text: str) -> str | None:
    """`file:line` の欄が 1 つの `path:行` なら path を、外れた形なら None を返す（NFC に寄せる）。"""
    m = LOCATION_RE.fullmatch(unicodedata.normalize("NFC", text.strip()))
    return m[1] if m else None


def _is_serious(row: Row) -> bool:
    return row.severity == "high" or row.category in BLOCKING_CATEGORIES


def _lighter(target: Row, row: Row) -> bool:
    """duplicate の参照先が参照元より軽い（severity が下か、参照元だけが実害クラス）。"""
    rank = {s: i for i, s in enumerate(SEVERITIES)}  # high=0 が最も重い
    if rank.get(target.severity, len(rank)) > rank.get(row.severity, len(rank)):
        return True
    return row.category in BLOCKING_CATEGORIES and target.category not in BLOCKING_CATEGORIES


def _dest_errors(sec: Section, row: Row, ids: dict[str, Row], earlier: dict[str, Row],
                 earlier_tasks: set[str]) -> list[str]:
    m = _DEST_RE.match(row.dest)
    if not m:
        return [f"{row.rid}: 行き先 `{row.dest}` が値域の外"]
    reason = m["reason"]
    if reason is not None and reason not in ADVISORY_REASONS:
        return [f"{row.rid}: advisory の理由 `{reason}` が値域の外"]
    errors: list[str] = []
    if row.verify == "refuted" and location_path(row.evidence) is None:
        errors.append(f"{row.rid}: 検証役が refuted と判定した行の根拠（path:line）が無い")
    if ABSENT_RE.match(row.evidence):
        if not same_sha(row.evidence.removeprefix("absent@"), sec.sha):
            errors.append(f"{row.rid}: absent@ の sha が節の sha（その Round の HEAD）と違う")
        if location_path(row.location) is None:
            errors.append(f"{row.rid}: absent@ の行の file:line が 1 つの path:行 でない")
    if m["dup"] is not None:
        target = ids.get(m["dup"])
        if target is None or target is row:
            errors.append(f"{row.rid}: duplicate の参照先 {m['dup']} が同じ巡に無い")
        elif target.dest.startswith("rejected:duplicate:"):
            errors.append(f"{row.rid}: duplicate の参照先 {m['dup']} も duplicate（連鎖にしない）")
        elif target.dest.startswith("rejected:") or target.verify == "refuted" or ABSENT_RE.match(target.evidence):
            errors.append(f"{row.rid}: duplicate の参照先 {m['dup']} が捨てた・下げた行（rejected・refuted・absent@）")
        elif _lighter(target, row):
            errors.append(f"{row.rid}: duplicate の参照先 {m['dup']} が参照元より軽い（severity・実害クラス）")
    if row.verify not in VERDICTS:
        errors.append(f"{row.rid}: 検証 `{row.verify}` が値域の外")
    elif row.dest == "rejected:refuted" and row.verify != "refuted":
        errors.append(f"{row.rid}: rejected:refuted は検証役が refuted と判定した行だけ")
    elif _is_serious(row) and reason in _NEEDS_REFUTE_SERIOUS and row.verify != "refuted" and not (
            reason == "unverified_file" and ABSENT_RE.match(row.evidence)):
        errors.append(f"{row.rid}: high・実害クラスを `{row.dest}` に下げるのは検証役が refuted と判定した行"
                      "（unverified_file は根拠が absent@<sha> の行も）だけ")
    if m["prior"] is not None:
        if m["prior"] not in earlier:
            errors.append(f"{row.rid}: re-reported の参照先 {m['prior']} が前の巡に無い")
        elif sec.kind == "IR" and _lighter(row, earlier[m["prior"]]):
            # 独立レビューの件数から high・実害クラスを隠さない。IG では、一部を直した後に軽くした再報告を止めない
            errors.append(f"{row.rid}: re-reported の行が参照先 {m['prior']} より軽い（severity・実害クラス）")
    if _is_serious(row) and row.dest.startswith("advisory"):
        if sec.kind == "IR":
            errors.append(f"{row.rid}: 独立レビューの high・実害クラスは advisory にできない（independent-review.md (3-d)）")
        elif reason is None or reason == "insufficient_evidence":
            errors.append(f"{row.rid}: high・実害クラスを `{row.dest}` にできない")
        elif reason == "calibration" and row.category in BLOCKING_CATEGORIES:
            errors.append(f"{row.rid}: 実害クラスは calibration で advisory にできない")
        elif reason == "out_of_scope" and not set(sec.tasks) <= earlier_tasks:
            errors.append(f"{row.rid}: high・実害クラスの out_of_scope は、節の task がどれも前の IG 節にある（再入の）ときだけ")
    return errors


def structure_errors(text: str) -> list[str]:
    """review-findings.md 全体の誤り（形・連番・値域・行き先の規則）。空なら正しい。"""
    sections, errors = parse(text)
    seen_names: set[str] = set()
    earlier: dict[str, Row] = {}
    earlier_tasks: set[str] = set()
    next_number = {"IG": 1, "IR": 1}
    for sec in sections:
        if sec.name in seen_names:
            errors.append(f"{sec.name}: 同じ巡の見出しが 2 つある")
        seen_names.add(sec.name)
        expected = f"{sec.kind}{next_number[sec.kind]}"
        if sec.name != expected:
            errors.append(f"{sec.name}: 節の番号が steering 通しの連番でない（ファイルの順で {expected} のはず）")
        next_number[sec.kind] += 1
        ids: dict[str, Row] = {}
        reviewer_ks: list[int] = []
        main_ks: list[int] = []
        for row in sec.rows:
            m = re.fullmatch(rf"{re.escape(sec.name)}-(m?)([1-9][0-9]*)", row.rid)
            if not m:
                errors.append(f"{sec.name}: id `{row.rid}` が `{sec.name}-<n>` か `{sec.name}-m<n>` でない")
                continue
            if row.rid in ids:
                errors.append(f"{row.rid}: id が重複している")
            ids[row.rid] = row
            (main_ks if m[1] else reviewer_ks).append(int(m[2]))
            if row.severity not in SEVERITIES:
                errors.append(f"{row.rid}: severity `{row.severity}` が値域の外")
            if row.category not in CATEGORIES:
                errors.append(f"{row.rid}: category `{row.category}` が値域の外")
            if m[1] and not row.dest.startswith("re-reported:"):
                errors.append(f"{row.rid}: main が足した行（m）の行き先は re-reported だけ")
        if reviewer_ks != list(range(1, sec.count + 1)):
            errors.append(f"{sec.name}: reviewer の指摘の id が findings: {sec.count} の 1〜{sec.count} の連番でない")
        if sorted(main_ks) != list(range(1, len(main_ks) + 1)):
            errors.append(f"{sec.name}: main が足した行の id が m1 からの連番でない")
        for row in ids.values():
            errors.extend(_dest_errors(sec, row, ids, earlier, earlier_tasks))
        earlier.update(ids)
        earlier_tasks.update(sec.tasks)
    return errors


def ir_counts(sec: Section) -> tuple[int, int, int]:
    """独立レビューの巡の (high, medium, blocking)。independent-review.md (3-b)(3-c) の数え方。"""
    high = medium = blocking = 0
    for row in sec.rows:
        if row.dest.startswith("rejected:duplicate:"):
            continue
        if row.severity == "high":
            high += 1
        elif row.dest != "advisory:out_of_scope":
            medium += 1
        if row.category in BLOCKING_CATEGORIES:
            blocking += 1
    return high, medium, blocking


def ir_count_errors(text: str, sha: str, high: int, medium: int, blocking: int) -> tuple[str, list[str]]:
    """`Independent Review` 行（sha・件数）に当たる巡の節を突き合わせる。(状態, 誤り) を返す。

    状態は ok / missing（その sha の IR の節が無い）/ invalid（形の誤り、件数の食い違い、同じ sha の前の節の high・実害クラスに最後の節の re-reported が無い）。
    sha は前方一致で比べる（same_sha）。引き継ぎは re-reported を元の id まで辿って比べる。
    """
    errors = structure_errors(text)
    sections, _ = parse(text)
    matched = [s for s in sections if s.kind == "IR" and same_sha(s.sha, sha)]
    if not matched:
        return ("invalid" if errors else "missing"), errors + [f"sha {sha} の IR の節が無い"]
    # 同じ tip を 2 回レビューしたら行は後の巡で上書きされるので、最後の節と突き合わせる。
    # tip が同じなら前の節すべての high・実害クラスは直っていないので、最後の節に re-reported が要る
    last = matched[-1]
    rows = {r.rid: r for s in sections for r in s.rows}

    def root(rid: str) -> str:
        seen: set[str] = set()
        while rid not in seen and rid in rows and rows[rid].dest.startswith("re-reported:"):
            seen.add(rid)
            rid = rows[rid].dest.removeprefix("re-reported:")
        return rid

    carried = {root(r.rid) for r in last.rows if r.dest.startswith("re-reported:")}
    for s in matched[:-1]:
        for r in s.rows:
            if _is_serious(r) and not r.dest.startswith("rejected:duplicate:") and root(r.rid) not in carried:
                errors.append(f"{r.rid}: 同じ sha の {last.name} に、{r.rid} を引き継ぐ re-reported の行が無い")
    got = ir_counts(last)
    if got != (high, medium, blocking):
        errors.append(
            f"{last.name} の件数 high {got[0]}・medium {got[1]}・blocking {got[2]} が "
            f"Independent Review の high {high}・medium {medium}・blocking {blocking} と違う"
        )
    return ("invalid" if errors else "ok"), errors
