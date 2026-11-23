"""突き合わせ agent の起動のときに、main の transcript のユーザーの発言で request.md を作る hook のテスト。

入口（hooks.json に登録した run-request-capture-hook.sh）から、transcript と steering の fixture を
読ませて、request.md の中身まで通す。
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from _paths import PLUGIN_ROOT

HOOK = PLUGIN_ROOT / "hooks" / "scripts" / "run-request-capture-hook.sh"
BEGIN = "<!-- gdd-request-capture:begin -->"
NOT_COPIED = "<!-- gdd-request-capture:not-copied -->"
END = "<!-- gdd-request-capture:end -->"
CROSSCHECK = "gate-driven-development:gdd-request-code-crosscheck"


def human(text: str, ts: str = "2026-10-31T01:00:00Z") -> dict:
    return {"type": "user", "timestamp": ts, "origin": {"kind": "human"}, "message": {"role": "user", "content": text}}


def said(text: str, sidechain: bool = False) -> dict:
    return {
        "type": "assistant",
        "isSidechain": sidechain,
        "message": {"role": "assistant", "content": [{"type": "text", "text": text}]},
    }


def typed_command(name: str, args: str, ts: str = "2026-10-31T02:00:00Z") -> dict:
    return {
        "type": "user",
        "timestamp": ts,
        "message": {
            "role": "user",
            "content": f"<command-message>{name}</command-message>\n<command-name>/{name}</command-name>\n<command-args>{args}</command-args>",
        },
    }


def skill_call(args: str, skill: str = "gate-driven-development:gdd-dev", ts: str = "2026-10-31T02:30:00Z") -> dict:
    return {
        "type": "assistant",
        "timestamp": ts,
        "message": {
            "role": "assistant",
            "content": [
                {"type": "tool_use", "id": "t1", "name": "Skill", "input": {"skill": skill, "args": args}}
            ],
        },
    }


def ask_answer(question: str, label: str) -> dict:
    return {
        "type": "user",
        "timestamp": "2026-10-31T03:00:00Z",
        "toolUseResult": {"questions": [{"question": question}], "answers": {question: label}},
        "message": {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "t2", "content": "answered"}]},
    }


def queued(text: str, kind: str = "human") -> dict:
    return {"type": "attachment", "attachment": {"type": "queued_command", "prompt": text, "origin": {"kind": kind}}}


def _load_validator():
    path = PLUGIN_ROOT / "hooks" / "scripts" / "validate-steering-write.py"
    spec = importlib.util.spec_from_file_location("validate_steering_write_for_test", path)
    module = importlib.util.module_from_spec(spec)
    import sys

    sys.path.insert(0, str(path.parent))
    spec.loader.exec_module(module)
    return module


class RequestCaptureTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.home = self.tmp / "home"
        (self.home / ".claude").mkdir(parents=True)
        self.task = self.tmp / "wt" / ".steering" / "20261031-x"
        self.task.mkdir(parents=True)
        (self.task / "state.md").write_text(
            "- Next Action: gdd-requirements-gating\n- Started At: 2026-10-31T20:00:00+09:00\n- Created In Session: s1\n",
            encoding="utf-8",
        )
        # Claude Code では runner は request.md を作らず、写しを request-notes.md に書く。
        self.request = self.task / "request.md"
        self.notes = self.task / "request-notes.md"
        self.notes.write_text("# runner の写し\n\nrunner が写した行\n", encoding="utf-8")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _transcript(self, records: list, raw_lines: list[str] | None = None) -> Path:
        path = self.tmp / "t.jsonl"
        lines = (raw_lines or []) + [json.dumps(r, ensure_ascii=False) for r in records]
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return path

    def _run(self, records: list | None, prompt: str | None = None, subagent_type: str = CROSSCHECK,
             extra_env: dict | None = None, raw_lines: list[str] | None = None,
             invoke: bool = True, session_id: str | None = "s1") -> subprocess.CompletedProcess[str]:
        # 写すのは steering を作った /gdd-dev の起動までなので、起動の無い記録には打った起動を足す。
        if records is not None and invoke and not any("gdd-dev" in json.dumps(r, ensure_ascii=False) for r in records):
            records = records + [typed_command("gdd-dev", "")]
        payload = {
            "hook_event_name": "PreToolUse",
            "session_id": session_id,
            "agent_id": "a1",
            "cwd": str(self.tmp),
            "tool_name": "Agent",
            "tool_input": {
                "subagent_type": subagent_type,
                "prompt": prompt if prompt is not None else f"request.md: {self.request}\nrepo: {self.tmp / 'wt'}",
            },
        }
        if session_id is None:
            del payload["session_id"]
        if records is not None:
            payload["transcript_path"] = str(self._transcript(records, raw_lines))
        env = {
            "HOME": str(self.home),
            "PATH": "/usr/bin:/bin:/opt/homebrew/bin:/usr/local/bin",
            "CLAUDE_PLUGIN_ROOT": str(PLUGIN_ROOT),
        }
        env.update(extra_env or {})
        return subprocess.run(["bash", str(HOOK)], input=json.dumps(payload), capture_output=True, text=True, env=env, timeout=30)

    def _assert_not_copied(self, result: subprocess.CompletedProcess[str]) -> None:
        text = self.request.read_text(encoding="utf-8")
        self.assertTrue(text.startswith(NOT_COPIED + "\n"), text)
        self.assertNotIn(BEGIN, text)
        self.assertNotIn("runner が写した行", text)
        self.assertEqual(self.notes.read_text(encoding="utf-8"), "# runner の写し\n\nrunner が写した行\n")
        self.assertIn("依頼の原文を写していません", json.loads(result.stdout)["systemMessage"])
        self.request.unlink()

    def _section(self) -> str:
        text = self.request.read_text(encoding="utf-8")
        self.assertIn(BEGIN, text)
        return text[text.index(BEGIN): text.index(END) + len(END)]

    def test_crosscheck_dispatch_creates_request_md_with_the_section(self) -> None:
        result = self._run([said("どうしますか？"), human("GDD の HITL を確認して")])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "")
        text = self.request.read_text(encoding="utf-8")
        self.assertTrue(text.startswith(BEGIN))
        self.assertIn("GDD の HITL を確認して", self._section())
        self.assertEqual(text.split(END, 1)[1].strip(), "")
        self.assertEqual(self.notes.read_text(encoding="utf-8"), "# runner の写し\n\nrunner が写した行\n")
        self.assertEqual(sorted(p.name for p in self.task.iterdir()), ["request-notes.md", "request.md", "state.md"])

    def test_existing_request_md_is_never_read_or_rewritten(self) -> None:
        both_marks = f"# 依頼の原文\n\n{NOT_COPIED}\n<!-- gdd-request-capture:not-copied:end -->\nユーザーの文\n{BEGIN}\n"
        for existing in ("# 依頼の原文\n\nmain が書いた依頼の要約\n", both_marks, ""):
            for state in ("- Started At: 2026-10-31T20:00:00+09:00\n- Created In Session: s1\n", "- Started At: 2026-10-31T20:00:00+09:00\n"):
                (self.task / "state.md").write_text(state, encoding="utf-8")
                self.request.write_bytes(existing.encode("utf-8"))
                self._run([human("本当の依頼"), skill_call("main が書いた依頼の要約")])
                self.assertEqual(self.request.read_bytes(), existing.encode("utf-8"))
        self.assertEqual(self.notes.read_text(encoding="utf-8"), "# runner の写し\n\nrunner が写した行\n")

    def test_dispatch_is_never_blocked(self) -> None:
        result = self._run([human("依頼")])
        self.assertNotIn("deny", result.stdout)
        self.assertNotIn('"block"', result.stdout)

    def test_bare_subagent_type_also_counts(self) -> None:
        self._run([human("依頼の文")], subagent_type="gdd-request-code-crosscheck")
        self.assertIn("依頼の文", self._section())

    def test_general_purpose_fallback_with_crosscheck_definition_counts(self) -> None:
        body = (PLUGIN_ROOT / "agents" / "gdd-request-code-crosscheck.md").read_text(encoding="utf-8").split("---", 2)[2]
        self._run([human("代わりの経路の依頼")], prompt=f"{body}\nrequest.md: {self.request}", subagent_type="general-purpose")
        self.assertIn("代わりの経路の依頼", self._section())

    def test_other_agents_do_not_create_request_md(self) -> None:
        self._run([human("依頼")], subagent_type="gate-driven-development:gdd-formal-gate-runner")
        self.assertFalse(self.request.exists())

    def test_preceding_assistant_text_is_quoted_as_context(self) -> None:
        self._run([said("案 A と案 B があります。推奨は案 A"), human("推奨で OK")])
        section = self._section()
        self.assertIn("推奨は案 A", section)
        self.assertLess(section.index("推奨は案 A"), section.index("推奨で OK"))

    def test_range_starts_after_last_done_marker_on_its_own_line(self) -> None:
        records = [
            human("前のタスクの依頼"),
            said('完了しました。\n<gdd-stop reason="done">'),
            human("新しい依頼"),
        ]
        self._run(records)
        section = self._section()
        self.assertIn("新しい依頼", section)
        self.assertNotIn("前のタスクの依頼", section)

    def test_range_ends_at_the_last_gdd_dev_invocation(self) -> None:
        records = [human("依頼の本文"), skill_call("要約"), said("起動しました"), human("起動の後の発言")]
        self._run(records)
        section = self._section()
        self.assertIn("依頼の本文", section)
        self.assertNotIn("起動の後の発言", section)

    def test_utterances_after_invocation_are_written_below_the_section(self) -> None:
        records = [human("依頼の本文"), skill_call("要約"), said("縮めますか？"), human("縮めないで", ts="2026-10-31T05:00:00Z")]
        self._run(records)
        text = self.request.read_text(encoding="utf-8")
        below = text.split(END, 1)[1]
        self.assertIn("縮めないで", below)
        self.assertIn("2026-10-31T05:00:00Z", below)
        self.assertIn("縮めますか？", below)
        self.assertNotIn("縮めないで", self._section())

    def test_resume_in_the_same_transcript_copies_up_to_the_invocation_that_made_the_steering(self) -> None:
        (self.task / "state.md").write_text("- Started At: 2026-10-31T11:45:00+09:00\n- Created In Session: s1\n", encoding="utf-8")
        records = [
            human("元の依頼"),
            skill_call("要約", ts="2026-10-31T02:30:00Z"),
            said("中断しました"),
            typed_command("gdd-dev", "resume 20261031-x", ts="2026-10-31T05:00:00Z"),
        ]
        self._run(records)
        self.assertIn("元の依頼", self._section())

    def test_resume_from_another_session_creates_the_not_copied_notice(self) -> None:
        (self.task / "state.md").write_text("- Started At: 2026-10-31T11:45:00+09:00\n- Created In Session: s1\n", encoding="utf-8")
        for records in (
            [human("続きから"), typed_command("gdd-dev", "20261031-x の続きから", ts="2026-10-31T05:00:00Z")],
            [typed_command("gdd-dev", "", ts="2026-10-31T05:00:00Z")],
            [human("続きをやって"), skill_call("gdd-resume", skill="gate-driven-development:gdd-resume", ts="2026-10-31T05:00:00Z")],
        ):
            self._assert_not_copied(self._run(records, invoke=False))

    def test_steering_made_in_another_session_is_not_matched_with_this_sessions_invocation(self) -> None:
        # session s1 で別のタスク X を起動した後、別の session で作った steering を s1 で再開して突き合わせる。
        (self.task / "state.md").write_text(
            "- Started At: 2026-10-31T11:00:00+09:00\n- Created In Session: other-session\n", encoding="utf-8"
        )
        records = [
            human("タスク X の依頼"),
            typed_command("gdd-dev", "タスク X", ts="2026-10-31T01:00:00Z"),
            typed_command("gdd-dev", "resume 20261031-x", ts="2026-10-31T03:00:00Z"),
        ]
        self._assert_not_copied(self._run(records))

    def test_missing_created_in_session_creates_the_not_copied_notice(self) -> None:
        (self.task / "state.md").write_text("- Started At: 2026-10-31T20:00:00+09:00\n", encoding="utf-8")
        self._assert_not_copied(self._run([human("依頼")]))

    def test_not_copied_reason_is_shown_to_the_user(self) -> None:
        (self.task / "state.md").write_text("- Started At: 2026-10-31T20:00:00+09:00\n", encoding="utf-8")
        result = self._run([human("依頼")])
        message = json.loads(result.stdout)["systemMessage"]
        self.assertIn("Created In Session", message)
        self.assertNotIn("deny", result.stdout)

    def test_empty_or_missing_session_id_is_not_matched(self) -> None:
        (self.task / "state.md").write_text("- Started At: 2026-10-31T20:00:00+09:00\n- Created In Session: s1\n", encoding="utf-8")
        for session_id in ("", None):
            self._assert_not_copied(self._run([human("依頼")], session_id=session_id))

    def test_utterances_after_invocation_are_kept_under_the_notice_when_none_came_before(self) -> None:
        records = [skill_call("要約"), said("どちらにしますか？"), human("広い側で", ts="2026-10-31T05:00:00Z")]
        result = self._run(records)
        text = self.request.read_text(encoding="utf-8")
        self.assertTrue(text.startswith(NOT_COPIED + "\n"), text)
        self.assertIn("広い側で", text)
        self.assertIn("2026-10-31T05:00:00Z", text)
        self.assertNotIn(BEGIN, text)
        self.assertIn("依頼の原文を写していません", json.loads(result.stdout)["systemMessage"])

    def test_existing_request_md_without_created_in_session_is_reported(self) -> None:
        (self.task / "state.md").write_text("- Started At: 2026-10-31T20:00:00+09:00\n", encoding="utf-8")
        self.request.write_text("# 依頼の原文\n\nmain が書いた依頼の要約\n", encoding="utf-8")
        before = self.request.read_bytes()
        result = self._run([human("本当の依頼")])
        self.assertEqual(self.request.read_bytes(), before)
        self.assertIn("Created In Session", json.loads(result.stdout)["systemMessage"])

        (self.task / "state.md").write_text("- Started At: 2026-10-31T20:00:00+09:00\n- Created In Session: s1\n", encoding="utf-8")
        self.assertEqual(self._run([human("本当の依頼")]).stdout.strip(), "")
        self.assertEqual(self.request.read_bytes(), before)

    def test_not_copied_notice_is_not_rewritten_by_a_later_dispatch(self) -> None:
        (self.task / "state.md").write_text("- Started At: 2026-10-31T20:00:00+09:00\n", encoding="utf-8")
        self._run([human("依頼")])
        notice = self.request.read_bytes()
        (self.task / "state.md").write_text("- Started At: 2026-10-31T20:00:00+09:00\n- Created In Session: s1\n", encoding="utf-8")
        self._run([human("依頼の本文")])
        self.assertEqual(self.request.read_bytes(), notice)

    def test_state_fields_are_read_with_the_canonical_reader(self) -> None:
        (self.task / "state.md").write_text(
            "```\nStarted At: <ISO 8601>\n```\n- `Started At`: 2026-10-31T20:00:00+09:00\n- `Created In Session`: s1\n",
            encoding="utf-8",
        )
        self._run([human("依頼の本文")])
        self.assertIn("依頼の本文", self._section())

    def test_no_invocation_or_unreadable_started_at_creates_the_not_copied_notice(self) -> None:
        self._assert_not_copied(self._run([human("起動の無い session の発言")], invoke=False))
        for state in ("- Next Action: x\n", "- Started At: 不明\n", "- Started At: 2026-10-31T20:00:00\n"):
            (self.task / "state.md").write_text(state + "- Created In Session: s1\n", encoding="utf-8")
            result = self._run([human("依頼")])
            self.assertIn("Started At", json.loads(result.stdout)["systemMessage"])
            self._assert_not_copied(result)

    def test_exception_leaves_no_request_md_and_no_temporary_file(self) -> None:
        (self.task / "state.md").write_bytes(b"- Started At: \xff\xfe\n- Created In Session: s1\n")
        result = self._run([human("依頼")])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(self.request.exists())
        self.assertEqual(sorted(p.name for p in self.task.iterdir()), ["request-notes.md", "state.md"])

    def test_range_ends_at_typed_gdd_dev_too(self) -> None:
        self._run([human("相談"), typed_command("gdd-dev", "打った依頼"), human("後の発言")])
        section = self._section()
        self.assertIn("打った依頼", section)
        self.assertNotIn("後の発言", section)

    def test_range_starts_after_last_cancelled_marker(self) -> None:
        records = [human("中止したタスクの依頼"), said('中止しました。\n<gdd-stop reason="cancelled">'), human("新しい依頼")]
        self._run(records)
        section = self._section()
        self.assertIn("新しい依頼", section)
        self.assertNotIn("中止したタスクの依頼", section)

    def test_all_assistant_text_since_the_previous_utterance_is_quoted(self) -> None:
        records = [human("相談"), said("案 A: 広い側の本文"), said("確認しました。どうしますか？"), human("A で")]
        self._run(records)
        section = self._section()
        self.assertIn("案 A: 広い側の本文", section)
        self.assertIn("どうしますか？", section)

    def test_quoted_done_marker_does_not_move_the_range(self) -> None:
        records = [
            human("最初の相談"),
            said('marker は `<gdd-stop reason="done">` の形です'),
            said('```\n<gdd-stop reason="done">\n```'),
            human("続き"),
        ]
        self._run(records)
        self.assertIn("最初の相談", self._section())

    def test_main_skill_args_are_not_written_to_request_md(self) -> None:
        records = [typed_command("gdd-dev", "ユーザーが打った依頼"), skill_call("main が書いた依頼の要約")]
        self._run(records)
        self.assertIn("ユーザーが打った依頼", self._section())
        self.assertNotIn("main が書いた依頼の要約", self.request.read_text(encoding="utf-8"))

    def test_ask_user_question_answer_is_copied(self) -> None:
        self._run([ask_answer("どちらにしますか？", "広い側（推奨）")])
        section = self._section()
        self.assertIn("どちらにしますか？", section)
        self.assertIn("広い側（推奨）", section)

    def test_queued_human_line_is_copied_but_queued_peer_is_not(self) -> None:
        self._run([queued("途中で打った指示"), queued("別セッションの指示", kind="peer")])
        section = self._section()
        self.assertIn("途中で打った指示", section)
        self.assertNotIn("別セッションの指示", section)

    def test_non_human_lines_are_not_copied(self) -> None:
        records = [
            human("本物の発言"),
            {"type": "user", "origin": {"kind": "peer"}, "isMeta": True, "message": {"content": "peer の報告"}},
            {"type": "user", "origin": {"kind": "task-notification"}, "message": {"content": "<task-notification>通知</task-notification>"}},
            {"type": "user", "isMeta": True, "message": {"content": "Base directory for this skill: 展開された本文"}},
            {"type": "user", "isCompactSummary": True, "message": {"content": "This session is being continued 要約"}},
            {"type": "user", "isSidechain": True, "origin": {"kind": "human"}, "message": {"content": "sidechain の行"}},
            {"type": "user", "message": {"content": "<system-reminder>origin の無い注入</system-reminder>"}},
            {"type": "user", "origin": {"kind": "human"}, "message": {"content": [{"type": "tool_result", "content": "tool の結果"}]}},
        ]
        self._run(records)
        section = self._section()
        self.assertIn("本物の発言", section)
        for text in ("peer の報告", "通知", "展開された本文", "要約", "sidechain の行", "origin の無い注入", "tool の結果"):
            self.assertNotIn(text, section)

    def test_system_reminder_inside_human_line_is_stripped(self) -> None:
        self._run([human("<system-reminder>\nworktree の案内\n</system-reminder>\n本文の依頼")])
        section = self._section()
        self.assertIn("本文の依頼", section)
        self.assertNotIn("worktree の案内", section)

    def test_values_the_steering_guard_blocks_are_replaced(self) -> None:
        words = (
            "パスは /Users/someone/repo/a.py と /home/x/b.py、連絡は taro@corp.example.co.jp、"
            "アカウント 123456789012、鍵は -----BEGIN RSA PRIVATE KEY----- 、password=hunter2hunter2 （略）"
        )
        self._run([human(words)])
        section = self._section()
        validator = _load_validator()
        violations = validator.collect_violations([section])
        self.assertEqual(violations, [], violations)
        for raw in ("/Users/someone", "/home/x", "taro@corp", "123456789012", "hunter2hunter2"):
            self.assertNotIn(raw, section)

    def test_existing_section_is_never_replaced(self) -> None:
        self._run([human("最初の依頼")])
        original = self._section()
        self._run([human("最初の依頼"), human("別の session の発言")])
        self.assertEqual(self._section(), original)
        self.assertEqual(self.request.read_text(encoding="utf-8").count(BEGIN), 1)

    def test_section_edited_by_a_person_is_not_restored(self) -> None:
        self._run([human("鍵は sk-proj-abcdefghijklmnop です")])
        edited = self.request.read_text(encoding="utf-8").replace("sk-proj-abcdefghijklmnop", "（伏せた）")
        self.request.write_text(edited, encoding="utf-8")
        self._run([human("鍵は sk-proj-abcdefghijklmnop です")], subagent_type="gate-driven-development:gdd-formal-gate-runner")
        self._run([human("鍵は sk-proj-abcdefghijklmnop です")])
        self.assertEqual(self.request.read_text(encoding="utf-8"), edited)

    def test_no_copy_of_the_words_is_kept_outside_the_steering(self) -> None:
        self._run([human("依頼の文")])
        state = self.home / ".claude" / ".gdd-hook-state"
        leftovers = [p for p in state.rglob("*") if p.is_file()] if state.exists() else []
        self.assertEqual(leftovers, [])

    def test_path_must_be_exactly_one_steering_request_md_with_state(self) -> None:
        other = self.tmp / "wt" / ".steering" / "20261031-y"
        other.mkdir(parents=True)
        (other / "state.md").write_text("x\n", encoding="utf-8")
        (other / "request.md").write_text("y\n", encoding="utf-8")
        self._run([human("依頼")], prompt=f"{self.request}\n{other / 'request.md'}")
        self.assertFalse(self.request.exists())

        (self.task / "state.md").unlink()
        self._run([human("依頼")])
        self.assertFalse(self.request.exists())

    def test_symlinked_request_md_is_not_written(self) -> None:
        target = self.tmp / "outside.md"
        target.write_text("outside\n", encoding="utf-8")
        self.request.symlink_to(target)
        self._run([human("依頼")])
        self.assertEqual(target.read_text(encoding="utf-8"), "outside\n")

    def test_dangling_symlink_or_symlinked_steering_is_not_written(self) -> None:
        missing = self.tmp / "missing.md"
        self.request.symlink_to(missing)
        self._run([human("依頼")])
        self.assertFalse(missing.exists())
        self.request.unlink()

        real = self.tmp / "real-steering"
        real.mkdir()
        (real / "state.md").write_text((self.task / "state.md").read_text(encoding="utf-8"), encoding="utf-8")
        link = self.tmp / "wt" / ".steering" / "20261031-link"
        link.symlink_to(real)
        self._run([human("依頼")], prompt=f"request.md: {link / 'request.md'}")
        self.assertFalse((real / "request.md").exists())

    def test_no_transcript_or_no_human_words_creates_the_not_copied_notice(self) -> None:
        result = self._run(None)
        self.assertEqual(result.returncode, 0)
        self._assert_not_copied(result)
        self._assert_not_copied(self._run([said("assistant だけ")], invoke=False))

    def test_broken_and_deeply_nested_lines_do_not_crash(self) -> None:
        result = self._run([human("壊れた行の後の依頼")], raw_lines=["{not json", "[" * 10**6 + "]" * 10**6])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("壊れた行の後の依頼", self._section())

    def test_unreadable_payload_exits_zero(self) -> None:
        result = subprocess.run(["bash", str(HOOK)], input="{broken", capture_output=True, text=True,
                                env={"HOME": str(self.home), "PATH": "/usr/bin:/bin:/opt/homebrew/bin"}, timeout=30)
        self.assertEqual(result.returncode, 0)

    def test_kill_switch_disables_the_hook(self) -> None:
        (self.home / ".claude" / "gdd-hooks-disabled").write_text("", encoding="utf-8")
        self._run([human("依頼")])
        self.assertFalse(self.request.exists())

    def test_registered_on_pre_tool_use_agent(self) -> None:
        hooks = json.loads((PLUGIN_ROOT / "hooks" / "hooks.json").read_text(encoding="utf-8"))["hooks"]
        commands = [h["command"] for e in hooks["PreToolUse"] if e.get("matcher") == "Agent" for h in e["hooks"]]
        self.assertTrue(any("run-request-capture-hook.sh" in c for c in commands))


if __name__ == "__main__":
    unittest.main()
