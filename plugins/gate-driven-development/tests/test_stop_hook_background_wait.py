"""Stop hook は、まだ終わっていない待ちの background の Bash があれば、継続の押し返しを出さない。

待ちの形は許可リストで閉じる（期限 timer の単独の `sleep <秒>` と、`wait-until.py` を起動するコマンド）。
ほかの background の Bash（テストの実行、`until … sleep` の loop など）は待ちに数えない。起動の時刻の窓は
マージ待ちの押し返し（autonomy_pushback）と同じ BACKGROUND_WINDOW_SECONDS にする。
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
from lib.transcript import parse_transcript


def _ago(seconds: float) -> str:
    return datetime.fromtimestamp(time.time() - seconds, timezone.utc).isoformat().replace("+00:00", "Z")


_WAIT_UNTIL = "python3 /x/plugins/gate-driven-development/scripts/wait-until.py --timeout 3000 --pr-checks 7"


def _bg_bash(at: object = "now", *, ack: bool = True, command: str = "sleep 3660") -> list[dict]:
    launch = {"type": "assistant", "message": {"content": [
        {"type": "tool_use", "id": "toolu_bg_1", "name": "Bash",
         "input": {"command": command, "run_in_background": True}}]}}
    if at is not None:
        launch["timestamp"] = _ago(0) if at == "now" else at
    content = "Command running in background with ID: bash_1. Output is being written to: /tmp/x" if ack else "done"
    return [launch, {"type": "user", "message": {"content": [
        {"type": "tool_result", "tool_use_id": "toolu_bg_1", "content": content}]}}]


_NOTIFIED = {"type": "user", "message": {"content": [{"type": "text", "text": (
    "<task-notification>\n<task-id>bash_1</task-id>\n<tool-use-id>toolu_bg_1</tool-use-id>\n"
    "<status>completed</status>\n<summary>done</summary>\n</task-notification>")}]}}


def _transcript(path: Path, middle: list[dict]) -> Path:
    lines = [
        {"type": "user", "message": {"content": [{"type": "text", "text": "/gdd-dev"}]}},
        *middle,
        {"type": "assistant", "message": {"content": [
            {"type": "text", "text": "continuing /gdd-dev. CI の完了通知を待ちます。"}]}},
    ]
    path.write_text("\n".join(json.dumps(x) for x in lines) + "\n", encoding="utf-8")
    return path


class BackgroundWaitSuppressesContinuationTests(unittest.TestCase):
    def _stop(self, middle: list[dict]) -> tuple[int, str, str]:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        workspace = Path(tmp.name)
        _write_state_file(workspace, {"active": "true", "session_id": "test-session", "iteration": "1",
                                      "workflow_runtime": "claude_code"})
        return _run_hook(workspace, transcript_path=_transcript(workspace / "transcript.jsonl", middle))

    def _assert_nudge(self, result: tuple[int, str, str]) -> None:
        code, out, err = result
        self.assertEqual(code, 0, err)
        payload = json.loads(out)
        self.assertEqual(payload.get("decision"), "block", out)
        self.assertTrue(payload["reason"].startswith("Continue the active `/gdd-dev` run"), out)

    def test_running_wait_bash_suppresses_the_nudge(self) -> None:
        for command in ("sleep 3660", "  sleep 3000  ", _WAIT_UNTIL,
                        "gh pr comment 7 --body x >/dev/null && echo ok; " + _WAIT_UNTIL + "; echo exit=$?",
                        "${CLAUDE_PLUGIN_ROOT}/scripts/wait-until.py --timeout 600 -- gh run list",
                        '"${CLAUDE_PLUGIN_ROOT}/scripts/wait-until.py" --timeout 600 -- true',
                        "gh pr checks 7 || " + _WAIT_UNTIL):
            with self.subTest(command=command):
                code, out, err = self._stop(_bg_bash(command=command))
                self.assertEqual(code, 0, err)
                self.assertEqual(out, "")

    def test_running_background_bash_outside_the_allowlist_does_not_suppress(self) -> None:
        for command in ("uv run pytest tests/unit/ -q", "gh pr checks 7 --watch",
                        'until grep -q done "$S"; do sleep 5; done', "sleep 5 && gh pr merge 7",
                        "sleep 1m", "sleep", "sleep 60; make deploy", "python3 wait-until.pyc", "my-wait-until.py.bak",
                        "cat /x/scripts/wait-until.py", "grep -n timeout scripts/wait-until.py",
                        "echo wait-until.py; npm run dev"):
            with self.subTest(command=command):
                self._assert_nudge(self._stop(_bg_bash(command=command)))

    def test_finished_background_bash_does_not_suppress(self) -> None:
        self._assert_nudge(self._stop([*_bg_bash(), _NOTIFIED]))

    def test_no_background_work_does_not_suppress(self) -> None:
        self._assert_nudge(self._stop([]))

    def test_launch_older_than_the_window_does_not_suppress(self) -> None:
        self._assert_nudge(self._stop(_bg_bash(at=_ago(BACKGROUND_WINDOW_SECONDS + 60))))

    def test_launch_without_a_readable_time_does_not_suppress(self) -> None:
        self._assert_nudge(self._stop(_bg_bash(at=None)))
        self._assert_nudge(self._stop(_bg_bash(at="not-a-time")))

    def test_launch_without_a_shell_id_does_not_suppress(self) -> None:
        self._assert_nudge(self._stop(_bg_bash(ack=False)))


class BackgroundWaitGuardFailsOpenTests(unittest.TestCase):
    def test_exception_in_the_background_check_keeps_the_nudge_and_is_logged(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            tv = parse_transcript(_transcript(root / "transcript.jsonl", _bg_bash()))
            with mock.patch.object(gdd_stop_hook, "any_background_wait_running", side_effect=RuntimeError("boom")), \
                    mock.patch.object(gdd_stop_hook, "append_hook_error") as logged:
                gdd_stop_hook._continuation_intent_guard(
                    tv, root, str(root / "transcript.jsonl"), root / "transcript.jsonl", tv.last_assistant_text)
            self.assertTrue(any("boom" in str(c) for c in logged.call_args_list), logged.call_args_list)


if __name__ == "__main__":
    unittest.main()
