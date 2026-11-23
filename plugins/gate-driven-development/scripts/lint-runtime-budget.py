#!/usr/bin/env python3
"""Lint GDD runtime budget surfaces.

This intentionally measures runtime-facing surfaces, not repository source size.
The token count is a deterministic local estimate so CI can run without model
provider dependencies.
"""
from __future__ import annotations

import argparse
import math
import sys
from dataclasses import dataclass
from pathlib import Path


EXPRESS_PROFILE = [
    "skills/gdd-dev/SKILL.md",
    "skills/gdd-using-skills/SKILL.md",
    "commands/gdd-dev.md",
    "skills/gdd-using-git-worktrees/SKILL.md",
    "skills/gdd-brainstorming/SKILL.md",
    "skills/gdd-requirements-gating/SKILL.md",
    "references/requirements-template-express.md",
    "references/human-check-template-compact.md",
    "references/context-budget.md",
]

STANDARD_PROFILE = [
    "skills/gdd-dev/SKILL.md",
    "skills/gdd-using-skills/SKILL.md",
    "commands/gdd-dev.md",
    "skills/gdd-using-git-worktrees/SKILL.md",
    "skills/gdd-brainstorming/SKILL.md",
    "skills/gdd-requirements-gating/SKILL.md",
    "skills/gdd-design-gating/SKILL.md",
    "skills/gdd-task-breakdown/SKILL.md",
    "references/requirements-template.md",
    "references/human-check-template-compact.md",
    "references/context-budget.md",
    "references/task-sizing.md",
]


@dataclass(frozen=True)
class FileMetric:
    relpath: str
    body_lines: int
    chars: int
    estimated_tokens: int


def strip_frontmatter(text: str) -> str:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return text
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            return "\n".join(lines[idx + 1 :])
    return text


def estimated_tokens(text: str) -> int:
    # A stable CI proxy. It deliberately over-approximates mixed Japanese/English
    # markdown enough to catch growth without importing tokenizer packages.
    return max(1, math.ceil(len(text) / 4))


def metric_for(root: Path, relpath: str, *, strip_skill_frontmatter: bool) -> FileMetric:
    path = root / relpath
    if not path.is_file():
        raise SystemExit(f"MISSING: {relpath}")
    text = path.read_text(encoding="utf-8")
    body = strip_frontmatter(text) if strip_skill_frontmatter else text
    return FileMetric(
        relpath=relpath,
        body_lines=len(body.splitlines()),
        chars=len(body),
        estimated_tokens=estimated_tokens(body),
    )


def collect_skill_metrics(root: Path) -> list[FileMetric]:
    metrics: list[FileMetric] = []
    for path in sorted((root / "skills").glob("*/SKILL.md")):
        relpath = path.relative_to(root).as_posix()
        metrics.append(metric_for(root, relpath, strip_skill_frontmatter=True))
    return metrics


def collect_template_lines(root: Path, relpaths: list[str]) -> int:
    return sum(metric_for(root, relpath, strip_skill_frontmatter=False).body_lines for relpath in relpaths)


def collect_profile(root: Path, name: str, relpaths: list[str]) -> tuple[int, int, list[FileMetric]]:
    metrics = [
        metric_for(root, relpath, strip_skill_frontmatter=relpath.endswith("/SKILL.md"))
        for relpath in relpaths
    ]
    return (
        sum(metric.body_lines for metric in metrics),
        sum(metric.estimated_tokens for metric in metrics),
        metrics,
    )


def print_profile(name: str, lines: int, tokens: int, metrics: list[FileMetric]) -> None:
    print(f"- {name} runtime profile: lines={lines}, estimated runtime tokens={tokens}")
    for metric in metrics:
        print(f"  - {metric.relpath}: lines={metric.body_lines}, estimated_tokens={metric.estimated_tokens}")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Lint GDD runtime budget surfaces.")
    parser.add_argument("plugin_root", type=Path)
    parser.add_argument("--max-skill-body-lines", type=int, required=True)
    parser.add_argument("--max-total-skill-body-lines", type=int, required=True)
    parser.add_argument("--max-express-template-lines", type=int, required=True)
    parser.add_argument("--max-standard-template-lines", type=int, required=True)
    parser.add_argument("--max-express-estimated-tokens", type=int, required=True)
    parser.add_argument("--max-standard-estimated-tokens", type=int, required=True)
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)

    root = args.plugin_root.resolve()
    errors: list[str] = []

    skill_metrics = collect_skill_metrics(root)
    total_skill_lines = sum(metric.body_lines for metric in skill_metrics)
    over_skill = [metric for metric in skill_metrics if metric.body_lines > args.max_skill_body_lines]
    if over_skill:
        for metric in over_skill:
            errors.append(
                f"SKILL body line budget exceeded: {metric.relpath} "
                f"{metric.body_lines} > {args.max_skill_body_lines}"
            )
    if total_skill_lines > args.max_total_skill_body_lines:
        errors.append(
            f"Total SKILL body line budget exceeded: "
            f"{total_skill_lines} > {args.max_total_skill_body_lines}"
        )

    express_template_lines = collect_template_lines(
        root,
        ["references/requirements-template-express.md", "references/human-check-template-compact.md"],
    )
    standard_template_lines = collect_template_lines(
        root,
        ["references/requirements-template.md", "references/human-check-template-compact.md"],
    )
    if express_template_lines > args.max_express_template_lines:
        errors.append(
            f"Runtime template budget exceeded: express "
            f"{express_template_lines} > {args.max_express_template_lines}"
        )
    if standard_template_lines > args.max_standard_template_lines:
        errors.append(
            f"Runtime template budget exceeded: standard "
            f"{standard_template_lines} > {args.max_standard_template_lines}"
        )

    express_lines, express_tokens, express_metrics = collect_profile(root, "express", EXPRESS_PROFILE)
    standard_lines, standard_tokens, standard_metrics = collect_profile(root, "standard", STANDARD_PROFILE)
    if express_tokens > args.max_express_estimated_tokens:
        errors.append(
            f"express runtime profile estimated runtime tokens exceeded: "
            f"{express_tokens} > {args.max_express_estimated_tokens}"
        )
    if standard_tokens > args.max_standard_estimated_tokens:
        errors.append(
            f"standard runtime profile estimated runtime tokens exceeded: "
            f"{standard_tokens} > {args.max_standard_estimated_tokens}"
        )

    if not args.quiet or errors:
        print("Runtime Budget")
        print(
            f"- SKILL body line budget: max_per_skill={args.max_skill_body_lines}, "
            f"total={total_skill_lines}/{args.max_total_skill_body_lines}"
        )
        print(
            f"- Runtime template budget: express={express_template_lines}/{args.max_express_template_lines}, "
            f"standard={standard_template_lines}/{args.max_standard_template_lines}"
        )
        print_profile("express", express_lines, express_tokens, express_metrics)
        print_profile("standard", standard_lines, standard_tokens, standard_metrics)
        if errors:
            print("FAIL")
            for error in errors:
                print(f"- {error}")
        else:
            print("OK")

    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
