"""AC-1 AC-2 AC-3: PreToolUse hook が active /gdd-dev session 中の
host-native EnterWorktree 呼び出しを block し、それ以外は fail-open で
allow することを検証する contract test。"""
from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


from _paths import PLUGIN_ROOT
from _git_fixture import init_repo


class BlockEnterWorktreeHookContractTests(unittest.TestCase):
    def _init_repo(self, path: Path) -> None:
        init_repo(path)

    def _write_state(self, path: Path, active: bool, session_id: str = "test-session") -> None:
        state_dir = path / ".claude"
        state_dir.mkdir(exist_ok=True)
        (state_dir / "gdd-dev.local.md").write_text(
            f"---\nactive: {str(active).lower()}\nsession_id: {session_id}\n---\n",
            encoding="utf-8",
        )

    def _run_hook(self, cwd: Path, session_id: str = "test-session") -> "subprocess.CompletedProcess[str]":
        payload = {"tool_name": "EnterWorktree", "tool_input": {}}
        env = {
            **os.environ,
            "CLAUDE_PLUGIN_ROOT": str(PLUGIN_ROOT),
            "CLAUDE_CODE_SESSION_ID": session_id,
        }
        return subprocess.run(
            ["bash", str(PLUGIN_ROOT / "hooks" / "scripts" / "run-block-enter-worktree-hook.sh")],
            cwd=cwd,
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            env=env,
            check=False,
        )

    def test_active_same_session_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            self._write_state(repo, active=True, session_id="test-session")
            result = self._run_hook(repo, session_id="test-session")
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["decision"], "block")
            self.assertIn("workspace-policy", payload["reason"])

    def test_no_state_file_allows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            result = self._run_hook(repo)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, "")

    def test_active_different_session_allows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            self._write_state(repo, active=True, session_id="other-session")
            result = self._run_hook(repo, session_id="test-session")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, "")

    def test_not_active_allows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            self._write_state(repo, active=False, session_id="test-session")
            result = self._run_hook(repo, session_id="test-session")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, "")

    def test_corrupted_state_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            state_dir = repo / ".claude"
            state_dir.mkdir(exist_ok=True)
            (state_dir / "gdd-dev.local.md").write_text("not valid frontmatter at all", encoding="utf-8")
            result = self._run_hook(repo)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["decision"], "block")

    def test_hooks_json_registers_enter_worktree_matcher(self) -> None:
        hooks_config = json.loads((PLUGIN_ROOT / "hooks" / "hooks.json").read_text(encoding="utf-8"))
        pre_tool_use = hooks_config["hooks"]["PreToolUse"]
        matchers = [entry.get("matcher", "") for entry in pre_tool_use]
        self.assertIn("EnterWorktree", matchers)
        matching_entry = next(entry for entry in pre_tool_use if entry.get("matcher") == "EnterWorktree")
        self.assertTrue(
            any(
                "run-block-enter-worktree-hook.sh" in hook.get("command", "")
                for hook in matching_entry["hooks"]
            )
        )


if __name__ == "__main__":
    unittest.main()
