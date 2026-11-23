"""trusted root の「対象 PR を記録していない」出口でも、GDD の PR 台帳を照合する。

desktop の worktree のセッションでは、hook のプロセスの cwd は root checkout（marker なし）で、
payload の最上位の `cwd` が worktree（marker あり）を指す。merge gate が最上位の cwd へ移ると、
root は marker のある worktree になり、その steering が対象 PR を記録していなければ素通りの
exit に届く。移る前は root checkout の marker 不在の経路で台帳を照合し、別の worktree の
GDD の PR なら止めていた。素通りの exit でも同じく台帳を照合し、hit なら不足として通知する
（miss・unknown・unreadable は marker 不在の経路と同じく通す）。
"""
from __future__ import annotations

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from _merge_gate_support import (
    _head_sha,
    _init_named_repo,
    _run_hook,
    _valid_evidence_lines,
    _write_marker_only,
    _write_state,
    _write_two_done_steerings,
)
from test_merge_gate_hook_non_gdd_merge import _ledger, _register

URL = "https://github.com/acme/widgets/pull/7"


class ToplevelCwdLedgerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp()).resolve()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.home = self.tmp / "home"
        (self.home / ".claude").mkdir(parents=True)
        # R: root checkout（marker なし）。W1: セッションの worktree（marker あり・active: false）。
        # W2: 別の GDD の worktree（PR #7 を記録・証跡なし・台帳に登録済み）。
        self.root = _init_named_repo(self.tmp, "root")
        subprocess.run(
            ["git", "-C", str(self.root), "remote", "add", "origin",
             "https://github.com/acme/widgets.git"], check=True,
        )
        self.w1 = self._add_worktree("w1")
        _write_marker_only(self.w1, active=False)
        self.w2 = self._add_worktree("w2")
        _write_state(self.w2, active=False, pr_url=URL)
        _register(self.home, self.w2)

    def _add_worktree(self, name):
        path = self.tmp / name
        subprocess.run(
            ["git", "-C", str(self.root), "worktree", "add", "-q", "-b", name, str(path)],
            check=True,
        )
        return path

    def _desktop(self, command, extra_env=None, top=None):
        """プロセスの cwd = R、最上位の cwd = W1（desktop の worktree のセッション）。"""
        payload = {"cwd": str(self.w1) if top is None else top,
                   "tool_input": {"command": command}}
        return _run_hook(payload, self.root, self.home, extra_env=extra_env)

    def _cli(self, command, extra_env=None):
        """最上位の cwd 無し・プロセスの cwd = W1（CLI のセッション）。"""
        return _run_hook({"tool_input": {"command": command}}, self.w1, self.home,
                         extra_env=extra_env)

    def _steering_forms(self):
        """W1 の steering の 3 通り（素通りの exit が 3 つある）。"""
        return (
            ("none", lambda: None),
            ("other-pr", lambda: _write_state(
                self.w1, active=False, pr_url=URL.replace("/7", "/9"))),
            ("two-done", lambda: _write_two_done_steerings(self.w1)),
        )

    def _set_steering(self, write):
        shutil.rmtree(self.w1 / ".steering", ignore_errors=True)
        write()

    def assertAllowed(self, result):
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "")

    def assertBlocked(self, result, reason):
        self.assertIn('"hookEventName": "PreToolUse"', result.stdout)
        self.assertIn(reason, result.stdout)

    # 1. 退行の再現（desktop の形）
    def test_desktop_session_blocks_a_ledger_pr_of_another_worktree(self):
        for name, write in self._steering_forms():
            with self.subTest(steering=name):
                self._set_steering(write)
                self.assertBlocked(self._desktop("gh pr merge 7 --merge"),
                                   "repo-root-unresolvable")

    # 2. CLI の形（最上位の cwd 無し・プロセスの cwd = W1）
    def test_cli_session_blocks_a_ledger_pr_of_another_worktree(self):
        for name, write in self._steering_forms():
            with self.subTest(steering=name):
                self._set_steering(write)
                self.assertBlocked(self._cli("gh pr merge 7 --merge"),
                                   "repo-root-unresolvable")

    # 3. 対象を決められない merge でも、読めた番号で照合する
    def test_unresolvable_merge_is_checked_with_the_number_it_read(self):
        for command in ("gh pr merge 7 --unknown-flag", "gh pr merge 7 extra"):
            for runner in (self._desktop, self._cli):
                with self.subTest(command=command, runner=runner.__name__):
                    self.assertBlocked(runner(command), "repo-root-unresolvable")

    # 4. 通知しすぎない
    def test_own_pr_with_evidence_in_the_ledger_allows(self):
        _write_state(
            self.w1, active=False, pr_url=URL,
            extra_lines=_valid_evidence_lines(_head_sha(self.w1)),
        )
        _register(self.home, self.w1)
        self.assertAllowed(self._desktop("gh pr merge 7 --merge"))

    def test_own_pr_in_a_dot_task_dir_allows(self):
        steering = self.w1 / ".steering" / ".20260101-demo"
        steering.mkdir(parents=True)
        (steering / "state.md").write_text(
            "## Gate Status\n- Resume From: done\n- Next Action: done\n"
            f"- PR URL: {URL}\n"
            + "".join(f"{ln}\n" for ln in _valid_evidence_lines(_head_sha(self.w1)))
        )
        _register(self.home, self.w1)
        self.assertAllowed(self._desktop("gh pr merge 7 --merge"))

    def test_pr_not_in_the_ledger_allows(self):
        for name, write in self._steering_forms():
            with self.subTest(steering=name):
                self._set_steering(write)
                self.assertAllowed(self._desktop("gh pr merge 8 --merge"))

    # 5. 決定として固定: 不一致の出口では unknown・unreadable は通す
    def test_unknown_and_unreadable_verdicts_allow_at_the_exits(self):
        for name, write in self._steering_forms():
            self._set_steering(write)
            with self.subTest(steering=name, verdict="unknown"):
                result = self._desktop("gh pr merge 7 --merge",
                                       extra_env={"GH_REPO": "acme/other"})
                self.assertAllowed(result)
            ledger = _ledger(self.home)
            with self.subTest(steering=name, verdict="unreadable"):
                ledger.unlink()
                ledger.mkdir()
                try:
                    self.assertAllowed(self._desktop("gh pr merge 7 --merge"))
                finally:
                    ledger.rmdir()
                    _register(self.home, self.w2)

    # 6. 使えない最上位の cwd は、プロセスの cwd に倒れて差分前と同じ判定
    def test_unusable_toplevel_cwd_falls_back_to_the_process_cwd(self):
        baseline = _run_hook({"tool_input": {"command": "gh pr merge 7 --merge"}},
                             self.root, self.home)
        self.assertBlocked(baseline, "repo-root-unresolvable")
        for top in ("w1", str(self.tmp / "missing"), 123, ["x"]):
            with self.subTest(top=top):
                result = self._desktop("gh pr merge 7 --merge", top=top)
                self.assertEqual(result.stdout, baseline.stdout)
                self.assertEqual(result.returncode, baseline.returncode)


if __name__ == "__main__":
    unittest.main()
