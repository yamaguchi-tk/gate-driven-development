"""途中（interim）の完了通知を、background の dispatch の終わりに数えないことのテスト。

subagent が自分の background の処理を残したまま返ると、host は <status>completed</status> に
「This agent stopped with background work of its own still running …」の <note> を付けた通知を出し、
処理が終わると同じ task-id でもう一度通知する。途中の通知を終わりに数えると、待っているだけの
main に Stop hook が継続を押し返し、期限の見張りも外れる。
"""
from __future__ import annotations

import sys
import time
from pathlib import Path as _P

sys.path.insert(0, str(_P(__file__).parent))
from _stop_hook_test_base import *  # noqa: F401,F403
from git_pre_push_review import _reviewer_outcomes
from lib.transcript import finished_task_ids, inflight_dispatch_ids, parse_transcript

# 実際の transcript にある 2 つの note（host の文言そのまま）。省略記号の形も実在する
_INTERIM_NOTE = (
    "This agent stopped with background work of its own still running. It may resume on its own when "
    "that work completes or reports, and the same task-id notifies again if it does; the result below may be interim."
)
_INTERIM_NOTE_ELIDED = "This agent stopped with background work of its own still running … the result below may be interim."
_FINAL_NOTE = (
    "A task-notification fires each time this agent stops with no live background children of its own. "
    "The user can send it another message and resume it, so the same task-id may notify more than once."
)


def _dispatch(n: str, at: float, subagent_type: str = "general-purpose") -> list[dict]:
    return [
        {"type": "assistant", "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(at)), "message": {"content": [
            {"type": "tool_use", "id": f"toolu_d_{n}", "name": "Agent",
             "input": {"subagent_type": subagent_type, "run_in_background": True, "prompt": "..."}}]}},
        {"type": "user", "message": {"content": [
            {"type": "tool_result", "tool_use_id": f"toolu_d_{n}",
             "content": f"Async agent launched successfully.\nagentId: agent_{n} (internal ID)"}]}},
    ]


def _notification(n: str, note: str | None, result: str = "結果") -> dict:
    """実際の通知と同じ順（task-id・tool-use-id・output-file・status・summary・note・result）で作る。"""
    note_line = f"<note>{note}</note>\n" if note is not None else ""
    text = (
        f"<task-notification>\n<task-id>agent_{n}</task-id>\n<tool-use-id>toolu_d_{n}</tool-use-id>\n"
        f"<output-file>/tmp/tasks/agent_{n}.output</output-file>\n<status>completed</status>\n"
        f"<summary>Agent \"x\" finished</summary>\n{note_line}<result>{result}</result>\n</task-notification>"
    )
    return {"type": "user", "message": {"content": [{"type": "text", "text": text}]}}


_FIXTURES = _P(__file__).parent / "fixtures" / "interim-task-notification"


def _recorded(name: str, n: str) -> dict:
    """実際の transcript から写した通知（id・パス・summary・result は伏せた）。"""
    text = (_FIXTURES / f"{name}.txt").read_text(encoding="utf-8")
    text = text.replace("{task_id}", f"agent_{n}").replace("{tool_use_id}", f"toolu_d_{n}")
    return {"type": "user", "message": {"content": [{"type": "text", "text": text}]}}


def _parse(items: list[dict]):
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "t.jsonl"
        path.write_text("\n".join(json.dumps(i) for i in items) + "\n", encoding="utf-8")
        return parse_transcript(path, Path(tmp))


class TestInterimNotificationParsing(unittest.TestCase):
    def test_interim_notification_does_not_end_the_dispatch(self):
        for note in (_INTERIM_NOTE, _INTERIM_NOTE_ELIDED):
            with self.subTest(note=note[-30:]):
                tv = _parse(_dispatch("a", time.time() - 60) + [_notification("a", note)])
                self.assertEqual(inflight_dispatch_ids(tv), {"toolu_d_a"})
                self.assertNotIn("agent_a", finished_task_ids(tv))
                self.assertEqual(tv.completed_notifications, [])

    def test_recorded_notifications(self):
        """実際の通知の写し: 途中の通知だけなら実行中、終わりの通知が来たら終わり。"""
        tv = _parse(_dispatch("a", time.time() - 60) + [_recorded("interim", "a")])
        self.assertEqual(inflight_dispatch_ids(tv), {"toolu_d_a"})
        tv = _parse(_dispatch("a", time.time() - 60) + [_recorded("interim", "a"), _recorded("final", "a")])
        self.assertEqual(inflight_dispatch_ids(tv), set())

    def test_later_final_notification_ends_the_dispatch(self):
        for note in (_FINAL_NOTE, None):
            with self.subTest(final_note=note is not None):
                tv = _parse(_dispatch("a", time.time() - 60)
                            + [_notification("a", _INTERIM_NOTE), _notification("a", note)])
                self.assertEqual(inflight_dispatch_ids(tv), set())
                self.assertIn(("agent_a", "toolu_d_a"), tv.completed_notifications)

    def test_interim_note_quoted_in_the_result_does_not_keep_it_running(self):
        """subagent が本文（<result>）に note を引用しても、終わりの通知は終わりに数える。"""
        tv = _parse(_dispatch("a", time.time() - 60)
                    + [_notification("a", _FINAL_NOTE, result=f"引用: <note>{_INTERIM_NOTE}</note>")])
        self.assertEqual(inflight_dispatch_ids(tv), set())

    def test_unclosed_interim_note_is_still_interim(self):
        """閉じタグの欠けた note も、接頭辞があれば途中として扱う（待つ側に倒す）。"""
        text = ("<task-notification>\n<task-id>agent_a</task-id>\n<tool-use-id>toolu_d_a</tool-use-id>\n"
                f"<status>completed</status>\n<summary>s</summary>\n<note>{_INTERIM_NOTE}\n<result>r</result>\n"
                "</task-notification>")
        tv = _parse(_dispatch("a", time.time() - 60)
                    + [{"type": "user", "message": {"content": [{"type": "text", "text": text}]}}])
        self.assertEqual(inflight_dispatch_ids(tv), {"toolu_d_a"})

    def test_reviewer_with_only_interim_notification_is_running(self):
        """push 前のレビューの確認も、途中の通知だけの reviewer を ok にしない。"""
        tv = _parse(_dispatch("a", time.time() - 60, "light-lane-independent-reviewer")
                    + [_notification("a", _INTERIM_NOTE)])
        self.assertEqual([o[0] for o in _reviewer_outcomes(tv)], ["running"])


class TestInterimNotificationFromHook(unittest.TestCase):
    """入口（gdd_stop_hook.py）から: 途中の通知しか来ていない dispatch は、まだ待っている扱いにする。"""

    def _run(self, ws: Path, items: list[dict], body: str) -> dict | None:
        transcript = ws / "transcript.jsonl"
        head = [{"type": "user", "message": {"content": [{"type": "text", "text": "/gdd-dev"}]}}]
        tail = [{"type": "assistant", "message": {"content": [{"type": "text", "text": body}]}}]
        transcript.write_text("\n".join(json.dumps(i) for i in head + items + tail) + "\n", encoding="utf-8")
        code, out, err = _run_hook(ws, transcript)
        self.assertEqual(code, 0, err)
        return json.loads(out) if out.strip().startswith("{") else None

    def _active(self, ws: Path) -> Path:
        return _write_state_file(ws, {"active": "true", "session_id": "test-session", "iteration": "1"})

    def test_continuation_is_not_pushed_while_only_interim_arrived(self):
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            self._active(ws)
            for notification in (_notification("a", _INTERIM_NOTE), _recorded("interim", "a")):
                items = _dispatch("a", time.time() - 60) + [notification]
                self.assertIsNone(self._run(ws, items, "担当役の完了を待っています。"))

    def test_continuation_is_pushed_after_the_final_notification(self):
        """対照: 終わりの通知が来た後は、今までどおり継続を押し返す。"""
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            self._active(ws)
            items = _dispatch("a", time.time() - 60) + [_notification("a", _INTERIM_NOTE),
                                                        _notification("a", _FINAL_NOTE)]
            payload = self._run(ws, items, "担当役の完了を待っています。")
            self.assertIsNotNone(payload)
            self.assertEqual(payload["decision"], "block")

    def test_state_clearing_stop_is_held_while_only_interim_arrived(self):
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            state = self._active(ws)
            items = _dispatch("a", time.time() - 60) + [_notification("a", _INTERIM_NOTE)]
            payload = self._run(ws, items, '止めます。<gdd-stop reason="blocked">\n\n## 👤 次にすること\n- 待つ')
            self.assertIsNotNone(payload)
            self.assertEqual(payload["decision"], "block")
            self.assertIn("agent_a", payload["reason"])
            self.assertTrue(state.exists())


if __name__ == "__main__":
    unittest.main()
