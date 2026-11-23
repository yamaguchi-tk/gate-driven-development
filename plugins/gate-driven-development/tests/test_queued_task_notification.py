"""main が動いている間に届いた完了通知（queued の形）を、完了の信号として読むかのテスト。

Claude Code は、turn の途中に届いた `<task-notification>` を `type: "user"` の行ではなく、
`queue-operation`（enqueue / remove）の content か、`attachment`（type: queued_command）の
prompt にだけ書くことがある。enqueue だけの通知は配達待ちで、まだ終わりとしない（ここで
loop state を消して止まると、通知が state の無いセッションに届く）。
"""
from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path as _P

sys.path.insert(0, str(_P(__file__).parent))
from _stop_hook_test_base import *  # noqa: F401,F403
from lib.transcript import inflight_dispatch_ids, last_user_turn_is_peer, parse_transcript
from test_peer_turn_write_boundary_contract import HUMAN_RECORD
from test_wait_watchdog import _dispatch, _iso, _timer
from test_queued_human_merge_cue import _parse


def _notification_text(task_id: str, tool_use_id: str, status: str = "completed") -> str:
    return (
        f"<task-notification>\n<task-id>{task_id}</task-id>\n<tool-use-id>{tool_use_id}</tool-use-id>\n"
        f"<status>{status}</status>\n<summary>done</summary>\n</task-notification>"
    )


def _enqueue(text: object, operation: str = "enqueue") -> dict:
    return {"type": "queue-operation", "operation": operation, "timestamp": _iso(time.time()),
            "sessionId": "s", "content": text}


def _queued_attachment(text: object, attachment_type: str = "queued_command") -> dict:
    return {"type": "attachment", "isSidechain": False,
            "attachment": {"type": attachment_type, "prompt": text}}


def _queued(shape: str, text: object) -> list[dict]:
    if shape == "enqueue":
        return [_enqueue(text)]
    if shape == "remove":
        return [_enqueue(text, "remove")]
    if shape == "enqueue+remove":
        return [_enqueue(text), _enqueue(text, "remove")]
    if shape == "attachment":
        return [_queued_attachment(text)]
    # 本文を content block の list で書く形（type:user の行と同じく text block と素の文字列を読む）
    if shape == "remove(list)":
        return [_enqueue(["", {"type": "text", "text": text}], "remove")]
    if shape == "attachment(list)":
        return [_queued_attachment([{"type": "text", "text": "x"}, text])]
    raise ValueError(shape)


SHAPES = ("remove", "enqueue+remove", "attachment", "remove(list)", "attachment(list)")



class _StopHookRun:
    def _run(self, ws: Path, items: list[dict], body: str) -> tuple[dict | None, str]:
        transcript = ws / "transcript.jsonl"
        head = [{"type": "user", "message": {"content": [{"type": "text", "text": "/gdd-dev"}]}}]
        tail = [{"type": "assistant", "message": {"content": [{"type": "text", "text": body}]}}]
        transcript.write_text("\n".join(json.dumps(i) for i in head + items + tail) + "\n", encoding="utf-8")
        code, out, err = _run_hook(ws, transcript)
        self.assertEqual(code, 0, err)
        return (json.loads(out) if out.strip().startswith("{") else None), out + err

    def _active(self, ws: Path) -> Path:
        return _write_state_file(ws, {"active": "true", "session_id": "test-session", "iteration": "1"})


class TestQueuedNotificationFromHook(_StopHookRun, unittest.TestCase):
    """入口（gdd_stop_hook.py）から: queued の形だけで届いた完了通知で、dispatch を終わりとして扱う。"""

    def test_stop_passes_after_queued_notification(self):
        """state を消す停止は、queued の形の完了通知の後なら押し返さない。"""
        for shape in SHAPES:
            with self.subTest(shape=shape), tempfile.TemporaryDirectory() as tmp:
                ws = Path(tmp)
                state = self._active(ws)
                items = (_dispatch("a", time.time() - 60, "general-purpose")
                         + _queued(shape, _notification_text("agent_a", "toolu_d_a")))
                payload, _ = self._run(ws, items, '止めます。<gdd-stop reason="blocked">\n\n## 👤 次にすること\n- 待つ')
                self.assertIsNone(payload)
                self.assertFalse(state.exists())

    def test_ended_reviewer_is_not_overdue(self):
        """上限を過ぎた reviewer でも、queued の形で終わっていれば watchdog は block せず、継続の block になる。"""
        for shape in SHAPES:
            with self.subTest(shape=shape), tempfile.TemporaryDirectory() as tmp:
                ws = Path(tmp)
                self._active(ws)
                items = (_dispatch("a", time.time() - 4000)
                         + _queued(shape, _notification_text("agent_a", "toolu_d_a")))
                payload, _ = self._run(ws, items, "reviewer の結果を読みます")
                self.assertIsNotNone(payload)
                self.assertTrue(payload["reason"].startswith("Continue the active"), payload["reason"])
                self.assertNotIn("agent_a", payload["reason"])

    def test_reviewer_with_only_enqueued_notification_is_overdue(self):
        """対照: enqueue だけ（配達待ち）なら、上限を過ぎた reviewer に watchdog が block する。"""
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            self._active(ws)
            items = (_dispatch("a", time.time() - 4000)
                     + _queued("enqueue", _notification_text("agent_a", "toolu_d_a")))
            payload, _ = self._run(ws, items, "reviewer の結果を読みます")
            self.assertIsNotNone(payload)
            self.assertEqual(payload["decision"], "block")
            self.assertIn("agent_a", payload["reason"])
            self.assertIn("上限", payload["reason"])

    def test_ended_timer_does_not_arm(self):
        """queued の形で終わった期限 timer は、まだ動いている reviewer を武装しない。"""
        for shape in SHAPES:
            with self.subTest(shape=shape), tempfile.TemporaryDirectory() as tmp:
                ws = Path(tmp)
                self._active(ws)
                now = time.time()
                items = (_dispatch("a", now - 100) + _timer("1", now - 90, 1800)
                         + _queued(shape, _notification_text("bash_1", "toolu_t_1")))
                payload, _ = self._run(ws, items, "reviewer を待ちます")
                self.assertIsNotNone(payload)
                self.assertEqual(payload["decision"], "block")
                self.assertIn("期限 timer が無い", payload["reason"])

    def test_stop_is_held_while_notification_is_only_enqueued(self):
        """enqueue だけ（配達待ち）の通知では、state を消す停止を押し返す。"""
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            state = self._active(ws)
            items = (_dispatch("a", time.time() - 60, "general-purpose")
                     + _queued("enqueue", _notification_text("agent_a", "toolu_d_a")))
            payload, _ = self._run(ws, items, '止めます。<gdd-stop reason="blocked">\n\n## 👤 次にすること\n- 待つ')
            self.assertIsNotNone(payload)
            self.assertEqual(payload["decision"], "block")
            self.assertIn("agent_a", payload["reason"])
            self.assertTrue(state.exists())


class TestQueuedNotificationFailOpen(unittest.TestCase):
    """L1+ 安全策 2 の fail-open の 3 ケース。"""

    def _inflight(self, tail: list[dict]) -> set[str]:
        return inflight_dispatch_ids(_parse(_dispatch("a", time.time() - 60) + tail))

    def test_non_ending_or_unrelated_queued_record_keeps_dispatch_running(self):
        """止めるべき入力が通らない: 終わりでない status、別の id、queued_command 以外の attachment。"""
        cases = {
            "enqueue だけ（配達待ち）": _queued("enqueue", _notification_text("agent_a", "toolu_d_a")),
            "running": _queued("enqueue+remove", _notification_text("agent_a", "toolu_d_a", "running")),
            "別の id": _queued("attachment", _notification_text("agent_b", "toolu_d_b")),
            "prompt_snapshot": [_queued_attachment(_notification_text("agent_a", "toolu_d_a"), "prompt_snapshot")],
            "hook の出力": [{"type": "attachment", "attachment": {
                "type": "hook_success", "content": _notification_text("agent_a", "toolu_d_a")}}],
            "dequeue（content なし）": [{"type": "queue-operation", "operation": "dequeue"}],
        }
        for name, tail in cases.items():
            with self.subTest(case=name):
                self.assertEqual(self._inflight(tail), {"toolu_d_a"})

    def test_malformed_queued_record_does_not_crash_and_other_lines_are_read(self):
        """例外で落ちない: 変な形の queued の行があっても、後ろの通知は読む。"""
        malformed = [
            _enqueue(None, "remove"), _enqueue(3, "remove"), _enqueue(["x"], "remove"), _enqueue({"a": 1}, "remove"),
            _queued_attachment(None), _queued_attachment(3), _queued_attachment(["x"]),
            {"type": "attachment", "attachment": None},
            {"type": "attachment", "attachment": "queued_command"},
            {"type": "attachment", "attachment": {"type": ["queued_command"], "prompt": "x"}},
            {"type": "queue-operation"},
        ]
        tv = _parse(_dispatch("a", time.time() - 60) + malformed
                    + _queued("remove", _notification_text("agent_a", "toolu_d_a")))
        self.assertEqual(inflight_dispatch_ids(tv), set())
        self.assertEqual(tv.skipped, [])

    def test_unreadable_queued_record_keeps_dispatch_running(self):
        """判定できないときは終わりにしない: 読めない queued の行だけなら、Agent の dispatch は実行中のまま
        （loop state を消す停止を押し返す側）。期限 timer では実行中のままが武装に数える側になる。"""
        text = _notification_text("agent_a", "toolu_d_a")
        cases = {
            "content が null": [_enqueue(None, "remove")],
            "prompt が dict": [_queued_attachment({"type": "text", "text": text})],
            "途中で切れた行": [],
        }
        for name, tail in cases.items():
            with self.subTest(case=name), tempfile.TemporaryDirectory() as tmp:
                p = Path(tmp) / "t.jsonl"
                lines = [json.dumps(i) for i in _dispatch("a", time.time() - 60) + tail]
                if name == "途中で切れた行":
                    lines.append(json.dumps(_enqueue(text, "remove"))[:-20])
                p.write_text("\n".join(lines) + "\n", encoding="utf-8")
                self.assertEqual(inflight_dispatch_ids(parse_transcript(p)), {"toolu_d_a"})


class TestQueuedRecordIsNotHumanTurn(unittest.TestCase):
    """queued の行は、人間の発話にも peer にも数えない。"""

    PEER = {"type": "user", "origin": {"kind": "peer"}, "message": {"content": [
        {"type": "text", "text": "Another Claude session sent a message:\nhi"}]}}

    def test_queued_records_do_not_change_last_user_text(self):
        human = {"type": "user", "message": {"content": [{"type": "text", "text": "/gdd-dev 続けて"}]}}
        for shape in SHAPES:
            with self.subTest(shape=shape):
                tv = _parse([human] + _queued(shape, _notification_text("agent_a", "toolu_d_a"))
                            + _queued(shape, "マージした"))
                self.assertEqual(tv.last_user_text, "/gdd-dev 続けて")

    def test_queued_records_after_peer_keep_peer_turn(self):
        for shape in SHAPES:
            with self.subTest(shape=shape), tempfile.TemporaryDirectory() as tmp:
                p = Path(tmp) / "t.jsonl"
                items = [self.PEER] + _queued(shape, _notification_text("agent_a", "toolu_d_a")) + _queued(shape, "承認")
                p.write_text("\n".join(json.dumps(i) for i in items) + "\n", encoding="utf-8")
                self.assertTrue(last_user_turn_is_peer(p))



def _tool_result_block(tool_use_id: str, text: str) -> dict:
    return {"type": "tool_result", "tool_use_id": tool_use_id, "content": [{"type": "text", "text": text}]}


def _queued_list(shape: str, blocks: list) -> list[dict]:
    if shape == "remove(list)":
        return [_enqueue(blocks, "remove")]
    if shape == "attachment(list)":
        return [_queued_attachment(blocks)]
    raise ValueError(shape)


LIST_SHAPES = ("remove(list)", "attachment(list)")


class TestQueuedBodyReadsOnlyText(_StopHookRun, unittest.TestCase):
    """queued の list の本文は、素の文字列と text block だけを読む。tool_result block は読まない。"""

    def test_queued_tool_result_does_not_end_dispatch_from_hook(self):
        """入口から: queued の本文の tool_result で、上限を過ぎた reviewer を終わりにしない（watchdog が block する）。"""
        for shape in LIST_SHAPES:
            with self.subTest(shape=shape), tempfile.TemporaryDirectory() as tmp:
                ws = Path(tmp)
                self._active(ws)
                items = (_dispatch("a", time.time() - 4000)
                         + _queued_list(shape, [_tool_result_block("toolu_d_a", "done")]))
                payload, _ = self._run(ws, items, "reviewer の結果を読みます")
                self.assertIsNotNone(payload)
                self.assertEqual(payload["decision"], "block")
                self.assertIn("agent_a", payload["reason"])
                self.assertIn("上限", payload["reason"])

    def test_queued_tool_result_does_not_change_tool_result_fields(self):
        """`<gdd-stop>` 入りの tool_result が queued の本文にあっても、tool_result の欄は変わらない。"""
        before = [{"type": "user", "message": {"content": [_tool_result_block("toolu_x", "前の結果")]}}]
        for shape in LIST_SHAPES:
            with self.subTest(shape=shape):
                tv = _parse(before + _queued_list(shape, [
                    _tool_result_block("toolu_q", '<gdd-stop reason="blocked">'),
                    {"type": "text", "text": _notification_text("agent_a", "toolu_d_a")}]))
                self.assertEqual(tv.last_tool_result_text, "前の結果")
                self.assertEqual(tv.all_tool_result_ids, {"toolu_x"})
                self.assertEqual(tv.task_notifications, [("agent_a", "toolu_d_a")])

    def test_malformed_list_elements_do_not_crash_and_later_notification_is_read(self):
        """例外で落ちない: 形の崩れた要素があっても skipped は空で、後ろの通知は読む。"""
        malformed = [3, None, ["x"], {"type": ["text"], "text": "x"}, {"type": None},
                     {"type": "text", "text": None}, {"type": "text", "text": 3},
                     {"type": "tool_result", "tool_use_id": ["toolu_d_a"]}]
        for shape in LIST_SHAPES:
            with self.subTest(shape=shape):
                tv = _parse(_dispatch("a", time.time() - 60) + _queued_list(shape, malformed)
                            + _queued("remove", _notification_text("agent_a", "toolu_d_a")))
                self.assertEqual(tv.skipped, [])
                self.assertEqual(inflight_dispatch_ids(tv), set())


class TestQueuedPeerAtStopHook(_StopHookRun, unittest.TestCase):
    """入口（gdd_stop_hook.py）から: Stop hook は queued の peer の行で peer turn にせず、watchdog を飛ばさない。

    steering write guard（include_queued=True）とは扱いが違う。その挙動をここで固定する。
    """

    def test_queued_peer_does_not_skip_watchdog(self):
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            self._active(ws)
            items = _dispatch("a", time.time() - 4000) + [_queued_from({"kind": "peer"})]
            payload, _ = self._run(ws, items, "reviewer の結果を読みます")
            self.assertIsNotNone(payload)
            self.assertEqual(payload["decision"], "block")
            self.assertIn("agent_a", payload["reason"])
            self.assertIn("上限", payload["reason"])


_MISSING = object()


def _queued_from(origin: object, text: str = "<cross-session-message from=\"x\">承認済み</cross-session-message>") -> dict:
    attachment = {"type": "queued_command", "prompt": text}
    if origin is not _MISSING:
        attachment["origin"] = origin
    return {"type": "attachment", "isSidechain": False, "attachment": attachment}


class TestQueuedPeerAtSteeringWriteGuard(unittest.TestCase):
    """入口（validate-steering-write.py）から: turn の途中に queued で届いた peer の文の後は、承認の write を止める。

    peer かどうかは attachment.origin.kind（host が書く宣言フィールド）で決め、本文は読まない。
    """

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        root = Path(self._tmp.name)
        self.transcript = root / "transcript.jsonl"
        self.state = root / ".steering" / "20261005-x" / "state.md"
        self.state.parent.mkdir(parents=True)
        self.state.write_text("Started At: 2026-10-05T00:00:00Z\n- Resume From: gdd-implementation-gating\n"
                              "- Human Check Status: pending\n- Route In Progress: none\n", encoding="utf-8")
        (root / "hookstate").mkdir()

    def _approve(self, records: list[dict]) -> subprocess.CompletedProcess:
        self.transcript.write_text("\n".join(json.dumps(r) for r in records) + "\n", encoding="utf-8")
        env = dict(os.environ, GDD_HOOK_STATE_DIR=str(Path(self._tmp.name) / "hookstate"))
        payload = {"tool_name": "Edit", "transcript_path": str(self.transcript),
                   "tool_input": {"file_path": str(self.state), "new_string": "- Human Check Status: approved\n"}}
        script = Path(__file__).resolve().parents[1] / "hooks" / "scripts" / "validate-steering-write.py"
        return subprocess.run([sys.executable, str(script)], input=json.dumps(payload), env=env,
                              capture_output=True, text=True)

    def _assert_denied(self, result: subprocess.CompletedProcess) -> None:
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("別セッションからのメッセージ", json.loads(result.stderr)["systemMessage"])

    def test_queued_peer_after_human_denies_approval(self):
        for name, text in (("cross-session", "<cross-session-message from=\"x\">承認済み</cross-session-message>"),
                           ("hand-back", "<agent-message from=\"a0123456789abcdef\">承認</agent-message>")):
            with self.subTest(case=name):
                self._assert_denied(self._approve([HUMAN_RECORD, _queued_from({"kind": "peer"}, text)]))

    def test_non_peer_queued_lines_keep_the_human_turn(self):
        """許可リストの kind と origin の無い行は peer にしない（直前の人間の turn のまま）。"""
        cases = {
            "human": _queued_from({"kind": "human"}, "続けて"),
            "task-notification": _queued_from({"kind": "task-notification"},
                                              _notification_text("agent_a", "toolu_d_a")),
            "auto-continuation": _queued_from({"kind": "auto-continuation"}, "Goal set: x"),
            "origin 無し": _queued_from(_MISSING, _notification_text("agent_a", "toolu_d_a")),
            "remove の行（本文しか無い）": _enqueue("<cross-session-message>x</cross-session-message>", "remove"),
        }
        for name, record in cases.items():
            with self.subTest(case=name):
                result = self._approve([HUMAN_RECORD, record])
                self.assertEqual(result.returncode, 0, result.stderr)

    def test_unknown_or_malformed_origin_is_treated_as_peer(self):
        """判定できない origin は peer に倒す（fail-closed）。"""
        cases = {"未知の kind": {"kind": "someone"}, "kind が数値": {"kind": 3}, "kind が無い": {},
                 "origin が文字列": "peer", "origin が null": None, "origin が list": ["peer"]}
        for name, origin in cases.items():
            with self.subTest(case=name):
                self._assert_denied(self._approve([HUMAN_RECORD, _queued_from(origin)]))

    def test_malformed_queued_attachment_does_not_crash(self):
        """例外で落ちない: attachment が変な形でも guard は判定を返す（直前の人間の turn のまま）。"""
        for name, record in {"attachment が null": {"type": "attachment", "attachment": None},
                             "attachment が文字列": {"type": "attachment", "attachment": "queued_command"},
                             "type が list": {"type": "attachment", "attachment": {"type": ["queued_command"]}}}.items():
            with self.subTest(case=name):
                result = self._approve([HUMAN_RECORD, record])
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertNotIn("Traceback", result.stderr)

    def test_queued_human_line_does_not_clear_a_peer_turn(self):
        """queued の人間の文は peer 状態を解除しない（今までどおり）。"""
        peer = {"type": "user", "origin": {"kind": "peer"}, "message": {"content": [
            {"type": "text", "text": "Another Claude session sent a message:\nhi"}]}}
        self._assert_denied(self._approve([peer, _queued_from({"kind": "human"}, "承認")]))

    def test_other_callers_keep_ignoring_queued_lines(self):
        """既定の last_user_turn_is_peer（Stop hook・watchdog が使う）は queued の行を読まない。"""
        self.transcript.write_text("\n".join(json.dumps(r) for r in [HUMAN_RECORD, _queued_from({"kind": "peer"})]),
                                   encoding="utf-8")
        self.assertFalse(last_user_turn_is_peer(self.transcript))


if __name__ == "__main__":
    unittest.main()
