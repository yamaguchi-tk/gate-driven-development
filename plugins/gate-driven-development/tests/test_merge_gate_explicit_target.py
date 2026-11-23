"""対象を repo つきで明示した merge（PR の URL、リテラルの `-R owner/name <番号>`）は、cd 先を
決められなくても `pr-target-unresolvable` として通知しない。

gh が操作する repo と PR は実行先に依存しないので、プロセス cwd の root の証跡で検査する。
root の steering に対象 PR が無ければ GDD の PR 台帳を引き、miss のときだけ通す
（台帳に載っている別の GDD worktree の PR を、その証跡を見ずに通過扱いにしない）。2026-10-01〜10-10 の実データでは、
`pr-target-unresolvable` の merge の大半がこの形だった（cd の前後に `$` がある、
または cd が merge の後ろにある）。
"""
from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from _merge_gate_input_classes import once_per_input_class
from _merge_gate_support import _head_sha, _run_hook, _valid_evidence_lines, _write_state
from _merge_gate_support import _new_repo_with_marker_and_pr
from test_merge_gate_hook_non_gdd_merge import _git_absent_path, _git_failing_path, _ledger, _register
import test_merge_gate_same_repo_worktree as _same_repo
from test_merge_gate_same_repo_worktree import URL


class ExplicitTargetTests(unittest.TestCase):
    setUp = _same_repo.SameRepoWorktreeTests.setUp
    _add_worktree = _same_repo.SameRepoWorktreeTests._add_worktree
    assertAllowed = _same_repo.SameRepoWorktreeTests.assertAllowed
    assertBlocked = _same_repo.SameRepoWorktreeTests.assertBlocked
    _dedicated_worktree = _same_repo.SameRepoWorktreeTests._dedicated_worktree

    def _run(self, command, extra_env=None, cwd=None):
        # どのテストも repo・台帳を最初の起動の前に整え、途中で変えない。env を足す起動は組の鍵に
        # 入らないので、毎回起動する
        if extra_env is not None:
            return _same_repo.SameRepoWorktreeTests._run(self, command, extra_env, cwd)
        if not hasattr(self, "_hook"):
            self._hook = once_per_input_class(
                lambda payload: _run_hook(payload, self.launch, self.home), self.launch)
        tool_input = {"command": command}
        if cwd is not None:
            tool_input["cwd"] = str(cwd)
        return self._hook({"tool_input": tool_input})

    def _own_pr_with_evidence(self):
        _write_state(self.launch, active=False, pr_url=URL,
                     extra_lines=_valid_evidence_lines(_head_sha(self.launch)))

    def _explicit_forms(self, prefix, suffix=""):
        return (
            f"{prefix}gh pr merge {URL} --merge{suffix}",
            f"{prefix}gh pr merge -R acme/widgets 7 --merge{suffix}",
            f"{prefix}gh pr merge 7 --repo=acme/widgets --merge{suffix}",
            f"{prefix}gh -R acme/widgets pr merge 7 --merge{suffix}",
        )

    def test_explicit_target_with_an_unresolvable_cd_allows(self):
        self._own_pr_with_evidence()
        for prefix, suffix in (
            (f"cd {self.root} && X=$(true) && ", ""),  # cd の後ろに `$`
            (f"cd {self.root} && sed -n 's/^a$/b/p' /dev/null && ", ""),
            ("", f" && cd {self.root} && echo $(date)"),  # merge の後ろの cd と `$`
            (f"cd {self.other} && X=$(true) && ", ""),  # 別 repo への cd でも gh の対象は変わらない
        ):
            for command in self._explicit_forms(prefix, suffix):
                with self.subTest(command=command):
                    self.assertAllowed(self._run(command))

    def test_explicit_target_without_a_session_pr_allows_on_a_ledger_miss(self):
        self.assertAllowed(self._run(f"cd {self.root} && X=$(true) && gh pr merge {URL} --merge"))

    # 不足を通知すべき入力が通過扱いになる: 別の GDD worktree の PR を、その証跡を見ずに通過扱いにしない
    def test_pr_of_another_gdd_worktree_in_the_ledger_blocks(self):
        dedicated = self._dedicated_worktree(evidence=False)
        _register(self.home, dedicated)
        for command in self._explicit_forms(f"cd {dedicated} && X=$(true) && "):
            with self.subTest(command=command):
                self.assertBlocked(self._run(command), "repo-root-unresolvable")

    def test_explicit_target_with_a_resolved_other_target_allows(self):
        # cd 先・payload の cwd が別 repo に決まった形（実行先のループの分岐）
        self._own_pr_with_evidence()
        for command in self._explicit_forms(f"cd {self.other} && "):
            with self.subTest(command=command):
                self.assertAllowed(self._run(command))
        for command in self._explicit_forms(""):
            with self.subTest(command=command, cwd="other"):
                self.assertAllowed(self._run(command, cwd=self.other))

    def test_resolved_target_with_a_pr_of_another_gdd_worktree_blocks(self):
        dedicated = self._dedicated_worktree(evidence=False)
        _register(self.home, dedicated)
        for command in self._explicit_forms(""):
            with self.subTest(command=command):
                self.assertBlocked(self._run(command, cwd=dedicated), "repo-root-unresolvable")

    # 判定できないときに通ってしまう: 台帳の名指しできない repo・読めない台帳
    def test_unlisted_repo_with_a_pr_of_another_gdd_worktree_blocks(self):
        dedicated = self._dedicated_worktree(evidence=False)
        _register(self.home, dedicated)
        prefix = f"cd {dedicated} && X=$(true) && "
        for command in (
            prefix + 'gh pr merge -R "$O/widgets" 7 --merge',
            prefix + "gh pr merge https://github.com/$O/widgets/pull/7",
            prefix + "gh pr merge https://github.com/acm*/widgets/pull/7",
        ):
            with self.subTest(command=command):
                self.assertIn('"hookEventName": "PreToolUse"', self._run(command).stdout)

    def test_unreadable_ledger_blocks_the_explicit_target(self):
        _ledger(self.home).mkdir(parents=True)
        for command in self._explicit_forms(f"cd {self.root} && X=$(true) && "):
            with self.subTest(command=command):
                self.assertBlocked(self._run(command), "repo-root-unresolvable")

    def test_the_session_pr_still_needs_evidence(self):
        _write_state(self.launch, active=False, pr_url=URL)
        result = self._run(f"cd {self.root} && X=$(true) && gh pr merge {URL} --merge")
        self.assertIn('"hookEventName": "PreToolUse"', result.stdout)
        self.assertNotIn("pr-target-unresolvable", result.stdout)

    def test_same_number_in_another_repo_blocks(self):
        self._own_pr_with_evidence()
        for command in (
            f"cd {self.root} && X=$(true) && gh pr merge -R evil/other 7 --merge",
            f"cd {self.root} && X=$(true) && gh pr merge https://github.com/evil/other/pull/7",
        ):
            with self.subTest(command=command):
                self.assertIn('"hookEventName": "PreToolUse"', self._run(command).stdout)

    # 判定できないときに通ってしまう: 明示とみなせない形は、今までどおり不足として通知する
    def test_forms_that_are_not_an_explicit_target_still_block(self):
        self._own_pr_with_evidence()
        prefix = f"cd {self.root} && X=$(true) && "
        for command in (
            prefix + "gh pr merge 7 --merge",  # 番号だけ
            prefix + "gh pr merge --merge",  # 引数を省いた形
            prefix + "gh pr merge -R acme/widgets --merge",  # -R だけで番号が無い
            prefix + 'gh pr merge -R "$R" 7 --merge',
            prefix + "gh pr merge -R github.com/acme/widgets 7 --merge",  # host つき
            prefix + "gh pr merge https://github.com/$O/widgets/pull/7",
            prefix + "gh pr merge https://github.com/acm*/widgets/pull/7",
            prefix + f"gh pr merge {URL} && gh pr merge {URL}",  # merge が 2 つ
        ):
            with self.subTest(command=command):
                self.assertIn('"hookEventName": "PreToolUse"', self._run(command).stdout)

    def test_repo_overriding_env_still_blocks(self):
        self._own_pr_with_evidence()
        command = f"cd {self.root} && X=$(true) && gh pr merge -R acme/widgets 7 --merge"
        for env in ({"GH_HOST": "ghe.example.com"}, {"GH_REPO": "acme/other"}):
            with self.subTest(env=env):
                self.assertIn('"hookEventName": "PreToolUse"', self._run(command, extra_env=env).stdout)


class LedgerUnlistedRepoTests(unittest.TestCase):
    """台帳の照合は、owner/repo が許可リストの形でない（展開前の `$`・`*` など）とき、番号だけで照合する。

    展開前の文字列を台帳の repo と比べると一致せず miss になり、実シェルでは展開された同じ PR を
    証跡なしで merge しうる。台帳を引く 3 つの経路（root を決められない・marker の無い git cwd・
    共通ディレクトリ）で確かめる。
    """

    setUp = _same_repo.SameRepoWorktreeTests.setUp
    _add_worktree = _same_repo.SameRepoWorktreeTests._add_worktree
    _run = _same_repo.SameRepoWorktreeTests._run
    assertBlocked = _same_repo.SameRepoWorktreeTests.assertBlocked
    assertAllowed = _same_repo.SameRepoWorktreeTests.assertAllowed
    _dedicated_worktree = _same_repo.SameRepoWorktreeTests._dedicated_worktree

    FORMS = (
        "gh pr merge -R acme/$R 7 --merge",
        "gh pr merge https://github.com/$O/widgets/pull/7 --merge",
        "gh pr merge https://github.com/acm*/widgets/pull/7 --merge",
    )

    def setUp(self):  # noqa: F811 - _same_repo.SameRepoWorktreeTests.setUp に台帳の登録を足す
        _same_repo.SameRepoWorktreeTests.setUp(self)
        _register(self.home, self._dedicated_worktree(evidence=False))
        self.non_repo = self.tmp / "non-repo"
        self.non_repo.mkdir()

    def _from(self, cwd, command, payload_cwd=None):
        tool_input = {"command": command}
        if payload_cwd is not None:
            tool_input["cwd"] = str(payload_cwd)
        return _run_hook({"tool_input": tool_input}, cwd, self.home)

    def test_unlisted_repo_matches_the_ledger_by_number(self):
        for route, cwd, payload_cwd, reason in (
            ("root を決められない", self.non_repo, None, "repo-root-unresolvable"),
            ("marker の無い git cwd", self.root, None, "repo-root-unresolvable"),
            ("共通ディレクトリ", self.launch, self.root, "repo-root-unresolvable"),
        ):
            for command in self.FORMS:
                with self.subTest(route=route, command=command):
                    self.assertBlocked(self._from(cwd, command, payload_cwd), reason)

    def test_listed_repo_of_another_number_still_passes(self):
        # 許可リストの形の repo は今までどおり repo と番号の組で照合する（台帳に無い PR は通る）
        self.assertAllowed(self._from(self.non_repo, "gh pr merge -R acme/widgets 8 --merge"))
        self.assertAllowed(self._from(self.root, "gh pr merge -R acme/widgets 8 --merge"))


class RootUnresolvedExplicitTargetTests(unittest.TestCase):
    """root を決められない経路（cwd が git でない）でも、対象を repo つきで明示した merge は、cd の意図・
    cd 先・payload の cwd を見ずに GDD の PR 台帳だけで決める（miss のときだけ通す）。"""

    _add_worktree = _same_repo.SameRepoWorktreeTests._add_worktree
    assertBlocked = _same_repo.SameRepoWorktreeTests.assertBlocked
    assertAllowed = _same_repo.SameRepoWorktreeTests.assertAllowed
    _dedicated_worktree = _same_repo.SameRepoWorktreeTests._dedicated_worktree
    _from = LedgerUnlistedRepoTests._from

    def setUp(self):
        _same_repo.SameRepoWorktreeTests.setUp(self)
        self.dedicated = self._dedicated_worktree(evidence=False)
        _register(self.home, self.dedicated)
        self.non_repo = self.tmp / "non-repo"
        self.non_repo.mkdir()

    def _forms(self, number, prefix="", suffix=""):
        return (
            f"{prefix}gh pr merge https://github.com/acme/widgets/pull/{number} --merge{suffix}",
            f"{prefix}gh pr merge -R acme/widgets {number} --merge{suffix}",
        )

    def _shapes(self, number):
        for prefix, suffix in (
            (f"cd {self.root} && X=$(true) && ", ""),
            (f"cd {self.dedicated} && X=$(true) && ", ""),
            ("", f" && cd {self.root} && echo $(date)"),
            ("pushd /tmp && ", ""),
        ):
            yield from self._forms(number, prefix, suffix)

    def test_explicit_target_not_in_the_ledger_allows(self):
        for command in self._shapes(8):
            with self.subTest(command=command):
                self.assertAllowed(self._from(self.non_repo, command))
        for command in self._forms(8):
            with self.subTest(payload_cwd="relative", command=command):
                self.assertAllowed(self._from(self.non_repo, command, payload_cwd="rel/dir"))

    def test_explicit_target_in_the_ledger_blocks(self):
        for command in self._shapes(7):
            with self.subTest(command=command):
                self.assertBlocked(self._from(self.non_repo, command), "repo-root-unresolvable")

    def test_unreadable_ledger_blocks(self):
        _ledger(self.home).unlink()
        _ledger(self.home).mkdir()
        for command in self._shapes(8):
            with self.subTest(command=command):
                self.assertBlocked(self._from(self.non_repo, command), "repo-root-unresolvable")

    def test_forms_that_are_not_an_explicit_target_still_block(self):
        for command in (
            f"cd {self.root} && X=$(true) && gh pr merge 8 --merge",
            f"cd {self.root} && X=$(true) && gh pr merge -R github.com/acme/widgets 8 --merge",
            f"cd {self.root} && X=$(true) && gh pr merge -R acme/$R 8 --merge",
        ):
            with self.subTest(command=command):
                self.assertBlocked(self._from(self.non_repo, command), "repo-root-unresolvable")
        result = _run_hook(
            {"tool_input": {"command": f"cd {self.root} && X=$(true) && gh pr merge -R acme/widgets 8 --merge"}},
            self.non_repo, self.home, extra_env={"GH_REPO": "acme/other"},
        )
        self.assertBlocked(result, "repo-root-unresolvable")


class GitBrokenMarkerExplicitTargetTests(unittest.TestCase):
    """git が無い・`git rev-parse` が失敗して root を決められないとき、明示した merge でも、決められる
    実行先（プロセス cwd・payload の cwd・cd 先）の祖先に marker があれば不足として通知する（台帳に無い PR でも）。"""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.home = self.tmp / "home"
        (self.home / ".claude").mkdir(parents=True)
        self.non_repo = self.tmp / "work-claude"
        self.non_repo.mkdir()
        self.gdd = _new_repo_with_marker_and_pr(self.tmp, "gdd-repo", pr=7)
        self.sub = self.gdd / "sub"
        self.sub.mkdir()

    def test_marker_on_a_resolved_execution_target_blocks(self):
        forms = ("gh pr merge https://github.com/acme/gdd-repo/pull/7 --merge",
                 "gh pr merge -R acme/gdd-repo 7 --merge")
        for name, path in (("rev-parse が失敗", _git_failing_path(self.tmp)),
                           ("git が無い", _git_absent_path(self.tmp))):
            env = {"PATH": path}
            for form in forms:
                for cwd, command, payload_cwd in (
                    (self.gdd, form, None),
                    (self.sub, form, None),
                    (self.non_repo, f"cd {self.gdd} && {form}", None),
                    (self.non_repo, form, self.sub),
                ):
                    with self.subTest(git=name, cwd=str(cwd), command=command, payload_cwd=payload_cwd):
                        tool_input = {"command": command}
                        if payload_cwd is not None:
                            tool_input["cwd"] = str(payload_cwd)
                        result = _run_hook({"tool_input": tool_input}, cwd, self.home, extra_env=env)
                        self.assertIn('"hookEventName": "PreToolUse"', result.stdout)
                        self.assertIn("repo-root-unresolvable", result.stdout)


if __name__ == "__main__":
    unittest.main()
