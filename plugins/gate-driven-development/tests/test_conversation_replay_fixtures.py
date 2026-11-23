"""Replay conversation routing fixtures for GDD/superpowers coexistence."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


from _paths import PLUGIN_ROOT
FIXTURE_ROOT = PLUGIN_ROOT / "tests" / "fixtures" / "conversation-replay"


class ConversationReplayFixtureTests(unittest.TestCase):
    def test_all_conversation_replay_fixtures_pass(self) -> None:
        fixtures = sorted(FIXTURE_ROOT.glob("*.json"))
        self.assertGreaterEqual(len(fixtures), 3, "expected GDD/superpowers routing replay fixtures")

        for fixture in fixtures:
            with self.subTest(fixture=fixture.name):
                result = subprocess.run(
                    [
                        sys.executable,
                        str(PLUGIN_ROOT / "scripts" / "lint-conversation-routing-replay.py"),
                        str(fixture),
                    ],
                    text=True,
                    capture_output=True,
                    check=False,
                )
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


class ShadowMarkerInputIgnoredTests(unittest.TestCase):
    """SessionStart の `[gdd:shadow-marker]` は撤去済み。replay の `shadow_marker` 入力で routing を変えない。"""

    def _lint(self, fixture: dict) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory(prefix="gdd-replay-") as tmp:
            path = Path(tmp) / "case.json"
            path.write_text(json.dumps(fixture, ensure_ascii=False), encoding="utf-8")
            return subprocess.run(
                [sys.executable, str(PLUGIN_ROOT / "scripts" / "lint-conversation-routing-replay.py"), str(path)],
                text=True, capture_output=True, check=False,
            )

    def test_active_planning_amendment_routes_to_amendment_even_with_shadow_marker(self) -> None:
        result = self._lint({
            "case_id": "shadow-input-ignored",
            "conversation": [{"role": "user", "text": "計画途中でこれも追加して。承認前の完了条件に監査ログ確認も入れて"}],
            "context": {"active_gdd_marker": True, "shadow_marker": True, "planning_before_approval": True},
            "expected": {"primary": "gdd", "route_contains": "gate-driven-development:gdd-requirements-amendment"},
        })
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_no_marker_follow_up_is_not_status_required_even_with_shadow_marker(self) -> None:
        result = self._lint({
            "case_id": "shadow-input-ignored-continue",
            "conversation": [{"role": "user", "text": "続けて"}],
            "context": {"active_gdd_marker": False, "shadow_marker": True},
            "expected": {"primary": "gdd", "route_contains": "gate-driven-development:gdd-pre-workflow-brainstorming"},
        })
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_requires_status_or_resume_rejects_non_status_route(self) -> None:
        # primary が gdd でも、status / resume 以外の route（ここでは amendment）なら落とす
        result = self._lint({
            "case_id": "requires-status-but-amendment",
            "conversation": [{"role": "user", "text": "計画途中でこれも追加して。承認前の完了条件に監査ログ確認も入れて"}],
            "context": {"active_gdd_marker": True, "planning_before_approval": True},
            "expected": {"primary": "gdd", "requires_status_or_resume": True},
        })
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("expected status/resume-safe GDD routing", result.stderr)


if __name__ == "__main__":
    unittest.main()
