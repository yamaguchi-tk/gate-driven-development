"""merge gate: 番号の先頭の 0 と、台帳照合で読めないものを通す側に落とさない。

Issue #125・#126・#128（PR #124 の独立レビュー・codex-4 の、未修正のまま残した high）。

- #126: gh は PR 番号を `strconv.Atoi` で読むので、`007` は #7 を指す。merge gate は
  番号を文字列で比べていたので、台帳照合でも本体（marker のある worktree）でも一致せず
  通っていた。番号は入口で 1 回だけ正規化する
- #128: 台帳のパスがディレクトリ・FIFO・壊れた symlink、または親が辿れないと、
  読めないのに miss（通す）に進んでいた。FIFO では待ち続けて hook が timeout していた
- #125: 最初の読めない state.md で返すので、後ろの hit が隠れていた。root・`.steering`・
  task dir が辿れないときは「無い」扱いで miss になっていた。全部を走査し、
  hit > unreadable > miss の順で決める

経路ごとの倒し方は変えない（root 未解決の経路は miss だけ通す、git cwd の marker 不在の
経路は hit だけ不足として通知する。`test_merge_gate_hook_non_gdd_merge.py` の `test_verdict_by_path_table`）。
"""
from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from _merge_gate_support import (
    HANG_GUARD,
    HOOK_TIMEOUT,
    _init_named_repo,
    _new_repo_with_marker_and_pr,
    _run_hook,
    _write_marker_only,
    _write_state,
    _write_two_done_steerings,
)
from test_merge_gate_hook_non_gdd_merge import _clone_like, _ledger, _register, _run_pre_pr
from _timing_budget import hang_guard_seconds, timing_budget

# HOOK_TIMEOUT は merge gate の hooks.json の timeout（秒）。merge gate の FIFO のテストは、壁時計の
# 打ち切り（HANG_GUARD）で待ち続けを TimeoutExpired にする。長い入力のテストは、CPU 時間を HOOK_TIMEOUT
# と比べる（壁時計は負荷で伸び、並列の実行で落ちる）。hook の処理はほぼ直列なので、CPU 時間だけで
# hook の timeout を超えるなら、壁時計でも超えて PreToolUse は通る。テスト時間の ADR の二本立て（壁時計の
# backstop は timeout の半分）にしないのは、この 2 本は CPU 時間そのものが timeout の数割を使い、
# backstop が負荷で落ちるため。
GDD_PR = "gh pr merge -R acme/infra-gdd 7"
OTHER_PR = "gh pr merge -R acme/infra-gdd 8"


def _hook(command: str, cwd: Path, home: Path, **kw):
    # 実行環境の GDD_HOOK_STATE_DIR を引き継ぐと、fixture ではなく手元の台帳を読む。
    return _run_hook({"tool_input": {"command": command}}, cwd, home,
                     drop_env=("GDD_HOOK_STATE_DIR",), **kw)


def _is_block(result) -> bool:
    return result.returncode == 0 and '"hookEventName": "PreToolUse"' in result.stdout


def _is_pass(result) -> bool:
    return result.returncode == 0 and '"hookEventName"' not in result.stdout


class _LedgerCase(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.home = self.tmp / "home"
        (self.home / ".claude").mkdir(parents=True)
        self.non_repo = self.tmp / "work-claude"
        self.non_repo.mkdir()
        # GDD worktree（PR URL: https://github.com/acme/infra-gdd/pull/7）。
        self.gdd = _new_repo_with_marker_and_pr(self.tmp, "infra-gdd", pr=7, commit=False)
        # marker の無い root checkout（origin は同じ repo）。git cwd の経路の実行先。
        self.checkout = _clone_like(self.tmp, "root-checkout", "https://github.com/acme/infra-gdd.git")
        self._locked: list[tuple[Path, int]] = []

    def tearDown(self):
        for path, mode in reversed(self._locked):
            path.chmod(mode)

    def _lock(self, path: Path, mode: int = 0) -> None:
        if os.geteuid() == 0:
            self.skipTest("root は権限を落としても読めてしまう")
        self._locked.append((path, path.stat().st_mode & 0o7777))
        path.chmod(mode)

    def _from_non_git(self, command):
        return _hook(command, self.non_repo, self.home)

    def _from_checkout(self, command):
        return _hook(command, self.checkout, self.home)

    def _unreadable_verdict(self):
        """unreadable の経路ごとの判定: root 未解決は不足として通知し、git cwd の marker 不在は通す。"""
        self.assertTrue(_is_block(self._from_non_git(OTHER_PR)))
        self.assertTrue(_is_pass(self._from_checkout("gh pr merge 8")))


class LeadingZeroPrNumberTests(_LedgerCase):
    """#126 と、その対になる本体の経路。"""

    def test_main_path_checks_leading_zero_number(self):
        # 本体: marker のある GDD worktree で、done の steering の PR を `007` で merge する。
        repo = _new_repo_with_marker_and_pr(self.tmp, "widgets", pr=7)
        baseline = _hook("gh pr merge 7", repo, self.home)
        self.assertTrue(_is_block(baseline))
        for command in ("gh pr merge 007", "gh pr merge 0007 --squash"):
            with self.subTest(command=command):
                result = _hook(command, repo, self.home)
                self.assertTrue(_is_block(result), result.stdout)
                self.assertIn("approval-missing", result.stdout)

    def test_ledger_matches_leading_zero_number_on_both_paths(self):
        _register(self.home, self.gdd)
        self.assertTrue(_is_block(self._from_non_git("gh pr merge -R acme/infra-gdd 007")))
        self.assertTrue(_is_block(self._from_checkout("gh pr merge 007")))
        self.assertTrue(_is_pass(self._from_checkout("gh pr merge 008")))

    def test_ledger_matches_leading_zero_in_state_url(self):
        _write_state(self.gdd, active=False, pr_url="https://github.com/acme/infra-gdd/pull/007")
        _register(self.home, self.gdd)
        self.assertTrue(_is_block(self._from_checkout("gh pr merge 7")))

    def test_all_zero_number_does_not_crash(self):
        # fail-open ケース「例外で guard 全体が落ちる」: 正規化で空にならない（set -u）。
        _register(self.home, self.gdd)
        repo = _new_repo_with_marker_and_pr(self.tmp, "widgets", pr=7)
        for cwd in (repo, self.checkout):
            with self.subTest(cwd=cwd.name):
                result = _hook("gh pr merge 000", cwd, self.home)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertNotIn("unbound variable", result.stderr)



class LedgerRepoUnresolvableTests(_LedgerCase):
    """台帳の照合も、記録から owner/repo を取り出せない PR URL は一致とみなして不足として通知する（本体の経路と同じ）。"""

    def test_state_url_without_a_repo_is_a_hit(self):
        for pr_url in ("/pull/7", "widgets/pull/7", "[#7](../pull/7)"):
            with self.subTest(pr_url=pr_url):
                _write_state(self.gdd, active=False, pr_url=pr_url)
                _register(self.home, self.gdd)
                self.assertTrue(_is_block(self._from_non_git(GDD_PR)))
                self.assertTrue(_is_block(self._from_checkout("gh pr merge https://github.com/acme/infra-gdd/pull/7")))

    def test_url_is_matched_when_a_number_is_also_seen_from_a_checkout(self):
        """不足として通知すべき入力: marker の無い checkout から、台帳の PR を URL で指し番号も見える merge を通さない。"""
        _register(self.home, self.gdd)
        for command in (
            "gh pr merge -st 8 https://github.com/acme/infra-gdd/pull/7",
            "gh pr merge -st 8 7",
            "gh pr merge 7 https://github.com/acme/infra-gdd/pull/7",
        ):
            with self.subTest(command=command):
                self.assertTrue(_is_block(self._from_checkout(command)))

    def test_other_number_still_misses(self):
        """通知しすぎない: 番号が違えば、repo を取り出せない記録でも照合しない。"""
        _write_state(self.gdd, active=False, pr_url="/pull/7")
        _register(self.home, self.gdd)
        self.assertTrue(_is_pass(self._from_checkout("gh pr merge 8")))

class LedgerPathKindTests(_LedgerCase):
    """#128: 台帳のパスが通常ファイルでないとき。"""

    def test_directory_ledger_is_unreadable(self):
        _ledger(self.home).mkdir(parents=True)
        self._unreadable_verdict()

    def test_fifo_ledger_is_unreadable_without_waiting(self):
        # 待ち続けると hooks.json の timeout で PreToolUse は通るので、待たずに返す（待てば HANG_GUARD で落ちる）。
        ledger = _ledger(self.home)
        ledger.parent.mkdir(parents=True)
        os.mkfifo(ledger)
        result = _hook(OTHER_PR, self.non_repo, self.home)
        self.assertTrue(_is_block(result), result.stdout)

    def test_dangling_symlink_ledger_is_unreadable(self):
        ledger = _ledger(self.home)
        ledger.parent.mkdir(parents=True)
        ledger.symlink_to(self.tmp / "missing-ledger")
        self._unreadable_verdict()

    def test_symlink_to_regular_ledger_still_matches(self):
        real = self.tmp / "real-ledger"
        real.write_text(f"{self.gdd}\n", encoding="utf-8")
        ledger = _ledger(self.home)
        ledger.parent.mkdir(parents=True)
        ledger.symlink_to(real)
        self.assertTrue(_is_block(self._from_checkout("gh pr merge 7")))
        self.assertTrue(_is_pass(self._from_non_git(OTHER_PR)))

    def test_unsearchable_ledger_parent_is_unreadable(self):
        _register(self.home, self.gdd)
        self._lock(_ledger(self.home).parent)
        self._unreadable_verdict()

    def test_missing_ledger_and_parent_still_pass(self):
        # 台帳が無い（親も無い）ときは従来どおり miss。
        self.assertTrue(_is_pass(self._from_non_git(OTHER_PR)))
        _ledger(self.home).parent.mkdir(parents=True)
        self.assertTrue(_is_pass(self._from_non_git(OTHER_PR)))


class LedgerScanTests(_LedgerCase):
    """#125: 読めないものがあっても全部を走査し、hit > unreadable > miss で決める。"""

    def _other_gdd_with_unreadable_state(self):
        other = _new_repo_with_marker_and_pr(self.tmp, "other-gdd", pr=9, commit=False)
        self._lock(other / ".steering" / "20260101-demo" / "state.md")
        return other

    def test_unreadable_state_in_earlier_root_does_not_hide_hit(self):
        _register(self.home, self._other_gdd_with_unreadable_state(), self.gdd)
        self.assertTrue(_is_block(self._from_checkout("gh pr merge 7")))

    def test_unreadable_state_in_later_root_keeps_hit(self):
        _register(self.home, self.gdd, self._other_gdd_with_unreadable_state())
        self.assertTrue(_is_block(self._from_checkout("gh pr merge 7")))

    def test_unreadable_state_in_earlier_task_does_not_hide_hit(self):
        old = self.gdd / ".steering" / "20250101-old"
        old.mkdir()
        (old / "state.md").write_text("- PR URL: https://github.com/acme/infra-gdd/pull/3\n")
        self._lock(old / "state.md")
        _register(self.home, self.gdd)
        self.assertTrue(_is_block(self._from_checkout("gh pr merge 7")))
        self._unreadable_verdict()

    def test_unsearchable_task_dir_is_unreadable(self):
        _register(self.home, self.gdd)
        self._lock(self.gdd / ".steering" / "20260101-demo", 0o600)
        self._unreadable_verdict()

    def test_unlistable_steering_is_unreadable(self):
        _register(self.home, self.gdd)
        self._lock(self.gdd / ".steering", 0o300)
        self._unreadable_verdict()

    def test_unsearchable_root_is_unreadable(self):
        _register(self.home, self.gdd)
        self._lock(self.gdd, 0o600)
        self._unreadable_verdict()

    def test_root_that_is_a_file_is_unreadable(self):
        # hit はありえないが、在るのに辿れないものは不足として通知する側に倒す。repo 内へ移れば
        # （git cwd の経路）通る。
        stray = self.tmp / "stray-file"
        stray.write_text("x", encoding="utf-8")
        _register(self.home, stray)
        self._unreadable_verdict()

    def test_state_that_is_a_directory_is_unreadable(self):
        task = self.gdd / ".steering" / "20250101-odd"
        (task / "state.md").mkdir(parents=True)
        _register(self.home, self.gdd)
        self._unreadable_verdict()
        self.assertTrue(_is_block(self._from_checkout("gh pr merge 7")))

    def test_dangling_symlink_state_is_unreadable(self):
        task = self.gdd / ".steering" / "20250101-link"
        task.mkdir()
        (task / "state.md").symlink_to(self.tmp / "missing-state")
        _register(self.home, self.gdd)
        self._unreadable_verdict()

    def test_empty_or_missing_steering_is_a_miss(self):
        # fail-open ケース「例外で guard 全体が落ちる」: glob が 0 件でも落ちない。
        empty = _clone_like(self.tmp, "empty-gdd", "https://github.com/acme/empty.git")
        (empty / ".steering").mkdir()
        bare = _clone_like(self.tmp, "no-steering", "https://github.com/acme/bare.git")
        _register(self.home, empty, bare, self.tmp / "deleted-worktree")
        result = self._from_non_git(OTHER_PR)
        self.assertTrue(_is_pass(result), result.stdout + result.stderr)
        self.assertNotIn("unbound variable", result.stderr)

    def test_steering_that_is_a_file_is_unreadable(self):
        odd = _clone_like(self.tmp, "odd-gdd", "https://github.com/acme/odd.git")
        (odd / ".steering").write_text("x", encoding="utf-8")
        _register(self.home, odd)
        self._unreadable_verdict()


class MainPathNumberTests(_LedgerCase):
    """本体の経路でも、state.md の URL 側の番号を正規化して比べる。長い値で timeout しない。"""

    def test_state_url_with_leading_zero_is_checked(self):
        repo = _new_repo_with_marker_and_pr(self.tmp, "widgets", pr=7)
        _write_state(repo, active=False, pr_url="https://github.com/acme/widgets/pull/007")
        for command in ("gh pr merge 007", "gh pr merge 7"):
            with self.subTest(command=command):
                result = _hook(command, repo, self.home)
                self.assertTrue(_is_block(result), result.stdout)
        self.assertTrue(_is_pass(_hook("gh pr merge 8", repo, self.home)))

    def test_many_leading_zeros_do_not_time_out(self):
        # hooks.json の timeout は 10 秒で、timeout すると PreToolUse は通る。
        repo = _new_repo_with_marker_and_pr(self.tmp, "widgets", pr=7)
        with timing_budget() as timing:
            result = _hook("gh pr merge " + "0" * 200_000 + "7", repo, self.home, timeout=HANG_GUARD)
        self.assertTrue(_is_block(result), result.stdout)
        self.assertIn("approval-missing", result.stdout)
        self.assertLess(timing.cpu_seconds, HOOK_TIMEOUT, f"wall {timing.wall_seconds:.2f}s")

    def test_oversized_state_url_fails_closed_without_waiting(self):
        repo = _new_repo_with_marker_and_pr(self.tmp, "widgets", pr=7)
        huge = "https://github.com/acme/widgets/pull/" + "0" * 100_000 + "7"
        _write_state(repo, active=False, pr_url=huge)
        _register(self.home, repo)
        for cwd, command in ((repo, "gh pr merge 7"), (self.non_repo, "gh pr merge -R acme/widgets 7")):
            with self.subTest(cwd=cwd.name):
                with timing_budget() as timing:
                    result = _hook(command, cwd, self.home, timeout=HANG_GUARD)
                self.assertTrue(_is_block(result), result.stdout)
                self.assertLess(timing.cpu_seconds, HOOK_TIMEOUT, f"wall {timing.wall_seconds:.2f}s")


class MainPathUnreadableSteeringTests(_LedgerCase):
    """本体の経路の探し直しも、読めない steering を「無い」として飛ばさない。"""

    def _repo_with_locked_target(self, mode=0, *, found=False):
        repo = _init_named_repo(self.tmp, "widgets")
        if found:
            # 終わっていない steering が 1 件（primary は found）で、PR URL は別 PR。
            _write_marker_only(repo, active=False, session_id=None)
            live = repo / ".steering" / "20260101-live"
            live.mkdir(parents=True)
            (live / "state.md").write_text(
                "## Gate Status\n- Resume From: implement\n- Next Action: implement\n"
                "- PR URL: https://github.com/acme/widgets/pull/1\n"
            )
        else:
            _write_two_done_steerings(repo)
        target = repo / ".steering" / "20260103-target"
        target.mkdir(parents=True)
        (target / "state.md").write_text(
            "## Gate Status\n- Resume From: done\n- Next Action: done\n"
            "- PR URL: https://github.com/acme/widgets/pull/7\n"
        )
        self._lock(target / "state.md" if mode == 0 else target, mode)
        return repo

    def test_unreadable_target_state_blocks_when_steerings_are_many(self):
        result = _hook("gh pr merge 7", self._repo_with_locked_target(), self.home)
        self.assertTrue(_is_block(result), result.stdout)
        self.assertIn("state-unreadable", result.stdout)

    def test_unsearchable_target_dir_blocks_when_steerings_are_many(self):
        result = _hook("gh pr merge 7", self._repo_with_locked_target(0o600), self.home)
        self.assertTrue(_is_block(result), result.stdout)
        self.assertIn("state-unreadable", result.stdout)

    def test_unreadable_target_state_blocks_when_found_points_elsewhere(self):
        result = _hook("gh pr merge 7", self._repo_with_locked_target(found=True), self.home)
        self.assertTrue(_is_block(result), result.stdout)
        self.assertIn("state-unreadable", result.stdout)


class LedgerDotTaskDirTests(_LedgerCase):
    """本体の `find` と同じく、ドットで始まる task dir も台帳の照合で見る。"""

    def test_dot_task_dir_is_matched(self):
        steering = self.gdd / ".steering"
        (steering / "20260101-demo").rename(steering / ".20260101-demo")
        _register(self.home, self.gdd)
        self.assertTrue(_is_block(self._from_checkout("gh pr merge 7")))


class PrePrGateLedgerKindTests(_LedgerCase):
    """#128 の対: 台帳に書く側（pre-PR gate）も、FIFO の台帳で待たない。"""

    def test_fifo_ledger_does_not_stall_pre_pr_gate(self):
        worktree = _init_named_repo(self.tmp, "pre-pr")
        _write_state(worktree, active=True)
        baseline = _run_pre_pr(worktree, self.home)
        ledger = _ledger(self.home)
        ledger.unlink()
        os.mkfifo(ledger)
        # FIFO の grep は待ち続けるので、壁時計の打ち切り（止まったときの保険）で TimeoutExpired にする。
        result = _run_pre_pr(worktree, self.home, timeout=hang_guard_seconds("run-pre-pr-gate-hook.sh"))
        self.assertEqual(result.returncode, baseline.returncode)
        self.assertEqual(result.stdout, baseline.stdout)


class UnresolvedSteeringTests(_LedgerCase):
    """steering が 1 件も解決できない（none）ときも、読めない steering があれば不足として通知する。

    読める steering の件数で、不足として通知する側と素通りが反転しないこと（対の両側）を確かめる。
    """

    def _repo(self, *, readable_other: bool, name: str = "widgets"):
        repo = _init_named_repo(self.tmp, name)
        _write_marker_only(repo, active=False, session_id=None)
        if readable_other:
            other = repo / ".steering" / "20260101-other"
            other.mkdir(parents=True)
            (other / "state.md").write_text(
                "## Gate Status\n- Resume From: done\n- Next Action: done\n"
                "- PR URL: https://github.com/acme/widgets/pull/1\n"
            )
        target = repo / ".steering" / "20260103-target"
        target.mkdir(parents=True)
        (target / "state.md").write_text(
            "## Gate Status\n- Resume From: done\n- Next Action: done\n"
            "- PR URL: https://github.com/acme/widgets/pull/7\n"
        )
        return repo, target

    def _assert_state_unreadable(self, repo):
        result = _hook("gh pr merge 7", repo, self.home)
        self.assertTrue(_is_block(result), result.stdout)
        self.assertIn("state-unreadable", result.stdout)

    def test_unsearchable_task_dir_blocks_with_or_without_a_readable_steering(self):
        for readable_other in (False, True):
            with self.subTest(readable_other=readable_other):
                repo, target = self._repo(readable_other=readable_other, name=f"widgets-{readable_other}")
                self._lock(target, 0o600)
                self._assert_state_unreadable(repo)

    def test_task_dir_without_read_permission_blocks(self):
        # x だけの task dir は `find` に拾われない。読めるとは扱わない。
        for readable_other in (False, True):
            with self.subTest(readable_other=readable_other):
                repo, target = self._repo(readable_other=readable_other, name=f"widgets-x-{readable_other}")
                self._lock(target, 0o311)
                self._assert_state_unreadable(repo)

    def test_unsearchable_steering_blocks(self):
        repo, _ = self._repo(readable_other=False)
        self._lock(repo / ".steering", 0o600)
        self._assert_state_unreadable(repo)

    def test_missing_or_readable_terminal_steering_still_passes(self):
        # `.steering` が無い形と、読める done の steering が別 PR だけの形は従来どおり通す。
        bare = _init_named_repo(self.tmp, "bare")
        _write_marker_only(bare, active=False, session_id=None)
        self.assertTrue(_is_pass(_hook("gh pr merge 7", bare, self.home)))
        repo, target = self._repo(readable_other=True)
        (target / "state.md").unlink()
        target.rmdir()
        self.assertTrue(_is_pass(_hook("gh pr merge 7", repo, self.home)))


class SuppressedLogKindTests(_LedgerCase):
    """抑止ログが通常ファイルでない（FIFO など）とき、書かずに先へ進む。"""

    def test_fifo_log_does_not_stall_the_demoted_marker_path(self):
        # 別セッションの `active: true` marker は降格され、ログを書いた後に証跡の検査へ進む。
        repo = _new_repo_with_marker_and_pr(self.tmp, "widgets", pr=7)
        _write_state(repo, active=True, session_id="other-session",
                     pr_url="https://github.com/acme/widgets/pull/7")
        baseline = _hook("gh pr merge 7", repo, self.home)
        self.assertTrue(_is_block(baseline), baseline.stdout)
        log = self.home / ".claude" / ".gdd-hook-state" / "merge-gate-suppressed.log"
        log.parent.mkdir(parents=True, exist_ok=True)
        if log.exists():
            log.unlink()
        os.mkfifo(log)
        result = _hook("gh pr merge 7", repo, self.home)
        self.assertTrue(_is_block(result), result.stdout)
        self.assertIn("approval-missing", result.stdout)


if __name__ == "__main__":
    unittest.main()
