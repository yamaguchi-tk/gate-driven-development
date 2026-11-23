#!/usr/bin/env python3
"""Fail when raw task steering files are tracked or introduced."""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def tracked_files(root: Path, against: str | None = None, staged: bool = False) -> list[str]:
    if staged:
        cmd = [
            "git",
            "-C",
            str(root),
            "diff",
            "--cached",
            "--name-only",
            "--diff-filter=ACMRT",
        ]
    elif against:
        cmd = [
            "git",
            "-C",
            str(root),
            "diff",
            "--name-only",
            "--diff-filter=ACMRT",
            f"{against}...HEAD",
        ]
    else:
        cmd = ["git", "-C", str(root), "ls-files"]
    proc = subprocess.run(
        cmd,
        check=True,
        capture_output=True,
        text=True,
    )
    return [line.strip() for line in proc.stdout.splitlines() if line.strip()]


def is_raw_task_steering(path: str) -> bool:
    return ".steering" in Path(path).parts


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Reject tracked raw task .steering/<task>/ files."
    )
    parser.add_argument(
        "--root",
        default=".",
        help="Git repository root or any path inside it.",
    )
    parser.add_argument(
        "--against",
        default=None,
        help="Optional base ref. When set, only files introduced or changed by BASE...HEAD are checked.",
    )
    parser.add_argument(
        "--staged",
        action="store_true",
        help="Check only staged files. Use this from a pre-commit hook or before creating a local commit.",
    )
    args = parser.parse_args()

    if args.staged and args.against:
        parser.error("--staged cannot be combined with --against")

    root = Path(args.root).resolve()
    offenders = [
        path
        for path in tracked_files(root, args.against, staged=args.staged)
        if is_raw_task_steering(path)
    ]
    if not offenders:
        return 0

    if args.staged:
        scope = " staged"
    elif args.against:
        scope = f" introduced relative to {args.against}"
    else:
        scope = " tracked"
    print(f"ERROR: raw task steering files are{scope}.", file=sys.stderr)
    print("Raw task .steering/<task>/ is branch-only working state and must not reach PR/main.", file=sys.stderr)
    print("Move durable decisions to docs/adr/ or an adopted repo-level learned-patterns file.", file=sys.stderr)
    for path in offenders:
        print(f"- {path}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
