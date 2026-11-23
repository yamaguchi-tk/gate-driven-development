"""PR の statusCheckRollup を 1 つの CI の状態に分ける（Stop hook のマージ待ちの押し返しと scripts/wait-until.py）。

lib のほかの module に依存しない（scripts/ から top-level module として読むため）。
"""
from __future__ import annotations


def ci_states(rollup: object) -> set[str] | None:
    """check ごとの状態（failure / pending / success）の集合。check が無ければ空集合、読めない形なら None。"""
    if not isinstance(rollup, list):
        return None
    states: set[str] = set()
    for check in rollup:
        if not isinstance(check, dict):
            return None
        if "status" in check:
            status = str(check.get("status") or "").upper()
            conclusion = str(check.get("conclusion") or "").upper()
            if status != "COMPLETED":
                states.add("pending")
            elif conclusion in {"SUCCESS", "NEUTRAL", "SKIPPED"}:
                states.add("success")
            else:
                states.add("failure")
        else:
            state = str(check.get("state") or "").upper()
            if state == "SUCCESS":
                states.add("success")
            elif state in {"PENDING", "EXPECTED"}:
                states.add("pending")
            else:
                states.add("failure")
    return states


def ci_state(rollup: object) -> str | None:
    """failure / pending / success / no-checks のどれか（failure を最優先する）。読めない形なら None。"""
    states = ci_states(rollup)
    if states is None:
        return None
    for state in ("failure", "pending", "success"):
        if state in states:
            return state
    return "no-checks"  # checks がまだ登録されていない（push の直後）か、repo に checks が無い
