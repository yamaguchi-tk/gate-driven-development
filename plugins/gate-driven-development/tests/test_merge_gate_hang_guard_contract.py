"""merge gate hook を実起動するテストの壁時計の打ち切りを、1 か所の値から導く契約テスト。

hook 1 回の CPU 時間は、hooks.json の timeout（10 秒）に十分収まる。壁時計はほぼ
プロセス起動の待ちで、並列の全量テストと外部の負荷の下では timeout に届く（2026-10-26 に、
load average が高い中で timeout の近くまで延びたのを測った）。打ち切りを hooks.json の timeout と同じ
10 秒にすると、判定が正しいテストが `subprocess.TimeoutExpired` で落ちる。打ち切りは
止まったときの保険（`HANG_GUARD`）にし、値は `_merge_gate_support` の 1 か所から導く。
"""
from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import _merge_gate_support
import test_merge_gate_followup_findings
import test_merge_gate_ledger_fail_closed
from _timing_budget import hook_timeout_seconds


def _captured_timeouts(call) -> list:
    """`subprocess.run` を差し替えて `call()` を走らせ、渡った `timeout` を集める。"""
    seen = []

    def fake_run(*args, **kwargs):
        seen.append(kwargs.get("timeout"))
        return subprocess.CompletedProcess(args, 0, stdout="", stderr="")

    with mock.patch("subprocess.run", side_effect=fake_run):
        call()
    return seen


class HangGuardDerivationTests(unittest.TestCase):
    def test_hang_guard_is_six_times_the_hooks_json_timeout(self):
        hook_timeout = hook_timeout_seconds("run-merge-gate-hook.sh")
        self.assertEqual(_merge_gate_support.HOOK_TIMEOUT, hook_timeout)
        self.assertEqual(_merge_gate_support.HANG_GUARD, hook_timeout * 6)

    def test_ledger_tests_share_the_support_values(self):
        self.assertIs(test_merge_gate_ledger_fail_closed.HOOK_TIMEOUT, _merge_gate_support.HOOK_TIMEOUT)
        self.assertIs(test_merge_gate_ledger_fail_closed.HANG_GUARD, _merge_gate_support.HANG_GUARD)


class HookLaunchTimeoutTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def test_shared_run_hook_defaults_to_hang_guard(self):
        seen = _captured_timeouts(
            lambda: _merge_gate_support._run_hook({"tool_input": {"command": "ls"}}, self.tmp, self.tmp)
        )
        self.assertEqual(seen, [_merge_gate_support.HANG_GUARD])

    def test_shared_run_hook_keeps_an_explicit_timeout(self):
        seen = _captured_timeouts(
            lambda: _merge_gate_support._run_hook(
                {"tool_input": {"command": "ls"}}, self.tmp, self.tmp, timeout=3,
            )
        )
        self.assertEqual(seen, [3])

    def test_followup_findings_run_hook_uses_hang_guard(self):
        seen = _captured_timeouts(
            lambda: test_merge_gate_followup_findings._run_hook(
                {"tool_input": {"command": "ls"}}, self.tmp, self.tmp,
            )
        )
        self.assertEqual(seen, [_merge_gate_support.HANG_GUARD])


if __name__ == "__main__":
    unittest.main()
