"""express も requirements-gating の計画のレビューを通る（2026-10-29）。

express の requirements.md は、reviewer を起動する前の lint-plan-consistency.py を通る形で書く。
build の precheck は、express でも Requirements Review Status の承認を求める。
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _paths import PLUGIN_ROOT  # noqa: E402
from test_p0_p1_operational_hardening_contract import build_precheck_passes  # noqa: E402

LINT = PLUGIN_ROOT / "scripts" / "lint-plan-consistency.py"
EXPRESS_TEMPLATE = PLUGIN_ROOT / "references" / "requirements-template-express.md"


def express_template_body() -> str:
    text = EXPRESS_TEMPLATE.read_text(encoding="utf-8")
    match = re.search(r"^## Template\n+```markdown\n(.*?)^```$", text, re.M | re.S)
    if match is None:
        raise AssertionError("requirements-template-express.md に ## Template の markdown fence が無い")
    return match.group(1)


class ExpressTemplatePassesLintTest(unittest.TestCase):
    def test_express_template_passes_requirements_entry_lint(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            steering = Path(tmp)
            (steering / "requirements.md").write_text(express_template_body(), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(LINT), "--steering-dir", str(steering), "--entry", "requirements"],
                capture_output=True,
                text=True,
            )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


class ExpressBuildPrecheckTest(unittest.TestCase):
    def setUp(self) -> None:
        self.schema = json.loads((PLUGIN_ROOT / "references" / "state-schema.json").read_text(encoding="utf-8"))

    def test_express_without_requirements_review_does_not_enter_build(self) -> None:
        state = {
            "Requirements Review Status": "pending",
            "Design Review Status": "pending",
            "Human Check Status": "approved",
        }
        self.assertFalse(build_precheck_passes(self.schema, "quick (express)", state))

    def test_express_with_requirements_review_in_review_does_not_enter_build(self) -> None:
        state = {
            "Requirements Review Status": "in_review",
            "Design Review Status": "approved",
            "Human Check Status": "approved",
        }
        self.assertFalse(build_precheck_passes(self.schema, "quick (express)", state))

    def test_express_without_design_review_status_approved_does_not_enter_build(self) -> None:
        state = {
            "Requirements Review Status": "approved",
            "Design Review Status": "pending",
            "Human Check Status": "approved",
        }
        self.assertFalse(build_precheck_passes(self.schema, "quick (express)", state))

    def test_express_after_requirements_gating_and_human_check_enters_build(self) -> None:
        state = {
            "Requirements Review Status": "approved",
            "Design Review Status": "approved",
            "Human Check Status": "approved",
        }
        self.assertTrue(build_precheck_passes(self.schema, "quick (express)", state))


if __name__ == "__main__":
    unittest.main()
