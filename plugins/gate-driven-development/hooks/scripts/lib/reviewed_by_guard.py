"""steering write guard の `completed_reviewed_by` の判定（完了タスクの `Reviewed by` を落とす tasklist.md の書き込み）。

`validate-steering-write.py` の collector が呼ぶ。前と後の比較は `tasklist_parse.reviewed_by_regressions`。
"""
from __future__ import annotations

from pathlib import Path

from tasklist_parse import reviewed_by_regressions

_WHY = {
    "removed": "not found in Completed, Current or Pending Tasks (deleted, renamed, or moved to another section)",
    "missing": "its Reviewed by line is gone",
    "no-implementation-reviewer": "gdd-implementation-reviewer is gone from its Reviewed by line",
}


def edited_text(text: str, edits: list[tuple[str, str, bool]]) -> str | None:
    """Edit / MultiEdit を、Claude Code の Edit の規則で当てた結果。old_string が見つからなければ `None`。

    空の new_string で old_string が改行で終わらないとき、old_string と改行が 1 か所でも続いていれば、
    old_string と改行を置換の対象にする（replace_all なら全部、そうでなければ最初の 1 つ。2026-09-29 実測。
    `edit_misses_old_string` が止める形）。素の置換で投影すると、行を前の行につなげる Edit
    （`- Commit: abc1234` の `abc1234` を消すなど）を見落とす。
    """
    for old, new, replace_all in edits:
        if old not in text:
            return None
        if new == "" and not old.endswith("\n") and old + "\n" in text:
            old += "\n"
        text = text.replace(old, new) if replace_all else text.replace(old, new, 1)
    return text


def lost_reviewed_by(path: Path, tool_name: str, written: str | None, edits: list[tuple[str, str, bool]]) -> list[str]:
    """書き込みで `Reviewed by` が ok でなくなる完了タスクの説明（無ければ空）。

    無いファイルと、全文にならない書き込み（ApplyPatch など。`written` が `None`）は見ない。
    読めないなどの例外はそのまま上げる（呼び出し側が止める側に倒す）。
    """
    if not path.exists():
        return []
    before = path.read_text(encoding="utf-8")
    if tool_name in ("Edit", "MultiEdit"):
        after = edited_text(before, edits)
        if after is None:
            return ["an old_string is not in the file, so the result cannot be checked"]
    elif written is None:
        return []
    else:
        after = written
    return [f"completed task {name!r}: {_WHY.get(why, why)}" for name, why in reviewed_by_regressions(before, after)]
