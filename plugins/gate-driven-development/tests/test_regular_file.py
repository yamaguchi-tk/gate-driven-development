"""`lib.regular_file.read_regular_bytes` が、通常のファイルだけを読み、無いものと読めないものを分けること。

FIFO は別プロセスで呼び、timeout で止まらないことを確かめる（同じプロセスで open が止まると、
テストごと戻らない）。
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import _stop_hook_test_base  # noqa: E402,F401  hooks/scripts を sys.path に入れる
from _timing_budget import hang_guard_seconds  # noqa: E402

from lib.regular_file import read_regular_bytes, read_regular_text  # noqa: E402

LIB_DIR = Path(__file__).resolve().parents[1] / "hooks" / "scripts"


def run_in_subprocess(code: str, path: Path) -> str:
    """`code` を別プロセスで走らせ、stdout を返す。`path` は argv[1] で渡す。"""
    result = subprocess.run(
        [sys.executable, "-c", code, str(path)],
        capture_output=True,
        text=True,
        timeout=hang_guard_seconds("run-gdd-stop-hook.sh"),
        cwd=str(LIB_DIR),
    )
    return result.stdout.strip()


class ReadRegularBytesTests(unittest.TestCase):
    def test_regular_file_is_read(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "a.md"
            path.write_bytes(b"x\xff\n")
            self.assertEqual(read_regular_bytes(path), b"x\xff\n")

    def test_missing_path_is_none(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "file").write_text("", encoding="utf-8")
            self.assertIsNone(read_regular_bytes(Path(tmp) / "a.md"))
            self.assertIsNone(read_regular_bytes(Path(tmp) / "dir" / "a.md"))
            self.assertIsNone(read_regular_bytes(Path(tmp) / "file" / "a.md"))

    def test_dangling_symlink_raises(self) -> None:
        """在るのに辿れない symlink は「無い」ではない（shell 側の gdd_path_kind と同じ）。"""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "a.md"
            os.symlink("missing-target", path)
            with self.assertRaises(OSError):
                read_regular_bytes(path)

    def test_reads_without_o_nonblock(self) -> None:
        """`os.O_NONBLOCK` の無い環境（Windows）でも通常のファイルを読める。"""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "a.md"
            path.write_bytes(b"x")
            saved = os.O_NONBLOCK
            del os.O_NONBLOCK
            try:
                self.assertEqual(read_regular_bytes(path), b"x")
            finally:
                os.O_NONBLOCK = saved

    def test_non_regular_paths_raise(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            loop = Path(tmp) / "loop.md"
            os.symlink("loop.md", loop)
            for path in (Path(tmp), loop, Path(os.devnull)):
                with self.subTest(path=path), self.assertRaises(OSError):
                    read_regular_bytes(path)

    def test_fifo_raises_without_blocking(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fifo = Path(tmp) / "a.md"
            os.mkfifo(fifo)
            out = run_in_subprocess(
                "import sys; from pathlib import Path; from lib.regular_file import read_regular_bytes\n"
                "try:\n    read_regular_bytes(Path(sys.argv[1]))\nexcept OSError:\n    print('raised')",
                fifo,
            )
            self.assertEqual(out, "raised")


class ReadRegularTextTests(unittest.TestCase):
    def test_newlines_are_normalized_like_read_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "a.md"
            path.write_bytes(b"---\r\na: 1\rb\n")
            self.assertEqual(read_regular_text(path), "---\na: 1\nb\n")
            self.assertEqual(read_regular_text(path), path.read_text(encoding="utf-8"))

    def test_missing_is_none_and_non_regular_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIsNone(read_regular_text(Path(tmp) / "a.md"))
            with self.assertRaises(OSError):
                read_regular_text(Path(tmp))

    def test_invalid_utf8_raises_unless_replaced(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "a.md"
            path.write_bytes(b"x\xff")
            with self.assertRaises(UnicodeDecodeError):
                read_regular_text(path)
            self.assertEqual(read_regular_text(path, errors="replace"), "x\ufffd")


if __name__ == "__main__":
    unittest.main()
