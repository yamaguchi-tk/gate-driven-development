"""Contract tests for S-1: auth-waiting non-terminal pause base.

Covers AC-1 / AC-2 / AC-2b / AC-3(b,c,d) of gdd-self-healing-resume-gaps.
Mirrors the existing external-review-waiting pause e2e (OT-F3) for the hook path.

Run from plugins/gate-driven-development/:
  python3 -m pytest tests/test_auth_waiting_pause_contract.py -q
"""
from __future__ import annotations
# isort: skip_file
# ruff: noqa: F401,F403,F811
import sys
from pathlib import Path as _P

sys.path.insert(0, str(_P(__file__).parent))

from _stop_hook_test_base import *  # noqa: F401,F403
from _plugin_module_loader import load_plugin_module

from _paths import PLUGIN_ROOT as _PLUGIN_ROOT
_LINT_PATH = _PLUGIN_ROOT / "scripts" / "lint-pr-review-followup-state.py"

# token-shaped fake secret (NOT a real credential) for the no-leak negative test.
_FAKE_TOKEN = "ghp_FAKE0000000000000000000000000000000000"

_NEXT_ACTION_BLOCK = "\n\n## 👤 次にすること\n再ログインしてください。完了後に自動で再開します。"


def _load_lint_module():
    return load_plugin_module("scripts/lint-pr-review-followup-state.py")


# ---------------------------------------------------------------------------
# AC-1: constants membership
# ---------------------------------------------------------------------------
class TestAuthWaitingConstants(unittest.TestCase):
    def test_constants_auth_waiting_in_allowed_and_incomplete_not_complete(self):
        from lib import constants
        self.assertIn("auth-waiting", constants.ALLOWED_STOP_REASONS)
        self.assertIn("auth-waiting", constants.GOAL_INCOMPLETE_REASONS)
        self.assertNotIn("auth-waiting", constants.GOAL_COMPLETE_REASONS)


# ---------------------------------------------------------------------------
# AC-2 / AC-2b / AC-3a / AC-3c: stop hook path
# ---------------------------------------------------------------------------
class TestAuthWaitingHookPath(unittest.TestCase):
    def _setup_active_session(self, ws: Path, assistant_text: str) -> Path:
        _write_state_file(ws, {"active": "true", "session_id": "test-session", "iteration": "1"})
        transcript = ws / "transcript.jsonl"
        _make_transcript_jsonl(transcript, assistant_text=assistant_text)
        return transcript

    def test_auth_waiting_is_pause_and_preserves_state(self):
        """AC-2 / AC-3a: auth-waiting is non-terminal; state.md preserved, no nudge."""
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            state_file = _write_state_file(ws, {
                "active": "true", "session_id": "test-session", "iteration": "1",
            })
            tasklist_dirty = textwrap.dedent("""\
                # Tasklist

                ## Current Task
                ### Task: T-1 | AC-01 | active task

                ## Pending Tasks
                - T2 | AC-02 | next

                ## Completed Tasks
                - なし
            """)
            _write_steering(ws, "20260501-test", tasklist_dirty)
            transcript = self._setup_active_session(
                ws,
                "<gdd-phase>gdd-pr-review-followup</gdd-phase>\n"
                "SSO セッションが切れました。\n\n"
                '<gdd-stop reason="auth-waiting">' + _NEXT_ACTION_BLOCK,
            )
            code, out, _ = _run_hook(ws, transcript, session_id="test-session")
            self.assertEqual(code, 0)
            self.assertNotIn('"decision": "block"', out)
            self.assertNotIn("Continue to terminal state", out)
            self.assertTrue(
                state_file.exists(),
                "auth-waiting must preserve state.md (pause, not terminal)",
            )

    def test_auth_waiting_passes_next_action_guard_when_block_present(self):
        """AC-2b: auth-waiting + '👤 次にすること' is NOT blocked by line 558 guard;
        and auth-waiting must not be EXEMPT (the block is required)."""
        from lib.next_action_check import EXEMPT_REASONS
        self.assertNotIn("auth-waiting", EXEMPT_REASONS)
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            _write_steering(ws, "20260501-test", "# Tasklist\n\n## Current Task\n- なし\n")
            transcript = self._setup_active_session(
                ws,
                '<gdd-stop reason="auth-waiting">' + _NEXT_ACTION_BLOCK,
            )
            code, out, _ = _run_hook(ws, transcript, session_id="test-session")
            self.assertEqual(code, 0)
            self.assertNotIn("👤 次にすること` ブロックが見当たりません", out)
            self.assertNotIn('"decision": "block"', out)

    def test_auth_waiting_path_is_preserve_only_and_token_free(self):
        """AC-3c / security M-1: the auth-waiting branch must not introduce a NEW
        leak path. It is preserve-only — it keeps the existing state.md unchanged
        and writes nothing transcript-derived. A token-shaped value present in the
        assistant output must not appear in stdout nor be injected into state.md.

        Scope note (impl-gate M-1 remediation): general Context-Handoff summary
        persistence (`persist_handoff_summary`) is a reason-agnostic, pre-existing
        mechanism and its redaction is out of S-1 scope. This test binds the
        auth-waiting-specific guarantee: the pause adds no new persistence surface.
        """
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            state_file = _write_state_file(ws, {
                "active": "true", "session_id": "test-session", "iteration": "1",
            })
            before = state_file.read_text(encoding="utf-8")
            self.assertNotIn(_FAKE_TOKEN, before)
            _write_steering(ws, "20260501-test", "# Tasklist\n\n## Current Task\n- なし\n")
            # assistant prose carries a token-shaped value (NO Context Handoff block).
            transcript = self._setup_active_session(
                ws,
                f"auth 失効を検知しました（参考トークン: {_FAKE_TOKEN}）\n\n"
                '<gdd-stop reason="auth-waiting">' + _NEXT_ACTION_BLOCK,
            )
            code, out, _ = _run_hook(ws, transcript, session_id="test-session")
            self.assertEqual(code, 0)
            self.assertNotIn(_FAKE_TOKEN, out)
            # preserve-only: state.md kept and byte-identical → no new write path.
            self.assertTrue(state_file.exists(), "auth-waiting must preserve state.md")
            after = state_file.read_text(encoding="utf-8")
            self.assertEqual(after, before, "auth-waiting must not mutate state.md (preserve-only)")
            self.assertNotIn(_FAKE_TOKEN, after)


class TestAuthPauseLintCLI(unittest.TestCase):
    """M1 remediation: the --skill CLI enforcement point must be real (not dead)
    and fail-closed on zero input."""

    def _run_lint(self, *args: str) -> int:
        import subprocess
        return subprocess.run(
            ["python3", str(_LINT_PATH), *args],
            capture_output=True, text=True,
        ).returncode

    def test_zero_input_is_fail_closed(self):
        # neither positional path nor --skill → must NOT silently pass (exit 0).
        self.assertNotEqual(self._run_lint("--quiet"), 0)


# ---------------------------------------------------------------------------
# AC-3b: structured auth pause marker lint
# ---------------------------------------------------------------------------
class TestAuthPauseMarkerLint(unittest.TestCase):
    def test_lint_auth_pause_marker_accepts_valid_block(self):
        from lib import constants
        lint = _load_lint_module()
        valid = (
            "### auth pause 再開規約\n"
            "```gdd-auth-pause\n"
            "reason: auth-waiting\n"
            "resume-on: 再ログイン検知後の ScheduleWakeup 再 arm で自走再開\n"
            "no-cred: 認証情報（SSO token 等）は保持・出力しない\n"
            "```\n"
        )
        errors = lint.lint_auth_pause_marker(valid, constants.ALLOWED_STOP_REASONS)
        self.assertEqual(errors, [])

    def test_lint_auth_pause_marker_rejects_missing_block(self):
        from lib import constants
        lint = _load_lint_module()
        errors = lint.lint_auth_pause_marker("散文だけで構造化ブロックなし", constants.ALLOWED_STOP_REASONS)
        self.assertTrue(errors, "missing structured block must produce errors")


# ---------------------------------------------------------------------------
# AC-3d: bounded wake cap
# ---------------------------------------------------------------------------
class TestAuthWaitingWakeCap(unittest.TestCase):
    def test_wake_cap_rearms_until_limit_then_blocks(self):
        from lib.auth_waiting import next_reason_after_auth_wake
        from lib.constants import AUTH_WAITING_MAX_WAKES
        self.assertEqual(next_reason_after_auth_wake(0), "auth-waiting")
        self.assertEqual(next_reason_after_auth_wake(AUTH_WAITING_MAX_WAKES - 1), "auth-waiting")
        self.assertEqual(next_reason_after_auth_wake(AUTH_WAITING_MAX_WAKES), "blocked")

    def test_wake_cap_max_is_overridable(self):
        from lib.auth_waiting import next_reason_after_auth_wake
        self.assertEqual(next_reason_after_auth_wake(2, max_wakes=3), "auth-waiting")
        self.assertEqual(next_reason_after_auth_wake(3, max_wakes=3), "blocked")


if __name__ == "__main__":
    unittest.main()
