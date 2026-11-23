#!/usr/bin/env python3
"""Lint GDD PR review follow-up state for premature clean claims.

Exit code:
  0: pass
  1: premature or inconsistent PR review follow-up state found
  2: usage error / file not found
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


COUNT_RE = re.compile(r"^\s*-\s*Valid actionable findings:\s*(\d+)\s*$", re.MULTILINE)
FIXED_RE = re.compile(r"^\s*-\s*Fixed findings:\s*(.+?)\s*$", re.MULTILINE)
PUSH_RE = re.compile(r"^\s*-\s*Push:\s*(.+?)\s*$", re.MULTILINE)
RE_REVIEW_RE = re.compile(r"^\s*-\s*Re-review request:\s*(.+?)\s*$", re.MULTILINE)
SHA_RE = re.compile(r"\b[0-9a-f]{7,40}\b", re.IGNORECASE)
ISO_RE = re.compile(r"\b20\d\d-\d\d-\d\dT\d\d:\d\d:\d\d")
UNSAFE_CHECK_STATUSES = (
    "pending",
    "queued",
    "in_progress",
    "in progress",
    "running",
    "failure",
    "failed",
    "fail",
    "action_required",
    "cancelled",
    "timed_out",
    "timed out",
)


def has_clean_status(text: str) -> bool:
    return bool(re.search(r"^PR Review Follow-up Status:\s*clean\s*$", text, re.MULTILINE))


def valid_actionable_count(text: str) -> int | None:
    match = COUNT_RE.search(text)
    if not match:
        return None
    return int(match.group(1))


def line_value(text: str, label: str) -> str | None:
    prefix = f"{label}:"
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("- "):
            stripped = stripped[2:].strip()
        if stripped.startswith(prefix):
            return stripped[len(prefix) :].strip()
    return None


def fixed_findings_value(text: str) -> str | None:
    match = FIXED_RE.search(text)
    return match.group(1).strip() if match else None


def has_fixed_findings(text: str) -> bool:
    value = fixed_findings_value(text)
    if value is None:
        return False
    return value.lower() not in {"none", "なし", "-", "not_needed"}


def field_value(text: str, pattern: re.Pattern[str]) -> str | None:
    match = pattern.search(text)
    return match.group(1).strip() if match else None


def checks_evidence_has_unsafe_status(value: str | None) -> bool:
    if value is None:
        return False
    lowered = value.lower()
    return any(status in lowered for status in UNSAFE_CHECK_STATUSES)


def has_sha(value: str | None) -> bool:
    return bool(value and SHA_RE.search(value))


def has_timestamp(value: str | None) -> bool:
    return bool(value and ISO_RE.search(value))


def first_sha(value: str | None) -> str:
    if not value:
        return ""
    match = SHA_RE.search(value)
    return match.group(0).lower() if match else ""


def lint_text(text: str) -> list[str]:
    errors: list[str] = []
    clean = has_clean_status(text)
    valid_count = valid_actionable_count(text)
    fixed_findings = has_fixed_findings(text)
    checks_evidence = line_value(text, "Fresh PR Checks Evidence")
    post_fix_review_evidence = line_value(text, "Post-fix Fresh PR Review Evidence")
    post_fix_checks_evidence = line_value(text, "Post-fix Fresh PR Checks Evidence")
    head_sha = line_value(text, "PR Head SHA")
    pushed_sha = line_value(text, "Pushed SHA")
    review_head_sha = line_value(text, "Fresh PR Review Head SHA")
    checks_head_sha = line_value(text, "Fresh PR Checks Head SHA")
    evidence_collected_at = line_value(text, "Evidence collected at")
    post_fix_collected_at = line_value(text, "Post-fix evidence collected at")

    if clean and "Fresh PR Review Evidence:" not in text:
        errors.append("PR Review Follow-up clean claim requires fresh review evidence")
    if clean and "Fresh PR Checks Evidence:" not in text:
        errors.append("PR Review Follow-up clean claim requires fresh checks evidence")
    if clean and checks_evidence_has_unsafe_status(checks_evidence):
        errors.append("PR Review Follow-up clean claim rejected because fresh checks evidence is not pass/neutral/skipped")
    if clean and valid_count is None:
        errors.append("PR Review Follow-up clean claim requires Valid actionable findings count")
    if clean and valid_count is not None and valid_count > 0:
        errors.append("PR Review Follow-up clean claim conflicts with remaining valid actionable findings")
    if clean and not has_sha(head_sha):
        errors.append("PR Review Follow-up clean claim requires PR Head SHA")
    if clean and not has_sha(review_head_sha):
        errors.append("PR Review Follow-up clean claim requires Fresh PR Review Head SHA")
    if clean and not has_sha(checks_head_sha):
        errors.append("PR Review Follow-up clean claim requires Fresh PR Checks Head SHA")
    current_head = first_sha(head_sha)
    review_head = first_sha(review_head_sha)
    checks_head = first_sha(checks_head_sha)
    pushed_head = first_sha(pushed_sha)

    if clean and current_head and review_head and current_head != review_head:
        errors.append("PR Review Follow-up clean claim review evidence is for a stale head SHA")
    if clean and current_head and checks_head and current_head != checks_head:
        errors.append("PR Review Follow-up clean claim checks evidence is for a stale head SHA")
    if clean and not has_timestamp(evidence_collected_at):
        errors.append("PR Review Follow-up clean claim requires Evidence collected at timestamp")
    if clean and "- Next: actionable finding 0件" in text and valid_count is not None and valid_count > 0:
        errors.append("PR Review Follow-up Next says actionable finding 0件 while valid findings remain")
    if fixed_findings:
        push = field_value(text, PUSH_RE)
        re_review = field_value(text, RE_REVIEW_RE)
        if push is None or push.lower() in {"not_pushed", "not_needed", "none", "なし", "-"}:
            errors.append("PR Review Follow-up fixed findings need push evidence")
        if not has_sha(pushed_sha):
            errors.append("PR Review Follow-up fixed findings need pushed SHA evidence")
        if re_review is None or re_review.lower() != "sent":
            errors.append("PR Review Follow-up fixed findings need re-review request evidence")
        if clean and post_fix_review_evidence is None:
            errors.append("PR Review Follow-up clean claim after fixes requires post-fix fresh review evidence")
        if clean and post_fix_checks_evidence is None:
            errors.append("PR Review Follow-up clean claim after fixes requires post-fix fresh checks evidence")
        if clean and checks_evidence_has_unsafe_status(post_fix_checks_evidence):
            errors.append("PR Review Follow-up clean claim rejected because post-fix fresh checks evidence is not pass/neutral/skipped")
        if clean and not has_timestamp(post_fix_collected_at):
            errors.append("PR Review Follow-up clean claim after fixes requires post-fix evidence timestamp")
        if clean and pushed_head and current_head and pushed_head != current_head:
            errors.append("PR Review Follow-up clean claim head SHA must match pushed SHA after fixes")

    return errors


# tolerate CRLF and optional whitespace after the fence info string (release-gating lint).
_AUTH_PAUSE_BLOCK_RE = re.compile(r"```gdd-auth-pause[^\n]*\n(.*?)```", re.DOTALL)
_AUTH_PAUSE_REQUIRED_LABELS = ("reason", "resume-on", "no-cred")


def lint_auth_pause_marker(skill_text: str, allowed_reasons: set[str]) -> list[str]:
    """Structurally validate the auth pause resume contract block in a SKILL.

    This is a structural check, not a prose grep:
    - the fenced ```gdd-auth-pause block must exist,
    - it must carry the three required labels (reason / resume-on / no-cred),
    - the reason value must equal 'auth-waiting' and be a member of allowed_reasons.
    """
    errors: list[str] = []
    match = _AUTH_PAUSE_BLOCK_RE.search(skill_text)
    if not match:
        errors.append("auth pause marker: ```gdd-auth-pause block not found")
        return errors
    labels: dict[str, str] = {}
    for line in match.group(1).splitlines():
        stripped = line.strip()
        if ":" in stripped:
            key, value = stripped.split(":", 1)
            labels[key.strip()] = value.strip()
    for required in _AUTH_PAUSE_REQUIRED_LABELS:
        if required not in labels:
            errors.append(f"auth pause marker: missing '{required}' label")
    reason_value = labels.get("reason", "")
    if reason_value != "auth-waiting":
        errors.append(
            f"auth pause marker: reason must be 'auth-waiting', got '{reason_value}'"
        )
    elif reason_value not in allowed_reasons:
        errors.append("auth pause marker: reason 'auth-waiting' not in ALLOWED_STOP_REASONS")
    return errors


def _allowed_stop_reasons() -> set[str]:
    """Load ALLOWED_STOP_REASONS from the hook lib (release-gating lane helper)."""
    # **top-level module として**読む。`hooks/scripts` を載せて `from lib.X import`
    # すると `sys.modules["lib"]` が hooks 側に固定され、同一プロセスの
    # `scripts/lib`（`lint_base` 等）が解決できなくなる（実測: ModuleNotFoundError）。
    lib_dir = str(Path(__file__).resolve().parent.parent / "hooks" / "scripts" / "lib")
    sys.path.insert(0, lib_dir)
    try:
        from constants import ALLOWED_STOP_REASONS
    finally:
        if lib_dir in sys.path:
            sys.path.remove(lib_dir)

    return set(ALLOWED_STOP_REASONS)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", help="state.md or worklog.md files to lint")
    parser.add_argument(
        "--skill",
        action="append",
        default=[],
        help="SKILL.md file(s) to validate the auth pause marker (gdd-auth-pause block)",
    )
    parser.add_argument("--quiet", action="store_true", help="Suppress OK output")
    args = parser.parse_args()

    # fail-closed: a lint invoked with no target must not silently pass.
    if not args.paths and not args.skill:
        parser.error("at least one positional path or --skill <SKILL.md> is required")

    all_errors: list[tuple[Path, str]] = []
    for raw_path in args.paths:
        path = Path(raw_path)
        if not path.is_file():
            print(f"ERROR: file not found: {path}", file=sys.stderr)
            return 2
        text = path.read_text(encoding="utf-8", errors="replace")
        all_errors.extend((path, error) for error in lint_text(text))

    if args.skill:
        allowed = _allowed_stop_reasons()
        for raw_path in args.skill:
            path = Path(raw_path)
            if not path.is_file():
                print(f"ERROR: file not found: {path}", file=sys.stderr)
                return 2
            text = path.read_text(encoding="utf-8", errors="replace")
            all_errors.extend((path, error) for error in lint_auth_pause_marker(text, allowed))

    if all_errors:
        print("ERROR: PR Review Follow-up state is not safe to call clean.")
        for path, error in all_errors:
            print(f"- {error}: {path}")
        return 1

    if not args.quiet:
        print("OK: PR Review Follow-up state lint passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
