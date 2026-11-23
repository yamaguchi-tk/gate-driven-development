"""Bounded wake policy for the auth-waiting pause (S-1).

auth-waiting is a non-terminal pause used when an SSO/auth session expires during
autonomous execution. The session re-arms a ScheduleWakeup to resume after the
human re-logs in. To avoid re-arming forever when no re-login ever happens, the
wake budget is bounded: at the cap the loop transitions to `blocked` instead of
silently re-arming. No credential value is ever read or stored here.
"""
from __future__ import annotations

from lib.constants import AUTH_WAITING_MAX_WAKES


def next_reason_after_auth_wake(
    wake_count: int, max_wakes: int = AUTH_WAITING_MAX_WAKES
) -> str:
    """Return the stop reason to emit after an auth-waiting wake.

    - below the cap: keep pausing as `auth-waiting` (re-arm the wake).
    - at/above the cap: transition to `blocked` (bounded; avoids infinite re-arm).
    """
    if wake_count >= max_wakes:
        return "blocked"
    return "auth-waiting"
