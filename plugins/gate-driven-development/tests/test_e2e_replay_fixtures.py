"""Replay small GDD artifact fixtures for known workflow regressions.

These are not full agent E2E tests. They replay persisted artifacts and final
HITL text through the same lints that guard release readiness.
"""
from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


from _paths import PLUGIN_ROOT
FIXTURE_ROOT = PLUGIN_ROOT / "tests" / "fixtures" / "e2e-replay"


class E2EReplayFixtureTests(unittest.TestCase):
    def test_all_replay_fixtures_match_expected_status(self) -> None:
        expected_files = sorted(FIXTURE_ROOT.glob("*/expected.json"))
        self.assertGreaterEqual(len(expected_files), 5, "expected the P0 and tuned replay fixtures")

        for expected_file in expected_files:
            with self.subTest(fixture=expected_file.parent.name):
                expected = json.loads(expected_file.read_text(encoding="utf-8"))
                result = self._run_fixture(expected_file.parent, expected)
                combined_output = result.stdout + result.stderr

                if expected["expected_status"] == "fail":
                    self.assertNotEqual(result.returncode, 0, combined_output)
                else:
                    self.assertEqual(result.returncode, 0, combined_output)

                for token in expected.get("expected_reason_contains", []):
                    self.assertIn(token, combined_output)

    def _run_fixture(self, fixture_dir: Path, expected: dict[str, object]) -> subprocess.CompletedProcess[str]:
        runner = str(expected["runner"])
        if runner == "lint-resume-integrity":
            command = [
                sys.executable,
                str(PLUGIN_ROOT / "scripts" / "lint-resume-integrity.py"),
                "--steering-dir",
                str(fixture_dir / str(expected["steering_dir"])),
            ]
            if expected.get("branch"):
                command.extend(["--branch", str(expected["branch"])])
            if expected.get("worktree_path"):
                command.extend(["--worktree-path", str(fixture_dir / str(expected["worktree_path"]))])
        elif runner == "lint-hitl-display-integrity":
            command = [
                sys.executable,
                str(PLUGIN_ROOT / "scripts" / "lint-hitl-display-integrity.py"),
                str(fixture_dir / str(expected["path"])),
            ]
        elif runner == "lint-human-check-language":
            command = [
                sys.executable,
                str(PLUGIN_ROOT / "scripts" / "lint-human-check-language.py"),
                str(fixture_dir / str(expected["path"])),
            ]
        elif runner == "lint-hitl-complexity":
            command = [
                sys.executable,
                str(PLUGIN_ROOT / "scripts" / "lint-hitl-complexity.py"),
                str(fixture_dir / str(expected["path"])),
            ]
        elif runner == "lint-pr-review-followup-state":
            command = [
                sys.executable,
                str(PLUGIN_ROOT / "scripts" / "lint-pr-review-followup-state.py"),
                str(fixture_dir / str(expected["path"])),
            ]
        elif runner == "lint-worktree-provenance":
            command = [
                sys.executable,
                str(PLUGIN_ROOT / "scripts" / "lint-worktree-provenance.py"),
                "--steering-dir",
                str(fixture_dir / str(expected["steering_dir"])),
            ]
            if expected.get("branch"):
                command.extend(["--branch", str(expected["branch"])])
            if expected.get("worktree_path"):
                command.extend(["--worktree-path", str(fixture_dir / str(expected["worktree_path"]))])
            if expected.get("pr_head_branch"):
                command.extend(["--pr-head-branch", str(expected["pr_head_branch"])])
            if expected.get("diff_files"):
                command.extend(["--diff-files", str(fixture_dir / str(expected["diff_files"]))])
        elif runner == "lint-state-tasklist-continuity":
            command = [
                sys.executable,
                str(PLUGIN_ROOT / "scripts" / "lint-state-tasklist-continuity.py"),
                "--steering-dir",
                str(fixture_dir / str(expected["steering_dir"])),
            ]
        elif runner == "lint-hitl-decision-quality":
            command = [
                sys.executable,
                str(PLUGIN_ROOT / "scripts" / "lint-hitl-decision-quality.py"),
                str(fixture_dir / str(expected["path"])),
            ]
        else:
            raise AssertionError(f"unknown fixture runner: {runner}")

        return subprocess.run(command, text=True, capture_output=True, check=False)

if __name__ == "__main__":
    unittest.main()
