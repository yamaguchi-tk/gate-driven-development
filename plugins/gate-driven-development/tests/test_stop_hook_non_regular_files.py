"""stop hook が読む tasklist.md・requirements.md・state.md・post-merge の marker・gdd-dev.local.md が通常のファイルでないとき。

FIFO は書き手が来るまで open が戻らないので、hook が timeout まで止まる。ディレクトリ・
symlink のループ・指す先の無い symlink を「無い」と取り違えると、done guard が素通りする。
tasklist.md・requirements.md・state.md・marker は止める側に倒す。gdd-dev.local.md は shell 側の
`[[ -f ]]` と同じく止めず、記録して停止を通す。
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _stop_hook_test_base import (  # noqa: E402
    _CLEAN_STATE,
    _CLEAN_TASKLIST,
    _make_transcript_jsonl,
    _run_hook,
    _write_binding,
    _write_state_file,
    _write_steering,
)

NEXT_ACTION = "\n\n## 👤 次にすること\n完了（追加対応なし）"
KINDS = ("fifo", "directory", "loop", "dangling")
POST_MERGE_TEXT = "post-merge verification を実施しました。state/tasklist を re-read しました。"


def _setup(ws: Path) -> Path:
    _write_state_file(ws, {"active": "true", "session_id": "test-session", "iteration": "1"})
    steering_dir = _write_steering(ws, "20260620-task", _CLEAN_TASKLIST, _CLEAN_STATE)
    _write_binding(ws, "20260620-task")
    return steering_dir


def _stop(ws: Path, user_text: str | None = None, assistant_text: str = "") -> str:
    transcript = ws / "transcript.jsonl"
    kwargs = {"assistant_text": assistant_text or '<gdd-stop reason="done">' + NEXT_ACTION}
    if user_text is not None:
        kwargs["user_text"] = user_text
    _make_transcript_jsonl(transcript, **kwargs)
    code, out, _ = _run_hook(ws, transcript, session_id="test-session")
    assert code == 0
    return out


def _replace(path: Path, kind: str) -> None:
    path.unlink(missing_ok=True)
    if kind == "fifo":
        os.mkfifo(path)
    elif kind == "directory":
        path.mkdir()
    elif kind == "dangling":
        os.symlink("missing-target", path)
    else:
        os.symlink(path.name, path)


class TasklistTests(unittest.TestCase):
    def test_non_regular_tasklist_blocks_done(self) -> None:
        for kind in KINDS:
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as tmp:
                ws = Path(tmp)
                _replace(_setup(ws) / "tasklist.md", kind)
                payload = json.loads(_stop(ws).strip())
                self.assertEqual(payload["decision"], "block")
                self.assertIn("tasklist.md", payload["reason"])

    def test_missing_tasklist_allows_done(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            (_setup(ws) / "tasklist.md").unlink()
            self.assertNotIn('"decision": "block"', _stop(ws))


class RequirementsTests(unittest.TestCase):
    def test_fifo_requirements_blocks_done_without_next_plan(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            os.mkfifo(_setup(ws) / "requirements.md")
            payload = json.loads(_stop(ws).strip())
            self.assertEqual(payload["decision"], "block")
            self.assertIn("次の計画", payload["reason"])


class PostMergeMarkerTests(unittest.TestCase):
    def test_non_regular_marker_blocks_merge_stop(self) -> None:
        for kind in KINDS:
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as tmp:
                ws = Path(tmp)
                _setup(ws)
                marker = ws / ".claude" / "gdd-post-merge-continuation.json"
                _replace(marker, kind)
                payload = json.loads(
                    _stop(
                        ws,
                        user_text="マージした",
                        assistant_text=POST_MERGE_TEXT + '<gdd-stop reason="done">' + NEXT_ACTION,
                    ).strip()
                )
                self.assertEqual(payload["decision"], "block")
                self.assertIn("gdd-post-merge-continuation.json", payload["reason"])


class StateMdTests(unittest.TestCase):
    def test_non_regular_state_md_blocks_done(self) -> None:
        for kind in KINDS:
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as tmp:
                ws = Path(tmp)
                _replace(_setup(ws) / "state.md", kind)
                payload = json.loads(_stop(ws).strip())
                self.assertEqual(payload["decision"], "block")
                self.assertIn("state.md を通常のファイルとして読めない", payload["reason"])
                self.assertIn("20260620-task", payload["reason"])
                self.assertIn("通常のファイルに置き換え", payload["reason"])


class LocalStateTests(unittest.TestCase):
    def test_non_regular_local_state_returns_and_is_recorded(self) -> None:
        for kind in KINDS:
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as tmp:
                ws = Path(tmp)
                _setup(ws)
                _replace(ws / ".claude" / "gdd-dev.local.md", kind)
                transcript = ws / "transcript.jsonl"
                _make_transcript_jsonl(transcript, assistant_text='<gdd-stop reason="done">' + NEXT_ACTION)
                code, out, err = _run_hook(ws, transcript, session_id="test-session", timeout=20)
                self.assertEqual(code, 0)
                self.assertNotIn('"decision": "block"', out)
                self.assertIn("parse_state", err)


class UnlistableSteeringTests(unittest.TestCase):
    """bind が無く `.steering` を一覧できない（読み取り権限が無い）とき。

    ポーリング上限のための steering の選び方は external-review-waiting の停止でだけ走らせる。
    ほかの停止理由で走らせると、一覧の例外で hook が落ち、wrapper が block に変えて pause が
    強制継続になる。external-review-waiting では回数を確かめられないので `blocked` に倒して記録する。
    """

    def _run(self, reason: str) -> tuple[Path, str]:
        if os.geteuid() == 0:
            self.skipTest("root は権限を落としても読めてしまう")
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        ws = Path(tmp.name)
        _write_state_file(ws, {"active": "true", "session_id": "test-session", "iteration": "1"})
        steering = _write_steering(ws, "20260620-task", _CLEAN_TASKLIST, _CLEAN_STATE).parent
        steering.chmod(0o300)
        self.addCleanup(steering.chmod, 0o755)
        out = _stop(ws, assistant_text=f'<gdd-stop reason="{reason}">' + NEXT_ACTION)
        return ws, out

    def test_human_check_waiting_pauses_without_crashing(self) -> None:
        ws, out = self._run("human-check-waiting")
        self.assertNotIn('"decision": "block"', out)
        self.assertTrue((ws / ".claude" / "gdd-dev.local.md").is_file())  # pause は local state を残す

    def test_external_review_waiting_is_blocked_and_recorded(self) -> None:
        ws, out = self._run("external-review-waiting")
        self.assertNotIn('"decision": "block"', out)
        self.assertFalse((ws / ".claude" / "gdd-dev.local.md").exists())  # blocked は local state を消す
        self.assertIn("pr_review_poll_cap", (ws / ".gdd" / "hook-errors.log").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
