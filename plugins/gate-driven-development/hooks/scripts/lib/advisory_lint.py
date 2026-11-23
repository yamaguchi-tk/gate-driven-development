"""steering write hook の advisory lint を 1 本ずつ実行し、allow の応答を組み立てる（validate-steering-write.py から分離）。

advisory なので、lint script の不在・timeout・実行失敗は無言で通す（deny に昇格させない）。
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def run_lint_script(script_path: Path, args: list[str], timeout: float = 2.0) -> tuple[int, str]:
    """lint script を実行する。失敗時は silent（plugin を壊さない）。

    Returns: (exit_code, combined_output). exit_code は subprocess の返却値、
    output は stdout+stderr の concat。script が無い / 実行できない場合は (0, "")。
    """
    if not script_path.is_file():
        return 0, ""
    try:
        cmd = [sys.executable if script_path.suffix == ".py" else "bash", str(script_path)] + args
        # script に shebang があるなら直接実行できる
        if os.access(script_path, os.X_OK):
            cmd = [str(script_path)] + args
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        output = "\n".join(filter(None, [result.stdout.strip(), result.stderr.strip()]))
        return result.returncode, output
    except (subprocess.TimeoutExpired, OSError, ValueError):
        return 0, ""


def lint_warning(
    script: Path, args: list[str], prefix: str, extra_markers: tuple[str, ...]
) -> str | None:
    """lint script を 1 本走らせ、warning として出すべき出力があれば整形して返す。

    非 0 終了は出力があるときだけ warning にする（advisory なので無言の失敗を deny に昇格させない）。
    正常終了でも `extra_markers` を含む出力は warning にする。
    """
    code, out = run_lint_script(script, args)
    if code != 0 and out:
        return f"{prefix}\n{out}"
    if code == 0 and any(marker in out for marker in extra_markers):
        return f"{prefix}\n{out}"
    return None


def allow_response(base: dict, advisory: list[str], notice: str, context: list[str]) -> dict:
    """allow の応答を作る。advisory と notice は systemMessage（利用者の端末だけ）、context は main に届く additionalContext。"""
    response = dict(base)
    message = "\n\n".join(filter(None, ["[GDD advisory lint]\n" + "\n".join(advisory) if advisory else "", notice]))
    if message or context:
        response.pop("suppressOutput", None)
    if message:
        response["systemMessage"] = message
    if context:
        response["hookSpecificOutput"] = {"hookEventName": "PreToolUse", "additionalContext": "\n".join(context)}
    return response
