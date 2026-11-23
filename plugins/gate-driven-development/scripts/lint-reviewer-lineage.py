#!/usr/bin/env python3
"""Lint Reviewer Lineage for bias / false positive 繰り返しを検出する。

同一 root feature 系統（supersede / hotfix / amendment）の reviewer 判定履歴
を `state.md` の `## Reviewer Lineage` セクションから抽出し、以下の anti-pattern
を検出する:

1. **Bias warning（一貫した waived）**: 同じ root feature で同じ reviewer が
   N 連続（default 3）で `waived` のとき、判定の機械的繰り返しを警告。
   true positive 見落としの可能性を提示する。
2. **Repeated changes_requested**: 同じ reviewer が連続して changes_requested
   を返している場合、reviewer instruction の調整 or rotation 検討を提案。
3. **Long chain without rotation**: chain が 5+ steerings に達しても reviewer
   set が完全に同じなら、新観点 / 別 reviewer の追加検討を提案。

Exit code:
  0: pass（INFO / WARN のみ出力）
  1: ERROR（lineage section の schema 違反）
  2: usage error / file not found

Usage:
  lint-reviewer-lineage.py <state.md path>
  lint-reviewer-lineage.py --steering-dir <.steering/<task>/>
  lint-reviewer-lineage.py --threshold-consecutive-waived 4 --threshold-chain 6
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Iterable

LINEAGE_SECTION_RE = re.compile(
    r"^##\s*Reviewer Lineage.*?$([\s\S]*?)(?=^##\s|\Z)", re.MULTILINE
)
CHAIN_ENTRY_RE = re.compile(
    r"^\s*-\s*steering:\s*([^\s|]+)\s*\|\s*(.+?)$", re.MULTILINE
)


def parse_lineage_section(state_text: str) -> tuple[list[dict[str, str]], list[str]]:
    """Parse `## Reviewer Lineage` section from state.md.

    Returns: (chain_entries, errors)
    chain_entries: list of dict with fields {steering, relation, ...reviewers, outcome}
    errors: list of schema violation messages
    """
    errors: list[str] = []
    m = LINEAGE_SECTION_RE.search(state_text)
    if not m:
        return [], []

    section = m.group(1)
    entries: list[dict[str, str]] = []

    for line_m in CHAIN_ENTRY_RE.finditer(section):
        steering = line_m.group(1).strip()
        rest = line_m.group(2).strip()
        # rest is `relation: foo | reviewer_a=... | reviewer_b=... | outcome: ...`
        entry: dict[str, str] = {"steering": steering}
        for part in rest.split("|"):
            part = part.strip()
            if "=" in part:
                k, _, v = part.partition("=")
                entry[k.strip()] = v.strip()
            elif ":" in part:
                k, _, v = part.partition(":")
                entry[k.strip()] = v.strip()
        entries.append(entry)

    if not entries:
        errors.append("Reviewer Lineage section exists but no chain entries found")

    return entries, errors


def detect_consecutive_waived(
    entries: list[dict[str, str]], reviewer_fields: Iterable[str], threshold: int
) -> list[str]:
    """Detect a reviewer that has been consecutively `waived` for `threshold` entries."""
    warnings: list[str] = []
    for field in reviewer_fields:
        consec = 0
        max_consec = 0
        chain_at_max: list[str] = []
        cur_chain: list[str] = []
        for e in entries:
            val = e.get(field, "")
            if val.startswith("waived"):
                consec += 1
                cur_chain.append(e.get("steering", "?"))
                if consec > max_consec:
                    max_consec = consec
                    chain_at_max = list(cur_chain)
            else:
                consec = 0
                cur_chain = []
        if max_consec >= threshold:
            warnings.append(
                f"WARN: {field} が {max_consec} 連続 waived（steerings: {chain_at_max[-3:]} ...）。"
                "true positive 見落としの可能性。次の steering で再起動を検討してください"
            )
    return warnings


def detect_repeated_changes_requested(
    entries: list[dict[str, str]], reviewer_fields: Iterable[str], threshold: int
) -> list[str]:
    """Detect a reviewer that returned `changes_requested` N 連続。"""
    warnings: list[str] = []
    for field in reviewer_fields:
        consec = 0
        max_consec = 0
        for e in entries:
            val = e.get(field, "")
            if "changes_requested" in val:
                consec += 1
                if consec > max_consec:
                    max_consec = consec
            else:
                consec = 0
        if max_consec >= threshold:
            warnings.append(
                f"WARN: {field} が {max_consec} 連続 changes_requested。"
                "reviewer instruction の調整または別観点の reviewer 追加を検討してください"
            )
    return warnings


def detect_long_chain_no_rotation(
    entries: list[dict[str, str]], reviewer_fields: Iterable[str], chain_threshold: int
) -> list[str]:
    """Detect long chain where the same reviewer set is reused without variation."""
    warnings: list[str] = []
    if len(entries) < chain_threshold:
        return warnings
    # Compute reviewer-status tuples per entry
    sigs = []
    for e in entries:
        sig = tuple(sorted((f, e.get(f, "")) for f in reviewer_fields))
        sigs.append(sig)
    if len(set(sigs)) == 1:
        warnings.append(
            f"WARN: chain が {len(entries)} steerings で reviewer 構成が完全に同一。"
            "long chain without rotation: 新観点 / 別 reviewer の追加を検討してください"
        )
    return warnings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("state_md", nargs="?", help="Path to state.md")
    parser.add_argument(
        "--steering-dir",
        help="Path to .steering/<task>/ directory (auto-resolves state.md)",
    )
    parser.add_argument(
        "--threshold-consecutive-waived",
        type=int,
        default=3,
        help="N 連続 waived を WARN 化する閾値 (default: 3)",
    )
    parser.add_argument(
        "--threshold-consecutive-changes",
        type=int,
        default=3,
        help="N 連続 changes_requested を WARN 化する閾値 (default: 3)",
    )
    parser.add_argument(
        "--threshold-chain",
        type=int,
        default=5,
        help="long chain rotation check 閾値 (default: 5)",
    )
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    state_path: Path | None = None
    if args.steering_dir:
        state_path = Path(args.steering_dir) / "state.md"
    elif args.state_md:
        state_path = Path(args.state_md)

    if state_path is None:
        print("usage: lint-reviewer-lineage.py <state.md> | --steering-dir <dir>", file=sys.stderr)
        return 2

    if not state_path.is_file():
        if not args.quiet:
            print(f"INFO: state.md not found: {state_path}", file=sys.stderr)
        return 2

    text = state_path.read_text(encoding="utf-8", errors="replace")
    entries, errors = parse_lineage_section(text)

    if errors:
        for e in errors:
            print(f"ERROR: {e}")
        return 1

    if not entries:
        if not args.quiet:
            print(f"INFO: Reviewer Lineage section が見つかりません（{state_path}）")
        return 0

    reviewer_fields = {"planning_reviewer", "security_reviewer", "implementation_reviewer"}
    # Use only fields actually present in entries
    used_fields = {f for f in reviewer_fields if any(f in e for e in entries)}

    if not args.quiet:
        print(f"INFO: lineage chain length = {len(entries)}（reviewer fields: {sorted(used_fields)}）")

    warnings: list[str] = []
    warnings.extend(detect_consecutive_waived(entries, used_fields, args.threshold_consecutive_waived))
    warnings.extend(detect_repeated_changes_requested(entries, used_fields, args.threshold_consecutive_changes))
    warnings.extend(detect_long_chain_no_rotation(entries, used_fields, args.threshold_chain))

    for w in warnings:
        print(w)

    if not warnings and not args.quiet:
        print("OK: no bias / repeated-changes / long-chain warnings")

    return 0


if __name__ == "__main__":
    sys.exit(main())
