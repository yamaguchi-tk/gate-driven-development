"""GDD配線チェック改善 変えること3: `scripts/lint-unused-new-symbols.py` の契約テスト。

diff で新規追加された Python の関数・定数のうち、テスト以外から参照 0 件のものを列挙する
report-only スクリプト。**block しない**（exit code は常に 0）。completion-check から
呼ばれ、レビュー時の判断材料として finding を提示するだけで、gate 判定には使わない。

開いた入力の扱い（本スクリプト自身への適用）: 対象は Python の module-level def/class/定数の
みで、ネストした関数・メソッド・非 Python 言語は対象外（限界として開示する。scope を広げると
静的解析なしでは誤検知が支配的になる）。参照カウントは tokenize の NAME トークン一致による
best-effort であり、再エクスポート経由の呼び出しや `getattr` 経由の動的参照は検出できない。
"""
import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path

from _paths import PLUGIN_ROOT
SCRIPT_PATH = PLUGIN_ROOT / "scripts" / "lint-unused-new-symbols.py"

_spec = importlib.util.spec_from_file_location("lint_unused_new_symbols", SCRIPT_PATH)
lint_unused_new_symbols = importlib.util.module_from_spec(_spec)
sys.modules["lint_unused_new_symbols"] = lint_unused_new_symbols
_spec.loader.exec_module(lint_unused_new_symbols)  # type: ignore[union-attr]


class ParseAddedSymbolsTests(unittest.TestCase):
    def test_detects_added_top_level_function(self) -> None:
        diff = (
            "diff --git a/foo.py b/foo.py\n"
            "+++ b/foo.py\n"
            "@@ -0,0 +1,2 @@\n"
            "+def new_helper():\n"
            "+    return 1\n"
        )
        result = lint_unused_new_symbols.parse_added_symbols(diff)
        self.assertEqual(result, {"foo.py": {"new_helper"}})

    def test_detects_added_class_and_constant(self) -> None:
        diff = (
            "+++ b/bar.py\n"
            "@@ -0,0 +1,2 @@\n"
            "+class NewThing:\n"
            "+    pass\n"
            "+MAX_RETRY = 3\n"
        )
        result = lint_unused_new_symbols.parse_added_symbols(diff)
        self.assertEqual(result, {"bar.py": {"NewThing", "MAX_RETRY"}})

    def test_ignores_non_python_files(self) -> None:
        diff = "+++ b/README.md\n@@ -0,0 +1 @@\n+def not_python():\n"
        result = lint_unused_new_symbols.parse_added_symbols(diff)
        self.assertEqual(result, {})

    def test_ignores_nested_indented_def(self) -> None:
        """限界として開示: ネストした関数・メソッドは対象外（top-level のみ検出）。"""
        diff = "+++ b/baz.py\n@@ -0,0 +1,2 @@\n+class C:\n+    def method(self):\n"
        result = lint_unused_new_symbols.parse_added_symbols(diff)
        self.assertEqual(result, {"baz.py": {"C"}})


class IsTestPathTests(unittest.TestCase):
    def test_tests_directory_is_test_path(self) -> None:
        self.assertTrue(lint_unused_new_symbols.is_test_path("tests/test_foo.py"))

    def test_test_prefixed_file_is_test_path(self) -> None:
        self.assertTrue(lint_unused_new_symbols.is_test_path("scripts/test_bar.py"))

    def test_regular_source_file_is_not_test_path(self) -> None:
        self.assertFalse(lint_unused_new_symbols.is_test_path("scripts/lint-foo.py"))


class CountReferencesTests(unittest.TestCase):
    def _write(self, root: Path, rel_path: str, content: str) -> None:
        p = root / rel_path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")

    def test_zero_references_outside_definition(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(root, "foo.py", "def new_helper():\n    return 1\n")
            self._write(root, "other.py", "x = 1\n")
            count = lint_unused_new_symbols.count_references(root, "new_helper", "foo.py")
            self.assertEqual(count, 0)

    def test_reference_from_non_test_file_counted(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(root, "foo.py", "def new_helper():\n    return 1\n")
            self._write(root, "caller.py", "from foo import new_helper\nnew_helper()\n")
            count = lint_unused_new_symbols.count_references(root, "new_helper", "foo.py")
            self.assertGreaterEqual(count, 1)

    def test_reference_only_from_test_file_not_counted(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(root, "foo.py", "def new_helper():\n    return 1\n")
            self._write(root, "tests/test_foo.py", "from foo import new_helper\nnew_helper()\n")
            count = lint_unused_new_symbols.count_references(root, "new_helper", "foo.py")
            self.assertEqual(count, 0)

    def test_reassignment_reference_in_defining_file_is_counted(self) -> None:
        """独立レビュー medium finding: 受理集合の非対称。

        新設シンボル検出（`_DEF_RE`）はトップレベル（インデント無し）だけを対象にするが、
        定義行除外判定（`is_definition_line`）はインデントを見ていなかったため、
        `new_helper = staticmethod(new_helper)` のような同一ファイル内の再代入参照が
        「定義行」として誤って除外され、実際に参照されているのに 0 件と誤検知していた。
        """
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(
                root,
                "foo.py",
                "def new_helper():\n    return 1\n\n\nnew_helper = staticmethod(new_helper)\n",
            )
            count = lint_unused_new_symbols.count_references(root, "new_helper", "foo.py")
            self.assertGreaterEqual(count, 1)

    def test_string_literal_occurrence_of_symbol_name_is_not_counted_as_reference(self) -> None:
        """PR レビュー指摘 [P2]: コメント・docstring・文字列リテラル内の出現は実参照ではない。

        `API_URL = os.getenv("API_URL")` のような自己参照的な文字列リテラルは、定義行の
        1回の出現を差し引いた後でも、正規表現の単語境界一致では文字列リテラル内の
        "API_URL" をもう1件の実参照として数えてしまい、実際にはどこからも参照されて
        いないシンボルを「参照あり」と誤検知していた。
        """
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(root, "foo.py", 'API_URL = os.getenv("API_URL")\n')
            count = lint_unused_new_symbols.count_references(root, "API_URL", "foo.py")
            self.assertEqual(count, 0)

    def test_comment_occurrence_of_symbol_name_is_not_counted_as_reference(self) -> None:
        """PR レビュー指摘 [P2]: コメント内の出現は実参照ではない。"""
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write(root, "foo.py", "def new_helper():\n    return 1\n")
            self._write(root, "caller.py", "# new_helper is unused\nx = 1\n")
            count = lint_unused_new_symbols.count_references(root, "new_helper", "foo.py")
            self.assertEqual(count, 0)


class CliReportOnlyTests(unittest.TestCase):
    def test_exit_code_is_always_zero_even_with_findings(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.email", "t@example.com"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.name", "t"], cwd=root, check=True)
            (root / "foo.py").write_text("x = 1\n", encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(["git", "commit", "-q", "-m", "base"], cwd=root, check=True)
            (root / "foo.py").write_text("x = 1\n\n\ndef unreferenced_new_fn():\n    return 1\n", encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(["git", "commit", "-q", "-m", "add fn"], cwd=root, check=True)

            proc = subprocess.run(
                [sys.executable, str(SCRIPT_PATH), "--repo-root", str(root), "--base-ref", "HEAD~1", "--format", "json"],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertIn("unreferenced_new_fn", proc.stdout)
            self.assertIn('"report_only": true', proc.stdout)

    def test_nonexistent_repo_root_exits_zero_without_traceback(self) -> None:
        """独立レビュー high finding: `--repo-root` が存在しない/非 git ディレクトリだと
        `subprocess.run(["git", ...])` の `FileNotFoundError` が捕捉されずに伝播し、
        report-only 契約（exit code は常に 0）に反して exit 1 で落ちていた。"""
        proc = subprocess.run(
            [
                sys.executable,
                str(SCRIPT_PATH),
                "--repo-root",
                "/definitely/not/a/real/path/xyz",
                "--base-ref",
                "origin/main",
                "--format",
                "json",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertNotIn("Traceback", proc.stderr)

    def test_nonexistent_repo_root_reports_explicit_error(self) -> None:
        """Snyk Code (python/PT, CWE-23) 指摘への対応: CLI 引数由来の `--repo-root` を
        フィルタ無しで `Path` に渡していた。境界チェック（存在確認 + ディレクトリ確認）を
        `git diff` 実行より前に置くことで、無効な `--repo-root` を早期に弾き、
        「該当なし」への黙殺（fail-open）も防ぐ。"""
        proc = subprocess.run(
            [
                sys.executable,
                str(SCRIPT_PATH),
                "--repo-root",
                "/definitely/not/a/real/path/xyz",
                "--base-ref",
                "origin/main",
                "--format",
                "json",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertIn("error", payload)
        self.assertIn("repo-root", payload["error"])

    def test_git_diff_failure_surfaces_error_not_silent_empty(self) -> None:
        """独立レビュー medium finding: `git diff` が失敗（存在しない base-ref 等）しても
        `check=False` により空文字列の stdout が返り、「新設シンボル無し」と区別できず
        黙って `該当なし` を報告していた（fail-open：スキャン未実施を成功として見せる）。"""
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.email", "t@example.com"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.name", "t"], cwd=root, check=True)
            (root / "foo.py").write_text("x = 1\n", encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(["git", "commit", "-q", "-m", "base"], cwd=root, check=True)

            proc = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--repo-root",
                    str(root),
                    "--base-ref",
                    "this-ref-does-not-exist",
                    "--format",
                    "json",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            payload = json.loads(proc.stdout)
            self.assertIn("error", payload, "git diff 失敗が report-only 出力に反映されていない")


if __name__ == "__main__":
    unittest.main()
