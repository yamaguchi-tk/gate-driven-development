"""budget 実測の 1 コマンド化（O-3）の契約。

O-2（planning 成果物の二層化 = trace 群の記入時期遅延）は精度二層化で
trace 群自体が廃止されたため、
本ファイルには measure-budgets.sh の契約だけが残る。
"""

import subprocess
import unittest

from _paths import PLUGIN_ROOT as ROOT


class MeasureBudgetsScriptTests(unittest.TestCase):
    def test_script_reports_all_three_budgets_with_headroom(self) -> None:
        proc = subprocess.run(
            ["bash", str(ROOT / "scripts" / "measure-budgets.sh")],
            capture_output=True, text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        for label in (
            "references/*.md lines (ratchet)",
            "express runtime tokens",
            "standard runtime tokens",
            "headroom",
        ):
            self.assertIn(label, proc.stdout)


if __name__ == "__main__":
    unittest.main()
