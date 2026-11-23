"""Contract tests for the review-followup nudge hook。

`hooks/scripts/run-review-followup-nudge-hook.sh` は PreToolUse (Bash matcher) で
`git push` を検知し、push 先 branch に PR が既にあるなら `pr-review-followup`
skill の手順に従うよう `additionalContext` を 1 行注入する。既存の
`run-pre-push-gate-hook.sh`（active GDD 限定の pre-push gate）とは独立に動き、
active/非 active を問わず常に注入する（Opus advisory 実測: active でも
session-mismatch/optout/unresolved-steering で無言通過する分岐が直近30日に
あり、「active なら既存 gate が必ず文言を出す」という前提は成立しないため）。

テストは 3 ファイルに分けている。本ファイルは基本の流れ・opt-out・記録・注入の文言・
hooks.json への配線を測る。push の検知と push 先 branch の解決は
`test_review_followup_nudge_hook_push_target.py`、`gh` の呼び出し・結果の分類・cache は
`test_review_followup_nudge_hook_gh.py` が測る。fixture（一時 repo・hook 起動・`gh` の
stub）は `_review_followup_nudge_support.py` の `ReviewFollowupNudgeFixtureMixin` にある。
"""
from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from _paths import PLUGIN_ROOT
from _review_followup_nudge_support import (
    HANG_GUARD,
    HOOK,
    HOOKS_JSON,
    _write_stub_gh,
    ReviewFollowupNudgeFixtureMixin,
)


class ReviewFollowupNudgeHookTests(ReviewFollowupNudgeFixtureMixin, unittest.TestCase):
    def test_non_push_command_is_noop(self) -> None:
        with tempfile.TemporaryDirectory(prefix="gdd-rfn-") as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            self._init_repo(repo)
            result = self._run_hook(repo, "git status")
            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stdout.strip(), "")

    def test_push_with_pr_injects_pointer(self) -> None:
        with tempfile.TemporaryDirectory(prefix="gdd-rfn-") as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            self._init_repo(repo)
            gh_stub = Path(tmp) / "gh-stub.sh"
            _write_stub_gh(gh_stub, behavior="has-pr")
            state_dir = Path(tmp) / "hookstate"
            result = self._run_hook(
                repo,
                "git push origin feature-x",
                extra_env={
                    "GDD_HOOK_STATE_DIR": str(state_dir),
                    "GDD_REVIEW_FOLLOWUP_GH_BIN": str(gh_stub),
                },
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("additionalContext", result.stdout)
            payload = json.loads(result.stdout)
            ctx = payload["hookSpecificOutput"]["additionalContext"]
            self.assertIn("pr-review-followup", ctx)
            log_file = state_dir / "review-followup-nudge.log"
            self.assertTrue(log_file.exists())
            self.assertIn("event: injected", log_file.read_text(encoding="utf-8"))

    def test_push_without_pr_is_noop(self) -> None:
        with tempfile.TemporaryDirectory(prefix="gdd-rfn-") as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            self._init_repo(repo)
            gh_stub = Path(tmp) / "gh-stub.sh"
            _write_stub_gh(gh_stub, behavior="no-pr")
            result = self._run_hook(
                repo,
                "git push origin feature-x",
                extra_env={
                    "GDD_HOOK_STATE_DIR": str(Path(tmp) / "hookstate"),
                    "GDD_REVIEW_FOLLOWUP_GH_BIN": str(gh_stub),
                },
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), "")

    def test_optout_process_env_suppresses_injection(self) -> None:
        with tempfile.TemporaryDirectory(prefix="gdd-rfn-") as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            self._init_repo(repo)
            gh_stub = Path(tmp) / "gh-stub.sh"
            counter = Path(tmp) / "counter.log"
            _write_stub_gh(gh_stub, behavior="has-pr", counter_file=counter)
            result = self._run_hook(
                repo,
                "git push origin feature-x",
                extra_env={
                    "GDD_HOOK_STATE_DIR": str(Path(tmp) / "hookstate"),
                    "GDD_REVIEW_FOLLOWUP_GH_BIN": str(gh_stub),
                    "GDD_SKIP_PRE_PUSH_GATE": "1",
                },
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), "")
            self.assertFalse(counter.exists(), "gh must not be invoked when opted out")

    def test_optout_command_prefix_suppresses_injection(self) -> None:
        with tempfile.TemporaryDirectory(prefix="gdd-rfn-") as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            self._init_repo(repo)
            gh_stub = Path(tmp) / "gh-stub.sh"
            counter = Path(tmp) / "counter.log"
            _write_stub_gh(gh_stub, behavior="has-pr", counter_file=counter)
            result = self._run_hook(
                repo,
                "GDD_SKIP_PRE_PUSH_GATE=1 git push origin feature-x",
                extra_env={
                    "GDD_HOOK_STATE_DIR": str(Path(tmp) / "hookstate"),
                    "GDD_REVIEW_FOLLOWUP_GH_BIN": str(gh_stub),
                },
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), "")
            self.assertFalse(counter.exists(), "gh must not be invoked when opted out")

    def test_kill_switch_suppresses_injection(self) -> None:
        with tempfile.TemporaryDirectory(prefix="gdd-rfn-") as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            self._init_repo(repo)
            gh_stub = Path(tmp) / "gh-stub.sh"
            counter = Path(tmp) / "counter.log"
            _write_stub_gh(gh_stub, behavior="has-pr", counter_file=counter)
            home = Path(tmp) / "home"
            (home / ".claude").mkdir(parents=True)
            (home / ".claude" / "gdd-hooks-disabled").write_text("", encoding="utf-8")
            result = self._run_hook(
                repo,
                "git push origin feature-x",
                extra_env={
                    "HOME": str(home),
                    "GDD_HOOK_STATE_DIR": str(Path(tmp) / "hookstate"),
                    "GDD_REVIEW_FOLLOWUP_GH_BIN": str(gh_stub),
                },
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), "")
            self.assertFalse(counter.exists())

    def test_fires_regardless_of_active_gdd_marker(self) -> None:
        """Opus advisory 実測により active でも既存 gate が無言通過しうるため、
        この nudge hook は active: true の有無に関わらず発火する（案B）。"""
        with tempfile.TemporaryDirectory(prefix="gdd-rfn-") as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            self._init_repo(repo)
            state_dir = repo / ".claude"
            state_dir.mkdir(exist_ok=True)
            (state_dir / "gdd-dev.local.md").write_text(
                "---\nactive: true\nsession_id: other-session\n---\n",
                encoding="utf-8",
            )
            gh_stub = Path(tmp) / "gh-stub.sh"
            _write_stub_gh(gh_stub, behavior="has-pr")
            result = self._run_hook(
                repo,
                "git push origin feature-x",
                extra_env={
                    "GDD_HOOK_STATE_DIR": str(Path(tmp) / "hookstate"),
                    "GDD_REVIEW_FOLLOWUP_GH_BIN": str(gh_stub),
                },
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("additionalContext", result.stdout)

    def test_env_without_home_does_not_crash(self) -> None:
        """独立レビューで検出（blocking）: `STATE_DIR="${GDD_HOOK_STATE_DIR:-${HOME}/...}"`
        は HOME 未設定・GDD_HOOK_STATE_DIR 未設定のとき set -u で shell ごと即死し、
        kill switch 直後・全ロジック前に落ちていた（self-review-evidence.sh が同種の
        問題を修正済みの旧パターンを本 hook が再導入していた）。"""
        with tempfile.TemporaryDirectory(prefix="gdd-rfn-") as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            self._init_repo(repo)
            gh_stub = Path(tmp) / "gh-stub.sh"
            _write_stub_gh(gh_stub, behavior="has-pr")
            env = os.environ.copy()
            env.update({"CLAUDE_PLUGIN_ROOT": str(PLUGIN_ROOT), "GDD_REVIEW_FOLLOWUP_GH_BIN": str(gh_stub)})
            env.pop("HOME", None)
            env.pop("GDD_HOOK_STATE_DIR", None)
            payload = {"tool_name": "Bash", "tool_input": {"command": "git push origin feature-x"}}
            result = subprocess.run(
                ["bash", str(HOOK)],
                cwd=repo,
                input=json.dumps(payload),
                capture_output=True,
                text=True,
                env=env,
                check=False,
                timeout=HANG_GUARD,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertNotIn("unbound variable", result.stderr)
            self.assertIn("additionalContext", result.stdout)

    def test_no_pr_result_is_logged_as_skipped(self) -> None:
        """独立レビューで検出: injected/undeterminable しか記録されず、「PR なしで
        正しく no-op した」と「hook が壊れていた」を再計測手順で区別できなかった。"""
        with tempfile.TemporaryDirectory(prefix="gdd-rfn-") as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            self._init_repo(repo)
            gh_stub = Path(tmp) / "gh-stub.sh"
            _write_stub_gh(gh_stub, behavior="no-pr")
            state_dir = Path(tmp) / "hookstate"
            result = self._run_hook(
                repo,
                "git push origin feature-x",
                extra_env={
                    "GDD_HOOK_STATE_DIR": str(state_dir),
                    "GDD_REVIEW_FOLLOWUP_GH_BIN": str(gh_stub),
                },
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            log_text = (state_dir / "review-followup-nudge.log").read_text(encoding="utf-8")
            self.assertIn("event: skipped", log_text)
            self.assertIn("no-pr", log_text)

    def test_optout_is_logged_as_skipped(self) -> None:
        with tempfile.TemporaryDirectory(prefix="gdd-rfn-") as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            self._init_repo(repo)
            gh_stub = Path(tmp) / "gh-stub.sh"
            counter = Path(tmp) / "counter.log"
            _write_stub_gh(gh_stub, behavior="has-pr", counter_file=counter)
            state_dir = Path(tmp) / "hookstate"
            result = self._run_hook(
                repo,
                "git push origin feature-x",
                extra_env={
                    "GDD_HOOK_STATE_DIR": str(state_dir),
                    "GDD_REVIEW_FOLLOWUP_GH_BIN": str(gh_stub),
                    "GDD_SKIP_PRE_PUSH_GATE": "1",
                },
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse(counter.exists())
            log_text = (state_dir / "review-followup-nudge.log").read_text(encoding="utf-8")
            self.assertIn("event: skipped", log_text)
            self.assertIn("optout", log_text)

    def test_log_does_not_contain_raw_repo_path(self) -> None:
        with tempfile.TemporaryDirectory(prefix="gdd-rfn-") as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            self._init_repo(repo)
            gh_stub = Path(tmp) / "gh-stub.sh"
            _write_stub_gh(gh_stub, behavior="has-pr")
            state_dir = Path(tmp) / "hookstate"
            result = self._run_hook(
                repo,
                "git push origin feature-x",
                extra_env={
                    "GDD_HOOK_STATE_DIR": str(state_dir),
                    "GDD_REVIEW_FOLLOWUP_GH_BIN": str(gh_stub),
                },
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            log_text = (state_dir / "review-followup-nudge.log").read_text(encoding="utf-8")
            self.assertNotIn(str(repo), log_text)

    def test_nudge_message_does_not_assert_push_already_completed(self) -> None:
        """人間レビュー指摘 Medium: additionalContext は PreToolUse 時点
        （push 実行前）で作られるが、旧文言は「push しました」と完了を断定
        していた。過検出の残存ケース（コマンド先頭以外での出現）を完全には
        塞ぎきれない以上、文言側も断定を避け条件法にする。"""
        with tempfile.TemporaryDirectory(prefix="gdd-rfn-") as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            self._init_repo(repo)
            gh_stub = Path(tmp) / "gh-stub.sh"
            _write_stub_gh(gh_stub, behavior="has-pr")
            result = self._run_hook(
                repo,
                "git push origin feature-x",
                extra_env={
                    "GDD_HOOK_STATE_DIR": str(Path(tmp) / "hookstate"),
                    "GDD_REVIEW_FOLLOWUP_GH_BIN": str(gh_stub),
                },
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            ctx = payload["hookSpecificOutput"]["additionalContext"]
            self.assertNotIn("push しました", ctx)
            # 独立レビュー round 4 指摘 Low: 「push しました」の不在だけでは
            # 「push が完了しました」等の言い換えを見逃す。条件法の文言が
            # 実際に含まれることも positive に固定する。
            self.assertIn("成功した場合", ctx)

    def test_nudge_message_distinguishes_gdd_active_skill_name(self) -> None:
        """人間レビュー指摘 Medium: hook は active/非active を問わず常に発火
        するが（案B）、文言が汎用 `pr-review-followup` だけを指すと、GDD
        active session 下では証跡形式が state.md 側と食い違い、直後の
        pre-push gate で不足として通知されうる。両方の skill 名と使い分けを 1 行で
        示す。"""
        with tempfile.TemporaryDirectory(prefix="gdd-rfn-") as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            self._init_repo(repo)
            gh_stub = Path(tmp) / "gh-stub.sh"
            _write_stub_gh(gh_stub, behavior="has-pr")
            result = self._run_hook(
                repo,
                "git push origin feature-x",
                extra_env={
                    "GDD_HOOK_STATE_DIR": str(Path(tmp) / "hookstate"),
                    "GDD_REVIEW_FOLLOWUP_GH_BIN": str(gh_stub),
                },
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            ctx = payload["hookSpecificOutput"]["additionalContext"]
            self.assertIn("gdd-pr-review-followup", ctx)
            # 独立レビュー round 4 指摘 Low: "gdd-pr-review-followup" は
            # "pr-review-followup" を部分文字列として含むため、
            # assertIn("pr-review-followup", ctx) だけでは「汎用名を単独で
            # 案内していない」ことを固定できない。汎用名が active 以外の
            # 分岐として独立に出現することを、より具体的な文言で固定する。
            self.assertIn("それ以外では pr-review-followup", ctx)

    def test_brace_group_optout_is_honored(self) -> None:
        """PR #88 人間レビュー round 5 指摘 Medium: round 4 で push 検出だけ
        `{` を command-start に含めた結果、`{ GDD_SKIP_PRE_PUSH_GATE=1 git
        push ...; }` のような brace group 内では「push とは判定するのに
        opt-out は無視する」非対称があり、認証付き `gh` が呼ばれていた。"""
        with tempfile.TemporaryDirectory(prefix="gdd-rfn-") as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            self._init_repo(repo)
            gh_stub = Path(tmp) / "gh-stub.sh"
            counter = Path(tmp) / "counter.log"
            _write_stub_gh(gh_stub, behavior="has-pr", counter_file=counter)
            state_dir = Path(tmp) / "hookstate"
            result = self._run_hook(
                repo,
                "{ GDD_SKIP_PRE_PUSH_GATE=1 git push origin feature-x; }",
                extra_env={
                    "GDD_HOOK_STATE_DIR": str(state_dir),
                    "GDD_REVIEW_FOLLOWUP_GH_BIN": str(gh_stub),
                },
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), "")
            self.assertFalse(counter.exists(), "brace group 内の opt-out で gh を呼んではならない")
            log_text = (state_dir / "review-followup-nudge.log").read_text(encoding="utf-8")
            self.assertIn("event: skipped", log_text)
            self.assertIn("optout", log_text)

    def test_hook_is_wired_in_hooks_json(self) -> None:
        config = json.loads(HOOKS_JSON.read_text(encoding="utf-8"))
        commands = [
            hook.get("command", "")
            for matcher in config["hooks"].get("PreToolUse", [])
            for hook in matcher.get("hooks", [])
        ]
        self.assertTrue(
            any("run-review-followup-nudge-hook.sh" in c for c in commands),
            "new hook must be registered under PreToolUse in hooks.json",
        )


if __name__ == "__main__":
    unittest.main()
