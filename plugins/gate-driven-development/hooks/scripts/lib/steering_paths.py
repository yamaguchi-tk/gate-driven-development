"""steering の書き込み hook（`validate-steering-write.py`）が使う path の判定。"""
from __future__ import annotations


def normalize_path(path: str) -> str:
    return path.replace("\\", "/")


def is_steering_path(path: str) -> bool:
    """`.steering/` 配下の path かを判定する（大文字小文字を無視する）。

    macOS(APFS 既定) / Windows は大文字小文字を区別しないファイルシステムで、
    `.STEERING/x/State.MD` と `.steering/x/state.md` は実ファイルとして同一を
    指す（実測）。大文字小文字を区別したまま比較すると、casing を変えただけの
    path が `steering_targets` から漏れ、この hook の全検査（peer-turn /
    origin-session write-once / secrets / ellipsis）を素通りしたまま実 file
    を書き換えられる（PR #31 独立レビュー Finding F-4）。
    """
    normalized = normalize_path(path).lower()
    return normalized.startswith(".steering/") or "/.steering/" in normalized


def is_state_md_path(path: str) -> bool:
    # 大文字小文字を無視する理由は is_steering_path() と同じ（Finding F-4）。
    normalized = normalize_path(path).lower()
    return normalized.endswith("/state.md") or normalized == "state.md"


def is_tasklist_md_path(path: str) -> bool:
    # 大文字小文字を無視する理由は is_steering_path() と同じ（Finding F-4）。
    normalized = normalize_path(path).lower()
    return normalized.endswith("/tasklist.md") or normalized == "tasklist.md"
