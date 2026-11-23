from __future__ import annotations

import re

from lib.constants import (
    GOAL_COMPLETE_REASONS,
    GOAL_INCOMPLETE_REASONS,
    _APPROVAL_REPLY_RE,
    _GDD_PHASE_MARKER_RE,
    _GDD_SKILL_REF_RE,
    _GDD_SLASH_RE,
    _HUMAN_CHECK_PAUSE_RE,
)


def goal_completion_allowed_for_stop(reason: str) -> bool:
    """Return True only when a GDD stop reason may complete the Codex Goal."""
    return reason in GOAL_COMPLETE_REASONS


def goal_guard_message(reason: str) -> str:
    if goal_completion_allowed_for_stop(reason):
        return (
            "Codex Goal guard: GDD done guard passed. It is safe to mark the "
            "thread Goal complete if no other user-requested work remains."
        )
    if reason in GOAL_INCOMPLETE_REASONS:
        return (
            f"Codex Goal guard: <gdd-stop reason=\"{reason}\"> is not a "
            "successful completion state. Do not mark the thread Goal complete; "
            "resume /gdd-dev after the required human or environment action."
        )
    return (
        f"Codex Goal guard: unknown stop reason {reason!r}. Do not mark the "
        "thread Goal complete unless Next Action=done and done guard passed."
    )


def looks_like_gdd_continuation(user_text: str, last_assistant_text: str) -> bool:
    """Decide whether the Stop hook should force the model to keep running
    the active GDD workflow.

    Returns True only when the user (or the just-finished assistant turn)
    clearly indicates the workflow is still in motion:

    1. The user's most recent prompt invokes GDD explicitly — `/gdd-dev`,
       `/gdd-status`, mention of a GDD skill name.
    2. The previous assistant turn emitted a human-check pause template
       (`<gdd-stop reason="human-check-waiting">`, `🔍 確認をお願いします`,
       `承認ポイント`) — and the user replied with a short approval-style
       message (`OK`, `承認`, `進めて` …) or nothing.
    3. The previous assistant turn emitted a `<gdd-phase>` marker, meaning
       a phase skill is mid-flight (and therefore wants to continue across
       turn boundaries).

    Returns False when the user appears to have moved on to an unrelated
    topic. In that case the Stop hook exits silently instead of injecting
    `Continue the active /gdd-dev run.`, which previously hijacked any
    conversation that happened while a stale `.claude/gdd-dev.local.md`
    sat on disk.
    """
    s = (user_text or "").strip()
    if s:
        # A bare URL is never a GDD continuation signal — early-exit to prevent
        # URL pastes from being classified as GDD task starts.
        if re.match(r'^https?://\S+$', s):
            return False
        if _GDD_SLASH_RE.search(s):
            return True
        if _GDD_SKILL_REF_RE.search(s):
            return True
    if last_assistant_text:
        if _GDD_PHASE_MARKER_RE.search(last_assistant_text):
            return True
        if _HUMAN_CHECK_PAUSE_RE.search(last_assistant_text):
            # Only treat as continuation when the user replies with an approval
            # (or sends nothing). An unrelated question like "worktreeで作業してる？"
            # or a tool-confirm "OK" should NOT trigger GDD resumption.
            if not s or _APPROVAL_REPLY_RE.match(s):
                return True
    return False
