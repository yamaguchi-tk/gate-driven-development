"""root branch guard が、ブランチを作る実行先（`git -C`・先行する `cd`）でも判定すること。

linked worktree のセッションから `cd <root> && git checkout -b …` で root checkout にブランチを
作る形は、実データ（2026-10-04、全 project の transcript）に何十件もあった。payload の cwd は
候補に残したまま実行先を候補に足し、どれか 1 つが「active で linked worktree でない」なら止める。
"""

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from _root_branch_guard_support import RootBranchGuardFixtureMixin


class ExecTargetTests(RootBranchGuardFixtureMixin, unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name).resolve()
        self.root = self.base / "root"
        self.root.mkdir()
        self._init_repo(self.root)
        self._write_active_state(self.root)
        self.worktree = self.base / "wt"
        subprocess.run(
            ["git", "worktree", "add", "-q", "-b", "wt-branch", str(self.worktree)],
            cwd=self.root, check=True, capture_output=True,
        )
        self.other = self.base / "wt2"
        subprocess.run(
            ["git", "worktree", "add", "-q", "-b", "wt2-branch", str(self.other)],
            cwd=self.root, check=True, capture_output=True,
        )
        # linked worktree の例外を確かめるため、行き先の worktree も active にする。
        self._write_active_state(self.other)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def assert_deny(self, cwd: Path, command: str) -> dict:
        result = self._run_guard(cwd, command)
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        payload = json.loads(result.stderr.strip())
        self.assertEqual(payload["hookSpecificOutput"]["permissionDecision"], "deny")
        return payload

    def assert_allow(self, cwd: Path, command: str) -> None:
        result = self._run_guard(cwd, command)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_cd_to_active_root_from_worktree_is_denied(self) -> None:
        for command in (
            f"cd {self.root} && git checkout -b feat",
            f"cd {self.root}; git switch -c feat",
            f"cd {self.root}\ngit branch feat",
            "cd ../root && git checkout -b feat",
        ):
            with self.subTest(command=command):
                payload = self.assert_deny(self.worktree, command)
                self.assertIn(f"cwd: {self.root}\n", payload["systemMessage"])

    def test_git_dash_c_to_active_root_from_worktree_is_denied(self) -> None:
        for command in (
            f"git -C {self.root} checkout -b feat",
            f"git -C {self.root} switch -c feat",
            "git -C ../root branch feat",
            f"git -C {self.base} -C root switch -c feat",
            f"cd {self.base} && git -C root checkout -b feat",
        ):
            with self.subTest(command=command):
                self.assert_deny(self.worktree, command)

    def test_undeterminable_dash_c_keeps_the_chain(self) -> None:
        # 決められない `-C` は `cd` と同じく飛ばし、後ろの `-C` を前の基点から解く。
        for command in (
            f"git -C ~+ -C {self.root} switch -c feat",
            f'git -C "$R" -C {self.root} switch -c feat',
            f"git -C /x/$(echo y) -C {self.root} switch -c feat",
            # 後ろが相対パスでも、飛ばした要素の前の基点から解く。
            f'git -C {self.base} -C "$R" -C root switch -c feat',
            f"git -C {self.base} -C x$(echo y) -C root switch -c feat",
        ):
            with self.subTest(command=command):
                payload = self.assert_deny(self.worktree, command)
                self.assertIn(f"cwd: {self.root}\n", payload["systemMessage"])

    def test_undeterminable_dash_c_then_relative_worktree_stays_allowed(self) -> None:
        self.assert_allow(self.worktree, 'git -C "$R" -C ../wt2 switch -c feat')

    def test_targets_that_are_linked_worktrees_stay_allowed(self) -> None:
        for command in (
            f"cd {self.other} && git checkout -b feat",
            f"git -C {self.other} switch -c feat",
            # `-C` をサブコマンドの後まで拾うと、`../root` を active な root に解いて止めてしまう。
            "git branch -C ../root copy",
        ):
            with self.subTest(command=command):
                self.assert_allow(self.worktree, command)

    def test_payload_cwd_stays_a_candidate(self) -> None:
        # 実行先を候補に足すだけなので、payload cwd が root なら、cd の先が worktree でも止まる。
        self.assert_deny(self.root, f"(cd {self.worktree}) ; git checkout -b feat")
        self.assert_deny(self.root, f"cd {self.worktree} && git -C {self.root} checkout -b feat")
        # cd の行き先をシェルと同じ規則で決めることはできないので、先頭の `cd <worktree> &&` でも止める（限界）。
        for command in (
            f"cd {self.other} && git checkout -b feat",
            f'W={self.other}; cd "$W" && git switch -c feat',
            f"cd ../{self.other.name} && git checkout -b feat",
            f"HOME={self.base}; cd ~/{self.other.name} && git checkout -b feat",
        ):
            with self.subTest(command=command):
                self.assert_deny(self.root, command)

    def test_unresolved_target_falls_back_to_payload_cwd(self) -> None:
        # 変数の先は決められない。今までどおり payload cwd だけで判定する（限界）。
        self.assert_allow(self.worktree, 'cd "$R" && git checkout -b feat')

    def test_unexpandable_tilde_is_not_a_target(self) -> None:
        # `~-` は Python では展開できない。変数と同じく行き先を決めず、例外で止めない。
        self.assert_allow(self.worktree, "cd ~-/x && git checkout -b feat")

    def test_unusable_target_path_fails_closed(self) -> None:
        self.assert_deny(self.worktree, "cd 'a\x00b' && git checkout -b feat")


if __name__ == "__main__":
    unittest.main()
