"""`collect-gdd-telemetry.py --include-worktrees` が、消えた worktree で落ちないことを固定する。

`git worktree list` は、ディレクトリを消した worktree の行も出す（`git worktree prune` まで）。
この行は飛ばして集計を続け、`--root` で明示した場所が無いときだけ終了 1 にする。
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _git_fixture import init_repo  # noqa: E402
from _plugin_module_loader import PLUGIN_ROOT  # noqa: E402

_TELEMETRY_SCRIPT = PLUGIN_ROOT / "scripts" / "collect-gdd-telemetry.py"


def _git(cwd: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=cwd, check=True, capture_output=True, text=True, timeout=120
    ).stdout


def _add_steering(root: Path, task: str) -> None:
    steering = root / ".steering" / task
    steering.mkdir(parents=True)
    (steering / "state.md").write_text("- Next Action: done\n", encoding="utf-8")


class MissingWorktreeTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        base = Path(self._tmp.name).resolve()
        self.repo = base / "repo"
        self.repo.mkdir()
        init_repo(self.repo)
        _add_steering(self.repo, "20261028-main")
        # 消えた worktree を、残っている worktree より先に一覧に出す
        self.gone = base / "a-gone"
        self.live = base / "b-live"
        _git(self.repo, "worktree", "add", "-q", "--detach", str(self.gone))
        _git(self.repo, "worktree", "add", "-q", "--detach", str(self.live))
        _add_steering(self.live, "20261028-live")
        shutil.rmtree(self.gone)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _run(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(_TELEMETRY_SCRIPT), *args],
            cwd=self.repo, capture_output=True, text=True, timeout=120,
        )

    def test_missing_listed_worktree_is_skipped(self) -> None:
        listed = [
            Path(line[len("worktree "):]).resolve()
            for line in _git(self.repo, "worktree", "list", "--porcelain").splitlines()
            if line.startswith("worktree ")
        ]
        self.assertLess(listed.index(self.gone), listed.index(self.live))

        proc = self._run("--include-worktrees", "--format=json")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        tasks = json.loads(proc.stdout)["tasks"]
        self.assertEqual(
            sorted(t["steering_id"] for t in tasks), ["20261028-live", "20261028-main"]
        )
        self.assertEqual(
            proc.stderr.splitlines(), [f"WARNING: skipped missing worktree: {self.gone}"]
        )

    def test_missing_explicit_root_still_fails(self) -> None:
        proc = self._run("--root", str(self.gone), "--format=json")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("root not found", proc.stderr)


if __name__ == "__main__":
    unittest.main()
