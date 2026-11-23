"""steering が複数で 1 つに決まらないときの案内と、その案内で実際に解けることの契約。

案内は「使わない steering（PR が open のものは除く）の state.md で、Resume From と
Next Action をどちらも cancelled にする」。削除・移動はさせない。
- 移すと、PR が open の steering が merge gate の PR URL 照合から外れる
- `.steering/` の外へ移すと `.steering/` の ignore から外れ、git に見える未追跡ファイルになる

3 系統の検出（primary・pre-push の union・pre-PR の completed）は、どれも cancelled を
候補から外す。union は done・blocked をどちらの field でも拾うので、片方だけでは外れない。
"""
from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from _git_fixture import init_repo
from _merge_gate_support import _init_repo as _mg_init_repo
from _merge_gate_support import _run_hook as _mg_run_hook
from _merge_gate_support import _write_marker_only
from _paths import PLUGIN_ROOT

HOOKS = PLUGIN_ROOT / "hooks" / "scripts"
CANCEL_GUIDANCE = "Resume From と Next Action をどちらも cancelled"
# 別 session・別 runtime が作業中かもしれないので、agent が自分で選ばない（abandon-and-pause.md の規定）
USER_CONFIRM = "ユーザーに確認"
ACTIVE = ("gdd-implementation-gating", "gdd-implementation-gating")
DONE = ("gdd-completion-check", "done")
CANCELLED = ("cancelled", "cancelled")


class _Checkout(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(os.path.realpath(self._tmp.name))
        self.repo = self.tmp / "repo"
        self.repo.mkdir()
        init_repo(self.repo, branch="main")
        subprocess.run(["git", "switch", "-q", "-c", "feature"], cwd=self.repo, check=True)
        (self.repo / ".claude").mkdir()
        (self.repo / ".claude" / "gdd-dev.local.md").write_text(
            "---\nactive: true\nsession_id: test-session\n---\n", encoding="utf-8"
        )

    def _write(self, slug: str, values: tuple[str, str]) -> None:
        steering = self.repo / ".steering" / slug
        steering.mkdir(parents=True, exist_ok=True)
        (steering / "state.md").write_text(
            f"- Resume From: {values[0]}\n- Human Check Status: approved\n"
            f"- Route In Progress: none\n- Next Action: {values[1]}\n"
            "- Task Size: standard\n- Started At: 2026-09-24T00:00:00Z\n",
            encoding="utf-8",
        )

    def _env(self) -> dict[str, str]:
        env = os.environ.copy()
        env.update(
            {
                "HOME": str(self.tmp / "home"),
                "CLAUDE_PLUGIN_ROOT": str(PLUGIN_ROOT),
                "CLAUDE_CODE_SESSION_ID": "test-session",
                "GDD_HOOK_STATE_DIR": str(self.tmp / "hookstate"),
            }
        )
        env.pop("GDD_STEERING_DIR", None)
        env.pop("GDD_WORKTREES_ROOT", None)
        return env

    def _bash_tool(self, hook: str, command: str) -> str:
        payload = {"tool_name": "Bash", "tool_input": {"command": command}}
        result = subprocess.run(
            ["bash", str(HOOKS / hook)],
            cwd=self.repo, input=json.dumps(payload), capture_output=True, text=True,
            env=self._env(), check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def _push_reason(self) -> str:
        out = self._bash_tool("run-pre-push-gate-hook.sh", "git push origin feature")
        self.assertTrue(out, "検査されずに通った（fail-open）")
        payload = json.loads(out)
        self.assertEqual(payload["hookSpecificOutput"]["hookEventName"], "PreToolUse")
        return payload["hookSpecificOutput"]["additionalContext"]

    def _pr_reason(self) -> str:
        payload = json.loads(self._bash_tool("run-pre-pr-gate-hook.sh", "gh pr create --title t --body b"))
        self.assertEqual(payload["hookSpecificOutput"]["hookEventName"], "PreToolUse")
        return payload["hookSpecificOutput"]["additionalContext"]

    def _session_start_context(self) -> str:
        (self.tmp / "home").mkdir(exist_ok=True)
        env = self._env()
        env.pop("CLAUDE_CODE_SESSION_ID", None)
        env.pop("GDD_HOOK_STATE_DIR", None)
        result = subprocess.run(
            ["bash", str(HOOKS / "run-session-start-hook.sh")],
            cwd=self.repo, input="", capture_output=True, text=True, env=env, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"]


class PrePushGuidanceTests(_Checkout):
    def test_steering_multiple_points_to_the_cancel_procedure(self) -> None:
        """pre-push の不足の通知は ASCII の語を allow-list で縛るので、手順は参照先に置く。"""
        self._write("20260923-a", ACTIVE)
        self._write("20260924-b", ACTIVE)
        reason = self._push_reason()
        self.assertIn("steering-multiple", reason)
        self.assertIn("削除も移動もせず", reason)
        self.assertIn("references/self-review-lanes.md の「使わないステアリングの終え方」", reason)
        self.assertIn(USER_CONFIRM, reason)
        self.assertNotIn("別の場所へ移", reason)


class CancelResolvesMultipleTests(_Checkout):
    """案内どおりに片方を cancelled にすると、3 つの入口の multiple が解ける。"""

    def test_pre_push_resolves_to_the_remaining_steering(self) -> None:
        for label, kept in (("active", ACTIVE), ("done", DONE)):
            with self.subTest(kept=label):
                self.setUp()
                self._write("20260923-unused", CANCELLED)
                self._write("20260924-kept", kept)
                reason = self._push_reason()
                self.assertNotIn("steering-multiple", reason)
                self.assertIn("missing-evidence", reason)

    def test_pre_push_needs_both_fields(self) -> None:
        """片方の field だけ cancelled にしても、union は残りの done を拾って multiple のまま。"""
        self._write("20260923-unused", ("done", "cancelled"))
        self._write("20260924-kept", DONE)
        self.assertIn("steering-multiple", self._push_reason())

    def test_pre_pr_resolves_to_the_remaining_steering(self) -> None:
        for label, kept in (("active", ACTIVE), ("done", DONE)):
            with self.subTest(kept=label):
                self.setUp()
                self._write("20260923-unused", CANCELLED)
                self._write("20260924-kept", kept)
                out = self._bash_tool("run-pre-pr-gate-hook.sh", "gh pr create --title t --body b")
                self.assertNotIn(CANCEL_GUIDANCE, out)
                self.assertNotIn("一意に解決できません", out)

    def test_session_start_no_longer_warns(self) -> None:
        self._write("20260923-unused", CANCELLED)
        self._write("20260924-kept", ACTIVE)
        self.assertNotIn("[gdd:warning]", self._session_start_context())

    def test_session_start_and_pre_pr_give_the_same_guidance(self) -> None:
        self._write("20260923-a", ACTIVE)
        self._write("20260924-b", ACTIVE)
        for text in (self._session_start_context(), self._pr_reason()):
            self.assertIn(CANCEL_GUIDANCE, text)
            self.assertIn(USER_CONFIRM, text)


class StaleSteeringHelperTests(_Checkout):
    """stale steering の片付けの helper も、移動・削除ではなく cancelled を提案する。"""

    def test_default_mode_suggests_cancel_not_move_or_delete(self) -> None:
        (self.repo / ".gitignore").write_text(".steering/\n", encoding="utf-8")
        steering = self.repo / ".steering" / "20260101-old"
        steering.mkdir(parents=True)
        (steering / "state.md").write_text(
            "- Started At: 2026-01-01T00:00:00Z\n- Resume From: gdd-brainstorming\n"
            "- Human Check Status: pending\n- Route In Progress: none\n"
            "- Next Action: gdd-brainstorming\n",
            encoding="utf-8",
        )
        result = subprocess.run(
            ["bash", str(PLUGIN_ROOT / "scripts" / "find-stale-steerings.sh")],
            cwd=self.repo, capture_output=True, text=True, env=self._env(), check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("20260101-old", result.stdout)
        self.assertIn("Cancel 提案", result.stdout)
        self.assertIn(CANCEL_GUIDANCE, result.stdout)
        self.assertIn(USER_CONFIRM, result.stdout)
        for forbidden in ("mv ", "rm -rf", ".steering-archive", "Archive 提案", "Discard 提案"):
            self.assertNotIn(forbidden, result.stdout)


class MergeGateKeepsCancelledSteeringTests(unittest.TestCase):
    """cancelled にした steering も、PR URL の照合で merge gate の対象に残る（移すと外れる）。"""

    def test_cancelled_steering_with_target_pr_is_still_gated(self) -> None:
        tmp = Path(tempfile.mkdtemp())
        home = tmp / "home"
        (home / ".claude").mkdir(parents=True)
        repo = _mg_init_repo(tmp)
        _write_marker_only(repo, active=False, session_id="test-session")
        for slug, body in (
            ("20260924-active", "- Resume From: gdd-implementation-gating\n- Next Action: gdd-implementation-gating\n"
                                "- PR URL: https://github.com/acme/widgets/pull/9\n"),
            ("20260923-cancelled", "- Resume From: cancelled\n- Next Action: cancelled\n"
                                   "- PR URL: https://github.com/acme/widgets/pull/7\n"),
        ):
            steering = repo / ".steering" / slug
            steering.mkdir(parents=True)
            (steering / "state.md").write_text("## Gate Status\n" + body, encoding="utf-8")
        result = _mg_run_hook({"tool_input": {"command": "gh pr merge 7"}}, repo, home)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('"hookEventName": "PreToolUse"', result.stdout)
        self.assertIn("reason code: approval-missing", result.stdout)


if __name__ == "__main__":
    unittest.main()
