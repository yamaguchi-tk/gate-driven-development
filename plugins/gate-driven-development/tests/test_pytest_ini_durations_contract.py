"""plugin 直下の `pytest.ini` が、遅いテストの一覧（`--durations=30 --durations-min=1.0`）を出すことの契約。

一覧の見出しは毎回出る。行は 1 秒以上かかったものだけを、遅い順に最大 30 行出す。

CI（`.github/workflows/plugin-lint.yml`）は `pytest.ini` を読んで全量を回すので、CI のログに
遅いテストの上位が残る。テストの実行時間を削るときは、この一覧を前後の比較に使う。
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from _paths import PLUGIN_ROOT

# 内側の pytest に渡すテスト。何もしないので、負荷の下でも 1 秒に届かない（git などを起動するテストを渡すと、
# 負荷で 1 秒を超えて一覧に出る。2026-10-26 の並列の全量で起きた）。
FAST_TESTS = "def test_a():\n    pass\n\n\ndef test_b():\n    pass\n"


class PytestIniDurationsContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "test_fast.py").write_text(FAST_TESTS, encoding="utf-8")
            # plugin の外のファイルを渡すので、`-c` で plugin の pytest.ini を読ませる
            cls.result = subprocess.run(
                [
                    sys.executable, "-m", "pytest", "test_fast.py",
                    "-c", str(PLUGIN_ROOT / "pytest.ini"), "--rootdir", tmp,
                    "-q", "-n", "0", "-p", "no:cacheprovider",
                ],
                cwd=tmp,
                capture_output=True,
                text=True,
                check=False,
            )

    def test_pytest_run_reports_slowest_durations(self) -> None:
        result = self.result
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("slowest 30 durations", result.stdout)

    def test_fast_tests_are_hidden_from_the_list(self) -> None:
        """手元で速いテストだけを回したときは、一覧に行を出さない（出力を agent の文脈に積まない）。"""
        result = self.result
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("durations < 1s hidden", result.stdout)
        self.assertNotRegex(result.stdout, r"\d+\.\d+s (setup|call|teardown) ")


if __name__ == "__main__":
    unittest.main()
