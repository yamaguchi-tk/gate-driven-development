"""Ctx-1: plan-reread フックの注入 dedup 契約。

plan-reread フックは Write/Edit 前に Current Task + AC を再注入する。compaction 後の
再注入が目的なので完全な抑制はしない。同一内容かつ前回注入から WINDOW 秒以内のときだけ
skip し、内容が変わるか WINDOW を超えたら再注入する（時間窓つき dedup）。
"""
from __future__ import annotations

import json
import os
import subprocess
import tempfile
import time
import unittest
from pathlib import Path

from _paths import PLUGIN_ROOT
HOOK = PLUGIN_ROOT / "hooks" / "scripts" / "run-pre-tool-use-plan-reread-hook.sh"

_STATE = (
    "Started At: 2026-06-21T00:00:00+09:00\n"
    "Resume From: gdd-subagent-driven-implementation\n"
    "Requirements Review Status=approved | evidence: req\n"
    "Design Review Status=approved | evidence: design\n"
    "Human Check Status=approved | evidence: human\n"
    "Route In Progress=none\n"
)
_REQUIREMENTS = "### 一言\nCtx-1 dedup fixture\n\n## 受入条件\n- AC-1: x\n"


def _tasklist(task_name: str) -> str:
    return (
        "## Current Task\n"
        f"### Task: {task_name}\n"
        "- AC-1: implement it\n\n"
        "## Pending Tasks\n- なし\n\n"
        "## Review Status\nNext Action=gdd-subagent-driven-implementation\n"
    )


def _setup(repo: Path, task_name: str = "T-1 | implement") -> None:
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    # 毎ターンの注入は GDD の印（active な marker）があるときだけ
    (repo / ".claude").mkdir(exist_ok=True)
    (repo / ".claude" / "gdd-dev.local.md").write_text("---\nactive: true\n---\n", encoding="utf-8")
    steering = repo / ".steering" / "20260621-ctx1"
    steering.mkdir(parents=True, exist_ok=True)
    steering.joinpath("state.md").write_text(_STATE, encoding="utf-8")
    steering.joinpath("requirements.md").write_text(_REQUIREMENTS, encoding="utf-8")
    steering.joinpath("tasklist.md").write_text(_tasklist(task_name), encoding="utf-8")


def _run(repo: Path, window: str | None = None) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    # Determinism: drop host env that would change steering detection or the window.
    # No CLAUDE_CODE_SESSION_ID → session continuity is fail-open.
    for var in ("CLAUDE_CODE_SESSION_ID", "GDD_PLUGIN_ROOT", "CLAUDE_PLUGIN_ROOT", "GDD_PLAN_REREAD_DEDUP_WINDOW"):
        env.pop(var, None)
    if window is not None:
        env["GDD_PLAN_REREAD_DEDUP_WINDOW"] = window
    return subprocess.run(
        ["bash", str(HOOK)],
        cwd=repo,
        input=json.dumps({"tool_name": "Edit", "tool_input": {}}),
        capture_output=True,
        text=True,
        env=env,
    )


class PlanRereadDedupContractTests(unittest.TestCase):
    def test_first_injection_emits_context(self) -> None:
        with tempfile.TemporaryDirectory(prefix="gdd-ctx1-") as tmp:
            repo = Path(tmp)
            _setup(repo)
            result = _run(repo)
            self.assertEqual(result.returncode, 0)
            self.assertIn("additionalContext", result.stdout)
            self.assertIn("Task: T-1", result.stdout)

    def test_identical_reinjection_within_window_is_deduped(self) -> None:
        with tempfile.TemporaryDirectory(prefix="gdd-ctx1-") as tmp:
            repo = Path(tmp)
            _setup(repo)
            first = _run(repo)
            self.assertIn("additionalContext", first.stdout)
            second = _run(repo)
            # returncode==0 distinguishes intentional dedup from an internal crash
            # (a crash under set -euo pipefail would also produce empty stdout).
            self.assertEqual(second.returncode, 0, f"dedup must exit 0, got {second.returncode}")
            self.assertEqual(
                second.stdout.strip(), "",
                f"identical re-injection within window must be deduped: {second.stdout!r}",
            )

    def test_non_integer_window_is_sanitized_without_arithmetic_error(self) -> None:
        """A malformed GDD_PLAN_REREAD_DEDUP_WINDOW (e.g. '90s') must not raise a bash
        arithmetic error under set -euo pipefail. It is normalized to the default
        window and the hook behaves deterministically (exit 0, no stderr error)."""
        with tempfile.TemporaryDirectory(prefix="gdd-ctx1-") as tmp:
            repo = Path(tmp)
            _setup(repo)
            _run(repo, window="90s")  # first run primes the cache
            second = _run(repo, window="90s")
            self.assertEqual(second.returncode, 0, f"must not crash, got {second.returncode}: {second.stderr!r}")
            # No arithmetic error leaking to stderr — the window must be sanitized,
            # not left to fall through via a bash arithmetic syntax error.
            self.assertNotIn("value too great", second.stderr)
            self.assertNotIn("((:", second.stderr)

    def test_leading_zero_window_no_octal_arithmetic_error(self) -> None:
        """A leading-zero window like '09' must not be parsed as octal in the
        comparison; the hook forces base-10 and raises no arithmetic error."""
        with tempfile.TemporaryDirectory(prefix="gdd-ctx1-") as tmp:
            repo = Path(tmp)
            _setup(repo)
            _run(repo, window="09")  # primes cache
            second = _run(repo, window="09")
            self.assertEqual(second.returncode, 0, f"must not crash: {second.stderr!r}")
            self.assertNotIn("value too great", second.stderr)
            self.assertNotIn("((:", second.stderr)

    def test_leading_zero_zero_window_is_always_reinject(self) -> None:
        """`GDD_PLAN_REREAD_DEDUP_WINDOW='00'` is numerically 0, so it must act as the
        always-reinject safety valve. The cache epoch is forced to the future so a
        >0 window would dedup; '00' must still inject (proves base-10 normalization
        of the 0 check, not a string compare)."""
        with tempfile.TemporaryDirectory(prefix="gdd-ctx1-") as tmp:
            repo = Path(tmp)
            _setup(repo)
            _run(repo, window="00")  # prime cache
            cache = repo / ".claude" / ".gdd-plan-reread-cache"
            hash_line = cache.read_text(encoding="utf-8").splitlines()[1]
            cache.write_text(f"{int(time.time()) + 100000}\n{hash_line}\n", encoding="utf-8")
            second = _run(repo, window="00")
            self.assertIn(
                "additionalContext", second.stdout,
                "window '00' must normalize to 0 (always reinject), not string-compare",
            )

    def test_window_zero_always_reinjects(self) -> None:
        with tempfile.TemporaryDirectory(prefix="gdd-ctx1-") as tmp:
            repo = Path(tmp)
            _setup(repo)
            _run(repo, window="0")
            second = _run(repo, window="0")
            self.assertIn(
                "additionalContext", second.stdout,
                "window=0 must re-inject every time (anti-compaction safety valve)",
            )

    def test_changed_context_reinjects_within_window(self) -> None:
        with tempfile.TemporaryDirectory(prefix="gdd-ctx1-") as tmp:
            repo = Path(tmp)
            _setup(repo)
            _run(repo)
            # Current Task changes → must re-inject even within the window.
            (repo / ".steering" / "20260621-ctx1" / "tasklist.md").write_text(
                _tasklist("T-2 | next task"), encoding="utf-8"
            )
            second = _run(repo)
            self.assertIn("additionalContext", second.stdout)
            self.assertIn("Task: T-2", second.stdout)


if __name__ == "__main__":
    unittest.main()
