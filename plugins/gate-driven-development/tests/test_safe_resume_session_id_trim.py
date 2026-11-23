"""SessionStart の Safe Resume が、stored session_id の末尾の空白・CR を落として照合する契約テスト。

Safe Resume Candidate Mode（`run-session-start-hook.sh`）は `.claude/gdd-dev.local.md` の
`session_id:` を `STORED_SESSION_ID` に読み、現在の `CLAUDE_CODE_SESSION_ID` と比べる。
この読み取りだけが末尾の空白・CR を落とさず、手で編集した・改行コードを変換した
local state では、同じ session でも Candidate Mode（`[gdd:paused]`）が誤発火していた
（PR #140 の review-log の Z6 / V13 / Q1）。

同じファイルを読む `gdd_session_continuity_ok`（`lib/detect-steering.sh`）と
`state_io.py::parse_state` は末尾を落とす。本テストは、現在の session id が非空の入力に限って、
Safe Resume の結論を `gdd_session_continuity_ok` と同じ入力表で突き合わせる。
現在の session id が空の入力では、Safe Resume の連鎖に soft note の分岐があるため
2 実装は元々一致しない（本テストは検知しない。限界として changelog に書いた）。

fixture は `git init` のみで commit しない（HEAD が無いので既定ブランチ・branch 名の判定は
通らず、session_id の判定に届く。`test_p0_p1_operational_hardening_contract.py` と同じ型）。
"""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from _paths import PLUGIN_ROOT as ROOT
HOOK = ROOT / "hooks" / "scripts" / "run-session-start-hook.sh"
DETECT_STEERING = ROOT / "hooks" / "scripts" / "lib" / "detect-steering.sh"

CURRENT = "sess-current"
PAUSED_MARK = "Safe Resume Candidate Mode"
STEERING_NAME = "20260606-human-check-pending"
STATE_MD = (
    "Resume From: human-check-waiting\n"
    "Human Check Status: pending\n"
    "Route In Progress: none\n"
)
_LEAKED_ENV = (
    "GDD_STEERING_DIR", "GDD_HOOK_STATE_DIR",
    "GDD_MAX_AUTO_CYCLES", "CLAUDE_CODE_SESSION_ID", "GDD_WORKTREES_ROOT",
)

LF = b"\n"
CRLF = b"\r\n"

# (名前, 現在の session id, `session_id:` の行（改行を除く）, 行末, 期待)
# 期待: "same" = 同じ session（Candidate Mode にならない）、"different" = Candidate Mode
CASES = [
    ("control: 一致（LF）", CURRENT, b"session_id: sess-current", LF, "same"),
    ("session_id の行だけ末尾が CR", CURRENT, b"session_id: sess-current\r", LF, "same"),
    ("ファイル全体が CRLF", CURRENT, b"session_id: sess-current", CRLF, "same"),
    ("末尾の空白", CURRENT, b"session_id: sess-current   ", LF, "same"),
    ("末尾のタブ", CURRENT, b"session_id: sess-current\t", LF, "same"),
    ("末尾の空白・タブ・CR の混在", CURRENT, b"session_id: sess-current \t \r", LF, "same"),
    ("コロンの後に空白なし＋CR", CURRENT, b"session_id:sess-current\r", LF, "same"),
    ("値の途中に空白（末尾に CR）", "ab cd", b"session_id: ab cd \r", LF, "same"),
    # block すべき入力が allow にならない
    ("別の ID（末尾の空白・CR 付き）", CURRENT, b"session_id: other-session \r", LF, "different"),
    ("別の ID（そのまま）", CURRENT, b"session_id: other-session", LF, "different"),
    ("値の途中の空白は保持する（全空白を除去すると一致してしまう）", "abcd", b"session_id: ab cd", LF, "different"),
    ("値の途中に空白が無い stored とは一致しない", "ab cd", b"session_id: abcd", LF, "different"),
    ("値の途中の空白の数が違う", "ab cd", b"session_id: ab  cd", LF, "different"),
    # 判定できないときに通らない
    ("値が空", CURRENT, b"session_id: ", LF, "different"),
    ("値が CR だけ", CURRENT, b"session_id:\r", LF, "different"),
    ("値が空白・タブ・CR だけ", CURRENT, b"session_id: \t \r", LF, "different"),
    ("session_id の行が無い", CURRENT, None, LF, "different"),
    ("UTF-8 として不正なバイト列", CURRENT, b"session_id: \xff\xfe", LF, "different"),
    # 現在の session id 側は trim しない（両側 trim にすると、空白だけの現在 id が空扱いになり
    # soft note の経路（reboot）に落ちる。block → allow の反転）
    ("現在の id が空白だけで stored が空", " ", b"session_id: ", LF, "different"),
]


def _local_state(session_line: bytes | None, eol: bytes) -> bytes:
    lines = [b"---", b"active: true"]
    if session_line is not None:
        lines.append(session_line)
    lines.append(b"---")
    return eol.join(lines) + eol


def _env(home: Path, current: str | None) -> dict[str, str]:
    env = os.environ.copy()
    env["HOME"] = str(home)
    env["CLAUDE_PLUGIN_ROOT"] = str(ROOT)
    for leaked in _LEAKED_ENV:
        env.pop(leaked, None)
    if current is not None:
        env["CLAUDE_CODE_SESSION_ID"] = current
    return env


class SafeResumeSessionIdTrimTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="gdd-safe-resume-trim-")
        self.addCleanup(self._tmp.cleanup)
        tmp = Path(os.path.realpath(self._tmp.name))
        self.home = tmp / "home"
        self.home.mkdir()
        self.repo = tmp / "repo"
        self.repo.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=self.repo, check=True)
        steering = self.repo / ".steering" / STEERING_NAME
        steering.mkdir(parents=True)
        steering.joinpath("state.md").write_text(STATE_MD, encoding="utf-8")
        (self.repo / ".claude").mkdir()
        self.local = self.repo / ".claude" / "gdd-dev.local.md"

    def _hook(self, current: str) -> str:
        """実プロセスで SessionStart hook を走らせ、additionalContext を返す（入口からの到達経路）。"""
        result = subprocess.run(
            ["bash", str(HOOK)], input="", capture_output=True, text=True,
            env=_env(self.home, current), cwd=str(self.repo), timeout=120,
        )
        # 例外で guard 全体が落ちない（rc 0 で JSON を 1 個だけ出す）
        self.assertEqual(result.returncode, 0, result.stderr)
        lines = [line for line in result.stdout.splitlines() if line.strip()]
        self.assertEqual(len(lines), 1, lines)
        return json.loads(lines[0])["hookSpecificOutput"]["additionalContext"]

    def _continuity_ok(self, current: str) -> bool:
        """同じ入力を読む既存の実装（block gate と共有）の結論。"""
        result = subprocess.run(
            ["bash", "-c", 'source "$1"; gdd_session_continuity_ok "$2"', "_",
             str(DETECT_STEERING), str(self.local)],
            capture_output=True, text=True, env=_env(self.home, current), timeout=60,
        )
        self.assertIn(result.returncode, (0, 1), result.stderr)
        return result.returncode == 0

    def test_safe_resume_and_continuity_ok_agree_on_the_same_input_table(self) -> None:
        for name, current, session_line, eol, expected in CASES:
            with self.subTest(name):
                self.local.write_bytes(_local_state(session_line, eol))

                additional = self._hook(current)

                if expected == "same":
                    self.assertIn("[gdd:reboot]", additional)
                    self.assertNotIn(PAUSED_MARK, additional)
                else:
                    self.assertIn("[gdd:paused]", additional)
                    self.assertIn(PAUSED_MARK, additional)
                self.assertEqual(self._continuity_ok(current), expected == "same")


if __name__ == "__main__":
    unittest.main()
