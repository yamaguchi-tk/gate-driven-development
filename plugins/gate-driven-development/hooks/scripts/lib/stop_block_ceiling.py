"""Stop hook の連続 block の上限（gdd_stop_hook から移した。挙動は同じ）。"""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

from lib.state_io import write_state

# Claude Code's own hard cap on consecutive Stop-hook blocks is internal and
# not exposed as a constant we can read; 9 is the highest value observed in
# practice before Claude Code force-overrides the hook. GDD_STOP_HOOK_MAX_
# CONSECUTIVE_BLOCKS below is clamped strictly under this so an operator
# override can never accidentally equal/exceed Claude Code's own cap, which
# would defeat the point of failing closed on GDD's own terms first.
_CLAUDE_STOP_HOOK_HARD_CAP_OBSERVED = 9

# Self-imposed ceiling on consecutive stop_hook_active=true invocations (see
# enforce_consecutive_block_ceiling). Kept below Claude Code's own hard cap
# above so GDD can fail closed to a resumable pause on its own terms instead
# of being force-overridden mid-workflow.
try:
    STOP_HOOK_MAX_CONSECUTIVE_BLOCKS = int(
        os.environ.get("GDD_STOP_HOOK_MAX_CONSECUTIVE_BLOCKS", "6")
    )
except ValueError:
    STOP_HOOK_MAX_CONSECUTIVE_BLOCKS = 6
if not (1 <= STOP_HOOK_MAX_CONSECUTIVE_BLOCKS < _CLAUDE_STOP_HOOK_HARD_CAP_OBSERVED):
    # <1 would trip the ceiling immediately (or every call), breaking
    # legitimate multi-phase same-turn continuation; >= the observed hard
    # cap would let Claude Code's own override fire first. Either way, fall
    # back to the default instead of honoring an unusable configured value.
    STOP_HOOK_MAX_CONSECUTIVE_BLOCKS = 6

# stop_hook_active=false does not always mean "a fresh user turn started" —
# a background Agent's <task-notification> also arrives as a new user turn
# with stop_hook_active=false, which would otherwise reset the ceiling
# counter on every notification during a long completion wait and let the
# block burst run forever. This window treats a stop_hook_active=false call
# arriving shortly after the previous block as still part of the same burst.
try:
    GDD_STOP_HOOK_BLOCK_RESET_WINDOW_SECONDS = int(
        os.environ.get("GDD_STOP_HOOK_BLOCK_RESET_WINDOW_SECONDS", "120")
    )
except ValueError:
    GDD_STOP_HOOK_BLOCK_RESET_WINDOW_SECONDS = 120
if GDD_STOP_HOOK_BLOCK_RESET_WINDOW_SECONDS < 0:
    GDD_STOP_HOOK_BLOCK_RESET_WINDOW_SECONDS = 120


def _coerce_stop_hook_active(value: object) -> bool:
    """Robustly interpret hook_input["stop_hook_active"].

    Claude Code sends this as a real JSON boolean, but tolerate string forms
    ("true"/"false"/"1"/"0") defensively — `bool("false")` would otherwise be
    `True` and could wrongly increment the consecutive-block counter.
    """
    if isinstance(value, str):
        return value.strip().lower() not in ("", "false", "0")
    return bool(value)


def next_block_count(hook_input: dict, frontmatter: dict[str, str], now: int) -> int:
    """この Stop で block したときの連続 block の数（frontmatter は変えない）。"""
    stop_hook_active = _coerce_stop_hook_active(hook_input.get("stop_hook_active"))
    try:
        count = int(frontmatter.get("consecutive_stop_hook_blocks", "0"))
    except ValueError:
        count = 0
    try:
        last_block_at = int(frontmatter.get("consecutive_stop_hook_blocks_at", "0"))
    except ValueError:
        last_block_at = 0
    within_reset_window = (
        last_block_at > 0 and (now - last_block_at) < GDD_STOP_HOOK_BLOCK_RESET_WINDOW_SECONDS
    )
    return count + 1 if (stop_hook_active or within_reset_window) else 0


def enforce_consecutive_block_ceiling(
    hook_input: dict,
    frontmatter: dict[str, str],
    prompt_body: str,
    state_path: Path,
) -> None:
    """Fail-closed guard against runaway Stop-hook block chains (T-10).

    Claude Code sets `stop_hook_active=true` when this Stop hook fires again
    as a direct continuation of its own previous "block" decision within the
    same turn chain — not because of a fresh user message. GDD intentionally
    chains many such blocks to drive autonomous phase transitions, so we
    cannot simply allow stop whenever `stop_hook_active` is true (that would
    break multi-phase continuation after the very first block). Instead we
    count consecutive chained invocations and self-abort before Claude
    Code's own hard STOP_HOOK_BLOCK_CAP has to force an ungraceful override
    (observed: 9 consecutive blocks with no GDD-owned resume state).

    Called only once main() has determined it is about to force another
    continuation block (no valid <gdd-stop> marker was found anywhere).
    Preserve-only pause reasons (auth-waiting etc.) exit via
    try_stop_with_done_guard before this function is ever reached, so this
    guard never mutates state.md on those paths.

    stop_hook_active=false does not by itself mean a fresh user turn began
    a new burst — a background Agent's <task-notification> also arrives as
    a new user turn with stop_hook_active=false. If such a notification
    lands within GDD_STOP_HOOK_BLOCK_RESET_WINDOW_SECONDS of the previous
    block, the counter keeps incrementing instead of resetting, so a long
    completion wait cannot restart the burst indefinitely (AC-E9-3).

    When under the ceiling, only mutates `frontmatter` in place — the
    caller's own write_state() call a few lines later persists it, avoiding
    a redundant write. When the ceiling is exceeded, writes the reset
    immediately since that path exits before the caller's write_state runs.
    """
    now = int(time.time())
    count = next_block_count(hook_input, frontmatter, now)

    if count > STOP_HOOK_MAX_CONSECUTIVE_BLOCKS:
        frontmatter["consecutive_stop_hook_blocks"] = "0"
        frontmatter["consecutive_stop_hook_blocks_at"] = "0"
        write_state(state_path, frontmatter, prompt_body)
        print(
            f"GDD Stop hook: {count - 1} consecutive stop-hook blocks reached "
            f"the self-imposed ceiling ({STOP_HOOK_MAX_CONSECUTIVE_BLOCKS}) "
            "without a <gdd-stop> marker being emitted. Pausing before Claude "
            "Code's own hard block cap forces an ungraceful stop. "
            "state.md/tasklist.md are preserved — resume with /gdd-dev.",
            file=sys.stderr,
        )
        raise SystemExit(0)

    frontmatter["consecutive_stop_hook_blocks"] = str(count)
    frontmatter["consecutive_stop_hook_blocks_at"] = "0" if count == 0 else str(now)
