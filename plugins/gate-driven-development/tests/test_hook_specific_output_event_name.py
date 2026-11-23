"""hookSpecificOutput は Claude Code 側で hookEventName を必須フィールドとして
検証する。run-session-start-hook.sh は対応済みだが、run-user-prompt-submit-hook.sh /
run-pre-tool-use-plan-reread-hook.sh / run-steering-write-hook.sh (validate-steering-write.py)
は欠落しており "Hook JSON output validation failed" を起こす。run-user-prompt-submit-hook.sh の
全5出力パス（manual merge continuation / review cue / multiple steering warning /
blocked state / 通常の active steering context）と run-pre-tool-use-plan-reread-hook.sh、
validate-steering-write.py の emit_deny、run-steering-write-hook.sh の Python 未検出
フォールバックで、それぞれ正しい hookEventName が含まれることを確認する。
"""
from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from _paths import PLUGIN_ROOT
USER_PROMPT_SUBMIT_HOOK = PLUGIN_ROOT / "hooks" / "scripts" / "run-user-prompt-submit-hook.sh"
PLAN_REREAD_HOOK = PLUGIN_ROOT / "hooks" / "scripts" / "run-pre-tool-use-plan-reread-hook.sh"
STEERING_WRITE_HOOK = PLUGIN_ROOT / "hooks" / "scripts" / "run-steering-write-hook.sh"

_STATE = (
    "Started At: 2026-06-21T00:00:00+09:00\n"
    "Resume From: gdd-subagent-driven-implementation\n"
    "Requirements Review Status=approved | evidence: req\n"
    "Design Review Status=approved | evidence: design\n"
    "Human Check Status=approved | evidence: human\n"
    "Route In Progress=none\n"
)
_REQUIREMENTS = "### 一言\nevent-name fixture\n\n## 受入条件\n- AC-1: x\n"
_TASKLIST = (
    "## Current Task\n"
    "### Task: T-1 | implement\n"
    "- AC-1: implement it\n\n"
    "## Pending Tasks\n- なし\n\n"
    "## Review Status\nNext Action=gdd-subagent-driven-implementation\n"
)


def _setup_steering(repo: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    # 毎ターンの注入は GDD の印（active な marker）があるときだけ
    (repo / ".claude").mkdir(exist_ok=True)
    (repo / ".claude" / "gdd-dev.local.md").write_text("---\nactive: true\n---\n", encoding="utf-8")
    steering = repo / ".steering" / "20260621-eventname"
    steering.mkdir(parents=True, exist_ok=True)
    steering.joinpath("state.md").write_text(_STATE, encoding="utf-8")
    steering.joinpath("requirements.md").write_text(_REQUIREMENTS, encoding="utf-8")
    steering.joinpath("tasklist.md").write_text(_TASKLIST, encoding="utf-8")


def _clean_env() -> dict:
    env = os.environ.copy()
    for var in (
        "CLAUDE_CODE_SESSION_ID",
        "GDD_PLUGIN_ROOT",
        "CLAUDE_PLUGIN_ROOT",
        "GDD_PLAN_REREAD_DEDUP_WINDOW",
        "GDD_STEERING_DIR",
    ):
        env.pop(var, None)
    return env


class UserPromptSubmitHookEventNameTests(unittest.TestCase):
    def test_manual_merge_continuation_includes_event_name(self) -> None:
        with tempfile.TemporaryDirectory(prefix="gdd-eventname-") as tmp:
            repo = Path(tmp)
            claude_dir = repo / ".claude"
            claude_dir.mkdir(parents=True, exist_ok=True)
            claude_dir.joinpath("gdd-post-merge-continuation.json").write_text("{}", encoding="utf-8")
            env = _clean_env()
            env["CLAUDE_USER_PROMPT"] = "マージした"
            result = subprocess.run(
                ["bash", str(USER_PROMPT_SUBMIT_HOOK)],
                cwd=repo,
                input="",
                capture_output=True,
                text=True,
                env=env,
            )
            self.assertEqual(
                result.returncode,
                0,
                f"hook exited non-zero: stdout={result.stdout!r} stderr={result.stderr!r}",
            )
            self.assertIn("additionalContext", result.stdout)
            payload = json.loads(result.stdout)
            self.assertEqual(
                payload["hookSpecificOutput"].get("hookEventName"),
                "UserPromptSubmit",
                f"stdout missing hookEventName: {result.stdout!r}",
            )

    def test_active_steering_context_includes_event_name(self) -> None:
        with tempfile.TemporaryDirectory(prefix="gdd-eventname-") as tmp:
            repo = Path(tmp)
            _setup_steering(repo)
            env = _clean_env()
            result = subprocess.run(
                ["bash", str(USER_PROMPT_SUBMIT_HOOK)],
                cwd=repo,
                input="",
                capture_output=True,
                text=True,
                env=env,
            )
            self.assertEqual(
                result.returncode,
                0,
                f"hook exited non-zero: stdout={result.stdout!r} stderr={result.stderr!r}",
            )
            self.assertIn("additionalContext", result.stdout)
            payload = json.loads(result.stdout)
            self.assertEqual(
                payload["hookSpecificOutput"].get("hookEventName"),
                "UserPromptSubmit",
                f"stdout missing hookEventName: {result.stdout!r}",
            )

    def test_review_cue_includes_event_name(self) -> None:
        with tempfile.TemporaryDirectory(prefix="gdd-eventname-") as tmp:
            repo = Path(tmp)
            steering = repo / ".steering" / "20260621-reviewcue"
            steering.mkdir(parents=True, exist_ok=True)
            steering.joinpath("state.md").write_text(
                "Resume From: gdd-implementation-gating\n", encoding="utf-8"
            )
            env = _clean_env()
            env["GDD_STEERING_DIR"] = str(steering)
            env["CLAUDE_USER_PROMPT"] = "レビューコメントを直して"
            result = subprocess.run(
                ["bash", str(USER_PROMPT_SUBMIT_HOOK)],
                cwd=repo,
                input="",
                capture_output=True,
                text=True,
                env=env,
            )
            self.assertEqual(
                result.returncode,
                0,
                f"hook exited non-zero: stdout={result.stdout!r} stderr={result.stderr!r}",
            )
            self.assertIn("additionalContext", result.stdout)
            payload = json.loads(result.stdout)
            self.assertEqual(
                payload["hookSpecificOutput"].get("hookEventName"),
                "UserPromptSubmit",
                f"stdout missing hookEventName: {result.stdout!r}",
            )

    def test_multiple_steering_warning_includes_event_name(self) -> None:
        with tempfile.TemporaryDirectory(prefix="gdd-eventname-") as tmp:
            repo = Path(tmp)
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            # 毎ターンの注入は GDD の印（active な marker）があるときだけ
            (repo / ".claude").mkdir(exist_ok=True)
            (repo / ".claude" / "gdd-dev.local.md").write_text("---\nactive: true\n---\n", encoding="utf-8")
            state = (
                "Started At: 2026-06-21T00:00:00+09:00\n"
                "Resume From: gdd-subagent-driven-implementation\n"
                "Requirements Review Status=approved | evidence: req\n"
                "Design Review Status=approved | evidence: design\n"
                "Human Check Status=approved | evidence: human\n"
                "Route In Progress=none\n"
            )
            for name in ("20260621-a", "20260621-b"):
                steering = repo / ".steering" / name
                steering.mkdir(parents=True, exist_ok=True)
                steering.joinpath("state.md").write_text(state, encoding="utf-8")
            env = _clean_env()
            result = subprocess.run(
                ["bash", str(USER_PROMPT_SUBMIT_HOOK)],
                cwd=repo,
                input="",
                capture_output=True,
                text=True,
                env=env,
            )
            self.assertEqual(
                result.returncode,
                0,
                f"hook exited non-zero: stdout={result.stdout!r} stderr={result.stderr!r}",
            )
            self.assertIn("additionalContext", result.stdout)
            payload = json.loads(result.stdout)
            self.assertEqual(
                payload["hookSpecificOutput"].get("hookEventName"),
                "UserPromptSubmit",
                f"stdout missing hookEventName: {result.stdout!r}",
            )

    def test_blocked_state_includes_event_name(self) -> None:
        with tempfile.TemporaryDirectory(prefix="gdd-eventname-") as tmp:
            repo = Path(tmp)
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            # 毎ターンの注入は GDD の印（active な marker）があるときだけ
            (repo / ".claude").mkdir(exist_ok=True)
            (repo / ".claude" / "gdd-dev.local.md").write_text("---\nactive: true\n---\n", encoding="utf-8")
            steering = repo / ".steering" / "20260621-blocked"
            steering.mkdir(parents=True, exist_ok=True)
            steering.joinpath("state.md").write_text(
                "Started At: 2026-06-21T00:00:00+09:00\n"
                "Resume From: gdd-subagent-driven-implementation\n"
                "Requirements Review Status=approved | evidence: req\n"
                "Design Review Status=approved | evidence: design\n"
                "Human Check Status=approved | evidence: human\n",
                encoding="utf-8",
            )
            env = _clean_env()
            result = subprocess.run(
                ["bash", str(USER_PROMPT_SUBMIT_HOOK)],
                cwd=repo,
                input="",
                capture_output=True,
                text=True,
                env=env,
            )
            self.assertEqual(
                result.returncode,
                0,
                f"hook exited non-zero: stdout={result.stdout!r} stderr={result.stderr!r}",
            )
            self.assertIn("additionalContext", result.stdout)
            payload = json.loads(result.stdout)
            self.assertEqual(
                payload["hookSpecificOutput"].get("hookEventName"),
                "UserPromptSubmit",
                f"stdout missing hookEventName: {result.stdout!r}",
            )


class PlanRereadHookEventNameTests(unittest.TestCase):
    def test_injection_includes_event_name(self) -> None:
        with tempfile.TemporaryDirectory(prefix="gdd-eventname-") as tmp:
            repo = Path(tmp)
            _setup_steering(repo)
            env = _clean_env()
            result = subprocess.run(
                ["bash", str(PLAN_REREAD_HOOK)],
                cwd=repo,
                input=json.dumps({"tool_name": "Edit", "tool_input": {}}),
                capture_output=True,
                text=True,
                env=env,
            )
            self.assertEqual(
                result.returncode,
                0,
                f"hook exited non-zero: stdout={result.stdout!r} stderr={result.stderr!r}",
            )
            self.assertIn("additionalContext", result.stdout)
            payload = json.loads(result.stdout)
            self.assertEqual(
                payload["hookSpecificOutput"].get("hookEventName"),
                "PreToolUse",
                f"stdout missing hookEventName: {result.stdout!r}",
            )


class SteeringWriteDenyEventNameTests(unittest.TestCase):
    def test_emit_deny_includes_event_name(self) -> None:
        script = PLUGIN_ROOT / "hooks" / "scripts" / "validate-steering-write.py"
        spec = importlib.util.spec_from_file_location("validate_steering_write", script)
        self.assertIsNotNone(spec, f"failed to load module spec from {script}")
        self.assertIsNotNone(spec.loader, f"module spec has no loader: {script}")
        module = importlib.util.module_from_spec(spec)
        sys.modules["validate_steering_write"] = module
        spec.loader.exec_module(module)
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            code = module.emit_deny([("email", "test violation")])
        self.assertEqual(code, 2)
        output = stderr.getvalue()
        payload = json.loads(output)
        self.assertEqual(
            payload["hookSpecificOutput"].get("hookEventName"),
            "PreToolUse",
            f"stderr missing hookEventName: {output!r}",
        )


class SteeringWriteFallbackEventNameTests(unittest.TestCase):
    def test_python_not_found_fallback_includes_event_name(self) -> None:
        bash_path = shutil.which("bash")
        self.assertIsNotNone(bash_path, "bash not found on PATH")
        with tempfile.TemporaryDirectory(prefix="gdd-eventname-") as tmp:
            repo = Path(tmp)
            empty_bin = repo / "empty-bin"
            empty_bin.mkdir()
            env = _clean_env()
            env["PATH"] = str(empty_bin)
            result = subprocess.run(
                [bash_path, str(STEERING_WRITE_HOOK)],
                cwd=repo,
                input=json.dumps({"tool_name": "Write", "tool_input": {}}),
                capture_output=True,
                text=True,
                env=env,
            )
            self.assertEqual(result.returncode, 2, f"expected deny exit code: stdout={result.stdout!r} stderr={result.stderr!r}")
            payload = json.loads(result.stderr)
            self.assertEqual(
                payload["hookSpecificOutput"].get("hookEventName"),
                "PreToolUse",
                f"stderr missing hookEventName: {result.stderr!r}",
            )


if __name__ == "__main__":
    unittest.main()
