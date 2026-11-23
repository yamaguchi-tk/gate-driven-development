"""Check for '👤 次にすること' block in stop output (OT-F10)."""
from __future__ import annotations

import re

_NEXT_ACTION_RE = re.compile(r'^#+\s*👤\s*次にすること', re.MULTILINE)

# Reasons that do NOT require a 次にすること block.
# cancelled = user-initiated explicit abort; no user guidance needed.
EXEMPT_REASONS = frozenset({"cancelled"})

# Canonical heading string embedded in the Stop hook's own continuation
# message so both sides (the instruction and the done-guard check) share a
# single source of truth instead of independently hand-written literals.
NEXT_ACTION_HEADING = "# 👤 次にすること"


def has_next_action_block(text: str) -> bool:
    """Return True if text contains a Markdown heading line with '👤 次にすること'."""
    return bool(_NEXT_ACTION_RE.search(text))
