"""hook の記録（lib/errors.py の append_log_record）は、通常のファイルにだけ追記し、FIFO などで止まらない。"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import threading
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "hooks" / "scripts"))

from lib.errors import append_log_record  # noqa: E402


def _call_with_limit(target: Path, seconds: float = 5.0) -> bool:
    """append_log_record を thread で呼び、seconds 以内に戻ったか。"""
    worker = threading.Thread(target=append_log_record, args=(target, "test", "message"), daemon=True)
    worker.start()
    worker.join(seconds)
    return not worker.is_alive()


class AppendLogRecordTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_regular_file_is_appended(self) -> None:
        target = self.root / ".gdd" / "hook-errors.log"
        self.assertTrue(_call_with_limit(target))
        self.assertTrue(_call_with_limit(target))
        records = [json.loads(line) for line in target.read_text(encoding="utf-8").splitlines()]
        self.assertEqual([r["message"] for r in records], ["message", "message"])

    def test_fifo_without_reader_returns_without_writing(self) -> None:
        target = self.root / "hook-errors.log"
        os.mkfifo(target)
        self.assertTrue(_call_with_limit(target), "FIFO の open で止まった")

    def test_fifo_with_reader_is_not_written(self) -> None:
        target = self.root / "hook-errors.log"
        os.mkfifo(target)
        fd = os.open(target, os.O_RDONLY | os.O_NONBLOCK)
        try:
            self.assertTrue(_call_with_limit(target))
            try:
                data = os.read(fd, 4096)
            except BlockingIOError:
                data = b""
            self.assertEqual(data, b"")
        finally:
            os.close(fd)


if __name__ == "__main__":
    unittest.main()
