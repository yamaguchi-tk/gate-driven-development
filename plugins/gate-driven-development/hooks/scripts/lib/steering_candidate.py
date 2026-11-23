"""stop hook が読む steering の状態ファイルを選ぶ（bind 済み steering、または bind が無いときの最新の steering）。

**他 worktree は列挙しない**。使えるのは、steering 配下の通常のファイルのときだけ（containment。
広域スイープの Medium 3。`Path.is_dir()` は symlink を辿る）。最新の steering のディレクトリが
使えない（steering の外を指す symlink・ループ・権限で stat できない）か、在るのに使えない
ファイルを持つときは、古い steering へ飛ばさず「使えない」で返す。古いタスクの
`human-check-waiting` や回数で停止を判定してしまうため。「無い」とするのは ENOENT・ENOTDIR だけ。
is_file() を先に見るのは、3.12 以前の contained_file がループで RuntimeError を投げるため。
"""
from __future__ import annotations

import stat
from pathlib import Path

from lib.regular_file import lstat_or_none
from lib.task_binding_resolve import contained_file, contained_steering_dir


def usable_candidate(candidate: Path, base: Path) -> tuple[Path, bool] | None:
    """`candidate` が無ければ None。在れば、`base` 配下の通常のファイルか。stat できなければ使えない。"""
    try:
        if lstat_or_none(candidate) is None:
            return None
    except OSError:
        return candidate, False
    return candidate, candidate.is_file() and contained_file(candidate, base)


def latest_steering_candidate(steering_root: Path, filename: str) -> tuple[Path, bool] | None:
    """`.steering` を名前の降順で見て、最初に在る steering の `filename` と、それが使えるか。"""
    if lstat_or_none(steering_root) is None or not steering_root.is_dir():
        return None
    for steering in sorted(steering_root.iterdir(), reverse=True):
        candidate = steering / filename
        try:
            entry = lstat_or_none(steering)
        except OSError:  # 権限で stat できない entry は「無い」ではない
            return candidate, False
        if entry is None or not (stat.S_ISLNK(entry.st_mode) or stat.S_ISDIR(entry.st_mode)):
            continue  # README などのファイル
        if not contained_steering_dir(steering, steering_root):
            return candidate, False
        found = usable_candidate(candidate, steering_root)
        if found is not None:
            return found
    return None
