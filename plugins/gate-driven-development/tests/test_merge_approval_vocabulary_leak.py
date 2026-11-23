"""AC-2: 配布物のどの行も is_merge_approval() で承認と判定されないことを固定する。

design.md § 承認判定の設計 条件2「リークテストは述語で行う」が正本。
素の MERGE_APPROVAL_RE の部分一致で書くと、`マージして再学習まで` を含む
既存 10 行が誤って承認判定される（design.md が実測列挙）。
"""
from __future__ import annotations

import sys
import unittest

from _paths import PLUGIN_ROOT
sys.path.insert(0, str(PLUGIN_ROOT / "hooks" / "scripts"))

from lib.constants import is_merge_approval  # noqa: E402

SCAN_GLOBS = ("skills/**/*.md", "references/**/*.md", "agents/**/*.md",
              "commands/**/*.md", "CLAUDE.md", "README.md", "CHANGELOG.md", "CHANGELOG-archive*.md",
              "changelog.d/*.md")


def _scan_files():
    found = []
    for pattern in SCAN_GLOBS:
        found.extend(sorted(PLUGIN_ROOT.glob(pattern)))
    return found


class MergeApprovalVocabularyLeakTests(unittest.TestCase):
    def test_self_check_positive_fixture_is_detected(self):
        # このテスト自身が判別力を持つことを先に自己検証する（空洞化防止）。
        self.assertTrue(is_merge_approval("マージして"))

    def test_no_distributed_file_line_is_approval(self):
        files = _scan_files()
        self.assertTrue(files, "走査対象ファイルが 0 件（glob の誤り）")
        leaks = []
        for path in files:
            try:
                text = path.read_text(encoding="utf-8")
            except OSError:
                continue
            for lineno, line in enumerate(text.splitlines(), start=1):
                if is_merge_approval(line):
                    leaks.append(f"{path.relative_to(PLUGIN_ROOT)}:{lineno}: {line!r}")
        self.assertEqual(leaks, [], f"承認語彙リーク: {leaks}")


if __name__ == "__main__":
    unittest.main()
