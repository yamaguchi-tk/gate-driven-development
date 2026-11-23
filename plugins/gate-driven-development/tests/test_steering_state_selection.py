"""bind が無いとき、最新の steering の state.md が通常のファイルでなくても古い steering へ飛ばないこと。

resume-from（`_bound_steering_file`）とポーリング上限（`escalate_polling_reason`）は、
同じ `_steering_candidate` で `.steering/` の名前の降順に最初の state.md を選ぶ。最新が FIFO・
ディレクトリ・symlink のループ・指す先の無い symlink だと `is_file()` で飛ばして古いタスクの
state.md を読み、古いタスクの `human-check-waiting` で停止を許したり、古いタスクの回数で上限を
判定したりしていた。最新の steering のディレクトリ自体が使えない（steering の外を指す symlink
など）ときも、古い steering へ飛ばさない。

FIFO は、読み込みが戻らないとテストごと止まるので、別プロセスで timeout 付きで判定する。
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
from _plugin_module_loader import load_plugin_module  # noqa: E402

from lib.pr_review_followup_polling import escalate_polling_reason  # noqa: E402
from _stop_hook_test_base import _write_binding  # noqa: E402

KINDS = ("fifo", "directory", "loop", "dangling")
PLUGIN_ROOT = Path(__file__).resolve().parents[1]
_POLL_CODE = (
    "import sys; from pathlib import Path\n"
    "sys.path.insert(0, 'tests')\n"
    "from _plugin_module_loader import load_plugin_module\n"
    "from lib.pr_review_followup_polling import escalate_polling_reason\n"
    "m = load_plugin_module('hooks/scripts/gdd_stop_hook.py')\n"
    "root = Path(sys.argv[1])\n"
    "print(escalate_polling_reason(sys.argv[2], lambda: m._steering_candidate(root, 'state.md'), root))"
)


def _poll(root: Path, reason: str = "external-review-waiting") -> str:
    """stop hook と同じ選び方で state.md を選び、ポーリング上限の判定を別プロセスで返す。"""
    result = subprocess.run(
        [sys.executable, "-c", _POLL_CODE, str(root), reason],
        capture_output=True,
        text=True,
        timeout=20,
        cwd=str(PLUGIN_ROOT),
        env={**os.environ, "PYTHONPATH": str(PLUGIN_ROOT / "hooks" / "scripts")},
    )
    return result.stdout.strip() or result.stderr


def _make_steerings(root: Path, newest_kind: str, old_state: str) -> None:
    old = root / ".steering" / "20260101-old"
    new = root / ".steering" / "20260201-new"
    old.mkdir(parents=True)
    new.mkdir(parents=True)
    (old / "state.md").write_text(old_state, encoding="utf-8")
    state = new / "state.md"
    if newest_kind == "fifo":
        os.mkfifo(state)
    elif newest_kind == "directory":
        state.mkdir()
    elif newest_kind == "loop":
        os.symlink("state.md", state)
    elif newest_kind == "dangling":
        os.symlink("missing-target", state)
    else:
        state.write_text(newest_kind, encoding="utf-8")


class BoundSteeringFileTests(unittest.TestCase):
    def test_non_regular_newest_state_does_not_fall_back_to_older(self) -> None:
        module = load_plugin_module("hooks/scripts/gdd_stop_hook.py")
        for kind in KINDS:
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                _make_steerings(root, kind, "- Resume From: human-check-waiting\n")
                module._BIND_CACHE.clear()
                try:
                    self.assertIsNone(module._bound_steering_file(root, "state.md"))
                finally:
                    module._BIND_CACHE.clear()

    def test_unusable_newest_steering_dir_does_not_fall_back_to_older(self) -> None:
        """最新の steering 自体が steering の外を指す symlink・ループなら、古い steering へ飛ばさない。"""
        module = load_plugin_module("hooks/scripts/gdd_stop_hook.py")
        for kind in ("outside", "loop"):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                old = root / ".steering" / "20260101-old"
                old.mkdir(parents=True)
                (old / "state.md").write_text("- Resume From: human-check-waiting\n", encoding="utf-8")
                newest = root / ".steering" / "20260201-new"
                if kind == "outside":
                    outside = root / "outside"
                    outside.mkdir()
                    (outside / "state.md").write_text("- Resume From: done\n", encoding="utf-8")
                    os.symlink(outside, newest)
                else:
                    os.symlink(newest.name, newest)
                module._BIND_CACHE.clear()
                try:
                    self.assertIsNone(module._bound_steering_file(root, "state.md"))
                    self.assertEqual(_poll(root), "blocked")
                finally:
                    module._BIND_CACHE.clear()

    def test_plain_files_under_steering_are_skipped(self) -> None:
        module = load_plugin_module("hooks/scripts/gdd_stop_hook.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            old = root / ".steering" / "20260101-old"
            old.mkdir(parents=True)
            (old / "state.md").write_text("- Resume From: done\n", encoding="utf-8")
            (root / ".steering" / "README.md").write_text("x", encoding="utf-8")
            module._BIND_CACHE.clear()
            try:
                self.assertEqual(module._bound_steering_file(root, "state.md"), old / "state.md")
            finally:
                module._BIND_CACHE.clear()

    def test_missing_newest_state_falls_back_to_older(self) -> None:
        module = load_plugin_module("hooks/scripts/gdd_stop_hook.py")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".steering" / "20260201-new").mkdir(parents=True)
            (root / ".steering" / "20260101-old").mkdir(parents=True)
            old_state = root / ".steering" / "20260101-old" / "state.md"
            old_state.write_text("- Resume From: done\n", encoding="utf-8")
            module._BIND_CACHE.clear()
            try:
                self.assertEqual(module._bound_steering_file(root, "state.md"), old_state)
            finally:
                module._BIND_CACHE.clear()


class EscalatePollingReasonTests(unittest.TestCase):
    def test_non_regular_newest_state_is_blocked_and_recorded(self) -> None:
        for kind in KINDS:
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                _make_steerings(root, kind, "- PR Review Follow-up Attempts: 0\n")
                self.assertEqual(_poll(root), "blocked")
                log = root / ".gdd" / "hook-errors.log"
                self.assertIn("pr_review_poll_cap", log.read_text(encoding="utf-8"))

    def test_regular_newest_state_is_judged_by_its_attempts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _make_steerings(root, "- PR Review Follow-up Attempts: 1\n", "- PR Review Follow-up Attempts: 99\n")
            self.assertEqual(_poll(root), "external-review-waiting")
            self.assertEqual(_poll(root, "blocked"), "blocked")
            self.assertEqual(_poll(root, "done"), "done")

    def test_no_state_keeps_the_reason(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(_poll(Path(tmp)), "external-review-waiting")
            self.assertEqual(
                escalate_polling_reason("external-review-waiting", lambda: None, Path(tmp)), "external-review-waiting"
            )


@unittest.skipIf(os.geteuid() == 0, "root は権限を落としても読めてしまう")
class UnstatableSteeringTests(unittest.TestCase):
    """権限で stat できない steering を「無い」と読まない。

    `os.path.lexists`・`Path.is_dir()` は EACCES も False にするので、最新の task dir に x が無いと
    「state.md が無い」と読んで古い steering へ飛んでいた。「無い」とするのは ENOENT・ENOTDIR だけにする。
    """

    def _assert_not_fall_back(self, root: Path) -> None:
        module = load_plugin_module("hooks/scripts/gdd_stop_hook.py")
        module._BIND_CACHE.clear()
        try:
            self.assertIsNone(module._bound_steering_file(root, "state.md"))
        finally:
            module._BIND_CACHE.clear()
        self.assertEqual(_poll(root), "blocked")

    def test_newest_task_dir_without_x_does_not_fall_back(self) -> None:
        for mode in (0o000, 0o600):
            with self.subTest(mode=oct(mode)), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                _make_steerings(root, "- PR Review Follow-up Attempts: 0\n", "- Resume From: human-check-waiting\n")
                newest = root / ".steering" / "20260201-new"
                newest.chmod(mode)
                try:
                    self._assert_not_fall_back(root)
                finally:
                    newest.chmod(0o755)

    def test_steering_root_without_x_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _make_steerings(root, "- PR Review Follow-up Attempts: 0\n", "- Resume From: human-check-waiting\n")
            steering = root / ".steering"
            steering.chmod(0o600)
            try:
                self._assert_not_fall_back(root)
            finally:
                steering.chmod(0o755)

    def test_bound_task_dir_without_x_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            _make_steerings(root, "- PR Review Follow-up Attempts: 0\n", "- PR Review Follow-up Attempts: 0\n")
            _write_binding(root, "20260101-old")
            bound = root / ".steering" / "20260101-old"
            bound.chmod(0o000)
            try:
                self._assert_not_fall_back(root)
            finally:
                bound.chmod(0o755)


if __name__ == "__main__":
    unittest.main()
