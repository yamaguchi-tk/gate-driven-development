"""共有 fixture `_git_fixture.init_repo` の契約を固定する。

各テストが書き写していた「git init → user 設定 → README.md の 1 commit」を 1 箇所に置く。
`branch` を渡さないときは初期ブランチ名を指定しない（ホストの `init.defaultBranch` に従う。
従来の `git init -q` と同じ）。
"""
from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from _git_fixture import init_repo


def _git_out(path: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=path, check=True, capture_output=True, text=True
    ).stdout.strip()


class InitRepoContractTests(unittest.TestCase):
    def test_makes_a_repo_with_one_commit_and_user_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            init_repo(repo)

            self.assertEqual(_git_out(repo, "rev-list", "--count", "HEAD"), "1")
            self.assertEqual(_git_out(repo, "status", "--porcelain"), "")
            self.assertEqual(_git_out(repo, "config", "user.name"), "Test User")
            self.assertEqual(_git_out(repo, "config", "user.email"), "test@example.com")
            self.assertEqual((repo / "README.md").read_text(encoding="utf-8"), "test\n")

    def test_disables_auto_maintenance(self) -> None:
        """`git commit` が auto maintenance の子プロセスを起こさないようにする。

        起こすと `.git/objects/maintenance.lock` が一瞬でき、直後に `.git` を
        `shutil.copytree` するテスト（`test_root_branch_guard_real_git.py`）が
        「コピー中にファイルが消えた」で落ちる。
        """
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            init_repo(repo)

            self.assertEqual(
                _git_out(repo, "config", "--get", "--default", "true", "maintenance.auto"),
                "false",
            )

    def test_branch_argument_names_the_initial_branch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            init_repo(repo, branch="feature-x")

            self.assertEqual(_git_out(repo, "branch", "--show-current"), "feature-x")

    def test_without_branch_the_host_default_is_kept(self) -> None:
        """ホストの `init.defaultBranch` を、どのホストでも使われない名前に差し替えて見る。

        ホストの既定と突き合わせるだけだと、既定が `main` の機では `-b main` を常に
        付ける退行を見逃す。
        """
        with tempfile.TemporaryDirectory() as tmp:
            gitconfig = Path(tmp) / "gitconfig"
            gitconfig.write_text(
                "[init]\n\tdefaultBranch = host-default-probe\n", encoding="utf-8"
            )
            repo = Path(tmp) / "repo"
            repo.mkdir()
            host_env = {"GIT_CONFIG_GLOBAL": str(gitconfig), "GIT_CONFIG_NOSYSTEM": "1"}
            with mock.patch.dict(os.environ, host_env):
                init_repo(repo)

            self.assertEqual(
                _git_out(repo, "branch", "--show-current"), "host-default-probe"
            )

    def test_commit_date_argument_sets_author_and_committer_date(self) -> None:
        """merge gate の A-1 pin は HEAD の committer date を読む。author date も揃える。"""
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            init_repo(repo, commit_date="2026-01-02T03:04:05Z")

            self.assertEqual(
                _git_out(repo, "log", "-1", "--format=%at %ct"), "1767323045 1767323045"
            )


if __name__ == "__main__":
    unittest.main()
