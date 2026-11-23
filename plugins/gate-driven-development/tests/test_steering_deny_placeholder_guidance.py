"""steering の書き込みの検査が、パス・email の置き換え先に placeholder を勧めないことを確かめる。

deny 文がパス・email に `<redacted>` などを勧めると、`/Users/<redacted>/...` のように伏せた後も
絶対パスの形が残り、同じ deny が繰り返される。
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

# 以前の find_local_path が、行に含まれるとパスの検出を行全体で飛ばしていた語。
# deny 文はパス・email の値をどう書き換えるかを案内する。そこでこれらの語を勧めると、
# 値の一部だけを伏せて絶対パスの形が残り、deny が繰り返される。plugin のファイルを
# `${CLAUDE_PLUGIN_ROOT}/...` で指すこと（faq）は、値の書き換えではないので別の話である。
PATH_PLACEHOLDER_TOKENS = (
    "<absolute-path>",
    "/absolute/path",
    "/path/to/",
    "/path/to",
    "${CLAUDE_PLUGIN_ROOT}",
    "<redacted>",
    "***",
)

HOOK = PLUGIN_ROOT / "hooks" / "scripts" / "validate-steering-write.py"


class SteeringDenyPlaceholderGuidanceTests(unittest.TestCase):
    def setUp(self) -> None:
        self._state_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self._state_dir, ignore_errors=True)
        self._tmp = str(Path(tempfile.mkdtemp()).resolve())
        self.addCleanup(shutil.rmtree, self._tmp, ignore_errors=True)

    def _deny_message(self, content: str) -> str:
        path = Path(self._tmp) / ".steering" / "20261008-test" / "request.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"tool_name": "Write", "tool_input": {"file_path": str(path), "content": content}}
        env = dict(os.environ)
        env["GDD_HOOK_STATE_DIR"] = self._state_dir
        result = subprocess.run(
            [sys.executable, str(HOOK)],
            input=json.dumps(payload),
            env=env,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 2, result.stderr)
        return json.loads(result.stdout or result.stderr)["systemMessage"]

    def _assert_no_placeholder(self, message: str) -> None:
        for token in PATH_PLACEHOLDER_TOKENS:
            self.assertNotIn(token, message)

    def test_path_deny_does_not_recommend_placeholder(self) -> None:
        message = self._deny_message("> see /Users/" + "someone/work/notes.md\n")
        self._assert_no_placeholder(message)

    def test_email_deny_does_not_recommend_placeholder(self) -> None:
        message = self._deny_message("> mail " + "real.person" + "@" + "gmail.com\n")
        self._assert_no_placeholder(message)
        self.assertIn("example.com", message)

    def test_secret_deny_still_recommends_redacted(self) -> None:
        message = self._deny_message("password: " + "hunter2hunter2\n")
        self.assertIn("<redacted>", message)
        self.assertNotIn("(local path)", message)


if __name__ == "__main__":
    unittest.main()
