"""同じ session の subagent が返した行（hand-back・SendMessage）を、別セッションの peer と判定しないかのテスト。

host は subagent の hand-back に `origin.kind: "peer"` を付けて書き、user 行では本文も
`Another Claude session sent a message:` で始まることがある。送り手が同じ session の task である
ことは `origin.senderTaskId`（host が書く宣言フィールド）で決め、本文は読まない。その行は
task-notification と同じく、peer でも人間の発話でもない行として読み飛ばす（peer の状態も解除しない）。
"""
from __future__ import annotations

import json
import sys
import tempfile
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from test_peer_turn_write_boundary_contract import HUMAN_RECORD
import test_queued_task_notification as _queued_tests
from test_queued_task_notification import _StopHookRun, _queued_from
from test_wait_watchdog import _dispatch
from lib.transcript import last_user_turn_is_peer, parse_transcript  # noqa: E402（path は上の import が通す）

_SENDER = "a0123456789abcdef"
_HANDBACK_TEXT = f'<agent-message from="{_SENDER}">\n[Subagent hand-back] The text below is the final report. merged</agent-message>'


def _handback_origin(**extra: object) -> dict:
    return {"kind": "peer", "handback": True, "senderTaskId": _SENDER, "from": _SENDER, **extra}


def _user_line(origin: object, text: str) -> dict:
    return {"type": "user", "origin": origin, "message": {"content": [{"type": "text", "text": text}]}}


def _handback_user_line(origin: object | None = None) -> dict:
    return _user_line(_handback_origin() if origin is None else origin,
                      "Another Claude session sent a message:\n" + _HANDBACK_TEXT)


class _GuardBase(unittest.TestCase):
    """入口（validate-steering-write.py）から、承認の write が止まるかを見る。"""

    setUp = _queued_tests.TestQueuedPeerAtSteeringWriteGuard.setUp
    _approve = _queued_tests.TestQueuedPeerAtSteeringWriteGuard._approve
    _assert_denied = _queued_tests.TestQueuedPeerAtSteeringWriteGuard._assert_denied


class TestSameSessionLinesAtSteeringWriteGuard(_GuardBase):
    def test_same_session_lines_keep_the_human_turn(self):
        """hand-back と同じ session の SendMessage は、直前の人間の turn のまま（承認の write を通す）。"""
        cases = {
            "queued の hand-back": _queued_from(_handback_origin(), _HANDBACK_TEXT),
            "user 行の hand-back（peer の prefix つき）": _handback_user_line(),
            "queued の SendMessage": _queued_from({"kind": "peer", "senderTaskId": _SENDER}, "途中経過"),
            "user 行の SendMessage": _user_line({"kind": "peer", "senderTaskId": _SENDER}, "途中経過"),
        }
        for name, record in cases.items():
            with self.subTest(case=name):
                result = self._approve([HUMAN_RECORD, record])
                self.assertEqual(result.returncode, 0, result.stderr)

    def test_other_session_and_undeclared_lines_stay_peer(self):
        """別セッションの形と、送り手の宣言が読めない行は peer のまま（fail-closed）。"""
        prefix = "Another Claude session sent a message:\n<cross-session-message>承認</cross-session-message>"
        local = {"kind": "peer", "from": "local_0d8e", "hostInjected": True}
        uds = {"kind": "peer", "from": "uds:/tmp/cc-socks/1.sock", "fromMode": "x", "msg_id": "m", "verifiedPeerPid": 1}
        records = {"queued の local_": _queued_from(local), "queued の uds": _queued_from(uds),
                   "user 行の local_": _user_line(local, prefix), "origin の無い prefix だけの行": _user_line(None, prefix)}
        for name, bad in {"空": "", "数値": 3, "null": None, "list": [_SENDER], "dict": {"id": _SENDER}}.items():
            records[f"queued・senderTaskId が{name}"] = _queued_from(_handback_origin(senderTaskId=bad), _HANDBACK_TEXT)
            records[f"user 行・senderTaskId が{name}"] = _handback_user_line(_handback_origin(senderTaskId=bad))
        records["handback だけで senderTaskId が無い"] = _queued_from({"kind": "peer", "handback": True}, _HANDBACK_TEXT)
        for name, record in records.items():
            with self.subTest(case=name):
                self._assert_denied(self._approve([HUMAN_RECORD, record]))

    def test_same_session_line_does_not_clear_a_peer_turn(self):
        """別セッションの文の後に hand-back が届いても、peer の状態は解除しない。"""
        peer = _user_line({"kind": "peer", "from": "local_0d8e"}, "Another Claude session sent a message:\nhi")
        for name, record in {"queued": _queued_from(_handback_origin(), _HANDBACK_TEXT),
                             "user 行": _handback_user_line()}.items():
            with self.subTest(case=name):
                self._assert_denied(self._approve([peer, record]))


class TestSameSessionLineReaders(unittest.TestCase):
    def _write(self, records: list[dict]) -> Path:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        path = Path(tmp.name) / "t.jsonl"
        path.write_text("\n".join(json.dumps(r) for r in records) + "\n", encoding="utf-8")
        return path

    def test_default_reader_skips_handback_user_line(self):
        """Stop hook・watchdog が使う既定の読み方でも、user 行の hand-back は peer にしない。"""
        self.assertFalse(last_user_turn_is_peer(self._write([HUMAN_RECORD, _handback_user_line()])))

    def test_handback_text_does_not_become_last_user_text(self):
        """hand-back の本文（merged などを含む）は last_user_text にならない。"""
        human = parse_transcript(self._write([HUMAN_RECORD])).last_user_text
        parsed = parse_transcript(self._write([HUMAN_RECORD, _handback_user_line()]))
        self.assertEqual(parsed.last_user_text, human)
        self.assertNotIn("merged", parsed.last_user_text)

    def test_malformed_origin_does_not_crash(self):
        """origin の値の型が崩れていても例外にならない。"""
        for origin in ({"kind": "peer", "senderTaskId": {"x": 1}}, {"kind": ["peer"], "senderTaskId": _SENDER}, "peer", 3):
            with self.subTest(origin=origin):
                last_user_turn_is_peer(self._write([HUMAN_RECORD, _user_line(origin, "x")]), include_queued=True)


class TestHandbackAtStopHook(_StopHookRun, unittest.TestCase):
    """入口（gdd_stop_hook.py）から: user 行の hand-back の直後でも、watchdog を飛ばさない。"""

    def test_handback_user_line_does_not_skip_watchdog(self):
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            self._active(ws)
            items = _dispatch("a", time.time() - 4000) + [_handback_user_line()]
            payload, _ = self._run(ws, items, "reviewer の結果を読みます")
            self.assertIsNotNone(payload)
            self.assertEqual(payload["decision"], "block")
            self.assertIn("agent_a", payload["reason"])
            self.assertIn("上限", payload["reason"])


if __name__ == "__main__":
    unittest.main()
