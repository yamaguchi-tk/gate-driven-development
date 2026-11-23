"""SessionStart は、現 worktree の外にある steering を案内しない契約テスト。

以前は、現 worktree に有効な steering が無いとき、同じ repo の別の worktree や
worktree の置き場（`~/.gdd/worktrees/<repo>`・`<current>/.worktrees`・設定済みの Worktree Base）を
走査し、非終端の steering があれば `[gdd:shadow-marker]` で `gdd-status` / `/gdd-dev resume` を案内していた。
2026-09-17〜09-21 の記録では何度も注入されたのに、その後に gdd-status・resume が起動されたことは無く、
指す先は放棄された古い steering だけだった。走査は worktree の多い repo で SessionStart の timeout（5 秒）の
かなりの部分を使い、打ち切りを起こしていたため撤去した。

ここでは、別の置き場に非終端の steering があっても、通常の案内（active steering なし）だけが出ることを固定する。
"""

from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

import test_session_start_no_post_merge_seed as _post_merge_seed

NON_TERMINAL = "Resume From: human-check-waiting\nHuman Check Status: pending\nRoute In Progress: none\n"


def _git(cwd: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)


def _state(steering_dir: Path) -> Path:
    steering_dir.mkdir(parents=True, exist_ok=True)
    (steering_dir / "state.md").write_text(NON_TERMINAL, encoding="utf-8")
    return steering_dir


class NoShadowMarkerTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="gdd-no-shadow-")
        self.addCleanup(self._tmp.cleanup)
        tmp = Path(os.path.realpath(self._tmp.name))
        self.home = tmp / "home"
        self.home.mkdir()
        self.repo = tmp / "repo"
        self.repo.mkdir()
        _git(self.repo, "init", "-q")
        _git(self.repo, "-c", "user.email=t@example.com", "-c", "user.name=t",
             "commit", "--allow-empty", "-q", "-m", "init")
        # 実運用と同じく origin を持たせる（repo 名で置き場を引いていた経路も踏む）
        _git(self.repo, "remote", "add", "origin", "https://example.com/owner/repo.git")
        self.other = self.repo.parent / "other-wt"
        _git(self.repo, "worktree", "add", "-q", "-b", "other", str(self.other))
        self.custom = tmp / "custom-base"

    _run = _post_merge_seed.NoPostMergeSeedTests._run

    def _assert_no_shadow(self, additional: str, steering: Path) -> None:
        self.assertNotIn("[gdd:shadow-marker]", additional)
        self.assertNotIn("shadow", additional.lower())
        self.assertNotIn(str(steering), additional)
        self.assertNotIn("/gdd-dev resume", additional)
        self.assertIn("gate-driven-development is available.", additional)

    def test_other_git_worktree_steering_is_not_announced(self) -> None:
        steering = _state(self.other / ".steering" / "20260916-other-task")

        self._assert_no_shadow(self._run(), steering)

    def test_default_worktree_base_steering_is_not_announced(self) -> None:
        steering = _state(self.home / ".gdd" / "worktrees" / "repo" / "20260916-gdd-task"
                          / ".steering" / "20260916-gdd-task")

        self._assert_no_shadow(self._run(), steering)

    def test_repo_local_worktrees_steering_is_not_announced(self) -> None:
        steering = _state(self.repo / ".worktrees" / "20260915-local-task"
                          / ".steering" / "20260915-local-task")

        self._assert_no_shadow(self._run(), steering)

    def test_configured_worktree_base_steering_is_not_announced(self) -> None:
        (self.repo / ".gdd-config.md").write_text(f"Worktree Base: {self.custom}\n", encoding="utf-8")
        steering = _state(self.custom / "repo" / "20260917-custom-task" / ".steering" / "20260917-custom-task")

        self._assert_no_shadow(self._run(), steering)

    def test_env_worktrees_root_steering_is_not_announced(self) -> None:
        steering = _state(self.custom / "repo" / "20260917-env-task" / ".steering" / "20260917-env-task")

        self._assert_no_shadow(self._run(extra_env={"GDD_WORKTREES_ROOT": str(self.custom)}), steering)

    def test_superpowers_session_gets_normal_routing_reason(self) -> None:
        settings_dir = self.home / ".claude"
        settings_dir.mkdir()
        (settings_dir / "settings.json").write_text('{"enabledPlugins":["superpowers"]}', encoding="utf-8")
        steering = _state(self.home / ".gdd" / "worktrees" / "repo" / "20260607-shadow-task"
                          / ".steering" / "20260607-shadow-task")

        additional = self._run()

        self.assertNotIn("[gdd:shadow-marker]", additional)
        self.assertNotIn(str(steering), additional)
        self.assertIn("Routing reason: no active GDD marker detected", additional)
        self.assertIn("superpowers advisory only", additional)


if __name__ == "__main__":
    unittest.main()
