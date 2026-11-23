"""Contract tests for GDD improvements inspired by Superpowers.

These tests keep the comparison actionable: GDD should borrow useful
Superpowers discipline while preserving its state-machine differentiation.
"""
from __future__ import annotations

import unittest
import json
import os
import subprocess
import tempfile
from pathlib import Path

from _validate_plugin_reader import read_validate_plugin_and_checks


from _paths import PLUGIN_ROOT


def read_text(path: str) -> str:
    return (PLUGIN_ROOT / path).read_text(encoding="utf-8")


class SuperpowersDifferentiationContractTests(unittest.TestCase):

    def test_skill_count_budget_is_machine_enforced(self) -> None:
        validate = read_validate_plugin_and_checks()
        contributing = read_text("CONTRIBUTING.md")

        actual_skill_count = len(list((PLUGIN_ROOT / "skills").glob("*/SKILL.md")))

        self.assertEqual(actual_skill_count, 29)
        for token in [
            "MAX_SKILL_COUNT=29",
            "Skill count budget",
            "find \"$ROOT/skills\"",
            "skill count",
        ]:
            self.assertIn(token, validate)
        for token in [
            "Skill count budget",
            "29",
            "新しい skill を追加する場合",
            "既存 skill の統合",
            "SKILL_COUNT_BUDGET_CHANGE",
            "SKILL_COUNT_REDUCTION_PLAN",
            "manifest skill count",
        ]:
            self.assertIn(token, contributing)

        for token in [
            "SKILL_COUNT_BUDGET_CHANGE",
            "SKILL_COUNT_REDUCTION_PLAN",
            "manifest skill count",
            "codex_manifest_skill_count",
        ]:
            self.assertIn(token, validate)


    def test_session_start_superpowers_guidance_includes_routing_reason(self) -> None:
        hook = PLUGIN_ROOT / "hooks" / "scripts" / "run-session-start-hook.sh"

        with tempfile.TemporaryDirectory(prefix="gdd-session-routing-reason-") as tmp_raw:
            tmp = Path(tmp_raw)
            repo = tmp / "repo"
            repo.mkdir()
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)

            home = tmp / "home"
            settings_dir = home / ".claude"
            settings_dir.mkdir(parents=True)
            settings_dir.joinpath("settings.json").write_text(
                '{"enabledPlugins":["superpowers"]}',
                encoding="utf-8",
            )

            env = dict(os.environ)
            env["HOME"] = str(home)
            result = subprocess.run(
                ["bash", str(hook)],
                cwd=repo,
                env=env,
                capture_output=True,
                text=True,
                check=True,
            )

        payload = json.loads(result.stdout)
        additional = payload["hookSpecificOutput"]["additionalContext"]
        self.assertIn("Routing reason: no active GDD marker detected", additional)
        self.assertIn("formal GDD auto-trigger is disabled", additional)
        self.assertIn("GDD natural-language planning intent", additional)
        self.assertIn("superpowers advisory only", additional)


if __name__ == "__main__":
    unittest.main()
