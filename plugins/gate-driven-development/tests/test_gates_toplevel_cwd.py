"""pre-push・pre-PR・merge gate と push 後の nudge が、payload の最上位の `cwd` で判定すること。

Claude Code の Bash の PreToolUse payload は、tool_input に cwd を持たず、最上位に `cwd` を持つ。
desktop の worktree のセッションでは、hook のプロセスの cwd が root checkout になる。4 つの hook は
最上位の `cwd` が使える（空でない絶対パスの文字列で、存在するディレクトリ）ときは、プロセスの
cwd をそこへ移してから判定する。使えるのは、空でない絶対パスの文字列で、タブ・改行・CR を
含まず、存在して中に入れる（実行権のある）ディレクトリのとき（`lib/hook_cwd.py`）。使えない
ときは今までどおりプロセスの cwd で判定する。
"""
from __future__ import annotations

import hashlib
import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from _git_fixture import init_repo
from _merge_gate_support import _new_repo_with_marker_and_pr
import test_pre_pr_gate_contract as _pre_pr_contract
from _paths import PLUGIN_ROOT
from _plugin_module_loader import load_plugin_module

sys.path.insert(0, str(PLUGIN_ROOT / "hooks" / "scripts" / "lib"))
import hook_cwd  # noqa: E402

SCRIPTS = PLUGIN_ROOT / "hooks" / "scripts"
PRE_PUSH = SCRIPTS / "run-pre-push-gate-hook.sh"
PRE_PR = SCRIPTS / "run-pre-pr-gate-hook.sh"
MERGE = SCRIPTS / "run-merge-gate-hook.sh"
NUDGE = SCRIPTS / "run-review-followup-nudge-hook.sh"
GUARD = load_plugin_module("hooks/scripts/validate-worktree-command.py")

_LEAKY_ENV = (
    "GH_HOST",
    "GH_REPO",
    "GDD_HOOK_STATE_DIR",
    "GDD_SKIP_PRE_PUSH_GATE",
    "GDD_REVIEW_FOLLOWUP_GH_BIN",
    "GDD_REVIEW_FOLLOWUP_GH_TIMEOUT",
    "GDD_REVIEW_FOLLOWUP_PR_CACHE_TTL",
    "GDD_REVIEW_FOLLOWUP_PR_UNKNOWN_TTL",
)


def _hash8(value: str) -> str:
    return hashlib.sha1(value.encode("utf-8")).hexdigest()[:8]


def _write_active_marker(repo: Path, session_id: str = "test-session") -> None:
    (repo / ".claude").mkdir(exist_ok=True)
    (repo / ".claude" / "gdd-dev.local.md").write_text(
        f"---\nactive: true\nsession_id: {session_id}\n---\n", encoding="utf-8"
    )


def _write_stub_gh(path: Path) -> None:
    path.write_text("#!/usr/bin/env bash\necho OPEN\nexit 0\n", encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IEXEC)


class _Base(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name).resolve()
        self.home = self.tmp / "home"
        self.home.mkdir()
        self.state_dir = self.tmp / "hookstate"
        # root checkout 役（hook のプロセスの cwd）と worktree 役（セッションの cwd）
        self.root = self.tmp / "root"
        self.root.mkdir()
        init_repo(self.root, branch="feature-x")
        self.wt = self.tmp / "wt"
        self.wt.mkdir()
        init_repo(self.wt, branch="feature-x")

    def tearDown(self) -> None:
        for path in self.tmp.rglob("*"):
            if path.is_dir() and not path.is_symlink():
                path.chmod(0o755)
        self._tmp.cleanup()

    def run_hook(self, hook: Path, payload: object, process_cwd: Path, extra_env=None):
        env = {k: v for k, v in os.environ.items() if k not in _LEAKY_ENV}
        env.update(
            {
                "HOME": str(self.home),
                "CLAUDE_PLUGIN_ROOT": str(PLUGIN_ROOT),
                "CLAUDE_CODE_SESSION_ID": "test-session",
                "GDD_HOOK_STATE_DIR": str(self.state_dir),
            }
        )
        if extra_env:
            env.update(extra_env)
        return subprocess.run(
            ["bash", str(hook)],
            cwd=str(process_cwd),
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            env=env,
            check=False,
            timeout=30,
        )

    @staticmethod
    def payload(
        command: str, top_cwd: object = None, tool_cwd: str | None = None, tool_cwd_key: str = "cwd"
    ) -> dict:
        # tool_input の実行先は tool_input.cwd、Codex は tool_input.workdir。hook はどちらも読む。
        tool_input = {"command": command}
        if tool_cwd is not None:
            tool_input[tool_cwd_key] = tool_cwd
        data: dict = {"tool_name": "Bash", "tool_input": tool_input}
        if top_cwd is not None:
            data["cwd"] = top_cwd
        return data

    def log_lines(self, name: str) -> list[str]:
        path = self.state_dir / name
        if not path.exists():
            return []
        return [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

    def assert_silent_pass(self, result) -> None:
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn('"hookEventName"', result.stdout)


class ToplevelCwdPredicateTests(unittest.TestCase):
    """受け入れの条件が、root branch guard（`extract_cwd`）と同じであること。"""

    def test_accepts_the_same_values_as_the_root_branch_guard(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw).resolve()
            process = tmp / "process"
            (process / "rel").mkdir(parents=True)
            target = tmp / "target"
            target.mkdir()
            newline_dir = tmp / "a\nb"
            newline_dir.mkdir()
            tab_mid = tmp / "a\tb"
            tab_mid.mkdir()
            tab_end = tmp / "tab-end\t"
            tab_end.mkdir()
            cr_dir = tmp / "a\rb"
            cr_dir.mkdir()
            locked = tmp / "locked"
            locked.mkdir()
            locked.chmod(0o600)
            cases = {
                "absolute dir": str(target),
                "relative dir that exists from the process cwd": "rel",
                "absent absolute path": str(tmp / "absent"),
                "empty": "",
                "number": 7,
                "list": [str(target)],
                "null": None,
                "newline in the path": str(newline_dir),
                "tab in the middle of the path": str(tab_mid),
                "tab at the end of the path": str(tab_end),
                "CR in the path": str(cr_dir),
                "directory without the execute bit": str(locked),
            }
            rejected = {
                "relative dir that exists from the process cwd",
                "absent absolute path",
                "empty",
                "number",
                "list",
                "null",
                "newline in the path",
                "tab in the middle of the path",
                "tab at the end of the path",
                "CR in the path",
            }
            if not os.access(locked, os.X_OK):
                rejected.add("directory without the execute bit")
            saved = os.getcwd()
            os.chdir(process)
            try:
                for label, value in cases.items():
                    with self.subTest(label):
                        payload = {"tool_input": {"command": "true"}, "cwd": value}
                        accepted = hook_cwd.toplevel_cwd(payload)
                        guard_cwd = GUARD.extract_cwd(payload)
                        guard_accepted = guard_cwd != process.resolve()
                        self.assertEqual(bool(accepted), guard_accepted, (accepted, guard_cwd))
                        if label in rejected:
                            self.assertEqual(accepted, "")
                        if accepted:
                            self.assertEqual(Path(accepted).resolve(), guard_cwd)
                self.assertEqual(hook_cwd.toplevel_cwd({"cwd": str(target)}), str(target))
            finally:
                os.chdir(saved)
                locked.chmod(0o755)

    def test_non_dict_payload_is_not_accepted(self) -> None:
        for payload in (None, [], "x", 3):
            with self.subTest(payload=payload):
                self.assertEqual(hook_cwd.toplevel_cwd(payload), "")


class PrePushGateToplevelCwdTests(_Base):
    def test_relative_git_dir_resolves_from_the_toplevel_cwd(self) -> None:
        """`--git-dir=../other/.git` は、最上位の cwd から解いたときだけ active な repo を指す。"""
        other = self.tmp / "other"
        other.mkdir()
        init_repo(other, branch="feature-x")
        _write_active_marker(other)
        deep = self.root / "a" / "b"
        deep.mkdir(parents=True)
        result = self.run_hook(
            PRE_PUSH, self.payload("git --git-dir=../other/.git push origin main", str(self.wt)), deep
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["hookSpecificOutput"]["hookEventName"], "PreToolUse")
        self.assertIn("unresolvable-root", result.stdout)

    def test_active_worktree_is_judged_even_when_the_process_cwd_is_root(self) -> None:
        _write_active_marker(self.wt, session_id="another-session")
        result = self.run_hook(PRE_PUSH, self.payload("git push origin main", str(self.wt)), self.root)
        self.assert_silent_pass(result)
        lines = self.log_lines("pre-push-optout.log")
        self.assertEqual(len(lines), 1, lines)
        self.assertIn("event: session-mismatch", lines[0])

    def test_tool_input_cwd_still_wins_over_the_toplevel_cwd(self) -> None:
        _write_active_marker(self.wt, session_id="another-session")
        for key in ("cwd", "workdir"):
            with self.subTest(key=key):
                # 前の subTest のログが残ると、どちらの key が壊れたかが分からなくなる。
                log = self.state_dir / "pre-push-optout.log"
                if log.exists():
                    log.unlink()
                result = self.run_hook(
                    PRE_PUSH,
                    self.payload("git push origin main", str(self.wt), tool_cwd=str(self.root), tool_cwd_key=key),
                    self.root,
                )
                self.assert_silent_pass(result)
                self.assertEqual(self.log_lines("pre-push-optout.log"), [])

    def test_unusable_toplevel_cwd_falls_back_to_the_process_cwd(self) -> None:
        inner = self.root / "inner"
        inner.mkdir()
        init_repo(inner, branch="feature-x")
        _write_active_marker(inner)
        for value in ("inner", str(self.tmp / "absent"), "", 7, [str(inner)], {"p": str(inner)}):
            with self.subTest(value=value):
                result = self.run_hook(
                    PRE_PUSH, self.payload("git --git-dir=.git push origin main", value), self.root
                )
                self.assert_silent_pass(result)

    def test_same_toplevel_and_process_cwd_keeps_the_old_behavior(self) -> None:
        result = self.run_hook(PRE_PUSH, self.payload("git push origin main", str(self.root)), self.root)
        self.assert_silent_pass(result)
        _write_active_marker(self.root)
        result = self.run_hook(
            PRE_PUSH, self.payload("git --git-dir=.git push origin main", str(self.root)), self.root
        )
        self.assertIn("unresolvable-root", result.stdout)

    def test_toplevel_cwd_that_cannot_be_entered_falls_back_to_the_process_cwd(self) -> None:
        _write_active_marker(self.root)
        self.wt.chmod(0o600)
        if os.access(self.wt, os.X_OK):
            self.skipTest("running with permissions that ignore the mode bits")
        result = self.run_hook(
            PRE_PUSH, self.payload("git --git-dir=.git push origin main", str(self.wt)), self.root
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("unresolvable-root", result.stdout)


class ReviewFollowupNudgeToplevelCwdTests(_Base):
    def setUp(self) -> None:
        super().setUp()
        self.gh = self.tmp / "gh-stub"
        _write_stub_gh(self.gh)
        self.env = {"GDD_REVIEW_FOLLOWUP_GH_BIN": str(self.gh)}

    def test_nudge_looks_up_the_pr_of_the_toplevel_cwd(self) -> None:
        result = self.run_hook(
            NUDGE, self.payload("git push origin feature-x", str(self.wt)), self.root, self.env
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        lines = self.log_lines("review-followup-nudge.log")
        self.assertEqual(len(lines), 1, lines)
        self.assertIn("event: injected", lines[0])
        self.assertIn(f"repo: {_hash8(str(self.wt))}", lines[0])

    def test_tool_input_cwd_comes_before_the_toplevel_cwd(self) -> None:
        for key in ("cwd", "workdir"):
            with self.subTest(key=key):
                log = self.state_dir / "review-followup-nudge.log"
                if log.exists():
                    log.unlink()
                result = self.run_hook(
                    NUDGE,
                    self.payload("git push origin feature-x", str(self.root), tool_cwd=str(self.wt), tool_cwd_key=key),
                    self.root,
                    self.env,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                lines = self.log_lines("review-followup-nudge.log")
                self.assertEqual(len(lines), 1, lines)
                self.assertIn(f"repo: {_hash8(str(self.wt))}", lines[0])

    def test_relative_cd_resolves_from_the_toplevel_cwd(self) -> None:
        (self.wt / "sub").mkdir()
        result = self.run_hook(
            NUDGE, self.payload("cd sub && git push origin feature-x", str(self.wt)), self.root, self.env
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        lines = self.log_lines("review-followup-nudge.log")
        self.assertEqual(len(lines), 1, lines)
        self.assertIn("event: injected", lines[0])

    def test_unusable_toplevel_cwd_falls_back_to_the_process_cwd(self) -> None:
        for value in ("wt", str(self.tmp / "absent"), 7):
            with self.subTest(value=value):
                if self.state_dir.exists():
                    for path in self.state_dir.rglob("*"):
                        if path.is_file():
                            path.unlink()
                result = self.run_hook(
                    NUDGE, self.payload("git push origin feature-x", value), self.root, self.env
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                lines = self.log_lines("review-followup-nudge.log")
                self.assertEqual(len(lines), 1, lines)
                self.assertIn(f"repo: {_hash8(str(self.root))}", lines[0])


class MergeGateToplevelCwdTests(_Base):
    def test_marker_repo_at_the_toplevel_cwd_is_gated(self) -> None:
        target = _new_repo_with_marker_and_pr(self.tmp, "marked", pr=7)
        result = self.run_hook(MERGE, self.payload("gh pr merge 7", str(target)), self.root)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('"hookEventName": "PreToolUse"', result.stdout)

    def test_trusted_candidate_moves_to_the_toplevel_cwd(self) -> None:
        """trusted の候補（今までのプロセスの cwd の位置）が最上位の cwd に移る。

        セッションの cwd は git の外で、cd を伴う merge は repo-root-unresolvable を不足として通知する。
        プロセスの cwd（root の下の深い場所）は marker の無い repo の中である。判定（stdout）
        は、セッションの cwd で hook を起動したときと一致しなければならない。
        """
        session = self.tmp / "session"
        session.mkdir()
        _new_repo_with_marker_and_pr(session, "marked", pr=7)
        deep = self.root / "a" / "b"
        deep.mkdir(parents=True)
        command = "cd marked && gh pr merge 7"
        expected = self.run_hook(MERGE, self.payload(command), session)
        self.assertIn('"hookEventName": "PreToolUse"', expected.stdout)
        result = self.run_hook(MERGE, self.payload(command, str(session)), deep)
        self.assertEqual(result.returncode, expected.returncode, result.stderr)
        self.assertEqual(result.stdout, expected.stdout)

    def assert_merge_silent(self, result) -> None:
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "")
        self.assertEqual(self.log_lines("merge-gate-suppressed.log"), [])

    def test_same_toplevel_and_process_cwd_keeps_the_old_behavior(self) -> None:
        result = self.run_hook(MERGE, self.payload("gh pr merge 7", str(self.root)), self.root)
        self.assert_merge_silent(result)

    def test_unusable_toplevel_cwd_falls_back_to_the_process_cwd(self) -> None:
        target = _new_repo_with_marker_and_pr(self.tmp, "marked", pr=7)
        for value in ("marked", str(self.tmp / "absent"), 7, [str(target)], ""):
            with self.subTest(value=value):
                result = self.run_hook(MERGE, self.payload("gh pr merge 7", value), self.root)
                self.assert_merge_silent(result)


class PrePrGateToplevelCwdTests(_Base):
    COMMAND = "gh pr create --title t --body b"

    _init_pr_repo = _pre_pr_contract.PrePrGateContractTests._init_repo
    _write_local_state = _pre_pr_contract.PrePrGateContractTests._write_local_state
    _write_steering = _pre_pr_contract.PrePrGateContractTests._write_steering
    _head_sha = _pre_pr_contract.PrePrGateContractTests._head_sha
    _independent_review_line = _pre_pr_contract.PrePrGateContractTests._independent_review_line

    def test_relative_body_file_is_read_from_the_toplevel_cwd(self) -> None:
        """相対の `--body-file` は最上位の cwd から読む（プロセスの cwd には無い）。"""
        repo = self.tmp / "pr-repo"
        repo.mkdir()
        self._init_pr_repo(repo)
        self._write_local_state(repo)
        self._write_steering(repo)
        (repo / "pr.md").write_text("safe body\n", encoding="utf-8")
        (repo / "feature.py").write_text("print(1)\n", encoding="utf-8")
        subprocess.run(["git", "add", "feature.py"], cwd=repo, check=True)
        subprocess.run(["git", "commit", "-q", "-m", "add feature"], cwd=repo, check=True)
        command = "gh pr create --title test --body-file pr.md"
        expected = self.run_hook(PRE_PR, self.payload(command), repo)
        self.assertEqual(expected.stdout, "")
        result = self.run_hook(PRE_PR, self.payload(command, str(repo)), self.root)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "")

    def test_active_worktree_at_the_toplevel_cwd_is_gated(self) -> None:
        _write_active_marker(self.wt)
        result = self.run_hook(PRE_PR, self.payload(self.COMMAND, str(self.wt)), self.root)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('"hookEventName": "PreToolUse"', result.stdout)

    def test_same_toplevel_and_process_cwd_keeps_the_old_behavior(self) -> None:
        result = self.run_hook(PRE_PR, self.payload(self.COMMAND, str(self.root)), self.root)
        self.assert_silent_pass(result)

    def test_tool_input_cwd_comes_before_the_toplevel_cwd(self) -> None:
        # 最上位の cwd（active な wt）で判定すると不足の通知が出る。tool_input の値（root）が先なら通知は出ない。
        _write_active_marker(self.wt)
        for key in ("cwd", "workdir"):
            with self.subTest(key=key):
                result = self.run_hook(
                    PRE_PR,
                    self.payload(self.COMMAND, str(self.wt), tool_cwd=str(self.root), tool_cwd_key=key),
                    self.root,
                )
                self.assert_silent_pass(result)

    def test_unusable_toplevel_cwd_falls_back_to_the_process_cwd(self) -> None:
        _write_active_marker(self.wt)
        for value in ("wt", str(self.tmp / "absent"), 7, None):
            with self.subTest(value=value):
                result = self.run_hook(PRE_PR, self.payload(self.COMMAND, value), self.root)
                self.assert_silent_pass(result)


if __name__ == "__main__":
    unittest.main()
