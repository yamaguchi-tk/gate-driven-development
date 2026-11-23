#!/usr/bin/env python3
"""Lint `HITL Outcome Audit` rows in requirements.md.

completion-check は、human check で承認された Approved Direction と
最終成果物が一致しているかを `HITL Outcome Audit` で確認する。
`mismatch` / `unverified` が残る場合は completion を通さない。

Exit code:
  0: pass
  1: audit missing or has mismatch/unverified/invalid status
  2: usage error / file not found
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# hook は lib/kill-switch.sh で python3 を -I で起動し、PYTHONSAFEPATH も設定する。その下では、このファイルの
# ディレクトリが sys.path に入らない
if sys.flags.isolated or getattr(sys.flags, "safe_path", False):
    sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.lint_base import check_file


ALLOWED_PASS = {"match", "n/a", "na"}
BLOCKING = {"mismatch", "unverified"}
STATUS_RE = re.compile(r"\b(match|mismatch|unverified|N/A|NA)\b", re.IGNORECASE)


def extract_section(text: str, heading: str) -> str | None:
    pattern = re.compile(rf"^##\s+{re.escape(heading)}\s*$", re.MULTILINE)
    match = pattern.search(text)
    if not match:
        return None
    start = match.end()
    next_heading = re.search(r"^##\s+", text[start:], re.MULTILINE)
    end = start + next_heading.start() if next_heading else len(text)
    return text[start:end]


def lint_text(text: str) -> tuple[list[tuple[str, str]], list[str]]:
    section = extract_section(text, "HITL Outcome Audit")
    if section is None:
        return [], ["HITL Outcome Audit section is missing"]

    blocking_rows: list[tuple[str, str]] = []
    invalid_rows: list[str] = []
    data_row_count = 0
    for raw_line in section.splitlines():
        line = raw_line.strip()
        if not line.startswith("|") or "---" in line or "Approved Direction" in line:
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) < 3:
            continue
        data_row_count += 1
        status_cell = cells[2]
        status_match = STATUS_RE.search(status_cell)
        if not status_match:
            invalid_rows.append(line)
            continue
        status = status_match.group(1).lower()
        if status in BLOCKING:
            blocking_rows.append((status, line))
        elif status not in ALLOWED_PASS:
            invalid_rows.append(line)

    errors: list[str] = []
    if data_row_count == 0:
        errors.append("HITL Outcome Audit has no data rows")
    for row in invalid_rows:
        errors.append(f"invalid status row: {row}")
    return blocking_rows, errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", help="requirements.md path")
    parser.add_argument("--quiet", action="store_true", help="Suppress OK output")
    args = parser.parse_args()

    path = Path(args.path)
    if (rc := check_file(path)) is not None:
        return rc

    text = path.read_text(encoding="utf-8", errors="replace")
    blocking_rows, errors = lint_text(text)
    if blocking_rows or errors:
        print("ERROR: HITL Outcome Audit が未完了です。mismatch / unverified が残る場合は completion を通さないでください。")
        for error in errors:
            print(f"- {error}")
        for status, row in blocking_rows:
            print(f"- blocking status={status}: {row}")
        return 1

    if not args.quiet:
        print("OK: HITL Outcome Audit passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
