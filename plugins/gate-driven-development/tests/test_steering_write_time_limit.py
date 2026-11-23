"""steering write guard は、入力の処理がどれだけ遅くても hook の上限（hooks.json の timeout）より前に終わる。

guard の中の処理（NFKC の正規化・正規表現など）が遅いと、harness が hook を kill し、guard 全体が
走らずに書き込みが通る。Python 3.12 以前の NFKC は、結合文字の長い連なりで長さの二乗の時間がかかる
（3.9・3.12 で 17 秒台）。遅い形を 1 つずつ直すのではなく、guard の入口で既定の動作の SIGALRM を
掛け、上限で止まる（wrapper が 0・2 以外の終了コードを deny に倒す）ことを固定する。
"""
from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time
import unittest
from pathlib import Path

PLUGIN = Path(__file__).resolve().parents[1]
SCRIPT = PLUGIN / "hooks" / "scripts" / "validate-steering-write.py"
WRAPPER = PLUGIN / "hooks" / "scripts" / "run-steering-write-hook.sh"
HOOKS_JSON = PLUGIN / "hooks" / "hooks.json"
# bash・Python の起動と import は時限の外なので、hook の上限との間にこれだけの余裕を求める。
STARTUP_MARGIN_SECONDS = 10

# guard の最初の処理（stdin の JSON の読み取り）を、C の中で終わらない処理に差し替えて入口から走らせる。
# Python の handler は C の処理の途中では動かないので、ここで止まるなら既定の動作の SIGALRM である。
_SLOW_DRIVER = """
import json, re, runpy, sys
json.load = lambda *a, **k: re.match(r"(a+)+$", "a" * 60 + "b")
runpy.run_path(sys.argv[1], run_name="__main__")
"""


def module_limit() -> float:
    text = SCRIPT.read_text(encoding="utf-8")
    return float(text.split("GUARD_TIME_LIMIT_SECONDS = ", 1)[1].split("\n", 1)[0])


@unittest.skipUnless(hasattr(signal, "setitimer"), "signal.setitimer が無い環境では時限を張れない")
class SteeringWriteTimeLimitTest(unittest.TestCase):
    def test_the_hook_timeout_leaves_room_for_startup_before_the_time_limit(self) -> None:
        timeouts = [h["timeout"] for entries in json.loads(HOOKS_JSON.read_text(encoding="utf-8"))["hooks"].values()
                    for entry in entries for h in entry["hooks"] if "run-steering-write-hook.sh" in h["command"]]
        self.assertEqual(len(timeouts), 1)
        self.assertGreaterEqual(timeouts[0], module_limit() + STARTUP_MARGIN_SECONDS)

    def test_a_slow_guard_stops_before_the_hook_timeout(self) -> None:
        started = time.monotonic()
        try:
            proc = subprocess.run([sys.executable, "-c", _SLOW_DRIVER, str(SCRIPT)], input="{}",
                                  capture_output=True, text=True, timeout=module_limit() + 7)
        except subprocess.TimeoutExpired:
            self.fail("guard が hook の上限を過ぎても終わらない（harness の kill で書き込みが通る）")
        self.assertLess(time.monotonic() - started, module_limit() + 1)
        self.assertEqual(proc.returncode, -signal.SIGALRM)

    def test_the_wrapper_turns_the_time_limit_exit_into_a_deny(self) -> None:
        # 時限で終わったときの終了コード（bash では 128+14）を、wrapper が deny（exit 2）に倒す。
        env = dict(os.environ, CLAUDE_PLUGIN_ROOT=str(PLUGIN))
        fake = Path(self.enterContext(__import__("tempfile").TemporaryDirectory()))
        (fake / "python3").write_text("#!/bin/sh\nkill -ALRM $$\n")
        (fake / "python3").chmod(0o755)
        env["PATH"] = f"{fake}:{env['PATH']}"
        proc = subprocess.run(["bash", str(WRAPPER)], input=json.dumps({}), capture_output=True,
                              text=True, env=env, timeout=30)
        self.assertEqual(proc.returncode, 2)
        self.assertIn('"permissionDecision":"deny"', proc.stderr)


if __name__ == "__main__":
    unittest.main()
