"""Stop hook の stop 理由・`<gdd-stop>` marker・Goal の完了・post-merge 継続の誤検知の単体テスト。

`test_stop_hook_unit.py` から分けた。確かめる本体は `hooks/scripts/gdd_stop_hook.py`・`hooks/scripts/lib/constants.py`・`hooks/scripts/lib/guards.py`・`hooks/scripts/lib/transcript.py`・`hooks/scripts/lib/post_merge_continuation.py`。
"""
from __future__ import annotations
# isort: skip_file
# ruff: noqa: F401,F811
import sys
from pathlib import Path as _P
sys.path.insert(0, str(_P(__file__).parent))
from _stop_hook_test_base import *  # noqa: F403

class TestStopPattern(unittest.TestCase):
    """STOP_PATTERN and ALLOWED_STOP_REASONS."""

    def test_matches_done(self):
        m = STOP_PATTERN.search('<gdd-stop reason="done">')
        self.assertIsNotNone(m)
        self.assertEqual(m.group(1), "done")

    def test_matches_human_check_waiting(self):
        m = STOP_PATTERN.search('<gdd-stop reason="human-check-waiting">')
        self.assertIsNotNone(m)
        self.assertIn(m.group(1), ALLOWED_STOP_REASONS)

    def test_rejects_unknown_reason(self):
        m = STOP_PATTERN.search('<gdd-stop reason="unknown">')
        self.assertIsNotNone(m)
        self.assertNotIn(m.group(1), ALLOWED_STOP_REASONS)

    def test_no_match_on_malformed(self):
        m = STOP_PATTERN.search("<gdd-stop>")
        self.assertIsNone(m)


class TestLastToolResultText(unittest.TestCase):
    """last_tool_result_text() extracts <gdd-stop> from Agent tool results.

    When gdd-brainstorming runs as a subagent via Agent(), its output
    (including <gdd-stop>) lands in a tool_result of role=user, not in
    assistant text. These tests verify the fallback scanner.
    """

    def _make_transcript(self, lines: list[dict]) -> Path:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".jsonl", delete=False, encoding="utf-8"
        ) as f:
            for line in lines:
                f.write(json.dumps(line, ensure_ascii=False) + "\n")
            return Path(f.name)

    def test_extracts_stop_marker_from_string_content(self):
        """Subagent outputs <gdd-stop> as a plain string in tool_result content."""
        path = self._make_transcript([
            {
                "type": "user",
                "message": {
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": "tu1",
                            "content": '## 🔍 確認をお願いします\n...\n<gdd-stop reason="human-check-waiting">',
                        }
                    ]
                },
            }
        ])
        try:
            text = last_tool_result_text(path)
            m = STOP_PATTERN.search(text)
            self.assertIsNotNone(m)
            self.assertIn(m.group(1), ALLOWED_STOP_REASONS)
        finally:
            path.unlink(missing_ok=True)

    def test_extracts_stop_marker_from_list_content(self):
        """Tool result content as list of text blocks (alternative format)."""
        path = self._make_transcript([
            {
                "type": "user",
                "message": {
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": "tu1",
                            "content": [
                                {
                                    "type": "text",
                                    "text": '確認テンプレート\n<gdd-stop reason="human-check-waiting">',
                                }
                            ],
                        }
                    ]
                },
            }
        ])
        try:
            text = last_tool_result_text(path)
            m = STOP_PATTERN.search(text)
            self.assertIsNotNone(m)
        finally:
            path.unlink(missing_ok=True)

    def test_returns_empty_when_no_tool_result(self):
        """Returns empty string when transcript has only assistant messages."""
        path = self._make_transcript([
            {
                "type": "assistant",
                "message": {
                    "content": [{"type": "text", "text": "承認待ちです"}]
                },
            }
        ])
        try:
            self.assertEqual(last_tool_result_text(path), "")
        finally:
            path.unlink(missing_ok=True)

    def test_returns_last_tool_result_not_first(self):
        """When multiple tool_results exist, returns the last one."""
        path = self._make_transcript([
            {
                "type": "user",
                "message": {
                    "content": [
                        {"type": "tool_result", "tool_use_id": "tu1", "content": "first result"}
                    ]
                },
            },
            {
                "type": "user",
                "message": {
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": "tu2",
                            "content": '最後の確認\n<gdd-stop reason="human-check-waiting">',
                        }
                    ]
                },
            },
        ])
        try:
            text = last_tool_result_text(path)
            self.assertIn("最後の確認", text)
            self.assertNotIn("first result", text)
        finally:
            path.unlink(missing_ok=True)

    def test_ignores_non_tool_result_user_messages(self):
        """User messages that are not tool_result are ignored."""
        path = self._make_transcript([
            {
                "type": "user",
                "message": {
                    "content": [
                        {"type": "text", "text": "OK"}
                    ]
                },
            }
        ])
        try:
            self.assertEqual(last_tool_result_text(path), "")
        finally:
            path.unlink(missing_ok=True)


class TestAllowedStopReasons(unittest.TestCase):
    """Validate ALLOWED_STOP_REASONS constants.

    The workflow_phase fallback (Fallback 2) has been removed as part of
    SSOT migration. These tests verify the stop reason constants remain correct.
    """

    def test_human_check_waiting_is_allowed_stop_reason(self):
        self.assertIn("human-check-waiting", ALLOWED_STOP_REASONS)

    def test_clarification_needed_is_allowed_stop_reason(self):
        self.assertIn("clarification-needed", ALLOWED_STOP_REASONS)

    def test_done_and_cancelled_are_allowed_stop_reasons(self):
        self.assertIn("done", ALLOWED_STOP_REASONS)
        self.assertIn("cancelled", ALLOWED_STOP_REASONS)

    def test_phase_names_do_not_collide_with_stop_reasons(self):
        """Regular GDD phase names must never appear in ALLOWED_STOP_REASONS."""
        phase_names = [
            "gdd-brainstorming",
            "gdd-requirements-gating",
            "gdd-design-gating",
            "gdd-task-breakdown",
            "gdd-test-driven-development",
            "gdd-implementation-gating",
            "gdd-completion-check",
            "gdd-systematic-debugging",
        ]
        for phase in phase_names:
            self.assertNotIn(
                phase, ALLOWED_STOP_REASONS,
                f"Phase name '{phase}' must not collide with ALLOWED_STOP_REASONS",
            )


class TestGoalCompletionGuard(unittest.TestCase):
    """Codex Goal must only complete after the GDD done guard passes."""

    def test_done_is_the_only_goal_complete_reason(self):
        self.assertTrue(goal_completion_allowed_for_stop("done"))
        for reason in ["blocked", "human-check-waiting", "clarification-needed", "cancelled"]:
            with self.subTest(reason=reason):
                self.assertFalse(goal_completion_allowed_for_stop(reason))

    def test_incomplete_stop_reasons_warn_not_to_complete_goal(self):
        for reason in GOAL_INCOMPLETE_REASONS:
            with self.subTest(reason=reason):
                msg = goal_guard_message(reason)
                self.assertIn("Do not mark the thread Goal complete", msg)
                self.assertIn(reason, msg)

    def test_done_goal_guard_allows_goal_completion(self):
        msg = goal_guard_message("done")
        self.assertIn("safe to mark the thread Goal complete", msg)

    def test_unknown_reason_fails_closed_for_goal_completion(self):
        msg = goal_guard_message("workflow_phase")
        self.assertFalse(goal_completion_allowed_for_stop("workflow_phase"))
        self.assertIn("unknown stop reason", msg)
        self.assertIn("Next Action=done", msg)


class TestSubagentStopMarkerIntegration(unittest.TestCase):
    """Regression test for the infinite-loop bug.

    Bug: When gdd-brainstorming runs as Agent() subagent, its <gdd-stop>
    appears in tool_result (role=user), not in assistant text. The original
    stop hook only checked assistant text → loop of 7+ iterations.

    Fix: Fallback 1 scans the last tool_result for <gdd-stop>.
    """

    _make_transcript = TestLastToolResultText._make_transcript

    def test_primary_check_misses_subagent_stop_marker(self):
        """Primary check (assistant text only) does NOT find <gdd-stop> in tool_result."""
        path = self._make_transcript([
            {
                "type": "assistant",
                "message": {
                    "content": [
                        {"type": "tool_use", "id": "tu1", "name": "Agent", "input": {}}
                    ]
                },
            },
            {
                "type": "user",
                "message": {
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": "tu1",
                            "content": '## 🔍 確認をお願いします\n...\n<gdd-stop reason="human-check-waiting">',
                        }
                    ]
                },
            },
            {
                "type": "assistant",
                "message": {
                    "content": [
                        # Main session forgot to include <gdd-stop> — the original bug
                        {"type": "text", "text": "承認待ちです。「OK」とご回答ください。"}
                    ]
                },
            },
        ])
        try:
            assistant_text = last_assistant_text(path)
            m = STOP_PATTERN.search(assistant_text)
            self.assertIsNone(m, "Primary check should NOT detect <gdd-stop> in assistant text when it's absent")
        finally:
            path.unlink(missing_ok=True)

    def test_fallback_detects_subagent_stop_marker_in_tool_result(self):
        """Fallback 1 (tool_result scan) detects <gdd-stop> even when assistant text lacks it."""
        path = self._make_transcript([
            {
                "type": "assistant",
                "message": {
                    "content": [
                        {"type": "tool_use", "id": "tu1", "name": "Agent", "input": {}}
                    ]
                },
            },
            {
                "type": "user",
                "message": {
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": "tu1",
                            "content": '## 🔍 確認をお願いします\n...\n<gdd-stop reason="human-check-waiting">',
                        }
                    ]
                },
            },
            {
                "type": "assistant",
                "message": {
                    "content": [
                        {"type": "text", "text": "承認待ちです。「OK」とご回答ください。"}
                    ]
                },
            },
        ])
        try:
            tool_text = last_tool_result_text(path)
            m = STOP_PATTERN.search(tool_text)
            self.assertIsNotNone(m, "Fallback should find <gdd-stop> in tool_result")
            self.assertIn(m.group(1), ALLOWED_STOP_REASONS)
        finally:
            path.unlink(missing_ok=True)


class TestPostMergeClaudeMdInjectionFalsePositive(unittest.TestCase):
    """GDD CLAUDE.md injection must not trigger the post-merge continuation block.

    Root cause: The GDD CLAUDE.md describes 'マージした' as an
    example keyword in its 'Merge Report Cleanup Trigger' section. When injected
    as a user text block at session start, MANUAL_MERGE_RE (now in
    lib/post_merge_continuation.py) matches it and blocks the
    stop hook even though the user never actually merged.

    Fix: Add '# Gate-Driven Development' to _HOOK_INJECTION_PREFIXES so that
    the CLAUDE.md injection is excluded from last_user_text.
    """

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tmpdir.name)
        (self.root / ".claude").mkdir()

    def tearDown(self):
        self.tmpdir.cleanup()

    def _write_marker(self) -> None:
        import time

        payload = {
            "session_id": "prev-session-abc",
            "created_at_epoch": int(time.time()),
            "tasklist_path": str(self.root / ".steering" / "20260601-test" / "tasklist.md"),
            "pr_url": "https://github.com/example-org/repo/pull/100",
            "status": "pending_manual_merge",
        }
        (self.root / ".claude" / "gdd-post-merge-continuation.json").write_text(
            json.dumps(payload, ensure_ascii=False), encoding="utf-8"
        )

    def _write_transcript(
        self, path: Path, *, last_user_text: str, last_assistant_text: str
    ) -> None:
        lines = [
            json.dumps({
                "type": "user",
                "message": {
                    "role": "user",
                    "content": [{"type": "text", "text": last_user_text}],
                },
            }),
            json.dumps({
                "type": "assistant",
                "message": {
                    "role": "assistant",
                    "content": [{"type": "text", "text": last_assistant_text}],
                },
            }),
        ]
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def test_different_pr_number_does_not_block(self):
        """'#999 をマージした' must not trigger when the marker PR is #100."""
        transcript = self.root / "transcript.jsonl"
        self._write_marker()  # marker PR is pull/100
        self._write_transcript(
            transcript,
            last_user_text="#999 をマージしたので CI を確認してください。",
            last_assistant_text="確認します。",
        )
        rc, stdout, _stderr = _run_hook(self.root, transcript_path=transcript)
        if stdout.strip():
            output = json.loads(stdout.strip())
            self.assertNotEqual(
                output.get("decision"),
                "block",
                f"Must not block for a different PR number. stdout={stdout!r}",
            )
        self.assertEqual(rc, 0)

    def test_different_pr_url_does_not_block(self):
        """A message containing a GitHub URL for a different PR must not trigger."""
        transcript = self.root / "transcript.jsonl"
        self._write_marker()  # marker PR is pull/100
        self._write_transcript(
            transcript,
            last_user_text=(
                "https://github.com/example-org/repo/pull/999 をマージしたので"
                "この実装を進めてください。"
            ),
            last_assistant_text="了解しました。",
        )
        rc, stdout, _stderr = _run_hook(self.root, transcript_path=transcript)
        if stdout.strip():
            output = json.loads(stdout.strip())
            self.assertNotEqual(
                output.get("decision"),
                "block",
                f"Must not block for a different PR URL. stdout={stdout!r}",
            )
        self.assertEqual(rc, 0)

    def test_pr_number_substring_url_does_not_confuse_prs(self):
        """A PR URL like '.../pull/1004' must not be confused with marker '.../pull/100'.

        Regression guard: `_marker_url in u` treated pull/100 as a substring
        match of pull/1004 (a different PR). That false match made the guard
        fail to recognize this as an unrelated PR mention, so it would not
        suppress the block even though the mentioned PR is not the GDD PR.
        """
        transcript = self.root / "transcript.jsonl"
        self._write_marker()  # marker PR is pull/100
        self._write_transcript(
            transcript,
            last_user_text=(
                "https://github.com/example-org/repo/pull/1004 をマージしたので"
                "この実装を進めてください。"
            ),
            last_assistant_text="了解しました。",
        )
        rc, stdout, _stderr = _run_hook(self.root, transcript_path=transcript)
        if stdout.strip():
            output = json.loads(stdout.strip())
            self.assertNotEqual(
                output.get("decision"),
                "block",
                f"Must not block for pull/1004 mistaken as marker pull/100. stdout={stdout!r}",
            )
        self.assertEqual(rc, 0)

    def test_different_repo_same_pr_number_does_not_confuse_prs(self):
        """A same-numbered PR in a different repo must not match the marker's PR.

        Regression guard: comparing only the numeric PR number (ignoring
        owner/repo) would treat 'https://github.com/other/repo/pull/100' as
        the same PR as the marker's 'https://github.com/example-org/repo/pull/100',
        even though they are unrelated PRs in different repositories.
        """
        transcript = self.root / "transcript.jsonl"
        self._write_marker()  # marker PR is https://github.com/example-org/repo/pull/100
        self._write_transcript(
            transcript,
            last_user_text=(
                "https://github.com/other/repo/pull/100 をマージしたので"
                "この実装を進めてください。"
            ),
            last_assistant_text="了解しました。",
        )
        rc, stdout, _stderr = _run_hook(self.root, transcript_path=transcript)
        if stdout.strip():
            output = json.loads(stdout.strip())
            self.assertNotEqual(
                output.get("decision"),
                "block",
                f"Must not block for a same-numbered PR in a different repo. stdout={stdout!r}",
            )
        self.assertEqual(rc, 0)

    def test_betsuno_pr_phrase_wins_even_with_corrupt_marker(self):
        """Explicit "別のPR" wording must suppress the block even if the marker
        file is corrupt/unparseable.

        Regression guard: this check must run before the marker JSON is read,
        so a read/parse failure can never suppress this marker-independent
        signal (which would otherwise fall through to the block).
        """
        transcript = self.root / "transcript.jsonl"
        (self.root / ".claude" / "gdd-post-merge-continuation.json").write_text(
            "{not valid json", encoding="utf-8"
        )
        self._write_transcript(
            transcript,
            last_user_text="別のPRをマージしたので、こちらの実装を進めてください。",
            last_assistant_text="了解しました。",
        )
        rc, stdout, _stderr = _run_hook(self.root, transcript_path=transcript)
        if stdout.strip():
            output = json.loads(stdout.strip())
            self.assertNotEqual(
                output.get("decision"),
                "block",
                f"Must not block despite corrupt marker file. stdout={stdout!r}",
            )
        self.assertEqual(rc, 0)

    def test_betsuno_pr_phrase_does_not_block(self):
        """'別のPRをマージしたからこれをやって' must not trigger the block."""
        transcript = self.root / "transcript.jsonl"
        self._write_marker()
        self._write_transcript(
            transcript,
            last_user_text="別のPRをマージしたからこれをやって",
            last_assistant_text="承知しました。",
        )
        rc, stdout, _stderr = _run_hook(self.root, transcript_path=transcript)
        if stdout.strip():
            output = json.loads(stdout.strip())
            self.assertNotEqual(
                output.get("decision"),
                "block",
                f"Must not block for explicit 'different PR' mention. stdout={stdout!r}",
            )
        self.assertEqual(rc, 0)

    def test_gdd_claude_md_injection_does_not_block(self):
        """GDD CLAUDE.md injection containing 'マージした' must not trigger the block.

        The text below is the structure of the actual GDD CLAUDE.md that is
        injected as a user message at session start. It contains 'マージした' in
        the Merge Report Cleanup Trigger documentation section — NOT as actual
        user intent to merge a PR.
        """
        gdd_claude_md_snippet = (
            "# Gate-Driven Development\n\n"
            "gate-driven-development の steering-first workflow entrypoint。\n\n"
            "### Merge Report Cleanup Trigger\n\n"
            "ユーザーが `マージした` / `mergeした` / `merged` と報告した場合、"
            "それは post-merge verification cue です。"
        )
        transcript = self.root / "transcript.jsonl"
        self._write_marker()
        self._write_transcript(
            transcript,
            last_user_text=gdd_claude_md_snippet,
            last_assistant_text="CI の確認を始めます。",
        )
        rc, stdout, _stderr = _run_hook(self.root, transcript_path=transcript)
        if stdout.strip():
            output = json.loads(stdout.strip())
            self.assertNotEqual(
                output.get("decision"),
                "block",
                "Hook must not block when only GDD CLAUDE.md injection contains "
                f"'マージした'. stdout={stdout!r}",
            )
        self.assertEqual(rc, 0, f"Hook must allow stop. stdout={stdout!r}")

    def test_peer_message_after_manual_merge_report_does_not_reactivate_workflow(self):
        """Copilot レビュー是正 (PR #31 review, commit 6cf2773 への指摘):
        `maybe_block_incomplete_post_merge_continuation()` は `main()` の
        peer-turn guard（Finding Z、`looks_like_gdd_continuation()` 用）より
        **前**に呼ばれるため、その guard の保護を受けない。`[human: "mergeした",
        peer: "..."]` という並びでは、`tv.last_user_text` は peer 除外により
        古い "mergeした" のまま残り、直近の実会話ターンが peer であるにも
        関わらず `decision:block` が出て workflow を再開させてしまっていた。
        「peer message は停止中の workflow を再開させない」という他の権限
        境界と同じ原則を、この経路にも適用したことを確認する。
        """
        transcript = self.root / "transcript.jsonl"
        self._write_marker()
        lines = [
            json.dumps({
                "type": "user",
                "message": {"role": "user", "content": [{"type": "text", "text": "mergeした"}]},
            }),
            json.dumps({
                "type": "assistant",
                "message": {"role": "assistant", "content": [{"type": "text", "text": "確認します"}]},
            }),
            json.dumps({
                "type": "user",
                "origin": {"kind": "peer"},
                "message": {
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                "Another Claude session sent a message:\n"
                                "<cross-session-message>hi</cross-session-message>"
                            ),
                        }
                    ]
                },
            }),
        ]
        transcript.write_text("\n".join(lines) + "\n", encoding="utf-8")
        rc, stdout, _stderr = _run_hook(self.root, transcript_path=transcript)
        if stdout.strip():
            output = json.loads(stdout.strip())
            self.assertNotEqual(
                output.get("decision"),
                "block",
                "peer message の後は古い manual-merge 報告を根拠に再開してはいけない"
                f". stdout={stdout!r}",
            )

    def test_peer_message_then_unreadable_line_does_not_reactivate_workflow(self):
        """peer の後に json.loads が JSONDecodeError 以外で失敗する行（桁の多い整数）があっても、
        古い manual-merge 報告を根拠に再開しない（peer の判定の例外は止める側に倒す）。"""
        transcript = self.root / "transcript.jsonl"
        self._write_marker()
        lines = [
            json.dumps({"type": "user", "message": {"role": "user", "content": [{"type": "text", "text": "mergeした"}]}}),
            json.dumps({"type": "assistant", "message": {"role": "assistant", "content": [{"type": "text", "text": "確認します"}]}}),
            json.dumps({"type": "user", "origin": {"kind": "peer"}, "message": {"content": [{"type": "text", "text": (
                "Another Claude session sent a message:\n<cross-session-message>hi</cross-session-message>")}]}}),
            '{"type": "assistant", "n": ' + "1" * 5000 + "}",
        ]
        with self.assertRaises(ValueError):  # 前提: int の桁数の上限（sys.get_int_max_str_digits）で読めない
            json.loads(lines[-1])
        transcript.write_text("\n".join(lines) + "\n", encoding="utf-8")
        rc, stdout, stderr = _run_hook(self.root, transcript_path=transcript)
        self.assertEqual(rc, 0, stderr)
        if stdout.strip():
            self.assertNotEqual(json.loads(stdout.strip()).get("decision"), "block", stdout)
        log = (self.root / ".gdd" / "hook-errors.log").read_text(encoding="utf-8")
        self.assertIn('"source": "post_merge_precheck"', log)

    def test_manual_merge_report_without_peer_still_blocks(self):
        """false positive ガードの反対側: peer turn が介在しない通常の manual-merge
        報告は、上記の peer guard 追加後も引き続き block されなければならない。
        """
        transcript = self.root / "transcript.jsonl"
        self._write_marker()
        self._write_transcript(
            transcript,
            last_user_text="mergeした",
            last_assistant_text="確認します",
        )
        rc, stdout, _stderr = _run_hook(self.root, transcript_path=transcript)
        self.assertTrue(stdout.strip(), "peer turn が無い通常の manual-merge 報告は block されなければならない")
        output = json.loads(stdout.strip())
        self.assertEqual(output.get("decision"), "block")


if __name__ == "__main__":
    unittest.main()
