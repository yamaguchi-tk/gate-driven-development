#!/usr/bin/env python3
"""Lint AC ID consistency between requirements.md and tasklist.md.

GDD では AC（Acceptance Criteria）が:
  - `requirements.md` の `## 受入条件` 配下に `- AC-N:` で定義され
  - `tasklist.md` の `Verification` 行で `method=ac:<id>` で参照される
  - `tasklist.md` の `#### RED Evidence` セクションで `- AC: <ID>` 行として紐付けられる

両者の AC ID が同期していないと:
  - AC 追加忘れ（requirements にあるが tasklist で verify されない）
  - 古い AC ID 参照（tasklist が削除済み AC を verify しようとする）
  - AC ID typo（`AC-3` と `AC-3a` の区別ミス）
  - RED Evidence の AC ID 未紐付け（gdd-test-driven-development § AC ID Binding 必須違反）
  - RED Evidence が requirements.md に存在しない架空 AC を参照

を completion-check / pr-review まで検出できない。この lint で planning / build 段階で潰す。

Exit code:
  0: pass (warning は出力するが exit は 0)
  1: ERROR（tasklist が requirements に無い AC ID を参照、または重複定義）
  2: usage error / file not found

Usage:
  lint-ac.py <requirements.md path> [<tasklist.md path>]
  lint-ac.py --steering-dir <.steering/<task>/ path>
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# AC ID core token: AC-1, AC-2a, AC-3b, AC-F1, AC-3-d, AC-E9-1, AC-E9-1a, etc.
# (optional component letter) + digits + (optional -digits/-letter compound suffix)
# + (optional trailing letter)
# 複合サフィックスは数字（`AC-8-2`）と英字（`AC-3-d`）の両方を受ける。英字を受けないと
# `AC-3-d` が `AC-3` に潰れ、定義側も参照側も同じ ID になって矛盾が検出できない。
_AC_ID_CORE = r"AC-[A-Za-z]?\d+(?:-(?:\d+|[a-z]))?[a-z]?"
AC_ID_RE = re.compile(r"\b" + _AC_ID_CORE + r"\b")
# ID と `:` の間に入る注記（`- **AC-8-2**（DH-1、人間承認済み）: ...`）。
# 括弧で閉じた塊のみを許容し、注記の直後に `:` が来ることを要求する。こうしないと
# 本文中の `- AC-2 (前述) は対象外: ...` のような偶発的言及まで定義扱いになる。
_AC_DEF_ANNOTATION = r"(?:\s*(?:（[^）\n]*）|\([^)\n]*\)|［[^］\n]*］|\[[^\]\n]*\]|【[^】\n]*】))*"
# Bullet definition in requirements.md（開き `**` と閉じ `**` の両方を許容する: `- **AC-1**: ...`）
AC_DEF_RE = re.compile(
    r"^\s*[-*]\s*(\*\*)?\s*(" + _AC_ID_CORE + r")\s*(?:\*\*)?" + _AC_DEF_ANNOTATION + r"\s*[:：]",
    re.MULTILINE,
)
# Verification reference in tasklist.md: `method=ac:AC-3a` or `method: ac:AC-3a`
AC_REF_RE = re.compile(r"method\s*[=:]?\s*ac\s*:\s*(" + _AC_ID_CORE + r")")
# RED Evidence section header in tasklist.md
RED_EVIDENCE_HEADING_RE = re.compile(r"^####\s+RED\s+Evidence", re.MULTILINE | re.IGNORECASE)
# AC line within a RED Evidence section: `- AC: AC-1` or `- AC: AC-1, AC-2`
RED_AC_LINE_RE = re.compile(r"^\s*[-*]\s*AC\s*:\s*(.+)$", re.MULTILINE)


def extract_ac_ids_from_requirements(text: str) -> tuple[set[str], list[str]]:
    """Extract defined AC IDs from requirements.md markdown bullets.

    Returns (unique_set, all_with_duplicates).
    """
    matches = AC_DEF_RE.findall(text)
    ids = [m[1] for m in matches]
    return set(ids), ids


def requirements_has_yaml_ac_frontmatter(text: str) -> bool:
    """Detect a no-longer-supported YAML frontmatter AC block (`acceptance_criteria`).

    Callers must ERROR on this rather than silently treating it as "no AC
    defined": an empty `req_ids` from an unmigrated YAML-only requirements.md
    would otherwise make `check_red_evidence_ac_binding`'s `if defined_ac_ids:`
    guard skip orphan-AC detection entirely (PR #96 review, fail-open, HIGH).
    """
    if not text.startswith("---\n") and not text.startswith("---\r\n"):
        return False
    end_marker = text.find("\n---", 4)
    if end_marker < 0:
        return False
    fm_text = text[4:end_marker]
    return re.search(r"(?m)^\s*acceptance_criteria\s*:", fm_text) is not None


def extract_ac_ids_from_tasklist(text: str) -> set[str]:
    """Extract referenced AC IDs from tasklist.md Verification block."""
    return set(AC_REF_RE.findall(text))


def extract_red_evidence_sections(text: str) -> list[tuple[int, str]]:
    """Extract RED Evidence sections from tasklist.md.

    Returns a list of (line_number, section_body_until_next_heading) tuples.
    Each section starts after a `#### RED Evidence` heading and ends at the
    next heading (any level) or end of file.
    """
    sections: list[tuple[int, str]] = []
    lines = text.splitlines(keepends=True)
    in_section = False
    start_line = 0
    buffer: list[str] = []
    for i, line in enumerate(lines, start=1):
        if RED_EVIDENCE_HEADING_RE.match(line):
            if in_section:
                sections.append((start_line, "".join(buffer)))
            in_section = True
            start_line = i
            buffer = []
            continue
        if in_section:
            # End section on next heading (##, ###, ####, #####)
            if re.match(r"^#{2,5}\s", line):
                sections.append((start_line, "".join(buffer)))
                in_section = False
                buffer = []
                continue
            buffer.append(line)
    if in_section:
        sections.append((start_line, "".join(buffer)))
    return sections


def check_red_evidence_ac_binding(
    text: str, defined_ac_ids: set[str]
) -> tuple[list[tuple[int, str]], list[tuple[int, list[str]]]]:
    """Check AC ID Binding compliance in RED Evidence sections.

    Returns (missing_ac_sections, orphan_ac_refs) where:
      - missing_ac_sections: list of (line_number, snippet) for sections without `AC:` line
      - orphan_ac_refs: list of (line_number, [unknown_ac_ids]) for sections referencing
        AC IDs not defined in requirements.md
    """
    missing: list[tuple[int, str]] = []
    orphans: list[tuple[int, list[str]]] = []

    for start_line, body in extract_red_evidence_sections(text):
        ac_match = RED_AC_LINE_RE.search(body)
        if not ac_match:
            # No `- AC:` line → AC ID Binding violation
            snippet = body.strip().splitlines()[0] if body.strip() else "(empty section)"
            missing.append((start_line, snippet[:80]))
            continue
        # Extract all AC IDs from the `AC:` line value
        ac_value = ac_match.group(1)
        referenced = AC_ID_RE.findall(ac_value)
        if not referenced:
            # `AC:` line exists but no valid AC ID format
            missing.append((start_line, f"AC line malformed: {ac_value.strip()[:60]}"))
            continue
        # `defined_ac_ids` が空集合でも「AC 未定義」を理由に架空 AC 参照を素通り
        # させない（req_ids が空になる原因は問わない：early planning・未対応の
        # YAML 表記いずれでも、RED Evidence が存在する AC を参照している以上は
        # 検査対象にする。PR #96 レビュー指摘 HIGH、fail-open クラスタ 2 巡目）。
        unknown = [ac for ac in referenced if ac not in defined_ac_ids]
        if unknown:
            orphans.append((start_line, unknown))

    return missing, orphans


def find_duplicates(items: list[str]) -> list[str]:
    seen: dict[str, int] = {}
    for x in items:
        seen[x] = seen.get(x, 0) + 1
    return sorted(k for k, v in seen.items() if v > 1)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("requirements_md", nargs="?", help="Path to requirements.md")
    parser.add_argument("tasklist_md", nargs="?", help="Path to tasklist.md (optional)")
    parser.add_argument(
        "--steering-dir",
        help="Path to .steering/<task>/ directory (auto-resolves requirements.md and tasklist.md)",
    )
    parser.add_argument("--quiet", action="store_true", help="Suppress WARN/INFO output")
    parser.add_argument("--strict", action="store_true", help="Treat WARN as ERROR")
    args = parser.parse_args()

    req_path: Path | None = None
    task_path: Path | None = None

    if args.steering_dir:
        d = Path(args.steering_dir)
        req_path = d / "requirements.md"
        task_path = d / "tasklist.md"
    else:
        if not args.requirements_md:
            print("usage: lint-ac.py <requirements.md> [<tasklist.md>]", file=sys.stderr)
            print("       lint-ac.py --steering-dir <.steering/<task>/>", file=sys.stderr)
            return 2
        req_path = Path(args.requirements_md)
        if args.tasklist_md:
            task_path = Path(args.tasklist_md)

    if not req_path.is_file():
        print(f"ERROR: requirements.md not found: {req_path}", file=sys.stderr)
        return 2

    req_text = req_path.read_text(encoding="utf-8", errors="replace")
    req_ids, req_ids_all = extract_ac_ids_from_requirements(req_text)
    duplicate_defs = find_duplicates(req_ids_all)

    has_error = False
    has_warn = False

    # ERROR: duplicate definitions in requirements
    if duplicate_defs:
        print(f"ERROR: requirements.md に AC ID の重複定義があります: {duplicate_defs}")
        has_error = True

    if not req_ids:
        if requirements_has_yaml_ac_frontmatter(req_text):
            print(
                "ERROR: requirements.md の AC が YAML frontmatter（`acceptance_criteria`）で"
                "定義されていますが、この形式は撤去されました。`- AC-1: ...` の markdown "
                "bullet 形式へ移行してください。"
            )
            has_error = True
        elif not args.quiet:
            print(f"INFO: requirements.md に AC 定義が見つかりません ({req_path})")
        # AC 定義が本当に無い場合はエラーではない（early planning の可能性）

    # If tasklist.md is not provided or does not exist, lint only the requirements side
    if task_path is None or not task_path.is_file():
        if task_path is not None and not args.quiet:
            print(f"INFO: tasklist.md が存在しないため AC 参照側の lint は skip ({task_path})")
        if not args.quiet and req_ids:
            print(f"INFO: requirements.md で定義された AC ID: {sorted(req_ids)}")
        return 1 if has_error else 0

    task_text = task_path.read_text(encoding="utf-8", errors="replace")
    referenced_ids = extract_ac_ids_from_tasklist(task_text)

    # ERROR: tasklist が requirements に存在しない AC ID を参照
    orphan_refs = referenced_ids - req_ids
    if orphan_refs:
        print(f"ERROR: tasklist.md が requirements.md に存在しない AC ID を参照しています: {sorted(orphan_refs)}")
        print("       → requirements.md に該当 AC を追加するか、tasklist.md の Verification を修正してください")
        has_error = True

    # WARN: requirements にあるが tasklist で verify されていない AC ID
    unverified_acs = req_ids - referenced_ids
    if unverified_acs:
        msg = f"WARN: requirements.md にあるが tasklist.md で verify されない AC ID: {sorted(unverified_acs)}"
        if args.strict:
            print(f"ERROR (strict): {msg.removeprefix('WARN: ')}")
            has_error = True
        elif not args.quiet:
            print(msg)
            print("       → tasklist.md の Verification に method=ac:<id> 行を追加するか、AC を削除してください")
        has_warn = True

    # RED Evidence AC ID Binding check (gdd-test-driven-development § AC ID Binding 必須)
    missing_red, orphan_red = check_red_evidence_ac_binding(task_text, req_ids)
    if missing_red:
        msg_lines = [
            f"WARN: tasklist.md の RED Evidence セクションに `AC:` 行が未記載のものがあります（{len(missing_red)} 件）"
        ]
        for line_no, snippet in missing_red:
            msg_lines.append(f"       line {line_no} (`#### RED Evidence` 見出し行): {snippet}")
        msg_lines.append("       → state machine 一体型 TDD では RED Evidence に `AC: <ID>` 行が必須")
        msg_lines.append("       → 該当セクションに `- AC: AC-N` 行を追加するか、tasklist.md の Current Task に `Covers AC:` を追加してから RED を作り直してください")
        msg = "\n".join(msg_lines)
        if args.strict:
            print(f"ERROR (strict): {msg}")
            has_error = True
        elif not args.quiet:
            print(msg)
        has_warn = True

    if orphan_red:
        orphan_msg_lines = [
            f"ERROR: tasklist.md の RED Evidence が requirements.md に存在しない AC ID を参照しています（{len(orphan_red)} 件）"
        ]
        for line_no, unknown in orphan_red:
            orphan_msg_lines.append(f"       line {line_no} (`#### RED Evidence` 見出し行): {sorted(unknown)}")
        orphan_msg_lines.append("       → requirements.md の AC を確認し、実在する AC ID に修正してください（架空 AC は不可）")
        print("\n".join(orphan_msg_lines))
        has_error = True

    if not has_error and not has_warn and not args.quiet:
        print(f"OK: AC ID 整合性 pass（定義 {len(req_ids)} 件 / 参照 {len(referenced_ids)} 件）")

    return 1 if has_error else 0


if __name__ == "__main__":
    sys.exit(main())
