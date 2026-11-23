"""PreToolUse（Agent）: main からの gdd-formal-gate-runner の起動を background に強制する。

同期で起動すると Stop が来ないので、期限 watchdog（lib/wait_watchdog.py）が当たらない。
対象は main の呼び出しだけで、subagent の中（payload に agent_id がある）は強制しない（subagent が
background の完了通知を受け取れるかは確かめていない）。reviewer は main が turn の中で結果を集める経路があるので対象外。

正本の規定は references/subagent-dispatch.md § Typed Agent Resolution（時間上限は § Reviewer Input and Time Budget）。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from lib.errors import append_hook_error
from lib.wait_watchdog import LIMITS, limit_kind

TARGET = "gdd-formal-gate-runner"


def deny_reason(payload: object) -> str | None:
    """deny するなら理由を返す。通すなら None（型を読めない payload も通す）。"""
    if not isinstance(payload, dict) or "agent_id" in payload:
        return None
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return None
    subagent_type = tool_input.get("subagent_type")
    if not isinstance(subagent_type, str) or limit_kind(subagent_type) != TARGET:
        return None
    # 文字列の "true" も通す。2026-11-13、Agent の定義に run_in_background が無いセッション（定義の説明は
    # 「subagent は background で動く」）で、この値が文字列の "true" のまま届いた（観測）。定義に引数がある host では
    # 届く前に bool へ変換されると推定している。欠落・False は host によって同期になるので止める。
    background = tool_input.get("run_in_background")
    if background is True or background == "true":
        return None
    return (
        f"{TARGET} は Agent の run_in_background: true で起動する（同期で起動すると期限を測れない）。"
        f"起動の後に、Bash の run_in_background: true で期限 timer `sleep {LIMITS[TARGET] + 60}` を起動し、"
        "目印（gdd-stop）を書かずに turn を終えて待つ。gate-runner 自身の完了通知（途中の通知を除く）の result で Post-Return Routing に"
        "進み、先に返ったら timer を TaskStop で止め、返った marker は本文に書く"
        "（references/subagent-dispatch.md § Typed Agent Resolution）。"
    )


def main(project_root: str) -> None:
    try:
        reason = deny_reason(json.loads(sys.stdin.read()))
    except Exception as exc:
        append_hook_error(Path(project_root), "background_dispatch_gate", repr(exc))
        return
    if reason:
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }}, ensure_ascii=False))
