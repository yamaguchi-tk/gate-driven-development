from __future__ import annotations

import json
import os
import stat
import sys
from datetime import datetime, timezone
from pathlib import Path


def hook_error_log_path(project_root: Path) -> Path:
    return project_root / ".gdd" / "hook-errors.log"


def hitl_lint_log_path(project_root: Path) -> Path:
    return project_root / ".gdd" / "hitl-lint.log"


def append_hook_error(project_root: Path, source: str, message: str) -> None:
    append_log_record(hook_error_log_path(project_root), source, message)


def append_log_record(target: Path, source: str, message: str) -> None:
    """通常のファイルにだけ追記する。FIFO で止まらないよう、非ブロッキングで開いてから種類を確かめる
    （lib/regular_file.py の読む側と同じ形）。読み手のいない FIFO は open が失敗し、読み手のいる FIFO などには書かない。"""
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "hook": "gdd_stop_hook",
            "source": source,
            "message": message,
        }
        flags = os.O_WRONLY | os.O_APPEND | os.O_CREAT | getattr(os, "O_NONBLOCK", 0)  # Windows には無い
        fd = os.open(target, flags, 0o666)  # Path.open("a") と同じ（umask で削る）
        with os.fdopen(fd, "a", encoding="utf-8") as f:
            if stat.S_ISREG(os.fstat(fd).st_mode):
                f.write(json.dumps(payload, ensure_ascii=False) + "\n")
    except Exception:
        pass


def block_hook_integrity_failure(project_root: Path, source: str, message: str) -> None:
    append_hook_error(project_root, source, message)
    payload = {
        "decision": "block",
        "reason": "GDD Stop hook integrity failure",
        "systemMessage": (
            f"[GDD Stop hook 不全] {source}: {message}. "
            "状態を消さずに停止しました。gdd-status の Hook Errors と "
            ".gdd/hook-errors.log を確認してから再開してください。"
        ),
    }
    print(json.dumps(payload, ensure_ascii=False))
    raise SystemExit(0)


def suppress_hook_integrity_failure(
    project_root: Path,
    source: str,
    message: str,
    *,
    quiet: bool = False,
) -> None:
    """Log non-actionable hook integrity problems without injecting a block.

    Missing transcript information usually means the host did not provide enough
    context to prove the current turn is an active GDD continuation. Blocking in
    that state creates a repeating "Stop hook integrity failure" loop from stale
    local state. Preserve state for explicit resume, but do not hijack the chat.
    """
    if quiet:
        raise SystemExit(0)
    append_hook_error(project_root, source, message)
    print(
        f"GDD Stop hook: {source}: {message}. "
        "自動継続を抑止しました。state.md は保持しています — "
        "再開するには `/gdd-dev` を明示してください。",
        file=sys.stderr,
    )
    raise SystemExit(0)
