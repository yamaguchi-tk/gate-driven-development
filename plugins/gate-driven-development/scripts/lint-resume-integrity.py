#!/usr/bin/env python3
"""Lint GDD steering identity before resume.

This is a lightweight fail-closed check for the class of bugs where a stale
`.steering/<old-task>/state.md` is resumed on a different branch/worktree.

Exit code:
  0: pass
  1: resume identity mismatch
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


TERMINAL_PHASES = {"done", "cancelled", "canceled", "blocked", "abandoned"}
DEFAULT_BRANCHES = {"main", "master", "trunk", "develop", "development"}
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


def field_head(text: str, name: str) -> str:
    # state field は pipe 区切りの注記（`updated_by` 等。references/state-machine.md
    # § state field のフォーマット検証）を伴うことがある。先頭セグメント（pipe より前）
    # だけを比較に使う（独立-20 finding 2: 独立-19 は Resume From・Task Size の 2 読み取り
    # にしか適用せず、is_terminal() と build_like の Next Action 読み取りが尾部を含んだまま
    # 比較され、terminal 判定漏れ・build_like 誤検知の両方が起きていた。読み取り箇所を
    # 問わずこのヘルパーに統一する）。
    return extract_field(text, name).split("|", 1)[0]


def is_terminal(state_text: str) -> bool:
    resume_from = normalize_slug(field_head(state_text, "Resume From"))
    next_action = normalize_slug(field_head(state_text, "Next Action"))
    return resume_from in TERMINAL_PHASES or next_action in TERMINAL_PHASES


def same_path(left: str, right: str) -> bool:
    return Path(left).expanduser().resolve(strict=False) == Path(right).expanduser().resolve(strict=False)


def branch_matches_task(branch: str, task_id: str) -> bool:
    branch_slug = normalize_slug(branch)
    task_slug = normalize_slug(task_id)
    if not branch_slug or not task_slug:
        return False
    if branch_slug in DEFAULT_BRANCHES:
        return False
    return branch_slug == task_slug or branch_slug.endswith(task_slug)


def lint_steering(steering_dir: Path, branch: str = "", worktree_path: str = "") -> list[str]:
    errors: list[str] = []
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
    if effective_branch and active_branch and normalize_slug(branch or active_branch) != normalize_slug(active_branch):
        errors.append(f"branch mismatch: current={branch} state={active_branch}")

    if not terminal and effective_branch and task_id and not branch_matches_task(effective_branch, task_id):
        errors.append(f"branch/task mismatch: branch={effective_branch} task={task_id}")

    expected_worktree = worktree_path or str(steering_dir.parent.parent)
    if active_worktree and not same_path(active_worktree, expected_worktree):
        errors.append(f"worktree mismatch: state={active_worktree} expected={expected_worktree}")

    if not terminal and normalize_slug(effective_branch) in DEFAULT_BRANCHES:
        errors.append(f"non-terminal steering on default branch: {effective_branch}")

    next_action = field_head(state_text, "Next Action")
    resume_from = field_head(state_text, "Resume From")
    task_size = field_head(state_text, "Task Size")
    build_tokens = (
        "test-driven-development",
        "subagent-driven-implementation",
        "implementation-gating",
        "systematic-debugging",
        "refactor-planning",
        "completion-check",
    )
    # Next Action 側は build candidate の正本（state-machine.md の Next Action 条件）として
    # そのまま見る。Resume From 側は express の crash recovery window（承認直後〜
    # tasklist.md 作成前、Resume From=gdd-test-driven-development が正常。
    # references/state-machine.md § Express 昇格時の state ロールバック規則）だけを除外し、
    # それ以外の build 系 Resume From（tasklist.md 未作成のまま壊れた state）は引き続き
    # block する（独立-19 finding 3。独立-15 finding 9 で Resume From を丸ごと判定から
    # 外したところ、この窓以外の build 系 Resume From も素通りするようになっていた。独立-18
    # finding 2 で Resume From 側の判定を戻したが、Task Size を見ずに値 1 つだけで除外して
    # いたため、Task Size が express 以外（`quick (express → standard)` 等）でも同じ値なら
    # 素通りする穴が残っていた。除外は Task Size=quick (express) かつ Resume From=
    # gdd-test-driven-development の組み合わせだけに絞る）。
    # この窓（express crash recovery window の除外）は scripts/lint-state-tasklist-continuity.py
    # 側では対象外（同スクリプトは tasklist.md の存在を前提条件として要求する continuity
    # 検査で、「tasklist.md が存在すべきか」を判定する本スクリプトとは適用範囲が異なる。
    # 独立-20 finding 5）。ただし pipe 尾部の読み方（`field_head()` の先頭セグメント切り
    # 出し）は state field の汎用書式であり、この適用範囲の差では説明できない。独立-21
    # finding 2 でこの非対称（特に Next Action 側は本ファイルの field_head 化で新たに
    # 生じた）が発覚し、lint-state-tasklist-continuity.py 側にも同じ field_head 相当を
    # 追加して揃えた。除外するのは express window だけで、pipe 尾部の扱いは両者で揃える。
    is_express_crash_recovery_window = (
        normalize_slug(task_size) == "quick-express"
        and normalize_slug(resume_from) == "gdd-test-driven-development"
    )
    build_like = any(token in normalize_slug(next_action) for token in build_tokens) or (
        not is_express_crash_recovery_window
        and any(token in normalize_slug(resume_from) for token in build_tokens)
    )
    if build_like and not (steering_dir / "tasklist.md").is_file():
        errors.append("build resume requires tasklist.md")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--steering-dir", required=True, help=".steering/<task> directory")
    parser.add_argument("--branch", default="", help="current git branch, if known")
    parser.add_argument("--worktree-path", default="", help="current active worktree path, if known")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    errors = lint_steering(Path(args.steering_dir), branch=args.branch, worktree_path=args.worktree_path)
    return report_errors(
        errors,
        "ERROR: Resume Integrity failed.\ntask / branch / worktree / state.md が混線している可能性があるため、自動再開しないでください。",
        "OK: Resume Integrity passed",
        quiet=args.quiet,
    )


if __name__ == "__main__":
    sys.exit(main())
