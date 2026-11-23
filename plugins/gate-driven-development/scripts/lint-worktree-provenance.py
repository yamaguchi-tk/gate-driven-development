#!/usr/bin/env python3
"""Lint GDD worktree provenance before resume, PR review, or completion.

Exit code:
  0: pass
  1: task / branch / PR / steering / diff provenance mismatch
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
from lib.lint_base import report_errors


DEFAULT_BRANCHES = {"main", "master", "trunk", "develop", "development"}
TERMINAL_PHASES = {"done", "cancelled", "canceled", "blocked", "abandoned"}
FIELD_PATTERNS = (
    r"^\s*[-*]?\s*`?{name}`?\s*[:=]\s*(?P<value>.+?)\s*$",
    r"^\s*[-*]?\s*`?{name}\s*=\s*(?P<value>.+?)`?\s*$",
)


def normalize_slug(value: str) -> str:
    value = value.strip().strip("`")
    if "/" in value:
        value = value.rsplit("/", 1)[-1]
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    return value


def extract_field(text: str, name: str) -> str:
    escaped = re.escape(name)
    for line in text.splitlines():
        for pattern in FIELD_PATTERNS:
            match = re.match(pattern.format(name=escaped), line, flags=re.IGNORECASE)
            if match:
                return match.group("value").strip().strip("`")
    return ""


def branch_matches_task(branch: str, task_id: str) -> bool:
    branch_slug = normalize_slug(branch)
    task_slug = normalize_slug(task_id)
    if not branch_slug or not task_slug or branch_slug in DEFAULT_BRANCHES:
        return False
    return branch_slug == task_slug or branch_slug.endswith(task_slug)


def same_path(left: str, right: str) -> bool:
    return Path(left).expanduser().resolve(strict=False) == Path(right).expanduser().resolve(strict=False)


def is_terminal(state_text: str) -> bool:
    resume_from = normalize_slug(extract_field(state_text, "Resume From"))
    next_action = normalize_slug(extract_field(state_text, "Next Action"))
    return resume_from in TERMINAL_PHASES or next_action in TERMINAL_PHASES


def read_diff_files(diff_files_path: str) -> list[str]:
    if not diff_files_path:
        return []
    path = Path(diff_files_path)
    if not path.is_file():
        raise FileNotFoundError(str(path))
    return [line.strip() for line in path.read_text(encoding="utf-8", errors="replace").splitlines() if line.strip()]


def lint_provenance(
    steering_dir: Path,
    *,
    branch: str = "",
    worktree_path: str = "",
    pr_head_branch: str = "",
    repo_root: str = "",
    diff_files: list[str] | None = None,
) -> list[str]:
    errors: list[str] = []
    diff_files = diff_files or []

    if not steering_dir.is_dir():
        return [f"steering dir not found: {steering_dir}"]

    state_path = steering_dir / "state.md"
    if not state_path.is_file():
        return [f"state.md not found: {state_path}"]

    state_text = state_path.read_text(encoding="utf-8", errors="replace")
    task_from_dir = steering_dir.name
    task_id = extract_field(state_text, "Task ID") or extract_field(state_text, "Task")
    active_branch = extract_field(state_text, "Active Branch")
    active_worktree = extract_field(state_text, "Active Worktree Path")
    terminal = is_terminal(state_text)

    if not task_id:
        errors.append("missing Task ID in state.md")
    elif normalize_slug(task_id) != normalize_slug(task_from_dir):
        errors.append(f"task id mismatch: state={task_id} steering_dir={task_from_dir}")

    effective_branch = branch or active_branch
    if branch and active_branch and normalize_slug(branch) != normalize_slug(active_branch):
        errors.append(f"branch mismatch: current={branch} state={active_branch}")
    if pr_head_branch and effective_branch and normalize_slug(pr_head_branch) != normalize_slug(effective_branch):
        errors.append(f"PR head branch mismatch: pr={pr_head_branch} active={effective_branch}")
    if not terminal and effective_branch and task_id and not branch_matches_task(effective_branch, task_id):
        errors.append(f"branch/task mismatch: branch={effective_branch} task={task_id}")
    if not terminal and normalize_slug(effective_branch) in DEFAULT_BRANCHES:
        errors.append(f"non-terminal steering on default branch: {effective_branch}")

    expected_worktree = worktree_path or str(steering_dir.parent.parent)
    if active_worktree and not same_path(active_worktree, expected_worktree):
        errors.append(f"worktree mismatch: state={active_worktree} expected={expected_worktree}")

    task_slug = normalize_slug(task_id or task_from_dir)
    for raw_file in diff_files:
        path_slug = normalize_slug(raw_file)
        if raw_file.startswith(".steering/") and task_slug and task_slug not in path_slug:
            errors.append(f"diff touches another steering task: {raw_file}")

    if repo_root:
        root = Path(repo_root)
        root_steering = root / ".steering"
        if root_steering.is_dir():
            for candidate in root_steering.iterdir():
                if not candidate.is_dir() or candidate.name == task_from_dir:
                    continue
                candidate_state = candidate / "state.md"
                if not candidate_state.is_file():
                    continue
                candidate_text = candidate_state.read_text(encoding="utf-8", errors="replace")
                if not is_terminal(candidate_text):
                    errors.append(f"non-terminal duplicate steering candidate: {candidate.name}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--steering-dir", required=True, help=".steering/<task> directory")
    parser.add_argument("--branch", default="", help="current git branch, if known")
    parser.add_argument("--worktree-path", default="", help="current active worktree path, if known")
    parser.add_argument("--pr-head-branch", default="", help="GitHub PR head branch, if known")
    parser.add_argument("--repo-root", default="", help="repo/worktree root for duplicate steering checks")
    parser.add_argument("--diff-files", default="", help="newline-separated changed paths")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    try:
        diff_files = read_diff_files(args.diff_files)
    except FileNotFoundError as exc:
        print(f"ERROR: file not found: {exc}", file=sys.stderr)
        return 2

    errors = lint_provenance(
        Path(args.steering_dir),
        branch=args.branch,
        worktree_path=args.worktree_path,
        pr_head_branch=args.pr_head_branch,
        repo_root=args.repo_root,
        diff_files=diff_files,
    )
    return report_errors(
        errors,
        "ERROR: Worktree Provenance failed.\ntask / branch / PR / worktree / steering / diff が混線しているため、自動再開や完了宣言を止めてください。",
        "OK: Worktree Provenance passed",
        quiet=args.quiet,
    )


if __name__ == "__main__":
    sys.exit(main())
