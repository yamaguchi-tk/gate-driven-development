"""steering write guard の `completed_reviewed_by`（完了タスクの Reviewed by を落とす書き込み）のテスト。

実行: `python3 -m pytest plugins/gate-driven-development/tests/test_completed_reviewed_by_write_guard.py -q`

hook の入口（run-steering-write-hook.sh）に PreToolUse の payload を渡す。2026-10-01 の S-0 では、
サイズ上限で tasklist.md を要約したときに完了タスクの `Reviewed by:` が落ち、completion-check で
差し戻された。それまでの hook は `Reviewed by:` を読まなかったので、書き込みの時点で止める。
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from _paths import PLUGIN_ROOT

WRAPPER = PLUGIN_ROOT / "hooks" / "scripts" / "run-steering-write-hook.sh"
BLOCK1 = "### Task 1: 一つ目\n\n- Commit: abc1234\n- Reviewed by: gdd-implementation-reviewer\n\n"
TASKLIST = (
    "# Task List\n\nNext Action: done\n\n## Current Task\n\n- なし\n\n## Completed Tasks\n\n"
    + BLOCK1
    + "### Task 2: 二つ目\n\n- Commit: def5678\n- Reviewed by: gdd-implementation-reviewer\n\n## Verification\n"
)


class CompletedReviewedByWriteGuardTests(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name).resolve()
        self.tasklist = self.root / ".steering" / "20261002-x" / "tasklist.md"
        self.tasklist.parent.mkdir(parents=True)
        self.tasklist.write_text(TASKLIST, encoding="utf-8")

    def _run(self, tool_name: str, tool_input: dict) -> subprocess.CompletedProcess[str]:
        env = dict(os.environ)
        env["GDD_HOOK_STATE_DIR"] = str(self.root / "hookstate")
        env["HOME"] = str(self.root)  # kill switch を読まない
        env["CLAUDE_PLUGIN_ROOT"] = str(PLUGIN_ROOT)
        return subprocess.run(
            ["bash", str(WRAPPER)], input=json.dumps({"tool_name": tool_name, "tool_input": tool_input}),
            env=env, capture_output=True, text=True, check=False,
        )

    def _edit(self, old: str, new: str) -> subprocess.CompletedProcess[str]:
        return self._run("Edit", {"file_path": str(self.tasklist), "old_string": old, "new_string": new})

    def assert_denied(self, result: subprocess.CompletedProcess[str], *needles: str) -> None:
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        message = json.loads(result.stderr)["systemMessage"]
        for needle in needles:
            self.assertIn(needle, message)

    def test_summarizing_write_that_drops_reviewed_by_is_denied(self):
        summarized = TASKLIST.replace("- Reviewed by: gdd-implementation-reviewer\n", "", 1)
        result = self._run("Write", {"file_path": str(self.tasklist), "content": summarized})
        self.assert_denied(result, "一つ目", "Reviewed by")

    def test_edit_that_deletes_only_the_reviewed_by_line_is_denied(self):
        self.assert_denied(self._edit("- Reviewed by: gdd-implementation-reviewer\n\n### Task 2", "\n### Task 2"), "一つ目")

    def test_edit_that_deletes_a_completed_task_block_is_denied(self):
        self.assert_denied(self._edit(BLOCK1, ""), "一つ目")

    def test_reopen_in_one_multiedit_is_allowed(self):
        result = self._run("MultiEdit", {"file_path": str(self.tasklist), "edits": [
            {"old_string": BLOCK1, "new_string": ""},
            {"old_string": "## Current Task\n\n- なし\n", "new_string": "## Current Task\n\n### Task 1: 一つ目\n\n- 再オープン\n"},
        ]})
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_reopen_in_two_writes_is_allowed(self):
        # 先に Current へ足し、次の書き込みで Completed から消す（deny 文言が案内する 2 回の書き込み）
        reopened = TASKLIST.replace("## Current Task\n\n- なし\n", "## Current Task\n\n" + BLOCK1)
        first = self._run("Write", {"file_path": str(self.tasklist), "content": reopened})
        self.assertEqual(first.returncode, 0, first.stderr)
        self.tasklist.write_text(reopened, encoding="utf-8")
        self.assertEqual(self._edit("## Completed Tasks\n\n" + BLOCK1, "## Completed Tasks\n\n").returncode, 0)

    def test_moving_detail_lines_is_allowed(self):
        self.assertEqual(self._edit("- Commit: abc1234\n", "").returncode, 0)

    def test_new_file_is_allowed(self):
        other = self.tasklist.parent.parent / "20261003-y" / "tasklist.md"
        result = self._run("Write", {"file_path": str(other), "content": TASKLIST})
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_apply_patch_is_not_checked(self):
        # 書き込み後の全文を投影できない（限界として開示する）
        patch = (
            "*** Begin Patch\n*** Update File: " + str(self.tasklist) + "\n@@\n"
            "-- Reviewed by: gdd-implementation-reviewer\n*** End Patch\n"
        )
        result = self._run("ApplyPatch", {"patch": patch})
        self.assertEqual(result.returncode, 0, result.stderr)

    @unittest.skipIf(hasattr(os, "geteuid") and os.geteuid() == 0, "root は読み取り権限を無視する")
    def test_unreadable_tasklist_is_denied(self):
        # 判定できない（書き込み前を読めない）ときは止める側に倒す
        self.tasklist.chmod(0)
        self.addCleanup(self.tasklist.chmod, 0o644)
        result = self._run("Write", {"file_path": str(self.tasklist), "content": TASKLIST})
        self.assert_denied(result, "could not check", "PermissionError")

    def test_tasklist_with_invalid_utf8_is_denied(self):
        # 置き換えて読むと構造の行が読めなくなる（UTF-16 など）ので、UTF-8 で読めなければ止める（検算・done guard と同じ厳密さ）
        self.tasklist.write_bytes(TASKLIST.encode("utf-16"))
        summarized = TASKLIST.replace("- Reviewed by: gdd-implementation-reviewer\n", "", 1)
        result = self._run("Write", {"file_path": str(self.tasklist), "content": summarized})
        self.assert_denied(result, "could not check", "UnicodeDecodeError")

    def test_tasklist_with_too_many_unclosed_fences_is_denied(self):
        # 閉じていない fence の読み直しに上限があり、超えたら判定できないとして止める（hook の timeout で通さない）
        self.tasklist.write_text(TASKLIST + "```x\n" * 50, encoding="utf-8")
        result = self._run("Write", {"file_path": str(self.tasklist), "content": TASKLIST})
        self.assert_denied(result, "could not check", "ValueError")

    def test_third_consecutive_deny_is_demoted_to_warning(self):
        old, new = BLOCK1, ""
        self.assertEqual(self._edit(old, new).returncode, 2)
        self.assertEqual(self._edit(old, new).returncode, 2)
        third = self._edit(old, new)
        self.assertEqual(third.returncode, 0, third.stderr)
        self.assertIn("HUMAN REVIEW REQUIRED", json.loads(third.stdout)["systemMessage"])

    def test_moving_a_completed_task_to_an_archive_section_is_denied(self):
        archived = TASKLIST.replace(BLOCK1, "") + "\n## Archived Tasks\n\n" + BLOCK1
        self.assert_denied(self._run("Write", {"file_path": str(self.tasklist), "content": archived}), "一つ目")

    def test_edit_whose_empty_new_string_joins_the_reviewed_by_line_is_denied(self):
        # 空の new_string は続く改行ごと消す（Claude Code の Edit）。`- Commit: ` と Reviewed by の行がつながる
        self.assert_denied(self._edit("abc1234", ""), "一つ目")

    def test_edit_whose_old_string_is_not_found_is_denied(self):
        self.assert_denied(self._edit("- Commit: zzz9999\n", ""), "old_string")

    def test_clean_writes_between_denies_reset_the_count(self):
        clean = ("- Commit: def5678\n", "")
        for _ in range(2):
            self.assertEqual(self._edit(BLOCK1, "").returncode, 2)
            self.assertEqual(self._edit(*clean).returncode, 0)
        self.assertEqual(self._edit(BLOCK1, "").returncode, 2)

    def test_route_in_progress_does_not_exempt_the_write(self):
        # route は task-breakdown が作り直す前に none へ戻るので、例外にしない（作り直しは先に Pending へ移す）
        for route in ("human_recheck_required", "planning_rework_required", "design_detail_only"):
            shutil.rmtree(self.root / "hookstate", ignore_errors=True)  # 3 回目の降格を避ける
            (self.tasklist.parent / "state.md").write_text(f"# State\n\n- Route In Progress: {route}\n", encoding="utf-8")
            self.assert_denied(self._edit(BLOCK1, ""), "一つ目")

    def test_dropping_three_tasks_in_one_write_is_not_demoted_on_the_first_try(self):
        # S-0 の形（要約で複数の完了タスクを一度に落とす）。降格の回数は書き込み 1 回につき 1 だけ進む
        three = TASKLIST.replace("## Verification", "### Task 3: 三つ目\n\n- Reviewed by: gdd-implementation-reviewer\n\n## Verification")
        self.tasklist.write_text(three, encoding="utf-8")
        summarized = three.split("## Completed Tasks")[0] + "## Completed Tasks\n\n- 3 件完了\n\n## Verification\n"
        for _ in range(2):
            self.assert_denied(self._run("Write", {"file_path": str(self.tasklist), "content": summarized}), "一つ目", "二つ目", "三つ目")
        third = self._run("Write", {"file_path": str(self.tasklist), "content": summarized})
        self.assertEqual(third.returncode, 0, third.stderr)
        self.assertIn("HUMAN REVIEW REQUIRED", json.loads(third.stdout)["systemMessage"])

    def test_same_file_named_by_two_keys_counts_as_one_deny(self):
        # file_path と path（綴り違いを含む）で同じ tasklist.md を指しても、書き込み 1 回は 1 回と数える
        summarized = TASKLIST.replace("- Reviewed by: gdd-implementation-reviewer\n", "", 1)
        for other in (str(self.tasklist), f"{self.tasklist.parent}/./{self.tasklist.name}"):
            shutil.rmtree(self.root / "hookstate", ignore_errors=True)
            payload = {"file_path": str(self.tasklist), "path": other, "content": summarized}
            for _ in range(2):
                self.assert_denied(self._run("Write", payload), "一つ目")
            third = self._run("Write", payload)
            self.assertEqual(third.returncode, 0, third.stderr)
            self.assertIn("HUMAN REVIEW REQUIRED", json.loads(third.stdout)["systemMessage"])

    def test_keys_differing_only_in_separators_share_one_counter(self):
        # normalize_path が同じ path とみなす綴り（\ と /）は、counter（_state_key）でまとめて 1 回と数える
        design = self.tasklist.parent / "design.md"
        payload = {"file_path": str(design), "path": str(design).replace("/", "\\"), "content": "...省略\n"}
        for _ in range(2):
            self.assert_denied(self._run("Write", payload), "省略")
        third = self._run("Write", payload)
        self.assertEqual(third.returncode, 0, third.stderr)
        self.assertIn("HUMAN REVIEW REQUIRED", json.loads(third.stdout)["systemMessage"])


if __name__ == "__main__":
    unittest.main()
