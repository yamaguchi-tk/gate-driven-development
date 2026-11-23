"""軽いレーンの「関係するテスト」（root CLAUDE.md 手順 3）を列挙するスクリプトの契約テスト。

スクリプトは repo root の `scripts/light-lane-related-tests.py`（GDD plugin の配布物の外）。
変えたファイルの名前を参照する GDD のテストと、変えたテストそのものを出す。GDD 以外の plugin か
marketplace.json を変えたら、その plugin（marketplace.json なら GDD 以外の全部）のテストも出す。
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
SCRIPT = REPO_ROOT / "scripts" / "light-lane-related-tests.py"
IN_CANONICAL_REPO = (REPO_ROOT / "plugins" / "gate-driven-development").resolve() == PLUGIN_ROOT.resolve() and (
    REPO_ROOT / "review-log" / "README.md"
).is_file()
GIT_ENV = {**os.environ, "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"}
GDD_TESTS = "plugins/gate-driven-development/tests"
PW_TESTS = "plugins/plain-writing/tests"
JRG_TESTS = "plugins/japanese-reply-guard/tests"


def load():
    spec = importlib.util.spec_from_file_location("light_lane_related_tests", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], check=True, env=GIT_ENV, capture_output=True, text=True).stdout


class RelatedTestsBase(unittest.TestCase):
    def setUp(self) -> None:
        if not IN_CANONICAL_REPO:
            self.skipTest("canonical repo 外では repo root の scripts/ を検査しない")
        self.mod = load()
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self._tmp.name)
        git(self.repo.parent, "init", "-q", "-b", "main", str(self.repo))
        files = {
            "plugins/gate-driven-development/hooks/scripts/lib/errors.py": "X = 1\n",
            "plugins/gate-driven-development/tests/checks/version-not-consumed.sh": "echo\n",
            f"{GDD_TESTS}/test_errors.py": "from lib.errors import X\n",
            f"{GDD_TESTS}/test_version.py": "CHECK = 'version-not-consumed'\n",
            f"{GDD_TESTS}/test_other.py": "pass\n",
            f"{GDD_TESTS}/test_review_log_present.py": "pass\n",
            f"{GDD_TESTS}/_helper.py": "errors = 1\n",
            f"{GDD_TESTS}/checks/test_nested.py": "errors\n",
            f"{PW_TESTS}/test_pw.py": "pass\n",
            f"{JRG_TESTS}/test_jrg.py": "pass\n",
            "plugins/japanese-reply-guard/hooks/reply_hook.py": "x\n",
            f"{GDD_TESTS}/test_ignore.py": "path = '.gitignore'\n",
            ".gitignore": "*.log\n",
            "plugins/gate-driven-development/hooks/scripts/guard-body.py": "x\n",
            f"{GDD_TESTS}/_guard_support.py": "HOOK = 'guard-body.py'\n",
            f"{GDD_TESTS}/test_guard_via_helper.py": "from _guard_support import HOOK\n",
            "plugins/plain-writing/skills/x/SKILL.md": "x\n",
            ".claude-plugin/marketplace.json": "{}\n",
            "README.md": "x\n",
        }
        for rel, text in files.items():
            (self.repo / rel).parent.mkdir(parents=True, exist_ok=True)
            (self.repo / rel).write_text(text, encoding="utf-8")
        git(self.repo, "add", "-A")
        git(self.repo, "-c", "user.name=t", "-c", "user.email=t@example.com", "commit", "-q", "-m", "base")
        git(self.repo, "checkout", "-q", "-b", "topic")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def related(self, *changed: str) -> list[str]:
        return self.mod.related_tests(list(changed), self.repo)


class RelatedTestsTests(RelatedTestsBase):
    def test_tests_that_name_the_changed_file_without_extension(self) -> None:
        self.assertEqual(
            self.related("plugins/gate-driven-development/hooks/scripts/lib/errors.py"),
            [f"{GDD_TESTS}/test_errors.py"],
        )
        self.assertEqual(
            self.related("plugins/gate-driven-development/tests/checks/version-not-consumed.sh"),
            [f"{GDD_TESTS}/test_version.py"],
        )

    def test_changed_test_is_included_and_helpers_are_not(self) -> None:
        self.assertEqual(self.related(f"{GDD_TESTS}/test_other.py"), [f"{GDD_TESTS}/test_other.py"])
        self.assertEqual(self.related(f"{GDD_TESTS}/_helper.py"), [])
        self.assertEqual(self.related(f"{GDD_TESTS}/checks/test_nested.py"), [])

    def test_helper_that_names_the_changed_file_brings_in_tests_that_use_it(self) -> None:
        self.assertEqual(
            self.related("plugins/gate-driven-development/hooks/scripts/guard-body.py"),
            [f"{GDD_TESTS}/test_guard_via_helper.py"],
        )

    def test_dotfile_name_is_looked_up_without_the_leading_dot(self) -> None:
        self.assertEqual(self.related(".gitignore"), [f"{GDD_TESTS}/test_ignore.py"])

    def test_deleted_test_is_not_included(self) -> None:
        self.assertEqual(self.related(f"{GDD_TESTS}/test_gone.py"), [])

    def test_other_plugin_adds_its_tests_and_marketplace_adds_all_other_plugins(self) -> None:
        self.assertEqual(self.related("plugins/plain-writing/skills/x/SKILL.md"), [f"{PW_TESTS}/test_pw.py"])
        self.assertEqual(self.related("plugins/japanese-reply-guard/hooks/reply_hook.py"), [f"{JRG_TESTS}/test_jrg.py"])
        self.assertEqual(
            self.related(".claude-plugin/marketplace.json"), [f"{JRG_TESTS}/test_jrg.py", f"{PW_TESTS}/test_pw.py"]
        )

    def test_unrelated_change_has_no_tests(self) -> None:
        self.assertEqual(self.related("docs/unrelated-name.md"), [])

    def test_review_log_or_changelog_fragment_brings_in_the_record_check(self) -> None:
        # #476: review-log の行の書き損じで main の test_review_log_present が落ちたが、名前の一致では選ばれなかった
        record_check = [f"{GDD_TESTS}/test_review_log_present.py"]
        self.assertEqual(self.related("review-log/20261014-x.md"), record_check)
        self.assertEqual(self.related("review-log/20261014-x.request.md"), record_check)
        self.assertEqual(self.related("plugins/gate-driven-development/changelog.d/20261014-x.md"), record_check)
        self.assertEqual(self.related("plugins/plain-writing/changelog.d/x.md"), [f"{PW_TESTS}/test_pw.py"])


class EntryPointTests(RelatedTestsBase):
    def run_script(self, *args: str, base: str = "main", extra: tuple[str, ...] = ()) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args, str(self.repo), base, *extra],
            capture_output=True, text=True, env=GIT_ENV, check=False,
        )

    def commit(self, message: str) -> None:
        git(self.repo, "-c", "user.name=t", "-c", "user.email=t@example.com", "commit", "-qam", message)

    def commit_all(self, message: str) -> None:
        git(self.repo, "add", "-A")
        self.commit(message)

    def test_committed_staged_unstaged_and_untracked_changes_are_all_counted(self) -> None:
        (self.repo / "plugins/gate-driven-development/hooks/scripts/lib/errors.py").write_text("X = 2\n", encoding="utf-8")
        self.commit("change")
        (self.repo / "plugins/gate-driven-development/tests/checks/version-not-consumed.sh").write_text("echo 2\n", encoding="utf-8")
        (self.repo / GDD_TESTS / "test_other.py").write_text("x = 1\n", encoding="utf-8")
        git(self.repo, "add", f"{GDD_TESTS}/test_other.py")
        (self.repo / GDD_TESTS / "test_new.py").write_text("pass\n", encoding="utf-8")
        result = self.run_script()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            result.stdout.split(),
            [
                f"{GDD_TESTS}/test_errors.py",
                f"{GDD_TESTS}/test_new.py",
                f"{GDD_TESTS}/test_other.py",
                f"{GDD_TESTS}/test_version.py",
            ],
        )

    def test_rename_also_looks_up_the_old_name(self) -> None:
        git(self.repo, "mv", "plugins/gate-driven-development/hooks/scripts/lib/errors.py", "plugins/gate-driven-development/hooks/scripts/lib/errs.py")
        self.commit("rename")
        result = self.run_script()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(f"{GDD_TESTS}/test_errors.py", result.stdout.split())

    def test_no_related_tests_exits_with_its_own_code_and_empty_stdout(self) -> None:
        # 空の出力を pytest に渡すと、引数なしで repo 全体を集めてしまう。終了コードは pytest の 0〜5 と重ねない
        for args in ((), ("--run",)):
            result = self.run_script(*args)
            self.assertEqual(result.returncode, 65, args)
            self.assertEqual(result.stdout, "")
            self.assertIn("関係するテストなし", result.stderr)

    def test_unresolvable_base_exits_with_the_error_code_and_is_not_reported_as_no_tests(self) -> None:
        result = self.run_script(base="no-such-ref")
        self.assertEqual(result.returncode, 64)
        self.assertNotIn("関係するテストなし", result.stderr)
        self.assertIn("no-such-ref", result.stderr)

    def test_run_passes_every_listed_test_to_one_pytest(self) -> None:
        for name in ("test_a.py", "test_b.py"):
            (self.repo / GDD_TESTS / name).write_text("def test_ok():\n    pass\n", encoding="utf-8")
        result = self.run_script("--run")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("2 passed", result.stdout)

    def test_tests_added_after_double_dash_run_even_when_nothing_is_listed(self) -> None:
        (self.repo / "extra_test_dir").mkdir()
        (self.repo / "extra_test_dir" / "test_extra.py").write_text("def test_ok():\n    pass\n", encoding="utf-8")
        git(self.repo, "add", "extra_test_dir")
        self.commit_all("extra")
        result = self.run_script("--run", extra=("--", "extra_test_dir/test_extra.py"))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("1 passed", result.stdout)

    def test_missing_path_after_double_dash_is_an_error_when_nothing_is_listed(self) -> None:
        result = self.run_script("--run", extra=("--", "no/such/test_x.py"))
        self.assertEqual(result.returncode, 64)
        self.assertIn("no/such/test_x.py", result.stderr)
        self.assertNotIn("関係するテストなし", result.stderr)

    def test_option_value_path_is_passed_as_a_test_so_pytest_does_not_collect_the_tree(self) -> None:
        (self.repo / "extra_test_dir").mkdir()
        (self.repo / "extra_test_dir" / "test_extra.py").write_text("def test_ok():\n    pass\n", encoding="utf-8")
        (self.repo / "test_elsewhere.py").write_text("def test_other():\n    pass\n", encoding="utf-8")
        self.commit_all("extra")
        result = self.run_script("--run", extra=("--", "--deselect", "extra_test_dir/test_extra.py::test_ok"))
        # 位置引数が無いと tree 全体を集め、fixture の壊れたテストで収集エラー（2）になる。足したテストだけなら 5（全部 deselect）
        self.assertEqual(result.returncode, 5, result.stdout + result.stderr)
        self.assertIn("1 deselected", result.stdout)

    def test_other_plugin_validate_script_is_named_for_running_by_hand(self) -> None:
        (self.repo / "plugins/aws-investigate/tests").mkdir(parents=True)
        (self.repo / "plugins/aws-investigate/tests/validate-plugin.sh").write_text("true\n", encoding="utf-8")
        (self.repo / "plugins/aws-investigate/agents").mkdir()
        (self.repo / "plugins/aws-investigate/agents/investigator.md").write_text("x\n", encoding="utf-8")
        result = self.run_script()
        self.assertIn("plugins/aws-investigate/tests/validate-plugin.sh", result.stderr)

    def test_options_alone_after_double_dash_do_not_start_pytest_without_tests(self) -> None:
        result = self.run_script("--run", extra=("--", "-x"))
        self.assertEqual(result.returncode, self.mod.EXIT_NO_TESTS)
        self.assertEqual(result.stdout, "")

    def test_double_dash_without_run_is_an_error(self) -> None:
        result = self.run_script(extra=("--", "x"))
        self.assertEqual(result.returncode, self.mod.EXIT_ERROR)

    def test_run_lists_the_selected_tests_on_stderr(self) -> None:
        (self.repo / GDD_TESTS / "test_a.py").write_text("def test_ok():\n    pass\n", encoding="utf-8")
        (self.repo / "extra_test_dir").mkdir()
        (self.repo / "extra_test_dir" / "test_extra.py").write_text("def test_ok():\n    pass\n", encoding="utf-8")
        self.commit_all("extra")
        (self.repo / GDD_TESTS / "test_a.py").write_text("def test_ok():\n    pass\n", encoding="utf-8")
        result = self.run_script("--run", extra=("--", "extra_test_dir/test_extra.py"))
        self.assertIn(f"{GDD_TESTS}/test_a.py", result.stderr)
        self.assertIn("extra_test_dir/test_extra.py", result.stderr)

    def test_review_log_change_alone_lists_the_record_check(self) -> None:
        (self.repo / "review-log").mkdir()
        (self.repo / "review-log" / "20261014-x.md").write_text("x\n", encoding="utf-8")
        result = self.run_script()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.splitlines(), [f"{GDD_TESTS}/test_review_log_present.py"])

    def test_pycache_is_not_a_changed_file(self) -> None:
        cache = self.repo / JRG_TESTS / "__pycache__"
        cache.mkdir()
        (cache / "test_jrg.cpython-312.pyc").write_bytes(b"x")
        result = self.run_script()
        self.assertEqual(result.returncode, self.mod.EXIT_NO_TESTS, result.stdout)

    def test_subdirectory_is_resolved_to_the_top_level(self) -> None:
        (self.repo / GDD_TESTS / "test_a.py").write_text("pass\n", encoding="utf-8")
        result = subprocess.run(
            [sys.executable, str(SCRIPT), str(self.repo / GDD_TESTS), "main"],
            capture_output=True, text=True, env=GIT_ENV, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.split(), [f"{GDD_TESTS}/test_a.py"])

    def test_run_returns_pytest_failure(self) -> None:
        (self.repo / GDD_TESTS / "test_a.py").write_text("def test_ng():\n    assert False\n", encoding="utf-8")
        result = self.run_script("--run")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("1 failed", result.stdout)


if __name__ == "__main__":
    unittest.main()
