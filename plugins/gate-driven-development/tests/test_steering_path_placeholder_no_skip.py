"""steering の書き込みの検査は、placeholder を含む行でもローカルの絶対パスを止める。

以前の `find_local_path` は、`<redacted>`・`***`・`${CLAUDE_PLUGIN_ROOT}` などを 1 つでも含む行で
パスの検出を行全体で飛ばしていた。2026-09-03 の transcript には、`${CLAUDE_PLUGIN_ROOT}` を含む
行に書いたユーザー名入りの絶対パスが、この例外で素通りした書き込みがあった。
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from _paths import PLUGIN_ROOT

HOOK = PLUGIN_ROOT / "hooks" / "scripts" / "validate-steering-write.py"
HOME_PATH = "/Users/" + "alice/work/notes.md"
LINUX_PATH = "/home/" + "bob/work/notes.md"


class SteeringPathPlaceholderNoSkipTests(unittest.TestCase):
    def setUp(self) -> None:
        self._state_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self._state_dir, ignore_errors=True)
        self._tmp = str(Path(tempfile.mkdtemp()).resolve())
        self.addCleanup(shutil.rmtree, self._tmp, ignore_errors=True)
        self._target = Path(self._tmp) / ".steering" / "20261009-test" / "worklog.md"
        self._target.parent.mkdir(parents=True, exist_ok=True)

    def _run(self, tool_name: str, tool_input: dict) -> subprocess.CompletedProcess[str]:
        # 呼ぶたびに新しい状態にする（同じ deny が 3 回続くと警告付きで通す既存の降格を避ける）
        state_dir = tempfile.mkdtemp(dir=self._state_dir)
        env = dict(os.environ)
        env["GDD_HOOK_STATE_DIR"] = state_dir
        return subprocess.run(
            [sys.executable, str(HOOK)],
            input=json.dumps({"tool_name": tool_name, "tool_input": tool_input}),
            env=env,
            capture_output=True,
            text=True,
        )

    def _write(self, content: str) -> subprocess.CompletedProcess[str]:
        return self._run("Write", {"file_path": str(self._target), "content": content})

    def _assert_denied_for_path(self, result: subprocess.CompletedProcess[str]) -> None:
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        message = json.loads(result.stdout or result.stderr)["systemMessage"]
        self.assertIn("local absolute path", message)

    # block すべき入力が allow になる（placeholder が同じ行のパスの検査を外す）
    def test_placeholder_and_real_path_on_same_line_are_denied(self) -> None:
        for placeholder in ("<redacted>", "***", "${CLAUDE_PLUGIN_ROOT}", "/path/to/x"):
            with self.subTest(placeholder=placeholder):
                self._assert_denied_for_path(self._write(f"- {placeholder} は {HOME_PATH} への symlink\n"))

    def test_placeholder_and_linux_home_path_are_denied(self) -> None:
        self._assert_denied_for_path(self._write(f"- value <redacted> at {LINUX_PATH}\n"))

    # 判定できないとき（ユーザー名を伏せた絶対パス）は止める側に倒す
    def test_absolute_path_with_masked_user_is_denied(self) -> None:
        for masked in ("/Users/" + "***/work/x.md", "/Users/" + "<redacted>/work/x.md"):
            with self.subTest(masked=masked):
                self._assert_denied_for_path(self._write(f"- see {masked}\n"))

    # Edit・MultiEdit の経路でも同じく deny になる
    def test_edit_and_multiedit_paths_are_denied_too(self) -> None:
        self._target.write_text("# worklog\n")
        line = f"- ${{CLAUDE_PLUGIN_ROOT}} -> {HOME_PATH}\n"
        self._assert_denied_for_path(
            self._run("Edit", {"file_path": str(self._target), "old_string": "# worklog\n", "new_string": line})
        )
        self._assert_denied_for_path(
            self._run(
                "MultiEdit",
                {"file_path": str(self._target), "edits": [{"old_string": "# worklog\n", "new_string": line}]},
            )
        )

    # block すべき入力が allow になる（`Active Worktree Path` の語が同じ行のパスの検査を外す）
    def test_active_worktree_path_word_with_other_path_is_denied(self) -> None:
        for line in (
            f"| worktree root | `{HOME_PATH}` | state.md の Active Worktree Path と一致 |\n",
            f"- Active Worktree Path: `.` 、元は {HOME_PATH}\n",
            f"- Active Worktree Path: {HOME_PATH} {LINUX_PATH}\n",
        ):
            with self.subTest(line=line):
                self._assert_denied_for_path(self._write(line))

    def test_active_worktree_path_field_line_is_allowed(self) -> None:
        for line in (
            f"- Active Worktree Path: {HOME_PATH}\n",
            f"- Active Worktree Path: `{HOME_PATH}`\n",
            f"Active Worktree Path: {HOME_PATH}\n",
        ):
            with self.subTest(line=line):
                result = self._write(line)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_placeholder_only_lines_are_allowed(self) -> None:
        content = "- `${CLAUDE_PLUGIN_ROOT}/hooks/x.py` と `/path/to/file`、token は <redacted>\n"
        result = self._write(content)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
