"""独立レビュー R3 #1: wrapper が Python の非 block 終了を deny(exit 2) に倒す契約。

Python 側の top-level guard は `main()` の中でしか効かない。module import 段階の例外
（`lib/steering_size.py` の欠落・部分更新・`sys.modules["lib"]` 衝突）は exit 1 =
PreToolUse の**非 block** になり、email / secret / peer-turn の既存 deny が
1 件も走らないまま write が通る。fail-closed の正本は
`hooks/scripts/run-steering-write-hook.sh` の rc guard 側に置く。
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from _paths import PLUGIN_ROOT
WRAPPER = PLUGIN_ROOT / "hooks" / "scripts" / "run-steering-write-hook.sh"
REAL_SCRIPTS = PLUGIN_ROOT / "hooks" / "scripts"

NON_EXAMPLE_EMAIL = "real.person" + "@" + "gmail.com"


class SteeringWriteWrapperFailClosedTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self._tmp, ignore_errors=True)
        self._home = self._tmp / "home"
        (self._home / ".claude").mkdir(parents=True)

    def _fake_plugin_root(self) -> Path:
        """`hooks/scripts` を丸ごと写した壊せる plugin root を作る。"""
        root = self._tmp / "fake-plugin-root"
        shutil.copytree(
            REAL_SCRIPTS,
            root / "hooks" / "scripts",
            ignore=shutil.ignore_patterns("__pycache__"),
        )
        return root

    def _run(
        self, plugin_root: Path, payload: dict, *, extra_env: dict | None = None
    ) -> subprocess.CompletedProcess[str]:
        env = dict(os.environ)
        env["HOME"] = str(self._home)
        env["CLAUDE_PLUGIN_ROOT"] = str(plugin_root)
        env["GDD_HOOK_STATE_DIR"] = str(self._tmp / "state")
        if extra_env:
            env.update(extra_env)
        return subprocess.run(
            ["bash", str(WRAPPER)],
            input=json.dumps(payload),
            env=env,
            capture_output=True,
            text=True,
            timeout=60,
        )

    def _payload(self) -> dict:
        state_path = self._tmp / ".steering" / "20260906-wrapper" / "state.md"
        state_path.parent.mkdir(parents=True, exist_ok=True)
        return {
            "tool_name": "Write",
            "tool_input": {
                "file_path": str(state_path),
                "content": f"contact: {NON_EXAMPLE_EMAIL}\n",
            },
        }

    def test_import_failure_denies_with_fixed_message_and_no_traceback(self) -> None:
        """`lib/steering_size.py` が読めないと Python は exit 1（import 例外）。

        wrapper が rc を受けて固定文 deny + exit 2 に倒す。traceback は path /
        content の生値を含みうるため出さない。
        """
        root = self._fake_plugin_root()
        (root / "hooks" / "scripts" / "lib" / "steering_size.py").unlink()

        result = self._run(root, self._payload())

        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        self.assertNotIn("ModuleNotFoundError", result.stderr)
        message = json.loads(result.stderr)["systemMessage"]
        self.assertIn("could not run to completion and fails closed", message)
        self.assertNotIn(NON_EXAMPLE_EMAIL, result.stderr)

    def test_healthy_plugin_root_still_emits_the_real_deny(self) -> None:
        """正常時は Python の deny 本文（exit 2 / stderr JSON）がそのまま通る。"""
        result = self._run(self._fake_plugin_root(), self._payload())

        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("email address", json.loads(result.stderr)["systemMessage"])

    def test_healthy_plugin_root_allows_clean_write(self) -> None:
        """allow 経路（exit 0 / stdout JSON）も wrapper の rc guard で潰れない。"""
        payload = self._payload()
        payload["tool_input"]["content"] = "ok\n"

        result = self._run(self._fake_plugin_root(), payload)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(json.loads(result.stdout)["continue"])

    def test_unwritable_tmpdir_still_denies_with_reason(self) -> None:
        """`mktemp` が失敗しても deny(exit 2) と本来の理由を落とさない（独立レビュー R4 #2）。

        stderr 退避先が作れない縮退経路。`set -e` 依存の構造では中継や rm の失敗が
        別 rc の途中終了 = PreToolUse の非 block になり、退避先を `/dev/null` に倒すと
        rc 2 の deny 本文まで消えて「理由なし block」になっていた。
        """
        unwritable = self._tmp / "no-write"
        unwritable.mkdir(mode=0o500)
        self.addCleanup(unwritable.chmod, 0o700)

        result = self._run(
            self._fake_plugin_root(), self._payload(), extra_env={"TMPDIR": str(unwritable)}
        )

        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("email address", json.loads(result.stderr)["systemMessage"])

    def test_kill_switch_still_short_circuits_before_python(self) -> None:
        """kill switch は従来どおり Python 起動前に効く（rc guard より前）。"""
        (self._home / ".claude" / "gdd-hooks-disabled").write_text("")
        root = self._fake_plugin_root()
        (root / "hooks" / "scripts" / "lib" / "steering_size.py").unlink()

        result = self._run(root, self._payload())

        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
