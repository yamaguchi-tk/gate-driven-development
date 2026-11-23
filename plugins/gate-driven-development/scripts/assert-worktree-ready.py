#!/usr/bin/env python3
"""Fail closed before writing GDD steering artifacts outside the active worktree."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def resolve_path(raw: str) -> Path:
    return Path(raw).expanduser().resolve()


def is_relative_to(child: Path, parent: Path) -> bool:
    try:
        child.relative_to(parent)
        return True
    except ValueError:
        return False


def fail(message: str) -> int:
    print(message, file=sys.stderr)
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify that GDD steering writes target an active dedicated worktree."
    )
    parser.add_argument("--repo-root", required=True, help="Original repository root checkout.")
    parser.add_argument("--worktree-path", required=True, help="Active GDD worktree absolute path.")
    parser.add_argument("--steering-slug", required=True, help="Current task steering slug.")
    parser.add_argument(
        "--steering-path",
        help="Optional exact steering directory path. Defaults to <worktree-path>/.steering/<steering-slug>.",
    )
    parser.add_argument(
        "--legacy-migration",
        action="store_true",
        help="Allow a root steering duplicate only as an explicit legacy-migration source.",
    )
    args = parser.parse_args()

    repo_root = resolve_path(args.repo_root)
    worktree_path = resolve_path(args.worktree_path)
    steering_path = (
        resolve_path(args.steering_path)
        if args.steering_path
        else worktree_path / ".steering" / args.steering_slug
    )
    expected_steering_path = worktree_path / ".steering" / args.steering_slug
    root_steering_path = repo_root / ".steering" / args.steering_slug

    if not repo_root.exists():
        return fail(f"repo_root_not_found: {repo_root}")

    if not worktree_path.exists():
        return fail(f"worktree_path_not_found: {worktree_path}")

    if repo_root == worktree_path:
        return fail(
            "Refusing to write GDD steering artifacts into repo root: "
            f"repo-root and worktree-path are identical ({repo_root})"
        )

    if steering_path != expected_steering_path:
        return fail(
            "steering_path_mismatch: expected "
            f"{expected_steering_path}, got {steering_path}"
        )

    if not is_relative_to(steering_path, worktree_path / ".steering"):
        return fail(
            "steering_path_outside_worktree: "
            f"{steering_path} is not under {worktree_path / '.steering'}"
        )

    if root_steering_path.exists() and not args.legacy_migration:
        return fail(
            "root_steering_duplicate: "
            f"{root_steering_path} exists. Resolve root bleed before continuing, "
            "or rerun with --legacy-migration only when copying a legacy root artifact once."
        )

    print(f"OK: pre-artifact worktree guard passed for {expected_steering_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
