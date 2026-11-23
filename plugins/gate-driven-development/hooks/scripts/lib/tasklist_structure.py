"""done guard の Check 1 の前段の組み立て（行区切り文字・fence の閉じ忘れと、構造行の取り出し）。

`gdd_stop_hook.py` の `validate_done_preconditions` から切り出した。done guard と
completion-check の機械検査（`scripts/check-completion-mechanical.py`）が同じ組み立てを
呼ぶためで、挙動は変えていない。`done_guard.py` に置かないのは、同ファイルが Codebase Health の
複雑度の上限を既に超えていて、触ると `--mode changed` の High になるため。
"""
from __future__ import annotations

from lib.done_guard import _line_break_char_error
from lib.tasklist_parse import strip_fenced_lines_marked


def tasklist_structure(
    tasklist_text: str,
) -> tuple[list[str], list[str], list[list[int]], list[int]]:
    """Check 1 の前段（行区切り文字・fence の閉じ忘れ）と構造行。残りのタスクは呼び出し側が
    `structural_lines` に `_scan_remaining_tasks` を当てて数える（block 理由の文は hook 本体に置く）。

    `(errors, structural_lines, fence_before, fenced_heading_lines)` を返す。後ろの 3 つは
    Check 2（`_scan_verification`）に同じ構造行を渡すため。done guard（`gdd_stop_hook.py`）と
    completion-check の機械検査（`scripts/check-completion-mechanical.py`）が共有する。
    """
    errors: list[str] = []
    # LF / CR 以外の行区切り文字は splitlines() で行を分け、節や検証行の境界を崩す（R23 #1）
    line_break_error = _line_break_char_error(tasklist_text, "tasklist.md")
    if line_break_error:
        errors.append(line_break_error)
    structural_lines, fence_unclosed, fence_before, fenced_heading_lines = strip_fenced_lines_marked(
        tasklist_text
    )
    if fence_unclosed:
        # **fail-closed**。閉じ忘れを黙って読み飛ばすと、そこから先の実タスクが
        # 1 件も数えられず done が通る（= guard が無言で無効化される）。
        errors.append(
            "tasklist.md の code fence が閉じていません（``` / ~~~ の対応が取れていない）。"
            "この状態では未完了タスクを正しく数えられないため done を許可しません。"
        )
    return errors, structural_lines, fence_before, fenced_heading_lines
