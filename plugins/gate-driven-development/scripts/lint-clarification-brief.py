#!/usr/bin/env python3
"""Lint GDD clarification-needed output for decision-ready intake briefs.

Exit code:
  0: pass
  1: clarification brief is too thin for a human to decide
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


REQUIRED_MARKERS = (
    "Intake Brief",
    "確定済み",
    "まだ曖昧",
    "次に決めること",
    "回答後にどう進むか",
    '<gdd-stop reason="clarification-needed">',
)
DECISION_MATERIAL_MARKER = "判断材料"
RESEARCH_MARKERS = (
    "外部調査",
    "公開事例",
    "論文",
    "調査",
    "比較",
    "候補",
    "source",
    "link",
    "ReAct",
    "Reflexion",
    "Tree of Thoughts",
    "Self-Refine",
)
QUESTION_EFFECT_MARKERS = (
    "requirements",
    "requirements.md",
    "AC",
    "受入条件",
    "Non-Goal",
    "Deferred",
    "Implementation Approach",
    "technology stack",
    "反映",
)
TOO_THIN_MATERIAL_PATTERNS = (
    r"初期確認した外部ソース候補",
    r"source(?:s)?\s*:",
    r"参考\s*:",
)


def _section_after(text: str, marker: str) -> str:
    index = text.find(marker)
    if index < 0:
        return ""
    rest = text[index + len(marker) :]
    next_match = re.search(r"\n(?:\d+\.\s|#{1,4}\s|\*\*[^*\n]+?\*\*)", rest)
    if next_match:
        rest = rest[: next_match.start()]
    return rest.strip()


def _visible_lines(section: str) -> list[str]:
    lines: list[str] = []
    for line in section.splitlines():
        stripped = line.strip(" -*|")
        if stripped and not set(stripped) <= {"-", "|", ":"}:
            lines.append(stripped)
    return lines


def lint_text(text: str) -> list[str]:
    errors: list[str] = []

    if '<gdd-stop reason="clarification-needed">' not in text:
        return errors

    for marker in REQUIRED_MARKERS:
        if marker not in text:
            errors.append(f"missing clarification marker: {marker}")

    has_research_or_options = any(marker.lower() in text.lower() for marker in RESEARCH_MARKERS)
    if has_research_or_options and DECISION_MATERIAL_MARKER not in text:
        errors.append("missing decision material for research/options clarification: 判断材料")

    material = _section_after(text, DECISION_MATERIAL_MARKER)
    if DECISION_MATERIAL_MARKER in text:
        material_lines = _visible_lines(material)
        if has_research_or_options and len(material_lines) < 3:
            errors.append("decision material is too short for research/options clarification")
        if any(re.search(pattern, material, flags=re.IGNORECASE) for pattern in TOO_THIN_MATERIAL_PATTERNS) and not any(
            phrase in material for phrase in ("分かったこと", "違い", "何が良くなる", "テスト", "向いている")
        ):
            errors.append("decision material lists sources/candidates without explaining what they mean")

    next_decision = _section_after(text, "次に決めること")
    if next_decision and not any(marker in next_decision for marker in QUESTION_EFFECT_MARKERS):
        errors.append("next decision does not explain where the answer will be reflected")

    after_answer = _section_after(text, "回答後にどう進むか")
    if after_answer and not any(
        marker in after_answer
        for marker in ("requirements", "requirements.md", "design", "design.md", "human-check", "再 clarification", "再確認")
    ):
        errors.append("after-answer path does not explain the next workflow step")

    return errors


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", help="clarification-needed markdown sample path")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)

    path = Path(args.path)
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"ERROR: cannot read {path}: {exc}", file=sys.stderr)
        return 2

    errors = lint_text(text)
    return report_errors(
        errors,
        "ERROR: Clarification Brief failed.\n質問は短くてよいですが、人間が選べる判断材料を削らないでください。",
        "OK: Clarification Brief passed",
        quiet=args.quiet,
    )


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
