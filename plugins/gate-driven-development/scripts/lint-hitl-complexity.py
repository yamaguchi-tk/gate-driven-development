#!/usr/bin/env python3
"""Lint GDD HITL samples against a lightweight Complexity Budget.

この script は human-check の生成物サンプル向け。正本テンプレート全文には
詳細ルールが含まれるため、生成された HITL sample / fixture / PR evidence を
対象にする。

Exit code:
  0: pass
  1: budget exceeded
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
from lib.hitl_budget import HITL_SAMPLE_MAX_LINES
from lib.lint_base import check_file


APPROVAL_POINT_RE = re.compile(r"^\s*(?:\*\*)?(?:承認ポイント\s*)?\d+[.．]\s+|^\s*\|\s*\d+\s*\|")
TABLE_SEPARATOR_RE = re.compile(r"^\s*\|?\s*:?-{3,}:?\s*(?:\|\s*:?-{3,}:?\s*)+\|?\s*$")
INTERNAL_TERMS = (
    "holdout",
    "human-confirm",
    "executable",
    "no-post",
    "prod_equivalent",
    "production model env",
    "Route In Progress",
    "Next Action",
)


def count_tables(lines: list[str]) -> int:
    return sum(1 for line in lines if TABLE_SEPARATOR_RE.match(line))


def lint_text(
    text: str,
    *,
    max_lines: int,
    max_approval_points: int,
    max_tables: int,
    max_internal_terms: int,
) -> list[str]:
    lines = [line for line in text.splitlines() if line.strip()]
    approval_points = [line for line in lines if APPROVAL_POINT_RE.search(line)]
    table_count = count_tables(lines)
    internal_term_count = sum(text.count(term) for term in INTERNAL_TERMS)

    errors: list[str] = []
    if len(lines) > max_lines:
        errors.append(f"HITL行数 exceeds budget: {len(lines)} > {max_lines}")
    if len(approval_points) > max_approval_points:
        errors.append(f"承認ポイント数 exceeds budget: {len(approval_points)} > {max_approval_points}")
    if table_count > max_tables:
        errors.append(f"詳細表数 exceeds budget: {table_count} > {max_tables}")
    if internal_term_count > max_internal_terms:
        errors.append(f"内部用語数 exceeds budget: {internal_term_count} > {max_internal_terms}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", help="HITL sample path")
    parser.add_argument("--max-lines", type=int, default=HITL_SAMPLE_MAX_LINES)
    parser.add_argument("--max-approval-points", type=int, default=5)
    parser.add_argument("--max-tables", type=int, default=8)
    parser.add_argument("--max-internal-terms", type=int, default=12)
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    path = Path(args.path)
    if (rc := check_file(path)) is not None:
        return rc

    errors = lint_text(
        path.read_text(encoding="utf-8", errors="replace"),
        max_lines=args.max_lines,
        max_approval_points=args.max_approval_points,
        max_tables=args.max_tables,
        max_internal_terms=args.max_internal_terms,
    )
    if errors:
        print("ERROR: GDD Complexity Budget を超過しています。判断に効かない段落を外すか内部用語を説明してください（判断の筋書きは削らない。human-check-template.md § 判断の書き方）。")
        for error in errors:
            print(f"- {error}")
        return 1

    if not args.quiet:
        print("OK: GDD Complexity Budget passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
