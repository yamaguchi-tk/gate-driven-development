"""SessionStart の additionalContext に制御文字が混ざっても JSON を壊さない契約テスト。

active steering（`[gdd:reboot]`）・複数 steering（`[gdd:warning]`）の 2 分岐は、
steering の dir 名や worktree のパスをそのまま文字列に連結し、出力時に `"` と `\\` しか
エスケープしていなかった。TAB や ESC を含むディレクトリ名があると SessionStart の出力が
JSON として読めず、additionalContext 全体が落ちる（PR #105 レビュー指摘）。
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
NON_TERMINAL = "Resume From: human-check-waiting\nHuman Check Status: pending\nRoute In Progress: none\n"
CONTROL_NAME = "20260917-tab\there-esc\x1bhere"
CLEAN_NAME = "20260917-tabhere-eschere"


def _git(cwd: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)


def _state(steering_dir: Path) -> Path:
    steering_dir.mkdir(parents=True, exist_ok=True)
    (steering_dir / "state.md").write_text(NON_TERMINAL, encoding="utf-8")
    return steering_dir


class SessionStartContextControlCharTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="gdd-ctx-cntrl-")
        self.addCleanup(self._tmp.cleanup)
        tmp = Path(os.path.realpath(self._tmp.name))
        self.home = tmp / "home"
        self.home.mkdir()
        self.repo = tmp / "repo"
        self.repo.mkdir()
        # commit を作らない: default branch に HEAD があると `[gdd:paused]` 分岐に入り、task 名を出さない
        _git(self.repo, "init", "-q")

    def _additional(self, locale: str | None = None, failing_python: bool = False) -> str:
        env = os.environ.copy()
        if locale:
            env["LC_ALL"] = locale
        if failing_python:
            fake_bin = self.home.parent / "fake-bin"
            fake_bin.mkdir()
            fake = fake_bin / "python3"
            fake.write_text("#!/bin/sh\necho 'python3: broken shim' >&2\nexit 127\n", encoding="utf-8")
            fake.chmod(0o755)
            env["PATH"] = f"{fake_bin}{os.pathsep}{env['PATH']}"
        env["HOME"] = str(self.home)
        env["CLAUDE_PLUGIN_ROOT"] = str(ROOT)
        for leaked in ("GDD_STEERING_DIR", "GDD_HOOK_STATE_DIR",
                       "GDD_MAX_AUTO_CYCLES", "CLAUDE_CODE_SESSION_ID", "GDD_WORKTREES_ROOT"):
            env.pop(leaked, None)
        result = subprocess.run(
            ["bash", str(HOOK)], input=b"", capture_output=True,
            env=env, cwd=str(self.repo), timeout=120,
        )
        stderr = result.stderr.decode("utf-8", "replace")
        self.assertEqual(result.returncode, 0, stderr)
        # 置換なしで decode する: 不正な UTF-8 を U+FFFD に置き換えると、JSON として読めない出力を隠す
        stdout = result.stdout.decode("utf-8")
        lines = [line for line in stdout.splitlines() if line.strip()]
        self.assertEqual(len(lines), 1, lines)
        additional = json.loads(lines[0])["hookSpecificOutput"]["additionalContext"]
        self.assertNotRegex(additional, r"[\x00-\x1f\x7f]")
        return additional

    def test_reboot_context_with_control_chars_in_task_name_is_valid_json(self) -> None:
        _state(self.repo / ".steering" / CONTROL_NAME)

        additional = self._additional()

        self.assertIn("[gdd:reboot]", additional)
        self.assertIn(CLEAN_NAME, additional)

    def test_multiple_steering_warning_with_control_chars_is_valid_json(self) -> None:
        _state(self.repo / ".steering" / CONTROL_NAME)
        _state(self.repo / ".steering" / "20260917-plain")

        additional = self._additional()

        self.assertIn("[gdd:warning]", additional)
        self.assertIn(CLEAN_NAME, additional)

    def test_invalid_utf8_in_state_value_does_not_abort_hook_under_utf8_locale(self) -> None:
        # 制御文字の除去自体が落ちないこと: UTF-8 ロケールの BSD tr は不正なバイト列で
        # `Illegal byte sequence` を返し、`set -euo pipefail` の下で hook 全体が出力無しで止まる
        steering = _state(self.repo / ".steering" / "20260917-invalid-utf8")
        (steering / "requirements.md").write_bytes("### 一言\nゴール".encode("utf-8") + b"\xff\t" + "です\n".encode("utf-8"))

        additional = self._additional(locale="en_US.UTF-8")

        self.assertIn("[gdd:reboot]", additional)
        self.assertIn("20260917-invalid-utf8", additional)
        self.assertIn("ゴール", additional)

    def test_invalid_utf8_goal_stays_valid_json_when_python_is_unavailable(self) -> None:
        # python3 が使えないと gdd_truncate_chars は値を素通しし、CONTEXT の sanitize は不正な UTF-8 を落とせない。
        # 不正なバイトは Goal の抽出の時点で落とす（_additional が置換なしの UTF-8 と JSON で読めることを確かめる）
        steering = _state(self.repo / ".steering" / "20260917-invalid-utf8-nopy")
        (steering / "requirements.md").write_bytes("### 一言\nゴール".encode("utf-8") + b"\xff" + "です\n".encode("utf-8"))

        additional = self._additional(locale="en_US.UTF-8", failing_python=True)

        self.assertIn("ゴール", additional)

    def test_failing_python_does_not_blank_the_reboot_context(self) -> None:
        # 不正な UTF-8 の除去に使う python3 が失敗しても（壊れた pyenv shim 等）、案内を空にしない
        _state(self.repo / ".steering" / CONTROL_NAME)

        reboot = self._additional(failing_python=True)

        self.assertIn("[gdd:reboot]", reboot)
        self.assertIn(CLEAN_NAME, reboot)

    def test_failing_python_does_not_blank_the_multiple_steering_warning(self) -> None:
        _state(self.repo / ".steering" / CONTROL_NAME)
        _state(self.repo / ".steering" / "20260917-plain")

        multiple = self._additional(failing_python=True)

        self.assertIn("[gdd:warning]", multiple)
        self.assertIn(CLEAN_NAME, multiple)


if __name__ == "__main__":
    unittest.main()
