"""共有 fixture `_git_fixture.init_repo` の、作り済みの repo を複製する経路の契約を固定する。

`test_git_fixture_contract.py` は、`test_pytest_ini_durations_contract.py` が「1 秒未満の
速いテスト」の見本として回す。複製の試験は git を何度も起動し、負荷が高いと 1 秒を超えるので、
別のファイルに置く。
"""
from __future__ import annotations

import os
import subprocess
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

import _git_fixture
from _git_fixture import init_repo
from test_git_fixture_contract import _git_out


class InitRepoTemplateTests(unittest.TestCase):
    """2 回目以降の `init_repo` は、作り済みの repo を複製して git の起動を 1 回にする。

    全量のテストは git を非常に多く起動していて（2026-10-14 に測った）、その多くがこの手順だった。
    複製しても、日時・ブランチ・設定は 1 回ずつ作ったときと同じにする。
    """

    def _git_calls(self, repo: Path, **kwargs) -> int:
        calls = []
        real = subprocess.run

        def counting(args, *a, **k):
            if args and args[0] == "git":
                calls.append(args)
            return real(args, *a, **k)

        with mock.patch.object(_git_fixture.subprocess, "run", counting):
            init_repo(repo, **kwargs)
        return len(calls)

    def test_second_call_runs_git_once(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            first, second = Path(tmp) / "a", Path(tmp) / "b"
            first.mkdir()
            second.mkdir()
            init_repo(first, branch="template-probe")
            self.assertLessEqual(self._git_calls(second, branch="template-probe"), 1)
            self.assertEqual(_git_out(second, "branch", "--show-current"), "template-probe")
            self.assertEqual(_git_out(second, "rev-list", "--count", "HEAD"), "1")
            self.assertEqual(_git_out(second, "status", "--porcelain"), "")
            self.assertEqual(_git_out(second, "config", "user.name"), "Test User")
            self.assertEqual(
                _git_out(second, "config", "--get", "--default", "true", "maintenance.auto"),
                "false",
            )

    def test_copied_repo_commit_dates_are_the_time_of_the_call(self) -> None:
        """日時を渡さない repo の HEAD は、呼んだ時刻の commit にする（複製元の時刻を残さない）。

        commit の日時を読む gate（merge gate のレビュー待ちなど）のテストが、複製元を作った
        時刻からの経過で結果を変えないようにする。
        """
        with tempfile.TemporaryDirectory() as tmp:
            first, second = Path(tmp) / "a", Path(tmp) / "b"
            first.mkdir()
            second.mkdir()
            init_repo(first, branch="date-probe")
            # 複製元を古い時刻の commit にしておく（待たずに、作ってから時間が経った形を作る）
            old = {**os.environ, "GIT_COMMITTER_DATE": "2001-01-01T00:00:00Z"}
            for key, template in _git_fixture._templates.items():
                if key[:2] != ("date-probe", None):
                    continue
                subprocess.run(["git", "commit", "-q", "--amend", "--no-edit",
                                "--date=2001-01-01T00:00:00Z"], cwd=template, check=True, env=old)
            before = int(time.time())
            init_repo(second, branch="date-probe")
            author, committer = map(int, _git_out(second, "log", "-1", "--format=%at %ct").split())
            self.assertGreaterEqual(author, before)
            self.assertGreaterEqual(committer, before)

    def test_copied_repo_keeps_a_given_commit_date(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            first, second = Path(tmp) / "a", Path(tmp) / "b"
            first.mkdir()
            second.mkdir()
            init_repo(first, commit_date="2026-01-02T03:04:05Z")
            init_repo(second, commit_date="2026-01-02T03:04:05Z")
            self.assertEqual(
                _git_out(second, "log", "-1", "--format=%at %ct"), "1767323045 1767323045"
            )

    def test_host_default_branch_change_is_not_hidden_by_the_template(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            first = Path(tmp) / "a"
            first.mkdir()
            init_repo(first)
            gitconfig = Path(tmp) / "gitconfig"
            gitconfig.write_text(
                "[init]\n\tdefaultBranch = host-default-probe-2\n", encoding="utf-8"
            )
            repo = Path(tmp) / "repo"
            repo.mkdir()
            host_env = {"GIT_CONFIG_GLOBAL": str(gitconfig), "GIT_CONFIG_NOSYSTEM": "1"}
            with mock.patch.dict(os.environ, host_env):
                init_repo(repo)
            self.assertEqual(
                _git_out(repo, "branch", "--show-current"), "host-default-probe-2"
            )

    def test_non_empty_directory_keeps_its_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            first, second = Path(tmp) / "a", Path(tmp) / "b"
            first.mkdir()
            second.mkdir()
            init_repo(first, branch="keep-probe")
            (second / "other.txt").write_text("x\n", encoding="utf-8")
            init_repo(second, branch="keep-probe")
            self.assertEqual((second / "other.txt").read_text(encoding="utf-8"), "x\n")
            self.assertEqual(_git_out(second, "status", "--porcelain"), "?? other.txt")


if __name__ == "__main__":
    unittest.main()
