"""他の PR の断片の書き換えを、review-log の front matter `amends:` で宣言したときだけ通す（version-not-consumed.sh）。

宣言を読むのは、この branch で足した断片と対になる review-log（merge-base に無いもの）の HEAD の版だけ。
通すのは、宣言した断片の同じパスでの書き換えだけ（`type:` の書き換えも通す）。
"""
from __future__ import annotations

import re
import tempfile
import unittest
from pathlib import Path

from test_changelog_fragments import commit_all, fragment, git, init_repo, run_check, write

OLD = "20260911-old.md"
NEW = "20260912-new.md"


class AmendsDeclarationTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self._tmp.name)
        self.plugin = init_repo(self.repo)
        self.fragments = self.plugin / "changelog.d"
        write(self.fragments / OLD, fragment("patch", summary="- 元の要約"))
        write(self.fragments / "20260911-other.md", fragment("patch", summary="- 別の PR の要約"))
        write(self.repo / "review-log" / "20260911-other.md", "---\nlane: L1\npr: 2\n---\n")
        commit_all(self.repo, "merged PRs")
        self.assertEqual(git(self.repo, "switch", "-q", "-c", "feat", "main").returncode, 0)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _own(self, frontmatter: str = f"amends: {OLD}\n", *, commit: bool = True) -> None:
        write(self.fragments / NEW, fragment("patch", summary="- 追加の要約"))
        write(self.repo / "review-log" / NEW, f"---\nlane: L1\npr:\n{frontmatter}---\n")
        if commit:
            commit_all(self.repo, "own fragment and review-log")

    def _rewrite(self, name: str = OLD, kind: str = "patch") -> None:
        write(self.fragments / name, fragment(kind, summary="- 書き換えた要約"))

    def _assert_fails(self, *needles: str) -> None:
        result = run_check(self.plugin)
        self.assertEqual(result.returncode, 1, result.stdout)
        # 検査は例外を `unexpected exception during check` の FAIL にするので、traceback の有無では例外を見分けない
        self.assertNotIn("unexpected exception", result.stdout)
        self.assertNotIn("Traceback", result.stdout + result.stderr)
        for needle in needles:
            self.assertIn(needle, result.stdout)

    def test_declared_rewrite_passes(self) -> None:
        self._rewrite()
        self._own()
        result = run_check(self.plugin)
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("1 fragment(s) added", result.stdout)

    def test_several_declared_rewrites_pass(self) -> None:
        self._rewrite()
        self._rewrite("20260911-other.md")
        self._own(f"amends: {OLD}, 20260911-other.md\n")
        self.assertEqual(run_check(self.plugin).returncode, 0)

    def test_declared_rewrite_may_change_the_type_in_either_direction(self) -> None:
        git(self.repo, "switch", "-q", "main")
        write(self.fragments / "20260911-minor.md", fragment("minor", summary="- minor の要約"))
        commit_all(self.repo, "minor fragment merged")
        git(self.repo, "switch", "-q", "-C", "feat", "main")
        self._rewrite(kind="minor")
        self._rewrite("20260911-minor.md", kind="patch")
        self._own(f"amends: {OLD}, 20260911-minor.md\n")
        result = run_check(self.plugin)
        self.assertEqual(result.returncode, 0, result.stdout)

    # --- block すべき入力が allow にならない ---

    def test_rewrite_without_declaration_fails_and_names_the_key(self) -> None:
        self._rewrite()
        self._own("follow_up_of: 1\n")
        self._assert_fails(OLD, "amends:")

    def test_declaring_one_and_rewriting_another_fails(self) -> None:
        self._rewrite("20260911-other.md")
        self._own()
        self._assert_fails("20260911-other.md")

    def test_deleting_a_declared_fragment_fails(self) -> None:
        (self.fragments / OLD).unlink()
        self._own()
        self._assert_fails(OLD)

    def test_renaming_and_rewriting_a_declared_fragment_fails(self) -> None:
        (self.fragments / OLD).unlink()
        write(self.fragments / "20260911-renamed.md", fragment("patch", summary="- 書き換えた要約"))
        self._own()
        self._assert_fails(OLD)

    def test_changing_the_type_without_declaration_fails(self) -> None:
        self._rewrite(kind="minor")
        self._own("follow_up_of: 1\n")
        self._assert_fails(OLD, "amends:")

    def test_declared_rewrite_without_a_type_line_fails(self) -> None:
        write(self.fragments / OLD, fragment("patch", summary="- 書き換えた要約").replace("type: patch\n", ""))
        self._own()
        self._assert_fails(OLD)

    def test_declaration_in_a_review_log_present_at_the_merge_base_is_not_read(self) -> None:
        # 既にある review-log（他の PR の記録）に amends: を足しても、宣言にならない
        git(self.repo, "switch", "-q", "main")
        write(self.repo / "review-log" / NEW, "---\nlane: L1\npr: 3\n---\n")
        commit_all(self.repo, "review-log merged earlier")
        git(self.repo, "switch", "-q", "-C", "feat", "main")
        self._rewrite()
        self._own()
        self._assert_fails(OLD)

    def test_declaration_in_a_review_log_without_an_added_fragment_is_not_read(self) -> None:
        self._rewrite()
        write(self.fragments / NEW, fragment("patch", summary="- 追加の要約"))
        write(self.repo / "review-log" / "20260912-unpaired.md", f"---\nlane: L1\npr:\namends: {OLD}\n---\n")
        commit_all(self.repo, "declaration in an unpaired review-log")
        self._assert_fails(OLD)

    def test_declaration_only_in_the_working_tree_is_not_read(self) -> None:
        self._rewrite()
        self._own("lane2: x\n")
        write(self.repo / "review-log" / NEW, f"---\nlane: L1\npr:\namends: {OLD}\n---\n")
        self._assert_fails(OLD)

    # --- 判定できない宣言は止める ---

    def test_unreadable_declarations_fail(self) -> None:
        # 書き換えを置かずに宣言だけを置く（書き換えの FAIL の文で needle が満たされないようにする）
        not_a_fragment = "which is not the file name of a fragment"
        cases = {
            "空": ("amends:\n", not_a_fragment),
            "パスを含む": (f"amends: changelog.d/{OLD}\n", not_a_fragment),
            "名前の形でない": ("amends: old.md\n", not_a_fragment),
            "merge-base に無い": ("amends: 20260911-missing.md\n", not_a_fragment),
            "2 行": (f"amends: {OLD}\namends: {OLD}\n", "is declared 2 times"),
        }
        for name, (frontmatter, needle) in cases.items():
            with self.subTest(name):
                git(self.repo, "reset", "-q", "--hard", "main")
                self._own(frontmatter)
                self._assert_fails(needle)

    def test_broken_review_logs_fail_without_a_traceback(self) -> None:
        cases = {
            "front matter が閉じていない": (f"---\nlane: L1\namends: {OLD}\n".encode(), "cannot read the frontmatter"),
            "UTF-8 でない": (b"---\nlane: L1\namends: \xff\xfe\n---\n", "which is not the file name of a fragment"),
        }
        for name, (raw, needle) in cases.items():
            with self.subTest(name):
                git(self.repo, "reset", "-q", "--hard", "main")
                write(self.fragments / NEW, fragment("patch", summary="- 追加の要約"))
                (self.repo / "review-log").mkdir(exist_ok=True)
                (self.repo / "review-log" / NEW).write_bytes(raw)
                commit_all(self.repo, "broken review-log")
                self._assert_fails(needle)


class FrontmatterShapeContractTest(unittest.TestCase):
    """version-not-consumed.sh が review-log の front matter を読む形は、review-log-present.sh と同じ（クラス A）。"""

    def test_both_checks_use_the_same_frontmatter_pattern(self) -> None:
        checks = Path(__file__).resolve().parent / "checks"
        found = {name: re.findall(r"^\s*FRONTMATTER_RE = (.*)$", (checks / name).read_text(encoding="utf-8"), re.M)
                 for name in ("version-not-consumed.sh", "review-log-present.sh")}
        self.assertEqual([len(v) for v in found.values()], [1, 1], found)
        self.assertEqual(*found.values())


if __name__ == "__main__":
    unittest.main()
