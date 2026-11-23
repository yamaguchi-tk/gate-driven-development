"""Shared helpers for scripts/lint-*.py."""
from __future__ import annotations

import sys
from pathlib import Path


def check_file(path: Path) -> int | None:
    """Return 2 if path is not a file; print error to stderr. Return None if OK."""
    if not path.is_file():
        print(f"ERROR: file not found: {path}", file=sys.stderr)
        return 2
    return None


def report_errors(errors: list[str], header: str, ok_msg: str, *, quiet: bool) -> int:
    """Print errors or OK message; return 1 on errors, 0 otherwise.

    ``header`` may contain ``\\n`` for multi-line output.
    """
    if errors:
        if not quiet:
            print(header)
            for e in errors:
                print(f"- {e}")
        return 1
    if not quiet:
        print(ok_msg)
    return 0
