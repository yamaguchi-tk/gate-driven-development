"""`記録の場所: なし` の印の付け忘れの知らせ（human check の返事を受けたターンの Stop）の E2E。

hook の入口（run-display-marker-hook.sh）を subprocess で起動し、transcript と steering を一時ディレクトリに置いて確かめる。
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from _paths import PLUGIN_ROOT  # noqa: E402

HOOK = PLUGIN_ROOT / "hooks" / "scripts" / "run-display-marker-hook.sh"
MARKER = '<gdd-stop reason="human-check-waiting">'
ROW = "| 3 | 依「全件を消す」 | 既存とぶつかる | 依頼の側に仮決定。記録の場所: なし |"
OTHER_ROW = "| 4 | 依「毎日回す」 | 既存とぶつかる | 依頼の側に仮決定。記録の場所: なし |"
DISPLAY = f"## 確認\n### ズレ確認\n{ROW}\n推奨: 案 A で進めます。\n{MARKER}\n## 👤 次にすること\nOK と返信してください"
MARKED = " / 表示: 済み"


def human(text: str) -> dict:
    return {"type": "user", "origin": {"kind": "human"}, "message": {"content": text}}


def assistant(text: str) -> dict:
    return {"type": "assistant", "message": {"content": [{"type": "text", "text": text}]}}


CROSS_SESSION = {"type": "user", "origin": {"kind": "cross-session"}, "message": {"content": "OK"}}
COMPACT = {"type": "system", "subtype": "compact_boundary", "content": "Conversation compacted"}


def requirements(*rows: str) -> str:
    return "# 要件\n\n### ズレ確認\n\n| # | 原文 | 判定 | 根拠 |\n|---|---|---|---|\n" + "\n".join(rows) + "\n"


class DisplayMarkerHookTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = Path(tmp.name)
        self.repo = self.dir / "repo"
        self.repo.mkdir()
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True)
        self.steering = self.repo / ".steering" / "20261116-task"
        self.steering.mkdir(parents=True)
        self.state = self.dir / "state"
        self.transcript = self.dir / "t.jsonl"

    def write(self, records: list[dict], *rows: str) -> None:
        self.transcript.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in records) + "\n", encoding="utf-8")
        (self.steering / "requirements.md").write_text(requirements(*rows), encoding="utf-8")

    def run_hook(self, **payload_extra) -> subprocess.CompletedProcess:
        payload = {
            "session_id": "s1",
            "transcript_path": str(self.transcript),
            "cwd": str(self.repo),
            "stop_hook_active": False,
        }
        payload.update(payload_extra)
        env = dict(os.environ)
        env["HOME"] = str(self.dir)
        env["GDD_HOOK_STATE_DIR"] = str(self.state)
        env["CLAUDE_PLUGIN_ROOT"] = str(PLUGIN_ROOT)
        env.pop("GDD_DISABLE_HOOKS", None)
        result = subprocess.run(["bash", str(HOOK)], input=json.dumps(payload), capture_output=True, text=True,
                                env=env, cwd=str(self.repo), timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result

    def message(self, result: subprocess.CompletedProcess) -> str:
        self.assertTrue(result.stdout.strip(), "知らせが出ていない")
        output = json.loads(result.stdout)
        self.assertNotIn("decision", output, "知らせだけで、止めてはいけない")
        return output["systemMessage"]

    def log_lines(self) -> list[dict]:
        path = self.state / "display-marker.log"
        if not path.is_file():
            return []
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

    def test_warns_when_the_reply_turn_leaves_the_row_unmarked(self):
        self.write([human("依頼"), assistant(DISPLAY), human("OK"), assistant("設計に進みます。")], ROW)
        text = self.message(self.run_hook())
        self.assertIn(MARKED.strip(), text)
        self.assertIn("1 行", text)
        self.assertIn(str(self.steering / "requirements.md"), text)

    def test_counts_only_the_unmarked_rows(self):
        self.write([human("依頼"), assistant(DISPLAY.replace(ROW, ROW + "\n" + OTHER_ROW)), human("OK"), assistant("進めます。")],
                   ROW + MARKED, OTHER_ROW)
        self.assertIn("1 行", self.message(self.run_hook()))

    def test_silent_when_only_rows_not_on_the_display_are_unmarked(self):
        self.write([human("依頼"), assistant(DISPLAY), human("OK"), assistant("進めます。")], ROW + MARKED, OTHER_ROW)
        self.assertEqual(self.run_hook().stdout.strip(), "")

    def test_says_when_a_displayed_row_is_not_in_requirements(self):
        self.write([human("依頼"), assistant(DISPLAY), human("OK"), assistant("進めます。")], OTHER_ROW + MARKED)
        text = self.message(self.run_hook())
        self.assertIn("見つからない", text)
        self.assertIn("1 行", text)

    def test_matches_the_row_whatever_the_list_mark(self):
        self.write([human("依頼"), assistant(DISPLAY.replace(ROW, "- " + ROW.strip("| ").replace(" | ", "｜"))), human("OK"),
                    assistant("進めます。")], ROW + MARKED)
        self.assertEqual(self.run_hook().stdout.strip(), "")

    def test_silent_when_every_row_is_marked(self):
        self.write([human("依頼"), assistant(DISPLAY), human("OK"), assistant("進めます。")], ROW + MARKED)
        self.assertEqual(self.run_hook().stdout.strip(), "")

    def test_silent_at_the_stop_that_shows_the_display(self):
        self.write([human("依頼"), assistant(DISPLAY)], ROW)
        self.assertEqual(self.run_hook().stdout.strip(), "")

    def test_silent_when_the_reply_is_not_from_the_person(self):
        self.write([human("依頼"), assistant(DISPLAY), CROSS_SESSION, assistant("情報のみとして記録しました。")], ROW)
        self.assertEqual(self.run_hook().stdout.strip(), "")

    def test_silent_after_compaction_between_the_display_and_the_reply(self):
        self.write([human("依頼"), assistant(DISPLAY), COMPACT, human("OK"), assistant("進めます。")], ROW)
        self.assertEqual(self.run_hook().stdout.strip(), "")

    def test_silent_when_the_reply_turn_shows_the_check_again(self):
        self.write([human("依頼"), assistant(DISPLAY), human("3 は別の案にして"), assistant(DISPLAY)], ROW)
        self.assertEqual(self.run_hook().stdout.strip(), "")

    def test_silent_when_the_display_has_no_such_row(self):
        self.write([human("依頼"), assistant(DISPLAY.replace(ROW + "\n", "")), human("OK"), assistant("進めます。")], ROW)
        self.assertEqual(self.run_hook().stdout.strip(), "")

    def test_silent_on_a_later_turn(self):
        self.write([human("依頼"), assistant(DISPLAY), human("OK"), assistant("進めます。"), human("続けて"), assistant("続けます。")], ROW)
        self.assertEqual(self.run_hook().stdout.strip(), "")

    def test_silent_when_stop_hook_is_active(self):
        self.write([human("依頼"), assistant(DISPLAY), human("OK"), assistant("進めます。")], ROW)
        self.assertEqual(self.run_hook(stop_hook_active=True).stdout.strip(), "")

    def test_never_stops_on_an_unreadable_transcript(self):
        self.write([human("依頼")], ROW)
        self.assertEqual(self.run_hook(transcript_path=str(self.dir / "missing.jsonl")).stdout.strip(), "")
        self.transcript.write_text("{not json\n", encoding="utf-8")
        self.assertEqual(self.run_hook().stdout.strip(), "")

    def test_never_stops_without_requirements(self):
        self.write([human("依頼"), assistant(DISPLAY), human("OK"), assistant("進めます。")], ROW)
        (self.steering / "requirements.md").unlink()
        self.assertEqual(self.run_hook().stdout.strip(), "")

    def test_never_stops_on_a_malformed_payload(self):
        result = subprocess.run(["bash", str(HOOK)], input="[1, 2]", capture_output=True, text=True, timeout=30,
                                env={**os.environ, "HOME": str(self.dir), "GDD_HOOK_STATE_DIR": str(self.state)})
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), "")

    def test_logs_each_warning_for_the_later_reading(self):
        self.write([human("依頼"), assistant(DISPLAY), human("OK"), assistant("進めます。")], ROW)
        self.run_hook()
        lines = self.log_lines()
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0]["session_id"], "s1")
        self.assertEqual((lines[0]["shown"], lines[0]["unmarked"], lines[0]["missing"]), (1, 1, 0))
        self.assertNotIn("全件を消す", json.dumps(lines[0], ensure_ascii=False), "行の本文は記録に残さない")

    def test_logs_the_marked_case_too(self):
        self.write([human("依頼"), assistant(DISPLAY), human("OK"), assistant("進めます。")], ROW + MARKED)
        self.run_hook()
        self.assertEqual([(l["shown"], l["unmarked"], l["missing"]) for l in self.log_lines()], [(1, 0, 0)])


if __name__ == "__main__":
    unittest.main()
