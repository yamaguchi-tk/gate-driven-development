"""`tasklist_parse.completed_tasks_reviewed_by` のテスト（completion-check Step 2a の機械検算）。

実行: `python3 -m pytest plugins/gate-driven-development/tests/test_completed_tasks_reviewed_by.py -q`

見るのは「`## Completed Tasks` の各タスクのブロックに `Reviewed by:` 行があり、
`gdd-implementation-reviewer` を含む」だけ。reviewer の judgment は自由文なので見ない。
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _plugin_module_loader import load_plugin_module  # noqa: E402

_mod = load_plugin_module("hooks/scripts/lib/tasklist_parse.py")
check = _mod.completed_tasks_reviewed_by
regressions = _mod.reviewed_by_regressions

OK = """# Tasklist

Next Action: done

## Current Task

- なし

## Completed Tasks

### Task 1: 一つ目

- Commit: abc1234
- Reviewed by: gdd-implementation-reviewer, gdd-security-reviewer

### Task 2: 二つ目

#### Steps

- 手順

**Reviewed by**: gdd-implementation-reviewer（approved）

## Verification
"""


class CompletedTasksReviewedByTests(unittest.TestCase):
    def test_all_present(self):
        self.assertEqual(check(OK), ([("一つ目", "ok"), ("二つ目", "ok")], False))

    def test_line_removed_is_detected(self):
        text = OK.replace("- Reviewed by: gdd-implementation-reviewer, gdd-security-reviewer\n", "")
        self.assertEqual(check(text), ([("一つ目", "missing"), ("二つ目", "ok")], False))

    def test_without_implementation_reviewer_is_detected(self):
        text = OK.replace("gdd-implementation-reviewer（approved）", "gdd-security-reviewer")
        self.assertEqual(check(text), ([("一つ目", "ok"), ("二つ目", "no-implementation-reviewer")], False))

    def test_line_only_inside_fence_is_missing(self):
        text = OK.replace(
            "**Reviewed by**: gdd-implementation-reviewer（approved）",
            "```\nReviewed by: gdd-implementation-reviewer\n```",
        )
        self.assertEqual(check(text), ([("一つ目", "ok"), ("二つ目", "missing")], False))

    def test_line_in_next_section_does_not_count(self):
        # Verification 節（次の `## `）にある行は、直前のタスクのものとして数えない
        text = OK.replace("**Reviewed by**: gdd-implementation-reviewer（approved）\n", "")
        text = text.replace("## Verification\n", "## Verification\n\nReviewed by: gdd-implementation-reviewer\n")
        self.assertEqual(check(text), ([("一つ目", "ok"), ("二つ目", "missing")], False))

    def test_line_of_previous_task_does_not_cover_next(self):
        text = OK.replace("**Reviewed by**: gdd-implementation-reviewer（approved）\n", "")
        self.assertEqual(check(text), ([("一つ目", "ok"), ("二つ目", "missing")], False))

    def test_decorations_are_accepted(self):
        for line in (
            "Reviewed by: gdd-implementation-reviewer",
            "- **Reviewed by: gdd-implementation-reviewer**",
            "* Reviewed by: `gdd-implementation-reviewer` (`approved`)",
            "  - Reviewed by: gdd-implementation-reviewer=approved",
        ):
            with self.subTest(line=line):
                text = OK.replace("**Reviewed by**: gdd-implementation-reviewer（approved）", line)
                self.assertEqual(check(text), ([("一つ目", "ok"), ("二つ目", "ok")], False))

    def test_list_item_tasks(self):
        text = (
            "## Completed Tasks\n\n"
            "- T1 | AC-1 | 一つ目\n  - Reviewed by: gdd-implementation-reviewer\n"
            "- T2 | AC-2 | 二つ目\n"
        )
        self.assertEqual(check(text), ([("T1 | AC-1 | 一つ目", "ok"), ("T2 | AC-2 | 二つ目", "missing")], False))

    def test_no_completed_section(self):
        self.assertEqual(check("## Current Task\n\n- なし\n"), ([], False))

    def test_heading_with_suffix_is_the_section(self):
        # done guard と同じく見出しは前方一致で読む
        text = OK.replace("## Completed Tasks", "## Completed Tasks（2 件）")
        self.assertEqual(check(text), ([("一つ目", "ok"), ("二つ目", "ok")], False))

    def test_indented_task_like_line_does_not_start_a_task(self):
        # 行頭にない task 行は構造として読まない（done guard と同じ）。後ろの Reviewed by は前のタスクのもの
        text = OK.replace("- Commit: abc1234\n", "- Commit: abc1234\n  - T3 | AC-1 | 本文の中の例\n    ### Task 9: 例\n")
        self.assertEqual(check(text), ([("一つ目", "ok"), ("二つ目", "ok")], False))

    def test_unclosed_fence_is_reported(self):
        text = OK.replace("#### Steps", "```\n#### Steps")
        self.assertTrue(check(text)[1])


class ReviewedByRegressionsTests(unittest.TestCase):
    """書き込みの前と後で、完了タスクの Reviewed by が ok でなくなったもの（steering write guard が止める）。"""

    def test_unchanged_is_empty(self):
        self.assertEqual(regressions(OK, OK), [])

    def test_line_removed(self):
        after = OK.replace("- Reviewed by: gdd-implementation-reviewer, gdd-security-reviewer\n", "")
        self.assertEqual(regressions(OK, after), [("一つ目", "missing")])

    def test_implementation_reviewer_removed(self):
        after = OK.replace("gdd-implementation-reviewer（approved）", "gdd-security-reviewer")
        self.assertEqual(regressions(OK, after), [("二つ目", "no-implementation-reviewer")])

    def test_block_removed(self):
        after = OK.replace("### Task 1: 一つ目\n\n- Commit: abc1234\n- Reviewed by: gdd-implementation-reviewer, gdd-security-reviewer\n\n", "")
        self.assertEqual(regressions(OK, after), [("一つ目", "removed")])

    def test_heading_summarized_away(self):
        # 要約で見出しの形が崩れ、タスクとして読めなくなる（Reviewed by は前のタスクに入る）
        after = OK.replace("### Task 2: 二つ目", "二つ目は完了")
        self.assertEqual(regressions(OK, after), [("二つ目", "removed")])

    def test_reopen_to_current_section_is_allowed(self):
        block = "### Task 1: 一つ目\n\n- Commit: abc1234\n- Reviewed by: gdd-implementation-reviewer, gdd-security-reviewer\n\n"
        after = OK.replace(block, "").replace("## Current Task\n\n- なし\n", "## Current Task\n\n### Task 1: 一つ目\n\n- 再オープン\n")
        self.assertEqual(regressions(OK, after), [])

    def test_duplicate_line_merged_is_allowed(self):
        before = OK.replace("- Commit: abc1234\n", "- Commit: abc1234\n- Reviewed by: gdd-implementation-reviewer\n")
        self.assertEqual(regressions(before, OK), [])

    def test_task_already_missing_is_not_reported(self):
        before = OK.replace("- Reviewed by: gdd-implementation-reviewer, gdd-security-reviewer\n", "")
        after = before.replace("- Commit: abc1234", "- Commit: def5678")
        self.assertEqual(regressions(before, after), [])

    def test_moving_current_task_into_completed_is_allowed(self):
        before = OK.replace("## Current Task\n\n- なし\n", "## Current Task\n\n### Task 3: 三つ目\n\n- 作業中\n")
        after = OK.replace("## Verification", "### Task 3: 三つ目\n\n- Reviewed by: gdd-implementation-reviewer\n\n## Verification")
        self.assertEqual(regressions(before, after), [])

    def test_unclosed_fence_hiding_completed_tasks_is_reported(self):
        after = OK.replace("## Completed Tasks", "```\n## Completed Tasks")
        self.assertEqual(regressions(OK, after), [("一つ目", "removed"), ("二つ目", "removed")])

    def test_moving_to_a_section_other_than_current_or_pending_is_reported(self):
        # 再オープンの移し先は、done guard が残りのタスクとして数える Current と Pending だけ
        block = "### Task 1: 一つ目\n\n- Commit: abc1234\n- Reviewed by: gdd-implementation-reviewer, gdd-security-reviewer\n\n"
        after = OK.replace(block, "") + "\n## Archived Tasks\n\n" + block
        self.assertEqual(regressions(OK, after), [("一つ目", "removed")])

    def test_renamed_completed_heading_is_reported(self):
        after = OK.replace("## Completed Tasks", "## 完了タスク")
        self.assertEqual(regressions(OK, after), [("一つ目", "removed"), ("二つ目", "removed")])

    def test_reopen_to_pending_section_is_allowed(self):
        block = "### Task 1: 一つ目\n\n- Commit: abc1234\n- Reviewed by: gdd-implementation-reviewer, gdd-security-reviewer\n\n"
        after = OK.replace(block, "").replace("## Completed Tasks", "## Pending Tasks（再オープン）\n\n### Task 1: 一つ目\n\n## Completed Tasks")
        self.assertEqual(regressions(OK, after), [])

    def test_one_of_two_tasks_with_the_same_name_losing_reviewed_by_is_reported(self):
        # task_name は番号を落とすので、同名の 2 件を名前の集合で比べると片方の欠落を見落とす
        before = OK.replace("二つ目", "一つ目")
        after = before.replace("- Reviewed by: gdd-implementation-reviewer, gdd-security-reviewer\n", "")
        self.assertEqual(regressions(before, after), [("一つ目", "missing")])

    def test_one_of_two_tasks_with_the_same_name_removed_is_reported(self):
        before = OK.replace("二つ目", "一つ目")
        block = "### Task 1: 一つ目\n\n- Commit: abc1234\n- Reviewed by: gdd-implementation-reviewer, gdd-security-reviewer\n\n"
        self.assertEqual(regressions(before, before.replace(block, "")), [("一つ目", "removed")])

    def test_deleting_after_adding_to_pending_in_an_earlier_write_is_allowed(self):
        block = "### Task 1: 一つ目\n\n- Commit: abc1234\n- Reviewed by: gdd-implementation-reviewer, gdd-security-reviewer\n\n"
        before = OK.replace("## Completed Tasks", "## Pending Tasks\n\n### Task 1: 一つ目\n\n## Completed Tasks")
        self.assertEqual(regressions(before, before.replace(block, "")), [])

    def test_one_of_two_tasks_with_the_same_name_reopened_is_allowed(self):
        before = OK.replace("二つ目", "一つ目")
        block = "### Task 1: 一つ目\n\n- Commit: abc1234\n- Reviewed by: gdd-implementation-reviewer, gdd-security-reviewer\n\n"
        after = before.replace(block, "").replace("## Current Task\n\n- なし\n", "## Current Task\n\n### Task 1: 一つ目\n")
        self.assertEqual(regressions(before, after), [])


    def test_losing_reviewed_by_with_a_same_name_open_task_is_reported(self):
        # 前から Current にある同名のタスクは、Completed に残ったまま Reviewed by を落とした分を差し引かない
        before = OK.replace("## Current Task\n\n- なし\n", "## Current Task\n\n### Task 1: 一つ目\n")
        after = before.replace("- Reviewed by: gdd-implementation-reviewer, gdd-security-reviewer\n", "")
        self.assertEqual(regressions(before, after), [("一つ目", "missing")])

    def test_dropping_reviewed_by_after_an_unclosed_fence_already_there_is_reported(self):
        # 書き込みの前から閉じていない fence があっても、その先の完了タスクを守る
        before = OK.replace("## Current Task\n\n- なし\n", "## Current Task\n\n- なし\n\n```\n")
        after = before.replace("- Reviewed by: gdd-implementation-reviewer, gdd-security-reviewer\n", "")
        self.assertEqual(regressions(before, after), [("一つ目", "missing")])

    def test_unrelated_write_with_an_unclosed_fence_already_there_is_allowed(self):
        before = OK.replace("## Current Task\n\n- なし\n", "## Current Task\n\n- なし\n\n```\n")
        self.assertEqual(regressions(before, before.replace("- Commit: abc1234", "- Commit: def5678")), [])

    def test_closing_an_unclosed_fence_is_allowed(self):
        before = OK.replace("## Current Task\n\n- なし\n", "## Current Task\n\n- なし\n\n```\n")
        after = OK.replace("## Current Task\n\n- なし\n", "## Current Task\n\n- なし\n\n```\n```\n")
        self.assertEqual(regressions(before, after), [])

    def test_dropping_reviewed_by_after_two_unclosed_fences_is_reported(self):
        # 閉じていない fence を除いた後に、次の閉じていない fence が現れる形（info 付きの行は閉じ fence にならない）
        before = OK.replace("## Current Task\n\n- なし\n", "## Current Task\n\n- なし\n\n```\n").replace(
            "- Commit: abc1234\n", "```python\n- Commit: abc1234\n")
        after = before.replace("- Reviewed by: gdd-implementation-reviewer, gdd-security-reviewer\n", "")
        self.assertEqual(regressions(before, after), [("一つ目", "missing")])

    def test_too_many_unclosed_fences_cannot_be_checked(self):
        # 閉じていない fence を除いて読み直す回数には上限があり、超えたら判定できないとして例外にする（呼び出し側が止める）
        before = OK.replace("## Verification", "```x\n" * 50 + "## Verification")
        with self.assertRaises(ValueError):
            regressions(before, before)

    def test_hiding_completed_tasks_behind_a_new_fence_is_reported_with_an_unclosed_fence_already_there(self):
        # 前から閉じていない fence（後ろの info 付きの行）があっても、fence を追う読み方の比較もする
        before = OK.replace("## Verification", "## Verification\n\n```python\n")
        after = before.replace("## Completed Tasks", "```\n## Completed Tasks")
        self.assertEqual(regressions(before, after), [("一つ目", "removed"), ("二つ目", "removed")])

    def test_reopen_with_a_same_name_task_already_missing_is_allowed(self):
        before = OK.replace("二つ目", "一つ目").replace("**Reviewed by**: gdd-implementation-reviewer（approved）\n", "")
        block = "### Task 1: 一つ目\n\n- Commit: abc1234\n- Reviewed by: gdd-implementation-reviewer, gdd-security-reviewer\n\n"
        after = before.replace(block, "").replace("## Current Task\n\n- なし\n", "## Current Task\n\n### Task 1: 一つ目\n")
        self.assertEqual(regressions(before, after), [])

    def test_adding_a_same_name_completed_task_without_reviewed_by_is_allowed(self):
        after = OK.replace("## Verification", "### Task 3: 一つ目\n\n- 作業中\n\n## Verification")
        self.assertEqual(regressions(OK, after), [])

if __name__ == "__main__":
    unittest.main()
