#!/usr/bin/env python3
"""Lint GDD state/tasklist continuity after requirements or design changes.

`Requirements Revision` / `Design Revision` は tasklist の任意 field として扱う。
GDD の正本 contract（`references/task-breakdown-steps.md` の Agentic Worker Header /
`references/state-machine.md` の Stage Continuity）はこの 2 つを規定しておらず、
必須化すると正規手順で生成した tasklist が構造的に通らなくなる。
記録がある場合だけ artifact 側の `Revision` と突き合わせる。

Exit code:
  0: pass
  1: state/tasklist/requirements/design continuity mismatch
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


BUILD_ACTION_TOKENS = (
    "gdd-test-driven-development",
    "gdd-subagent-driven-implementation",
    "gdd-implementation-gating",
    "gdd-completion-check",
)
FIELD_PATTERNS = (
    r"^\s*[-*]?\s*`?{name}`?\s*[:=]\s*(?P<value>.+?)\s*$",
    r"^\s*[-*]?\s*`?{name}\s*=\s*(?P<value>.+?)`?\s*$",
    # Agentic Worker Header の正準記法（`references/task-breakdown-steps.md`）。
    # `**Field:** value` / `**Field**: value` のどちらも読む。bullet 記法だけを読むと、
    # 正準記法で記録された field を黙って照合対象外にしてしまう。
    r"^\s*\*\*{name}\s*[:=]\s*\*\*\s*(?P<value>.+?)\s*$",
    r"^\s*\*\*{name}\*\*\s*[:=]\s*(?P<value>.+?)\s*$",
)


def normalize(value: str) -> str:
    value = value.strip().strip("`").lower()
    value = re.sub(r"\s+", " ", value)
    return value


def extract_field(text: str, name: str) -> str:
    escaped = re.escape(name)
    for line in text.splitlines():
        for pattern in FIELD_PATTERNS:
            match = re.match(pattern.format(name=escaped), line, flags=re.IGNORECASE)
            if match:
                return match.group("value").strip().strip("`")
    return ""


def extract_header_region(text: str) -> str:
    """先頭から最初の `## ` 見出しまでを返す（tasklist の Agentic Worker Header 相当）。

    `Task ID` は `## Implementation Reviewer Selection` の per-task field としても現れるため、
    走査範囲を絞らないと steering task id と衝突して誤検知になる。
    """
    match = re.search(r"^## ", text, flags=re.MULTILINE)
    return text[: match.start()] if match else text


def extract_section(text: str, heading: str) -> str:
    start = text.find(heading)
    if start < 0:
        return ""
    rest = text[start + len(heading) :]
    next_heading = rest.find("\n## ")
    if next_heading >= 0:
        rest = rest[:next_heading]
    return rest


def field_head(text: str, name: str) -> str:
    # state field は pipe 区切りの注記（`updated_by` 等。references/state-machine.md
    # § state field のフォーマット検証）を伴うことがある。先頭セグメント（pipe より前）
    # だけを比較に使う（独立-21 finding 2: lint-resume-integrity.py 側だけ pipe 尾部を
    # 切り出すようになった結果、同じ Next Action / Resume From を読む本スクリプトとの
    # 間に受理集合のずれが生じていた。pipe 尾部の扱いは state field の汎用書式であり、
    # 両スクリプトで揃える）。
    return extract_field(text, name).split("|", 1)[0]


def action_is_build_like(state_text: str) -> bool:
    action_blob = " ".join(
        [
            field_head(state_text, "Next Action"),
            field_head(state_text, "Resume From"),
        ]
    ).lower()
    return any(token in action_blob for token in BUILD_ACTION_TOKENS)


def lint_continuity(steering_dir: Path) -> list[str]:
    errors: list[str] = []
    state_path = steering_dir / "state.md"
    tasklist_path = steering_dir / "tasklist.md"
    requirements_path = steering_dir / "requirements.md"
    design_path = steering_dir / "design.md"

    for path in (state_path, tasklist_path):
        if not path.is_file():
            return [f"required file not found: {path}"]

    state_text = state_path.read_text(encoding="utf-8", errors="replace")
    tasklist_text = tasklist_path.read_text(encoding="utf-8", errors="replace")

    if action_is_build_like(state_text) and not extract_section(tasklist_text, "## Current Task").strip():
        errors.append("build-like resume requires tasklist.md Current Task")

    # state.md 側は全文走査のまま。`Task ID` の配置は contract に固定されておらず、
    # 他の consumer（lint-resume-integrity / lint-worktree-provenance / gdd_task_binding）も
    # 全文で読む。節を絞ると照合を黙って飛ばす方向にしか働かない。
    tasklist_scope = extract_header_region(tasklist_text)
    state_task_id = extract_field(state_text, "Task ID") or extract_field(state_text, "Task")
    tasklist_task_id = extract_field(tasklist_scope, "Task ID") or extract_field(tasklist_scope, "Task")
    if state_task_id and tasklist_task_id and normalize(state_task_id) != normalize(tasklist_task_id):
        errors.append(f"task id mismatch: state={state_task_id} tasklist={tasklist_task_id}")

    for label, artifact_path in (("Requirements Revision", requirements_path), ("Design Revision", design_path)):
        tasklist_revision = extract_field(tasklist_text, label)
        if not tasklist_revision:
            continue
        if not artifact_path.is_file():
            errors.append(f"{label} is recorded but artifact is missing: {artifact_path.name}")
            continue
        artifact_text = artifact_path.read_text(encoding="utf-8", errors="replace")
        artifact_revision = extract_field(artifact_text, "Revision") or extract_field(artifact_text, label)
        if artifact_revision and normalize(artifact_revision) != normalize(tasklist_revision):
            errors.append(f"{label} mismatch: tasklist={tasklist_revision} artifact={artifact_revision}")

    if design_path.is_file():
        design_text = design_path.read_text(encoding="utf-8", errors="replace")
        continuity_source = extract_field(design_text, "Stage Continuity Source")
        if continuity_source and "requirements" not in continuity_source.lower():
            errors.append("design Stage Continuity Source must point back to requirements/tasklist continuity")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--steering-dir", required=True, help=".steering/<task> directory")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    steering_dir = Path(args.steering_dir)
    if not steering_dir.is_dir():
        print(f"ERROR: steering dir not found: {steering_dir}", file=sys.stderr)
        return 2

    errors = lint_continuity(steering_dir)
    return report_errors(
        errors,
        "ERROR: State / Tasklist Continuity failed.\nrequirements / design の更新後に古い tasklist や state で再開しようとしています。",
        "OK: State / Tasklist Continuity passed",
        quiet=args.quiet,
    )


if __name__ == "__main__":
    sys.exit(main())
