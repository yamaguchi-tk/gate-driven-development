"""background の待ちのループを deny し、scripts/wait-until.py で待たせる PreToolUse(Bash) hook。

対象は run_in_background が bool の true の Bash で、ループの語（until・while・for）の後ろに sleep がある
もの、`--watch`、`gh run watch`。GDD active を問わず、subagent の中も対象にする。
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from _paths import PLUGIN_ROOT

LIB_DIR = PLUGIN_ROOT / "hooks" / "scripts" / "lib"
HOOK_SCRIPT = PLUGIN_ROOT / "hooks" / "scripts" / "run-wait-loop-gate-hook.sh"
WAIT_SCRIPT = PLUGIN_ROOT / "scripts" / "wait-until.py"
sys.path.insert(0, str(LIB_DIR.parent))
from lib import wait_loop_gate as gate  # noqa: E402
from lib.wait_watchdog import _TIMER_RE  # noqa: E402

WU = f"python3 {WAIT_SCRIPT}"

DENIED = [
    "until gh pr view 1 --json state -q .state | grep -q MERGED; do sleep 30; done",
    "while true; do gh run list --limit 1; sleep 20; done",
    "for i in $(seq 1 40); do s=$(gh run view 1 --json status -q .status); [ \"$s\" = completed ] && break; sleep 20; done",
    "cd /tmp && until [ -f done.txt ]; do sleep 5; done",
    "until gh pr checks 3; do python3 -c \"import time; time.sleep(30)\"; done",
    "cat > x.py <<'E'\nimport time\nwhile True:\n    time.sleep(10)\nE\npython3 x.py",
    "gh pr checks 274 --watch --interval 30",
    "timeout 1500 gh pr checks 12 --watch",
    "gh run watch 123456",
    "x=1\nwhile [ $x -lt 3 ]\ndo\n  sleep 1\n  x=$((x+1))\ndone",
]

ALLOWED = [
    "sleep 600",
    "sleep 90; echo done",
    "sleep 420; gh pr checks 3",
    f"{WU} --timeout 3600 --pr-checks 42",
    f"{WU} --timeout 3600 --pr-checks 42 -R o/r",
    f"{WU} --timeout 1800 -- bash -c 'sleep 2; gh run view 1 --json status -q .status | grep -q completed'",
    "python3 /opt/for-ci/wait-until.py --timeout 60 -- bash -c 'sleep 1; true'",
    "python3 -m pytest tests/ -q",
    "for f in a b c; do echo $f; done",
    "sleep 60; for f in a b; do echo $f; done",
    "sleep 60; echo \"waiting for CI\"",
    "npm run build",
]


def _payload(command: object, *, background: object = True, agent_id: str | None = None) -> dict:
    tool_input: dict = {"command": command, "description": "x"}
    if background is not None:
        tool_input["run_in_background"] = background
    payload: dict = {"tool_name": "Bash", "tool_input": tool_input}
    if agent_id is not None:
        payload["agent_id"] = agent_id
    return payload


class DenyReasonTests(unittest.TestCase):
    def test_wait_loops_in_background_are_denied(self):
        for command in DENIED:
            for agent_id in (None, "a1b2c3"):
                with self.subTest(command=command, agent_id=agent_id):
                    self.assertIsNotNone(gate.deny_reason(_payload(command, agent_id=agent_id)))

    def test_non_loops_and_the_wait_script_are_allowed(self):
        for command in ALLOWED:
            with self.subTest(command=command):
                self.assertIsNone(gate.deny_reason(_payload(command)))

    def test_deadline_timer_accepted_by_the_watchdog_is_allowed(self):
        # wait_watchdog が期限 timer と認める形は、同じ入力で必ず通す
        for command in ("sleep 1", "sleep 3660", " sleep 600 ", "sleep\t999999"):
            with self.subTest(command=command):
                self.assertIsNotNone(_TIMER_RE.fullmatch(command))
                self.assertIsNone(gate.deny_reason(_payload(command)))

    def test_only_bool_true_background_is_judged(self):
        for background in (None, False, "true", 1, "yes"):
            with self.subTest(background=background):
                self.assertIsNone(gate.deny_reason(_payload(DENIED[0], background=background)))

    def test_unreadable_shapes_are_allowed(self):
        for payload in (None, [], "x", {"tool_input": "x"}, {"tool_input": None},
                        _payload(None), _payload(["until", "sleep"]), _payload(1)):
            with self.subTest(payload=payload):
                self.assertIsNone(gate.deny_reason(payload))

    def test_unsafe_wait_script_path_is_not_echoed(self):
        # 理由文に載せる待機スクリプトのパスに制御文字・surrogate があれば、Stop hook と同じ placeholder にする
        from unittest import mock
        for bad in ("/p/a\x1b[2Kb/wait-until.py", "/p/\udc80/wait-until.py", "/p/a\u2028b/wait-until.py"):
            with self.subTest(bad=bad), mock.patch.object(gate, "WAIT_SCRIPT", Path(bad)):
                for agent_id in (None, "a1"):
                    reason = gate.deny_reason(_payload(DENIED[0], agent_id=agent_id))
                    self.assertIn("python3 …/scripts/wait-until.py --timeout", reason)
                    self.assertNotIn(bad, reason)
                    reason.encode("utf-8")

    def test_reason_points_to_the_existing_wait_script(self):
        reason = gate.deny_reason(_payload(DENIED[0]))
        self.assertIn(str(WAIT_SCRIPT), reason)
        self.assertTrue(WAIT_SCRIPT.is_file())
        for form in ("--pr-checks", "-- bash -c", "sleep N"):
            with self.subTest(form=form):
                self.assertIn(form, reason)

    def test_reason_invocations_are_accepted_by_the_script_and_the_gate(self):
        # 理由文が示す呼び出しは、wait-until.py が受け付け、この gate も通す
        import importlib.util
        import re
        spec = importlib.util.spec_from_file_location("wait_until_for_gate_test", WAIT_SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        for extra in ({}, {"agent_id": "a1b2c3"}):
            reason = gate.deny_reason(_payload(DENIED[0], **extra))
            calls = [c for c in re.findall(r"`([^`]*)`", reason) if "wait-until.py" in c]
            self.assertEqual(len(calls), 2, reason)
            for call in calls:
                filled = re.sub(r"<秒[^>]*>", "60", call.replace("<PR 番号>", "42")
                                .replace("[-R <owner/name>]", "-R o/r").replace("<条件>", "true"))
                with self.subTest(call=filled):
                    self.assertFalse(gate.is_wait_loop(filled))
                    argv = __import__("shlex").split(filled)[2:]
                    module._parse(argv)  # 受け付けなければ SystemExit で落ちる

    def test_subagent_reason_points_to_foreground_then_monitor(self):
        main_reason = gate.deny_reason(_payload(DENIED[0]))
        sub_reason = gate.deny_reason(_payload(DENIED[0], agent_id="a1b2c3"))
        self.assertNotIn("Monitor", main_reason)
        self.assertIn("Monitor", sub_reason)
        # subagent が background の完了通知や Monitor のイベントを受け取れるかは確かめていないので、
        # background で起動して完了通知を待つ案内は出さず、foreground の待ち方を先に案内する
        self.assertIn("foreground", sub_reason)
        self.assertNotIn("run_in_background: true", sub_reason)
        self.assertNotIn("完了通知を待つ", sub_reason)
        self.assertLess(sub_reason.index("foreground"), sub_reason.index("Monitor"))
        # Bash の timeout は省くと 120 秒なので、--timeout はそれより短くする必要がある
        self.assertIn("120 秒", sub_reason)
        # foreground の Bash は 600 秒で打ち切られるので、600 秒を超える --timeout を例に出さない
        for value in re.findall(r"--timeout (\d+)", sub_reason):
            self.assertLess(int(value), 600, sub_reason)

    def test_long_heredoc_is_judged_quickly(self):
        import time
        command = ("until x; do echo; " * 20000) + "done"
        started = time.time()
        self.assertIsNone(gate.deny_reason(_payload(command)))
        self.assertLess(time.time() - started, 1)


def _run_hook(payload: object, *, cwd: Path, home: Path | None, state_dir: Path | None = None) -> subprocess.CompletedProcess:
    env = {k: v for k, v in os.environ.items() if k not in ("HOME", "GDD_HOOK_STATE_DIR")}
    if state_dir is not None:
        env["GDD_HOOK_STATE_DIR"] = str(state_dir)
    if home is not None:
        env["HOME"] = str(home)
    env["CLAUDE_PLUGIN_ROOT"] = str(PLUGIN_ROOT)
    stdin = payload if isinstance(payload, str) else json.dumps(payload)
    return subprocess.run(["bash", str(HOOK_SCRIPT)], input=stdin, capture_output=True, text=True,
                          cwd=cwd, env=env, timeout=30)


def _decision(proc: subprocess.CompletedProcess) -> str | None:
    if not proc.stdout.strip():
        return None
    return json.loads(proc.stdout)["hookSpecificOutput"]["permissionDecision"]


class HookEntryTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.ws = Path(self._tmp.name)
        self.home = self.ws / "home"
        self.home.mkdir()
        self.cwd = self.ws / "work"
        self.cwd.mkdir()

    def tearDown(self):
        self._tmp.cleanup()

    def test_loop_is_denied_outside_git_and_outside_active_gdd(self):
        (self.cwd / ".claude").mkdir()
        (self.cwd / ".claude" / "gdd-dev.local.md").write_text("---\nactive: false\n---\n", encoding="utf-8")
        for agent_id in (None, "a1b2c3"):
            with self.subTest(agent_id=agent_id):
                proc = _run_hook(_payload(DENIED[0], agent_id=agent_id), cwd=self.cwd, home=self.home)
                self.assertEqual(proc.returncode, 0, proc.stderr)
                self.assertEqual(_decision(proc), "deny")
                reason = json.loads(proc.stdout)["hookSpecificOutput"]["permissionDecisionReason"]
                self.assertIn(str(WAIT_SCRIPT), reason)

    def test_allowed_commands_pass_through_the_entry(self):
        for command in ("sleep 600", f"{WU} --timeout 60 --pr-checks 1"):
            with self.subTest(command=command):
                proc = _run_hook(_payload(command), cwd=self.cwd, home=self.home)
                self.assertEqual((proc.returncode, proc.stdout), (0, ""), proc.stderr)

    def test_repo_lib_package_and_json_module_do_not_replace_the_gate(self):
        # hook の cwd（repo）に lib パッケージや json.py があっても、plugin の判定を読む
        (self.cwd / "lib").mkdir()
        (self.cwd / "lib" / "__init__.py").write_text("", encoding="utf-8")
        (self.cwd / "json.py").write_text("raise ImportError('repo json')\n", encoding="utf-8")
        proc = _run_hook(_payload(DENIED[0]), cwd=self.cwd, home=self.home)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(_decision(proc), "deny", proc.stderr)

    def test_kill_switch_allows(self):
        (self.home / ".claude").mkdir()
        (self.home / ".claude" / "gdd-hooks-disabled").write_text("", encoding="utf-8")
        proc = _run_hook(_payload(DENIED[0]), cwd=self.cwd, home=self.home)
        self.assertEqual((proc.returncode, proc.stdout), (0, ""), proc.stderr)

    def test_unreadable_payload_is_allowed_and_logged_outside_the_repo(self):
        proc = _run_hook('{"tool_input": {"run_in_background": true, "command": "until', cwd=self.cwd, home=self.home)
        self.assertEqual((proc.returncode, proc.stdout), (0, ""), proc.stderr)
        log = self.home / ".claude" / ".gdd-hook-state" / "wait-loop-gate.log"
        self.assertEqual(len(log.read_text(encoding="utf-8").splitlines()), 1)
        self.assertEqual(log.stat().st_mode & 0o777, 0o600)
        self.assertFalse((self.cwd / ".gdd").exists())

    def test_state_dir_env_moves_the_log(self):
        state = self.ws / "state"
        proc = _run_hook("not json run_in_background", cwd=self.cwd, home=self.home, state_dir=state)
        self.assertEqual((proc.returncode, proc.stdout), (0, ""), proc.stderr)
        self.assertTrue((state / "wait-loop-gate.log").is_file())
        self.assertFalse((self.home / ".claude" / ".gdd-hook-state").exists())

    def test_missing_home_still_judges_and_never_exits_2(self):
        proc = _run_hook(_payload(DENIED[0]), cwd=self.cwd, home=None)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(_decision(proc), "deny")
        proc = _run_hook("not json run_in_background", cwd=self.cwd, home=None)
        self.assertEqual((proc.returncode, proc.stdout), (0, ""), proc.stderr)

    def test_hook_is_wired_to_bash_pre_tool_use(self):
        config = json.loads((PLUGIN_ROOT / "hooks" / "hooks.json").read_text(encoding="utf-8"))
        wired = [hook for entry in config["hooks"]["PreToolUse"] if entry.get("matcher") == "Bash"
                 for hook in entry["hooks"] if HOOK_SCRIPT.name in hook.get("command", "")]
        self.assertEqual(len(wired), 1)
        self.assertEqual(wired[0].get("timeout"), 10)


if __name__ == "__main__":
    unittest.main()
