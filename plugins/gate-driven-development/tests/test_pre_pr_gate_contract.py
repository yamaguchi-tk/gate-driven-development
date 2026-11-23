"""Contract tests for the active GDD pre-PR runtime gate."""
from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

import _block_reason_support as support


from _paths import PLUGIN_ROOT
from _git_fixture import init_repo
from _pre_push_gate_support import PrePushGateFixtureMixin
HOOK = PLUGIN_ROOT / "hooks" / "scripts" / "run-pre-pr-gate-hook.sh"
# fixture が作る steering slug。否定側検査（slug が reason へ漏れない）で実値と
# 突き合わせるため、`_write_steering` が使う 1 本をここに置く。
STEERING_SLUG = "20260614-pre-pr-gate"


class PrePrGateContractTests(unittest.TestCase):
    def _init_repo(self, path: Path, *, default_branch: str = "main") -> None:
        init_repo(path, branch=default_branch)
        subprocess.run(["git", "switch", "-q", "-c", "feature"], cwd=path, check=True)

    def _write_local_state(self, path: Path, *, active: bool = True) -> None:
        state_dir = path / ".claude"
        state_dir.mkdir(exist_ok=True)
        (state_dir / "gdd-dev.local.md").write_text(
            f"---\nactive: {str(active).lower()}\nsession_id: test-session\n---\n",
            encoding="utf-8",
        )

    _head_sha = PrePushGateFixtureMixin._head_sha

    _independent_review_line = PrePushGateFixtureMixin._independent_review_line

    def _write_steering(
        self,
        path: Path,
        *,
        next_action: str = "done",
        task_size: str = "quick (express)",
        adr_distilled: str = "not_applicable",
        adr_reason: str = "quick express / 重要判断なし",
        pre_pr_self_review: str = "",
        independent_review: str | None = None,
        auto_independent_review: bool = True,
        extra_state: str = "",
    ) -> None:
        steering = path / ".steering" / STEERING_SLUG
        steering.mkdir(parents=True, exist_ok=True)
        review_line = f"Pre-PR Self Review: {pre_pr_self_review}\n" if pre_pr_self_review else ""
        # standard の dry gate は `Independent Review` 行（HEAD sha / high 0 / blocking 0）
        # も要求する（独立レビュー #5。述語・parser は pre-push step 13b と同一）。
        # dry gate へ到達する fixture では既定で HEAD sha の正常行を自動付与し、
        # 既存 test が新分岐で落ちないようにする。
        if independent_review is None and auto_independent_review and pre_pr_self_review:
            independent_review = self._independent_review_line(sha=self._head_sha(path))
        ir_line = f"Independent Review: {independent_review}\n" if independent_review else ""
        steering.joinpath("state.md").write_text(
            "Resume From: gdd-completion-check\n"
            "Human Check Status: approved\n"
            "Route In Progress: none\n"
            f"Task Size: {task_size}\n"
            f"ADR distilled: {adr_distilled}\n"
            f"ADR distillation reason: {adr_reason}\n"
            f"{review_line}"
            f"{ir_line}"
            f"{extra_state}"
            "Started At: 2026-06-14T00:00:00Z\n",
            encoding="utf-8",
        )
        steering.joinpath("tasklist.md").write_text(
            "# Task List\n\n"
            "## Current Task\n"
            "- なし\n\n"
            "## Pending Tasks\n"
            "- なし\n\n"
            "## Completed Tasks\n"
            "- done\n\n"
            f"Next Action={next_action}\n",
            encoding="utf-8",
        )

    def _run_hook(
        self,
        cwd: Path,
        command: str,
        *,
        extra_env: dict[str, str] | None = None,
        tool_cwd: Path | None = None,
        tool_cwd_key: str = "cwd",
    ) -> subprocess.CompletedProcess[str]:
        tool_input = {"command": command}
        if tool_cwd is not None:
            tool_input[tool_cwd_key] = str(tool_cwd)
        payload = {
            "tool_name": "Bash",
            "tool_input": tool_input,
        }
        env = os.environ.copy()
        env.update({
            "CLAUDE_PLUGIN_ROOT": str(PLUGIN_ROOT),
            "CLAUDE_CODE_SESSION_ID": "test-session",
            # hook は GDD の PR 台帳（gdd-pr-roots）を state dir へ書く。実 HOME を汚さない。
            "GDD_HOOK_STATE_DIR": tempfile.mkdtemp(),
        })
        if extra_env:
            env.update(extra_env)
        return subprocess.run(
            ["bash", str(HOOK)],
            cwd=cwd,
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            env=env,
            check=False,
        )

    def test_hooks_json_registers_bash_pre_pr_gate(self) -> None:
        hooks = json.loads((PLUGIN_ROOT / "hooks" / "hooks.json").read_text(encoding="utf-8"))
        commands = [
            hook["command"]
            for entry in hooks["hooks"]["PreToolUse"]
            if entry.get("matcher") == "Bash"
            for hook in entry.get("hooks", [])
        ]

        self.assertTrue(commands, "PreToolUse must register a Bash matcher")
        self.assertTrue(any("run-pre-pr-gate-hook.sh" in command for command in commands), commands)

    def test_non_active_gdd_clean_diff_allows_gh_pr_create(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)

            result = self._run_hook(repo, "gh pr create --title test --body ok")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, "")

    def test_raw_steering_blocks_pr_create_without_active_marker(self) -> None:
        """Worktree 相当: .claude/gdd-dev.local.md がなくても raw steering は不足として通知される。"""
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            # marker を書かない（worktree 相当）
            self._write_steering(repo)
            subprocess.run(["git", "add", ".steering"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-q", "-m", "leak steering"], cwd=repo, check=True)

            result = self._run_hook(repo, "gh pr create --title test --body ok")

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["hookSpecificOutput"]["hookEventName"], "PreToolUse")
            self.assertIn("raw task .steering", payload["hookSpecificOutput"]["additionalContext"])

    def test_clean_diff_allows_pr_create_without_active_marker(self) -> None:
        """Worktree 相当: marker なし・.steering なし → allow（fail-open / クリーン時通過を固定）。"""
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            # marker を書かない、.steering も commit しない

            result = self._run_hook(repo, "gh pr create --title test --body ok")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, "")

    def test_base_unresolvable_fails_open(self) -> None:
        """base ref が解決できない（fallback 候補に含まれないデフォルトブランチ・origin なし）→ fail-open で不足として通知しない。"""
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            # fallback 候補 (main/master/trunk/develop) に含まれないデフォルトブランチ名を使う
            self._init_repo(repo, default_branch="production")
            # marker を書かない（worktree 相当）
            self._write_steering(repo)
            subprocess.run(["git", "add", ".steering"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-q", "-m", "leak steering"], cwd=repo, check=True)
            # origin なし・origin/HEAD も origin/main も main も master も trunk も develop も存在しない

            result = self._run_hook(repo, "gh pr create --title test --body ok")

            self.assertEqual(result.returncode, 0, result.stderr)
            # 判定不能 → fail-open: 不足として通知してはいけない
            self.assertEqual(result.stdout, "")

    def test_active_gdd_allows_non_pr_create_bash_command(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            self._write_local_state(repo)

            result = self._run_hook(repo, "gh pr view --json number")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, "")

    def test_active_gdd_non_pr_command_returns_before_python_parser(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            self._init_repo(repo)
            self._write_local_state(repo)
            bin_dir = Path(tmp) / "bin"
            bin_dir.mkdir()
            python_stub = bin_dir / "python3"
            python_stub.write_text("#!/usr/bin/env sh\nexit 99\n", encoding="utf-8")
            python_stub.chmod(0o755)

            result = self._run_hook(
                repo,
                "git status --short",
                extra_env={"PATH": f"{bin_dir}{os.pathsep}{os.environ.get('PATH', '')}"},
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, "")

    def test_active_gdd_blocks_pr_create_before_completion_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            self._write_local_state(repo)
            self._write_steering(repo, next_action="gdd-completion-check")

            result = self._run_hook(repo, "gh pr create --title test --body ok")

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["hookSpecificOutput"]["hookEventName"], "PreToolUse")
            self.assertIn("completion-check", payload["hookSpecificOutput"]["additionalContext"])
            self.assertIn("Next Action=gdd-completion-check", payload["hookSpecificOutput"]["additionalContext"])
            self.assertIn("使わないステアリングの終え方", payload["hookSpecificOutput"]["additionalContext"])

    def test_active_gdd_blocks_gh_api_pulls_before_completion_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            self._write_local_state(repo)
            self._write_steering(repo, next_action="gdd-completion-check")

            result = self._run_hook(
                repo,
                "gh api repos/org/repo/pulls -f title=test -f head=feature -f base=main -f body=ok",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["hookSpecificOutput"]["hookEventName"], "PreToolUse")
            self.assertIn("Next Action=gdd-completion-check", payload["hookSpecificOutput"]["additionalContext"])

    def test_active_gdd_allows_heredoc_body_mentioning_pr_create(self) -> None:
        """heredoc 本文に PR 作成コマンドの語の並びを含むだけのコマンドは不足として通知しない。

        heredoc の中身は **データ**であって command word ではない。落とさずに token 化
        すると `git commit -F - <<MSG ... MSG` の本文が単語ごとに割れ、「PR 作成」と
        誤判定される。二重引用符で括った引用は shlex が 1 token にまとめるので誤検出
        しない、という非対称があるため heredoc だけが刺さる。しかも誤検出された
        非 PR コマンドは body を持たないので「PR body を検査できません」を満たしよう
        がなく、原理的に通せない（実測で本 PR の commit が止まった。当時の gate は止めていた）。
        """
        phrase = "gh pr create"
        cases = {
            "plain": "git commit -F - <<MSG\n" + phrase + " を停止しました\nMSG",
            "quoted-word": "git commit -F - <<'MSG'\n" + phrase + "\nMSG",
            "dash-indent": "git commit -F - <<-MSG\n  " + phrase + "\n  MSG",
        }
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            self._write_local_state(repo)
            self._write_steering(repo, next_action="gdd-completion-check")

            for label, command in cases.items():
                with self.subTest(heredoc=label):
                    result = self._run_hook(repo, command)

                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertEqual(result.stdout, "", f"{label} が block された")

    def test_active_gdd_allows_gh_api_pulls_subresource_post(self) -> None:
        """`/pulls/<n>/<sub>` への POST は PR 作成ではないので不足として通知しない。

        `gdd-pr-review-followup` が規定する Copilot レビュー依頼
        （`POST .../pulls/<n>/requested_reviewers`）とインライン返信
        （`POST .../pulls/<n>/comments`）は、いずれも PR 作成ではなく
        **PR が既に在る前提**の操作である。判定を `"/pulls" in path` の部分一致で
        行うと、これらが「PR 作成」として不足の通知を受け、body を持たないため
        原理的に解消できなくなる（本 plugin の規定する運用が自分の gate の通知を出し続ける）。
        """
        subresources = (
            "requested_reviewers",
            "comments",
            "reviews",
            "merge",
        )
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            self._write_local_state(repo)
            self._write_steering(repo, next_action="gdd-completion-check")

            for sub in subresources:
                with self.subTest(subresource=sub):
                    result = self._run_hook(
                        repo,
                        f"gh api repos/org/repo/pulls/10/{sub} -X POST -f 'reviewers[]=x'",
                    )

                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertEqual(result.stdout, "", f"{sub} が block された")

    def test_active_gdd_blocks_pr_create_alias_before_completion_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            self._write_local_state(repo)
            self._write_steering(repo, next_action="gdd-completion-check")

            result = self._run_hook(repo, "gh pr new --title test --body ok")

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["hookSpecificOutput"]["hookEventName"], "PreToolUse")
            self.assertIn("Next Action=gdd-completion-check", payload["hookSpecificOutput"]["additionalContext"])

    def test_active_gdd_blocks_chained_pr_create_before_completion_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            self._write_local_state(repo)
            self._write_steering(repo, next_action="gdd-completion-check")

            result = self._run_hook(repo, "git push && gh pr create --title test --body ok")

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["hookSpecificOutput"]["hookEventName"], "PreToolUse")
            self.assertIn("Next Action=gdd-completion-check", payload["hookSpecificOutput"]["additionalContext"])

    def test_active_gdd_blocks_semicolon_joined_pr_create_before_completion_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            self._write_local_state(repo)
            self._write_steering(repo, next_action="gdd-completion-check")

            result = self._run_hook(repo, "true;gh pr create --title test --body ok")

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["hookSpecificOutput"]["hookEventName"], "PreToolUse")
            self.assertIn("Next Action=gdd-completion-check", payload["hookSpecificOutput"]["additionalContext"])

    def test_active_gdd_resolves_leading_cd_before_pr_create(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            parent = Path(tmp)
            repo = parent / "repo"
            repo.mkdir()
            self._init_repo(repo)
            self._write_local_state(repo)
            self._write_steering(repo, next_action="gdd-completion-check")

            result = self._run_hook(parent, f"cd {repo} && gh pr create --title test --body ok")

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["hookSpecificOutput"]["hookEventName"], "PreToolUse")
            self.assertIn("Next Action=gdd-completion-check", payload["hookSpecificOutput"]["additionalContext"])

    def test_active_gdd_resolves_env_cd_before_pr_create(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            parent = Path(tmp)
            repo = parent / "repo"
            repo.mkdir()
            self._init_repo(repo)
            self._write_local_state(repo)
            self._write_steering(repo, next_action="gdd-completion-check")

            result = self._run_hook(
                parent,
                "cd $GDD_REPO && gh pr create --title test --body ok",
                extra_env={"GDD_REPO": str(repo)},
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["hookSpecificOutput"]["hookEventName"], "PreToolUse")
            self.assertIn("Next Action=gdd-completion-check", payload["hookSpecificOutput"]["additionalContext"])

    def test_active_gdd_resolves_chained_relative_cd_before_pr_create(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            parent = Path(tmp)
            repo = parent / "repo"
            repo.mkdir()
            (repo / "subdir").mkdir()
            self._init_repo(repo)
            self._write_local_state(repo)
            self._write_steering(repo, next_action="gdd-completion-check")

            result = self._run_hook(parent, "cd repo && cd subdir && gh pr create --title test --body ok")

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["hookSpecificOutput"]["hookEventName"], "PreToolUse")
            self.assertIn("Next Action=gdd-completion-check", payload["hookSpecificOutput"]["additionalContext"])

    def test_active_gdd_uses_payload_cwd_before_pr_create(self) -> None:
        # payload の cwd は tool_input.cwd、Codex は tool_input.workdir。hook はどちらも読む。
        for key in ("cwd", "workdir"):
            with self.subTest(key=key), tempfile.TemporaryDirectory() as tmp:
                parent = Path(tmp)
                repo = parent / "repo"
                repo.mkdir()
                self._init_repo(repo)
                self._write_local_state(repo)
                self._write_steering(repo, next_action="gdd-completion-check")

                result = self._run_hook(parent, "gh pr create --title test --body ok", tool_cwd=repo,
                                        tool_cwd_key=key)

                self.assertEqual(result.returncode, 0, result.stderr)
                payload = json.loads(result.stdout)
                self.assertEqual(payload["hookSpecificOutput"]["hookEventName"], "PreToolUse")
                self.assertIn("Next Action=gdd-completion-check", payload["hookSpecificOutput"]["additionalContext"])

    def test_active_gdd_reads_body_file_relative_to_leading_cd(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            parent = Path(tmp)
            repo = parent / "repo"
            repo.mkdir()
            self._init_repo(repo)
            self._write_local_state(repo)
            self._write_steering(repo)
            (repo / "pr.md").write_text("safe body\n", encoding="utf-8")
            (repo / "feature.py").write_text("print('ok')\n", encoding="utf-8")
            subprocess.run(["git", "add", "feature.py"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-q", "-m", "add feature"], cwd=repo, check=True)

            result = self._run_hook(parent, f"cd {repo} && gh pr create --title test --body-file pr.md")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, "")

    def test_active_gdd_blocks_absolute_gh_path_before_completion_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            self._write_local_state(repo)
            self._write_steering(repo, next_action="gdd-completion-check")

            result = self._run_hook(repo, "/usr/bin/gh pr create --title test --body ok")

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["hookSpecificOutput"]["hookEventName"], "PreToolUse")
            self.assertIn("Next Action=gdd-completion-check", payload["hookSpecificOutput"]["additionalContext"])

    def test_active_gdd_blocks_nested_shell_pr_create_before_completion_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            self._write_local_state(repo)
            self._write_steering(repo, next_action="gdd-completion-check")

            result = self._run_hook(repo, "bash -lc 'gh pr create --title test --body ok'")

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["hookSpecificOutput"]["hookEventName"], "PreToolUse")
            self.assertIn("Next Action=gdd-completion-check", payload["hookSpecificOutput"]["additionalContext"])

    def test_active_gdd_blocks_eval_wrapped_pr_create_before_completion_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            self._write_local_state(repo)
            self._write_steering(repo, next_action="gdd-completion-check")

            result = self._run_hook(repo, "eval 'gh pr create --title test --body ok'")

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["hookSpecificOutput"]["hookEventName"], "PreToolUse")
            self.assertIn("Next Action=gdd-completion-check", payload["hookSpecificOutput"]["additionalContext"])

    def test_active_gdd_blocks_pr_create_with_global_repo_flag_before_completion_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            self._write_local_state(repo)
            self._write_steering(repo, next_action="gdd-completion-check")

            result = self._run_hook(repo, "gh -R org/repo pr create --title test --body ok")

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["hookSpecificOutput"]["hookEventName"], "PreToolUse")
            self.assertIn("Next Action=gdd-completion-check", payload["hookSpecificOutput"]["additionalContext"])

    def test_active_gdd_blocks_confidential_pr_body(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            self._write_local_state(repo)
            self._write_steering(repo)

            result = self._run_hook(repo, "gh pr create --title test --body 'account 123456789012'")

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["hookSpecificOutput"]["hookEventName"], "PreToolUse")
            self.assertIn("PR body", payload["hookSpecificOutput"]["additionalContext"])
            self.assertIn("12桁", payload["hookSpecificOutput"]["additionalContext"])

    def test_active_gdd_blocks_common_secret_pr_body_labels(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            self._write_local_state(repo)
            self._write_steering(repo)

            result = self._run_hook(repo, "gh pr create --title test --body 'access_token=abcdefghijklmnopqrstuvwxyz'")

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["hookSpecificOutput"]["hookEventName"], "PreToolUse")
            self.assertIn("PR body", payload["hookSpecificOutput"]["additionalContext"])
            self.assertIn("token/key/password", payload["hookSpecificOutput"]["additionalContext"])

    def test_active_gdd_blocks_generic_key_pr_body_labels(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            self._write_local_state(repo)
            self._write_steering(repo)

            result = self._run_hook(repo, "gh pr create --title test --body 'access_key=abcdefghijklmnopqrstuvwxyz'")

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["hookSpecificOutput"]["hookEventName"], "PreToolUse")
            self.assertIn("PR body", payload["hookSpecificOutput"]["additionalContext"])
            self.assertIn("token/key/password", payload["hookSpecificOutput"]["additionalContext"])

    def test_active_gdd_blocks_stdin_pr_body_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            self._write_local_state(repo)
            self._write_steering(repo)

            result = self._run_hook(repo, "gh pr create --title test --body-file -")

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["hookSpecificOutput"]["hookEventName"], "PreToolUse")
            self.assertIn("stdin", payload["hookSpecificOutput"]["additionalContext"])
            self.assertIn("PR body", payload["hookSpecificOutput"]["additionalContext"])

    def test_active_gdd_blocks_stdin_device_pr_body_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            self._write_local_state(repo)
            self._write_steering(repo)

            for command in [
                "gh pr create --title test --body-file /dev/stdin",
                "gh pr create --title test --body-file /proc/self/fd/0",
            ]:
                with self.subTest(command=command):
                    result = self._run_hook(repo, command)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    payload = json.loads(result.stdout)
                    self.assertEqual(payload["hookSpecificOutput"]["hookEventName"], "PreToolUse")
                    self.assertIn("stdin", payload["hookSpecificOutput"]["additionalContext"])
                    self.assertIn("PR body", payload["hookSpecificOutput"]["additionalContext"])

    def test_active_gdd_blocks_uninspectable_generated_pr_body(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            self._write_local_state(repo)
            self._write_steering(repo)

            result = self._run_hook(repo, "gh pr create --fill --title test")

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["hookSpecificOutput"]["hookEventName"], "PreToolUse")
            self.assertIn("PR body", payload["hookSpecificOutput"]["additionalContext"])
            self.assertIn("検査できません", payload["hookSpecificOutput"]["additionalContext"])

    def test_active_gdd_blocks_missing_pr_body_source(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            self._write_local_state(repo)
            self._write_steering(repo)

            result = self._run_hook(repo, "gh pr create --title test")

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["hookSpecificOutput"]["hookEventName"], "PreToolUse")
            self.assertIn("PR body", payload["hookSpecificOutput"]["additionalContext"])
            self.assertIn("検査できません", payload["hookSpecificOutput"]["additionalContext"])

    def test_active_gdd_stops_pr_flag_parsing_at_shell_separator(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            self._write_local_state(repo)
            self._write_steering(repo)

            result = self._run_hook(repo, "gh pr create --title test && echo --body ok")

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["hookSpecificOutput"]["hookEventName"], "PreToolUse")
            self.assertIn("PR body", payload["hookSpecificOutput"]["additionalContext"])
            self.assertIn("検査できません", payload["hookSpecificOutput"]["additionalContext"])

    def test_active_gdd_blocks_non_current_head_branch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            self._write_local_state(repo)
            self._write_steering(repo)

            result = self._run_hook(repo, "gh pr create --head other-branch --title test --body ok")

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["hookSpecificOutput"]["hookEventName"], "PreToolUse")
            self.assertIn("--head", payload["hookSpecificOutput"]["additionalContext"])

    def test_active_gdd_allows_owner_prefixed_current_head_branch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            self._write_local_state(repo)
            self._write_steering(repo)
            (repo / "feature.py").write_text("print('ok')\n", encoding="utf-8")
            subprocess.run(["git", "add", "feature.py"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-q", "-m", "add feature"], cwd=repo, check=True)

            result = self._run_hook(repo, "gh pr create --head monalisa:feature --title test --body ok")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, "")

    def test_active_gdd_blocks_shell_expanded_pr_body(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            self._write_local_state(repo)
            self._write_steering(repo)

            for command in [
                'gh pr create --title test --body "$PR_BODY"',
                'gh pr create --title test --body "$(cat pr.md)"',
            ]:
                with self.subTest(command=command):
                    result = self._run_hook(repo, command)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    payload = json.loads(result.stdout)
                    self.assertEqual(payload["hookSpecificOutput"]["hookEventName"], "PreToolUse")
                    self.assertIn("PR body", payload["hookSpecificOutput"]["additionalContext"])
                    self.assertIn("shell expansion", payload["hookSpecificOutput"]["additionalContext"])

    def test_active_gdd_blocks_unquoted_shell_expanded_pr_body(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            self._write_local_state(repo)
            self._write_steering(repo)

            result = self._run_hook(repo, "gh pr create --title test --body=$(cat pr.md)")

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["hookSpecificOutput"]["hookEventName"], "PreToolUse")
            self.assertIn("PR body", payload["hookSpecificOutput"]["additionalContext"])
            self.assertIn("shell expansion", payload["hookSpecificOutput"]["additionalContext"])

    def test_active_gdd_allows_readable_pr_template_body(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            self._write_local_state(repo)
            self._write_steering(repo)
            (repo / "PULL_REQUEST_TEMPLATE.md").write_text("safe template\n", encoding="utf-8")
            (repo / "feature.py").write_text("print('ok')\n", encoding="utf-8")
            subprocess.run(["git", "add", "feature.py"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-q", "-m", "add feature"], cwd=repo, check=True)

            result = self._run_hook(repo, "gh pr create --title test --template PULL_REQUEST_TEMPLATE.md")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, "")

    def test_active_gdd_blocks_raw_task_steering_in_pr_diff(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            self._write_local_state(repo)
            self._write_steering(repo)
            subprocess.run(["git", "add", ".steering"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-q", "-m", "leak steering"], cwd=repo, check=True)

            result = self._run_hook(repo, "gh pr create --title test --body ok")

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["hookSpecificOutput"]["hookEventName"], "PreToolUse")
            self.assertIn("raw task .steering", payload["hookSpecificOutput"]["additionalContext"])

    def test_active_gdd_blocks_standard_task_without_adr_distillation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            self._write_local_state(repo)
            self._write_steering(
                repo,
                task_size="standard",
                adr_distilled="",
                adr_reason="",
            )
            (repo / "feature.py").write_text("print('ok')\n", encoding="utf-8")
            subprocess.run(["git", "add", "feature.py"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-q", "-m", "add feature"], cwd=repo, check=True)

            result = self._run_hook(repo, "gh pr create --title test --body ok")

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["hookSpecificOutput"]["hookEventName"], "PreToolUse")
            self.assertIn("ADR", payload["hookSpecificOutput"]["additionalContext"])
            self.assertIn("docs/adr", payload["hookSpecificOutput"]["additionalContext"])

    def test_active_gdd_allows_standard_task_with_adr_in_pr_diff(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            self._write_local_state(repo)
            adr = repo / "docs" / "adr" / "20260614-pre-pr-gate.md"
            adr.parent.mkdir(parents=True)
            adr.write_text("# ADR\n\nDecision recorded.\n", encoding="utf-8")
            (repo / "feature.py").write_text("print('ok')\n", encoding="utf-8")
            subprocess.run(["git", "add", "docs/adr/20260614-pre-pr-gate.md", "feature.py"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-q", "-m", "add feature and adr"], cwd=repo, check=True)
            # `Independent Review` は HEAD 基準で検査されるため、commit 後に steering を書く
            self._write_steering(
                repo,
                task_size="standard",
                adr_distilled="yes",
                adr_reason="",
                pre_pr_self_review=(
                    "abc1234 | rounds: 3 | consecutive_clean: 2 | dry: yes "
                    "| lanes: internal=2,grounding=1,adversarial=1 | at: 2026-08-17T00:00:00Z"
                ),
            )

            result = self._run_hook(repo, "gh pr create --title test --body ok")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, "")

    def test_active_gdd_blocks_standard_task_with_adr_yes_but_no_adr_diff(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            self._write_local_state(repo)
            self._write_steering(repo, task_size="standard", adr_distilled="yes", adr_reason="")
            (repo / "feature.py").write_text("print('ok')\n", encoding="utf-8")
            subprocess.run(["git", "add", "feature.py"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-q", "-m", "add feature"], cwd=repo, check=True)

            result = self._run_hook(repo, "gh pr create --title test --body ok")

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["hookSpecificOutput"]["hookEventName"], "PreToolUse")
            self.assertIn("ADR", payload["hookSpecificOutput"]["additionalContext"])
            self.assertIn("PR diff", payload["hookSpecificOutput"]["additionalContext"])

    def test_active_gdd_blocks_high_codebase_health_finding(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            self._write_local_state(repo)
            self._write_steering(repo)
            (repo / "large_module.py").write_text("\n".join("print('x')" for _ in range(1601)), encoding="utf-8")
            subprocess.run(["git", "add", "large_module.py"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-q", "-m", "add large module"], cwd=repo, check=True)

            result = self._run_hook(repo, "gh pr create --title test --body ok")

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["hookSpecificOutput"]["hookEventName"], "PreToolUse")
            self.assertIn("Codebase Health Gate", payload["hookSpecificOutput"]["additionalContext"])
            self.assertIn("High", payload["hookSpecificOutput"]["additionalContext"])

    def test_active_gdd_allows_done_gate_with_clean_diff(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            self._write_local_state(repo)
            self._write_steering(repo)
            (repo / "feature.py").write_text("print('ok')\n", encoding="utf-8")
            subprocess.run(["git", "add", "feature.py"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-q", "-m", "add feature"], cwd=repo, check=True)

            result = self._run_hook(repo, "gh pr create --title test --body ok")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, "")

    def test_active_gdd_allows_completed_legacy_state_without_binding(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            self._write_local_state(repo)
            steering = repo / ".steering" / "20260614-legacy-done"
            steering.mkdir(parents=True, exist_ok=True)
            steering.joinpath("state.md").write_text(
                "Resume From: done\n"
                "Human Check Status: approved\n"
                "Route In Progress: none\n"
                "Task Size: quick (express)\n"
                "ADR distilled: not_applicable\n"
                "ADR distillation reason: quick express / 重要判断なし\n"
                "Started At: 2026-06-14T00:00:00Z\n"
                "Next Action=done\n",
                encoding="utf-8",
            )
            (repo / "feature.py").write_text("print('ok')\n", encoding="utf-8")
            subprocess.run(["git", "add", "feature.py"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-q", "-m", "add feature"], cwd=repo, check=True)

            result = self._run_hook(repo, "gh pr create --title test --body ok")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, "")

    def test_active_gdd_uses_terminal_binding_over_old_done_steering(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            self._write_local_state(repo)
            old_steering = repo / ".steering" / "20260613-old-done"
            old_steering.mkdir(parents=True, exist_ok=True)
            old_steering.joinpath("state.md").write_text("Next Action=done\n", encoding="utf-8")

            current = repo / ".steering" / "20260614-current-done"
            current.mkdir(parents=True, exist_ok=True)
            current.joinpath("state.md").write_text(
                "Task ID: current-done\n"
                f"Worktree: {repo}\n"
                "Branch: feature\n"
                "Resume From: done\n"
                "Human Check Status: approved\n"
                "Route In Progress: none\n"
                "Task Size: quick (express)\n"
                "ADR distilled: not_applicable\n"
                "ADR distillation reason: quick express / 重要判断なし\n"
                "Started At: 2026-06-14T00:00:00Z\n"
                "Next Action=done\n",
                encoding="utf-8",
            )
            subprocess.run(
                [
                    "python3",
                    str(PLUGIN_ROOT / "scripts" / "gdd_task_binding.py"),
                    "upsert-from-state",
                    "--repo-root",
                    str(repo),
                    "--state",
                    str(current / "state.md"),
                ],
                cwd=repo,
                check=True,
                capture_output=True,
                text=True,
            )
            (repo / "feature.py").write_text("print('ok')\n", encoding="utf-8")
            subprocess.run(["git", "add", "feature.py"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-q", "-m", "add feature"], cwd=repo, check=True)

            result = self._run_hook(repo, "gh pr create --title test --body ok")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, "")

    def test_active_gdd_blocks_ambiguous_active_steering_before_done_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            self._write_local_state(repo)
            for slug in ["20260614-active-a", "20260614-active-b"]:
                steering = repo / ".steering" / slug
                steering.mkdir(parents=True, exist_ok=True)
                steering.joinpath("state.md").write_text(
                    "Resume From: gdd-test-driven-development\n"
                    "Human Check Status: approved\n"
                    "Route In Progress: none\n"
                    f"Started At: 2026-06-14T00:00:0{slug[-1]}Z\n",
                    encoding="utf-8",
                )
            done = repo / ".steering" / "20260613-old-done"
            done.mkdir(parents=True, exist_ok=True)
            done.joinpath("state.md").write_text("Next Action=done\n", encoding="utf-8")

            result = self._run_hook(repo, "gh pr create --title test --body ok")

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["hookSpecificOutput"]["hookEventName"], "PreToolUse")
            self.assertIn("active steering", payload["hookSpecificOutput"]["additionalContext"])

    def test_active_gdd_allows_clean_diff_from_master_default_branch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo, default_branch="master")
            self._write_local_state(repo)
            self._write_steering(repo)
            (repo / "feature.py").write_text("print('ok')\n", encoding="utf-8")
            subprocess.run(["git", "add", "feature.py"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-q", "-m", "add feature"], cwd=repo, check=True)

            result = self._run_hook(repo, "gh pr create --title test --body ok")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, "")

    def test_active_gdd_allows_clean_diff_from_trunk_default_branch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo, default_branch="trunk")
            self._write_local_state(repo)
            self._write_steering(repo)
            (repo / "feature.py").write_text("print('ok')\n", encoding="utf-8")
            subprocess.run(["git", "add", "feature.py"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-q", "-m", "add feature"], cwd=repo, check=True)

            result = self._run_hook(repo, "gh pr create --title test --body ok")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, "")

    def test_active_gdd_uses_explicit_pr_base_for_diff_gates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            subprocess.run(["git", "switch", "-q", "main"], cwd=repo, check=True)
            subprocess.run(["git", "switch", "-q", "-c", "develop"], cwd=repo, check=True)
            (repo / "large_module.py").write_text("\n".join("print('x')" for _ in range(1601)), encoding="utf-8")
            subprocess.run(["git", "add", "large_module.py"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-q", "-m", "develop has existing large module"], cwd=repo, check=True)
            subprocess.run(["git", "switch", "-q", "-c", "feature-from-develop"], cwd=repo, check=True)
            self._write_local_state(repo)
            self._write_steering(repo)
            (repo / "feature.py").write_text("print('ok')\n", encoding="utf-8")
            subprocess.run(["git", "add", "feature.py"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-q", "-m", "add feature"], cwd=repo, check=True)

            result = self._run_hook(repo, "gh pr create --base develop --title test --body ok")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, "")

    def test_active_gdd_uses_remote_slash_pr_base_for_diff_gates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            subprocess.run(["git", "switch", "-q", "main"], cwd=repo, check=True)
            subprocess.run(["git", "switch", "-q", "-c", "release/foo"], cwd=repo, check=True)
            (repo / "large_module.py").write_text("\n".join("print('x')" for _ in range(1601)), encoding="utf-8")
            subprocess.run(["git", "add", "large_module.py"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-q", "-m", "release has existing large module"], cwd=repo, check=True)
            subprocess.run(["git", "update-ref", "refs/remotes/origin/release/foo", "HEAD"], cwd=repo, check=True)
            subprocess.run(["git", "switch", "-q", "-c", "feature-from-release"], cwd=repo, check=True)
            subprocess.run(["git", "branch", "-D", "release/foo"], cwd=repo, check=True)
            self._write_local_state(repo)
            self._write_steering(repo)
            (repo / "feature.py").write_text("print('ok')\n", encoding="utf-8")
            subprocess.run(["git", "add", "feature.py"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-q", "-m", "add feature"], cwd=repo, check=True)

            result = self._run_hook(repo, "gh pr create --base release/foo --title test --body ok")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, "")

    def test_active_gdd_uses_branch_configured_pr_base_for_diff_gates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            subprocess.run(["git", "switch", "-q", "main"], cwd=repo, check=True)
            subprocess.run(["git", "switch", "-q", "-c", "develop"], cwd=repo, check=True)
            (repo / "large_module.py").write_text("\n".join("print('x')" for _ in range(1601)), encoding="utf-8")
            subprocess.run(["git", "add", "large_module.py"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-q", "-m", "develop has existing large module"], cwd=repo, check=True)
            subprocess.run(["git", "switch", "-q", "-c", "feature-from-develop"], cwd=repo, check=True)
            subprocess.run(["git", "config", "branch.feature-from-develop.gh-merge-base", "develop"], cwd=repo, check=True)
            self._write_local_state(repo)
            self._write_steering(repo)
            (repo / "feature.py").write_text("print('ok')\n", encoding="utf-8")
            subprocess.run(["git", "add", "feature.py"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-q", "-m", "add feature"], cwd=repo, check=True)

            result = self._run_hook(repo, "gh pr create --title test --body ok")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, "")

    def test_adr_not_applicable_blocks_standard_task_with_express_in_reason(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            self._init_repo(path)
            self._write_local_state(path)
            self._write_steering(
                path,
                task_size="standard",
                adr_distilled="not_applicable",
                adr_reason="express っぽい判断だったが重要判断なしではない",
            )
            result = self._run_hook(path, "gh pr create --title x --body y")
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["hookSpecificOutput"]["hookEventName"], "PreToolUse")
            self.assertIn("ADR not_applicable", payload["hookSpecificOutput"]["additionalContext"])

    def test_adr_not_applicable_blocks_upgraded_standard_with_express_in_reason(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            self._init_repo(path)
            self._write_local_state(path)
            self._write_steering(
                path,
                task_size="standard (upgraded from quick)",
                adr_distilled="not_applicable",
                adr_reason="express から昇格したため",
            )
            result = self._run_hook(path, "gh pr create --title x --body y")
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["hookSpecificOutput"]["hookEventName"], "PreToolUse")

    def test_adr_not_applicable_allows_quick_express_exact_match(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            self._init_repo(path)
            self._write_local_state(path)
            self._write_steering(
                path,
                task_size="quick (express)",
                adr_distilled="not_applicable",
                adr_reason="express",
            )
            result = self._run_hook(path, "gh pr create --title x --body y")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), "")

    def test_adr_not_applicable_allows_reason_case_insensitive(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            self._init_repo(path)
            self._write_local_state(path)
            self._write_steering(
                path,
                task_size="standard",
                adr_distilled="not_applicable",
                adr_reason="QUICK EXPRESS",
                pre_pr_self_review=(
                    "abc1234 | rounds: 3 | consecutive_clean: 2 | dry: yes "
                    "| lanes: internal=2,grounding=1,adversarial=1 | at: 2026-08-17T00:00:00Z"
                ),
            )
            result = self._run_hook(path, "gh pr create --title x --body y")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), "")

    # ---- Decision Handoff: 申し送りのある Decision は not_applicable にできない ----

    HANDOFF_TOKEN = "不足ガード=ADR not_applicable with Decision Handoff"
    HANDOFF_LINE = "- Decision Handoff: issue: #12 | at: 2026-10-14T00:00:00Z\n"
    DRY_YES = (
        "abc1234 | rounds: 3 | consecutive_clean: 2 | dry: yes "
        "| lanes: internal=2,grounding=1,adversarial=1 | at: 2026-08-17T00:00:00Z"
    )

    def _handoff_hook_result(self, *, task_size: str, adr_reason: str, extra_state: str,
                             pre_pr_self_review: str = "") -> subprocess.CompletedProcess[str]:
        tmp = tempfile.mkdtemp()
        path = Path(tmp)
        self._init_repo(path)
        self._write_local_state(path)
        self._write_steering(
            path,
            task_size=task_size,
            adr_distilled="not_applicable",
            adr_reason=adr_reason,
            pre_pr_self_review=pre_pr_self_review,
            extra_state=extra_state,
        )
        return self._run_hook(path, "gh pr create --title x --body y")

    def _assert_handoff_block(self, result: subprocess.CompletedProcess[str]) -> None:
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(result.stdout.strip(), "allow された（申し送りがあるのに not_applicable で通った）")
        payload = json.loads(result.stdout)
        self.assertEqual(payload["hookSpecificOutput"]["hookEventName"], "PreToolUse")
        self.assertIn(self.HANDOFF_TOKEN, payload["hookSpecificOutput"]["additionalContext"])

    def test_decision_handoff_blocks_not_applicable_in_express_and_trivial(self) -> None:
        """fail-open 1: Task Size の除外より前に、申し送りの行で not_applicable を受理せず、不足として通知する。"""
        for task_size, reason in (("quick (express)", "express"), ("trivial", "trivial")):
            with self.subTest(task_size=task_size):
                self._assert_handoff_block(self._handoff_hook_result(
                    task_size=task_size, adr_reason=reason, extra_state=self.HANDOFF_LINE))

    def test_decision_handoff_blocks_not_applicable_with_reason_juuyou_hanndan_nashi(self) -> None:
        """fail-open 1: standard で dry gate を満たしていても、理由「重要判断なし」で通さない。"""
        self._assert_handoff_block(self._handoff_hook_result(
            task_size="standard", adr_reason="重要判断なし", extra_state=self.HANDOFF_LINE,
            pre_pr_self_review=self.DRY_YES))

    def test_decision_handoff_blocks_every_line_shape(self) -> None:
        """fail-open 3: 値が読めない・事故で崩れた形も「ある」として扱い、不足として通知する（fence の中も不足として通知する側）。"""
        shapes = {
            "bullet なし": "Decision Handoff: issue: #12\n",
            "値が空で子の行": "- Decision Handoff:\n  - issue: #12\n",
            "値が空": "- Decision Handoff:\n",
            "太字": "- **Decision Handoff**: issue: #12\n",
            "小文字": "- decision handoff: issue: #12\n",
            "字下げ": "    - Decision Handoff: issue: #12\n",
            "fence の中": "```\n- Decision Handoff: issue: #12\n```\n",
        }
        for name, line in shapes.items():
            with self.subTest(shape=name):
                self._assert_handoff_block(self._handoff_hook_result(
                    task_size="quick (express)", adr_reason="express", extra_state=line))

    def test_decision_handoff_value_is_not_evaluated(self) -> None:
        """fail-open 2: 値に shell の特殊文字・非 UTF-8 があっても guard が落ちず、副作用も無い。"""
        tmp = Path(tempfile.mkdtemp())
        marker = tmp / "touched"
        values = (
            f"$(touch {marker})",
            f"`touch {marker}`",
            "\"'|\\ issue: #12",
            "issue: #12\r",
        )
        for value in values:
            with self.subTest(value=value):
                self._assert_handoff_block(self._handoff_hook_result(
                    task_size="quick (express)", adr_reason="express",
                    extra_state=f"- Decision Handoff: {value}\n"))
                self.assertFalse(marker.exists())
        path = Path(tempfile.mkdtemp())
        self._init_repo(path)
        self._write_local_state(path)
        self._write_steering(path, task_size="quick (express)", adr_reason="express")
        state = path / ".steering" / STEERING_SLUG / "state.md"
        state.write_bytes(state.read_bytes() + b"- Decision Handoff: \xff\xfe issue\n")
        # 非 UTF-8 の state.md は、行の中身によらず hook が exit 2（PreToolUse では実行を止める異常終了）で
        # 終わるか、不足の通知を出す既存の挙動になる。ここでは allow に落ちないことだけを固定する。
        result = self._run_hook(path, "gh pr create --title x --body y")
        blocked = result.returncode == 2 or (
            result.returncode == 0 and '"hookEventName": "PreToolUse"' in result.stdout)
        self.assertTrue(blocked, (result.returncode, result.stdout, result.stderr))

    def test_decision_handoff_allows_adr_yes_with_adr_in_diff(self) -> None:
        """陽性対照: ADR を蒸留して yes にすれば、申し送りがあっても通る。"""
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            self._write_local_state(repo)
            (repo / "docs" / "adr").mkdir(parents=True)
            (repo / "docs" / "adr" / "20261014-handoff.md").write_text("# ADR\n", encoding="utf-8")
            subprocess.run(["git", "add", "docs/adr/20261014-handoff.md"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-q", "-m", "add adr"], cwd=repo, check=True)
            self._write_steering(
                repo, task_size="quick (express)", adr_distilled="yes", adr_reason="",
                extra_state=self.HANDOFF_LINE,
            )
            result = self._run_hook(repo, "gh pr create --title x --body y")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), "")

    def test_adr_not_applicable_predicate_fails_closed_without_readable_state(self) -> None:
        """fail-open 3: state のパスが渡されない・読めないときは not_applicable を許さない。"""
        lib = PLUGIN_ROOT / "hooks" / "scripts" / "lib" / "gate-ledger.sh"
        tmp = tempfile.mkdtemp()
        cases = {
            "引数が 2 つ": "gdd_adr_not_applicable_allowed 'quick (express)' express",
            "パスが空": "gdd_adr_not_applicable_allowed 'quick (express)' express ''",
            "存在しない": f"gdd_adr_not_applicable_allowed 'quick (express)' express '{tmp}/none.md'",
            "ディレクトリ": f"gdd_adr_not_applicable_allowed 'quick (express)' express '{tmp}'",
        }
        for name, call in cases.items():
            with self.subTest(case=name):
                result = subprocess.run(
                    ["bash", "-c", f'set -euo pipefail; source "{lib}"; if {call}; then echo allow; else echo deny; fi'],
                    capture_output=True, text=True, check=False,
                )
                self.assertEqual(result.stdout.strip(), "deny", result.stderr)
        ok = Path(tmp) / "state.md"
        ok.write_text("Task Size: quick (express)\n", encoding="utf-8")
        result = subprocess.run(
            ["bash", "-c", f'set -euo pipefail; source "{lib}"; if gdd_adr_not_applicable_allowed "quick (express)" express "{ok}"; then echo allow; else echo deny; fi'],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.stdout.strip(), "allow", result.stderr)

    # ---- T-15: dry gate (AC-5, AC-7) ----------------------------------

    def test_standard_task_size_passes_with_dry_yes_evidence_ac5(self) -> None:
        """AC-5 双方向固定の pass 側: `dry: yes`（`consecutive_clean: 2` 込み）
        の証跡があれば standard task の `gh pr create` は通る。
        """
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            self._init_repo(path)
            self._write_local_state(path)
            self._write_steering(
                path,
                task_size="standard",
                adr_distilled="not_applicable",
                adr_reason="重要判断なし",
                pre_pr_self_review=(
                    "abc1234 | rounds: 3 | consecutive_clean: 2 | dry: yes "
                    "| lanes: internal=2,grounding=1,adversarial=1 | at: 2026-08-17T00:00:00Z"
                ),
            )
            result = self._run_hook(path, "gh pr create --title x --body y")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), "")

    def test_standard_dry_gate_requires_independent_review_evidence(self) -> None:
        """独立レビュー #5: pre-PR gate も `Independent Review` を機械検査する。

        `dry-not-reached` の通知文言は standard に「独立レビュー 1 回（high 0 /
        blocking 0）」を要求していたのに、pre-PR gate は当該行を一切読んでおらず
        機械強制できる述語を自己申告のまま残していた。述語・parser は pre-push
        step 13b と同一（HEAD 一致・high 0・blocking 0）。
        欠落 / sha 不一致 / high>0 の 3 分岐と正常系を 1 本で固定する。
        """
        cases = (
            ("missing", "independent-review-missing"),
            ("stale", "independent-review-stale"),
            ("high", "independent-review-high"),
            ("ok", None),
        )
        for kind, expected_code in cases:
            with self.subTest(case=kind), tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp)
                self._init_repo(path)
                self._write_local_state(path)
                stale = self._head_sha(path)
                (path / "feature.py").write_text("x = 1\n", encoding="utf-8")
                subprocess.run(["git", "add", "feature.py"], cwd=path, check=True)
                subprocess.run(["git", "commit", "-q", "-m", "feature"], cwd=path, check=True)
                head = self._head_sha(path)
                kwargs: dict[str, object] = {}
                if kind == "missing":
                    kwargs["auto_independent_review"] = False
                elif kind == "stale":
                    kwargs["independent_review"] = self._independent_review_line(sha=stale)
                elif kind == "high":
                    kwargs["independent_review"] = self._independent_review_line(
                        sha=head, high="2"
                    )
                self._write_steering(
                    path,
                    task_size="standard",
                    adr_distilled="not_applicable",
                    adr_reason="重要判断なし",
                    pre_pr_self_review=(
                        "abc1234 | rounds: 1 | consecutive_clean: 1 | dry: yes "
                        "| lanes: internal=2,grounding=not_applicable(independent-review),"
                        "adversarial=not_applicable(independent-review) | at: 2026-08-17T00:00:00Z"
                    ),
                    **kwargs,  # type: ignore[arg-type]
                )

                result = self._run_hook(path, "gh pr create --title x --body y")
                self.assertEqual(result.returncode, 0, result.stderr)
                if expected_code is None:
                    self.assertEqual(result.stdout.strip(), "")
                else:
                    payload = json.loads(result.stdout)
                    self.assertEqual(payload["hookSpecificOutput"]["hookEventName"], "PreToolUse", result.stdout)
                    self.assertIn(expected_code, payload["hookSpecificOutput"]["additionalContext"])

    def test_task_size_unknown_case_and_whitespace_values_require_dry_ac5(self) -> None:
        """design.md 147 行「4 値と完全一致。未知値は standard 扱い（fail-closed
        側）」を pre-PR gate 側でも固定する。`trivial` / `quick (express)` の
        skip アーム以外はすべて同一の catch-all アームに落ちるため、代表として
        未知値・空文字・大文字混じり+前後空白の 3 形を `dry: no` 証跡と組み合わせ、
        いずれも dry-not-reached で不足として通知されることを確認する
        （pre-push 側 `test_step9_task_size_case_and_unknown_values_normalize_to_standard_ac20` と同型）。
        """
        for label, raw_task_size in (
            ("unknown-falls-back", "banana"),
            ("empty-falls-back", ""),
            ("uppercase-with-whitespace", "  STANDARD  "),
        ):
            with self.subTest(case=label), tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp)
                self._init_repo(path)
                self._write_local_state(path)
                self._write_steering(
                    path,
                    task_size=raw_task_size,
                    adr_distilled="not_applicable",
                    adr_reason="重要判断なし",
                    pre_pr_self_review=(
                        "abc1234 | rounds: 2 | consecutive_clean: 0 | dry: no "
                        "| lanes: internal=2,grounding=1,adversarial=1 | at: 2026-08-17T00:00:00Z"
                    ),
                )
                result = self._run_hook(path, "gh pr create --title x --body y")
                self.assertEqual(result.returncode, 0, result.stderr)
                payload = json.loads(result.stdout)
                self.assertEqual(payload["hookSpecificOutput"]["hookEventName"], "PreToolUse")
                self.assertIn("dry-not-reached", payload["hookSpecificOutput"]["additionalContext"])

    def test_exempt_task_sizes_skip_dry_gate_without_evidence_ac7(self) -> None:
        """AC-7 の**免除側**を、免除リテラルごと・正規化ありで固定する。

        既存の免除カバレッジは既定値 `quick (express)`（完全一致・正規化不要）だけで、
        (i) `trivial` アームの削除 (ii) Task Size 正規化（`tr` + `sed`）の削除 の
        どちらも生き残っていた（impl-gate 実測の SURVIVOR M7 / M6 = advisory L-28 / L-27）。
        誤爆方向（免除タスクが誤って不足として通知される）は AC-7 の中心なので、判別力を
        持つ最小 fixture を 2 形だけ置く:

        - `trivial`: `trivial|` アームを消すと catch-all に落ちて不足として通知される
        - `  Quick (Express)  `: 正規化を消すと免除アームに一致せず不足として通知される

        いずれも証跡を **書かない** ことで、免除が効いていなければ必ず
        missing-evidence へ落ちる形にしてある。
        """
        for label, raw_task_size in (
            ("trivial-exact", "trivial"),
            ("express-uppercase-with-whitespace", "  Quick (Express)  "),
        ):
            with self.subTest(case=label), tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp)
                self._init_repo(path)
                self._write_local_state(path)
                self._write_steering(
                    path,
                    task_size=raw_task_size,
                    adr_distilled="not_applicable",
                    adr_reason="重要判断なし",
                )
                result = self._run_hook(path, "gh pr create --title x --body y")
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout.strip(), "", f"{label}: 免除されていない")

    def _block_reason_samples(self) -> list[support.BlockReasonSample]:
        """dry gate の到達可能な block reason を reason code ごとに 1 本ずつ集める。

        hook 横断 contract（`test_hook_block_reason_recovery_contract.py`）の provider
        でもある。否定側検査用に一時 repo の絶対パスと steering slug も返す。
        """
        dry_yes = (
            "abc1234 | rounds: 1 | consecutive_clean: 1 | dry: yes "
            "| lanes: internal=2,grounding=1,adversarial=1 | at: 2026-08-17T00:00:00Z"
        )
        samples: list[support.BlockReasonSample] = []
        for label, evidence, ir_kind in (
            ("missing-evidence", "", None),
            (
                "dry-not-reached",
                "abc1234 | rounds: 2 | consecutive_clean: 0 | dry: no "
                "| lanes: internal=2,grounding=1,adversarial=1 | at: 2026-08-17T00:00:00Z",
                None,
            ),
            ("independent-review-missing", dry_yes, "missing"),
            ("independent-review-stale", dry_yes, "stale"),
            ("independent-review-high", dry_yes, "high"),
        ):
            with tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp)
                self._init_repo(path)
                self._write_local_state(path)
                ir_kwargs: dict[str, object] = {}
                if ir_kind == "missing":
                    ir_kwargs["auto_independent_review"] = False
                elif ir_kind == "stale":
                    ir_kwargs["independent_review"] = self._independent_review_line(sha="0" * 40)
                elif ir_kind == "high":
                    ir_kwargs["independent_review"] = self._independent_review_line(
                        sha=self._head_sha(path), high="2"
                    )
                self._write_steering(
                    path,
                    task_size="standard",
                    adr_distilled="not_applicable",
                    adr_reason="重要判断なし",
                    pre_pr_self_review=evidence,
                    **ir_kwargs,  # type: ignore[arg-type]
                )
                result = self._run_hook(path, "gh pr create --title x --body y")
                payload = json.loads(result.stdout)
                self.assertEqual(payload["hookSpecificOutput"]["hookEventName"], "PreToolUse", f"{label}: {result.stdout}")
                reason = payload["hookSpecificOutput"]["additionalContext"]
                self.assertIn(label, reason, f"{label} を踏めていない: {reason}")
                samples.append(
                    support.BlockReasonSample(
                        code=label,
                        reason=reason,
                        forbidden=(str(path), STEERING_SLUG),
                    )
                )
        return samples


def _collect_pre_pr_block_reason_samples() -> list[support.BlockReasonSample]:
    """hook 横断 contract 用の fixture provider（`_block_reason_samples` の再利用）。"""
    case = PrePrGateContractTests("runTest")
    return case._block_reason_samples()


support.register_block_reason_provider(HOOK, _collect_pre_pr_block_reason_samples)


class PrePrBoundTerminalSteeringTests(unittest.TestCase):
    """worktree の binding が終端の steering を指すとき、pre-PR gate も作業中の steering を数える。

    binding が cancelled・stale な brainstorming を指すと、pre-PR gate は作業中の steering を数えず、
    別の done の steering が 1 件あればそれで completion-check を判定して PR を作らせていた。
    pre-push・merge gate と同じく、binding が無いときと同じ規則で作業中の steering を数え直す。
    """

    _run_hook = PrePrGateContractTests._run_hook
    _init_repo = PrePrGateContractTests._init_repo
    _write_local_state = PrePrGateContractTests._write_local_state

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.repo = Path(self._tmp.name)
        self._init_repo(self.repo)
        self._write_local_state(self.repo)

    def _steering(self, slug: str, body: str) -> Path:
        steering = self.repo / ".steering" / slug
        steering.mkdir(parents=True, exist_ok=True)
        (steering / "state.md").write_text(
            body
            + "Human Check Status: approved\nRoute In Progress: none\nTask Size: quick (express)\n"
            "ADR distilled: not_applicable\nADR distillation reason: quick express / 重要判断なし\n"
            "Started At: 2026-06-14T00:00:00Z\n",
            encoding="utf-8",
        )
        return steering / "state.md"

    def _bind(self, resume_from: str, next_action: str = "") -> None:
        line = f"Next Action: {next_action}\n" if next_action else ""
        state = self._steering(
            "20260901-bound",
            f"Task ID: 20260901-bound\nWorktree: {self.repo}\nBranch: feature\n"
            f"Resume From: {resume_from}\n{line}",
        )
        subprocess.run(
            ["python3", str(PLUGIN_ROOT / "scripts" / "gdd_task_binding.py"), "upsert-from-state",
             "--repo-root", str(self.repo), "--state", str(state)],
            cwd=self.repo, check=True, capture_output=True, text=True,
        )

    def _active(self) -> None:
        self._steering("20260924-active", "Resume From: gdd-test-driven-development\n")

    def _other_done(self) -> None:
        self._steering("20260910-done", "Resume From: gdd-completion-check\nNext Action: done\n")

    def _decision(self) -> str | None:
        result = self._run_hook(self.repo, "gh pr create --title test --body ok")
        self.assertEqual(result.returncode, 0, result.stderr)
        if not result.stdout.strip():
            return None
        payload = json.loads(result.stdout)
        self.assertNotIn("decision", payload)
        self.assertEqual(payload["hookSpecificOutput"]["hookEventName"], "PreToolUse")
        return "notice"

    def test_cancelled_binding_does_not_let_another_done_one_hide_the_active_one(self) -> None:
        """不足として通知すべき入力: binding が cancelled、作業中の steering と別の done の steering がある。"""
        self._bind("cancelled", "cancelled")
        self._active()
        self._other_done()
        self.assertEqual(self._decision(), "notice")

    def test_stale_brainstorming_binding_does_not_hide_the_active_one(self) -> None:
        """不足として通知すべき入力: binding が stale な brainstorming でも同じ。"""
        state = self.repo / ".steering" / "20260901-bound" / "state.md"
        self._bind("gdd-brainstorming", "gdd-brainstorming")
        state.write_text(
            state.read_text(encoding="utf-8").replace("2026-06-14T00:00:00Z", "2026-01-01T00:00:00Z"),
            encoding="utf-8",
        )
        self._active()
        self._other_done()
        self.assertEqual(self._decision(), "notice")

    def test_next_action_done_binding_does_not_hide_the_active_one(self) -> None:
        """不足として通知すべき入力: binding 先が Next Action: done でも、作業中の steering があれば不足として通知する。"""
        self._bind("gdd-completion-check", "done")
        self._active()
        self.assertEqual(self._decision(), "notice")

    def test_cancel_binding_does_not_let_another_done_one_decide(self) -> None:
        """不足として通知すべき入力: binding 先が Next Action: canceled で作業中が無いとき、別の done の steering で
        completion-check を判定せず、binding 先で判定する（数え直す前と同じ）。"""
        self._bind("gdd-completion-check", "canceled")
        self._other_done()
        self.assertEqual(self._decision(), "notice")

    def test_next_action_done_binding_without_active_steerings_allows(self) -> None:
        """Post-Completion の PR 作成（binding 先が Next Action: done、作業中なし）は今どおり通す。"""
        self._bind("gdd-completion-check", "done")
        self._other_done()
        self.assertIsNone(self._decision())

    def test_unreadable_active_state_blocks_with_a_reason(self) -> None:
        """例外で guard が落ちない: 数え直しで選んだ作業中の steering の state.md が読めなくても、
        理由つきで不足として通知する（無出力で終わらない）。"""
        if os.geteuid() == 0:
            self.skipTest("root は読み取り権限を無視する")
        self._bind("cancelled", "cancelled")
        state = self._steering("20260924-active", "Resume From: gdd-test-driven-development\n")
        state.chmod(0)
        self.addCleanup(state.chmod, 0o644)
        self.assertEqual(self._decision(), "notice")

    def test_followup_binding_without_active_steerings_allows(self) -> None:
        """followup 中の形（Next Action: done・Resume From: external-review-waiting）で作業中なしは今どおり通す。"""
        self._bind("external-review-waiting", "done")
        self.assertIsNone(self._decision())


if __name__ == "__main__":
    unittest.main()
