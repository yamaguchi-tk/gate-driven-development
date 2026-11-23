"""`lib/reviewed_by_guard.py` の `edited_text`（Edit を Claude Code の規則で当てた結果）のテスト。

実行: `python3 -m pytest plugins/gate-driven-development/tests/test_reviewed_by_guard_edited_text.py -q`

Claude Code の Edit は、`new_string` が空で `old_string` が改行で終わらないとき、`old_string` と改行が
1 か所でも続いていれば `old_string` と改行を置換の対象にする（replace_all なら全部、そうでなければ最初の 1 つ）。
"""
from __future__ import annotations

import sys
import unittest

from _paths import PLUGIN_ROOT
from _plugin_module_loader import load_plugin_module

sys.path.insert(0, str(PLUGIN_ROOT / "hooks" / "scripts" / "lib"))
edited_text = load_plugin_module("hooks/scripts/lib/reviewed_by_guard.py").edited_text


class EditedTextTests(unittest.TestCase):
    def test_cases(self):
        cases = [
            # (text, old, new, replace_all, 期待)
            ("ab\nx", "ab", "", False, "x"),
            ("ab x", "ab", "", False, " x"),
            ("ab\nab", "ab", "", True, "ab"),  # 改行が続く方だけを全部消す
            ("abab\n", "ab", "", True, "ab"),  # 改行が続かない最初の ab は残る
            ("aaa\n", "aa", "", True, "a"),  # 重なる old_string
            ("x ab\nab\n", "ab", "", False, "x ab\n"),  # 最初の「ab と改行」
            ("ab\nab\n", "ab\n", "", True, ""),
            ("ab\nab", "ab", "c", True, "c\nc"),
        ]
        for text, old, new, replace_all, expected in cases:
            with self.subTest(text=text, old=old, new=new, replace_all=replace_all):
                self.assertEqual(edited_text(text, [(old, new, replace_all)]), expected)

    def test_missing_old_string_is_none(self):
        self.assertIsNone(edited_text("abc", [("zz", "", False)]))


if __name__ == "__main__":
    unittest.main()
