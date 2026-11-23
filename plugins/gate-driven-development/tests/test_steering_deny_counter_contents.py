"""steering への書き込みの検査の deny counter が、回数と時刻だけを書くことの契約テスト。

counter（state dir の `<16 桁 hex>.json`）を読む実装は `load_deny_count`（`count`・`ts`）と
`clear_deny`（unlink）だけで、書き込み先のパスと category は読まれていなかった。
umask のまま作られるファイルに、絶対パスを平文で残さない。
hook は subprocess で起動し、実際の入口（PreToolUse payload）から確かめる。
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

from _paths import PLUGIN_ROOT

HOOK = PLUGIN_ROOT / "hooks" / "scripts" / "validate-steering-write.py"
STATE_LIMIT = 20_000
EMAIL = "real.person" + "@" + "gmail.com"


class SteeringDenyCounterContentsTests(unittest.TestCase):
    def setUp(self) -> None:
        self._state_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self._state_dir, ignore_errors=True)
        self._tmp = str(Path(tempfile.mkdtemp()).resolve())
        self.addCleanup(shutil.rmtree, self._tmp, ignore_errors=True)
        self._state_path = Path(self._tmp) / ".steering" / "20261004-counter-test" / "state.md"
        self._state_path.parent.mkdir(parents=True, exist_ok=True)

    def _run(self, payload: dict) -> subprocess.CompletedProcess[str]:
        env = dict(os.environ)
        env["GDD_HOOK_STATE_DIR"] = self._state_dir
        return subprocess.run(
            [sys.executable, str(HOOK)],
            input=json.dumps(payload),
            env=env,
            capture_output=True,
            text=True,
        )

    def _email_payload(self) -> dict:
        return {
            "tool_name": "Write",
            "tool_input": {"file_path": str(self._state_path), "content": f"contact: {EMAIL}"},
        }

    def _counter_files(self) -> list[Path]:
        return sorted(Path(self._state_dir).glob("*.json"))

    def _assert_only_count_and_ts(self) -> None:
        files = self._counter_files()
        self.assertEqual(len(files), 1, [f.name for f in files])
        data = json.loads(files[0].read_text())
        self.assertEqual(set(data), {"count", "ts"})
        self.assertNotIn(self._tmp, files[0].read_text())

    def test_existing_category_deny_writes_only_count_and_ts(self) -> None:
        result = self._run(self._email_payload())
        self.assertEqual(result.returncode, 2, result.stderr)
        self._assert_only_count_and_ts()

    def test_oversize_write_creates_no_counter(self) -> None:
        # 上限超過は止めずに通知するだけなので、steering_size の counter は作られない
        payload = {
            "tool_name": "Write",
            "tool_input": {"file_path": str(self._state_path), "content": "x" * (STATE_LIMIT + 1)},
        }
        result = self._run(payload)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("[steering size]", result.stdout)
        self.assertEqual(self._counter_files(), [])

    def test_third_consecutive_deny_still_downgrades_to_warning_allow(self) -> None:
        # 書く中身を減らしても、3 回目で warning 付き allow に降格する契約は変わらない
        payload = self._email_payload()
        for _ in range(2):
            self.assertEqual(self._run(payload).returncode, 2)
        third = self._run(payload)
        self.assertEqual(third.returncode, 0, third.stderr)
        self.assertIn("email address", third.stdout + third.stderr)

    def test_old_format_counter_with_path_keeps_counting(self) -> None:
        # path・category 入りの古い counter も今までどおり読み、回数を引き継ぐ
        self.assertEqual(self._run(self._email_payload()).returncode, 2)
        [counter] = self._counter_files()
        counter.write_text(
            json.dumps({"count": 2, "ts": time.time(), "path": str(self._state_path), "category": "email"})
        )
        result = self._run(self._email_payload())
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
