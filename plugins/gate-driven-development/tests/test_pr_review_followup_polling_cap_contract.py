"""Contract tests for the mechanical PR-review-followup poll cap (Architecture Check
hook mechanization).

Root cause (2026-08-14 GDD self-improvement investigation): `gdd-pr-review-followup`
SKILL.md prose says "ポーリング上限（既定 12 回）を超えたら blocked" but nothing in the
stop hook chain ever enforced it — mirrors the pre-existing gap where
`lib.auth_waiting.next_reason_after_auth_wake` was unit-tested but never wired into
`gdd_stop_hook.py`. An agent that self-declares an exemption from the skill's own
limit (observed in PR #900/#922/#927 sessions) can re-arm `external-review-waiting`
indefinitely. This makes the cap mechanical: the stop hook itself forces
reason=blocked once `PR Review Follow-up Attempts` reaches the cap, independent of
what the skill prose says or what the agent decides.

Run from plugins/gate-driven-development/:
  python3 -m pytest tests/test_pr_review_followup_polling_cap_contract.py -q
"""
from __future__ import annotations
# isort: skip_file
# ruff: noqa: F401,F403,F811
import sys
from pathlib import Path as _P

sys.path.insert(0, str(_P(__file__).parent))

from _stop_hook_test_base import *  # noqa: F401,F403
import test_auth_waiting_pause_contract as _auth_waiting

_NEXT_ACTION_BLOCK = "\n\n## 👤 次にすること\nレビュー収束を待っています。中断するには「中断」と言ってください。"


class TestPrReviewFollowupPollCapUnit(unittest.TestCase):
    def test_read_attempts_parses_markdown_field(self):
        from lib.pr_review_followup_polling import read_pr_review_followup_attempts
        text = "PR Review Follow-up Status: waiting_for_review\n- PR Review Follow-up Attempts: 7\n"
        self.assertEqual(read_pr_review_followup_attempts(text), 7)

    def test_read_attempts_defaults_to_zero_when_missing(self):
        from lib.pr_review_followup_polling import read_pr_review_followup_attempts
        self.assertEqual(read_pr_review_followup_attempts("# Tasklist\n\nno such field\n"), 0)

    def test_poll_cap_rearms_until_limit_then_blocks(self):
        from lib.pr_review_followup_polling import next_reason_after_pr_review_poll
        from lib.constants import PR_REVIEW_FOLLOWUP_MAX_ATTEMPTS
        self.assertEqual(next_reason_after_pr_review_poll(0), "external-review-waiting")
        self.assertEqual(
            next_reason_after_pr_review_poll(PR_REVIEW_FOLLOWUP_MAX_ATTEMPTS - 1),
            "external-review-waiting",
        )
        self.assertEqual(next_reason_after_pr_review_poll(PR_REVIEW_FOLLOWUP_MAX_ATTEMPTS), "blocked")

    def test_poll_cap_max_is_overridable(self):
        from lib.pr_review_followup_polling import next_reason_after_pr_review_poll
        self.assertEqual(next_reason_after_pr_review_poll(2, max_attempts=3), "external-review-waiting")
        self.assertEqual(next_reason_after_pr_review_poll(3, max_attempts=3), "blocked")


class TestPrReviewFollowupPollCapHookPath(unittest.TestCase):
    _setup_active_session = _auth_waiting.TestAuthWaitingHookPath._setup_active_session

    def test_below_cap_still_pauses_as_external_review_waiting(self):
        """Below the cap, the hook behaves exactly as before: pause, preserve state.md."""
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            state_file = _write_state_file(ws, {
                "active": "true", "session_id": "test-session", "iteration": "1",
            })
            tasklist = "# Tasklist\n\n## Current Task\n### Task: T-1 | AC-01 | active\n"
            state_body = (
                "# State\n\nResume From: external-review-waiting\n"
                "- PR Review Follow-up Attempts: 5\n"
            )
            _write_steering(ws, "20260501-test", tasklist, state_content=state_body)
            transcript = self._setup_active_session(
                ws,
                "<gdd-phase>gdd-pr-review-followup</gdd-phase>\n"
                'レビュー収束を待っています。\n\n<gdd-stop reason="external-review-waiting">'
                + _NEXT_ACTION_BLOCK,
            )
            code, out, _ = _run_hook(ws, transcript, session_id="test-session")
            self.assertEqual(code, 0)
            self.assertNotIn('"decision": "block"', out)
            self.assertTrue(state_file.exists(), "below cap: state.md must be preserved")

    def test_at_cap_forces_blocked_and_clears_state(self):
        """At the poll cap, the hook must force reason=blocked even though the
        transcript emitted external-review-waiting — the agent cannot self-exempt
        from the cap by continuing to emit the pause reason."""
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            state_file = _write_state_file(ws, {
                "active": "true", "session_id": "test-session", "iteration": "1",
            })
            tasklist = "# Tasklist\n\n## Current Task\n### Task: T-1 | AC-01 | active\n"
            state_body = (
                "# State\n\nResume From: external-review-waiting\n"
                "- PR Review Follow-up Attempts: 12\n"
            )
            _write_steering(ws, "20260501-test", tasklist, state_content=state_body)
            transcript = self._setup_active_session(
                ws,
                "<gdd-phase>gdd-pr-review-followup</gdd-phase>\n"
                'レビュー収束を待っています。\n\n<gdd-stop reason="external-review-waiting">'
                + _NEXT_ACTION_BLOCK,
            )
            code, out, _ = _run_hook(ws, transcript, session_id="test-session")
            self.assertEqual(code, 0)
            self.assertNotIn('"decision": "block"', out)
            self.assertFalse(
                state_file.exists(),
                "at cap: state.md must be cleared (blocked is terminal-for-this-loop, not a pause)",
            )


if __name__ == "__main__":
    unittest.main()
