"""Bounded poll policy for the gdd-pr-review-followup review-convergence loop.

Mirrors lib.auth_waiting: skill prose alone ("ポーリング上限（既定 12 回）を超えたら
blocked") was never enforced in the hook chain, so a stuck review loop could keep
re-arming ScheduleWakeup forever. This module makes the cap mechanical: the stop
hook reads `PR Review Follow-up Attempts` from state.md and forces reason=blocked
once the cap is reached, instead of trusting the skill to self-limit.
"""
from __future__ import annotations

import re
from collections.abc import Callable
from pathlib import Path

from lib.constants import PR_REVIEW_FOLLOWUP_MAX_ATTEMPTS
from lib.errors import append_hook_error
from lib.regular_file import read_regular_text

ATTEMPTS_PATTERN = re.compile(
    r'^[-*]?\s*`?PR Review Follow-up Attempts[=:]\s*(\d+)', re.IGNORECASE | re.MULTILINE
)


def read_pr_review_followup_attempts(state_text: str) -> int:
    """Extract `PR Review Follow-up Attempts` from a state.md body. Missing/unparseable → 0."""
    match = ATTEMPTS_PATTERN.search(state_text)
    if not match:
        return 0
    return int(match.group(1))


def next_reason_after_pr_review_poll(
    attempts: int, max_attempts: int = PR_REVIEW_FOLLOWUP_MAX_ATTEMPTS
) -> str:
    """Return the stop reason to emit after an external-review-waiting poll.

    - below the cap: keep pausing as `external-review-waiting` (re-arm the wake).
    - at/above the cap: transition to `blocked` (bounded; avoids infinite re-arm).
    """
    if attempts >= max_attempts:
        return "blocked"
    return "external-review-waiting"


def escalate_polling_reason(
    reason: str, find_state: Callable[[], tuple[Path, bool] | None], root: Path
) -> str:
    """ポーリング上限に達した `external-review-waiting` を `blocked` へ倒す。

    Architecture Check hook mechanization: skill の散文（「ポーリング上限 既定 12 回を
    超えたら blocked」）は自己強制されない ―― ループ中の agent は上限を超えても
    external-review-waiting を出し続けられる。transcript の内容とは独立に、active
    .steering state.md の `PR Review Follow-up Attempts` が
    PR_REVIEW_FOLLOWUP_MAX_ATTEMPTS に達した時点でここで reason を倒す
    （session evidence: PR #900/#922/#927）。`find_state` は stop hook の `_steering_candidate`
    で state.md と、それが使えるか（無ければ None）を返す。external-review-waiting のときだけ
    呼ぶ（ほかの停止理由で `.steering` の一覧の例外を出さない）。使えない（通常のファイルでない・
    steering の外）・一覧できない・読めないときも、回数を確かめられないので `blocked` に倒し、
    `.gdd/hook-errors.log` に記録する。
    """
    if reason != "external-review-waiting":
        return reason
    try:
        state = find_state()
        if state is None:
            return reason
        state_file, usable = state
        if not usable:
            raise OSError(f"not a regular file in the steering: {state_file}")
        state_text = read_regular_text(state_file, errors="replace")
    except OSError as exc:
        append_hook_error(root, "pr_review_poll_cap", f"state.md を読めないため blocked にした: {exc}")
        return "blocked"
    if state_text is None:
        return reason
    return next_reason_after_pr_review_poll(read_pr_review_followup_attempts(state_text))
