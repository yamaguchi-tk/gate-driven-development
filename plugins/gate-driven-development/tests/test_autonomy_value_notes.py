"""自走上限の値に付いた注記を、書き込み後の state.md で見つけて main に返すこと。

`references/post-merge-qa.md` § 入口の読み方は値を完全一致で比べるので、`マージまで（…）` のような
注記付きの値では自走のマージに入らない。2026-10 の実測では注記付きの書き込みが完全一致より多く、
lint の警告は systemMessage（利用者の端末だけ）で書き込みの 1 回後に出ており、main に届いていなかった。
"""
from __future__ import annotations

import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

from _paths import PLUGIN_ROOT
from _plugin_module_loader import load_plugin_module

HOOK = PLUGIN_ROOT / "hooks" / "scripts" / "validate-steering-write.py"
AD_LINT = PLUGIN_ROOT / "scripts" / "lint-approved-direction.py"
LIB = load_plugin_module("hooks/scripts/lib/autonomy_value.py")

CANONICAL = """# State

## Gate Status
Started At: 2026-10-02T00:26:19+09:00
- Resume From: gdd-task-breakdown
- Next Action: gdd-task-breakdown
- Human Check Status: approved | evidence: human:マージまで | updated_by: main | updated_at: 2026-10-02T09:16:12+09:00
- Route In Progress: none

## Approved Direction
- 自走上限: マージまで
- 人に戻す条件: 事前回答の人に戻す条件
"""

# 実測した注記の形（GDD を使う別の repo の steering、2026-10-01〜03）
ANNOTATED_LIMIT_LINES = (
    "- 自走上限: マージまで（merge ごとの確認は不要。人の事前回答 2026-10-01 夜・10-02 朝）",
    "- 自走上限: マージまで。PR-1 のみ。条件 3=merge 前に S-1a PR-1 が main にあること",
    "- 自走上限: マージ・デプロイ・QA まで（ユーザーが「マージして」と明示）",
    "- **自走上限**: マージまで + AC-9 の read-only 確認",
    "+ `自走上限（S-1）`= マージまで（Fable 代理）",
    "* 自走上限：マージまで（3 PR とも）",
)


def _state(limit_line: str = "- 自走上限: マージまで", evidence: str = "human:マージまで") -> str:
    return CANONICAL.replace("- 自走上限: マージまで", limit_line).replace("human:マージまで", evidence)


class AutonomyValueNotesTests(unittest.TestCase):
    def test_canonical_values_have_no_notes(self) -> None:
        for limit in LIB.MERGE_AUTONOMY_LIMITS:
            with self.subTest(limit=limit):
                self.assertEqual(LIB.autonomy_value_notes(_state(f"- 自走上限: {limit}", f"human:{limit}")), [])

    def test_annotated_limit_lines_get_a_note(self) -> None:
        for line in ANNOTATED_LIMIT_LINES:
            with self.subTest(line=line):
                notes = LIB.autonomy_value_notes(_state(line))
                self.assertTrue(any("に注記が付いた形" in n for n in notes), notes)

    def test_annotated_evidence_gets_a_note(self) -> None:
        evidence = "human:マージまで（2026-10-03 事前回答 + 同日「Fableに相談しながら自律的に進めて」）"
        notes = LIB.autonomy_value_notes(_state(evidence=evidence))
        self.assertTrue(any("に注記が付いた形" in n for n in notes), notes)

    def test_note_steers_to_the_narrow_value_not_to_dropping_the_annotation(self) -> None:
        """注記を消して完全一致を作る方向へ誘導しない。既定は `PR 作成まで` に倒す。"""
        note = "\n".join(LIB.autonomy_value_notes(_state(ANNOTATED_LIMIT_LINES[1])))
        self.assertIn("PR 作成まで", note)
        self.assertIn("worklog.md", note)
        self.assertIn("事前回答を適用した承認なら", note)
        self.assertNotIn("だけにし", note)

    def test_values_without_merge_are_left_alone(self) -> None:
        for line in (
            "- 自走上限: PR 作成まで。merge / deploy は別承認",
            "- 自走上限: PR マージ後検証 / 再学習まで",
        ):
            with self.subTest(line=line):
                notes = LIB.autonomy_value_notes(_state(line, "autonomy:human-check"))
                self.assertEqual(notes, [])

    def test_values_outside_the_table_that_mention_merge_get_a_note(self) -> None:
        """表の外の「マージ…」の値は、読み手（post-merge-qa § 入口の完全一致）が退けるので知らせる。

        `マージまで` などで始まらない値（I-1a の `マージ・検証まで（…）。…`）では、これまで何も返していなかった。
        """
        for line in (
            "- 自走上限: マージ・検証まで（2026-10-12T12:19:59+0900 依頼者「確定 OK / マージして検証まで実施したい」。"
            "旧: PR 作成まで）。マージは merge commit（squash しない）",
            "- 自走上限: マージ・検証まで",
            "- 自走上限: マージ・E2E まで",
            "- 自走上限: マージと E2E 検証まで",
            "- 自走上限: docs-only PR はマージまで",
        ):
            with self.subTest(line=line):
                value = line.removeprefix("- 自走上限: ")
                notes = LIB.autonomy_value_notes(_state(line, f"human:{value}"))
                self.assertTrue(any("表の値ではありません" in n for n in notes), notes)
                note = "\n".join(notes)
                self.assertIn("PR 作成まで", note)
                self.assertIn("§ 事前回答 5", note)

    def test_merge_limit_with_non_human_evidence_gets_a_note(self) -> None:
        """自走上限がマージの値でも、evidence が `human:<値>` でなければ自走のマージに入らない（手順 2）。"""
        for evidence in ("human check 2 回目「確定 OK」（2026-10-12T12:19:59+0900）", "autonomy:human-check", ""):
            with self.subTest(evidence=evidence):
                notes = LIB.autonomy_value_notes(_state(evidence=evidence))
                self.assertTrue(any("`human:` で始まりません" in n for n in notes), notes)
                note = "\n".join(n for n in notes if "`human:` で始まりません" in n)
                self.assertIn("書き換えません", note)

    def test_non_human_evidence_before_approval_is_left_alone(self) -> None:
        """承認前の status（`pending`・`changes_requested`）では、`human:` でない evidence は正規の形である。"""
        for status in ("pending", "changes_requested"):
            for evidence in ("none", "x"):
                with self.subTest(status=status, evidence=evidence):
                    state = _state(evidence=evidence).replace("Human Check Status: approved", f"Human Check Status: {status}")
                    self.assertEqual(LIB.autonomy_value_notes(state), [])

    def test_value_notes_still_come_before_approval(self) -> None:
        state = _state("- 自走上限: マージ・検証まで", "none").replace("Human Check Status: approved", "Human Check Status: pending")
        self.assertTrue(any("表の値ではありません" in n for n in LIB.autonomy_value_notes(state)))

    def test_status_outside_the_schema_values_still_gets_the_evidence_note(self) -> None:
        """承認前とみなすのは schema の `pending`・`changes_requested` だけで、`承認` などは承認前にしない。"""
        for status in ("承認", "approved（2026-10-12 本人）"):
            with self.subTest(status=status):
                state = _state(evidence="none").replace("Human Check Status: approved", f"Human Check Status: {status}")
                self.assertTrue(any("`human:` で始まりません" in n for n in LIB.autonomy_value_notes(state)))

    def test_evidence_note_shows_the_value_only_for_a_table_value(self) -> None:
        """表の外の自走上限を `human:` に写すよう示さない。"""
        canonical = "\n".join(LIB.autonomy_value_notes(_state(evidence="none")))
        self.assertIn("`human:マージまで`", canonical)
        outside = "\n".join(n for n in LIB.autonomy_value_notes(_state("- 自走上限: マージ・検証まで（依頼者）", "none"))
                            if "`human:` で始まりません" in n)
        self.assertNotIn("human:マージ・検証まで", outside)
        self.assertIn("表の値に直した", outside)
        annotated = "\n".join(n for n in LIB.autonomy_value_notes(_state(ANNOTATED_LIMIT_LINES[0], "none"))
                              if "`human:` で始まりません" in n)
        self.assertNotIn("`human:マージまで（", annotated)
        self.assertIn("表の値に直した", annotated)

    def test_before_approval_statuses_match_the_schema(self) -> None:
        schema = json.loads((PLUGIN_ROOT / "references" / "state-schema.json").read_text(encoding="utf-8"))
        allowed = set(schema["phase_status"]["Human Check Status"]["allowed"])
        self.assertEqual(set(LIB._BEFORE_APPROVAL), allowed - {"approved"})

    def test_unannotated_non_merge_table_value_skips_line_shape_notes(self) -> None:
        state = _state("- 自走上限: PR マージ後検証 / 再学習まで", "autonomy:x").replace(
            "- Route In Progress: none", "- Human Check Status（履歴）: approved | evidence: human:OK\n- Route In Progress: none"
        )
        self.assertEqual(LIB.autonomy_value_notes(state), [])
        self.assertEqual(LIB.autonomy_value_notes(_state("* 自走上限：PR マージ後検証 / 再学習まで", "autonomy:x")), [])

    def test_note_for_outside_values_does_not_add_an_undecided_fallback(self) -> None:
        """§ 事前回答 5 は、当てはめられない発話を引き上げない。WARN も「決められない」の当てはめを足さない。"""
        note = "\n".join(LIB.autonomy_value_notes(_state("- 自走上限: マージ・検証まで", "human:マージ・検証まで")))
        self.assertNotIn("決められない", note)

    def test_annotated_non_merge_table_value_gets_a_note_that_keeps_merge_manual(self) -> None:
        notes = LIB.autonomy_value_notes(_state("- 自走上限: PR マージ後検証 / 再学習まで（マージも自律で可）", "autonomy:x"))
        note = "\n".join(notes)
        self.assertIn("1 操作ごとの承認", note)
        self.assertNotIn("`human:` で始まりません", note)

    def test_spaced_human_evidence_is_reported_once_per_value(self) -> None:
        notes = LIB.autonomy_value_notes(_state("- 自走上限: マージ・検証まで", "human: マージ・検証まで"))
        self.assertEqual(sum("表の値ではありません" in n for n in notes), 1, notes)

    def test_the_i1a_state_gets_both_notes(self) -> None:
        state = _state(
            "- 自走上限: マージ・検証まで（2026-10-12T12:19:59+0900 依頼者）。マージは merge commit",
            "human check 2 回目「確定 OK」（2026-10-12T12:19:59+0900）",
        )
        notes = LIB.autonomy_value_notes(state)
        self.assertTrue(any("表の値ではありません" in n for n in notes), notes)
        self.assertTrue(any("`human:` で始まりません" in n for n in notes), notes)

    def test_lines_inside_code_fences_are_not_read(self) -> None:
        state = CANONICAL + "\n```\n- 自走上限: マージまで（記入例）\n```\n"
        self.assertEqual(LIB.autonomy_value_notes(state), [])

    def test_mismatch_between_evidence_and_limit_gets_a_note(self) -> None:
        notes = LIB.autonomy_value_notes(_state("- 自走上限: PR 作成まで"))
        self.assertTrue(any("一致しません" in n for n in notes), notes)

    def test_missing_limit_line_with_human_evidence_gets_a_note(self) -> None:
        notes = LIB.autonomy_value_notes(_state("- 承認者の指示: 自走の上限は マージまで"))
        self.assertTrue(any("0 行" in n for n in notes), notes)

    def test_reader_rejected_shapes_without_annotation_get_a_note(self) -> None:
        """注記が無くても、読み手（post-merge-qa § 入口）が退ける形は知らせる。"""
        shapes = {
            "非正規の行の形": (_state("* 自走上限：マージまで"), "形ではありません"),
            "太字の欄名": (_state("- **自走上限**: マージまで"), "形ではありません"),
            "括弧の注記と =": (_state("+ `自走上限（S-1）`= マージまで"), "形ではありません"),
            "全角コロン": (_state("- 自走上限：マージまで"), "形ではありません"),
            "human: の後の空白": (_state(evidence="human: マージまで"), "一致しません"),
            "自走上限が 2 行": (_state("- 自走上限: マージまで\n- 自走上限: マージまで"), "自走上限の行が 2 行"),
            "正規と非正規が並ぶ": (_state("- 自走上限: マージまで\n* 自走上限：PR 作成まで"), "自走上限の行が 2 行"),
            "Human Check Status が 2 行": (CANONICAL.replace(
                "- Route In Progress: none", "- Human Check Status: approved | evidence: human:マージまで\n- Route In Progress: none"
            ), "Human Check Status の行が 2 行"),
        }
        for name, (state, reason) in shapes.items():
            with self.subTest(name=name):
                self.assertTrue(any(reason in n for n in LIB.autonomy_value_notes(state)), name)

    def test_long_runs_of_stars_are_read_quickly(self) -> None:
        """`*` が長く続く行（ラベルの前・後）で、行の正規表現の後戻りが増えない。"""
        import time
        for name, line in {"ラベルの前": "*" * 36, "ラベルの後": "- 自走上限" + "*" * 16000}.items():
            with self.subTest(name=name):
                started = time.monotonic()
                LIB.autonomy_value_notes(CANONICAL + "\n" + line + "\n")
                self.assertLess(time.monotonic() - started, 0.5)

    def test_fence_reading_is_the_shared_one(self) -> None:
        """4 連の fence の中の ``` と、~~~ の中の ``` で、内外を取り違えない（tasklist_parse.strip_fenced_blocks）。"""
        example_inside = CANONICAL + "\n````\n```\n- 自走上限: マージまで（記入例）\n```\n````\n"
        self.assertEqual(LIB.autonomy_value_notes(example_inside), [])
        after_tilde = _state("- 人に戻す条件: なし") + "\n~~~\n```\n~~~\n- 自走上限: マージまで（注記）\n"
        self.assertTrue(any("注記" in n for n in LIB.autonomy_value_notes(after_tilde)))

    def test_long_values_are_quoted_short(self) -> None:
        notes = LIB.autonomy_value_notes(_state("- 自走上限: マージまで（" + "あ" * 300 + "）"))
        self.assertTrue(notes)
        self.assertTrue(all("あ" * 100 not in n for n in notes))

    def test_non_merge_steering_with_two_status_lines_is_left_alone(self) -> None:
        state = _state("- 自走上限: PR 作成まで", "human:PR 作成まで").replace(
            "- Route In Progress: none", "- Human Check Status（履歴）: approved | evidence: human:OK\n- Route In Progress: none"
        )
        self.assertEqual(LIB.autonomy_value_notes(state), [])

    def test_non_human_evidence_is_not_compared(self) -> None:
        self.assertEqual(LIB.autonomy_value_notes(_state("- 自走上限: PR 作成まで", "autonomy:human-check")), [])


class HookEntryTests(unittest.TestCase):
    """steering の書き込み hook の入口から、書き込み後の内容の注記が additionalContext で届く。"""

    def setUp(self) -> None:
        self._state_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self._state_dir, ignore_errors=True)
        self._tmp = Path(tempfile.mkdtemp()).resolve()
        self.addCleanup(shutil.rmtree, self._tmp, ignore_errors=True)
        self.state = self._tmp / ".steering" / "20261003-autonomy" / "state.md"
        self.state.parent.mkdir(parents=True)
        self.state.write_text(CANONICAL, encoding="utf-8")

    def _env(self) -> dict[str, str]:
        env = dict(os.environ, GDD_HOOK_STATE_DIR=self._state_dir, CLAUDE_PLUGIN_ROOT=str(PLUGIN_ROOT))
        return env

    def _run(self, tool_name: str, tool_input: dict) -> dict:
        payload = {"tool_name": tool_name, "tool_input": tool_input}
        result = subprocess.run(
            [sys.executable, str(HOOK)], input=json.dumps(payload), env=self._env(), capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return json.loads(result.stdout) if result.stdout.strip() else {}

    def _context(self, response: dict) -> str:
        return response.get("hookSpecificOutput", {}).get("additionalContext", "")

    def test_edit_that_adds_an_annotation_reports_it_on_the_same_write(self) -> None:
        response = self._run("Edit", {
            "file_path": str(self.state),
            "old_string": "- 自走上限: マージまで",
            "new_string": ANNOTATED_LIMIT_LINES[0],
        })
        self.assertIn("注記", self._context(response))
        self.assertNotIn("permissionDecision", response.get("hookSpecificOutput", {}))

    def test_write_with_annotated_evidence_reports_it(self) -> None:
        content = _state(evidence="human:マージまで（2026-10-03 事前回答）")
        response = self._run("Write", {"file_path": str(self.state), "content": content})
        self.assertIn("注記", self._context(response))

    def test_edit_that_removes_the_annotation_is_silent(self) -> None:
        self.state.write_text(_state(ANNOTATED_LIMIT_LINES[0]), encoding="utf-8")
        response = self._run("Edit", {
            "file_path": str(self.state),
            "old_string": ANNOTATED_LIMIT_LINES[0],
            "new_string": "- 自走上限: マージまで",
        })
        self.assertEqual(self._context(response), "")
        self.assertNotIn("human-evidence", response.get("systemMessage", ""))

    def test_canonical_state_is_silent(self) -> None:
        response = self._run("Edit", {
            "file_path": str(self.state),
            "old_string": "- Route In Progress: none",
            "new_string": "- Route In Progress: none ",
        })
        self.assertEqual(self._context(response), "")
        self.assertNotIn("systemMessage", response)

    def test_requirements_md_is_not_checked(self) -> None:
        req = self.state.parent / "requirements.md"
        response = self._run("Write", {"file_path": str(req), "content": "# R\n" + ANNOTATED_LIMIT_LINES[0] + "\n"})
        self.assertEqual(self._context(response), "")

    def test_writes_that_leave_the_autonomy_lines_unchanged_are_silent(self) -> None:
        """後から見つけた記録は書き換えないので、自走上限と Human Check Status の行が変わらない書き込みでは返さない。"""
        self.state.write_text(_state(ANNOTATED_LIMIT_LINES[0]), encoding="utf-8")
        # old_string が無い Edit は、リスクの段が低でない steering では risk_tier が先に止めるので、段を低にし、依頼の原文（hook の節で始まる request.md）を置く
        (self.state.parent / "request-crosscheck.md").write_text("### リスクの段\n\nリスクの段: 低\n", encoding="utf-8")
        (self.state.parent / "request.md").write_text("<!-- gdd-request-capture:begin -->\n", encoding="utf-8")
        for name, edit in {
            "無関係な行": ("- Route In Progress: none", "- Route In Progress: none "),
            "old_string が見つからない": ("存在しない行", "- 自走上限: マージまで"),
        }.items():
            with self.subTest(name=name):
                response = self._run("Edit", {"file_path": str(self.state), "old_string": edit[0], "new_string": edit[1]})
                self.assertEqual(self._context(response), "")

    def test_new_state_md_with_annotation_is_reported(self) -> None:
        """書き込み前の state.md が無いとき（新しい steering）も、行が変わったものとして返す。"""
        self.state.unlink()
        response = self._run("Write", {"file_path": str(self.state), "content": _state(ANNOTATED_LIMIT_LINES[0])})
        self.assertIn("に注記が付いた形", self._context(response))

    def test_delete_only_edit_reports_on_an_oversized_state_md(self) -> None:
        """上限超過中の state.md でも、行を消すだけの Edit は自走上限の注記を返す（減る書き込みなので size の通知は無い）。"""
        self.state.write_text(CANONICAL + "\n" + "x" * 20_001 + "\n", encoding="utf-8")
        payload = {"tool_name": "Edit", "tool_input": {
            "file_path": str(self.state), "old_string": "- 自走上限: マージまで\n", "new_string": "",
        }}
        result = subprocess.run(
            [sys.executable, str(HOOK)], input=json.dumps(payload), env=self._env(), capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("0 行", self._context(json.loads(result.stdout)))
        self.assertNotIn("[steering size]", result.stdout + result.stderr)

    def test_apply_patch_to_upper_case_state_md_keeps_the_lint_warning(self) -> None:
        upper = self.state.parent / "State.md"
        upper.write_text(_state(ANNOTATED_LIMIT_LINES[0]), encoding="utf-8")
        patch = (
            "*** Begin Patch\n*** Update File: " + str(upper) + "\n@@\n"
            "-- Route In Progress: none\n+- Route In Progress: none \n*** End Patch\n"
        )
        response = self._run("ApplyPatch", {"patch": patch})
        self.assertIn("human-evidence", response.get("systemMessage", ""))

    def test_edit_to_a_merge_value_outside_the_table_reports_it(self) -> None:
        response = self._run("Edit", {
            "file_path": str(self.state),
            "old_string": "- 自走上限: マージまで",
            "new_string": "- 自走上限: マージ・検証まで（2026-10-12 依頼者）",
        })
        self.assertIn("表の値ではありません", self._context(response))
        self.assertNotIn("permissionDecision", response.get("hookSpecificOutput", {}))

    def test_edit_to_non_human_evidence_under_a_merge_limit_reports_it(self) -> None:
        response = self._run("Edit", {
            "file_path": str(self.state),
            "old_string": "evidence: human:マージまで",
            "new_string": "evidence: human check 2 回目「確定 OK」",
        })
        self.assertIn("`human:` で始まりません", self._context(response))

    def test_write_of_an_annotated_non_merge_table_value_reports_it(self) -> None:
        """入口を開くのが注記付きの値だけのとき（evidence が `human:` でない）も、hook の入口から届く。"""
        content = _state("- 自走上限: PR マージ後検証 / 再学習まで（マージも自律で可）", "autonomy:x")
        response = self._run("Write", {"file_path": str(self.state), "content": content})
        self.assertIn("1 操作ごとの承認", self._context(response))

    def test_upper_case_state_md_is_checked(self) -> None:
        upper = self.state.parent / "State.md"
        upper.write_text(CANONICAL, encoding="utf-8")
        response = self._run("Edit", {
            "file_path": str(upper), "old_string": "- 自走上限: マージまで", "new_string": ANNOTATED_LIMIT_LINES[0],
        })
        self.assertIn("に注記が付いた形", self._context(response))

    def test_write_and_multiedit_use_the_written_text_only(self) -> None:
        """Write・MultiEdit も書き込み後の全文で見て、書き込み前の内容の lint の警告を出さない。"""
        payloads = {
            "Write": {"file_path": str(self.state), "content": CANONICAL},
            "MultiEdit": {"file_path": str(self.state), "edits": [
                {"old_string": ANNOTATED_LIMIT_LINES[0], "new_string": "- 自走上限: マージまで"},
            ]},
        }
        for tool, tool_input in payloads.items():
            with self.subTest(tool=tool):
                self.state.write_text(_state(ANNOTATED_LIMIT_LINES[0]), encoding="utf-8")
                response = self._run(tool, tool_input)
                self.assertEqual(self._context(response), "")
                self.assertNotIn("human-evidence", response.get("systemMessage", ""))

    def test_delete_only_edit_reports_the_missing_line(self) -> None:
        response = self._run("Edit", {
            "file_path": str(self.state),
            "old_string": "- 自走上限: マージまで\n",
            "new_string": "",
        })
        self.assertIn("0 行", self._context(response))

    def test_apply_patch_keeps_the_lint_human_evidence_warning(self) -> None:
        """書き込み後の全文を作れない ApplyPatch では、書き込み前の内容の lint の警告を残す。"""
        self.state.write_text(_state(ANNOTATED_LIMIT_LINES[0]), encoding="utf-8")
        patch = (
            "*** Begin Patch\n*** Update File: " + str(self.state) + "\n@@\n"
            "-- Route In Progress: none\n+- Route In Progress: none \n*** End Patch\n"
        )
        response = self._run("ApplyPatch", {"patch": patch})
        self.assertIn("human-evidence", response.get("systemMessage", ""))

    def test_exception_in_the_check_keeps_allow(self) -> None:
        hook = load_plugin_module("hooks/scripts/validate-steering-write.py")
        for name, new_string in {"中身のある Edit": ANNOTATED_LIMIT_LINES[0], "行を消すだけの Edit": ""}.items():
            payload = {"tool_name": "Edit", "tool_input": {
                "file_path": str(self.state), "old_string": "- 自走上限: マージまで\n", "new_string": new_string,
            }}
            out, err = io.StringIO(), io.StringIO()
            with self.subTest(name=name), mock.patch.dict(os.environ, self._env(), clear=True), \
                    mock.patch.object(hook, "notes_for_write", side_effect=RuntimeError("boom")), \
                    mock.patch.object(sys, "stdin", io.StringIO(json.dumps(payload))), \
                    redirect_stdout(out), redirect_stderr(err):
                rc = hook.main()
                self.assertEqual(rc, 0)
                self.assertEqual(err.getvalue(), "")
                response = json.loads(out.getvalue())
                self.assertTrue(response.get("continue"))
                self.assertNotIn("permissionDecision", response.get("hookSpecificOutput", {}))


class LintCliTests(unittest.TestCase):
    def _lint(self, text: str, *extra: str) -> subprocess.CompletedProcess:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "state.md"
            path.write_text(text, encoding="utf-8")
            return subprocess.run(
                [sys.executable, str(AD_LINT), str(path), "--quiet", *extra], capture_output=True, text=True,
            )

    def test_cli_reports_annotations_in_the_post_merge_qa_line_forms(self) -> None:
        for line in ANNOTATED_LIMIT_LINES:
            with self.subTest(line=line):
                self.assertIn("注記", self._lint(_state(line)).stdout)

    def test_hook_call_skips_human_evidence(self) -> None:
        """hook は Write・Edit・MultiEdit では書き込み後の全文で見るので、書き込み前のディスクを読む lint の分は出さない。"""
        result = self._lint(_state(ANNOTATED_LIMIT_LINES[0]), "--no-human-evidence")
        self.assertNotIn("human-evidence", result.stdout)


if __name__ == "__main__":
    unittest.main()
