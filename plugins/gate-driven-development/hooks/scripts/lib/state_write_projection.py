"""steering の書き込み hook（`validate-steering-write.py`）が、書き込み後の state.md の全文を作る関数。"""
from __future__ import annotations

from pathlib import Path

from steering_paths import normalize_path

_EDIT_PAIR_KEYS = (("old_string", "new_string"), ("oldText", "newText"))


def project_edited_text(tool_input: object, path: str) -> str | None:
    """`Edit` / `MultiEdit` の `old_string` -> `new_string` を既存内容へ仮想適用した結果（できなければ `None`）。

    値だけを置換する Edit は chunk に field 名が現れないので、書き込み後の値で判定する検査（peer turn・`Origin Session`・
    `risk_tier` の `risk-low`）が使う。読めないファイルも `None`（どの検査も、先に `edit_misses_old_string` で止める）。
    """
    edits = _edit_triples(tool_input)
    if not edits:
        return None
    try:
        text = Path(path).read_text(encoding="utf-8", errors="replace")
    except (OSError, ValueError):
        return None
    for old, new, replace_all in edits:
        text = text.replace(old, new) if replace_all else text.replace(old, new, 1)
    return text


def _edit_triples(tool_input: object) -> list[tuple[str, str, bool]]:
    """Edit / MultiEdit の `(old, new, replace_all)` を適用順に返す。"""
    if not isinstance(tool_input, dict):
        return []
    edits: list[tuple[str, str, bool]] = []

    def _collect(source: dict) -> None:
        for old_key, new_key in _EDIT_PAIR_KEYS:
            old = source.get(old_key)
            new = source.get(new_key)
            if isinstance(old, str) and isinstance(new, str) and old:
                edits.append((old, new, bool(source.get("replace_all"))))

    _collect(tool_input)
    raw_edits = tool_input.get("edits")
    if isinstance(raw_edits, dict):
        # `extract_content_chunks` と受理集合を揃える（dict の `edits` を 1 件の edit とみなす）。
        raw_edits = [raw_edits]
    if isinstance(raw_edits, list):
        for edit in raw_edits:
            if isinstance(edit, dict):
                _collect(edit)
    return edits


def edit_misses_old_string(tool_name: str, tool_input: object, path: str) -> bool:
    """Edit / MultiEdit の書き込み後のテキストを、素の置換（`project_edited_text`）で射影できないか。

    次のどちらかに当たる edit があれば `True`（呼び出し側が止める）。

    - `old_string` が、書き込み前のテキストに適用順で見つからない。射影では空振りして「変化なし」に
      見えるが、ツールの照合規則（引用符の正規化など）では当たるかもしれない
    - `new_string` が空で、`old_string` が改行で終わらず、テキストに `old_string` と改行が続く。
      Claude Code の Edit はこのとき改行ごと消す（2026-09-29 に実測。replace_all でも同じ）ので、
      素の置換が残す改行の分だけ、行のつながりが実ファイルと違う

    読めないファイルも `True`。どれにも当たらなければ、素の置換とツールの結果は一致する。
    """
    if tool_name not in ("Edit", "MultiEdit"):
        return False
    edits = _edit_triples(tool_input)
    if not edits:
        return False
    try:
        text = Path(path).read_text(encoding="utf-8", errors="replace")
    except (OSError, ValueError):
        return True
    for old, new, replace_all in edits:
        if old not in text:
            return True
        if new == "" and not old.endswith("\n") and old + "\n" in text:
            return True
        text = text.replace(old, new) if replace_all else text.replace(old, new, 1)
    return False


PROJECTABLE_TOOLS = ("Write", "Edit", "MultiEdit")  # project_written_text が書き込み後の全文を作れる tool


def project_written_text(tool_name: str, tool_input: object, path: str) -> str | None:
    """書込み後のファイル全文を再構成する（できない形なら `None`）。

    `Write` は `content` をそのまま返す（全文 Write で field 行を省く削除を拾う。PR #31 Finding K）。
    `Edit` / `MultiEdit` だけを `project_edited_text()` に委ねる。`ApplyPatch` は全文にならないので `None`
    （Origin Session は `_origin_session_patch_reason()` が値を推定せずに見る）。ApplyPatch の payload に `old_string` を混ぜて
    無害な投影を返させ、patch の削除の検査を飛ばす形を防ぐため、tool_name で絞る（Finding F-3）。
    """
    if tool_name == "Write" and isinstance(tool_input, dict):
        # 対象 path 宛の content かを確かめる。key 集合は `extract_target_paths()` と揃える
        # （`path` 等で対象を示す Cursor / Codex の Write を取りこぼさない。Finding F-7）。
        for key in ("file_path", "path", "target_file", "target_notebook"):
            target = tool_input.get(key)
            if isinstance(target, str) and normalize_path(target) == normalize_path(path):
                break
        else:
            return None
        for key in ("content", "contents"):
            value = tool_input.get(key)
            if isinstance(value, str):
                return value
        return None
    if tool_name not in PROJECTABLE_TOOLS:
        return None
    return project_edited_text(tool_input, path)
