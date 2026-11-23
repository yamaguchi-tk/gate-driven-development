"""`Judgment Change` の欄で impl-gating の review を外す判定のテスト。

実行: `python3 -m pytest plugins/gate-driven-development/tests/test_judgment_change.py -q`

外すのは、gate 単位（Current Task の全 task）の全 task が `- Judgment Change: no` ちょうどを持つときだけ。
欄が無い・値が違う・読めない・Express のときは review を回す（中）。外した task の完了は
`Reviewed by: none (Judgment Change: no)` で記録し、同じ task に `no` の宣言があるときだけ受け付ける。
正本: references/task-breakdown-steps.md § Judgment Change。
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _plugin_module_loader import load_plugin_module  # noqa: E402

_mod = load_plugin_module("hooks/scripts/lib/tasklist_parse.py")
#: gate 単位の差分（起点からの変更ファイル）。GATE の `no` の task が Files に宣言したファイルの中に収まる
CHANGED = frozenset({"docs/b.md"})


def review(text, size, changed=CHANGED, completed=None):
    # completed: state.md の Impl Gate Completed（gate 単位の始まりの Completed Tasks の数）。省くと今の数と同じ
    if completed is None:
        completed = len(_mod.completed_tasks_reviewed_by(text)[0]) if isinstance(text, str) else 0
    return _mod.impl_gate_review(text, size, changed, completed)


check = _mod.completed_tasks_reviewed_by
rows = _mod.reviewed_by_rows
regressions = _mod.reviewed_by_regressions

GATE = """# Tasklist

Next Action: gdd-implementation-gating

## Current Task

### Task: T-3 三つ目

- Covers AC: AC-3
- Judgment Change: no
- Execution Status: completed

#### RED Evidence

- Worktree: /tmp/wt

#### Files
- Modify: `docs/b.md`

## Pending Tasks

- なし

## Completed Tasks

### Task: T-1 一つ目

- Judgment Change: yes
- Reviewed by: gdd-implementation-reviewer
"""

#: Gate Batch・並列の batch（Current Task に 2 つ以上の task）。全 task が `no` でも外さない
GATE_TWO = GATE.replace("## Current Task\n\n", """## Current Task

### Task: T-2 二つ目

- Covers AC: AC-2
- Judgment Change: no
- Files: `src/a.py`, tests/test_a.py

""")

DONE = """# Tasklist

## Current Task

- なし

## Completed Tasks

### Task: T-1 一つ目

- Judgment Change: no
- Reviewed by: none (Judgment Change: no)

### Task: T-2 二つ目

- Reviewed by: gdd-implementation-reviewer

## Verification
"""


class ImplGateReviewGateUnitStartTests(unittest.TestCase):
    """gate 単位の途中か（Completed Tasks の数が、Step 11 が起点と同じ時点で書いた数と同じか）。"""

    def test_unreadable_count_runs(self):
        # 判定できないとき: state.md の欄が無い・読めない（script は None を渡す）
        skip, reason = _mod.impl_gate_review(GATE, "standard", CHANGED, None)
        self.assertFalse(skip)
        self.assertIn("Impl Gate Completed", reason)

    def test_task_moved_after_the_start_runs(self):
        # 並列の batch: 兄弟の task が起点の後に Completed へ移り、Current Task に最後の 1 task だけが残った
        skip, reason = review(GATE, "standard", completed=0)
        self.assertFalse(skip)
        self.assertIn("Completed Tasks の数", reason)

    def test_task_moved_out_of_completed_runs(self):
        # 縮めて worklog.md へ移した・再 gate で Current Task に戻した: 数が減っても外さない
        self.assertFalse(review(GATE, "standard", completed=2)[0])


class ImplGateReviewSkipTests(unittest.TestCase):
    def test_all_tasks_declared_no_are_skipped(self):
        self.assertEqual(review(GATE, "standard"), (True, "T-3 三つ目"))

    def test_quick_standard_is_skipped(self):
        self.assertTrue(review(GATE, "quick (standard)")[0])


class ImplGateReviewBlockStaysBlockedTests(unittest.TestCase):
    """fail-open 1: review を回すべき gate 単位が外れない。"""

    def assert_run(self, text, size="standard"):
        skip, detail = review(text, size)
        self.assertFalse(skip, detail)
        self.assertTrue(detail)

    def test_one_task_declared_yes_runs_the_whole_unit(self):
        self.assert_run(GATE.replace("- Covers AC: AC-3\n- Judgment Change: no", "- Covers AC: AC-3\n- Judgment Change: yes"))

    def test_one_task_without_the_field_runs_the_whole_unit(self):
        self.assert_run(GATE.replace("- Covers AC: AC-3\n- Judgment Change: no\n", "- Covers AC: AC-3\n"))

    def test_only_the_exact_value_skips(self):
        for line in (
            "- Judgment Change: no（文書だけ）",
            "- Judgment Change: No",
            "- Judgment Change: `no`",
            "- Judgment Change: no, see design",
            "- **Judgment Change**: no",
            "Judgment Change: no",
            "- Judgment Change:no",
            "- Judgment Change: none",
            "- Judgment Change: ",
        ):
            with self.subTest(line=line):
                self.assert_run(GATE.replace("- Covers AC: AC-3\n- Judgment Change: no", f"- Covers AC: AC-3\n{line}"))

    def test_conflicting_lines_run(self):
        self.assert_run(GATE.replace("- Judgment Change: no\n- Execution Status", "- Judgment Change: no\n- Judgment Change: yes\n- Execution Status"))

    def test_other_forms_of_the_field_beside_a_no_run(self):
        # 宣言の欄に見える行は、形・位置・大小文字を問わず、`- Judgment Change: no` ちょうど 1 本でなければ外さない
        for line in (
            "- **Judgment Change**: yes",
            "> - Judgment Change: yes",
            "- judgment change: yes",
            "- Judgement Change: yes",
            "1. Judgment Change: yes",
            "#### Judgment Change: yes",
            "| Judgment Change | yes |",
            "- Note: Judgment Change は yes に上げた",
            "- Judgment Change: no",
        ):
            with self.subTest(line=line):
                self.assert_run(GATE.replace("- Covers AC: AC-3\n- Judgment Change: no", f"- Covers AC: AC-3\n- Judgment Change: no\n{line}"))

    def test_lines_before_the_first_task_run(self):
        # 見出しでない形で書いた task の本文が、どの task にも属さずに捨てられないようにする
        for lines in (
            "1. Human check for approval.\n   - Execution Status: in_progress\n   - Judgment Change: yes",
            "- T-4 | AC-4 | 四つ目",
            "**Task: T-4 四つ目**",
            "None.",
            "- なし",
        ):
            with self.subTest(lines=lines):
                self.assert_run(GATE.replace("## Current Task\n\n", f"## Current Task\n\n{lines}\n\n"))

    def test_a_task_without_a_heading_mixed_into_a_block_runs(self):
        # 見出しが崩れた task が前の task の block に混ざると、テンプレートで 1 本だけの欄が重なる
        for fields in ("- Covers AC: AC-4", "- Execution Status: not_started", "- Complexity: standard", "- Depends on: T-3"):
            with self.subTest(fields=fields):
                block = "- Covers AC: AC-3\n- Judgment Change: no\n" + ("- Depends on: T-2\n" if "Depends" in fields else "") + ("- Complexity: standard\n" if "Complexity" in fields else "") + ("- Execution Status: not_started\n" if "Execution" in fields else "")
                text = GATE.replace("- Covers AC: AC-3\n- Judgment Change: no\n", block + f"\n**T-4 四つ目**\n\n{fields}\n")
                self.assert_run(text)

    def test_a_gate_round_line_runs(self):
        # 差し戻しを受けた gate 単位の再 gate は、宣言によらず review を回す（Step 8a・Step 9 の確認を飛ばさない）
        for line in ("- Gate Rounds: 1", "- Gate Rounds: 0", "- gate rounds: 2", "Gate Rounds: 1"):
            with self.subTest(line=line):
                self.assert_run(GATE.replace("- Covers AC: AC-3\n", f"- Covers AC: AC-3\n{line}\n"))
        self.assert_run(GATE.replace("## Current Task\n\n", "## Current Task\n\n- Gate Rounds: 1\n\n"))

    def test_field_only_inside_a_fence_does_not_count(self):
        self.assert_run(GATE.replace("- Covers AC: AC-3\n- Judgment Change: no", "- Covers AC: AC-3\n```\n- Judgment Change: no\n```"))

    def test_express_and_unknown_task_sizes_run(self):
        # Express から昇格した steering も外さない（昇格の元の High が直ったかを宣言からは判定できない）
        for size in ("quick (express)", "quick (express → standard)", "trivial", "", "standard?", "Standard"):
            with self.subTest(size=size):
                self.assert_run(GATE, size)

    def test_a_broken_task_heading_runs(self):
        # 見出しが崩れて task として読めないと、その本文が前の task の block に混ざる
        self.assert_run(GATE.replace("### Task: T-3 三つ目\n\n- Covers AC: AC-3\n- Judgment Change: no", "### 三つ目（見出しが崩れた）\n\n- Covers AC: AC-3"))

    def test_declaration_on_a_pending_task_does_not_count(self):
        text = GATE.replace("## Current Task\n\n### Task: T-3", "## Current Task\n\n- なし\n\n## Pending Tasks（前）\n\n### Task: T-3")
        self.assert_run(text)


class ImplGateReviewDiffTests(unittest.TestCase):
    """外すのは、gate 単位の差分が `no` の task の Files に収まるときだけ（崩れた task の変更は宣言の外に出る）。"""

    def assert_run(self, text, changed=CHANGED):
        skip, detail = review(text, "standard", changed)
        self.assertFalse(skip, detail)

    def test_a_change_outside_the_declared_files_runs(self):
        self.assert_run(GATE, CHANGED | {"hooks/guard.py"})

    def test_an_unknown_diff_runs(self):
        self.assert_run(GATE, None)

    def test_a_subset_of_the_declared_files_is_skipped(self):
        text = GATE.replace("- Modify: `docs/b.md`\n", "- Modify: `docs/b.md`, `docs/c.md`\n")
        self.assertTrue(review(text, "standard", frozenset({"docs/b.md"}))[0])

    def test_an_empty_diff_with_declared_files_runs(self):
        # 宣言したファイルが差分に出ていない（起点がその task の変更より後・別の checkout に書いた）
        self.assert_run(GATE, frozenset())

    def test_a_check_only_task_with_an_empty_diff_is_skipped(self):
        text = GATE.replace("#### Files\n- Modify: `docs/b.md`\n", "- Files: なし\n")
        self.assertTrue(review(text, "standard", frozenset())[0])
        self.assert_run(text, frozenset({"docs/b.md"}))

    def test_two_tasks_in_the_gate_unit_run(self):
        # Gate Batch・並列の batch: 起点と State Machine Impact block の単位が gate 単位と合わない
        self.assert_run(GATE_TWO, frozenset({"src/a.py", "tests/test_a.py", "docs/b.md"}))

    def test_a_no_task_without_files_runs(self):
        self.assert_run(GATE.replace("#### Files\n- Modify: `docs/b.md`\n", ""), frozenset({"src/a.py"}))

    def test_a_task_without_a_heading_after_a_read_task_runs(self):
        # 見出しも欄も持たない崩れた task: 文では前の task の本文と区別できないが、変更は宣言の外に出る
        text = GATE.replace("- Modify: `docs/b.md`\n", "- Modify: `docs/b.md`\n\n**T-4 認可の判定を直す**\n\n1. guard.py の allow 条件を変える\n")
        self.assert_run(text, CHANGED | {"hooks/guard.py"})

    def test_a_mixed_in_files_declaration_runs(self):
        # 崩れた task が自分の Files を持ち込むと、1 つの block に Files の宣言が 2 本になる
        for files in ("#### Files\n- Modify: `hooks/guard.py`", "- Files: hooks/guard.py"):
            with self.subTest(files=files):
                text = GATE.replace("- Modify: `docs/b.md`\n", f"- Modify: `docs/b.md`\n\n**T-4 認可の判定を直す**\n\n{files}\n")
                self.assert_run(text, CHANGED | {"hooks/guard.py"})

    def test_unreadable_files_declarations_run(self):
        for files in ("- Files: src/a.py and tests", "- Files: src/**", "- Files:", "#### Files\n- Modify: src/a.py の validation", "#### Files\n- Change: `src/a.py`", "#### Files"):
            with self.subTest(files=files):
                text = GATE.replace("#### Files\n- Modify: `docs/b.md`\n", files + "\n")
                self.assert_run(text, frozenset({"src/a.py"}))

    def test_real_forms_of_files_are_read(self):
        # ローカルの tasklist に実在する形: インデントした項目・Delete・パスの後ろの注記・Test: なし・1 行の形の動詞
        forms = (
            "- Files:\n  - Create: `docs/b.md`\n  - Delete: `src/old.py`\n  - Modify: `src/a.py`（import 元変更 + 戻り値, 2 箇所）\n  - Test: なし（文書のみ）\n- Estimated changes: ~40 行",
            "- Files: Modify `docs/b.md`",
            "- Files: `docs/b.md`（番号は commit 前に確定）, `src/a.py`",
        )
        for files in forms:
            with self.subTest(files=files):
                text = GATE.replace("#### Files\n- Modify: `docs/b.md`\n", files + "\n")
                self.assertTrue(review(text, "standard", frozenset({"docs/b.md"}))[0])

    def test_paths_inside_a_note_are_not_declared(self):
        # 注記の中のパスは宣言に数えない（宣言を広げる側に読まない）
        text = GATE.replace("- Modify: `docs/b.md`\n", "- Modify: `docs/b.md`（`hooks/guard.py` は触らない）\n")
        self.assert_run(text, frozenset({"hooks/guard.py"}))

    def test_block_files_accept_create_modify_test_and_dot_slash(self):
        text = GATE.replace("- Modify: `docs/b.md`\n", "- Create: `./docs/b.md`\n- Test: `tests/test_b.py`, `tests/test_c.py`\n")
        self.assertTrue(review(text, "standard", frozenset({"docs/b.md", "tests/test_c.py"}))[0])


class ImplGateReviewExecutionPlanTests(unittest.TestCase):
    """並列の batch は Execution Plan で見分ける（最後の 1 task だけが Current Task に残っても外さない）。

    外してよいのは、Execution Plan の見出しが無いか、`## Execution Plan` ちょうど 1 つの節に Mode の行が
    ちょうど 1 本あって許可した sequential の形で、番号つきの Gate Batch の行が無いときだけ（許可リスト）。
    """

    def plan(self, body, heading="## Execution Plan"):
        return GATE.replace("## Current Task\n", f"{heading}\n{body}\n\n## Current Task\n")

    def assert_run(self, text):
        skip, detail = review(text, "standard")
        self.assertFalse(skip, detail)

    def test_sequential_forms_are_skipped(self):
        # 実データの逐次の形: 理由の文・逐次の Batch の行・Gate Batch が無いことの注記を並べる
        for body in ("- Mode: sequential", "Mode: sequential", "- sequential", "- Mode: sequential\n- Source: requirements.md#Plan",
                     "- Mode: sequential\n- Batch 1: Task 1\n- Batch 2: Task 2", "- Mode: sequential\n- 理由: 並列にしない（同じファイル）",
                     "- Mode: sequential\n- Gate Batch: なし（quick (standard)）"):
            with self.subTest(body=body):
                self.assertTrue(review(self.plan(body), "standard")[0])

    def test_parallel_and_unknown_modes_run(self):
        for body in ("- Mode: parallel", "Mode: parallel", "- Mode: 並列", "- Mode: Parallel", "- Mode: parallel-then-sequential",
                     "- Mode: sequential（T-2 は並列可）", "- Mode: **sequential**", "- Source: requirements.md#Plan"):
            with self.subTest(body=body):
                self.assert_run(self.plan(body))

    def test_two_mode_lines_run(self):
        self.assert_run(self.plan("- Mode: sequential\n- Mode: parallel"))

    def test_batch_lines_run(self):
        for line in ("- Gate Batch 1: T-3", "- **Gate Batch 2**: T-3"):
            with self.subTest(line=line):
                self.assert_run(self.plan(f"- Mode: sequential\n{line}"))

    def test_other_headings_of_the_plan_run(self):
        for heading in ("### Execution Plan", "## 実行計画（Execution Plan）", "# Execution Plan"):
            with self.subTest(heading=heading):
                self.assert_run(self.plan("- Mode: parallel", heading))

    def test_two_plan_sections_run(self):
        text = self.plan("- Mode: sequential").replace("## Pending Tasks", "## Execution Plan\n- Mode: parallel\n\n## Pending Tasks")
        self.assert_run(text)


class ImplGateReviewDoesNotCrashTests(unittest.TestCase):
    """fail-open 2: 例外で判定ごと落ちず、review を回す側を返す。"""

    def test_non_text_input_runs(self):
        self.assertFalse(review(None, "standard")[0])
        self.assertFalse(review(GATE, None)[0])

    def test_many_unclosed_fences_run(self):
        self.assertFalse(review(GATE + "```x\n" * 50, "standard")[0])


class ImplGateReviewUndecidableTests(unittest.TestCase):
    """fail-open 3: 判定できないときに外さない。"""

    def test_no_current_task_section_runs(self):
        self.assertFalse(review(GATE.replace("## Current Task", "## 今の task"), "standard")[0])

    def test_empty_current_task_runs(self):
        self.assertFalse(review("## Current Task\n\n- なし\n\n## Pending Tasks\n\n- なし\n", "standard")[0])

    def test_unclosed_fence_runs(self):
        self.assertFalse(review(GATE.replace("#### RED Evidence", "```\n#### RED Evidence"), "standard")[0])


class SkippedReviewedByTests(unittest.TestCase):
    def test_declared_and_sentinel_is_skipped(self):
        self.assertEqual(check(DONE), ([("T-1 一つ目", "skipped"), ("T-2 二つ目", "ok")], False))

    def test_skipped_is_an_ok_row(self):
        status, detail = rows(DONE)[0]
        self.assertEqual(status, "ok")
        self.assertIn("Judgment Change: no", detail)

    def test_sentinel_without_the_declaration_is_invalid(self):
        text = DONE.replace("- Judgment Change: no\n", "")
        self.assertEqual(check(text)[0][0], ("T-1 一つ目", "no-implementation-reviewer"))

    def test_sentinel_with_a_yes_declaration_is_invalid(self):
        text = DONE.replace("- Judgment Change: no\n", "- Judgment Change: yes\n")
        self.assertEqual(check(text)[0][0], ("T-1 一つ目", "no-implementation-reviewer"))

    def test_declaration_without_the_sentinel_is_missing(self):
        text = DONE.replace("- Reviewed by: none (Judgment Change: no)\n", "")
        self.assertEqual(check(text)[0][0], ("T-1 一つ目", "missing"))

    def test_two_declarations_are_invalid(self):
        text = DONE.replace("- Judgment Change: no\n", "- Judgment Change: no\n- Judgment Change: no\n")
        self.assertEqual(check(text)[0][0], ("T-1 一つ目", "no-implementation-reviewer"))

    def test_declaration_only_inside_a_fence_is_invalid(self):
        text = DONE.replace("- Judgment Change: no\n", "```\n- Judgment Change: no\n```\n")
        self.assertEqual(check(text)[0][0], ("T-1 一つ目", "no-implementation-reviewer"))

    def test_other_sentinel_values_are_invalid(self):
        for value in ("none", "none (skipped)", "none (Judgment Change: no) approved", "skipped"):
            with self.subTest(value=value):
                text = DONE.replace("none (Judgment Change: no)", value)
                self.assertEqual(check(text)[0][0], ("T-1 一つ目", "no-implementation-reviewer"))


class SkippedRegressionsTests(unittest.TestCase):
    """steering write guard: 外して完了した task の記録を落とす書き込みは止める。"""

    def test_dropping_the_declaration_is_reported(self):
        after = DONE.replace("- Judgment Change: no\n", "")
        self.assertEqual(regressions(DONE, after), [("T-1 一つ目", "no-implementation-reviewer")])

    def test_dropping_the_sentinel_is_reported(self):
        after = DONE.replace("- Reviewed by: none (Judgment Change: no)\n", "")
        self.assertEqual(regressions(DONE, after), [("T-1 一つ目", "missing")])

    def test_reopening_to_current_task_is_allowed(self):
        block = "### Task: T-1 一つ目\n\n- Judgment Change: no\n- Reviewed by: none (Judgment Change: no)\n\n"
        after = DONE.replace(block, "").replace("## Current Task\n\n- なし\n", "## Current Task\n\n### Task: T-1 一つ目\n\n- Judgment Change: yes\n")
        self.assertEqual(regressions(DONE, after), [])

    def test_reviewed_task_rewritten_as_skipped_is_not_reported(self):
        after = DONE.replace("### Task: T-2 二つ目\n\n- Reviewed by: gdd-implementation-reviewer",
                             "### Task: T-2 二つ目\n\n- Judgment Change: no\n- Reviewed by: none (Judgment Change: no)")
        self.assertEqual(regressions(DONE, after), [])


if __name__ == "__main__":
    unittest.main()
