"""引用符が閉じない行の字句解析（`git_command_parse._lex_segment` の fallback）のテスト。

字句解析の芯（`shell_lexer.lex`）は引用符を行をまたいで追い、引用符の外の改行で分ける。
引用符が末尾まで閉じない片は shlex が ValueError になるので、引用符を見ずに割る
（縮退）。そのとき空白だけで割ると `2>&1|tail` が 1 token のまま残り、
`classify_refspec` が 2 つ目の refspec と読んで ambiguous を返していた。fallback でも
区切り記号の連を別の token に割る。縮退したときは、行ごとの読み（`_lex_by_line`。
引用符を行をまたいで追わない）でも push を探し、検出は 2 つの読みの和にする。

heredoc の本文は芯に渡す前に取り出し、別のコマンドとして読む。本文のアポストロフィで
引用符を追い違え、後ろの `git push` を飲み込まないためである。
"""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

from _paths import PLUGIN_ROOT
from _pre_push_gate_support import PrePushGateFixtureMixin
from _review_followup_nudge_support import ReviewFollowupNudgeFixtureMixin, _write_stub_gh
from _root_branch_guard_support import RootBranchGuardFixtureMixin

sys.path.insert(0, str(PLUGIN_ROOT / "hooks" / "scripts" / "lib"))

import git_command_parse as gcp  # noqa: E402
import push_command_parse as pcp  # noqa: E402

# 起点の形（GDD を使う別の repo の PR で nudge が一度も出なかった push）。
COMMIT_AND_PUSH = (
    'git add -A && git commit -q -m "fix: 件名\n\n'
    'Co-Authored-By: X <x@example.com>" && git push -q origin HEAD 2>&1|tail -1; echo $H'
)
COMMIT_AND_PUSH_SPACED = (
    'git commit -q -m "fix: 件名\n\nCo-Authored-By: X <x@example.com>" '
    "&& git push -q origin HEAD 2>&1 | tail -1"
)
COMMIT_AND_PUSH_SINGLE_QUOTE = (
    "git commit -q -m 'fix: a\n\nb' && git push -q origin topic 2>&1|tail -1"
)
COMMIT_AND_PUSH_HEREDOC_SUBST = (
    "git commit -m \"$(cat <<'EOF'\nfix: a\n\nCo-Authored-By: X <x@example.com>\nEOF\n)\" "
    "&& git push origin HEAD 2>&1|tail -1"
)
COMMIT_AND_PUSH_COLON_REFSPEC = (
    'git commit -q -m "fix: a\n\nb" && git push -q origin HEAD:refs/heads/topic 2>&1|tail -1; echo'
)


def _push_target(command: str) -> dict:
    tokens, raw = pcp.tokenize_with_boundary(command)
    found, git_index = pcp.is_git_push_at_command_start(tokens, raw)
    if not found:
        return {"detected": False}
    return {"detected": True, **pcp.classify_refspec(tokens, git_index)}


class FallbackTokenizeTests(unittest.TestCase):
    def test_multiline_commit_message_then_push_resolves_refspec(self) -> None:
        for command, ref in (
            (COMMIT_AND_PUSH, "HEAD"),
            (COMMIT_AND_PUSH_SPACED, "HEAD"),
            (COMMIT_AND_PUSH_SINGLE_QUOTE, "topic"),
            (COMMIT_AND_PUSH_HEREDOC_SUBST, "HEAD"),
            (COMMIT_AND_PUSH_COLON_REFSPEC, "HEAD"),
        ):
            with self.subTest(command=command):
                self.assertEqual(
                    _push_target(command),
                    {"detected": True, "ambiguous": False, "explicit_ref": ref},
                )

    def test_two_refspecs_on_fallback_line_stay_ambiguous(self) -> None:
        """判定できない形は、fallback の行でも ambiguous のまま残る。"""
        command = 'git commit -m "a\nb" && git push origin one two 2>&1|tail -1'
        self.assertEqual(
            _push_target(command),
            {"detected": True, "ambiguous": True, "explicit_ref": None},
        )

    def test_fallback_keeps_operator_runs_together(self) -> None:
        """区切り記号の連は 1 token に保つ（`>|` を `>`＋`|` に割らない）。"""
        self.assertEqual(
            gcp._lex_segment('b" && git switch >|f -c x 2>&1|tail'),
            ['b"', "&&", "git", "switch", ">|", "f", "-c", "x", "2", ">&", "1", "|", "tail"],
        )

    def test_fallback_splits_glued_operators_off_words(self) -> None:
        """語に密着した区切り記号を割り、区切り記号の連は 1 token に保つ。"""
        for segment, expected in (
            ('"', ['"']),
            ('a "b', ["a", '"b']),
            ("it's;git push", ["it's", ";", "git", "push"]),
            ('b"&&GDD_SKIP_PRE_PUSH_GATE=1 git push', ['b"', "&&", "GDD_SKIP_PRE_PUSH_GATE=1", "git", "push"]),
            ('"\t;;(|&<>)', ['"', ";;(|&<>)"]),
        ):
            with self.subTest(segment=segment):
                self.assertEqual(gcp._lex_segment(segment), expected)

    def test_heredoc_apostrophe_does_not_hide_following_push(self) -> None:
        """heredoc の本文のアポストロフィで、終端の後の `git push` を見逃さない。"""
        for body in ("it's", "it's and it's"):
            command = f"cat > f <<'EOF'\n{body}\nEOF\ngit push origin main"
            with self.subTest(body=body):
                self.assertEqual(
                    _push_target(command),
                    {"detected": True, "ambiguous": False, "explicit_ref": "main"},
                )

    def test_comment_apostrophe_does_not_hide_following_push(self) -> None:
        command = "# don't forget\n# let's go\ngit push origin main"
        self.assertEqual(
            _push_target(command),
            {"detected": True, "ambiguous": False, "explicit_ref": "main"},
        )


class NudgeHookFallbackTests(ReviewFollowupNudgeFixtureMixin, unittest.TestCase):
    def test_commit_and_push_in_one_command_injects_nudge(self) -> None:
        for command in (COMMIT_AND_PUSH, COMMIT_AND_PUSH_SPACED):
            with self.subTest(command=command), tempfile.TemporaryDirectory(prefix="gdd-lfs-") as tmp:
                repo = Path(tmp) / "repo"
                repo.mkdir()
                self._init_repo(repo, branch="topic-branch")
                gh_stub = Path(tmp) / "gh-stub.sh"
                args_file = Path(tmp) / "args.log"
                _write_stub_gh(gh_stub, behavior="has-pr", args_file=args_file)
                result = self._run_hook(
                    repo,
                    command,
                    extra_env={
                        "GDD_HOOK_STATE_DIR": str(Path(tmp) / "hookstate"),
                        "GDD_REVIEW_FOLLOWUP_GH_BIN": str(gh_stub),
                    },
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("[review-followup]", result.stdout)
                self.assertEqual(args_file.read_text(encoding="utf-8").strip(), "topic-branch")


class PrePushGateFallbackTests(PrePushGateFixtureMixin, unittest.TestCase):
    def test_commit_and_push_without_evidence_blocks_for_missing_evidence(self) -> None:
        """refspec-ambiguous で止めず、証跡の検査まで進んで止める（block のまま）。"""
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            self._init_repo(repo)
            self._write_local_state(repo, active=True)
            self._write_steering(repo, task_size="standard")
            result = self._run_hook(
                repo,
                COMMIT_AND_PUSH,
                extra_env={"GDD_HOOK_STATE_DIR": str(Path(tmp) / "hookstate")},
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["hookSpecificOutput"]["hookEventName"], "PreToolUse")
            self.assertNotIn("refspec-ambiguous", payload["hookSpecificOutput"]["additionalContext"])
            self.assertIn("missing-evidence", payload["hookSpecificOutput"]["additionalContext"])


class RootBranchGuardFallbackTests(RootBranchGuardFixtureMixin, unittest.TestCase):
    def test_branch_creation_on_fallback_line_is_denied(self) -> None:
        """引用符が閉じない行の後ろの branch の作成を止める。`;` が語に密着した 3 つ目は、
        変更前は `b";git` が 1 token に残って見落としていた。1・2 つ目は変更前も止めていた
        （区切り記号の連を割らないことの固定）。"""
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            self._write_active_state(repo)
            for command in (
                'git commit -m "a\nb" && git switch >|f -c codex/20261007-a',
                'git commit -m "a\nb" && git switch &>/dev/null -c codex/20261007-b',
                'git commit -m "a\nb";git switch -c codex/20261007-c',
            ):
                with self.subTest(command=command):
                    result = self._run_guard(repo, command)
                    self.assertEqual(result.returncode, 2, result.stderr)

    def test_option_of_next_command_is_not_read_as_checkout_option(self) -> None:
        """`; git status -sb` の `-sb` を、前の `git checkout` の `-b` と読まない。
        変更前は `main;` で `;` が割れず、`git status -sb` が同じ segment に入って
        branch の作成と読まれていた（実データで誤って止めていた形）。"""
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._init_repo(repo)
            self._write_active_state(repo)
            result = self._run_guard(
                repo,
                'git commit -qm "a\nb" && git push 2>&1 | grep -v \'^remote\'; '
                "git checkout -q main; git status -sb",
            )
            self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
