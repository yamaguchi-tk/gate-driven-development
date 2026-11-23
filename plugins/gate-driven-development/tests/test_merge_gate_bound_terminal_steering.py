"""worktree の binding が終端の steering を指すときの merge gate の契約テスト。

binding が cancelled の steering を指すと、resolver は binding の無い作業中の steering を数えず
`none/terminal-only` を返し、merge gate は承認の証跡を見ずに素通りしていた。resolver が
binding の無いときと同じ規則で作業中の steering を数え直すので、merge gate も同じ検査に進む。
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from _merge_gate_support import _head_sha, _init_repo, _run_hook, _write_marker_only
from _paths import PLUGIN_ROOT

PR_URL = "https://github.com/acme/widgets/pull/7"


class _MergeGateBoundFixture(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.home = self.tmp / "home"
        (self.home / ".claude").mkdir(parents=True)
        self.repo = _init_repo(self.tmp)
        self.head = _head_sha(self.repo)
        # done 後の最頻状態（marker は残るが active: false）。
        _write_marker_only(self.repo, active=False)
        branch = subprocess.run(
            ["git", "branch", "--show-current"], cwd=self.repo,
            capture_output=True, text=True, check=True,
        ).stdout.strip()
        self.bound = self._write(
            "20260901-bound", "cancelled",
            f"Task ID: 20260901-bound\nWorktree: {self.repo}\nBranch: {branch}\n",
        )

    def _write(self, slug: str, resume_from: str, extra: str = "") -> Path:
        steering = self.repo / ".steering" / slug
        steering.mkdir(parents=True, exist_ok=True)
        state = steering / "state.md"
        state.write_text(
            f"Resume From: {resume_from}\nNext Action: {resume_from}\nTask Size: standard\n{extra}",
            encoding="utf-8",
        )
        return state

    def _bind(self) -> None:
        subprocess.run(
            ["python3", str(PLUGIN_ROOT / "scripts" / "gdd_task_binding.py"), "upsert-from-state",
             "--repo-root", str(self.repo), "--state", str(self.bound)],
            cwd=self.repo, check=True, capture_output=True, text=True,
        )

    def _merge(self, command: str) -> str:
        result = _run_hook({"tool_input": {"command": command}}, self.repo, self.home)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout


class MergeGateBoundTerminalSteeringTests(_MergeGateBoundFixture):
    def test_active_steering_pr_is_gated_as_without_the_binding(self) -> None:
        """不足を通知すべき入力: 作業中の steering の PR を、承認の証跡なしに merge する。"""
        self._write("20260924-active", "gdd-pr-review", f"PR URL: {PR_URL}\n")
        with self.subTest(binding="none"):
            self.assertIn("approval-missing", self._merge("gh pr merge 7"))
        self._bind()
        with self.subTest(binding="cancelled"):
            self.assertIn("approval-missing", self._merge("gh pr merge 7"))

    def test_unreadable_active_state_blocks(self) -> None:
        """例外で guard が落ちない: 作業中の steering の state.md が読めなければ不足として通知する。"""
        if os.geteuid() == 0:
            self.skipTest("root は読み取り権限を無視する")
        state = self._write("20260924-active", "gdd-pr-review", f"PR URL: {PR_URL}\n")
        self._bind()
        state.chmod(0)
        self.addCleanup(state.chmod, 0o644)
        self.assertIn("state-unreadable", self._merge("gh pr merge 7"))

    def test_two_active_steerings_without_a_target_block(self) -> None:
        """判定できないときは不足として通知する: 作業中が 2 件で対象 PR を省くと steering-ambiguous。"""
        self._write("20260924-a", "gdd-pr-review", f"PR URL: {PR_URL}\n")
        self._write("20260925-b", "gdd-pr-review", "PR URL: https://github.com/acme/widgets/pull/8\n")
        self._bind()
        self.assertIn("steering-ambiguous", self._merge("gh pr merge"))

    def test_next_action_done_binding_is_chosen_by_the_target_pr(self) -> None:
        """binding 先が Next Action: done（Resume From は done 以外）で作業中の steering もあるとき、
        対象 PR を記録した binding 先で検査する。"""
        self.bound.write_text(
            self.bound.read_text(encoding="utf-8").replace(
                "Resume From: cancelled\nNext Action: cancelled\n",
                f"Resume From: gdd-pr-review\nNext Action: done\nPR URL: {PR_URL}\n",
            ),
            encoding="utf-8",
        )
        self._write("20260924-active", "gdd-pr-review", "PR URL: https://github.com/acme/widgets/pull/8\n")
        self._bind()
        self.assertIn("approval-missing", self._merge("gh pr merge 7"))

    def test_next_action_done_binding_with_an_active_one_needs_the_target_pr(self) -> None:
        """判定できないときは不足として通知する: binding 先が Next Action: done で作業中の steering もあるとき、
        対象 PR を省いた merge は steering-ambiguous で不足として通知する。"""
        self.bound.write_text(
            self.bound.read_text(encoding="utf-8").replace(
                "Resume From: cancelled\nNext Action: cancelled\n",
                f"Resume From: gdd-pr-review\nNext Action: done\nPR URL: {PR_URL}\n",
            ),
            encoding="utf-8",
        )
        self._write("20260924-active", "gdd-pr-review", "PR URL: https://github.com/acme/widgets/pull/8\n")
        self._bind()
        self.assertIn("steering-ambiguous", self._merge("gh pr merge"))

    def test_cancel_spelled_binding_without_active_steerings_is_still_gated(self) -> None:
        """不足を通知すべき入力: binding 先の Next Action だけが cancel（綴り違い）で作業中が無いとき、対象 PR を
        記録した binding 先を承認の証跡なしに merge させない（数え直す前と同じ）。"""
        self.bound.write_text(
            self.bound.read_text(encoding="utf-8").replace(
                "Resume From: cancelled\nNext Action: cancelled\n",
                f"Resume From: gdd-pr-review\nNext Action: Canceled\nPR URL: {PR_URL}\n",
            ),
            encoding="utf-8",
        )
        self._bind()
        self.assertIn("approval-missing", self._merge("gh pr merge 7"))

    def _outside_bound(self, next_action: str, dirname: str = "elsewhere") -> None:
        shutil.rmtree(self.repo / ".steering" / "20260901-bound", ignore_errors=True)
        outside = self.repo / dirname
        outside.mkdir(exist_ok=True)
        self.bound = outside / "state.md"
        branch = subprocess.run(
            ["git", "branch", "--show-current"], cwd=self.repo,
            capture_output=True, text=True, check=True,
        ).stdout.strip()
        self.bound.write_text(
            f"Resume From: gdd-pr-review\nNext Action: {next_action}\nTask Size: standard\n"
            f"PR URL: {PR_URL}\nTask ID: 20260901-outside\nWorktree: {self.repo}\nBranch: {branch}\n",
            encoding="utf-8",
        )
        self._bind()

    def test_bound_steering_outside_the_steering_dir_is_not_skipped_by_the_target_match(self) -> None:
        """判定できないときは不足として通知する: .steering/ の外の終端とみなした binding 先が対象 PR を記録し、作業中の
        steering もあるとき、.steering/ だけを探す対象 PR の照合で素通りさせない。"""
        self._write("20260924-active", "gdd-pr-review", "PR URL: https://github.com/acme/widgets/pull/8\n")
        for next_action in ("Canceled", "done"):
            with self.subTest(next_action=next_action):
                self._outside_bound(next_action)
                self.assertIn("steering-ambiguous", self._merge("gh pr merge 7"))

    def test_outside_bound_block_is_valid_json_without_the_path(self) -> None:
        """判定できないときも不足として通知する: binding 先のディレクトリ名に制御文字があっても、通知の出力は
        JSON として読め、reason に binding 先のパスを出さない（masking）。"""
        self._write("20260924-active", "gdd-pr-review", "PR URL: https://github.com/acme/widgets/pull/8\n")
        self._outside_bound("done", dirname="else\x1bwhere")
        payload = json.loads(self._merge("gh pr merge 7"))
        reason = payload["hookSpecificOutput"]["additionalContext"]
        self.assertIn("steering-ambiguous", reason)
        self.assertNotIn(str(self.repo), reason)

    def test_other_pr_merge_with_bound_steering_inside_still_passes(self) -> None:
        """通知しすぎない: binding 先が .steering/ の中にあれば、どちらの PR でもない merge は今どおり通す。"""
        self.bound.write_text(
            self.bound.read_text(encoding="utf-8").replace(
                "Resume From: cancelled\nNext Action: cancelled\n",
                f"Resume From: gdd-pr-review\nNext Action: Canceled\nPR URL: {PR_URL}\n",
            ),
            encoding="utf-8",
        )
        self._write("20260924-active", "gdd-pr-review", "PR URL: https://github.com/acme/widgets/pull/8\n")
        self._bind()
        self.assertNotIn('"hookEventName"', self._merge("gh pr merge 9"))

    def test_only_terminal_steerings_still_pass(self) -> None:
        self._write("20260920-old", "cancelled")
        self._bind()
        self.assertNotIn('"hookEventName"', self._merge("gh pr merge 7"))



class MergeGateTerminalSteeringWithTargetPrTests(_MergeGateBoundFixture):
    """終端の steering だけが残る checkout でも、対象 PR を記録した steering は merge gate の対象に残す。

    中止した steering（cancelled）だけが残ると resolver は `none/terminal-only` を返し、merge gate は
    承認の証跡を見ずに素通りしていた。binding の経路が `Next Action: cancelled` だけの中止を終端に
    した後は、binding 先が対象 PR を記録していても素通りになっていた。
    """

    def _bound_with_pr(self, resume_from: str, next_action: str) -> None:
        lines = [line for line in self.bound.read_text(encoding="utf-8").splitlines(keepends=True)
                 if not line.startswith(("Resume From:", "Next Action:", "PR URL:"))]
        self.bound.write_text(
            f"Resume From: {resume_from}\nNext Action: {next_action}\n{''.join(lines)}PR URL: {PR_URL}\n",
            encoding="utf-8",
        )
        self._bind()

    def test_bound_cancelled_steering_with_the_pr_is_gated(self) -> None:
        """不足を通知すべき入力: 対象 PR を記録した中止の steering の PR を、承認の証跡なしに merge する。"""
        for resume_from, next_action in (("external-review-waiting", "cancelled"), ("cancelled", "cancelled")):
            with self.subTest(resume_from=resume_from, next_action=next_action):
                self._bound_with_pr(resume_from, next_action)
                self.assertIn("approval-missing", self._merge("gh pr merge 7"))
                self.assertIn("approval-missing", self._merge(f"gh pr merge {PR_URL}"))

    def test_unbound_cancelled_steering_with_the_pr_is_gated(self) -> None:
        self._write("20260920-old", "cancelled", f"PR URL: {PR_URL}\n")
        self.assertIn("approval-missing", self._merge("gh pr merge 7"))

    def test_merge_without_a_target_is_ambiguous(self) -> None:
        """判定できないときは不足として通知する: 対象 PR を決められない merge は、PR を記録した steering があれば不足として通知する。

        binding 先は `Resume From: cancelled`（候補から外れ、候補が 0 件になる形）にする。
        """
        self._bound_with_pr("cancelled", "cancelled")
        for command in ("gh pr merge", "gh pr merge feature-x"):
            with self.subTest(command=command):
                self.assertIn("steering-ambiguous", self._merge(command))

    def test_unreadable_steering_blocks(self) -> None:
        """例外で guard が落ちない: 中止の steering の state.md が読めなければ不足として通知する。"""
        if os.geteuid() == 0:
            self.skipTest("root は読み取り権限を無視する")
        self._bound_with_pr("external-review-waiting", "cancelled")
        self.bound.chmod(0)
        self.addCleanup(self.bound.chmod, 0o644)
        self.assertIn("state-unreadable", self._merge("gh pr merge 7"))

    def test_other_pr_and_steerings_without_a_pr_still_pass(self) -> None:
        """通知しすぎない: 別の PR の merge と、どの steering も PR を記録していない checkout は通す。"""
        self._bound_with_pr("external-review-waiting", "cancelled")
        self.assertNotIn('"hookEventName"', self._merge("gh pr merge 8"))


if __name__ == "__main__":
    unittest.main()
