"""Contract tests for blocking standalone superpowers skills during active GDD."""
from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path


from _paths import PLUGIN_ROOT
from _git_fixture import init_repo


class ActiveGddSkillGateContractTests(unittest.TestCase):
    def _init_repo(self, path: Path) -> None:
        init_repo(path)

    def _write_active_state(self, path: Path, *, active: bool = True) -> None:
        state_dir = path / ".claude"
        state_dir.mkdir(exist_ok=True)
        (state_dir / "gdd-dev.local.md").write_text(
            f"---\nactive: {str(active).lower()}\nsession_id: test-session\n---\n",
            encoding="utf-8",
        )

    def _run_hook(self, cwd: Path, skill_name: str) -> subprocess.CompletedProcess[str]:
        payload = {
            "tool_name": "Skill",
            "tool_input": {"name": skill_name},
        }
        env = {
            "CLAUDE_PLUGIN_ROOT": str(PLUGIN_ROOT),
            "CLAUDE_CODE_SESSION_ID": "test-session",
        }
        return subprocess.run(
            ["bash", str(PLUGIN_ROOT / "hooks" / "scripts" / "run-active-gdd-skill-gate-hook.sh")],
            cwd=cwd,
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            env=env,
            check=False,
        )

    def _run_expansion_hook(self, cwd: Path, prompt: str) -> subprocess.CompletedProcess[str]:
        payload = {"prompt": prompt}
        env = {
            "CLAUDE_PLUGIN_ROOT": str(PLUGIN_ROOT),
            "CLAUDE_CODE_SESSION_ID": "test-session",
        }
        return subprocess.run(
            ["bash", str(PLUGIN_ROOT / "hooks" / "scripts" / "run-active-gdd-skill-expansion-gate-hook.sh")],
            cwd=cwd,
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            env=env,
            check=False,
        )

    def test_hooks_json_registers_skill_matcher(self) -> None:
        hooks = json.loads((PLUGIN_ROOT / "hooks" / "hooks.json").read_text(encoding="utf-8"))
        pre_tool = hooks["hooks"]["PreToolUse"]
        commands = [
            hook["command"]
            for entry in pre_tool
            if entry.get("matcher") == "Skill"
            for hook in entry.get("hooks", [])
        ]

        self.assertTrue(commands, "PreToolUse must register a Skill matcher")
        self.assertTrue(
            any("run-active-gdd-skill-gate-hook.sh" in command for command in commands),
            commands,
        )

    def test_hooks_json_registers_user_prompt_expansion_matcher(self) -> None:
        hooks = json.loads((PLUGIN_ROOT / "hooks" / "hooks.json").read_text(encoding="utf-8"))
        expansion_hooks = hooks["hooks"].get("UserPromptExpansion")
        self.assertIsInstance(expansion_hooks, list)

        commands = [
            hook["command"]
            for entry in expansion_hooks or []
            if entry.get("matcher") == "*"
            for hook in entry.get("hooks", [])
        ]
        self.assertTrue(
            any("run-active-gdd-skill-expansion-gate-hook.sh" in command for command in commands),
            commands,
        )

    def test_active_gdd_blocks_standalone_superpowers_planning_skill(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            self._write_active_state(repo)

            result = self._run_hook(repo, "superpowers:writing-plans")

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["decision"], "block")
            self.assertIn("active GDD", payload["reason"])
            self.assertIn("gdd-requirements-amendment", payload["reason"])
            self.assertIn("gdd-task-breakdown", payload["reason"])
            self.assertIn("gdd-brainstorming", payload["reason"])

    def test_active_gdd_blocks_standalone_superpowers_execution_and_brainstorming(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            self._write_active_state(repo)

            for skill_name in ["superpowers:executing-plans", "superpowers:brainstorming"]:
                with self.subTest(skill_name=skill_name):
                    result = self._run_hook(repo, skill_name)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    payload = json.loads(result.stdout)
                    self.assertEqual(payload["decision"], "block")

    def test_non_active_gdd_allows_superpowers_skill(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)

            result = self._run_hook(repo, "superpowers:writing-plans")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, "")

    def test_active_gdd_allows_gdd_skill(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            self._write_active_state(repo)

            result = self._run_hook(repo, "gate-driven-development:gdd-task-breakdown")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, "")

    def test_active_gdd_blocks_direct_superpowers_skill_invocation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            self._write_active_state(repo)

            result = self._run_expansion_hook(repo, "/superpowers:writing-plans")

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["decision"], "block")
            self.assertIn("UserPromptExpansion", payload["reason"])
            self.assertIn("gdd-requirements-amendment", payload["reason"])

    def test_non_active_gdd_allows_direct_superpowers_skill_invocation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)

            result = self._run_expansion_hook(repo, "/superpowers:writing-plans")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, "")


if __name__ == "__main__":
    unittest.main()
