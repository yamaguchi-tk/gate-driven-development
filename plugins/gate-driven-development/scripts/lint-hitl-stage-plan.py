#!/usr/bin/env python3
"""Lint GDD human-check staged implementation plan tables.

This catches the failure mode where HITL "looks structured" but the staged
plan is not actionable for humans.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


REQUIRED_COLUMNS = [
    "Stage",
    "この段階でやること",
    "このPR/後続",
    "このOKで承認する範囲",
    "完了確認",
    "次に進む条件 / 人間に戻す条件",
    "後続の追跡先",
    "見積もり diff 行数",
]

VAGUE_VALUES = {
    "",
    "-",
    "TBD",
    "TODO",
    "N/A",
    "未定",
    "後で決める",
    "適切に",
    "必要なら",
    "実装する",
    "テストする",
}

VAGUE_PATTERNS = [
    "適切に",
    "必要に応じて",
    "必要なら",
    "別途管理",
    "テスト等",
    "確認する",
    "実装する",
]

# `事前回答で後続PRも実施許可` は、本人の事前回答が後続 Stage の着手の合図を代える値
# （references/human-check-template.md § 事前回答）。`このPRで実施許可` を部分文字列に含めない
# （下の暗黙承認の検査が部分一致で見るため）。
FOLLOW_UP_SCOPES = {"後続PRの方針のみ承認", "後続PR着手前に再承認", "事前回答で後続PRも実施許可"}

APPROVAL_SCOPES = {"このPRで実施許可"} | FOLLOW_UP_SCOPES

APPROVAL_BY_BOUNDARY = {
    "current-pr": {"このPRで実施許可"},
    "follow-up-pr": FOLLOW_UP_SCOPES,
    "post-merge-verification": FOLLOW_UP_SCOPES,
}


def parse_table(markdown: str) -> tuple[list[str], list[dict[str, str]]]:
    if "### 段階実装案" not in markdown:
        raise ValueError("missing section: ### 段階実装案")

    after = markdown.split("### 段階実装案", 1)[1]
    table_lines: list[str] = []
    for line in after.splitlines():
        stripped = line.strip()
        if stripped.startswith("### ") and table_lines:
            break
        if stripped.startswith("|"):
            table_lines.append(stripped)

    if len(table_lines) < 3:
        raise ValueError("段階実装案 table is missing or too short")

    header = [cell.strip() for cell in table_lines[0].strip("|").split("|")]
    separator = table_lines[1]
    if not re.fullmatch(r"\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?", separator):
        raise ValueError("段階実装案 table separator is invalid")

    missing = [column for column in REQUIRED_COLUMNS if column not in header]
    if missing:
        raise ValueError(f"段階実装案 table missing columns: {', '.join(missing)}")

    rows: list[dict[str, str]] = []
    for raw in table_lines[2:]:
        cells = [cell.strip() for cell in raw.strip("|").split("|")]
        if len(cells) != len(header):
            raise ValueError(f"段階実装案 row has {len(cells)} cells, expected {len(header)}: {raw}")
        rows.append(dict(zip(header, cells)))

    if not rows:
        raise ValueError("段階実装案 table has no stage rows")
    return header, rows


def is_vague(value: str) -> bool:
    normalized = value.strip()
    if normalized in VAGUE_VALUES:
        return True
    if re.fullmatch(r"<[^>]+>", normalized):
        return True
    if any(pattern in normalized for pattern in VAGUE_PATTERNS):
        return True
    return False


def _lint_boundary_and_approval(index: int, stage: str, row: dict[str, str]) -> list[str]:
    errors: list[str] = []
    boundary = row["このPR/後続"]
    approval = row["このOKで承認する範囲"]
    tracking = row["後続の追跡先"]

    if boundary not in {"current-pr", "follow-up-pr", "post-merge-verification"}:
        errors.append(f"row {index} {stage}: invalid このPR/後続: {boundary}")

    if approval not in APPROVAL_SCOPES:
        errors.append(f"row {index} {stage}: invalid このOKで承認する範囲: {approval}")
    elif boundary in APPROVAL_BY_BOUNDARY and approval not in APPROVAL_BY_BOUNDARY[boundary]:
        errors.append(f"row {index} {stage}: approval scope does not match PR boundary")

    if boundary in {"follow-up-pr", "post-merge-verification"}:
        if "このPRで実施許可" in approval:
            errors.append(f"row {index} {stage}: follow-up stage cannot be implicitly approved for implementation")
        if tracking in {"none", "なし", "N/A"}:
            errors.append(f"row {index} {stage}: follow-up stage needs a tracking destination")

    return errors


def lint(markdown: str, expected_stages: set[str]) -> list[str]:
    _header, rows = parse_table(markdown)
    errors: list[str] = []
    seen_stages: set[str] = set()

    for index, row in enumerate(rows, start=1):
        stage = row["Stage"]
        if stage in seen_stages:
            errors.append(f"row {index}: duplicate Stage value: {stage}")
        seen_stages.add(stage)
        if not re.fullmatch(r"S-\d+|single-stage", stage):
            errors.append(f"row {index}: invalid Stage value: {stage}")

        for column in REQUIRED_COLUMNS:
            value = row[column]
            if is_vague(value):
                errors.append(f"row {index} {stage}: vague or empty cell in {column}: {value!r}")

        errors.extend(_lint_boundary_and_approval(index, stage, row))

    missing_stages = sorted(expected_stages - seen_stages)
    extra_stages = sorted(seen_stages - expected_stages) if expected_stages else []
    if missing_stages:
        errors.append(f"missing expected Stage IDs: {', '.join(missing_stages)}")
    if extra_stages:
        errors.append(f"unexpected Stage IDs: {', '.join(extra_stages)}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("human_check", type=Path, help="Path to a human-check markdown draft or fixture")
    parser.add_argument("--expected-stage", action="append", default=[], help="Expected Stage ID; repeatable")
    args = parser.parse_args()

    markdown = args.human_check.read_text(encoding="utf-8")
    try:
        errors = lint(markdown, set(args.expected_stage))
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("OK: staged HITL plan is actionable")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
