"""SendMessage で再開した agent の完了通知がまだなら、Stop hook は継続の押し返しを出さない。

再開は host が書く宣言フィールド（SendMessage の結果の行の `toolUseResult` の `success` が true で、
`resumedAgentId` が空でない str）だけで読む。再開の後に、同じ agentId の終わりの通知か、host が動いていないと答えた TaskStop の結果（本文の JSON の task_id・shell_id がその id の成功・No task found・is not running）が来たら
終わりとする（行の順で決める）。再開の時刻の窓は、マージ待ちの押し返しと同じ BACKGROUND_WINDOW_SECONDS。
"""
from __future__ import annotations

import json
import tempfile
import time
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

from _stop_hook_test_base import _run_hook, _write_state_file

import gdd_stop_hook
from lib.autonomy_pushback import BACKGROUND_WINDOW_SECONDS
from lib.transcript import any_resumed_agent_running, parse_transcript


def _ago(seconds: float) -> str:
    return datetime.fromtimestamp(time.time() - seconds, timezone.utc).isoformat().replace("+00:00", "Z")


def _resume(n: str = "1", *, agent_id: object = "agent_1", success: object = True, at: object = "now",
            tool_use_result: object = None) -> list[dict]:
    """SendMessage の tool_use と、host の結果の行（toolUseResult つき）。"""
    send = {"type": "assistant", "message": {"content": [
        {"type": "tool_use", "id": f"toolu_sm_{n}", "name": "SendMessage",
         "input": {"to": "agent_1", "message": "続けて"}}]}}
    result = {"type": "user", "message": {"content": [
        {"type": "tool_result", "tool_use_id": f"toolu_sm_{n}", "content": "Resuming agent"}]}}
    if tool_use_result is None:
        tool_use_result = {"success": success, "message": "Resuming agent", "resumedAgentId": agent_id}
    result["toolUseResult"] = tool_use_result
    if at is not None:
        result["timestamp"] = _ago(0) if at == "now" else at
    return [send, result]


def _ended(task_id: str = "agent_1", status: str = "completed") -> dict:
    text = (f"<task-notification>\n<task-id>{task_id}</task-id>\n"
            f"<status>{status}</status>\n<summary>done</summary>\n</task-notification>")
    return {"type": "user", "message": {"content": [{"type": "text", "text": text}]}}


def _task_stop(task_id: str = "agent_1", *, result: bool = True, error: str | None = None) -> list[dict]:
    records = [{"type": "assistant", "message": {"content": [
        {"type": "tool_use", "id": "toolu_stop", "name": "TaskStop", "input": {"task_id": task_id}}]}}]
    if result:
        block = {"type": "tool_result", "tool_use_id": "toolu_stop",
                 "content": error if error is not None else json.dumps({"message": "stopped", "task_id": task_id})}
        if error is not None:
            block["is_error"] = True
        records.append({"type": "user", "message": {"content": [block]}})
    return records


def _task_stop_with_json_id(json_id: str) -> list[dict]:
    """input では agent_1 を止め、成功の本文の JSON には別の id が書かれている TaskStop。"""
    records = _task_stop()
    records[1]["message"]["content"][0]["content"] = json.dumps({"message": "stopped", "task_id": json_id})
    return records


def _transcript(path: Path, middle: list[dict]) -> Path:
    lines = [
        {"type": "user", "message": {"content": [{"type": "text", "text": "/gdd-dev"}]}},
        *middle,
        {"type": "assistant", "message": {"content": [
            {"type": "text", "text": "continuing /gdd-dev. reviewer の完了通知を待ちます。"}]}},
    ]
    path.write_text("\n".join(json.dumps(x) for x in lines) + "\n", encoding="utf-8")
    return path


class ResumedAgentSuppressesContinuationTests(unittest.TestCase):
    def _stop(self, middle: list[dict]) -> tuple[int, str, str]:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        workspace = Path(tmp.name)
        _write_state_file(workspace, {"active": "true", "session_id": "test-session", "iteration": "1",
                                      "workflow_runtime": "claude_code"})
        return _run_hook(workspace, transcript_path=_transcript(workspace / "transcript.jsonl", middle))

    def _assert_silent(self, result: tuple[int, str, str]) -> None:
        code, out, err = result
        self.assertEqual(code, 0, err)
        self.assertEqual(out, "")

    def _assert_nudge(self, result: tuple[int, str, str]) -> None:
        code, out, err = result
        self.assertEqual(code, 0, err)
        payload = json.loads(out)
        self.assertEqual(payload.get("decision"), "block", out)
        self.assertTrue(payload["reason"].startswith("Continue the active `/gdd-dev` run"), out)

    def test_resumed_agent_without_a_notification_suppresses_the_nudge(self) -> None:
        self._assert_silent(self._stop(_resume()))

    def test_resume_after_an_earlier_notification_suppresses_the_nudge(self) -> None:
        # 前の実行の終わりの通知の後に再開したなら、まだ走っている（行の順で決める）
        self._assert_silent(self._stop([_ended(), *_resume()]))
        self._assert_silent(self._stop([*_resume("1"), _ended(), *_resume("2")]))
        self._assert_silent(self._stop([*_resume("1"), *_task_stop(), *_resume("2")]))

    def test_resume_inside_the_window_suppresses_the_nudge(self) -> None:
        self._assert_silent(self._stop(_resume(at=_ago(BACKGROUND_WINDOW_SECONDS - 60))))

    # block（押し返し）すべき入力が allow になる
    def test_ended_resumed_agent_keeps_the_nudge(self) -> None:
        for status in ("completed", "failed", "killed"):
            with self.subTest(status=status):
                self._assert_nudge(self._stop([*_resume(), _ended(status=status)]))

    def test_stopped_resumed_agent_keeps_the_nudge(self) -> None:
        for name, records in (
            ("TaskStop の成功", _task_stop()),
            ("No task found", _task_stop(error="<tool_use_error>No task found with ID: agent_1</tool_use_error>")),
        ):
            with self.subTest(name=name):
                self._assert_nudge(self._stop([*_resume(), *records]))

    def test_task_stop_without_a_not_running_answer_keeps_waiting(self) -> None:
        """TaskStop の結果がまだ無いか、拒否・未知のエラー・本文の JSON の id が input と違う成功で返った再開の agent は、まだ動いているかもしれない。"""
        for name, records in (
            ("TaskStop の入力だけ", _task_stop(result=False)),
            ("拒否", _task_stop(error="Permission for this action was denied by the Claude Code auto mode classifier.")),
            ("JSON の id が input と違う成功", _task_stop_with_json_id("agent_2")),
        ):
            with self.subTest(name=name):
                self._assert_silent(self._stop([*_resume(), *records]))
        # JSON が、input で止めていない別の再開した agent を指すときも、その agent を待ちから外さない。
        self._assert_silent(self._stop([*_resume(agent_id="agent_2"), *_task_stop_with_json_id("agent_2")]))

    def test_notification_for_another_task_does_not_end_the_resume(self) -> None:
        self._assert_silent(self._stop([*_resume(), _ended("agent_2")]))
        self._assert_silent(self._stop([*_resume(), _ended(status="running")]))

    def test_resume_outside_the_window_or_without_a_time_keeps_the_nudge(self) -> None:
        for name, at in (
            ("2 時間 10 分より前の再開", _ago(BACKGROUND_WINDOW_SECONDS + 60)),
            ("未来の時刻", _ago(-3600)),
            ("時刻が無い", None),
            ("時刻が読めない", "yesterday"),
            ("時差の無い時刻", "2026-10-09T00:00:00"),
        ):
            with self.subTest(name=name):
                self._assert_nudge(self._stop(_resume(at=at)))

    def test_undeclared_resume_keeps_the_nudge(self) -> None:
        for name, kwargs in (
            ("success が false", dict(success=False)),
            ("success が文字列", dict(success="true")),
            ("resumedAgentId が無い", dict(tool_use_result={"success": True, "message": "Resuming agent"})),
            ("resumedAgentId が空", dict(agent_id="")),
            ("resumedAgentId が str でない", dict(agent_id=["agent_1"])),
            ("toolUseResult が dict でない", dict(tool_use_result=["agent_1"])),
            ("toolUseResult が文字列", dict(tool_use_result="Resuming agent agent_1")),
        ):
            with self.subTest(name=name):
                self._assert_nudge(self._stop(_resume(**kwargs)))

    def test_resume_text_in_a_tool_result_alone_keeps_the_nudge(self) -> None:
        # 自由文の "Resuming agent" だけでは数えない（宣言フィールドだけを読む）
        records = _resume(tool_use_result={})
        self._assert_nudge(self._stop(records))


class ResumedAgentParseTests(unittest.TestCase):
    def _parse(self, middle: list[dict]):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        return parse_transcript(_transcript(Path(tmp.name) / "t.jsonl", middle))

    def test_bad_tool_use_result_does_not_drop_the_rest_of_the_line(self) -> None:
        for bad in (["x"], "x", 7, {"success": True, "resumedAgentId": {"id": "agent_1"}}):
            with self.subTest(bad=bad):
                tv = self._parse(_resume(tool_use_result=bad))
                self.assertIn("toolu_sm_1", tv.all_tool_result_ids)
                self.assertEqual(tv.skipped, [])

    def test_resume_is_running_until_its_end(self) -> None:
        running, ended = self._parse(_resume()), self._parse([*_resume(), _ended()])
        now = time.time()
        window = (now - BACKGROUND_WINDOW_SECONDS, now)
        self.assertTrue(any_resumed_agent_running(running, *window))
        self.assertFalse(any_resumed_agent_running(ended, *window))


class ResumedAgentGuardFailsOpenTests(unittest.TestCase):
    def test_exception_in_the_resume_check_keeps_the_nudge_and_is_logged(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            tv = parse_transcript(_transcript(root / "transcript.jsonl", _resume()))
            with mock.patch.object(gdd_stop_hook, "any_resumed_agent_running", side_effect=RuntimeError("boom")), \
                    mock.patch.object(gdd_stop_hook, "append_hook_error") as logged, \
                    mock.patch.object(gdd_stop_hook, "subagent_in_flight_from_parsed", return_value=False):
                gdd_stop_hook._continuation_intent_guard(
                    tv, root, str(root / "transcript.jsonl"), root / "transcript.jsonl", tv.last_assistant_text)
            self.assertTrue(any("boom" in str(c) for c in logged.call_args_list), logged.call_args_list)


if __name__ == "__main__":
    unittest.main()
