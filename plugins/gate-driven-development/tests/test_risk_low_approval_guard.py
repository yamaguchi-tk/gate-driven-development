"""steering の書き込み hook が、`risk-low:` の human check の承認を、リスクの段が `低` の steering でだけ通すこと。

PR-4 で `Human Check Status=approved | evidence: risk-low:…` を human check を待たない根拠にする。記録を読み違えて
`risk-low:` を書く事故を、書く時点で止める。値だけを置換する Edit は追加分に欄名が出ないので、書き込み後の
state.md の値でも見る（PR #31 Finding C）。検査の層は `risk_tier.collect_risk_low_approval_violations` の docstring の 4 つ。
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from _paths import PLUGIN_ROOT

HOOK = PLUGIN_ROOT / "hooks" / "scripts" / "validate-steering-write.py"

PENDING = "pending | evidence: none | updated_by: main | updated_at: 2026-10-27T09:00:00+09:00"
RISK_LOW = "approved | evidence: risk-low:request-crosscheck.md | updated_by: main | updated_at: 2026-10-27T10:00:00+09:00"
HUMAN = "approved | evidence: human:PR 作成まで | updated_by: main | updated_at: 2026-10-27T10:00:00+09:00"


REQUEST = "<!-- gdd-request-capture:begin -->\n## ユーザーの発言\n\n> 依頼\n"


def _state(status: str) -> str:
    return (
        "# State\n\n## Gate Status\nStarted At: 2026-10-27T09:00:00+09:00\n"
        "- Resume From: human-check-waiting\n"
        f"- Human Check Status: {status}\n"
        "- Route In Progress: none\n"
    )


RECORDS = {
    "低": "### リスクの段\n\nリスクの段: 低\n- 根拠: 文書だけ\n",
    "高": "### リスクの段\n\nリスクの段: 高\n- 根拠: 認証・権限\n",
    "崩れ": "### リスクの段\n\n**リスクの段: 低**\n",
    "無し": None,
}


class RiskLowApprovalGuardTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        root = Path(self._tmp.name)
        self.steering = root / ".steering" / "task"
        self.steering.mkdir(parents=True)
        self.state = self.steering / "state.md"
        self.state.write_text(_state(PENDING), encoding="utf-8")
        (self.steering / "request.md").write_text(REQUEST, encoding="utf-8")
        self._state_dir = str(root / "hook-state")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _record(self, tier: str) -> None:
        path = self.steering / "request-crosscheck.md"
        if path.exists():
            path.unlink()
        if RECORDS[tier] is not None:
            path.write_text(RECORDS[tier], encoding="utf-8")

    def _run(self, tool_name: str, tool_input: dict) -> tuple[int, str]:
        env = dict(os.environ, GDD_HOOK_STATE_DIR=self._state_dir, CLAUDE_PLUGIN_ROOT=str(PLUGIN_ROOT))
        result = subprocess.run(
            [sys.executable, str(HOOK)],
            input=json.dumps({"tool_name": tool_name, "tool_input": tool_input}),
            env=env, capture_output=True, text=True, timeout=30,
        )
        out = result.stdout + result.stderr
        denied = '"permissionDecision": "deny"' in out
        for stream in (result.stdout, result.stderr):
            try:
                out += json.dumps(json.loads(stream), ensure_ascii=False)
            except ValueError:
                pass
        if result.returncode not in (0, 2):
            self.fail(out)
        return (2 if denied else 0), out

    def _writes(self, status_line_value: str) -> dict[str, tuple[str, dict]]:
        line_old = f"- Human Check Status: {PENDING}"
        line_new = f"- Human Check Status: {status_line_value}"
        patch = (
            "*** Begin Patch\n"
            f"*** Update File: {self.state}\n"
            "@@\n"
            f"-{line_old}\n"
            f"+{line_new}\n"
            "*** End Patch\n"
        )
        return {
            "Write": ("Write", {"file_path": str(self.state), "content": _state(status_line_value)}),
            "Edit の行": ("Edit", {"file_path": str(self.state), "old_string": line_old, "new_string": line_new}),
            "Edit の値だけ": ("Edit", {"file_path": str(self.state), "old_string": PENDING, "new_string": status_line_value}),
            "MultiEdit の値だけ": ("MultiEdit", {
                "file_path": str(self.state), "edits": [{"old_string": PENDING, "new_string": status_line_value}],
            }),
            "ApplyPatch": ("ApplyPatch", {"patch": patch}),
        }

    def test_risk_low_approval_passes_only_when_the_record_reads_low(self) -> None:
        for tier in RECORDS:
            for name, (tool, tool_input) in self._writes(RISK_LOW).items():
                with self.subTest(tier=tier, write=name):
                    self._record(tier)
                    self.state.write_text(_state(PENDING), encoding="utf-8")
                    rc, out = self._run(tool, tool_input)
                    if tier == "低":
                        self.assertEqual(rc, 0, out)
                        self.assertNotIn("risk_low", out)
                        self.assertNotIn("リスクの段", out)
                    else:
                        self.assertEqual(rc, 2, out)
                        self.assertIn("リスクの段", out)

    def test_risk_low_is_stopped_unless_request_md_starts_with_the_hook_section(self) -> None:
        # state.md の Created In Session の有無によらない（runner が書き漏らした形と、欄を消してから risk-low を足す形）
        self._record("低")
        tool, base = self._writes(RISK_LOW)["Write"]
        path = self.steering / "request.md"
        for field in ("", "- Created In Session: s1\n"):
            tool_input = dict(base, content=base["content"] + field)
            for request in ("<!-- gdd-request-capture:not-copied -->\n## hook は依頼の原文を写していない\n", None,
                            "# 依頼の原文\n\nmain が書いた依頼の要約\n"):
                with self.subTest(field=field, request=request):
                    self.state.write_text(_state(PENDING) + field, encoding="utf-8")
                    path.unlink(missing_ok=True)
                    if request is not None:
                        path.write_text(request, encoding="utf-8")
                    rc, out = self._run(tool, tool_input)
                    self.assertEqual(rc, 2, out)
                    self.assertIn("request.md", out)
            with self.subTest(field=field, request="hook の節"):
                path.write_text(REQUEST, encoding="utf-8")
                rc, out = self._run(tool, tool_input)
                self.assertEqual(rc, 0, out)

    def test_spelling_variants_and_other_statuses_are_also_stopped(self) -> None:
        self._record("高")
        variants = [
            RISK_LOW.replace("risk-low", "Risk-Low"),
            RISK_LOW.replace("risk-low", "risk_low"),
            RISK_LOW.replace("risk-low", "risk low"),
            RISK_LOW.replace("evidence: risk-low:request-crosscheck.md", "evidence: `risk-low:request-crosscheck.md`"),
            RISK_LOW.replace("approved", "pending"),
            RISK_LOW.replace("risk-low", "ｒｉｓｋ－ｌｏｗ"),
            RISK_LOW.replace("risk-low", "risk\u2010low"),
            RISK_LOW.replace("risk-low:", "risk:low:"),
        ]
        for value in variants:
            for name, (tool, tool_input) in self._writes(value).items():
                with self.subTest(value=value, write=name):
                    self.state.write_text(_state(PENDING), encoding="utf-8")
                    rc, out = self._run(tool, tool_input)
                    self.assertEqual(rc, 2, out)

    def test_human_approval_and_other_files_are_not_stopped(self) -> None:
        self._record("高")
        for name, (tool, tool_input) in self._writes(HUMAN).items():
            with self.subTest(write=name):
                self.state.write_text(_state(PENDING), encoding="utf-8")
                rc, out = self._run(tool, tool_input)
                self.assertEqual(rc, 0, out)
                self.assertNotIn("リスクの段", out)
        worklog = self.steering / "worklog.md"
        rc, out = self._run("Write", {"file_path": str(worklog), "content": f"- Human Check Status: {RISK_LOW}\n"})
        self.assertEqual(rc, 0, out)
        self.assertNotIn("リスクの段", out)

    def test_risk_low_anywhere_in_a_write_that_touches_state_md_is_stopped(self) -> None:
        self._record("高")
        rc, out = self._run("Edit", {
            "file_path": str(self.state),
            "old_string": "- Route In Progress: none",
            "new_string": "- Route In Progress: none\n- メモ: 次は risk-low で進める",
        })
        self.assertEqual(rc, 2, out)
        worklog = self.steering / "worklog.md"
        patch = (
            "*** Begin Patch\n"
            f"*** Add File: {worklog}\n"
            f"+- Human Check Status: {RISK_LOW}\n"
            f"*** Update File: {self.state}\n"
            "@@\n"
            "-- Route In Progress: none\n"
            "+- Route In Progress: none\n"
            "*** End Patch\n"
        )
        rc, out = self._run("ApplyPatch", {"patch": patch})
        self.assertEqual(rc, 2, out)

    def test_apply_patch_line_outside_any_file_section_is_stopped(self) -> None:
        self._record("高")
        patch = (
            "*** Begin Patch\n"
            f"*** Update File: {self.state}\n"
            "@@\n"
            f"-- Human Check Status: {PENDING}\n"
            "*** End Patch\n"
            f"+- Human Check Status: {RISK_LOW}\n"
            "*** End Patch\n"
        )
        rc, out = self._run("ApplyPatch", {"patch": patch})
        self.assertEqual(rc, 2, out)
        self.assertIn("リスクの段", out)

    def test_unrelated_edit_on_a_state_that_already_has_the_approval_passes(self) -> None:
        self._record("高")
        self.state.write_text(_state(RISK_LOW), encoding="utf-8")
        rc, out = self._run("Edit", {
            "file_path": str(self.state), "old_string": "- Route In Progress: none", "new_string": "- Route In Progress: none\n",
        })
        self.assertEqual(rc, 0, out)
        self.assertNotIn("リスクの段", out)

    def test_edit_whose_old_string_misses_is_stopped_when_it_writes_risk_low(self) -> None:
        self._record("高")
        rc, out = self._run("Edit", {
            "file_path": str(self.state), "old_string": "pending | evidence: none  ", "new_string": RISK_LOW,
        })
        self.assertEqual(rc, 2, out)

    def test_risk_low_split_across_edits_is_stopped_by_the_written_text(self) -> None:
        self._record("高")
        cases = {
            "MultiEdit の 2 つの edit": ("MultiEdit", {"file_path": str(self.state), "edits": [
                {"old_string": "evidence: none", "new_string": "evidence: risk"},
                {"old_string": " | updated_by: main", "new_string": "-low:x | updated_by: main"},
            ]}, _state(PENDING)),
            "2 回目の Edit": ("Edit", {
                "file_path": str(self.state), "old_string": " | updated_by: main", "new_string": "-low:x | updated_by: main",
            }, _state(PENDING.replace("evidence: none", "evidence: risk"))),
            "数が同じまま入れ替わる": ("MultiEdit", {"file_path": str(self.state), "edits": [
                {"old_string": "メモ: risk-low は使わない", "new_string": "メモ: 使わない"},
                {"old_string": "evidence: none", "new_string": "evidence: risk"},
                {"old_string": " | updated_by: main", "new_string": "-low:x | updated_by: main"},
            ]}, _state(PENDING) + "- メモ: risk-low は使わない\n"),
            # 追加分をつないでも `risk-low` にならない順。書き込み後の全文を見る層だけが止める
            "つないでも現れない順の 2 つの edit": ("MultiEdit", {"file_path": str(self.state), "edits": [
                {"old_string": " | updated_by: main", "new_string": "-low:x | updated_by: main"},
                {"old_string": "evidence: none", "new_string": "evidence: risk"},
            ]}, _state(PENDING)),
            "つないでも現れない順で、数が同じまま入れ替わる": ("MultiEdit", {"file_path": str(self.state), "edits": [
                {"old_string": " | updated_by: main", "new_string": "-low:x | updated_by: main"},
                {"old_string": "メモ: risk-low は使わない", "new_string": "メモ: 使わない"},
                {"old_string": "evidence: none", "new_string": "evidence: risk"},
            ]}, _state(PENDING) + "- メモ: risk-low は使わない\n"),
            "改行ごと消える Edit": ("Edit", {"file_path": str(self.state), "old_string": "QQ", "new_string": ""},
                                     _state(PENDING.replace("evidence: none", "evidence: risQQ\nk-low:x"))),
        }
        for name, (tool, tool_input, before) in cases.items():
            with self.subTest(name):
                self.state.write_text(before, encoding="utf-8")
                rc, out = self._run(tool, tool_input)
                self.assertEqual(rc, 2, out)
                self.assertIn("リスクの段", out)

    def test_edit_that_cannot_be_applied_as_written_is_stopped_on_an_existing_state(self) -> None:
        cases = {
            "old_string が無い（ツールは引用符を正規化して当てるかもしれない）": (
                {"old_string": "“none”", "new_string": "x"}, _state(PENDING)),
            "replace_all で改行ごと消える": (
                {"old_string": "QQ", "new_string": "", "replace_all": True},
                _state(PENDING.replace("evidence: none", "evidence: risQQ\nk-low:x")) + "- メモ: QQ\n"),
        }
        for tier in ("高", "無し", "低"):
            for name, (edit, before) in cases.items():
                with self.subTest(tier=tier, case=name):
                    self._record(tier)
                    self.state.write_text(before, encoding="utf-8")
                    rc, out = self._run("Edit", {"file_path": str(self.state), **edit})
                    if tier == "低":
                        self.assertEqual(rc, 0, out)
                        self.assertNotIn("リスクの段", out)
                    else:
                        self.assertEqual(rc, 2, out)
                        self.assertIn("リスクの段", out)

    def test_edit_on_a_missing_state_is_not_stopped_by_this_check(self) -> None:
        self._record("高")
        self.state.unlink()
        rc, out = self._run("Edit", {"file_path": str(self.state), "old_string": "none", "new_string": "x"})
        self.assertEqual(rc, 0, out)
        self.assertNotIn("リスクの段", out)

    def test_risk_low_split_across_added_chunks_is_stopped(self) -> None:
        self._record("高")
        rc, out = self._run("MultiEdit", {"file_path": str(self.state), "edits": [
            {"old_string": "evidence: none", "new_string": "evidence: ris"},
            {"old_string": "- Route In Progress: none", "new_string": "k-low\n- Route In Progress: none"},
        ]})
        self.assertEqual(rc, 2, out)
        self.assertIn("リスクの段", out)

    def test_split_written_text_passes_when_the_record_reads_low(self) -> None:
        self._record("低")
        rc, out = self._run("MultiEdit", {"file_path": str(self.state), "edits": [
            {"old_string": "evidence: none", "new_string": "evidence: risk"},
            {"old_string": " | updated_by: main", "new_string": "-low:x | updated_by: main"},
        ]})
        self.assertEqual(rc, 0, out)
        self.assertNotIn("リスクの段", out)

    def test_apply_patch_line_starting_with_plus_plus_is_stopped(self) -> None:
        self._record("高")
        patch = (
            "*** Begin Patch\n"
            f"*** Update File: {self.state}\n"
            "@@\n"
            "-- Route In Progress: none\n"
            "+++ evidence: risk-low:x\n"
            "*** End Patch\n"
        )
        rc, out = self._run("ApplyPatch", {"patch": patch})
        self.assertEqual(rc, 2, out)
        self.assertIn("リスクの段", out)

    def test_the_stop_is_not_demoted_after_repeated_denies(self) -> None:
        self._record("高")
        tool, tool_input = self._writes(RISK_LOW)["Edit の値だけ"]
        for attempt in range(5):
            with self.subTest(attempt=attempt):
                rc, out = self._run(tool, tool_input)
                self.assertEqual(rc, 2, out)

    def test_crlf_state_passes_edits_that_keep_the_existing_approval(self) -> None:
        # 全文の Write は既にある `risk-low` の行も追加分に入るので、改行によらず追加分の層が止める
        self._record("高")
        crlf = _state(RISK_LOW).replace("\n", "\r\n")
        cases = {
            "CRLF の state.md への無関係な Edit": ("Edit", {
                "file_path": str(self.state), "old_string": "- Route In Progress: none", "new_string": "- Route In Progress: x",
            }, crlf),
            "CR だけの state.md への無関係な Edit": ("Edit", {
                "file_path": str(self.state), "old_string": "- Route In Progress: none", "new_string": "- Route In Progress: x",
            }, _state(RISK_LOW).replace("\n", "\r")),
        }
        for name, (tool, tool_input, before) in cases.items():
            with self.subTest(name):
                self.state.write_bytes(before.encode("utf-8"))
                rc, out = self._run(tool, tool_input)
                self.assertEqual(rc, 0, out)
                self.assertNotIn("リスクの段", out)

    def test_crlf_state_still_stops_a_new_risk_low_line(self) -> None:
        # 改行をそろえても、新しく現れた `risk-low` の行は止まる（fail-open にしない）
        self._record("高")
        crlf = _state(PENDING).replace("\n", "\r\n")
        cases = {
            "つないでも現れない順の 2 つの edit": ("MultiEdit", {"file_path": str(self.state), "edits": [
                {"old_string": " | updated_by: main", "new_string": "-low:x | updated_by: main"},
                {"old_string": "evidence: none", "new_string": "evidence: risk"},
            ]}),
            "CRLF の全文の Write": ("Write", {"file_path": str(self.state), "content": _state(RISK_LOW).replace("\n", "\r\n")}),
        }
        for name, (tool, tool_input) in cases.items():
            with self.subTest(name):
                self.state.write_bytes(crlf.encode("utf-8"))
                rc, out = self._run(tool, tool_input)
                self.assertEqual(rc, 2, out)
                self.assertIn("リスクの段", out)

    def test_undecodable_crlf_state_does_not_crash_the_guard(self) -> None:
        # 例外で guard 全体が落ちない（落ちると fail-closed の別の deny になり、この検査の Why が出ない）
        self._record("高")
        self.state.write_bytes(_state(RISK_LOW).replace("\n", "\r\n").encode("utf-8") + b"- \xff\xfe\r\n")
        rc, out = self._run("Edit", {
            "file_path": str(self.state), "old_string": "- Route In Progress: none", "new_string": "- Route In Progress: x",
        })
        self.assertEqual(rc, 0, out)

    def test_state_under_a_directory_without_permission_is_stopped(self) -> None:
        # 判定できないときは止める（`os.path.lexists` は EACCES を「無い」にする）
        self._record("高")
        os.chmod(self.steering, 0)
        try:
            if os.access(self.state, os.F_OK):
                self.skipTest("権限で読めなくならない環境（root など）")
            rc, out = self._run("Edit", {
                "file_path": str(self.state), "old_string": "- Route In Progress: none", "new_string": "- Route In Progress: x",
            })
        finally:
            os.chmod(self.steering, 0o755)
        self.assertEqual(rc, 2, out)
        self.assertIn("リスクの段", out)

    def test_apply_patch_that_moves_a_file_onto_state_md_is_stopped(self) -> None:
        # move の移動元の中身はこの検査が読まず、`Origin Session` の検査が state.md への move ごと止める
        self._record("高")
        source = self.steering / "worklog.md"
        source.write_text(_state(RISK_LOW), encoding="utf-8")
        self.state.unlink()
        patch = (
            "*** Begin Patch\n"
            f"*** Update File: {source}\n"
            f"*** Move to: {self.state}\n"
            "@@\n"
            "-- Route In Progress: none\n"
            "+- Route In Progress: x\n"
            "*** End Patch\n"
        )
        rc, out = self._run("ApplyPatch", {"patch": patch})
        self.assertEqual(rc, 2, out)


if __name__ == "__main__":
    unittest.main()
