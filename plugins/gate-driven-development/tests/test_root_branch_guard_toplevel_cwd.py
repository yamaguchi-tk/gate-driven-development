"""root branch guard が、Claude Code の payload の最上位の `cwd` で判定すること。

Claude Code の Bash の PreToolUse payload は、tool_input に cwd を持たず、最上位に `cwd` を持つ。
desktop の worktree のセッションでは hook のプロセスの cwd が root checkout になる（2026-10-09 実測）。
最上位の cwd を読まないと、worktree の中のブランチ作成を root の active な state で止めていた。
"""

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from _root_branch_guard_support import (
    RootBranchGuardFixtureMixin,
    init_git_repo,
    run_root_branch_guard_raw,
)

BRANCH = "git checkout -b feat"
UNUSABLE_TOP_CWDS = ("", 123, None, ["x"], "relative/dir", "~-/x", "/tmp/a\x00b", "/tmp/\ud800")


class ToplevelCwdTests(RootBranchGuardFixtureMixin, unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        base = Path(self._tmp.name).resolve()
        self.root = base / "repo"
        self.root.mkdir()
        init_git_repo(self.root)
        self.worktree = base / "wt"
        subprocess.run(
            ["git", "worktree", "add", "-q", "-b", "side", str(self.worktree)],
            cwd=self.root, check=True, capture_output=True,
        )
        self._write_active_state(self.root)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def run_guard(
        self, process_cwd: Path, command: str, top: object, tool_cwd: str | None = None, tool_cwd_key: str = "cwd"
    ):
        # tool_input の実行先は tool_input.cwd、Codex は tool_input.workdir。guard はどちらも読む。
        tool_input = {"command": command}
        if tool_cwd is not None:
            tool_input[tool_cwd_key] = tool_cwd
        stdin = json.dumps({"tool_name": "Bash", "tool_input": tool_input, "cwd": top}).encode()
        return run_root_branch_guard_raw(stdin, process_cwd=process_cwd)

    def assert_denied_at(self, result, cwd: Path) -> None:
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        message = json.loads(result.stderr.decode(errors="surrogateescape"))["systemMessage"]
        self.assertIn("Blocked GDD root branch creation", message)
        self.assertIn(f"cwd: {cwd}\n", message)

    def test_branch_in_linked_worktree_is_allowed_when_hook_cwd_is_root(self) -> None:
        result = self.run_guard(self.root, BRANCH, str(self.worktree))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_branch_in_active_root_is_denied_when_hook_cwd_is_worktree(self) -> None:
        self.assert_denied_at(self.run_guard(self.worktree, BRANCH, str(self.root)), self.root)

    def test_unusable_toplevel_cwd_falls_back_to_hook_cwd(self) -> None:
        for top in UNUSABLE_TOP_CWDS:
            with self.subTest(top=top):
                self.assert_denied_at(self.run_guard(self.root, BRANCH, top), self.root)
                allowed = self.run_guard(self.worktree, BRANCH, top)
                self.assertEqual(allowed.returncode, 0, allowed.stdout + allowed.stderr)

    def test_unusable_toplevel_cwd_with_removed_hook_cwd_is_unresolved(self) -> None:
        with tempfile.TemporaryDirectory() as base:
            gone = Path(base) / "gone"
            gone.mkdir()
            stdin = json.dumps({"tool_name": "Bash", "tool_input": {"command": BRANCH}, "cwd": "relative/dir"}).encode()
            result = run_root_branch_guard_raw(stdin, removed_cwd=gone)
            if b"failed to make path absolute" in result.stderr:
                self.skipTest("python3 cannot start in a removed cwd on this platform")
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertIn(b"could not resolve the working directory", result.stderr)

    def test_exec_target_in_active_root_is_denied_from_linked_worktree(self) -> None:
        for command in (f"git -C {self.root} switch -c feat", f"cd {self.root} && git checkout -b feat"):
            with self.subTest(command=command):
                self.assert_denied_at(self.run_guard(self.root, command, str(self.worktree)), self.root)

    def test_gdd_named_branch_in_inactive_root_exec_target_is_denied(self) -> None:
        (self.root / ".claude" / "gdd-dev.local.md").unlink()
        for command in (
            f"git -C {self.root} switch -c gdd/20261009-x",
            f"cd {self.root} && git checkout -b gdd/20261009-x",
        ):
            with self.subTest(command=command):
                self.assert_denied_at(self.run_guard(self.root, command, str(self.worktree)), self.root)
        allowed = self.run_guard(self.root, "git checkout -b gdd/20261009-x", str(self.worktree))
        self.assertEqual(allowed.returncode, 0, allowed.stdout + allowed.stderr)

    def test_tool_input_cwd_comes_before_toplevel_cwd(self) -> None:
        for key in ("cwd", "workdir"):
            with self.subTest(key=key):
                result = self.run_guard(
                    self.worktree, BRANCH, str(self.worktree), tool_cwd=str(self.root), tool_cwd_key=key
                )
                self.assert_denied_at(result, self.root)

    def test_gdd_worktree_from_head_is_still_denied_from_linked_worktree(self) -> None:
        command = "git worktree add ../wt2 -b gdd/20261009-x HEAD"
        result = self.run_guard(self.root, command, str(self.worktree))
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
