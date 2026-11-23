"""peer turn と `Origin Session` の境界を、実 hook の stdin 経路（subprocess で起動した `main()`）で固定する。

`test_peer_turn_write_boundary_contract.py` から分けた。transcript の fixture（`PEER_RECORD` など）は元のファイルに置いたまま、名前だけを import する。
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from _paths import PLUGIN_ROOT as ROOT
from test_peer_turn_write_boundary_contract import HUMAN_RECORD, PEER_RECORD, write_transcript


class TestPeerTurnMainWiringEndToEnd(unittest.TestCase):
    """implementation-reviewer High 2 是正: collect_peer_turn_state_write_violations()
    単体呼び出しだけでなく、実 hook stdin 経路（subprocess 経由の main()）で
    deny/allow 配線そのものを固定する。`reasons.extend(...)` の呼び出しが
    main() から消えても検知できるように、既存 test_validate_steering_write.py
    の subprocess パターンを踏襲する。
    """

    def setUp(self) -> None:
        self._state_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self._state_dir, ignore_errors=True)
        self._tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self._tmp, ignore_errors=True)
        self.transcript_path = Path(self._tmp) / "transcript.jsonl"
        self.state_path = Path(self._tmp) / ".steering" / "20260903-x" / "state.md"
        self.state_path.parent.mkdir(parents=True)
        self.state_path.write_text(
            "Started At: 2026-09-03T00:00:00Z\n"
            "- Resume From: gdd-implementation-gating\n"
            "- Human Check Status: pending\n"
            "- Route In Progress: none\n",
            encoding="utf-8",
        )

    def _run(self, new_string: str) -> subprocess.CompletedProcess[str]:
        env = dict(os.environ)
        env["GDD_HOOK_STATE_DIR"] = self._state_dir
        payload = {
            "tool_name": "Edit",
            "tool_input": {"file_path": str(self.state_path), "new_string": new_string},
            "transcript_path": str(self.transcript_path),
        }
        script = ROOT / "hooks" / "scripts" / "validate-steering-write.py"
        return subprocess.run(
            [sys.executable, str(script)],
            input=json.dumps(payload),
            env=env,
            capture_output=True,
            text=True,
        )

    def test_peer_turn_approval_write_is_denied_via_main(self) -> None:
        write_transcript(self.transcript_path, [PEER_RECORD])
        result = self._run("- Human Check Status: approved\n")
        self.assertEqual(result.returncode, 2, result.stderr)
        message = json.loads(result.stderr)["systemMessage"]
        self.assertIn("別セッションからのメッセージ", message)

    def test_non_peer_turn_approval_write_is_allowed_via_main(self) -> None:
        write_transcript(self.transcript_path, [HUMAN_RECORD])
        result = self._run("- Human Check Status: approved\n")
        self.assertEqual(result.returncode, 0, result.stderr)


class _PeerTurnStateEditFixture(unittest.TestCase):
    """state.md への Edit を、実 hook（validate-steering-write.py の main）に通す fixture。"""

    BASE_STATE = (
        "Started At: 2026-09-03T00:00:00Z\n"
        "- Resume From: gdd-implementation-gating\n"
        "- Human Check Status: pending\n"
        "- Route In Progress: none\n"
    )

    def setUp(self) -> None:
        self._state_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self._state_dir, ignore_errors=True)
        self._tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self._tmp, ignore_errors=True)
        self.transcript_path = Path(self._tmp) / "transcript.jsonl"
        self.state_path = Path(self._tmp) / ".steering" / "20260903-x" / "state.md"
        self.state_path.parent.mkdir(parents=True)

    def _run(self, existing: str, tool_input: dict) -> subprocess.CompletedProcess[str]:
        self.state_path.write_text(existing, encoding="utf-8")
        env = dict(os.environ)
        env["GDD_HOOK_STATE_DIR"] = self._state_dir
        payload = {
            "tool_name": "Edit",
            "tool_input": {"file_path": str(self.state_path), **tool_input},
            "transcript_path": str(self.transcript_path),
        }
        script = ROOT / "hooks" / "scripts" / "validate-steering-write.py"
        return subprocess.run(
            [sys.executable, str(script)],
            input=json.dumps(payload),
            env=env,
            capture_output=True,
            text=True,
        )


class TestPeerTurnValueOnlyEditBypassEndToEnd(_PeerTurnStateEditFixture):
    """pr-review 是正 (Finding C): 検査対象が chunk（追加文字列）だけだと、
    値のみを置換する Edit（`old_string="pending"` / `new_string="approved"`）は
    field 名が chunk に現れないため境界を素通りする。書込み後テキストを
    再構成して field 値で判定する。
    """

    def test_value_only_approval_edit_is_denied_on_peer_turn(self) -> None:
        write_transcript(self.transcript_path, [PEER_RECORD])
        result = self._run(
            self.BASE_STATE, {"old_string": "pending", "new_string": "approved"}
        )
        self.assertEqual(result.returncode, 2, result.stdout)
        self.assertIn("別セッションからのメッセージ", json.loads(result.stderr)["systemMessage"])

    def test_value_only_cancellation_edit_is_denied_on_peer_turn(self) -> None:
        write_transcript(self.transcript_path, [PEER_RECORD])
        result = self._run(
            self.BASE_STATE + "- Next Action: gdd-completion-check\n",
            {"old_string": "gdd-completion-check", "new_string": "cancelled"},
        )
        self.assertEqual(result.returncode, 2, result.stdout)

    def test_value_only_resume_from_cancel_or_done_edit_is_denied_on_peer_turn(self) -> None:
        """block すべき入力: 値だけを置換する Edit で `Resume From` を cancelled・done にさせない
        （binding 先が pre-push・merge・pre-PR gate の検査から外れる）。"""
        for new in ("cancelled", "cancelled | superseded-by: 20260930-x", "done"):
            with self.subTest(new=new):
                write_transcript(self.transcript_path, [PEER_RECORD])
                result = self._run(
                    self.BASE_STATE, {"old_string": "gdd-implementation-gating", "new_string": new}
                )
                self.assertEqual(result.returncode, 2, result.stdout)
                self.assertIn("別セッションからのメッセージ", json.loads(result.stderr)["systemMessage"])

    def test_unencodable_transcript_path_is_treated_as_peer_turn_for_resume_from_cancel(self) -> None:
        """例外で guard が落ちない: transcript のパスを開けず ValueError になる（NUL を含む）と、
        peer turn とみなして止める。"""
        self.transcript_path = Path(str(self.transcript_path) + "\x00")
        result = self._run(
            self.BASE_STATE, {"old_string": "gdd-implementation-gating", "new_string": "cancelled"}
        )
        self.assertEqual(result.returncode, 2, result.stdout)
        self.assertIn("別セッションからのメッセージ", json.loads(result.stderr)["systemMessage"])

    def _run_payload(self, tool_name: str, tool_input: dict, extra_env: dict | None = None):
        env = dict(os.environ)
        env["GDD_HOOK_STATE_DIR"] = self._state_dir
        env.update(extra_env or {})
        payload = {
            "tool_name": tool_name,
            "tool_input": {"file_path": str(self.state_path), **tool_input},
            "transcript_path": str(self.transcript_path),
        }
        return subprocess.run(
            [sys.executable, str(ROOT / "hooks" / "scripts" / "validate-steering-write.py")],
            input=json.dumps(payload), env=env, capture_output=True, text=True,
        )

    def test_decoy_line_does_not_hide_the_value_the_gate_reads(self) -> None:
        """block すべき入力: guard には見えて gate（gdd_extract_doc_field）には見えない囮の行を先に足して
        おき、本物の値だけを置換する Edit でも、gate が読む値で比べて止める。"""
        cases = {
            "resume-space": ("Resume From : gdd-implementation-gating\n", "gdd-implementation-gating\n- Human Check Status", "cancelled\n- Human Check Status"),
            "resume-vt": ("note\x0bResume From: gdd-implementation-gating\n", "gdd-implementation-gating\n- Human Check Status", "done\n- Human Check Status"),
            "human-space": ("Human Check Status : pending\n", "pending\n- Route", "approved\n- Route"),
        }
        for name, (decoy, old, new) in cases.items():
            with self.subTest(name=name):
                write_transcript(self.transcript_path, [PEER_RECORD])
                result = self._run(decoy + self.BASE_STATE, {"old_string": old, "new_string": new})
                self.assertEqual(result.returncode, 2, result.stdout)
                self.assertIn("別セッションからのメッセージ", json.loads(result.stderr)["systemMessage"])

    def test_approval_with_a_trailing_note_is_denied_on_peer_turn(self) -> None:
        """block すべき入力: `approved later` も gate は approved と読む（最初の空白まで）。"""
        write_transcript(self.transcript_path, [PEER_RECORD])
        result = self._run(self.BASE_STATE, {"old_string": "pending", "new_string": "approved later"})
        self.assertEqual(result.returncode, 2, result.stdout)

    def test_dict_edits_value_only_cancel_is_denied_on_peer_turn(self) -> None:
        """block すべき入力: MultiEdit の `edits` が dict でも、書き込み後の値で比べる。"""
        write_transcript(self.transcript_path, [PEER_RECORD])
        self.state_path.write_text(self.BASE_STATE, encoding="utf-8")
        result = self._run_payload("MultiEdit", {
            "edits": {"old_string": "gdd-implementation-gating", "new_string": "cancelled"},
        })
        self.assertEqual(result.returncode, 2, result.stdout)

    def test_reader_unavailable_denies_on_peer_turn(self) -> None:
        """判定できないときに通さない: gate の reader（bash）を起動できなければ、peer turn の
        state.md の書き込みを止める。"""
        write_transcript(self.transcript_path, [PEER_RECORD])
        self.state_path.write_text(self.BASE_STATE, encoding="utf-8")
        result = self._run_payload(
            "Edit", {"old_string": "Route In Progress: none", "new_string": "Route In Progress: none "},
            extra_env={"PATH": str(Path(self._state_dir) / "no-bin")},
        )
        self.assertEqual(result.returncode, 2, result.stdout)
        self.assertIn("別セッションからのメッセージ", json.loads(result.stderr)["systemMessage"])

    def test_decoy_edit_is_allowed_on_human_turn(self) -> None:
        write_transcript(self.transcript_path, [HUMAN_RECORD])
        result = self._run(
            "Resume From : gdd-implementation-gating\n" + self.BASE_STATE,
            {"old_string": "gdd-implementation-gating\n- Human Check Status", "new_string": "cancelled\n- Human Check Status"},
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_value_only_merge_approval_edit_is_denied_on_peer_turn(self) -> None:
        write_transcript(self.transcript_path, [PEER_RECORD])
        result = self._run(
            self.BASE_STATE + "- Merge Approval: not-yet\n",
            {"old_string": "not-yet", "new_string": "PR #1 / head deadbeef"},
        )
        self.assertEqual(result.returncode, 2, result.stdout)

    def test_multiedit_value_only_approval_is_denied_on_peer_turn(self) -> None:
        write_transcript(self.transcript_path, [PEER_RECORD])
        self.state_path.write_text(self.BASE_STATE, encoding="utf-8")
        env = dict(os.environ)
        env["GDD_HOOK_STATE_DIR"] = self._state_dir
        payload = {
            "tool_name": "MultiEdit",
            "tool_input": {
                "file_path": str(self.state_path),
                "edits": [
                    {"old_string": "gdd-implementation-gating", "new_string": "gdd-completion-check"},
                    {"old_string": "pending", "new_string": "approved"},
                ],
            },
            "transcript_path": str(self.transcript_path),
        }
        result = subprocess.run(
            [sys.executable, str(ROOT / "hooks" / "scripts" / "validate-steering-write.py")],
            input=json.dumps(payload),
            env=env,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 2, result.stdout)

    def test_value_only_approval_edit_is_allowed_on_human_turn(self) -> None:
        write_transcript(self.transcript_path, [HUMAN_RECORD])
        result = self._run(
            self.BASE_STATE, {"old_string": "pending", "new_string": "approved"}
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_value_only_cancellation_edit_on_tasklist_is_denied_on_peer_turn(self) -> None:
        """pr-review 是正 (Finding S): `Next Action` の正本は tasklist.md にもある
        （`detect-steering.sh:gdd_validate_active_state_fields` は tasklist.md →
        state.md の順に読む）。層 2 を state.md 限定にしていたため、tasklist.md 側で
        値だけを `cancelled` へ置換する Edit が peer turn 中でも通っていた。
        """
        write_transcript(self.transcript_path, [PEER_RECORD])
        tasklist_path = self.state_path.parent / "tasklist.md"
        tasklist_path.write_text("- Next Action: gdd-completion-check\n", encoding="utf-8")
        env = dict(os.environ)
        env["GDD_HOOK_STATE_DIR"] = self._state_dir
        payload = {
            "tool_name": "Edit",
            "tool_input": {
                "file_path": str(tasklist_path),
                "old_string": "gdd-completion-check",
                "new_string": "cancelled",
            },
            "transcript_path": str(self.transcript_path),
        }
        result = subprocess.run(
            [sys.executable, str(ROOT / "hooks" / "scripts" / "validate-steering-write.py")],
            input=json.dumps(payload),
            env=env,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 2, result.stdout)
        self.assertIn("別セッションからのメッセージ", json.loads(result.stderr)["systemMessage"])

    def test_value_only_cancellation_edit_on_tasklist_is_allowed_on_human_turn(self) -> None:
        """false positive ガード: 人間本人のターンなら tasklist.md の同じ編集は通す。"""
        write_transcript(self.transcript_path, [HUMAN_RECORD])
        tasklist_path = self.state_path.parent / "tasklist.md"
        tasklist_path.write_text("- Next Action: gdd-completion-check\n", encoding="utf-8")
        env = dict(os.environ)
        env["GDD_HOOK_STATE_DIR"] = self._state_dir
        payload = {
            "tool_name": "Edit",
            "tool_input": {
                "file_path": str(tasklist_path),
                "old_string": "gdd-completion-check",
                "new_string": "cancelled",
            },
            "transcript_path": str(self.transcript_path),
        }
        result = subprocess.run(
            [sys.executable, str(ROOT / "hooks" / "scripts" / "validate-steering-write.py")],
            input=json.dumps(payload),
            env=env,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_unrelated_tasklist_edit_is_allowed_on_peer_turn(self) -> None:
        """false positive ガード: tasklist.md の `Next Action` 以外の値置換は
        peer turn でも通す（対象 field は read 側の正本に合わせて絞る）。
        """
        write_transcript(self.transcript_path, [PEER_RECORD])
        tasklist_path = self.state_path.parent / "tasklist.md"
        tasklist_path.write_text(
            "- Next Action: gdd-completion-check\n- Owner: main-session\n", encoding="utf-8"
        )
        env = dict(os.environ)
        env["GDD_HOOK_STATE_DIR"] = self._state_dir
        payload = {
            "tool_name": "Edit",
            "tool_input": {
                "file_path": str(tasklist_path),
                "old_string": "main-session",
                "new_string": "worker-1",
            },
            "transcript_path": str(self.transcript_path),
        }
        result = subprocess.run(
            [sys.executable, str(ROOT / "hooks" / "scripts" / "validate-steering-write.py")],
            input=json.dumps(payload),
            env=env,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_unrelated_edit_on_already_approved_state_is_allowed_on_peer_turn(self) -> None:
        """false positive ガード: 既に `approved` が記録済みの state.md に対する
        無関係な Edit まで落とすと、peer turn 中の通常運用が全部止まる。
        deny するのは「この書込みで値が変わる」ときだけ。
        """
        write_transcript(self.transcript_path, [PEER_RECORD])
        result = self._run(
            self.BASE_STATE.replace("Human Check Status: pending", "Human Check Status: approved"),
            {"old_string": "- Route In Progress: none", "new_string": "- Route In Progress: pr_review"},
        )
        self.assertEqual(result.returncode, 0, result.stderr)


class TestApplyPatchLineBreakEndToEnd(unittest.TestCase):
    """独立-1 F1・F8: hook は patch を `str.splitlines()` で行に割るので、`\v`・`\f`・単独の `\r` などで
    field の行が追加行から落ちる。gate の reader（awk）はこれらで行を割らず、`- ` の後の空白として読む。
    peer turn の記録（F1）も `Origin Session` の write-once（F8）も、実 hook の stdin 経路で止めることを固定する。
    """

    def setUp(self) -> None:
        self._state_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self._state_dir, ignore_errors=True)
        self._tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self._tmp, ignore_errors=True)
        self.transcript_path = Path(self._tmp) / "transcript.jsonl"
        self.state_path = Path(self._tmp) / ".steering" / "20260903-x" / "state.md"
        self.state_path.parent.mkdir(parents=True)
        self.state_path.write_text(
            "Started At: 2026-09-03T00:00:00Z\n"
            "- Resume From: gdd-implementation-gating\n"
            "- Human Check Status: pending\n"
            "- Route In Progress: none\n"
            "- Origin Session: sess-origin\n",
            encoding="utf-8",
        )

    def _run_patch(self, added: str) -> subprocess.CompletedProcess[str]:
        patch = (
            f"*** Begin Patch\n*** Update File: {self.state_path}\n@@\n"
            f"+{added}\n - Resume From: gdd-implementation-gating\n*** End Patch\n"
        )
        env = dict(os.environ)
        env["GDD_HOOK_STATE_DIR"] = self._state_dir
        payload = {"tool_name": "ApplyPatch", "tool_input": {"patch": patch}, "transcript_path": str(self.transcript_path)}
        return subprocess.run(
            [sys.executable, str(ROOT / "hooks" / "scripts" / "validate-steering-write.py")],
            input=json.dumps(payload), env=env, capture_output=True, text=True,
        )

    def test_peer_turn_records_hidden_by_line_breaks_are_denied(self) -> None:
        """block すべき入力: peer turn の ApplyPatch で、行区切り文字の後ろに記録を隠す。素の形も止める。"""
        cases = {
            "plain": "- Resume From: cancelled",
            "vt-before-field": "-\x0bResume From: cancelled",
            "vt-before-value": "- Resume From:\x0bcancelled",
            "ff": "-\x0cResume From: cancelled",
            "lone-cr": "-\rResume From: cancelled",
            "ls-approval": "-\u2028Human Check Status: approved",
        }
        write_transcript(self.transcript_path, [PEER_RECORD])
        for name, added in cases.items():
            with self.subTest(name=name):
                result = self._run_patch(added)
                self.assertEqual(result.returncode, 2, result.stdout)
                message = json.loads(result.stderr)["systemMessage"]
                self.assertNotIn("internal error", message)
                expected = "別セッションからのメッセージ" if name == "plain" else "行区切り文字"
                self.assertIn(expected, message)

    def test_origin_session_hidden_by_line_breaks_is_denied_on_human_turn(self) -> None:
        """block すべき入力: 本人のターンでも、行区切り文字で隠した `Origin Session` の書き換えは止める。
        偽の header で別のファイルの行に見せる形も含む。"""
        write_transcript(self.transcript_path, [HUMAN_RECORD])
        cases = {
            "vt": "-\x0bOrigin Session: sess-attacker",
            "fake-header": "x\x0b*** Update File: other.md\n+- Origin Session: sess-attacker",
        }
        for name, added in cases.items():
            with self.subTest(name=name):
                result = self._run_patch(added)
                self.assertEqual(result.returncode, 2, result.stdout)
                self.assertIn("行区切り文字", json.loads(result.stderr)["systemMessage"])

    def test_ordinary_patch_is_allowed_on_human_turn(self) -> None:
        """本人のターンの通常の ApplyPatch（CRLF の行末を含む）は通す。"""
        write_transcript(self.transcript_path, [HUMAN_RECORD])
        # 既存の Origin Session がある state.md への ApplyPatch は、値によらず止まる
        self.state_path.write_text(self.state_path.read_text(encoding="utf-8").replace("- Origin Session: sess-origin\n", ""), encoding="utf-8")
        for name, added in {"lf": "- Resume From: cancelled", "crlf": "- Next Action: cancelled\r"}.items():
            with self.subTest(name=name):
                result = self._run_patch(added)
                self.assertEqual(result.returncode, 0, result.stderr)


class TestEditLineBreakAndMissedOldStringEndToEnd(unittest.TestCase):
    """独立-2 G1・G2 と、`Origin Session` の `\\v` の形。hook は既存の state.md を universal newlines で読み、
    値を python の規則（`splitlines()` 系）でも読むので、`\\r`・`\\v` などで行が gate の reader（LF だけで
    割る）とずれる。Write・Edit・MultiEdit の中身に行区切り文字があればターンを問わず止め、`old_string` が
    射影で見つからない Edit は、peer turn の記録と `Origin Session` のある state.md では止める。
    """

    BASE_STATE = (
        "Started At: 2026-09-03T00:00:00Z\n"
        "- Resume From: gdd-implementation-gating\n"
        "- Human Check Status: pending\n"
        "- Route In Progress: none\n"
        "- Origin Session: sess-origin\n"
    )

    def setUp(self) -> None:
        self._state_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self._state_dir, ignore_errors=True)
        self._tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self._tmp, ignore_errors=True)
        self.transcript_path = Path(self._tmp) / "transcript.jsonl"
        self.state_path = Path(self._tmp) / ".steering" / "20260903-x" / "state.md"
        self.state_path.parent.mkdir(parents=True)
        self.state_path.write_text(self.BASE_STATE, encoding="utf-8")

    def _run(self, tool_name: str, tool_input: dict) -> subprocess.CompletedProcess[str]:
        env = dict(os.environ)
        env["GDD_HOOK_STATE_DIR"] = self._state_dir
        payload = {
            "tool_name": tool_name,
            "tool_input": {"file_path": str(self.state_path), **tool_input},
            "transcript_path": str(self.transcript_path),
        }
        return subprocess.run(
            [sys.executable, str(ROOT / "hooks" / "scripts" / "validate-steering-write.py")],
            input=json.dumps(payload), env=env, capture_output=True, text=True,
        )

    def _assert_denied(self, result: subprocess.CompletedProcess[str], expected: str) -> None:
        self.assertEqual(result.returncode, 2, result.stdout)
        message = json.loads(result.stderr)["systemMessage"]
        self.assertNotIn("internal error", message)
        self.assertIn(expected, message)

    def test_line_breaks_in_edit_or_write_are_denied_on_human_turn(self) -> None:
        """block すべき入力: 本人のターンでも、Write・Edit・MultiEdit の中身の行区切り文字は止める。"""
        write_transcript(self.transcript_path, [HUMAN_RECORD])
        cases = {
            "origin-vt": ("Edit", {"old_string": "- Origin Session: sess-origin\n",
                                   "new_string": "- Origin Session:\x0b BBB\n- Origin Session: sess-origin\n"}),
            "origin-ls": ("Edit", {"old_string": "- Origin Session: sess-origin\n",
                                   "new_string": "- Origin Session:  BBB\n- Origin Session: sess-origin\n"}),
            "cr-decoy": ("Edit", {"old_string": "Started At",
                                  "new_string": "note\rResume From: gdd-implementation-gating\nStarted At"}),
            "cr-old": ("Edit", {"old_string": "sess-origin\rx", "new_string": "sess-attacker"}),
            "multiedit-dict": ("MultiEdit", {"edits": {"old_string": "none", "new_string": "none\x0c"}}),
            "write-cr": ("Write", {"content": self.BASE_STATE.replace("Started At", "note\rStarted At")}),
        }
        for name, (tool_name, tool_input) in cases.items():
            with self.subTest(name=name):
                self._assert_denied(self._run(tool_name, tool_input), "行区切り文字")

    def test_crlf_write_is_allowed_on_human_turn(self) -> None:
        write_transcript(self.transcript_path, [HUMAN_RECORD])
        result = self._run("Write", {"content": self.BASE_STATE.replace("\n", "\r\n")})
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_missed_old_string_is_denied_on_peer_turn(self) -> None:
        """判定できないときに通さない: peer turn の state.md への Edit で、`old_string` が射影で見つからない。"""
        write_transcript(self.transcript_path, [PEER_RECORD])
        result = self._run("Edit", {"old_string": "gdd-implementation-gating ", "new_string": "cancelled"})
        self._assert_denied(result, "書き込み後の値を判定できません")

    def test_missed_old_string_on_origin_session_state_is_denied_on_human_turn(self) -> None:
        """判定できないときに通さない: `Origin Session` のある state.md への Edit で、`old_string` が見つからない。"""
        write_transcript(self.transcript_path, [HUMAN_RECORD])
        result = self._run("Edit", {"old_string": "sess-origin ", "new_string": "sess-attacker"})
        self._assert_denied(result, "cannot tell the value after the write")

    def test_empty_new_string_that_joins_lines_is_denied(self) -> None:
        """block すべき入力: Claude Code の Edit は、new_string が空で old_string が改行で終わらず、ファイルに
        old_string＋改行があると、改行ごと消す（2026-09-29 にこのセッションの Edit で実測:
        `- Human Check Status: pending-q1\\napproved\\n` に old="pending-q1"・new="" → `- Human Check Status: approved`）。
        guard の素の置換は改行を残すので、書き込み後の値を判定できない。"""
        cases = {
            "peer-approved": (PEER_RECORD, "- Human Check Status: pending-q1\napproved\n", "Edit",
                              {"old_string": "pending-q1", "new_string": ""}),
            "peer-resume-cancel": (PEER_RECORD, "- Resume From: gdd-q1\ncancelled\n", "Edit",
                                   {"old_string": "gdd-q1", "new_string": ""}),
            "human-origin": (HUMAN_RECORD, "- Origin SessK\nion: BBB\n", "Edit",
                             {"old_string": "K", "new_string": ""}),
            "peer-multiedit-second": (PEER_RECORD, "- Human Check Status: pending-q1\napproved\n", "MultiEdit",
                                      {"edits": [{"old_string": "Route In Progress: none", "new_string": "Route In Progress: none"},
                                                 {"old_string": "pending-q1", "new_string": ""}]}),
        }
        for name, (record, prefix, tool_name, tool_input) in cases.items():
            with self.subTest(name=name):
                write_transcript(self.transcript_path, [record])
                self.state_path.write_text(prefix + self.BASE_STATE, encoding="utf-8")
                expected = "cannot tell the value after the write" if name == "human-origin" else "書き込み後の値を判定できません"
                self._assert_denied(self._run(tool_name, tool_input), expected)

    def test_deleting_a_line_with_its_newline_is_allowed(self) -> None:
        """old_string に改行まで含めた削除は、素の置換とツールの結果が一致するので通す。"""
        write_transcript(self.transcript_path, [HUMAN_RECORD])
        result = self._run("Edit", {"old_string": "- Route In Progress: none\n", "new_string": ""})
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_found_old_string_is_allowed_on_human_turn(self) -> None:
        write_transcript(self.transcript_path, [HUMAN_RECORD])
        result = self._run("Edit", {"old_string": "Route In Progress: none", "new_string": "Route In Progress: none "})
        self.assertEqual(result.returncode, 0, result.stderr)


class TestPeerTurnResumeFromCancelledEndToEnd(_PeerTurnStateEditFixture):
    """中止の記録は `Resume From: cancelled` だけでも、peer turn では deny する。

    steering の検出は `Resume From` と `Next Action` のどちらの cancelled でも中止とみなすのに、境界は
    `Next Action: cancelled` だけを見ていた。peer turn で `Resume From: cancelled` を書くと、境界を通って
    steering が中止扱いになっていた。
    """

    def test_chunk_forms_are_denied_on_peer_turn(self) -> None:
        write_transcript(self.transcript_path, [PEER_RECORD])
        for chunk in ("- Resume From: cancelled\n", "Resume From=cancelled\n",
                      "- Resume From: cancelled | superseded-by: 20260924-x\n"):
            with self.subTest(chunk=chunk):
                result = self._run(self.BASE_STATE, {"old_string": "", "new_string": chunk})
                self.assertEqual(result.returncode, 2, result.stdout)
                self.assertIn("別セッションからのメッセージ", json.loads(result.stderr)["systemMessage"])

    def test_value_only_edit_on_undecodable_state_is_denied_on_peer_turn(self) -> None:
        """例外で guard が落ちない: 既存の state.md に不正な UTF-8 があっても、値だけの Edit を deny する。"""
        write_transcript(self.transcript_path, [PEER_RECORD])
        self.state_path.write_bytes(b"- Note: \xff\xfe\n" + self.BASE_STATE.encode("utf-8"))
        env = dict(os.environ)
        env["GDD_HOOK_STATE_DIR"] = self._state_dir
        payload = {
            "tool_name": "Edit",
            "tool_input": {"file_path": str(self.state_path), "old_string": "gdd-implementation-gating",
                           "new_string": "cancelled"},
            "transcript_path": str(self.transcript_path),
        }
        result = subprocess.run(
            [sys.executable, str(ROOT / "hooks" / "scripts" / "validate-steering-write.py")],
            input=json.dumps(payload), env=env, capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 2, result.stdout)

    def test_human_turn_and_unrelated_edits_are_allowed(self) -> None:
        """止めすぎない: 人のターンの中止と、既に cancelled の state.md への無関係な Edit は通す。"""
        with self.subTest(turn="human"):
            write_transcript(self.transcript_path, [HUMAN_RECORD])
            result = self._run(
                self.BASE_STATE, {"old_string": "gdd-implementation-gating", "new_string": "cancelled"},
            )
            self.assertEqual(result.returncode, 0, result.stderr)
        with self.subTest(turn="peer, unrelated"):
            write_transcript(self.transcript_path, [PEER_RECORD])
            result = self._run(
                self.BASE_STATE.replace("gdd-implementation-gating", "cancelled"),
                {"old_string": "- Route In Progress: none", "new_string": "- Route In Progress: pr_review"},
            )
            self.assertEqual(result.returncode, 0, result.stderr)

class TestOriginSessionMainWiringEndToEnd(unittest.TestCase):
    """`reasons.extend(collect_origin_session_rewrite_violations(...))` が main() から
    消えても検知できるよう、実 hook stdin 経路で deny/allow 配線を固定する。
    """

    def setUp(self) -> None:
        self._state_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self._state_dir, ignore_errors=True)
        self._tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self._tmp, ignore_errors=True)
        self.transcript_path = Path(self._tmp) / "transcript.jsonl"
        write_transcript(self.transcript_path, [HUMAN_RECORD])
        self.state_path = Path(self._tmp) / ".steering" / "20260903-x" / "state.md"
        self.state_path.parent.mkdir(parents=True)
        self.state_path.write_text(
            "Started At: 2026-09-03T00:00:00Z\n"
            "- Resume From: gdd-implementation-gating\n"
            "- Human Check Status: pending\n"
            "- Route In Progress: none\n"
            "- Origin Session: sess-origin\n",
            encoding="utf-8",
        )

    _run = TestPeerTurnMainWiringEndToEnd._run

    def test_rewrite_is_denied_via_main(self) -> None:
        result = self._run("- Origin Session: sess-attacker\n")
        self.assertEqual(result.returncode, 2, result.stderr)
        message = json.loads(result.stderr)["systemMessage"]
        self.assertIn("Origin Session", message)
        self.assertIn("cross-session 通知の宛先", message)

    def test_same_value_rewrite_is_allowed_via_main(self) -> None:
        result = self._run("- Origin Session: sess-origin\n")
        self.assertEqual(result.returncode, 0, result.stderr)

    def _run_patch(self, patch: str) -> subprocess.CompletedProcess[str]:
        env = dict(os.environ)
        env["GDD_HOOK_STATE_DIR"] = self._state_dir
        payload = {
            "tool_name": "ApplyPatch",
            "tool_input": {"patch": patch},
            "transcript_path": str(self.transcript_path),
        }
        return subprocess.run(
            [sys.executable, str(ROOT / "hooks" / "scripts" / "validate-steering-write.py")],
            input=json.dumps(payload),
            env=env,
            capture_output=True,
            text=True,
        )

    def test_delete_file_apply_patch_is_denied_via_main(self) -> None:
        """pr-review 是正 (Finding P) の実 hook 経路。`*** Delete File:` を path 収集から
        落としていたため `steering_targets` が空になり、main() が検査前に allow していた。
        """
        result = self._run_patch(
            f"*** Begin Patch\n*** Delete File: {self.state_path}\n*** End Patch\n"
        )
        self.assertEqual(result.returncode, 2, result.stdout)
        self.assertIn("Origin Session", json.loads(result.stderr)["systemMessage"])

    def test_duplicate_origin_session_write_is_denied_via_main(self) -> None:
        """pr-review 是正 (Finding Q) の実 hook 経路。"""
        env = dict(os.environ)
        env["GDD_HOOK_STATE_DIR"] = self._state_dir
        content = (
            "Started At: 2026-09-03T00:00:00Z\n"
            "- Resume From: gdd-implementation-gating\n"
            "- Human Check Status: pending\n"
            "- Route In Progress: none\n"
            "- Origin Session: sess-origin\n"
            "- Origin Session: sess-attacker\n"
        )
        payload = {
            "tool_name": "Write",
            "tool_input": {"file_path": str(self.state_path), "content": content},
            "transcript_path": str(self.transcript_path),
        }
        result = subprocess.run(
            [sys.executable, str(ROOT / "hooks" / "scripts" / "validate-steering-write.py")],
            input=json.dumps(payload),
            env=env,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 2, result.stdout)
        self.assertIn("Origin Session", json.loads(result.stderr)["systemMessage"])

    def test_multi_file_apply_patch_rewrite_is_denied_via_main(self) -> None:
        """Finding T の形を実 hook の経路で止める（ApplyPatch は値を推定せず、語のある patch を止める）。"""
        worklog = self.state_path.parent / "worklog.md"
        worklog.write_text("- note\n", encoding="utf-8")
        result = self._run_patch(
            "*** Begin Patch\n"
            f"*** Update File: {worklog}\n"
            "@@\n"
            "+- Origin Session: sess-origin\n"
            f"*** Update File: {self.state_path}\n"
            "@@\n"
            "-- Origin Session: sess-origin\n"
            "+- Origin Session: sess-attacker\n"
            "*** End Patch\n"
        )
        self.assertEqual(result.returncode, 2, result.stdout)
        self.assertIn("sess-origin", json.loads(result.stderr)["systemMessage"])

    def test_first_write_on_peer_turn_is_denied_via_main(self) -> None:
        """pr-review 是正 (Finding D) の実 hook 経路。`Origin Session` を持たない
        state.md に peer 由来のターンから初回書込みしても deny される。
        """
        self.state_path.write_text(
            "Started At: 2026-09-03T00:00:00Z\n"
            "- Resume From: gdd-implementation-gating\n"
            "- Human Check Status: pending\n"
            "- Route In Progress: none\n",
            encoding="utf-8",
        )
        write_transcript(self.transcript_path, [PEER_RECORD])
        result = self._run("- Origin Session: sess-attacker\n")
        self.assertEqual(result.returncode, 2, result.stdout)
        self.assertIn("Origin Session", json.loads(result.stderr)["systemMessage"])

    def test_first_write_on_human_turn_is_allowed_via_main(self) -> None:
        self.state_path.write_text(
            "Started At: 2026-09-03T00:00:00Z\n"
            "- Resume From: gdd-implementation-gating\n"
            "- Human Check Status: pending\n"
            "- Route In Progress: none\n",
            encoding="utf-8",
        )
        result = self._run("- Origin Session: sess-origin\n")
        self.assertEqual(result.returncode, 0, result.stderr)

    def _run_payload(self, tool_name: str, tool_input: dict) -> subprocess.CompletedProcess[str]:
        env = dict(os.environ)
        env["GDD_HOOK_STATE_DIR"] = self._state_dir
        payload = {
            "tool_name": tool_name,
            "tool_input": tool_input,
            "transcript_path": str(self.transcript_path),
        }
        script = ROOT / "hooks" / "scripts" / "validate-steering-write.py"
        return subprocess.run(
            [sys.executable, str(script)],
            input=json.dumps(payload),
            env=env,
            capture_output=True,
            text=True,
        )

    def test_line_deleting_edit_is_denied_via_main(self) -> None:
        """pr-review 是正 (Finding J): `new_string=""` の削除 Edit は
        `extract_content_chunks()` が空を返し、main() が content chunk なしとして
        先に allow していた。security boundary の検査は chunk が空でも走らせる。
        """
        result = self._run_payload(
            "Edit",
            {
                "file_path": str(self.state_path),
                "old_string": "- Origin Session: sess-origin\n",
                "new_string": "",
            },
        )
        self.assertEqual(result.returncode, 2, result.stdout)
        self.assertIn("Origin Session", json.loads(result.stderr)["systemMessage"])

    def test_full_write_dropping_the_line_is_denied_via_main(self) -> None:
        """pr-review 是正 (Finding K): 全文 `Write` で `Origin Session` 行を省く形。"""
        result = self._run_payload(
            "Write",
            {
                "file_path": str(self.state_path),
                "content": (
                    "Started At: 2026-09-03T00:00:00Z\n"
                    "- Resume From: gdd-implementation-gating\n"
                    "- Human Check Status: pending\n"
                    "- Route In Progress: none\n"
                ),
            },
        )
        self.assertEqual(result.returncode, 2, result.stdout)
        self.assertIn("Origin Session", json.loads(result.stderr)["systemMessage"])

    def test_full_write_keeping_the_line_is_allowed_via_main(self) -> None:
        result = self._run_payload(
            "Write",
            {
                "file_path": str(self.state_path),
                "content": (
                    "Started At: 2026-09-03T00:00:00Z\n"
                    "- Resume From: gdd-completion-check\n"
                    "- Human Check Status: pending\n"
                    "- Route In Progress: none\n"
                    "- Origin Session: sess-origin\n"
                ),
            },
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_unrelated_line_deleting_edit_is_allowed_via_main(self) -> None:
        """false positive ガード: `Origin Session` を触らない削除 Edit は通す
        （空 chunk でも検査を走らせる変更で通常運用が止まらないこと）。
        """
        result = self._run_payload(
            "Edit",
            {
                "file_path": str(self.state_path),
                "old_string": "- Route In Progress: none\n",
                "new_string": "",
            },
        )
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
