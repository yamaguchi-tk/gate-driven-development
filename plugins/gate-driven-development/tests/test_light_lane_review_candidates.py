"""軽いレーンの独立レビューに渡す「呼び出し元の候補」を列挙するスクリプトの契約テスト。

スクリプトは repo root の `scripts/light-lane-review-candidates.py`（GDD plugin の配布物の外）。
差分から変えた関数名・定数名を決定的に抜き出し、リポジトリを grep した `ファイル:行` を
そのまま出す。main の判断は入れない（独立性を保つ）。
"""
from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from _paths import PLUGIN_ROOT, REPO_ROOT
SCRIPT = REPO_ROOT / "scripts" / "light-lane-review-candidates.py"
IN_CANONICAL_REPO = (REPO_ROOT / "plugins" / "gate-driven-development").resolve() == PLUGIN_ROOT.resolve() and (
    REPO_ROOT / "review-log" / "README.md"
).is_file()
GIT_ENV = {**os.environ, "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"}


def load():
    spec = importlib.util.spec_from_file_location("light_lane_review_candidates", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def diff_of(path: str, body: str, header: str = "") -> str:
    return (
        f"diff --git a/{path} b/{path}\n{header}"
        f"--- a/{path}\n+++ b/{path}\n"
        f"{body}"
    )


class CandidatesTestBase(unittest.TestCase):
    def setUp(self) -> None:
        if not IN_CANONICAL_REPO:
            self.skipTest("canonical repo 外では repo root の scripts/ を検査しない")
        self.mod = load()
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self._tmp.name)
        subprocess.run(["git", "init", "-q", "-b", "main", str(self.repo)], check=True, env=GIT_ENV)
        self.files = {
            "lib/guard.py": "def parse_x(s):\n    return s\n\nLIMIT_MAX = 3\n",
            "hooks/a.py": "from lib.guard import parse_x\n\nparse_x('a')\nif n > LIMIT_MAX:\n    pass\n",
            "hooks/b.sh": "check_it() {\n  :\n}\ncheck_it\n",
            "docs/note.md": "parse_x を呼ぶ\n",
            "review-log/x.md": "parse_x の指摘\n",
            "lib/old.py": "def old_fn():\n    pass\n",
            "hooks/c.py": "old_fn()\n",
        }
        for rel, text in self.files.items():
            (self.repo / rel).parent.mkdir(parents=True, exist_ok=True)
            (self.repo / rel).write_text(text, encoding="utf-8")
        subprocess.run(["git", "-C", str(self.repo), "add", "-A"], check=True, env=GIT_ENV)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def render(self, diff: str) -> str:
        return self.mod.render(self.mod.extract_symbols(diff), self.repo)


class ExtractSymbolsTests(CandidatesTestBase):
    def test_empty_diff_has_no_symbols_and_says_so(self) -> None:
        self.assertEqual(self.mod.extract_symbols(""), [])
        self.assertIn("候補なし", self.render(""))

    def test_function_and_constant_on_changed_lines(self) -> None:
        diff = diff_of("lib/guard.py", "@@ -1,4 +1,4 @@\n-def parse_x(s):\n+def parse_x(s, t=None):\n     return s\n-LIMIT_MAX = 3\n+LIMIT_MAX = 4\n")
        self.assertEqual(self.mod.extract_symbols(diff), ["LIMIT_MAX", "parse_x"])

    def test_enclosing_function_in_hunk_header(self) -> None:
        diff = diff_of("lib/guard.py", "@@ -1,2 +1,2 @@ def parse_x(s):\n-    return s\n+    return s.strip()\n")
        self.assertEqual(self.mod.extract_symbols(diff), ["parse_x"])

    def test_shell_function(self) -> None:
        diff = diff_of("hooks/b.sh", "@@ -1,3 +1,3 @@\n-check_it() {\n+check_it() {  # x\n")
        self.assertEqual(self.mod.extract_symbols(diff), ["check_it"])

    def test_deletion_only_diff_keeps_the_removed_symbol(self) -> None:
        diff = diff_of("lib/old.py", "@@ -1,2 +0,0 @@\n-def old_fn():\n-    pass\n", header="deleted file mode 100644\n")
        self.assertEqual(self.mod.extract_symbols(diff), ["old_fn"])
        self.assertIn("hooks/c.py:1", self.render(diff))

    def test_rename_lists_both_old_and_new_names(self) -> None:
        diff = (
            "diff --git a/lib/old.py b/lib/new.py\nsimilarity index 80%\n"
            "rename from lib/old.py\nrename to lib/new.py\n"
            "--- a/lib/old.py\n+++ b/lib/new.py\n"
            "@@ -1,2 +1,2 @@\n-def old_fn():\n+def new_fn():\n     pass\n"
        )
        self.assertEqual(self.mod.extract_symbols(diff), ["new_fn", "old_fn"])

    def test_pure_rename_without_content_change_has_no_symbols(self) -> None:
        diff = "diff --git a/lib/old.py b/lib/new.py\nsimilarity index 100%\nrename from lib/old.py\nrename to lib/new.py\n"
        self.assertEqual(self.mod.extract_symbols(diff), [])

    def test_markdown_files_are_not_scanned(self) -> None:
        diff = diff_of("docs/note.md", "@@ -1 +1 @@\n-def parse_x():\n+LIMIT_MAX = 1\n")
        self.assertEqual(self.mod.extract_symbols(diff), [])

    def test_file_header_lines_are_not_changed_lines(self) -> None:
        diff = diff_of("lib/guard.py", "@@ -1 +1 @@\n-x = 1\n+x = 2\n").replace(
            "--- a/lib/guard.py", "--- a/LIMIT_MAX = 1"
        )
        self.assertEqual(self.mod.extract_symbols(diff), [])

    def test_quoted_markdown_path_after_code_file_is_not_scanned(self) -> None:
        # 空白や非 ASCII を含むパスは git が引用符で囲む。前のファイルの状態を引き継がない
        diff = diff_of("lib/guard.py", "@@ -1 +1 @@\n-def parse_x(s):\n+def parse_x(s, t=None):\n") + (
            'diff --git "a/docs/\\346\\227\\245 x.md" "b/docs/\\346\\227\\245 x.md"\n'
            '--- "a/docs/\\346\\227\\245 x.md"\n+++ "b/docs/\\346\\227\\245 x.md"\n'
            "@@ -1 +1 @@\n-x\n+def only_in_markdown():\n"
        )
        self.assertEqual(self.mod.extract_symbols(diff), ["parse_x"])


class RenderTests(CandidatesTestBase):
    DIFF = diff_of("lib/guard.py", "@@ -1,4 +1,4 @@\n-def parse_x(s):\n+def parse_x(s, t=None):\n")

    def test_same_diff_gives_same_output(self) -> None:
        self.assertEqual(self.render(self.DIFF), self.render(self.DIFF))

    def test_lists_file_and_line_and_excludes_review_log(self) -> None:
        out = self.render(self.DIFF)
        self.assertIn("`parse_x`", out)
        self.assertIn("hooks/a.py:1", out)
        self.assertIn("hooks/a.py:3", out)
        self.assertIn("docs/note.md:1", out)
        self.assertNotIn("review-log/", out)

    def test_references_are_ordered_by_path_then_line_number(self) -> None:
        (self.repo / "many.py").write_text("x\n" * 9 + "parse_x()\n" + "x\n" * 90 + "parse_x()\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(self.repo), "add", "-A"], check=True, env=GIT_ENV)
        out = self.render(self.DIFF)
        self.assertLess(out.index("many.py:10"), out.index("many.py:101"))
        self.assertLess(out.index("hooks/a.py:3"), out.index("many.py:10"))

    def test_references_are_capped_deterministically(self) -> None:
        (self.repo / "many.py").write_text("".join("parse_x()\n" for _ in range(80)), encoding="utf-8")
        subprocess.run(["git", "-C", str(self.repo), "add", "-A"], check=True, env=GIT_ENV)
        out = self.render(self.DIFF)
        self.assertIn("ほか", out)
        self.assertEqual(out, self.render(self.DIFF))

    def test_path_with_colon_is_listed(self) -> None:
        (self.repo / "a:b.py").write_text("parse_x()\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(self.repo), "add", "-A"], check=True, env=GIT_ENV)
        self.assertIn("a:b.py:1", self.render(self.DIFF))

    def test_path_with_newline_does_not_abort_the_listing(self) -> None:
        # git grep -z は改行を含むパスを引用せずに出す。レコードを \n で割ると 1 件が割れて一覧ごと落ちる
        (self.repo / "we\nird.py").write_text("parse_x()\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(self.repo), "add", "-A"], check=True, env=GIT_ENV)
        out = self.render(self.DIFF)
        self.assertIn("we\nird.py:1", out)
        self.assertIn("hooks/a.py:1", out)

    def test_color_config_does_not_change_the_listing(self) -> None:
        # 呼び出し元の git config（color.grep=always など）で、パスや行番号に色の制御文字が混ざらない
        subprocess.run(["git", "-C", str(self.repo), "config", "color.grep", "always"], check=True, env=GIT_ENV)
        out = self.render(self.DIFF)
        self.assertIn("hooks/a.py:1", out)
        self.assertNotIn("\x1b", out)

    def test_line_with_other_line_breaks_does_not_break_the_listing(self) -> None:
        # git grep -z のレコードは \n で終わる。本文の U+2028・\x0c・単独の \r で割らない
        for sep in ("\u2028", "\x0c", "\r"):
            with self.subTest(sep=repr(sep)):
                with open(self.repo / "sep.py", "w", encoding="utf-8", newline="") as f:
                    f.write(f"parse_x('a{sep}b')\n")
                subprocess.run(["git", "-C", str(self.repo), "add", "-A"], check=True, env=GIT_ENV)
                self.assertIn("sep.py:1", self.render(self.DIFF))

    def test_too_many_references_show_only_the_count(self) -> None:
        # docs や CHANGELOG の一致で埋まる一般名は、起点にならないので一覧を出さない
        (self.repo / "many.py").write_text("".join("parse_x()\n" for _ in range(150)), encoding="utf-8")
        subprocess.run(["git", "-C", str(self.repo), "add", "-A"], check=True, env=GIT_ENV)
        out = self.render(self.DIFF)
        self.assertIn("`parse_x`（154 件", out)
        self.assertNotIn("many.py:1", out)
        self.assertNotIn("hooks/a.py:1", out)

    def test_cli_reads_diff_from_stdin(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPT), str(self.repo)],
            input=self.DIFF, capture_output=True, text=True, check=False, env=GIT_ENV,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, self.render(self.DIFF))

    def test_cli_fails_when_repo_is_not_a_git_checkout(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run(
                [sys.executable, str(SCRIPT), tmp],
                input=self.DIFF, capture_output=True, text=True, check=False, env=GIT_ENV,
            )
        self.assertNotEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
