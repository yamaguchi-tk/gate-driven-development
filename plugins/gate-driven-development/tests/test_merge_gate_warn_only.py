"""merge gate は merge を止めず、実行後の通知と would-block の記録だけを残す。

不足として通知する全 reason code（`_merge_gate_block_reason_samples()` が実 hook で踏む）で、
出力に `decision` が無く、通知が条件法の前置きで始まり、state dir のログに
`would-block:<code>` が 1 行残ることを確かめる。
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from _merge_gate_support import (
    _init_repo,
    _new_full_evidence_repo,
    _new_marker_only_repo,
    _run_hook,
    _write_local_state,
)
from test_merge_gate_hook_block_reason_quality import _merge_gate_block_reason_samples

NOTICE_PREFIX = "実行後の通知: merge gate は止めずに通した。"
SUCCESS_CLAUSE = "merge が成功した場合は、次の不足をユーザーに報告するだけにし、承認や証跡を後から書き足さないでください。"
FAILURE_CLAUSE = "merge が失敗した場合だけ、次の手順で直してから再実行してください。"


class MergeGateWarnOnlyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.samples = _merge_gate_block_reason_samples()

    def test_every_reason_code_allows_the_merge_with_a_notice(self) -> None:
        self.assertTrue(self.samples)
        for sample in self.samples:
            with self.subTest(code=sample.code):
                payload = json.loads(sample.reason)
                self.assertNotIn("decision", payload)
                self.assertNotIn("permissionDecision", json.dumps(payload))
                notice = payload["hookSpecificOutput"]["additionalContext"]
                self.assertEqual(payload["hookSpecificOutput"]["hookEventName"], "PreToolUse")
                self.assertEqual(payload["systemMessage"], notice)
                self.assertTrue(notice.startswith(NOTICE_PREFIX + SUCCESS_CLAUSE + FAILURE_CLAUSE), notice)
                self.assertIn(f"reason code: {sample.code}", notice)

    def test_would_block_is_logged_with_the_reason_code(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            parent = Path(tmp)
            root = _new_full_evidence_repo(parent, "root")
            other = _new_marker_only_repo(parent, "other")
            state_dir = parent / "state"
            result = _run_hook(
                {"tool_input": {"command": f"cd {other} && gh pr merge 7"}},
                root,
                parent / "home",
                extra_env={"GDD_HOOK_STATE_DIR": str(state_dir)},
            )
            self.assertIn("pr-target-unresolvable", result.stdout)
            log = (state_dir / "merge-gate-suppressed.log").read_text()
            self.assertIn("event: would-block:pr-target-unresolvable", log)
            self.assertNotIn(str(root), log)
            self.assertNotIn(str(other), log)

    def test_aggregated_block_logs_every_code_in_one_line(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            parent = Path(tmp)
            home = parent / "home"
            (home / ".claude").mkdir(parents=True)
            repo = _init_repo(parent)
            _write_local_state(repo, extra_lines=[])
            state_dir = parent / "state"
            result = _run_hook(
                {"tool_input": {"command": "gh pr merge 7"}}, repo, home,
                extra_env={"GDD_HOOK_STATE_DIR": str(state_dir)},
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            notice = json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"]
            codes = notice.split("不足条件: ", 1)[1].split("。", 1)[0].split(", ")
            self.assertIn("approval-missing", codes)
            self.assertGreater(len(codes), 1)
            lines = (state_dir / "merge-gate-suppressed.log").read_text().splitlines()
            self.assertEqual(len(lines), 1, lines)
            self.assertIn(f"event: would-block:{','.join(codes)} |", lines[0])
            top = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"], cwd=repo, capture_output=True, text=True, check=True,
            ).stdout.strip()
            self.assertTrue(lines[0].endswith(f"repo: {hashlib.sha1(top.encode()).hexdigest()[:8]}"), lines[0])

    def test_unwritable_state_dir_still_emits_the_notice(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            parent = Path(tmp)
            root = _new_full_evidence_repo(parent, "root")
            other = _new_marker_only_repo(parent, "other")
            blocker = parent / "not-a-dir"
            blocker.write_text("")
            result = _run_hook(
                {"tool_input": {"command": f"cd {other} && gh pr merge 7"}},
                root,
                parent / "home",
                extra_env={"GDD_HOOK_STATE_DIR": str(blocker / "state")},
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertIn("pr-target-unresolvable", payload["hookSpecificOutput"]["additionalContext"])


if __name__ == "__main__":
    unittest.main()
