#!/usr/bin/env python3
"""Lint mechanical consistency of a GDD plan (requirements.md / design.md).

AC は requirements.md の `## 受入条件` で定義し、次の場所では引用だけにする:
  - requirements.md の `## Summary Brief`（配下の `###` を含む）
  - requirements.md の `## Implementation Sequence Plan`
  - design.md の全体

検査すること:
  ERROR: 引用だけの場所に、受入条件に無い AC ID がある
  ERROR: 引用だけの場所に、AC の定義行（`- AC-1: ...`）がある（定義が 2 つになる）
  ERROR: requirements.md に `## 受入条件` 節が無い
  ERROR: コード fence が閉じていない（閉じ忘れの後ろは記入例と本文を区別できない）
  WARN:  AC ID を 1 つだけ含む引用行の数値（`20 分` など）が、その AC の定義にある
         同じ単位の数値のどれとも一致しない（自由文の照合なので warn だけにする）
  ERROR: `--entry requirements-reentry` のとき、reviews.md の最新 Round に `- 処置:` が無い、
         見出しが `- 処置:`（`（注記）` 可）の形でない、処置の行が 1 件 1 行の項目の形でない、
         1 件に `根拠:` か `伝播:` の欄が無い、reviews.md を読めない
         （欄の有無だけを見て、値は解析しない。形の正本は
         references/requirements-gating-steps.md § reviews.md の形式）
  ERROR: `--entry requirements` か `requirements-reentry` のとき、受入条件の AC（定義行から次の
         AC の定義行か見出しまで）に `根拠:` か `計測:` の欄が無い、`### 承認ポイント` の番号つき
         項目（`**方向性**` を除く。`3a.`・`3-1.` も 1 項目。次の項目か見出しまで）に `根拠:` の欄が
         無い、AC の定義が 0 件、承認ポイントの節か番号つき項目が無い（欄は箇条の先頭か ` / ` の後ろ
         だけを数え、値は解析しない。形の正本は references/requirements-template.md § requirements.md セクション一覧 の受入条件）

planning reviewer にこの突合をさせず、gate の main が reviewer を起動する前に回す
（正本: references/subagent-dispatch.md § Reviewer Input and Time Budget）。

Exit code:
  0: pass（WARN は出しても 0）
  1: ERROR
  2: usage error / requirements.md not found / --entry が無い

Usage:
  lint-plan-consistency.py --steering-dir <.steering/<task>/> --entry requirements|requirements-reentry|design
  lint-plan-consistency.py <requirements.md> [<design.md>] --entry ...
  （reviews.md は requirements.md と同じディレクトリのものを読む）
"""
from __future__ import annotations

import argparse
import importlib.util
import re
import sys
from pathlib import Path


def _load_lint_ac():
    # AC ID の文法は lint-ac.py を正本にする（書き写すと `AC-3-d` などの扱いがずれる）
    path = Path(__file__).resolve().parent / "lint-ac.py"
    spec = importlib.util.spec_from_file_location("gdd_lint_ac", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_lint_ac = _load_lint_ac()

# fence の走査は tasklist_parse を正本にする。記号の種類と長さを見て閉じ、閉じ忘れの
# 開き fence から後ろは検査に残す（読み飛ばすと ERROR が消える fail-open になる）。
# top-level module として読む（`lib` パッケージ名は scripts/lib と衝突する）。
_LIB_DIR = str(Path(__file__).resolve().parents[1] / "hooks" / "scripts" / "lib")
sys.path.insert(0, _LIB_DIR)
try:
    from tasklist_parse import _scan_fences  # noqa: E402
finally:
    if _LIB_DIR in sys.path:
        sys.path.remove(_LIB_DIR)
AC_ID_RE = _lint_ac.AC_ID_RE
AC_DEF_RE = _lint_ac.AC_DEF_RE

H2_RE = re.compile(r"^##\s+(.+?)\s*$")
# `3 分割`・`2 分岐` は分（時間）ではないので外す
NUMBER_RE = re.compile(r"(\d+(?:\.\d+)?)\s*(分(?![割岐類析散解])|秒|時間|行|件|回|日|巡|%|MB|KB)")

ACCEPTANCE = "受入条件"
CITE_ONLY_SECTIONS = ("Summary Brief", "Implementation Sequence Plan")


def unfenced_lines(text: str) -> list[tuple[int, str]]:
    """Return (line_no, line) outside closed code fences (例として書いた見出し・定義を数えない).

    閉じ忘れの fence は開きから後ろを返す。どちらに倒しても誤るので、main が ERROR にする。
    """
    lines, closed, _open_at, _spans = _scan_fences(text)
    return [(i + 1, line) for i, line in enumerate(lines) if i not in closed]


def split_h2_sections(text: str) -> list[tuple[str, int, str]]:
    """Return (heading, line_no, line) for every unfenced line, tagged by its `##` section."""
    rows: list[tuple[str, int, str]] = []
    current = ""
    for no, line in unfenced_lines(text):
        match = H2_RE.match(line)
        if match:
            current = match.group(1)
            continue
        rows.append((current, no, line))
    return rows


def unclosed_fence_line(text: str) -> int | None:
    _lines, _closed, open_at, _spans = _scan_fences(text)
    return open_at + 1 if open_at >= 0 else None


def numbers_by_unit(line: str) -> dict[str, set[str]]:
    found: dict[str, set[str]] = {}
    for value, unit in NUMBER_RE.findall(AC_ID_RE.sub(" ", line)):
        found.setdefault(unit, set()).add(value)
    return found


def check_cite_lines(
    label: str,
    rows: list[tuple[int, str]],
    defined: dict[str, str],
    errors: list[str],
    warnings: list[str],
    compare_table_rows: bool = True,
) -> None:
    for no, line in rows:
        if AC_DEF_RE.match(line + "\n"):
            errors.append(f"{label} line {no}: AC を定義し直している（受入条件の ID を引用だけにする）: {line.strip()}")
            continue
        cited = sorted(set(AC_ID_RE.findall(line)))
        unknown = [ac for ac in cited if ac not in defined]
        if unknown:
            errors.append(f"{label} line {no}: 受入条件に無い AC を引用している: {unknown}")
        if len(cited) != 1 or cited[0] not in defined:
            continue
        if not compare_table_rows and line.lstrip().startswith("|"):
            continue
        expected = numbers_by_unit(defined[cited[0]])
        for unit, values in numbers_by_unit(line).items():
            if unit in expected and not values & expected[unit]:
                shown = ", ".join(f"{v} {unit}" for v in sorted(values))
                want = ", ".join(f"{v} {unit}" for v in sorted(expected[unit]))
                warnings.append(
                    f"{label} line {no}: {cited[0]} の数値 {shown} が定義の {want} と食い違う"
                )


ROUND_RE = re.compile(r"^##\s+Round\b")
TREATMENT_HEADER_RE = re.compile(r"^- 処置\s*(?:（[^）]*）|\([^)]*\))?\s*[:：]\s*(.*)$")
TREATMENT_ITEM_RE = re.compile(r"^(?:[-*]|\d+[.)])\s")
# 行頭の記号・字下げ・強調を除いた先頭が `処置` の行は、決まった見出しの形でなければ止める
TREATMENT_LIKE_RE = re.compile(r"^[\s\-*+#>]*(?:\*\*|__)?\s*処置")
TREATMENT_FIELDS = ("根拠", "伝播")
ENTRIES = ("requirements", "requirements-reentry", "design")
HEADING_RE = re.compile(r"^#{1,6}\s")
APPROVAL_RE = re.compile(r"^###\s+承認ポイント\s*(?:[（(].*)?$")
# `3a.`・`3-1.` も 1 項目として数える（前の項目の続きにすると前の項目の欄で通る）
APPROVAL_ITEM_RE = re.compile(r"^\d+[0-9a-z-]*[.)]\s")
DIRECTION_RE = re.compile(r"^\d+[0-9a-z-]*[.)]\s+\*\*方向性")


def has_field(body: str, field: str) -> bool:
    """欄は箇条の先頭か ` / ` の直後に書いたものだけを数える（`判断根拠:`・`` `根拠:` ``・`再計測:` を欄にしない）。"""
    return re.search(r"(?:^\s*(?:[-*+]\s+)?|[/／]\s*)(?:\*\*)?" + field + r"(?:\*\*)?\s*[:：]", body, re.MULTILINE) is not None


def latest_round(text: str) -> list[tuple[int, str]]:
    """Return (line_no, line) of the last `## Round` section (閉じた fence の中を除く。閉じ忘れの後ろは読む)."""
    section: list[tuple[int, str]] = []
    inside = False
    for no, line in unfenced_lines(text):
        if ROUND_RE.match(line):
            section, inside = [], True
        elif H2_RE.match(line):
            inside = False
        elif inside:
            section.append((no, line))
    return section


def check_treatments(text: str, errors: list[str]) -> None:
    """requirements の再入の前に、最新 Round の処置の 1 件ごとに `根拠:`・`伝播:` があるかを見る。

    処置は Round の最後の塊で、1 件 1 行。最初の `- 処置:` からファイルの終わりまで（fence の中も）、
    空でない行は見出しか、同じ字下げの項目の形でなければならない。
    """
    first = None
    for no, line in latest_round(text):
        if not TREATMENT_LIKE_RE.match(line):
            continue
        if TREATMENT_HEADER_RE.match(line):
            first = no
            break
        errors.append(f"reviews.md line {no}: 処置の見出しが `- 処置:` の形でない: {line.strip()[:60]}")
    items: list[tuple[int, str]] = []
    headers = 0
    raw = text.splitlines()
    open_header, filled, indent = None, False, None
    for no in range(first or len(raw) + 1, len(raw) + 1):
        line = raw[no - 1]
        stripped = line.strip()
        if not stripped:
            continue
        header = TREATMENT_HEADER_RE.match(line)
        if header:
            if open_header and not filled:
                errors.append(f"reviews.md line {open_header}: 処置が空")
            headers += 1
            open_header, filled, indent = no, bool(header.group(1).strip()), None
            if filled:
                items.append((no, header.group(1).strip()))
            continue
        if TREATMENT_LIKE_RE.match(line):
            errors.append(f"reviews.md line {no}: 処置の見出しが `- 処置:` の形でない: {stripped[:60]}")
            continue
        width = len(line) - len(line.lstrip())
        if width == 0:
            errors.append(f"reviews.md line {no}: 処置の後ろに処置の項目でない行がある（処置は Round の最後に書く。備考などは処置の前か worklog.md に書く）: {stripped[:60]}")
            continue
        indent = width if indent is None else indent
        if width != indent or not TREATMENT_ITEM_RE.match(stripped):
            errors.append(f"reviews.md line {no}: 処置の行が 1 件 1 行の項目（`- `・`* `・`1. `）の形でない: {stripped[:60]}")
            continue
        items.append((no, stripped))
        filled = True
    if open_header and not filled:
        errors.append(f"reviews.md line {open_header}: 処置が空")
    if headers == 0:
        errors.append("reviews.md の最新 Round に `- 処置:` が無い（requirements の再入の前に、blocking ごとの処置を書く）")
    for item_no, item in items:
        for field in TREATMENT_FIELDS:
            if not has_field(item, field):
                errors.append(f"reviews.md line {item_no}: 処置に `{field}:` の欄が無い: {item[:60]}")


def field_blocks(text: str) -> tuple[list[tuple[int, str, tuple[str, ...], list[str]]], int, int | None]:
    """Return (blocks, AC の件数, 承認ポイントの番号つき項目の件数〔節が無ければ None〕)。閉じた fence の中を除く。

    blocks は AC と承認ポイントの項目ごとの (line_no, label, fields, lines)。
    """
    blocks: list[tuple[int, str, tuple[str, ...], list[str]]] = []
    acs, approvals = 0, None
    section = ""
    current: list[str] | None = None
    for no, line in unfenced_lines(text):
        if HEADING_RE.match(line):
            current = None
            h2 = H2_RE.match(line)
            if h2:
                section = h2.group(1)
            elif APPROVAL_RE.match(line):
                section = "承認ポイント"
                approvals = approvals or 0
            elif line.startswith("###") and section == "承認ポイント":
                section = ""
            continue
        ac = AC_DEF_RE.match(line + "\n") if section.startswith(ACCEPTANCE) else None
        if ac:
            current = [line]
            acs += 1
            blocks.append((no, ac.group(2), ("根拠", "計測"), current))
        elif section == "承認ポイント" and APPROVAL_ITEM_RE.match(line):
            current = None
            approvals = (approvals or 0) + 1
            # 方向性の除外はカテゴリの位置だけ（本文に太字の方向性がある項目は検査する）
            if not DIRECTION_RE.match(line):
                current = [line]
                blocks.append((no, "承認ポイント " + line.strip()[:40], ("根拠",), current))
        elif current is not None:
            current.append(line)
    return blocks, acs, approvals


def check_fields(text: str, errors: list[str]) -> None:
    """requirements の reviewer を起動する前に、AC と承認ポイントの項目ごとに欄があるかを見る（値は読まない）。"""
    blocks, acs, approvals = field_blocks(text)
    # 1 件も認識できなければ通さない（書式が違うと欄の検査が黙って抜ける）
    if acs == 0:
        errors.append(f"requirements.md の `## {ACCEPTANCE}` に AC の定義（`- AC-1: …`）が 1 件も無い")
    if not approvals:
        errors.append("requirements.md に `### 承認ポイント` の番号つき項目（`1. **<カテゴリ>**: …`）が無い（Human Check Questions を参照するだけにしない）")
    for no, label, fields, lines in blocks:
        body = "\n".join(lines)
        for field in fields:
            if not has_field(body, field):
                errors.append(
                    f"requirements.md line {no}: {label} に `{field}:` の欄が無い"
                    "（根拠: `file:line`・コマンドと値・`未測（理由）`・`なし（理由）`。計測: 何を・どの母集団で・どの値なら合格か）"
                )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("requirements_md", nargs="?")
    parser.add_argument("design_md", nargs="?")
    parser.add_argument("--steering-dir")
    parser.add_argument("--quiet", action="store_true", help="Suppress OK output")
    parser.add_argument(
        "--entry",
        choices=ENTRIES,
        help="requirements: requirements の初回（AC と承認ポイントの欄を見る）。requirements-reentry: requirements の再入（加えて処置の欄を見る）。design: design の起動",
    )
    args = parser.parse_args()
    if args.entry is None:
        print("ERROR: --entry が無い（requirements の初回なら requirements、再入なら requirements-reentry、design なら design）", file=sys.stderr)
        return 2

    if args.steering_dir:
        req_path = Path(args.steering_dir) / "requirements.md"
        design_path: Path | None = Path(args.steering_dir) / "design.md"
    elif args.requirements_md:
        req_path = Path(args.requirements_md)
        design_path = Path(args.design_md) if args.design_md else None
    else:
        parser.print_usage(sys.stderr)
        return 2
    if not req_path.is_file():
        print(f"ERROR: requirements.md not found: {req_path}", file=sys.stderr)
        return 2

    reviews_path = req_path.parent / "reviews.md"
    reviews_text: str | None = None
    if reviews_path.exists():
        try:
            reviews_text = reviews_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            reviews_text = None

    req_text = req_path.read_text(encoding="utf-8", errors="replace")
    rows = split_h2_sections(req_text)
    errors: list[str] = []
    unclosed = unclosed_fence_line(req_text)
    if unclosed is not None:
        errors.append(f"requirements.md line {unclosed}: コード fence が閉じていない")
    warnings: list[str] = []

    acceptance = [(no, line) for heading, no, line in rows if heading.startswith(ACCEPTANCE)]
    if not any(heading.startswith(ACCEPTANCE) for heading, _, _ in rows):
        errors.append(f"requirements.md に `## {ACCEPTANCE}` 節が無い")
    defined: dict[str, str] = {}
    for _, line in acceptance:
        match = AC_DEF_RE.match(line + "\n")
        if match:
            defined.setdefault(match.group(2), line)

    for section in CITE_ONLY_SECTIONS:
        section_rows = [(no, line) for heading, no, line in rows if heading.startswith(section)]
        # Implementation Sequence Plan の表は Stage ごとの見積もり diff 行数を持つので、数値を比べない
        check_cite_lines(
            f"requirements.md § {section}",
            section_rows,
            defined,
            errors,
            warnings,
            compare_table_rows=section != "Implementation Sequence Plan",
        )

    if design_path is not None and design_path.is_file():
        design_text = design_path.read_text(encoding="utf-8", errors="replace")
        unclosed = unclosed_fence_line(design_text)
        if unclosed is not None:
            errors.append(f"design.md line {unclosed}: コード fence が閉じていない")
        design_rows = unfenced_lines(design_text)
        check_cite_lines("design.md", design_rows, defined, errors, warnings)

    if args.entry in ("requirements", "requirements-reentry"):
        check_fields(req_text, errors)
    if args.entry == "requirements-reentry":
        if reviews_text is None:
            errors.append("reviews.md を読めない（requirements の再入には処置の記録が要る）")
        else:
            check_treatments(reviews_text, errors)

    for message in errors:
        print(f"ERROR: {message}")
    for message in warnings:
        print(f"WARN: {message}")
    if not errors and not warnings and not args.quiet:
        print(f"OK: 計画の整合 pass（AC 定義 {len(defined)} 件）")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
