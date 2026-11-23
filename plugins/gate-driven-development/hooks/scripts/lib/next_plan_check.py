"""Helpers for OT-F9 E2/E3: '### 次の計画' block and Follow-up Stage Lane checks."""
from __future__ import annotations
import re
from pathlib import Path

from lib.regular_file import read_regular_bytes
from lib.tasklist_parse import NON_NEWLINE_LINE_BREAKS, strip_fenced_blocks

# '### 次の計画' heading (1–3 hashes)
_NEXT_PLAN_RE = re.compile(r'^#{1,3}\s*次の計画', re.MULTILINE)

# 'Planned Follow-up Stage Lane' sections: from the heading line (any text after the
# title) to the next '#' or '##' heading. A heading needs a space, a tab or the line end
# after the hashes (CommonMark ATX), so '#\u3000note' does not end the section.
_STAGE_LANE_HEADING = 'Planned Follow-up Stage Lane'
_STAGE_LANE_SECTION_RE = re.compile(
    r'^##\s+Planned Follow-up Stage Lane[^\n]*(.*?)(?=^#{1,2}(?:[ \t]|$)|\Z)',
    re.MULTILINE | re.DOTALL,
)

# The only non-blank line a completed Lane may contain. Every other line is pending.
_CHECKED_ITEM_RE = re.compile(r'^\s*-\s+\[[xX]\]')

# "Registry: created" claim anywhere in text
_REGISTRY_CLAIMED_RE = re.compile(r'Registry:\s*created', re.IGNORECASE)

# .claude/gdd-continuations/<id>.json reference in text
_CONTINUATION_REF_RE = re.compile(r'gdd-continuations/([^./\s`"\']+)\.json')


def has_next_plan_block(text: str) -> bool:
    """Return True if text contains a '次の計画' Markdown heading (1–3 hashes)."""
    return bool(_NEXT_PLAN_RE.search(text))


def _lane_has_pending(section: str) -> bool:
    """Return True unless every non-blank line is a checked item ('- [x]').

    requirements-template.md writes the Lane as a table with no completion column,
    so any table row (header included) is pending: remove the table when every
    stage is done. Headings and other shapes are pending too (fail-closed).
    """
    return any(
        line.strip() and not _CHECKED_ITEM_RE.match(line) for line in section.splitlines()
    )


def has_incomplete_follow_up_stages(requirements_text: str) -> bool:
    """Return True if requirements_text has a Follow-up Stage Lane with pending items.

    Each Lane is complete only when its lines are checked items ('- [x]') or blank.
    Any other line, including a table row, a subheading and a '- [ ]' item, is pending.
    Fenced code blocks are examples, not current values, so they are dropped first
    (unclosed fences keep the text after the opener; see strip_fenced_blocks).
    If the Lane title appears anywhere and the text has a line break other than LF/CR
    anywhere, the lines are ambiguous and the Lane counts as pending.
    """
    if _STAGE_LANE_HEADING in requirements_text and any(
        ch in requirements_text for ch in NON_NEWLINE_LINE_BREAKS
    ):
        return True
    body = strip_fenced_blocks(requirements_text)
    return any(_lane_has_pending(m.group(1)) for m in _STAGE_LANE_SECTION_RE.finditer(body))


def requirements_lane_pending(path: Path) -> bool:
    """Read requirements.md at path and return has_incomplete_follow_up_stages for it.

    A missing path has no Lane: False. Anything else that is not a readable regular
    file (directory, FIFO, device, permission or I/O error, symlink loop) counts as
    pending: True, so the stop is held until the output has '### 次の計画' (fail-closed).
    """
    try:
        data = read_regular_bytes(path)
    except OSError:
        return True
    if data is None:
        return False
    return has_incomplete_follow_up_stages(data.decode("utf-8", errors="replace"))


def registry_creation_claimed(text: str) -> bool:
    """Return True if text contains 'Registry: created'."""
    return bool(_REGISTRY_CLAIMED_RE.search(text))


def continuation_file_exists(project_root: Path, text: str) -> bool:
    """Return True if a claimed .claude/gdd-continuations/<id>.json file exists.

    Fail-open: if no file path is referenced in text, returns True (nothing to verify).
    """
    m = _CONTINUATION_REF_RE.search(text)
    if not m:
        return True
    path = project_root / ".claude" / "gdd-continuations" / f"{m.group(1)}.json"
    return path.exists()
