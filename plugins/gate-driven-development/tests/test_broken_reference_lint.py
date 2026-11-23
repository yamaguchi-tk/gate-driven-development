"""RED/GREEN tests for tests/checks/broken-reference-lint.sh."""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from _paths import PLUGIN_ROOT
LINT_SCRIPT = PLUGIN_ROOT / "tests" / "checks" / "broken-reference-lint.sh"


class BrokenReferenceLintTests(unittest.TestCase):
    def _run_lint(self, fake_root: Path) -> subprocess.CompletedProcess:
        env = dict(os.environ)
        env["ROOT"] = str(fake_root)
        env["PYTHON_BIN"] = sys.executable
        return subprocess.run(
            ["bash", str(LINT_SCRIPT)],
            cwd=fake_root,
            env=env,
            capture_output=True,
            text=True,
        )

    def test_broken_reference_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill_dir = root / "skills" / "fake-skill"
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text(
                "See `scripts/nonexistent.sh` for details.\n",
                encoding="utf-8",
            )
            result = self._run_lint(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("nonexistent.sh", result.stderr)

    def test_skill_relative_and_plugin_relative_references_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill_dir = root / "skills" / "fake-skill"
            (skill_dir / "scripts").mkdir(parents=True)
            (skill_dir / "scripts" / "helper.sh").write_text("#!/usr/bin/env bash\n", encoding="utf-8")
            (root / "scripts").mkdir(parents=True)
            (root / "scripts" / "root-helper.sh").write_text("#!/usr/bin/env bash\n", encoding="utf-8")
            (skill_dir / "SKILL.md").write_text(
                "Skill-relative: `scripts/helper.sh`. "
                "Plugin-root-relative: `scripts/root-helper.sh`.\n",
                encoding="utf-8",
            )
            result = self._run_lint(root)
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_claude_plugin_root_prefixed_reference_resolves(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill_dir = root / "skills" / "fake-skill"
            skill_dir.mkdir(parents=True)
            (root / "scripts").mkdir(parents=True)
            (root / "scripts" / "root-helper.sh").write_text("#!/usr/bin/env bash\n", encoding="utf-8")
            (skill_dir / "SKILL.md").write_text(
                "Plugin-root prefixed: `${CLAUDE_PLUGIN_ROOT}/scripts/root-helper.sh`.\n",
                encoding="utf-8",
            )
            result = self._run_lint(root)
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_claude_plugin_root_prefixed_broken_reference_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill_dir = root / "skills" / "fake-skill"
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text(
                "Plugin-root prefixed: `${CLAUDE_PLUGIN_ROOT}/scripts/nonexistent.sh`.\n",
                encoding="utf-8",
            )
            result = self._run_lint(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("nonexistent.sh", result.stderr)

    def test_path_traversal_reference_is_treated_as_broken(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill_dir = root / "skills" / "fake-skill"
            skill_dir.mkdir(parents=True)
            (root / "CHANGELOG.md").write_text("# Changelog\n", encoding="utf-8")
            (skill_dir / "SKILL.md").write_text(
                "Traversal: `scripts/../CHANGELOG.md`.\n",
                encoding="utf-8",
            )
            result = self._run_lint(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("CHANGELOG.md", result.stderr)

    def test_reference_matching_a_directory_is_treated_as_broken(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill_dir = root / "skills" / "fake-skill"
            (root / "scripts" / "not-a-file.sh").mkdir(parents=True)
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text(
                "Reference: `scripts/not-a-file.sh`.\n",
                encoding="utf-8",
            )
            result = self._run_lint(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("not-a-file.sh", result.stderr)

    def test_fenced_code_block_paths_are_ignored(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill_dir = root / "skills" / "fake-skill"
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text(
                "```\nexample: `scripts/does-not-exist-illustrative.sh`\n```\n",
                encoding="utf-8",
            )
            result = self._run_lint(root)
            self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
