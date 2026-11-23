"""`next_plan_check.has_incomplete_follow_up_stages` がコードフェンスの中を Lane として読まないこと。

フェンスの中は記入例で、現在値ではない（正本: `lib/tasklist_parse.strip_fenced_blocks`）。
フェンスを考えずに読むと、フェンスの中の `## ` 行で Lane が切れて後ろの `- [ ]` を見落とし、
`### 次の計画` なしの done の停止が通る（fail-open）。
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))

import _stop_hook_test_base  # noqa: E402,F401  hooks/scripts を sys.path に入れる
from _timing_budget import hang_guard_seconds  # noqa: E402

STOP_HANG_GUARD = hang_guard_seconds("run-gdd-stop-hook.sh")

from lib.next_plan_check import has_incomplete_follow_up_stages, requirements_lane_pending  # noqa: E402

LANE = "## Planned Follow-up Stage Lane\n\n"


class FencedLaneTests(unittest.TestCase):
    def test_heading_inside_fence_does_not_end_lane(self) -> None:
        text = LANE + "```markdown\n## 例\n```\n\n- [ ] stage-b: Phase B\n"
        self.assertTrue(has_incomplete_follow_up_stages(text))

    def test_lane_example_inside_fence_is_not_the_lane(self) -> None:
        text = (
            "# Requirements\n\n```markdown\n" + LANE + "- [x] stage-a: 例\n```\n\n"
            + LANE + "- [ ] stage-b: Phase B\n"
        )
        self.assertTrue(has_incomplete_follow_up_stages(text))

    def test_unchecked_item_only_inside_fence_is_not_pending(self) -> None:
        text = LANE + "```markdown\n- [ ] stage-b: 記入例\n```\n\n- [x] stage-a: 済み\n"
        self.assertFalse(has_incomplete_follow_up_stages(text))

    def test_unclosed_fence_keeps_text_after_it(self) -> None:
        text = LANE + "```\n- [ ] stage-b: Phase B\n"
        self.assertTrue(has_incomplete_follow_up_stages(text))

    def test_h1_heading_ends_lane(self) -> None:
        text = LANE + "- [x] stage-a: 済み\n\n# 付録\n\n- [ ] 別のチェックリスト\n"
        self.assertFalse(has_incomplete_follow_up_stages(text))

    def test_subsection_does_not_end_lane(self) -> None:
        text = LANE + "### S-2\n\n- [ ] stage-b: Phase B\n"
        self.assertTrue(has_incomplete_follow_up_stages(text))

    def test_empty_and_fully_fenced_input_are_not_pending(self) -> None:
        self.assertFalse(has_incomplete_follow_up_stages(""))
        self.assertFalse(has_incomplete_follow_up_stages("```\n" + LANE + "- [ ] x\n```\n"))


class LineBreakAndHeadingTests(unittest.TestCase):
    """LF 以外の行区切り文字と、見出しにならない `#` の行で Lane を終えない。"""

    def test_non_newline_breaks_do_not_split_lines(self) -> None:
        for ch in ("\u2028", "\x85", "\x0c"):
            with self.subTest(ch=repr(ch)):
                text = LANE + f"- [x] S-1{ch}## メモ\n- [ ] S-2\n"
                self.assertTrue(has_incomplete_follow_up_stages(text))
                text = LANE + f"- [x] S-1{ch}```\n- [ ] S-2\n```\n"
                self.assertTrue(has_incomplete_follow_up_stages(text))

    def test_hash_followed_by_unicode_space_is_not_a_heading(self) -> None:
        for head in ("#\u3000注記", "##\u3000注記", "#\u00a0注記"):
            with self.subTest(head=head):
                text = LANE + f"- [x] S-1\n{head}\n- [ ] S-2\n"
                self.assertTrue(has_incomplete_follow_up_stages(text))

    def test_bare_hash_line_ends_lane(self) -> None:
        text = LANE + "- [x] S-1\n#\n- [ ] 別\n"
        self.assertFalse(has_incomplete_follow_up_stages(text))

    def test_lane_with_only_fenced_body_ends_at_next_heading(self) -> None:
        text = LANE + "```\n- [x] S-1\n```\n## 付録\n- [ ] 別\n"
        self.assertFalse(has_incomplete_follow_up_stages(text))


class TableLaneTests(unittest.TestCase):
    """requirements-template.md の書式（表）で書いた Lane の行を、未完の Stage として数える。"""

    HEADER = "| Pending Stage ID | Origin Steering | Next Planned Stage |\n|---|---|---|\n"

    def test_table_row_is_pending(self) -> None:
        text = LANE + self.HEADER + "| S-2 | .steering/x | 次の Stage |\n"
        self.assertTrue(has_incomplete_follow_up_stages(text))

    def test_header_only_table_is_pending(self) -> None:
        self.assertTrue(has_incomplete_follow_up_stages(LANE + self.HEADER))

    def test_item_above_delimiter_is_pending(self) -> None:
        for body in ("- [ ] S-2 | x\n|---|\n", "### S-2 | x\n|---|\n", "S-2 | x\n|---|\n"):
            with self.subTest(body=body):
                self.assertTrue(has_incomplete_follow_up_stages(LANE + body))

    def test_row_with_empty_first_cell_is_pending(self) -> None:
        text = LANE + self.HEADER + "|  | .steering/x | 次の Stage |\n"
        self.assertTrue(has_incomplete_follow_up_stages(text))

    def test_table_inside_fence_is_not_pending(self) -> None:
        text = LANE + "```\n" + self.HEADER + "| S-2 | a | b |\n```\n"
        self.assertFalse(has_incomplete_follow_up_stages(text))

    def test_table_after_lane_is_not_pending(self) -> None:
        text = LANE + "- [x] S-1\n\n## 付録\n\n" + self.HEADER + "| S-2 | a | b |\n"
        self.assertFalse(has_incomplete_follow_up_stages(text))

    def test_broken_rows_are_pending(self) -> None:
        for body in ("|\n", "||\n|\n", "| S-2\n", "|---|\n| S-2 |\n"):
            with self.subTest(body=body):
                self.assertTrue(has_incomplete_follow_up_stages(LANE + body))

    def test_table_without_outer_pipes_is_pending(self) -> None:
        text = LANE + "Pending Stage ID | Next\n--- | ---\nS-2 | 次の Stage\n"
        self.assertTrue(has_incomplete_follow_up_stages(text))

    def test_single_row_table_without_header_is_pending(self) -> None:
        self.assertTrue(has_incomplete_follow_up_stages(LANE + "| S-2 | 次の Stage |\n"))


class ClosedByDefaultTests(unittest.TestCase):
    """Lane の中は、`- [x]` の項目と空行だけなら完了。ほかの行（見出し・表の行を含む）は未完。"""

    def test_other_list_markers_are_pending(self) -> None:
        for item in ("* [ ] S-2", "+ [ ] S-2", "1. [ ] S-2", "1) [ ] S-2"):
            with self.subTest(item=item):
                self.assertTrue(has_incomplete_follow_up_stages(LANE + item + "\n"))

    def test_prose_and_nested_items_are_pending(self) -> None:
        for body in ("- [x] S-1\n  - 補足\n", "- [x] S-1\n**Continuation Mode**: manual\n"):
            with self.subTest(body=body):
                self.assertTrue(has_incomplete_follow_up_stages(LANE + body))

    def test_checked_items_and_blank_lines_are_complete(self) -> None:
        text = LANE + "- [x] S-1\n\n- [X] S-2\n  - [x] S-3\n\n"
        self.assertFalse(has_incomplete_follow_up_stages(text))

    def test_subheadings_are_pending(self) -> None:
        for body in ("### S-3: post-merge 検証\n", "### S-1\n- [x] S-1\n", "###x\n"):
            with self.subTest(body=body):
                self.assertTrue(has_incomplete_follow_up_stages(LANE + body))

    def test_header_like_row_inside_table_is_pending(self) -> None:
        header = "| Pending Stage ID | Next |\n|---|---|\n"
        for body in (header + "| S-2 | 次 |\n---\n", header + "| S-2 | 次 |\n| - | - |\n", "- [ ] S-2 | x\n---\n"):
            with self.subTest(body=body):
                self.assertTrue(has_incomplete_follow_up_stages(LANE + body))

    def test_delimiter_without_pipe_is_pending(self) -> None:
        for body in ("- [x] S-1\n---\n", "- [ ] S-2\n-\n", "-\n"):
            with self.subTest(body=body):
                self.assertTrue(has_incomplete_follow_up_stages(LANE + body))

    def test_other_checked_markers_are_pending(self) -> None:
        for item in ("* [x] S-2", "+ [x] S-2", "1. [x] S-2"):
            with self.subTest(item=item):
                self.assertTrue(has_incomplete_follow_up_stages(LANE + item + "\n"))

    def test_line_break_without_lane_is_not_pending(self) -> None:
        self.assertFalse(has_incomplete_follow_up_stages("# Requirements\n\n本文\u2028続き\n"))

    def test_item_after_non_newline_break_is_pending(self) -> None:
        for ch in ("\x0b", "\x0c", "\x1c", "\x1d", "\x1e", "\x85", "\u2028", "\u2029"):
            with self.subTest(ch=repr(ch)):
                self.assertTrue(has_incomplete_follow_up_stages(LANE + f"- [x] S-1{ch}- [ ] S-2\n"))
                self.assertTrue(has_incomplete_follow_up_stages(
                    f"前文{ch}## Planned Follow-up Stage Lane\n- [ ] S-2\n"))

    def test_heading_with_trailing_unicode_space_is_read(self) -> None:
        for tail in ("\u3000", "\u00a0"):
            with self.subTest(tail=repr(tail)):
                text = f"## Planned Follow-up Stage Lane{tail}\n\n- [ ] S-2\n"
                self.assertTrue(has_incomplete_follow_up_stages(text))

    def test_every_lane_heading_is_read(self) -> None:
        text = LANE + "- [x] S-1\n\n## 変更履歴\n\n" + LANE + "- [ ] S-3\n"
        self.assertTrue(has_incomplete_follow_up_stages(text))


class RequirementsLanePendingTests(unittest.TestCase):
    """requirements.md が無ければ Lane なし、通常のファイルとして読めなければ未完（止める側）。"""

    def test_missing_path_is_not_pending(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "file").write_text("", encoding="utf-8")
            self.assertFalse(requirements_lane_pending(Path(tmp) / "requirements.md"))
            self.assertFalse(requirements_lane_pending(Path(tmp) / "file" / "requirements.md"))

    def test_unreadable_file_is_pending(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            req = Path(tmp) / "requirements.md"
            req.write_text("# Requirements\n", encoding="utf-8")
            for error in (PermissionError(13, "denied"), OSError(5, "EIO")):
                with self.subTest(error=error), mock.patch.object(os, "open", side_effect=error):
                    self.assertTrue(requirements_lane_pending(req))

    def test_non_regular_paths_are_pending(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            req = Path(tmp) / "requirements.md"
            os.symlink("requirements.md", req)
            for path in (req, Path(tmp), Path(os.devnull)):
                with self.subTest(path=path):
                    self.assertTrue(requirements_lane_pending(path))

    def test_symlink_loop_is_pending_when_resolve_raises(self) -> None:
        """Python 3.12 以前の `Path.resolve()` はループで RuntimeError を投げる。それでも未完に倒す。"""
        with tempfile.TemporaryDirectory() as tmp:
            req = Path(tmp) / "requirements.md"
            os.symlink("requirements.md", req)
            with mock.patch.object(Path, "resolve", side_effect=RuntimeError("Symlink loop")):
                self.assertTrue(requirements_lane_pending(req))

    def test_dangling_symlink_is_pending(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            req = Path(tmp) / "requirements.md"
            os.symlink("missing-target", req)
            self.assertTrue(requirements_lane_pending(req))

    def test_fifo_is_pending_without_blocking(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fifo = Path(tmp) / "requirements.md"
            os.mkfifo(fifo)
            result = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    "import sys; from pathlib import Path; from lib.next_plan_check import requirements_lane_pending\n"
                    "print(requirements_lane_pending(Path(sys.argv[1])))",
                    str(fifo),
                ],
                capture_output=True,
                text=True,
                timeout=STOP_HANG_GUARD,
                cwd=str(Path(__file__).resolve().parents[1] / "hooks" / "scripts"),
            )
            self.assertEqual(result.stdout.strip(), "True")

    def test_readable_file_is_judged_by_its_lane(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            req = Path(tmp) / "requirements.md"
            req.write_text(LANE + "- [x] S-1\n", encoding="utf-8")
            self.assertFalse(requirements_lane_pending(req))
            req.write_bytes((LANE + "- [ ] S-2\n").encode("utf-8") + b"\xff\n")
            self.assertTrue(requirements_lane_pending(req))


if __name__ == "__main__":
    unittest.main()
