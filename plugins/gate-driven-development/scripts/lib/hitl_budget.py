"""Single source of truth for HITL line-count budgets.

`scripts/lint-hitl-complexity.py` and `references/human-check-template*.md`
both derive their numeric budgets from this module. Do not hardcode these
values elsewhere; a contract test (test_hitl_lint_marker_sync_contract.py)
asserts template text stays in sync.
"""
from __future__ import annotations

PRIMARY_SURFACE_MAX_LINES = {
    "quick (express)": 10,
    "quick (standard)": 20,
    "standard": 45,
}
HITL_SAMPLE_MAX_LINES = 60
