"""main からの gdd-formal-gate-runner の起動を background に強制する PreToolUse hook。

正本の規定は references/subagent-dispatch.md § Typed Agent Resolution（時間上限は § Reviewer Input and Time Budget）。
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from _git_fixture import init_repo
from _paths import PLUGIN_ROOT

LIB_DIR = PLUGIN_ROOT / "hooks" / "scripts" / "lib"
HOOK_SCRIPT = PLUGIN_ROOT / "hooks" / "scripts" / "run-background-dispatch-gate-hook.sh"
sys.path.insert(0, str(LIB_DIR.parent))
from lib import background_dispatch_gate as gate  # noqa: E402
from lib.wait_watchdog import LIMITS, limit_kind  # noqa: E402

RUNNER = "gate-driven-development:gdd-formal-gate-runner"


def _payload(subagent_type: str = RUNNER, *, background=None, agent_id: str | None = None) -> dict:
    tool_input: dict = {"subagent_type": subagent_type, "prompt": "x"}
    if background is not None:
        tool_input["run_in_background"] = background
    payload: dict = {"tool_name": "Agent", "tool_input": tool_input}
    if agent_id is not None:
        payload["agent_id"] = agent_id
        payload["agent_type"] = "gate-driven-development:gdd-formal-gate-runner"
    return payload


class DenyReasonTests(unittest.TestCase):
    def test_runner_without_background_is_denied(self):
        """run_in_background が true（bool か文字列の "true"）でなければ deny し、timer の形を示す。"""
        for background in (None, False, "false", "True", 1, "yes"):
            for subagent_type in (RUNNER, "gdd-formal-gate-runner"):
                with self.subTest(background=background, subagent_type=subagent_type):
                    reason = gate.deny_reason(_payload(subagent_type, background=background))
                    self.assertIsNotNone(reason)
                    self.assertIn("run_in_background: true", reason)
                    self.assertIn(f"`sleep {LIMITS['gdd-formal-gate-runner'] + 60}`", reason)

    def test_runner_in_background_is_allowed(self):
        self.assertIsNone(gate.deny_reason(_payload(background=True)))

    def test_runner_with_string_true_is_allowed(self):
        """Agent の定義に run_in_background が無いセッションでは、値が文字列の "true" のまま届いた（2026-11-13 の観測）。"""
        self.assertIsNone(gate.deny_reason(_payload(background="true")))

    def test_near_miss_strings_and_containers_are_denied_without_error(self):
        """文字列の "true" に近い値や、比較で例外になりうる値（list・dict）も deny し、例外で通さない。"""
        for background in (" true", "true ", "TRUE", "tru", "", ["true"], {"v": True}, 1.0, 0):
            with self.subTest(background=background):
                reason = gate.deny_reason(_payload(background=background))
                self.assertIsNotNone(reason)

    def test_call_inside_subagent_is_allowed(self):
        """subagent の中（payload に agent_id がある）は通知を受けられないので強制しない。"""
        self.assertIsNone(gate.deny_reason(_payload(agent_id="a1b2c3")))

    def test_other_subagent_types_are_allowed(self):
        for subagent_type in (
            "gate-driven-development:gdd-implementation-reviewer",
            "gate-driven-development:gdd-planning-reviewer",
            "gate-driven-development:gdd-light-task-runner",
            "general-purpose",
            "",
        ):
            with self.subTest(subagent_type=subagent_type):
                self.assertIsNone(gate.deny_reason(_payload(subagent_type)))

    def test_unreadable_shapes_are_allowed(self):
        """型を読めない payload は、判定できないものとして通す（宣言した挙動）。"""
        for payload in ({}, {"tool_input": "x"}, {"tool_input": {"subagent_type": 3}}, [], "x"):
            with self.subTest(payload=payload):
                self.assertIsNone(gate.deny_reason(payload))

    def test_template_timer_matches_limit(self):
        """規定の timer の秒数は hook が案内する秒数と同じで、gate-runner の Template 4 つは
        どれも background で起動する。"""
        doc = (PLUGIN_ROOT / "references" / "subagent-dispatch.md").read_text(encoding="utf-8")
        self.assertIn(f"`sleep {LIMITS[gate.TARGET] + 60}`", doc)
        blocks = [m.group(1) for m in re.finditer(r"^```\n(Agent\(\n.*?)^```$", doc, flags=re.S | re.M)]
        runner = [b for b in blocks if gate.TARGET in b]
        self.assertEqual(len(runner), 4)
        for block in runner:
            self.assertRegex(block, r"(?m)^\s*run_in_background=True,")

    def test_kind_is_normalized_like_the_watchdog(self):
        """deny と watchdog は同じ正規化で type を読む（空白付きの名前で食い違わない）。"""
        self.assertEqual(limit_kind(" gate-driven-development:gdd-formal-gate-runner "), gate.TARGET)
        self.assertIsNotNone(gate.deny_reason(_payload(" gdd-formal-gate-runner")))

    def test_runner_is_a_watchdog_target(self):
        """deny の対象は watchdog が期限を測る type に入っている（timer の秒数をそこから取る）。"""
        self.assertIn(gate.TARGET, LIMITS)


class HookEntryTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        init_repo(self.root)

    def tearDown(self):
        self._tmp.cleanup()

    def _activate(self, *, active: bool = True, session_id: str = "test-session") -> None:
        (self.root / ".claude").mkdir(exist_ok=True)
        (self.root / ".claude" / "gdd-dev.local.md").write_text(
            f"---\nactive: {str(active).lower()}\nsession_id: {session_id}\n---\n", encoding="utf-8"
        )

    def _run(self, stdin: str) -> subprocess.CompletedProcess[str]:
        env = {
            "CLAUDE_PLUGIN_ROOT": str(PLUGIN_ROOT),
            "CLAUDE_CODE_SESSION_ID": "test-session",
            "PATH": "/usr/bin:/bin:/usr/local/bin",
            "HOME": str(self.root),
        }
        return subprocess.run(
            ["bash", str(HOOK_SCRIPT)], cwd=self.root, input=stdin,
            capture_output=True, text=True, env=env, check=False,
        )

    def test_sync_runner_from_main_is_denied(self):
        self._activate()
        proc = self._run(json.dumps(_payload()))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        out = json.loads(proc.stdout)["hookSpecificOutput"]
        self.assertEqual(out["hookEventName"], "PreToolUse")
        self.assertEqual(out["permissionDecision"], "deny")
        self.assertIn("run_in_background: true", out["permissionDecisionReason"])

    def test_repo_lib_package_and_json_module_do_not_replace_the_gate(self):
        # hook の cwd（repo）に lib パッケージや json.py があっても、plugin の判定を読む
        self._activate()
        (self.root / "lib").mkdir()
        (self.root / "lib" / "__init__.py").write_text("", encoding="utf-8")
        (self.root / "json.py").write_text("raise ImportError('repo json')\n", encoding="utf-8")
        proc = self._run(json.dumps(_payload()))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(json.loads(proc.stdout)["hookSpecificOutput"]["permissionDecision"], "deny", proc.stderr)

    def test_allowed_cases_print_nothing(self):
        cases = {
            "background": (True, "test-session", _payload(background=True)),
            "background as string": (True, "test-session", _payload(background="true")),
            "subagent": (True, "test-session", _payload(agent_id="a1")),
            "inactive": (False, "test-session", _payload()),
            "other session": (True, "other-session", _payload()),
        }
        for name, (active, session_id, payload) in cases.items():
            with self.subTest(case=name):
                self._activate(active=active, session_id=session_id)
                proc = self._run(json.dumps(payload))
                self.assertEqual(proc.returncode, 0, proc.stderr)
                self.assertEqual(proc.stdout.strip(), "")

    def test_near_miss_string_is_denied_from_the_hook_entry(self):
        """入口から通しても、"true" と完全一致しない文字列は deny のまま。"""
        self._activate()
        proc = self._run(json.dumps(_payload(background="True")))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(json.loads(proc.stdout)["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_kill_switch_disables_the_deny(self):
        self._activate()
        (self.root / ".claude" / "gdd-hooks-disabled").write_text("", encoding="utf-8")
        proc = self._run(json.dumps(_payload()))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stdout.strip(), "")

    def test_no_state_file_prints_nothing(self):
        proc = self._run(json.dumps(_payload()))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stdout.strip(), "")

    def test_malformed_payload_is_allowed_and_logged(self):
        """読めない payload は通し（Agent の起動を全部止めない）、hook-errors に記録する。"""
        self._activate()
        proc = self._run("{not json")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stdout.strip(), "")
        log = self.root / ".gdd" / "hook-errors.log"
        self.assertTrue(log.is_file())
        self.assertIn("background_dispatch_gate", log.read_text(encoding="utf-8"))

    def test_registered_under_agent_matcher(self):
        hooks = json.loads((PLUGIN_ROOT / "hooks" / "hooks.json").read_text(encoding="utf-8"))["hooks"]
        commands = [
            h["command"]
            for entry in hooks["PreToolUse"] if entry["matcher"] == "Agent"
            for h in entry["hooks"]
        ]
        self.assertTrue(any(HOOK_SCRIPT.name in c for c in commands), commands)


if __name__ == "__main__":
    unittest.main()
