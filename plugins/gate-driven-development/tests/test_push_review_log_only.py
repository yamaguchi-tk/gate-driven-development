"""PR がある branch への push を、レビュー済みの tip かどうかで判定してログに書く（log-only）。

経路は 2 つの hook でできている。

- SessionStart の `run-push-review-env-hook.sh` が `$CLAUDE_ENV_FILE` に、git の設定による
  pre-push hook（`hook.gdd-push-review.*` を `GIT_CONFIG_*` で渡す）と transcript のパスを書く
- git が push の直前に `git-pre-push-review-hook.sh` を呼ぶ。stdin の
  `<local ref> <local sha> <remote ref> <remote sha>` を読み、PR が OPEN なら transcript を見て、
  tip の commit 時刻より後に reviewer の Agent が起動して成功で終わっているかを判定し、ログに 1 行書く

log-only なので、どの判定でも push は止めない。git の hook のテストは、env file を source した
shell で本物の `git push` を打ち、ログの判定と push の成否を見る。remote は
`https://github.com/o/r.git` として登録し、`insteadOf` で手元の bare repo に送る。
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path

from _paths import PLUGIN_ROOT
from _git_fixture import init_repo

SCRIPTS = PLUGIN_ROOT / "hooks" / "scripts"
SESSION_HOOK = SCRIPTS / "run-push-review-env-hook.sh"
GIT_HOOK = SCRIPTS / "git-pre-push-review-hook.sh"
HOOKS_JSON = PLUGIN_ROOT / "hooks" / "hooks.json"

COMMIT_DATE = "2026-01-01T00:00:00+00:00"
BEFORE_COMMIT = "2025-12-31T00:00:00.000Z"
SAME_SECOND_AS_COMMIT = "2026-01-01T00:00:00.500Z"
AFTER_COMMIT = "2026-01-02T00:00:00.000Z"
LATER_COMMIT_DATE = "2026-01-03T00:00:00+00:00"
GITHUB_URL = "https://github.com/o/r.git"


def _config_hooks_supported() -> bool:
    """git が設定による hook（`hook.<name>.event`）を実行するか。"""
    with tempfile.TemporaryDirectory(prefix="gdd-prv-probe-") as tmp:
        root = Path(tmp)
        subprocess.run(["git", "init", "-q", "--bare", str(root / "r.git")], check=True)
        (root / "w").mkdir()
        init_repo(root / "w")
        marker = root / "ran"
        env = {
            **os.environ,
            "GIT_CONFIG_COUNT": "2",
            "GIT_CONFIG_KEY_0": "hook.probe.event",
            "GIT_CONFIG_VALUE_0": "pre-push",
            "GIT_CONFIG_KEY_1": "hook.probe.command",
            "GIT_CONFIG_VALUE_1": f"touch '{marker}'",
        }
        subprocess.run(
            ["git", "push", "-q", str(root / "r.git"), "HEAD:refs/heads/p"],
            cwd=root / "w", env=env, capture_output=True,
        )
        return marker.exists()


CONFIG_HOOKS = _config_hooks_supported()


def _assistant_launch(tool_use_id: str, subagent_type: str, ts: str, background: bool = False) -> dict:
    inp = {"subagent_type": subagent_type, "description": "d", "prompt": "p"}
    if background:
        inp["run_in_background"] = True
    return {
        "type": "assistant",
        "timestamp": ts,
        "message": {"content": [{"type": "tool_use", "id": tool_use_id, "name": "Agent", "input": inp}]},
    }


def _tool_result(tool_use_id: str, text: str, ts: str, is_error: bool = False) -> dict:
    block = {"type": "tool_result", "tool_use_id": tool_use_id, "content": text}
    if is_error:
        block["is_error"] = True
    return {"type": "user", "timestamp": ts, "message": {"content": [block]}}


def _notification(agent_id: str, tool_use_id: str, ts: str, status: str = "completed") -> dict:
    body = (
        f"<task-notification><task-id>{agent_id}</task-id><tool-use-id>{tool_use_id}</tool-use-id>"
        f"<status>{status}</status><summary>s</summary></task-notification>"
    )
    return {"type": "user", "timestamp": ts, "message": {"content": [{"type": "text", "text": body}]}}


def _sync_review(ts: str = AFTER_COMMIT, subagent_type: str = "light-lane-independent-reviewer") -> list[dict]:
    return [_assistant_launch("toolu_r1", subagent_type, ts), _tool_result("toolu_r1", "high=0", ts)]


def _background_launch(ts: str = AFTER_COMMIT) -> list[dict]:
    ack = "Async agent launched successfully.\nagentId: agent-x\n"
    return [
        _assistant_launch("toolu_bg", "light-lane-independent-reviewer", ts, background=True),
        _tool_result("toolu_bg", ack, ts),
    ]


class _PushReviewFixture:
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="gdd-prv-")
        self.root = Path(self._tmp.name)
        self.remote = self.root / "remote.git"
        subprocess.run(["git", "init", "-q", "--bare", str(self.remote)], check=True)
        self.repo = self.root / "repo"
        self.repo.mkdir()
        init_repo(self.repo, commit_date=COMMIT_DATE)
        self._git("remote", "add", "origin", GITHUB_URL)
        self._git("config", f"url.{self.remote}.insteadOf", GITHUB_URL)
        self.state_dir = self.root / "state"
        self.env_file = self.root / "env.sh"
        self.transcript = self.root / "t.jsonl"
        self.transcript.write_text("", encoding="utf-8")
        self.gh = self.root / "gh"
        self.gh_args = self.root / "gh-args"
        self._write_gh("1")
        self.home = self.root / "home"
        self.home.mkdir()

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _git(self, *args: str, env: dict | None = None) -> str:
        return subprocess.run(
            ["git", *args], cwd=self.repo, check=True, capture_output=True, text=True,
            env={**os.environ, **(env or {})},
        ).stdout.strip()

    def _commit(self, path: str, date: str = LATER_COMMIT_DATE, content: str | None = None) -> None:
        target = self.repo / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content if content is not None else path + "\n", encoding="utf-8")
        self._git("add", path)
        self._git("commit", "-q", "-m", path, env={"GIT_AUTHOR_DATE": date, "GIT_COMMITTER_DATE": date})

    def _write_gh(self, out: str | None, rc: int = 0) -> None:
        echo = f'echo "{out}"' if out is not None else ":"
        self.gh.write_text(
            f'#!/usr/bin/env bash\nprintf "%s\\n" "$*" >> "{self.gh_args}"\n{echo}\nexit {rc}\n',
            encoding="utf-8",
        )
        self.gh.chmod(0o755)

    def _write_transcript(self, records: list[dict]) -> None:
        self.transcript.write_text("".join(json.dumps(r) + "\n" for r in records), encoding="utf-8")

    def _env(self, extra: dict | None = None) -> dict:
        env = {
            k: v for k, v in os.environ.items()
            if not k.startswith(("GIT_CONFIG_", "GDD_PUSH_REVIEW")) and k != "CLAUDE_ENV_FILE"
        }
        env.update({
            "HOME": str(self.home),
            "GDD_HOOK_STATE_DIR": str(self.state_dir),
            "GDD_PUSH_REVIEW_GH_BIN": str(self.gh),
        })
        env.update(extra or {})
        return env

    def _run_session_hook(self, payload: dict | None = None, extra: dict | None = None) -> subprocess.CompletedProcess:
        if payload is None:
            payload = {"session_id": "s1", "transcript_path": str(self.transcript), "source": "startup"}
        return subprocess.run(
            ["bash", str(SESSION_HOOK)], input=json.dumps(payload), capture_output=True, text=True,
            env=self._env({"CLAUDE_ENV_FILE": str(self.env_file), **(extra or {})}), timeout=30,
        )

    def _push(
        self, command: str = "git push origin HEAD:refs/heads/feature",
        extra: dict | None = None, shell: str = "bash",
    ) -> subprocess.CompletedProcess:
        script = f'source "{self.env_file}"\n{command}\n' if self.env_file.exists() else f"{command}\n"
        return subprocess.run(
            [shell, "-c", script], cwd=self.repo, capture_output=True, text=True, errors="replace",
            env=self._env(extra), timeout=60,
        )

    def _log_lines(self) -> list[str]:
        log = self.state_dir / "push-review.log"
        return log.read_text(encoding="utf-8").splitlines() if log.exists() else []

    def _clear_log(self) -> None:
        (self.state_dir / "push-review.log").unlink(missing_ok=True)

    def _env_file_text(self) -> str:
        return self.env_file.read_text(encoding="utf-8") if self.env_file.exists() else ""


class PushReviewSessionHookTests(_PushReviewFixture, unittest.TestCase):
    """SessionStart の hook だけで決まること（git の版に依らない）。"""

    def test_git_supports_config_hooks_in_ci(self) -> None:
        # CI で git が設定による hook を持たないと、下の git の hook のテストが全部 skip になり、
        # 何も確かめずに緑になる
        if os.environ.get("CI"):
            self.assertTrue(CONFIG_HOOKS, "CI の git が設定による hook（hook.<name>.event）に対応していない")

    def test_kill_switch_writes_nothing(self) -> None:
        (self.home / ".claude").mkdir()
        (self.home / ".claude" / "gdd-hooks-disabled").write_text("", encoding="utf-8")
        self.assertEqual(self._run_session_hook().returncode, 0)
        self.assertEqual(self._env_file_text().strip(), "")

    def test_non_json_payload_writes_nothing(self) -> None:
        result = subprocess.run(
            ["bash", str(SESSION_HOOK)], input="not json", capture_output=True, text=True,
            env=self._env({"CLAUDE_ENV_FILE": str(self.env_file)}), timeout=30,
        )
        self.assertEqual(result.returncode, 0)
        self.assertEqual(self._env_file_text().strip(), "")

    def test_without_claude_env_file_writes_nowhere(self) -> None:
        sentinel_dir = self.root / "cwd"
        sentinel_dir.mkdir()
        result = subprocess.run(
            ["bash", str(SESSION_HOOK)], input=json.dumps({"transcript_path": str(self.transcript)}),
            capture_output=True, text=True, env=self._env(), cwd=sentinel_dir, timeout=30,
        )
        self.assertEqual(result.returncode, 0)
        self.assertFalse(self.env_file.exists())
        self.assertEqual(list(sentinel_dir.iterdir()), [])

    def test_unsafe_transcript_path_is_not_written_and_is_logged(self) -> None:
        bad = self.root / "a'b.jsonl"
        self._run_session_hook({"session_id": "s1", "transcript_path": str(bad), "source": "startup"})
        self.assertEqual(self._env_file_text().strip(), "")
        lines = self._log_lines()
        self.assertEqual(len(lines), 1, lines)
        self.assertIn("verdict: not-installed | reason: unsafe-path", lines[0])
        expected = hashlib.sha1(bad.stem.encode("utf-8")).hexdigest()[:8]
        self.assertIn(f"session: {expected}", lines[0])
        self._run_session_hook({"session_id": "s1", "transcript_path": str(bad), "source": "compact"})
        self.assertEqual(len(self._log_lines()), 1)


@unittest.skipUnless(CONFIG_HOOKS, "git が設定による hook（hook.<name>.event）に対応していない")
class PushReviewGitHookTests(_PushReviewFixture, unittest.TestCase):
    def _verdict(self) -> str:
        lines = self._log_lines()
        self.assertEqual(len(lines), 1, lines)
        return lines[0]

    def _session_and_push(self, command: str = "git push origin HEAD:refs/heads/feature") -> subprocess.CompletedProcess:
        self.assertEqual(self._run_session_hook().returncode, 0)
        result = self._push(command)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result

    def _declare_exempt(self, config: str, date: str = COMMIT_DATE) -> None:
        self._commit(".gdd-config.md", date=date, content=config)

    # --- 判定 ---------------------------------------------------------------
    def test_push_without_review_is_logged_as_would_deny_and_still_pushed(self) -> None:
        self._session_and_push()
        self.assertIn("verdict: would-deny | reason: no-reviewer", self._verdict())
        self.assertIn("refs/heads/feature", self._git("ls-remote", str(self.remote)))

    def test_gh_is_asked_for_open_prs_of_the_branch_in_the_remote_repo(self) -> None:
        self._session_and_push()
        args = self.gh_args.read_text(encoding="utf-8").split()
        self.assertEqual(args[:2], ["pr", "list"])
        self.assertEqual(args[args.index("--repo") + 1], "o/r")
        self.assertEqual(args[args.index("--head") + 1], "feature")
        self.assertEqual(args[args.index("--state") + 1], "open")
        self.assertEqual(args[args.index("--json") + 1], "number")
        self.assertEqual(args[args.index("--jq") + 1], "length")

    def test_reviewer_succeeded_after_tip_commit_is_reviewed(self) -> None:
        self._write_transcript(_sync_review())
        self._session_and_push()
        line = self._verdict()
        self.assertIn("verdict: reviewed |", line)
        self.assertIn(f"by: light-lane-independent-reviewer@{AFTER_COMMIT}", line)

    def test_listed_reviewers_count_with_or_without_plugin_prefix(self) -> None:
        for i, name in enumerate([
            "light-lane-independent-reviewer-xhigh",
            "gate-driven-development:gdd-implementation-reviewer",
            "gate-driven-development:gdd-completion-reviewer",
            "gate-driven-development:gdd-security-reviewer",
            "superpowers:code-reviewer",
        ]):
            with self.subTest(name):
                self._clear_log()
                self._write_transcript(_sync_review(subagent_type=name))
                self._run_session_hook()
                result = self._push(f"git push origin HEAD:refs/heads/r{i}")
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("verdict: reviewed |", self._verdict())

    def test_unlisted_agent_names_do_not_count(self) -> None:
        for i, name in enumerate([
            "gate-driven-development:gdd-planning-reviewer",
            "previewer",
            "general-purpose",
            "",
        ]):
            with self.subTest(name):
                self._clear_log()
                self._write_transcript(_sync_review(subagent_type=name))
                self._run_session_hook()
                result = self._push(f"git push origin HEAD:refs/heads/u{i}")
                self.assertEqual(result.returncode, 0, result.stderr)
                line = self._verdict()
                self.assertIn("verdict: would-deny | reason: other-agent-only", line)
                self.assertIn(f"agents: {name or '-'}", line)

    def test_background_reviewer_counts_only_after_a_completed_notification(self) -> None:
        cases = [
            ("通知の前", [], "verdict: would-deny | reason: reviewer-incomplete"),
            ("completed", [_notification("agent-x", "toolu_bg", AFTER_COMMIT)], "verdict: reviewed |"),
            ("failed", [_notification("agent-x", "toolu_bg", AFTER_COMMIT, "failed")],
             "verdict: would-deny | reason: reviewer-failed"),
            ("killed", [_notification("agent-x", "toolu_bg", AFTER_COMMIT, "killed")],
             "verdict: would-deny | reason: reviewer-failed"),
        ]
        self._run_session_hook()
        for i, (name, extra, expected) in enumerate(cases):
            with self.subTest(name):
                self._clear_log()
                self._write_transcript(_background_launch() + extra)
                result = self._push(f"git push origin HEAD:refs/heads/bg{i}")
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn(expected, self._verdict())

    def test_background_reviewer_stopped_by_task_stop(self) -> None:
        """TaskStop で host が「動いていない」と答えた reviewer は失敗、拒否などのエラーなら動いているものとする。"""
        stop = {"type": "assistant", "timestamp": AFTER_COMMIT, "message": {"content": [
            {"type": "tool_use", "id": "toolu_stop", "name": "TaskStop", "input": {"task_id": "agent-x"}}]}}
        cases = [
            ("No task found", "<tool_use_error>No task found with ID: agent-x</tool_use_error>",
             "verdict: would-deny | reason: reviewer-failed"),
            ("拒否", "Permission for this action was denied by the Claude Code auto mode classifier.",
             "verdict: would-deny | reason: reviewer-incomplete"),
        ]
        self._run_session_hook()
        for i, (name, text, expected) in enumerate(cases):
            with self.subTest(name):
                self._clear_log()
                self._write_transcript(_background_launch() + [
                    stop, _tool_result("toolu_stop", text, AFTER_COMMIT, is_error=True)])
                result = self._push(f"git push origin HEAD:refs/heads/ts{i}")
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn(expected, self._verdict())

    def test_sync_reviewer_without_result_is_incomplete(self) -> None:
        self._write_transcript([_assistant_launch("toolu_r1", "light-lane-independent-reviewer", AFTER_COMMIT)])
        self._session_and_push()
        self.assertIn("verdict: would-deny | reason: reviewer-incomplete", self._verdict())

    def test_sync_reviewer_with_error_result_is_failed(self) -> None:
        self._write_transcript([
            _assistant_launch("toolu_r1", "light-lane-independent-reviewer", AFTER_COMMIT),
            _tool_result("toolu_r1", "Agent type 'light-lane-independent-reviewer' not found", AFTER_COMMIT, is_error=True),
        ])
        self._session_and_push()
        self.assertIn("verdict: would-deny | reason: reviewer-failed", self._verdict())

    def test_reviewer_before_or_in_same_second_as_tip_commit_does_not_count(self) -> None:
        for i, ts in enumerate([BEFORE_COMMIT, SAME_SECOND_AS_COMMIT]):
            with self.subTest(ts):
                self._clear_log()
                self._write_transcript(_sync_review(ts=ts))
                self._run_session_hook()
                result = self._push(f"git push origin HEAD:refs/heads/t{i}")
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("verdict: would-deny | reason: changed-after-review", self._verdict())

    def test_only_exempt_paths_after_review_are_exempt(self) -> None:
        self._declare_exempt("# config\n\nGDD Push Review Exempt Paths: review-log/ plugins/*/changelog.d/\n")
        self._write_transcript(_sync_review())
        self._commit("review-log/x.md")
        self._commit("plugins/p/changelog.d/y.md")
        self._session_and_push()
        self.assertIn("verdict: exempt-only |", self._verdict())

    def test_code_change_after_review_is_would_deny_even_with_exempt_declaration(self) -> None:
        self._declare_exempt("GDD Push Review Exempt Paths: review-log/\n")
        self._write_transcript(_sync_review())
        self._commit("review-log/x.md")
        self._commit("src/app.py")
        self._session_and_push()
        self.assertIn("verdict: would-deny | reason: changed-after-review", self._verdict())

    def test_exempt_declaration_added_after_review_is_not_used(self) -> None:
        self._write_transcript(_sync_review())
        self._declare_exempt("GDD Push Review Exempt Paths: review-log/ .gdd-config.md\n", date=LATER_COMMIT_DATE)
        self._commit("review-log/x.md")
        self._session_and_push()
        self.assertIn("verdict: would-deny | reason: changed-after-review", self._verdict())

    def test_exempt_declaration_outside_plain_lines_or_malformed_is_ignored(self) -> None:
        line = "GDD Push Review Exempt Paths: review-log/"
        for name, config in [
            ("fence", f"```\n{line}\n```\n"),
            ("HTML コメント", f"<!--\n{line}\n-->\n"),
            ("インデントコード", f"    {line}\n"),
            ("引用", f"> {line}\n"),
            ("不正な値", f"{line} ../x\n"),
            ("全体を除く値", f"{line} .\n"),
            ("2 行", f"{line}\nGDD Push Review Exempt Paths: docs/\n"),
        ]:
            with self.subTest(name):
                self.tearDown()
                self.setUp()
                self._declare_exempt(config)
                self._write_transcript(_sync_review())
                self._commit("review-log/x.md")
                self._session_and_push()
                self.assertIn("verdict: would-deny | reason: changed-after-review", self._verdict())

    def test_branch_without_open_pr_is_no_pr(self) -> None:
        self._write_gh("0")
        self._session_and_push()
        self.assertIn("verdict: no-pr |", self._verdict())

    def test_gh_failure_or_unreadable_output_is_unknown_not_reviewed(self) -> None:
        self._write_transcript(_sync_review())
        self._run_session_hook()
        for i, (name, (out, rc)) in enumerate({
            "エラー": ("x", 1), "空の出力": (None, 0), "数でない": ("OPEN", 0),
        }.items()):
            with self.subTest(name):
                self._clear_log()
                self._write_gh(out, rc)
                result = self._push(f"git push origin HEAD:refs/heads/g{i}")
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("verdict: gh-unknown |", self._verdict())

    def test_gh_that_is_not_an_absolute_path_is_not_run(self) -> None:
        self._run_session_hook()
        result = self._push(extra={"GDD_PUSH_REVIEW_GH_BIN": "gh-relative"})
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("verdict: gh-unknown |", self._verdict())
        self.assertFalse(self.gh_args.exists())

    def test_non_github_remote_is_not_asked_to_gh(self) -> None:
        self._git("remote", "add", "mirror", "https://gitlab.example.com/o/r.git")
        self._git("config", f"url.{self.remote}.insteadOf", "https://gitlab.example.com/o/r.git", "--add")
        self._run_session_hook()
        for i, command in enumerate([
            "git push mirror HEAD:refs/heads/feature",
            f"git push {self.remote} HEAD:refs/heads/other",
        ]):
            with self.subTest(command):
                self._clear_log()
                result = self._push(command)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("verdict: not-github |", self._verdict())
        self.assertFalse(self.gh_args.exists())

    def test_missing_transcript_is_no_transcript(self) -> None:
        self._run_session_hook({"session_id": "s1", "transcript_path": str(self.root / "none.jsonl"), "source": "startup"})
        result = self._push()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("verdict: no-transcript |", self._verdict())

    def test_branch_deletion_is_not_logged(self) -> None:
        self._session_and_push()
        self._clear_log()
        result = self._push("git push origin :refs/heads/feature")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self._log_lines(), [])

    def test_refs_beyond_the_limit_are_logged_as_one_skipped_line(self) -> None:
        for i in range(12):
            self._git("branch", f"b{i:02d}")
        self._session_and_push("git push origin --all")
        lines = self._log_lines()
        self.assertEqual(len(lines), 11, lines)
        self.assertEqual(sum("verdict: skipped | reason: ref-limit" in line for line in lines), 1)

    def test_log_line_has_session_and_owner_only_permissions(self) -> None:
        self._session_and_push()
        self.assertIn("| session: ", self._verdict())
        log = self.state_dir / "push-review.log"
        self.assertEqual(stat.S_IMODE(log.stat().st_mode), 0o600)

    def test_background_reviewer_with_unreadable_launch_ack_is_not_reviewed(self) -> None:
        self._write_transcript([
            _assistant_launch("toolu_bg", "light-lane-independent-reviewer", AFTER_COMMIT, background=True),
            _tool_result("toolu_bg", "launched in some new wording", AFTER_COMMIT),
        ])
        self._session_and_push()
        self.assertIn("verdict: would-deny | reason: reviewer-incomplete", self._verdict())

    def test_background_reviewer_with_unreadable_launch_ack_follows_its_notification(self) -> None:
        launch = [
            _assistant_launch("toolu_bg", "light-lane-independent-reviewer", AFTER_COMMIT, background=True),
            _tool_result("toolu_bg", "launched in some new wording", AFTER_COMMIT),
        ]
        self._run_session_hook()
        for i, (status, expected) in enumerate([
            ("completed", "verdict: reviewed |"),
            ("failed", "verdict: would-deny | reason: reviewer-failed"),
        ]):
            with self.subTest(status):
                self._clear_log()
                self._write_transcript(launch + [_notification("agent-y", "toolu_bg", AFTER_COMMIT, status)])
                result = self._push(f"git push origin HEAD:refs/heads/n{i}")
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn(expected, self._verdict())

    def test_unreadable_gdd_config_is_treated_as_no_declaration(self) -> None:
        self._commit(".gdd-config.md", date=COMMIT_DATE, content="x")
        (self.repo / ".gdd-config.md").write_bytes(b"\xff\xfe GDD Push Review Exempt Paths: review-log/\n")
        self._git("add", ".gdd-config.md")
        self._git("commit", "-q", "-m", "c", env={"GIT_AUTHOR_DATE": COMMIT_DATE, "GIT_COMMITTER_DATE": COMMIT_DATE})
        self._write_transcript(_sync_review())
        self._commit("review-log/x.md")
        self._session_and_push()
        self.assertIn("verdict: would-deny | reason: changed-after-review", self._verdict())

    def test_gh_output_that_is_not_utf8_is_unknown(self) -> None:
        self.gh.write_text("#!/usr/bin/env bash\nprintf '\\377'\n", encoding="utf-8")
        self._session_and_push()
        self.assertIn("verdict: gh-unknown |", self._verdict())

    def test_running_reviewer_after_tip_does_not_hide_exempt_only(self) -> None:
        self._declare_exempt("GDD Push Review Exempt Paths: review-log/\n")
        self._commit("review-log/x.md")
        self._write_transcript(_sync_review(ts="2026-01-04T00:00:00.000Z") + [
            _assistant_launch("toolu_bg", "light-lane-independent-reviewer", "2026-01-06T00:00:00.000Z", background=True),
            _tool_result("toolu_bg", "Async agent launched successfully.\nagentId: agent-y\n", "2026-01-06T00:00:00.000Z"),
        ])
        self._commit("review-log/y.md", date="2026-01-05T00:00:00+00:00")
        self._session_and_push()
        self.assertIn("verdict: exempt-only |", self._verdict())

    def test_commit_in_the_same_second_as_the_review_is_not_treated_as_reviewed(self) -> None:
        self._declare_exempt("GDD Push Review Exempt Paths: review-log/\n")
        self._commit("src/app.py", date="2026-01-04T00:00:10+00:00")
        self._write_transcript(_sync_review(ts="2026-01-04T00:00:10.500Z"))
        self._commit("review-log/x.md", date="2026-01-04T00:00:20+00:00")
        self._session_and_push()
        self.assertIn("verdict: would-deny | reason: changed-after-review", self._verdict())

    def test_pushurl_wins_over_url(self) -> None:
        self._git("remote", "add", "up", "https://github.com/up/r.git")
        self._git("remote", "set-url", "--push", "up", GITHUB_URL)
        self._run_session_hook()
        result = self._push("git push up HEAD:refs/heads/feature")
        self.assertEqual(result.returncode, 0, result.stderr)
        args = self.gh_args.read_text(encoding="utf-8").split()
        self.assertEqual(args[args.index("--repo") + 1], "o/r")

    def test_github_url_with_non_github_pushurl_is_not_github(self) -> None:
        self._git("remote", "add", "split2", GITHUB_URL)
        self._git("remote", "set-url", "--push", "split2", "https://gitlab.example.com/o/r.git")
        self._git("config", f"url.{self.remote}.insteadOf", "https://gitlab.example.com/o/r.git", "--add")
        self._run_session_hook()
        result = self._push("git push split2 HEAD:refs/heads/feature")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("verdict: not-github |", self._verdict())
        self.assertFalse(self.gh_args.exists())

    def test_github_pushurl_is_used_when_url_is_not_github(self) -> None:
        self._git("remote", "add", "split", "https://gitlab.example.com/o/r.git")
        self._git("remote", "set-url", "--push", "split", GITHUB_URL)
        self._run_session_hook()
        result = self._push("git push split HEAD:refs/heads/feature")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("verdict: would-deny | reason: no-reviewer", self._verdict())

    def test_exempt_declaration_in_a_file_with_fences_or_comments_is_ignored(self) -> None:
        line = "GDD Push Review Exempt Paths: review-log/"
        for name, config in [
            ("行の途中で開く HTML コメント", f"text <!--\n{line}\n-->\n"),
            ("4 つのバッククォート", f"````\n```\n{line}\n````\n"),
        ]:
            with self.subTest(name):
                self.tearDown()
                self.setUp()
                self._declare_exempt(config)
                self._write_transcript(_sync_review())
                self._commit("review-log/x.md")
                self._session_and_push()
                self.assertIn("verdict: would-deny | reason: changed-after-review", self._verdict())

    def test_skipped_line_writes_dash_for_missing_branch_and_sha(self) -> None:
        for i in range(12):
            self._git("branch", f"b{i:02d}")
        self._session_and_push("git push origin --all")
        skipped = [line for line in self._log_lines() if "verdict: skipped" in line]
        self.assertEqual(len(skipped), 1)
        self.assertIn("| branch: - | sha: - |", skipped[0])

    def test_gh_output_with_non_ascii_digits_is_unknown(self) -> None:
        self._write_gh("²")
        self._session_and_push()
        self.assertIn("verdict: gh-unknown |", self._verdict())

    def test_failure_outside_the_judgment_is_logged_as_error(self) -> None:
        # stdin が UTF-8 でない ref 名を含んでも、error の行を残す
        self._run_session_hook()
        self._git("branch", "feature")
        result = self._push("git push origin refs/heads/feature:refs/heads/$(printf 'x\\377')")
        # push は remote が ref を作れずに失敗する（hook は通している）
        self.assertNotIn("pre-push hook", result.stderr)
        lines = self._log_lines()
        self.assertEqual(len(lines), 1, lines)
        self.assertIn("verdict: error |", lines[0])

    # --- 壊さないこと ---------------------------------------------------------
    def test_original_pre_push_hook_still_runs_with_the_same_stdin(self) -> None:
        received = self.root / "orig-stdin"
        hook = self.repo / ".git" / "hooks" / "pre-push"
        hook.write_text(f"#!/bin/sh\ncat > '{received}'\n", encoding="utf-8")
        hook.chmod(0o755)
        self._session_and_push()
        sha = self._git("rev-parse", "HEAD")
        self.assertEqual(received.read_text(encoding="utf-8").split(), ["HEAD", sha, "refs/heads/feature", "0" * 40])
        self.assertEqual(len(self._log_lines()), 1)

    def test_original_pre_push_hook_can_still_block(self) -> None:
        hook = self.repo / ".git" / "hooks" / "pre-push"
        hook.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
        hook.chmod(0o755)
        self._run_session_hook()
        self.assertNotEqual(self._push().returncode, 0)

    def test_overriding_hooks_path_still_runs_the_config_hook(self) -> None:
        self._run_session_hook()
        result = self._push("git -c core.hooksPath=/dev/null push origin HEAD:refs/heads/feature")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(self._log_lines()), 1)

    def test_missing_hook_script_does_not_block_push(self) -> None:
        self._run_session_hook()
        text = self._env_file_text()
        self.assertIn(str(GIT_HOOK), text)
        self.env_file.write_text(text.replace(str(GIT_HOOK), str(self.root / "gone.sh")), encoding="utf-8")
        result = self._push()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self._log_lines(), [])

    def test_kill_switch_after_session_start_stops_logging(self) -> None:
        self._run_session_hook()
        (self.home / ".claude").mkdir()
        (self.home / ".claude" / "gdd-hooks-disabled").write_text("", encoding="utf-8")
        result = self._push()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self._log_lines(), [])

    def test_unwritable_log_does_not_break_push(self) -> None:
        self.state_dir.write_text("not a dir", encoding="utf-8")
        self._session_and_push()

    def test_broken_transcript_does_not_break_push(self) -> None:
        self.transcript.write_bytes(b"\xff\xfe{not json\n[1,2]\nnull\n")
        self._session_and_push()
        self.assertIn("verdict: would-deny |", self._verdict())

    def test_existing_git_config_env_is_kept(self) -> None:
        self._run_session_hook()
        result = self._push(
            "git config --get user.signingkey; git push origin HEAD:refs/heads/feature",
            extra={"GIT_CONFIG_COUNT": "1", "GIT_CONFIG_KEY_0": "user.signingkey", "GIT_CONFIG_VALUE_0": "KEPT"},
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("KEPT", result.stdout)
        self.assertEqual(len(self._log_lines()), 1)

    def test_session_hook_twice_runs_git_hook_once(self) -> None:
        self._run_session_hook()
        self._run_session_hook({"session_id": "s1", "transcript_path": str(self.transcript), "source": "compact"})
        result = self._push()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(self._log_lines()), 1)

    @unittest.skipUnless(shutil.which("zsh"), "zsh が無い")
    def test_env_file_works_when_sourced_by_zsh(self) -> None:
        self._run_session_hook()
        result = self._push(shell="zsh")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("verdict: would-deny | reason: no-reviewer", self._verdict())


class PushReviewWiringTests(unittest.TestCase):
    def test_session_start_registers_env_hook(self) -> None:
        data = json.loads(HOOKS_JSON.read_text(encoding="utf-8"))
        commands = [
            h.get("command", "")
            for entry in data["hooks"]["SessionStart"]
            for h in entry.get("hooks", [])
        ]
        self.assertTrue(any("run-push-review-env-hook.sh" in c for c in commands), commands)


if __name__ == "__main__":
    unittest.main()
