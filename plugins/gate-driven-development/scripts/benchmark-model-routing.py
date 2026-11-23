#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESOLVER = ROOT / "scripts" / "resolve-gdd-model.py"

SCENARIOS = [
    {
        "name": "codex_formal_gate_requirements",
        "args": ["--runtime", "codex", "--phase", "gdd-requirements-gating", "--text", "requirements summary cleanup"],
        "expected": {"tier": "formal_gate", "model": "gpt-5.6-sol", "effort": "medium"},
    },
    {
        "name": "cursor_formal_gate_design",
        "args": ["--runtime", "cursor", "--phase", "gdd-design-gating", "--text", "detailed design"],
        "expected": {"tier": "formal_gate", "model": "grok-4.6", "effort": "medium"},
    },
    {
        "name": "codex_general_heavy_refactor",
        "args": ["--runtime", "codex", "--phase", "gdd-refactor-planning", "--text", "refactor planning"],
        "expected": {"tier": "general_heavy", "model": "gpt-5.6-sol", "effort": "low"},
    },
    {
        "name": "cursor_risk_escalation",
        "args": ["--runtime", "cursor", "--phase", "gdd-refactor-planning", "--text", "undocumented step with security review and multiple modules"],
        "expected": {"tier": "general_heavy_risk", "model": "grok-4.6", "effort": "high"},
    },
    {
        "name": "codex_pr_ready_before_merge",
        "args": ["--runtime", "codex", "--phase", "gdd-pr-review", "--text", "PR-ready check before merge"],
        "expected": {"tier": "general_heavy_risk", "model": "gpt-5.6-sol", "effort": "high"},
    },
    {
        "name": "cursor_insufficient_investigation",
        "args": ["--runtime", "cursor", "--phase", "gdd-refactor-planning", "--text", "調査不足 with evidence missing across multiple modules"],
        "expected": {"tier": "general_heavy_risk", "model": "grok-4.6", "effort": "high"},
    },
    {
        "name": "codex_broad_refactor_many_files",
        "args": ["--runtime", "codex", "--phase", "gdd-refactor-planning", "--text", "broad refactor across many files"],
        "expected": {"tier": "general_heavy_risk", "model": "gpt-5.6-sol", "effort": "high"},
    },
    {
        "name": "codex_light_task_tdd",
        "args": ["--runtime", "codex", "--phase", "gdd-test-driven-development", "--text", "write red tests for approved AC"],
        "expected": {"tier": "light_task", "model": "gpt-5.6-terra", "effort": "medium"},
    },
    {
        "name": "cursor_leaf_task",
        "args": ["--runtime", "cursor", "--text", "classify routing candidates"],
        "expected": {"tier": "leaf_task", "model": "grok-4.5", "effort": "low"},
    },
    {
        "name": "claude_heavy_gate",
        "args": ["--runtime", "claude_code", "--phase", "gdd-brainstorming", "--text", "requirements cleanup"],
        "expected": {"tier": "formal_gate", "model": "opus", "effort": "high"},
    },
    {
        "name": "cursor_implementation_composer_25",
        "args": ["--runtime", "cursor", "--phase", "gdd-subagent-driven-implementation", "--text", "bounded implementation"],
        "expected": {"tier": "implementation", "model": "composer-2.5", "effort": "n/a"},
    },
    {
        "name": "claude_implementation_sonnet",
        "args": ["--runtime", "claude_code", "--phase", "gdd-subagent-driven-implementation", "--text", "bounded implementation"],
        "expected": {"tier": "implementation", "model": "sonnet", "effort": "medium"},
    },
]


def run_scenario(scenario: dict[str, object]) -> dict[str, object]:
    args = scenario["args"]
    assert isinstance(args, list)
    result = subprocess.run(
        [sys.executable, str(RESOLVER), *args, "--json"],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    expected = scenario["expected"]
    assert isinstance(expected, dict)
    mismatches = {
        key: {"expected": value, "actual": payload.get(key)}
        for key, value in expected.items()
        if payload.get(key) != value
    }
    return {
        "name": scenario["name"],
        "passed": not mismatches,
        "expected": expected,
        "actual": {key: payload.get(key) for key in ("tier", "model", "effort")},
        "reasons": payload.get("reasons", []),
        "mismatches": mismatches,
    }


def main() -> int:
    results = [run_scenario(scenario) for scenario in SCENARIOS]
    passed = sum(1 for result in results if result["passed"])
    total = len(results)
    payload = {
        "benchmark": "gdd-model-routing",
        "passed": passed,
        "total": total,
        "accuracy": passed / total,
        "results": results,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
