#!/usr/bin/env python3
"""Replay conversation routing fixtures for GDD vs superpowers drift.

This is a deterministic guard for known failure shapes. It does not try to
replace the model; it makes regressions visible when an active GDD
context would otherwise be routed to superpowers planning/execution.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

# hook は lib/kill-switch.sh で python3 を -I で起動し、PYTHONSAFEPATH も設定する。その下では、このファイルの
# ディレクトリが sys.path に入らない
if sys.flags.isolated or getattr(sys.flags, "safe_path", False):
    sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.lint_base import check_file


GDD_CONTEXT_TERMS = (
    "gdd",
    "/gdd-dev",
    "hitl",
    "human-check",
    "tasklist",
    "要件",
    "完了条件",
    "設計",
    "修正方針",
    "計画して",
    "進めて",
    "続けて",
)
SUPERPOWERS_TERMS = (
    "superpowers",
    "superpowers:",
)
PR_FOLLOWUP_TERMS = (
    "pr後",
    "pr 後",
    "pr作成後",
    "レビュー指摘",
    "review comment",
    "requested changes",
    "修正指示",
    "再レビュー",
    "pushして",
    "push して",
    "ci失敗",
    "failed check",
)
PLANNING_AMENDMENT_TERMS = (
    "これも入れて",
    "これも追加して",
    "追加して",
    "入れてほしい",
    "変更して",
    "変えたい",
    "見直したい",
)


def _latest_user_text(conversation: list[dict[str, Any]]) -> str:
    for message in reversed(conversation):
        if str(message.get("role", "")).lower() == "user":
            return str(message.get("text", ""))
    return ""


def _contains_any(text: str, terms: tuple[str, ...]) -> bool:
    lowered = text.lower()
    return any(term.lower() in lowered for term in terms)


def classify(fixture: dict[str, Any]) -> dict[str, str]:
    context = fixture.get("context", {})
    latest = _latest_user_text(list(fixture.get("conversation", [])))
    explicit_gdd = _contains_any(latest, GDD_CONTEXT_TERMS)
    explicit_superpowers = _contains_any(latest, SUPERPOWERS_TERMS)
    pr_followup = _contains_any(latest, PR_FOLLOWUP_TERMS) or bool(context.get("pr_exists")) or bool(context.get("review_feedback"))
    planning_amendment = (
        bool(context.get("planning_before_approval"))
        and _contains_any(latest, PLANNING_AMENDMENT_TERMS)
    )
    active_gdd = bool(context.get("active_gdd_marker"))

    if active_gdd and pr_followup:
        return {
            "primary": "gdd",
            "route": "gate-driven-development:gdd-pr-review-followup",
            "reason": "Active GDD PR follow-up; collect review/check findings, then route fixes through GDD gates instead of superpowers workflow owner.",
        }

    if active_gdd and planning_amendment:
        return {
            "primary": "gdd",
            "route": "gate-driven-development:gdd-requirements-amendment",
            "reason": "Active GDD planning-before-approval follow-up changes completion conditions; update requirements artifacts instead of starting a new plan.",
        }

    if active_gdd and (explicit_gdd or not explicit_superpowers):
        return {
            "primary": "gdd",
            "route": "gate-driven-development:gdd-status",
            "reason": "Active GDD marker is present; route through GDD state before planning or execution.",
        }

    if explicit_gdd:
        return {
            "primary": "gdd",
            "route": "gate-driven-development:gdd-pre-workflow-brainstorming",
            "reason": "The latest user request is GDD-related.",
        }

    if explicit_superpowers:
        return {
            "primary": "superpowers",
            "route": "superpowers:writing-plans",
            "reason": "Standalone superpowers request without GDD context.",
        }

    return {
        "primary": "general",
        "route": "general",
        "reason": "No GDD or superpowers routing signal.",
    }


def lint_fixture(path: Path) -> list[str]:
    fixture = json.loads(path.read_text(encoding="utf-8"))
    expected = fixture.get("expected", {})
    actual = classify(fixture)
    errors: list[str] = []

    expected_primary = expected.get("primary")
    if expected_primary and actual["primary"] != expected_primary:
        errors.append(f"primary mismatch: expected {expected_primary}, got {actual['primary']}")

    route_contains = expected.get("route_contains")
    if route_contains and str(route_contains) not in actual["route"]:
        errors.append(f"route missing token: {route_contains}; got {actual['route']}")

    for forbidden in expected.get("must_not_route", []):
        if str(forbidden) in actual["route"]:
            errors.append(f"forbidden route selected: {forbidden}")

    if expected.get("requires_status_or_resume") and "gate-driven-development:gdd-status" not in actual["route"]:
        errors.append("expected status/resume-safe GDD routing")

    print(json.dumps({"case_id": fixture.get("case_id", path.stem), "actual": actual}, ensure_ascii=False))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fixture", help="conversation replay JSON fixture")
    args = parser.parse_args()

    path = Path(args.fixture)
    if (rc := check_file(path)) is not None:
        return rc

    errors = lint_fixture(path)
    if errors:
        print("ERROR: conversation routing replay failed.", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
