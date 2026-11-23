"""hook が読む状態ファイルを、通常のファイルのときだけ読む。

`Path.is_file()` で確かめてから `read_text()` で読むと、FIFO・ディレクトリ・symlink の
ループ・指す先の無い symlink を「無い」と取り違え（guard が素通りする）、FIFO では
書き手が来るまで open が戻らない（hook が timeout まで止まる）。「無い」とするのは、
パスにも symlink にも何も無いときだけにする。
"""
from __future__ import annotations

import os
import stat
from pathlib import Path


def lstat_or_none(path: Path) -> os.stat_result | None:
    """`os.lstat(path)`。パスに何も無いとき（ENOENT・ENOTDIR）だけ None、ほかの OSError は送出する。

    `os.path.lexists`・`Path.is_dir()` は権限の無さ（EACCES）も「無い」にするので使わない。
    """
    try:
        return os.lstat(path)
    except (FileNotFoundError, NotADirectoryError):
        return None


def read_regular_bytes(path: Path) -> bytes | None:
    """`path` の中身。無ければ None、通常のファイルでない・読めないなら OSError を送出する。

    「無い」と扱うのは、パスの途中か末尾が存在しない（ENOENT・ENOTDIR）ときだけである。
    FIFO で止まらないよう、非ブロッキングで開いてから種類を確かめる。
    """
    try:
        fd = os.open(path, os.O_RDONLY | getattr(os, "O_NONBLOCK", 0))  # Windows には無い
    except (FileNotFoundError, NotADirectoryError):
        if os.path.lexists(path):  # 指す先の無い symlink
            raise
        return None
    with os.fdopen(fd, "rb") as f:
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            raise OSError(f"not a regular file: {path}")
        return f.read()


def read_regular_text(path: Path, errors: str = "strict") -> str | None:
    """`read_regular_bytes` を UTF-8 で decode し、改行を `Path.read_text()` と同じく `\n` にそろえる。"""
    data = read_regular_bytes(path)
    if data is None:
        return None
    return data.decode("utf-8", errors=errors).replace("\r\n", "\n").replace("\r", "\n")
