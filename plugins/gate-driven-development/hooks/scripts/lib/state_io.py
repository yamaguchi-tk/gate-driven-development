from __future__ import annotations

import re
from pathlib import Path

from lib.regular_file import read_regular_text


def parse_state(path: Path) -> tuple[dict[str, str], str]:
    # FIFO で止まらないよう通常のファイルだけを読む。無いもの・読めないものは例外にし、
    # 呼び出し元（stop hook の `_load_active_state`）が記録して停止を通す
    text = read_regular_text(path)
    if text is None:
        raise FileNotFoundError(path)
    lines = text.split("\n")
    if not lines or lines[0] != "---":
        raise ValueError("state file missing frontmatter start")
    # 独立レビュー round 9 High/blocking 指摘（H-1）: 従来 `text.split("---\n", 2)`
    # は部分文字列一致のため、frontmatter の値がたまたま `"---"` になる行
    # （例: `detected_phase: ---`）を終端行と誤認し、それより後ろの key
    # （`recommended_model`・`hitl_lint_blocks` 等）が丸ごと消えて body へ
    # 漏れていた（round 7 H-1 と同じ入口）。終端は「内容が厳密に `---` である
    # 行」でのみ判定する。
    try:
        end_index = lines.index("---", 1)
    except ValueError:
        raise ValueError("state file missing frontmatter end") from None
    body = "\n".join(lines[end_index + 1 :]).lstrip("\n")
    return dict(_frontmatter_items(lines[1:end_index])), body


def _frontmatter_items(lines: list[str]) -> list[tuple[str, str]]:
    # frontmatter の (key, value) を行の順に返す。同じ key が 2 行あれば 2 つとも返す
    # （parse_state は後勝ちで dict にし、marker_state は数えて止める）
    items: list[tuple[str, str]] = []
    for raw_line in lines:
        line = raw_line.strip()
        if not line or ":" not in line:
            continue
        key, value = line.split(":", 1)
        items.append((key.strip(), value.strip()))
    return items


_SESSION_ID = re.compile(r"[A-Za-z0-9._:-]+")


def marker_state(path: Path, current_session: str) -> int:
    """block gate が読む marker の状態。0 = この session の active、1 = 無い、2 = 判定できない。

    Stop hook と同じ parse_state の読み方で読み、active・session_id が 2 行以上あれば
    どちらの値を使うかが読み手で割れるので 2 にする。読めないもの・例外も 2 にする。
    """
    try:
        text = read_regular_text(path)
        if text is None:
            return 2
        lines = text.split("\n")
        if lines[0] != "---" or "---" not in lines[1:]:
            return 2
        items = _frontmatter_items(lines[1 : lines.index("---", 1)])
    except Exception:  # noqa: BLE001 - 判定できないときは止める側に倒す
        return 2
    actives = [v for k, v in items if k == "active"]
    sessions = [v for k, v in items if k == "session_id"]
    if len(actives) != 1 or len(sessions) > 1:
        return 2
    active = actives[0].lower()
    if active == "false":
        return 1
    if active != "true":
        return 2
    if not current_session:
        return 0
    stored = sessions[0] if sessions else ""
    if not stored:
        return 1
    if not _SESSION_ID.fullmatch(stored):
        return 2
    return 0 if stored == current_session else 1


def _sanitize_frontmatter_value(value: str) -> str:
    # 独立レビュー round 7 High/blocking 指摘（H-1）: 値に改行が混ざっていると
    # `f"{key}: {value}"` がそのまま複数の frontmatter 行になり、再パース時に
    # 後勝ちで既存 key（`active` 等）を上書きできた（guard bypass / fail-open）。
    # frontmatter へ書く全ての値でここ 1 箇所に集約して無害化する。独立レビュー
    # round 8 指摘（L-1）: `value.replace("\n", ...)` は `\n` しか潰さず、
    # `\r`/U+2028 等でも行が割れうるため `str.splitlines()` を使う（この関数は
    # 本ファイル内の行区切り集合とだけ対称であればよく、`lib/handoff_summary.py`
    # は別の信頼境界・別のパーサを持つため対称を主張しない。round 9 L-3 指摘）。
    return " | ".join(str(value).splitlines())


def write_state(path: Path, frontmatter: dict[str, str], body: str) -> None:
    lines = ["---"]
    for key in ["active", "iteration", "session_id", "started_at"]:
        if key in frontmatter:
            lines.append(f"{key}: {_sanitize_frontmatter_value(frontmatter[key])}")
    for key, value in frontmatter.items():
        if key not in {"active", "iteration", "session_id", "started_at"}:
            lines.append(f"{key}: {_sanitize_frontmatter_value(value)}")
    lines.append("---")
    lines.append("")
    lines.append(body.rstrip("\n"))
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")
