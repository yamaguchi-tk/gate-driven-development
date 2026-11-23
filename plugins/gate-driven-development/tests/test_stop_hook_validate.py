from __future__ import annotations
# isort: skip_file
# ruff: noqa: F401,F811
import sys
from pathlib import Path as _P
sys.path.insert(0, str(_P(__file__).parent))
from _stop_hook_test_base import *  # noqa: F401,F403
from lib.transcript import parse_transcript

_VALIDATE_PATH = (
    Path(__file__).parent.parent / "hooks" / "scripts" / "validate-steering-write.py"
).resolve()


def _run_validate(payload: dict, state_dir: Path | None = None) -> tuple[int, str, str]:
    """Run validate-steering-write.py with stdin payload. Returns (exit, stdout, stderr)."""
    env = os.environ.copy()
    _tmp = tempfile.TemporaryDirectory() if state_dir is None else None
    try:
        env["GDD_HOOK_STATE_DIR"] = _tmp.name if _tmp is not None else str(state_dir)
        result = _subprocess.run(
            ["python3", str(_VALIDATE_PATH)],
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            env=env,
        )
        return result.returncode, result.stdout, result.stderr
    finally:
        if _tmp is not None:
            _tmp.cleanup()


class TestValidateSteeringWrite(unittest.TestCase):
    """validate-steering-write.py: PreToolUse gate on .steering/ writes."""

    def test_non_steering_path_allowed(self):
        """Writes outside .steering/ pass through unconditionally."""
        with tempfile.TemporaryDirectory() as state:
            code, out, _ = _run_validate({
                "tool_name": "Write",
                "tool_input": {"file_path": "src/main.py", "content": "Contact: alice@company.com\n"},
            }, state_dir=Path(state))
            self.assertEqual(code, 0)
            self.assertIn('"continue": true', out)

    def test_steering_clean_content_allowed(self):
        with tempfile.TemporaryDirectory() as state:
            code, out, _ = _run_validate({
                "tool_name": "Write",
                "tool_input": {
                    "file_path": ".steering/20260501-task/requirements.md",
                    "content": "# 要件\n\n相対パス: scripts/foo.py を変更する。\n",
                },
            }, state_dir=Path(state))
            self.assertEqual(code, 0)
            self.assertIn('"continue": true', out)

    def test_steering_with_real_email_denied(self):
        with tempfile.TemporaryDirectory() as state:
            code, out, err = _run_validate({
                "tool_name": "Write",
                "tool_input": {
                    "file_path": ".steering/20260501-task/requirements.md",
                    "content": "Contact: alice@company.com for review",
                },
            }, state_dir=Path(state))
            self.assertEqual(code, 2)
            self.assertIn("alice@company.com", err)
            payload = json.loads(err.strip().splitlines()[-1])
            self.assertEqual(
                payload["hookSpecificOutput"]["permissionDecision"], "deny"
            )

    def test_example_email_domain_allowed(self):
        """example.com / example.org / localhost domains are whitelisted."""
        with tempfile.TemporaryDirectory() as state:
            code, out, _ = _run_validate({
                "tool_name": "Write",
                "tool_input": {
                    "file_path": ".steering/20260501-task/design.md",
                    "content": "サンプル: user@example.com を仮の宛先として使う。",
                },
            }, state_dir=Path(state))
            self.assertEqual(code, 0)

    def test_local_absolute_path_denied(self):
        with tempfile.TemporaryDirectory() as state:
            code, _, err = _run_validate({
                "tool_name": "Write",
                "tool_input": {
                    "file_path": ".steering/20260501-task/design.md",
                    "content": "See /Users/alice/secret/notes.md for context",
                },
            }, state_dir=Path(state))
            self.assertEqual(code, 2)
            self.assertIn("/Users/alice", err)

    def test_active_worktree_path_exception_allowed(self):
        """Lines containing 'Active Worktree Path' bypass the local-path check.
        worktree paths legitimately appear in state.md as documentation."""
        with tempfile.TemporaryDirectory() as state:
            code, _, _ = _run_validate({
                "tool_name": "Write",
                "tool_input": {
                    "file_path": ".steering/20260501-task/state.md",
                    "content": "- Active Worktree Path: /Users/alice/work/repo\n",
                },
            }, state_dir=Path(state))
            self.assertEqual(code, 0)

    def test_worktree_field_exception_allowed(self):
        """`- Worktree: <path>` (RED Evidence's required field, per
        `gdd-test-driven-development/SKILL.md` § Worktree Binding) bypasses the
        local-path check, mirroring the existing `Active Worktree Path` exception."""
        with tempfile.TemporaryDirectory() as state:
            code, _, _ = _run_validate({
                "tool_name": "Write",
                "tool_input": {
                    "file_path": ".steering/20260501-task/tasklist.md",
                    "content": "- Worktree: /Users/alice/.gdd/worktrees/repo/20260501-task\n",
                },
            }, state_dir=Path(state))
            self.assertEqual(code, 0)

    def test_worktree_word_elsewhere_in_line_still_denied(self):
        """Fail-open guard: the exception is anchored to the `- Worktree:` field
        line, not a bare substring match. A local path leaked in prose that merely
        mentions the word must still be denied."""
        with tempfile.TemporaryDirectory() as state:
            code, _, err = _run_validate({
                "tool_name": "Write",
                "tool_input": {
                    "file_path": ".steering/20260501-task/design.md",
                    "content": "この Worktree の実体は /Users/alice/secret/notes.md にある\n",
                },
            }, state_dir=Path(state))
            self.assertEqual(code, 2)
            self.assertIn("/Users/alice", err)

    def test_worktree_field_line_with_appended_path_still_denied(self):
        """Fail-open guard: the exception must cover only the field's own value,
        not the rest of the line. A line that starts with the legitimate
        `- Worktree:` field but smuggles a second, unrelated local path after it
        must still be denied for that second path."""
        with tempfile.TemporaryDirectory() as state:
            code, _, err = _run_validate({
                "tool_name": "Write",
                "tool_input": {
                    "file_path": ".steering/20260501-task/tasklist.md",
                    "content": (
                        "- Worktree: /Users/alice/.gdd/worktrees/repo/task"
                        " -- see also /Users/alice/.ssh/id_rsa for context\n"
                    ),
                },
            }, state_dir=Path(state))
            self.assertEqual(code, 2)
            self.assertIn("/Users/alice", err)

    def test_todo_in_steering_write_is_allowed(self):
        """TBD / TODO などの語は検出しない（自己レビューの証跡の行を止めていた）。"""
        with tempfile.TemporaryDirectory() as state:
            code, out, err = _run_validate({
                "tool_name": "Write",
                "tool_input": {
                    "file_path": ".steering/20260501-task/tasklist.md",
                    "content": "- Stub grep: TODO なし\n実装方針: TBD\n",
                },
            }, state_dir=Path(state))
            self.assertEqual(code, 0, err)
            self.assertIn('"continue": true', out)

    def test_todo_with_email_is_denied_by_email_only(self):
        """TODO と email を含む書き込みは email で止まり、TODO は理由に出ない。"""
        with tempfile.TemporaryDirectory() as state:
            code, _, err = _run_validate({
                "tool_name": "Write",
                "tool_input": {
                    "file_path": ".steering/20260501-task/requirements.md",
                    "content": "TODO: alice@company.com に確認する\n",
                },
            }, state_dir=Path(state))
            self.assertEqual(code, 2)
            self.assertIn("alice@company.com", err)
            self.assertNotIn("placeholder expression", err)

    def test_ellipsis_omission_marker_denied(self):
        with tempfile.TemporaryDirectory() as state:
            code, _, err = _run_validate({
                "tool_name": "Write",
                "tool_input": {
                    "file_path": ".steering/20260501-task/requirements.md",
                    "content": "AC-01: 入力例:\n```\nfield_a: value\n...省略\nfield_z: value\n```\n",
                },
            }, state_dir=Path(state))
            self.assertEqual(code, 2)
            # validate-steering-write.py uses default json.dumps (ensure_ascii=True),
            # so 省略 is escape-encoded. Parse the JSON and check the decoded message.
            payload = json.loads(err.strip().splitlines()[-1])
            self.assertIn("省略", payload["systemMessage"])
            self.assertEqual(
                payload["hookSpecificOutput"]["permissionDecision"], "deny"
            )

    def test_state_md_missing_started_at_denied(self):
        with tempfile.TemporaryDirectory() as state:
            code, _, err = _run_validate({
                "tool_name": "Write",
                "tool_input": {
                    "file_path": ".steering/20260501-task/state.md",
                    "content": (
                        "# State\n\n"
                        "## Gate Status\n"
                        "- Human Check Status=approved | evidence: hc\n"
                        "- Resume From=gdd-design-gating\n"
                        "- Route In Progress=none\n"
                    ),
                },
            }, state_dir=Path(state))
            self.assertEqual(code, 2)
            payload = json.loads(err.strip().splitlines()[-1])
            self.assertIn("Started At", payload["systemMessage"])
            self.assertEqual(
                payload["hookSpecificOutput"]["permissionDecision"], "deny"
            )

    def test_state_md_with_started_at_allowed(self):
        with tempfile.TemporaryDirectory() as state:
            code, out, _ = _run_validate({
                "tool_name": "Write",
                "tool_input": {
                    "file_path": ".steering/20260501-task/state.md",
                    "content": (
                        "# State\n\n"
                        "## Metadata\n"
                        "- Started At: 2026-05-06T00:00:00Z\n\n"
                        "## Gate Status\n"
                        "- Human Check Status=approved | evidence: hc\n"
                        "- Resume From=gdd-design-gating\n"
                        "- Route In Progress=none\n"
                    ),
                },
            }, state_dir=Path(state))
            self.assertEqual(code, 0)
            self.assertIn('"continue": true', out)

    def test_consecutive_denies_escalate_to_warning(self):
        """3rd consecutive deny on the same (path, category) triggers escape hatch → allow with warning.
        Counter resets after escape so the next violation is a normal deny again."""
        with tempfile.TemporaryDirectory() as state:
            payload = {
                "tool_name": "Write",
                "tool_input": {
                    "file_path": ".steering/20260501-task/design.md",
                    "content": "入力例:\n...省略\n",
                },
            }
            # Attempts 1, 2: deny
            for _ in range(2):
                code, _, _ = _run_validate(payload, state_dir=Path(state))
                self.assertEqual(code, 2)
            # Attempt 3: counter reaches MAX_CONSECUTIVE_DENIES → escape hatch
            code, out, _ = _run_validate(payload, state_dir=Path(state))
            self.assertEqual(code, 0, "3rd consecutive deny must escape to warning")
            self.assertIn("HUMAN REVIEW REQUIRED", out)
            self.assertIn("escaping to warning mode", out)

    def test_apply_patch_added_lines_scanned(self):
        """ApplyPatch: only added (+) lines should be scanned for violations."""
        patch = textwrap.dedent("""\
            *** Begin Patch
            *** Update File: .steering/20260501-task/design.md
            @@
            -old line that mentions /Users/alice/old (removed, should not block)
            +new line: contact bob@company.com
            *** End Patch
        """)
        with tempfile.TemporaryDirectory() as state:
            code, _, err = _run_validate({
                "tool_name": "ApplyPatch",
                "tool_input": {"patch": patch},
            }, state_dir=Path(state))
            # Added line has an email → deny. Removed line has /Users/ but it's not added.
            self.assertEqual(code, 2)
            self.assertIn("bob@company.com", err)
            self.assertNotIn("/Users/alice/old", err)


# ---------------------------------------------------------------------------
# OT-F1: subagent_in_flight() — unit tests (imported from lib.transcript)
# ---------------------------------------------------------------------------


class TestSubagentInFlightUnit(unittest.TestCase):
    """Unit tests for the subagent_in_flight() helper."""

    def _write(self, tmp: str, items: list[dict]) -> Path:
        p = Path(tmp) / "transcript.jsonl"
        p.write_text("\n".join(json.dumps(i) for i in items) + "\n", encoding="utf-8")
        return p

    def test_no_tool_use_returns_false(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = self._write(tmp, [
                {"type": "user", "message": {"content": [{"type": "text", "text": "go"}]}},
                {"type": "assistant", "message": {"content": [{"type": "text", "text": "ok"}]}},
            ])
            self.assertFalse(subagent_in_flight(p))

    def test_tool_use_with_matching_tool_result_returns_false(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = self._write(tmp, [
                {"type": "assistant", "message": {"content": [
                    {"type": "tool_use", "id": "abc123", "name": "Task", "input": {}},
                ]}},
                {"type": "user", "message": {"content": [
                    {"type": "tool_result", "tool_use_id": "abc123", "content": "done"},
                ]}},
                {"type": "assistant", "message": {"content": [{"type": "text", "text": "finished"}]}},
            ])
            self.assertFalse(subagent_in_flight(p))

    def test_tool_use_without_tool_result_returns_true(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = self._write(tmp, [
                {"type": "user", "message": {"content": [{"type": "text", "text": "/gdd-dev"}]}},
                {"type": "assistant", "message": {"content": [
                    {"type": "text", "text": "dispatching..."},
                    {"type": "tool_use", "id": "xyz999", "name": "Task", "input": {}},
                ]}},
            ])
            self.assertTrue(subagent_in_flight(p))

    def test_partial_tool_results_still_in_flight_across_text_only_turn(self):
        """Two tool_use ids in turn 1, only one resolved; turn 2 (last) is text-only → still True.
        A dispatch stays in-flight until its own tool_result arrives, regardless of how
        many text-only turns pass in between (in one session the stale continuation
        nudge fired repeatedly while a task-breakdown subagent was still running;
        reproduced and fixed)."""
        with tempfile.TemporaryDirectory() as tmp:
            p = self._write(tmp, [
                {"type": "assistant", "message": {"content": [
                    {"type": "tool_use", "id": "id1", "name": "Task", "input": {}},
                    {"type": "tool_use", "id": "id2", "name": "Task", "input": {}},
                ]}},
                {"type": "user", "message": {"content": [
                    {"type": "tool_result", "tool_use_id": "id1", "content": "ok"},
                ]}},
                {"type": "assistant", "message": {"content": [{"type": "text", "text": "waiting"}]}},
            ])
            # id2 has no tool_result yet, even though the last assistant turn had no tool_use
            self.assertTrue(subagent_in_flight(p))

    def test_earlier_assistant_turn_dispatch_counts_until_resolved(self):
        """A Task/Agent dispatched several turns ago, once resolved, no longer counts."""
        with tempfile.TemporaryDirectory() as tmp:
            p = self._write(tmp, [
                {"type": "assistant", "message": {"content": [
                    {"type": "tool_use", "id": "old_id", "name": "Task", "input": {}},
                ]}},
                {"type": "user", "message": {"content": [
                    {"type": "tool_result", "tool_use_id": "old_id", "content": "ok"},
                ]}},
                {"type": "assistant", "message": {"content": [{"type": "text", "text": "done"}]}},
            ])
            self.assertFalse(subagent_in_flight(p))

    def test_non_task_agent_tool_use_returns_false(self):
        """Bash/Edit/Read tool_use without tool_result is NOT in-flight (name filter)."""
        with tempfile.TemporaryDirectory() as tmp:
            p = self._write(tmp, [
                {"type": "user", "message": {"content": [{"type": "text", "text": "/gdd-dev"}]}},
                {"type": "assistant", "message": {"content": [
                    {"type": "tool_use", "id": "bash_id_001", "name": "Bash", "input": {"command": "ls"}},
                ]}},
            ])
            self.assertFalse(subagent_in_flight(p))

    def test_exception_returns_false_fail_open(self):
        self.assertFalse(subagent_in_flight(Path("/nonexistent/transcript.jsonl")))

    def test_empty_transcript_returns_false(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "t.jsonl"
            p.write_text("", encoding="utf-8")
            self.assertFalse(subagent_in_flight(p))

    def _launch_ack_tool_result(self, tool_use_id: str, agent_id: str) -> dict:
        text = (
            "Async agent launched successfully.\n"
            f"agentId: {agent_id} (internal ID - do not mention to user. "
            "Use SendMessage with this ID to continue the conversation.)\n"
            "The agent is working in the background. You will be notified "
            "automatically when it completes."
        )
        return {
            "type": "user",
            "message": {"content": [
                {"type": "tool_result", "tool_use_id": tool_use_id, "content": text},
            ]},
        }

    def _task_notification_user_turn(self, task_id: str, tool_use_id: str | None) -> dict:
        tool_use_line = f"\n<tool-use-id>{tool_use_id}</tool-use-id>" if tool_use_id else ""
        text = (
            "<task-notification>\n"
            f"<task-id>{task_id}</task-id>{tool_use_line}\n"
            f"<output-file>/private/tmp/foo/{task_id}.output</output-file>\n"
            "<status>completed</status>\n"
            "</task-notification>"
        )
        return {"type": "user", "message": {"content": [{"type": "text", "text": text}]}}

    def test_background_launch_ack_only_no_notification_is_in_flight(self):
        """(a) 起動応答のみ・完了通知未着 → in-flight=true。"""
        with tempfile.TemporaryDirectory() as tmp:
            p = self._write(tmp, [
                {"type": "assistant", "message": {"content": [
                    {"type": "tool_use", "id": "toolu_dispatch_a", "name": "Task", "input": {}},
                ]}},
                self._launch_ack_tool_result("toolu_dispatch_a", "agent_ack_a"),
                {"type": "assistant", "message": {"content": [{"type": "text", "text": "waiting..."}]}},
            ])
            self.assertTrue(subagent_in_flight(p))

    def test_background_launch_ack_with_matching_tool_use_id_notification_resolves(self):
        """(b) 起動応答 + tool-use-id 直接一致の完了通知 → in-flight=false（高速経路A）。"""
        with tempfile.TemporaryDirectory() as tmp:
            p = self._write(tmp, [
                {"type": "assistant", "message": {"content": [
                    {"type": "tool_use", "id": "toolu_dispatch_b", "name": "Task", "input": {}},
                ]}},
                self._launch_ack_tool_result("toolu_dispatch_b", "agent_ack_b"),
                self._task_notification_user_turn("agent_ack_b", "toolu_dispatch_b"),
            ])
            self.assertFalse(subagent_in_flight(p))

    def test_concurrent_dispatch_only_completed_one_resolves(self):
        """(c) 同時 dispatch 2 件で片方のみ完了通知 → 完了した方のみ in-flight 解消。"""
        with tempfile.TemporaryDirectory() as tmp:
            p = self._write(tmp, [
                {"type": "assistant", "message": {"content": [
                    {"type": "tool_use", "id": "toolu_dispatch_c1", "name": "Task", "input": {}},
                    {"type": "tool_use", "id": "toolu_dispatch_c2", "name": "Task", "input": {}},
                ]}},
                self._launch_ack_tool_result("toolu_dispatch_c1", "agent_ack_c1"),
                self._launch_ack_tool_result("toolu_dispatch_c2", "agent_ack_c2"),
                self._task_notification_user_turn("agent_ack_c1", "toolu_dispatch_c1"),
            ])
            self.assertTrue(subagent_in_flight(p))

    def test_task_notification_during_normal_continuation_does_not_break_judgement(self):
        """(d) 通常継続中のターンへの task-notification 混入 → 既存の継続判定を壊さない
        （同期 dispatch の残差判定は notification と無関係に従来通り機能する）。"""
        with tempfile.TemporaryDirectory() as tmp:
            p = self._write(tmp, [
                {"type": "assistant", "message": {"content": [
                    {"type": "tool_use", "id": "toolu_sync", "name": "Task", "input": {}},
                ]}},
                {"type": "user", "message": {"content": [
                    {"type": "tool_result", "tool_use_id": "toolu_sync", "content": "done"},
                ]}},
                self._task_notification_user_turn("unrelated_agent_id", "toolu_unrelated"),
                {"type": "assistant", "message": {"content": [{"type": "text", "text": "continuing"}]}},
            ])
            self.assertFalse(subagent_in_flight(p))

    def test_background_launch_ack_missing_tool_use_id_falls_back_to_agent_id(self):
        """(e) 起動応答 + tool-use-id 欠落だが agentId/task-id 一致の完了通知 → in-flight=false（フォールバックB）。"""
        with tempfile.TemporaryDirectory() as tmp:
            p = self._write(tmp, [
                {"type": "assistant", "message": {"content": [
                    {"type": "tool_use", "id": "toolu_dispatch_e", "name": "Task", "input": {}},
                ]}},
                self._launch_ack_tool_result("toolu_dispatch_e", "agent_ack_e"),
                self._task_notification_user_turn("agent_ack_e", None),
            ])
            self.assertFalse(subagent_in_flight(p))

    def _task_notification_user_turn_with_status(
        self, task_id: str, tool_use_id: str | None, status: str
    ) -> dict:
        tool_use_line = f"\n<tool-use-id>{tool_use_id}</tool-use-id>" if tool_use_id else ""
        text = (
            "<task-notification>\n"
            f"<task-id>{task_id}</task-id>{tool_use_line}\n"
            f"<output-file>/private/tmp/foo/{task_id}.output</output-file>\n"
            f"<status>{status}</status>\n"
            "</task-notification>"
        )
        return {"type": "user", "message": {"content": [{"type": "text", "text": text}]}}

    def test_non_terminal_status_notification_does_not_resolve_in_flight(self):
        """(M2) 終わっていない status（in_progress など）の task-notification は in-flight を解除しない。"""
        with tempfile.TemporaryDirectory() as tmp:
            p = self._write(tmp, [
                {"type": "assistant", "message": {"content": [
                    {"type": "tool_use", "id": "toolu_dispatch_f", "name": "Task", "input": {}},
                ]}},
                self._launch_ack_tool_result("toolu_dispatch_f", "agent_ack_f"),
                self._task_notification_user_turn_with_status(
                    "agent_ack_f", "toolu_dispatch_f", "in_progress"
                ),
            ])
            self.assertTrue(subagent_in_flight(p))

    def _background_dispatch(self, n: str) -> list[dict]:
        return [
            {"type": "assistant", "message": {"content": [
                {"type": "tool_use", "id": f"toolu_dispatch_{n}", "name": "Agent", "input": {}},
            ]}},
            self._launch_ack_tool_result(f"toolu_dispatch_{n}", f"agent_ack_{n}"),
        ]

    def test_terminal_non_completed_status_resolves_in_flight(self):
        """failed / killed / stopped で終わった background agent は in-flight にしない。
        completed だけを終わりとすると、reviewer が failed で返った後も待ちが続く
        （実測 2026-09-26〜10-03: failed・killed・stopped のどれも実データにあった）。"""
        for status in ("failed", "killed", "stopped"):
            with self.subTest(status=status), tempfile.TemporaryDirectory() as tmp:
                p = self._write(tmp, self._background_dispatch("t") + [
                    self._task_notification_user_turn_with_status(
                        "agent_ack_t", "toolu_dispatch_t", status
                    ),
                ])
                self.assertFalse(subagent_in_flight(p))

    def test_monitor_event_notification_without_status_does_not_resolve(self):
        """Monitor のイベント通知（<status> が無い）は終わりの通知ではない。"""
        with tempfile.TemporaryDirectory() as tmp:
            event = (
                "<task-notification>\n<task-id>agent_ack_m</task-id>\n"
                "<summary>Monitor event: \"x\"</summary>\n<event>DONE</event>\n"
                "</task-notification>"
            )
            p = self._write(tmp, self._background_dispatch("m") + [
                {"type": "user", "message": {"content": [{"type": "text", "text": event}]}},
            ])
            self.assertTrue(subagent_in_flight(p))

    def test_orphan_summary_notification_resolves_every_task_id(self):
        """前のセッションの孤児をまとめた通知（<task-id> が複数・<tool-use-id> 無し）は、
        並んだ id を全部終わりにする。"""
        with tempfile.TemporaryDirectory() as tmp:
            summary = (
                "<task-notification>\n<task-id>agent_ack_o1</task-id>\n"
                "<task-id>agent_ack_o2</task-id>\n"
                "<task-id>__orphan_summary__:agent</task-id>\n"
                "<status>stopped</status>\n"
                "<summary>2 background agents didn't finish</summary>\n"
                "</task-notification>"
            )
            p = self._write(tmp, self._background_dispatch("o1") + self._background_dispatch("o2") + [
                {"type": "user", "message": {"content": [{"type": "text", "text": summary}]}},
            ])
            self.assertFalse(subagent_in_flight(p))

    def _task_stop(self, task_id: str, *, is_error: bool = False, content: object = None) -> list[dict]:
        if content is None:
            content = json.dumps({
                "message": f"Successfully stopped task: {task_id} (review)",
                "task_id": task_id, "task_type": "local_agent", "command": "review",
            })
        result: dict = {"type": "tool_result", "tool_use_id": "toolu_stop", "content": content}
        if is_error:
            result["is_error"] = True
        return [
            {"type": "assistant", "message": {"content": [
                {"type": "tool_use", "id": "toolu_stop", "name": "TaskStop", "input": {"task_id": task_id}},
            ]}},
            {"type": "user", "message": {"content": [result]}},
        ]

    def test_task_stop_result_resolves_in_flight(self):
        """TaskStop の成功結果で止めた agent は、killed の通知が届く前でも in-flight にしない。"""
        with tempfile.TemporaryDirectory() as tmp:
            p = self._write(tmp, self._background_dispatch("s") + self._task_stop("agent_ack_s"))
            self.assertFalse(subagent_in_flight(p))

    def test_task_stop_answered_not_running_resolves_in_flight(self):
        """TaskStop が、host が「動いていない」と答えた決まった文面のエラー（id が input と同じ）で返った agent は、
        in-flight にしない（再開の手順〔references/subagent-dispatch.md〕は、前のプロセスの dispatch に
        TaskStop を呼び、"No task found" のエラーで返る）。"""
        cases = {
            "no task found": self._task_stop("agent_ack_e2", is_error=True, content=(
                "<tool_use_error>No task found with ID: agent_ack_e2</tool_use_error>")),
            "no task found with running list": self._task_stop("agent_ack_e2", is_error=True, content=(
                "<tool_use_error>No task found with ID: agent_ack_e2. Running background agents: "
                "agent_other (review)</tool_use_error>")),
            "not running": self._task_stop("agent_ack_e2", is_error=True, content=(
                "<tool_use_error>Task agent_ack_e2 is not running (status: completed)</tool_use_error>")),
            "no wrapper": self._task_stop("agent_ack_e2", is_error=True,
                                          content="No task found with ID: agent_ack_e2"),
            "text block list": self._task_stop("agent_ack_e2", is_error=True, content=[
                {"type": "text", "text": "<tool_use_error>No task found with ID: agent_ack_e2</tool_use_error>"}]),
        }
        for name, stop in cases.items():
            with self.subTest(case=name), tempfile.TemporaryDirectory() as tmp:
                p = self._write(tmp, self._background_dispatch("e2") + stop)
                self.assertFalse(subagent_in_flight(p))

    def test_success_without_the_stopped_id_keeps_in_flight(self):
        """is_error でない TaskStop の結果でも、本文の JSON に止めた id（target）が書かれていなければ
        待ちに残す（拒否が is_error なしで書かれた形・host の形の変化を、外さない側に倒す）。"""
        cases = {
            "success not json": self._task_stop("agent_ack_e4", content="stopped agent_ack_e4"),
            "success deep json": self._task_stop("agent_ack_e4", content="[" * 100000 + "]" * 100000),
            "success empty": self._task_stop("agent_ack_e4", content=""),
            "success json without id": self._task_stop("agent_ack_e4", content=json.dumps({"message": "ok"})),
            "success json other id": self._task_stop("agent_ack_e4", content=json.dumps({"task_id": "other"})),
        }
        for name, stop in cases.items():
            with self.subTest(case=name), tempfile.TemporaryDirectory() as tmp:
                p = self._write(tmp, self._background_dispatch("e4") + stop)
                self.assertTrue(subagent_in_flight(p))

    def test_success_releases_only_an_input_id_named_in_the_json(self):
        """成功で待ちから外すのは、本文の JSON（全部の text block の task_id・shell_id）に、input で止めた id が
        書かれているときだけ。input と違う id の dispatch は外さず、input の無い成功は何も外さない（待つ側に倒す）。"""
        def blocks(*texts):
            return [{"type": "text", "text": t} for t in texts]
        named = json.dumps({"task_id": "agent_ack_f1"})
        kept = {
            "json names another dispatch": self._task_stop_input(
                {"task_id": "agent_ack_zz"}, is_error=False, content=named),
            "no input id": self._task_stop_input({}, is_error=False, content=named),
            "odd blocks": self._task_stop_input(
                {"task_id": "agent_ack_f1"}, is_error=False, content=[None, 3, {"type": "text", "text": 5}]),
        }
        released = {
            "shell_id in json": self._task_stop_input(
                {"task_id": "agent_ack_f1"}, is_error=False, content=json.dumps({"shell_id": "agent_ack_f1"})),
            "json in an earlier block": self._task_stop_input(
                {"task_id": "agent_ack_f1"}, is_error=False, content=blocks(named, "stopped")),
            "json after a non-json block": self._task_stop_input(
                {"task_id": "agent_ack_f1"}, is_error=False, content=blocks("stopped", named)),
            "input shell_id": self._task_stop_input({"shell_id": "agent_ack_f1"}, is_error=False, content=named),
        }
        for name, stop in {**kept, **released}.items():
            with self.subTest(case=name), tempfile.TemporaryDirectory() as tmp:
                p = self._write(tmp, self._background_dispatch("f1") + stop)
                self.assertEqual(subagent_in_flight(p), name in kept)

    def _task_stop_input(self, inp: dict, *, is_error: bool, content: object) -> list[dict]:
        result: dict = {"type": "tool_result", "tool_use_id": "toolu_stop", "content": content}
        if is_error:
            result["is_error"] = True
        return [
            {"type": "assistant", "message": {"content": [
                {"type": "tool_use", "id": "toolu_stop", "name": "TaskStop", "input": inp}]}},
            {"type": "user", "message": {"content": [result]}},
        ]

    def test_task_stop_shell_id_alias_is_read(self):
        """TaskStop の input の shell_id（host の schema の古い名前）も、task_id と同じく止めた相手として読む。
        両方あるときは、どちらかが host の「動いていない」の文面の id と同じなら外す。"""
        not_found = "<tool_use_error>No task found with ID: agent_ack_e5</tool_use_error>"
        cases = {
            "shell_id only": {"shell_id": "agent_ack_e5"},
            "shell_id matches": {"task_id": "other", "shell_id": "agent_ack_e5"},
            "task_id matches": {"task_id": "agent_ack_e5", "shell_id": "other"},
        }
        for name, inp in cases.items():
            with self.subTest(case=name), tempfile.TemporaryDirectory() as tmp:
                stop = self._task_stop_input(inp, is_error=True, content=not_found)
                p = self._write(tmp, self._background_dispatch("e5") + stop)
                self.assertFalse(subagent_in_flight(p))
        with tempfile.TemporaryDirectory() as tmp:
            stop = self._task_stop_input({"task_id": "x", "shell_id": "y"}, is_error=True, content=not_found)
            p = self._write(tmp, self._background_dispatch("e5") + stop)
            self.assertTrue(subagent_in_flight(p))

    def test_unaccepted_task_stop_results_are_collected(self):
        """target があって待ちから外さなかった TaskStop の結果（未知のエラー・止めた id の無い成功）だけを集める。
        外した結果・結果なし・target の無い入力は集めない。"""
        collected = {
            "unknown error": self._task_stop("agent_ack_e6", is_error=True, content="<tool_use_error>Failed</tool_use_error>"),
            "denied": self._task_stop("agent_ack_e6", is_error=True, content="Permission denied"),
            "success not json": self._task_stop("agent_ack_e6", content="stopped"),
            "success other id": self._task_stop("agent_ack_e6", content=json.dumps({"task_id": "other"})),
        }
        not_collected = {
            "success": self._task_stop("agent_ack_e6"),
            "not running": self._task_stop("agent_ack_e6", is_error=True,
                                           content="Task agent_ack_e6 is not running (status: completed)"),
            "no result": self._task_stop("agent_ack_e6")[:1],
            "no target": self._task_stop_input({}, is_error=True, content="Missing required parameter: task_id"),
        }
        for name, stop in {**collected, **not_collected}.items():
            with self.subTest(case=name), tempfile.TemporaryDirectory() as tmp:
                tv = parse_transcript(self._write(tmp, self._background_dispatch("e6") + stop))
                ids = [tid for tid, _ in tv.unaccepted_task_stops]
                self.assertEqual(ids, ["toolu_stop"] if name in collected else [], name)

    def test_task_stop_without_a_not_running_answer_keeps_in_flight(self):
        """TaskStop がほかのエラー（拒否・未知の文面・空・別の id の文面）で返ったか、結果がまだ無いときは、
        agent はまだ動いているかもしれないので in-flight のまま（判定できないときは待つ側に倒す）。"""
        denied = ("Permission for this action was denied by the Claude Code auto mode classifier.")
        cases = {
            "denied": self._task_stop("agent_ack_k", is_error=True, content=denied),
            "unknown text": self._task_stop("agent_ack_k", is_error=True,
                                            content="<tool_use_error>Failed to stop task</tool_use_error>"),
            "empty": self._task_stop("agent_ack_k", is_error=True, content=""),
            "id prefix": self._task_stop("agent_ack_k", is_error=True,
                                         content="<tool_use_error>No task found with ID: agent_ack_kx</tool_use_error>"),
            "other id not running": self._task_stop("agent_ack_k", is_error=True,
                                                    content="<tool_use_error>Task other is not running</tool_use_error>"),
            "running suffix": self._task_stop("agent_ack_k", is_error=True,
                                              content="<tool_use_error>Task agent_ack_k is not runnings</tool_use_error>"),
            "no id": self._task_stop("agent_ack_k", is_error=True,
                                     content="<tool_use_error>No task found</tool_use_error>"),
            "json body": self._task_stop("agent_ack_k", is_error=True),
            "no result": self._task_stop("agent_ack_k")[:1],
            "odd content": self._task_stop("agent_ack_k", is_error=True, content=[None, 3, {"type": "text", "text": 5}]),
        }
        for name, stop in cases.items():
            with self.subTest(case=name), tempfile.TemporaryDirectory() as tmp:
                p = self._write(tmp, self._background_dispatch("k") + stop)
                self.assertTrue(subagent_in_flight(p))

    def test_not_running_answer_after_an_unknown_error_resolves_in_flight(self):
        """未知のエラーの後に、同じ agent への TaskStop が "No task found" で返ったら in-flight にしない。"""
        first = self._task_stop("agent_ack_m", is_error=True, content="<tool_use_error>Failed</tool_use_error>")
        second = json.loads(json.dumps(self._task_stop(
            "agent_ack_m", is_error=True, content="<tool_use_error>No task found with ID: agent_ack_m</tool_use_error>")))
        second[0]["message"]["content"][0]["id"] = "toolu_stop_2"
        second[1]["message"]["content"][0]["tool_use_id"] = "toolu_stop_2"
        with tempfile.TemporaryDirectory() as tmp:
            p = self._write(tmp, self._background_dispatch("m") + first)
            self.assertTrue(subagent_in_flight(p))
            p = self._write(tmp, self._background_dispatch("m") + first + second)
            self.assertFalse(subagent_in_flight(p))

    def test_task_stop_of_other_id_does_not_resolve_in_flight(self):
        """別の id を止めた TaskStop では、in-flight のまま（block すべき入力が allow にならない）。"""
        with tempfile.TemporaryDirectory() as tmp:
            p = self._write(tmp, self._background_dispatch("e3") + self._task_stop("other_task"))
            self.assertTrue(subagent_in_flight(p))

    def test_unreadable_task_stop_input_keeps_in_flight(self):
        """TaskStop の input が無い・dict でない・task_id が空や list のときは、例外にならず
        in-flight のまま（判定できないときは止まらせる側に倒す）。"""
        inputs = {"no input": None, "not dict": "agent_ack_u", "empty id": {"task_id": ""},
                  "list id": {"task_id": ["agent_ack_u"]}}
        for name, inp in inputs.items():
            block: dict = {"type": "tool_use", "id": "toolu_stop", "name": "TaskStop"}
            if inp is not None:
                block["input"] = inp
            stop = [
                {"type": "assistant", "message": {"content": [block]}},
                {"type": "user", "message": {"content": [
                    {"type": "tool_result", "tool_use_id": "toolu_stop", "is_error": True,
                     "content": "<tool_use_error>No task found</tool_use_error>"}]}},
            ]
            with self.subTest(case=name), tempfile.TemporaryDirectory() as tmp:
                p = self._write(tmp, self._background_dispatch("u") + stop)
                parse_transcript(p)
                self.assertTrue(subagent_in_flight(p))

    def test_sync_dispatch_without_agent_id_stays_in_flight_after_task_stop(self):
        """agentId の無い（起動応答の無い）dispatch は、TaskStop の対象に何があっても残る。"""
        with tempfile.TemporaryDirectory() as tmp:
            dispatch = [{"type": "assistant", "message": {"content": [
                {"type": "tool_use", "id": "toolu_sync", "name": "Agent", "input": {}}]}}]
            p = self._write(tmp, dispatch + self._task_stop("toolu_sync", is_error=True))
            self.assertTrue(subagent_in_flight(p))

    def test_malformed_task_stop_ids_do_not_raise(self):
        """TaskStop の id や tool_result の tool_use_id が文字列でないときも、
        parse_transcript が例外で抜けず（Stop hook ごと落ちず）in-flight のまま。"""
        bad_result_id = [
            {"type": "assistant", "message": {"content": [
                {"type": "tool_use", "id": "toolu_stop", "name": "TaskStop", "input": {}},
            ]}},
            {"type": "user", "message": {"content": [
                {"type": "tool_result", "tool_use_id": [], "content": "{}"},
            ]}},
        ]
        bad_tool_use_id = [
            {"type": "assistant", "message": {"content": [
                {"type": "tool_use", "id": ["x"], "name": "TaskStop", "input": {}},
            ]}},
        ]
        for name, items in {"result id": bad_result_id, "tool_use id": bad_tool_use_id}.items():
            with self.subTest(case=name), tempfile.TemporaryDirectory() as tmp:
                p = self._write(tmp, self._background_dispatch("x") + items)
                parse_transcript(p)
                self.assertTrue(subagent_in_flight(p))

    def test_malformed_line_is_skipped_and_later_lines_are_read(self):
        """文字列でない id・name・tool_use_id の block はその block だけを、桁の多い整数の行は
        その行だけを読み飛ばし、後ろの行は読む。どのフィールドでも parse_transcript ごと落ちない。"""
        bad_lines = {
            "result id list": {"type": "user", "message": {"content": [
                {"type": "tool_result", "tool_use_id": ["x"], "content": "{}"}]}},
            "result id dict": {"type": "user", "message": {"content": [
                {"type": "tool_result", "tool_use_id": {"a": 1}, "content": "{}"}]}},
            "tool_use id": {"type": "assistant", "message": {"content": [
                {"type": "tool_use", "id": ["x"], "name": "Agent", "input": {}}]}},
            "tool_use name": {"type": "assistant", "message": {"content": [
                {"type": "tool_use", "id": "x", "name": ["Agent"], "input": {}}]}},
        }
        later = {"type": "assistant", "message": {"content": [{"type": "text", "text": "later line"}]}}
        for name, bad in bad_lines.items():
            with self.subTest(case=name), tempfile.TemporaryDirectory() as tmp:
                p = self._write(tmp, self._background_dispatch("z") + [bad, later])
                self.assertEqual(parse_transcript(p).last_assistant_text, "later line")
                self.assertTrue(subagent_in_flight(p))
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "transcript.jsonl"
            huge_int = '{"type": "assistant", "n": ' + "1" * 5000 + "}"
            with self.assertRaises(ValueError):  # 前提: int の桁数の上限（sys.get_int_max_str_digits）で読めない
                json.loads(huge_int)
            p.write_text(huge_int + "\n" + json.dumps(later) + "\n", encoding="utf-8")
            self.assertEqual(parse_transcript(p).last_assistant_text, "later line")

    def test_task_id_quoted_in_result_body_does_not_resolve(self):
        """終わりの通知の <result> に引用された別の task の id は、終わりにしない。"""
        with tempfile.TemporaryDirectory() as tmp:
            other_done = (
                "<task-notification>\n<task-id>agent_ack_done</task-id>\n"
                "<status>completed</status>\n<summary>Agent finished</summary>\n"
                "<result>see <task-id>agent_ack_q</task-id> "
                "<tool-use-id>toolu_dispatch_q</tool-use-id></result>\n"
                "</task-notification>"
            )
            p = self._write(tmp, self._background_dispatch("q") + [
                {"type": "user", "message": {"content": [{"type": "text", "text": other_done}]}},
            ])
            self.assertTrue(subagent_in_flight(p))

    def test_unknown_status_value_resolves_in_flight(self):
        """<status> を持つ通知は、終わっていない status（in_progress など）でなければ終わりとする。
        許可リストにすると、host が新しい終わりの status を出したときに同じ取りこぼしが起きる。"""
        with tempfile.TemporaryDirectory() as tmp:
            p = self._write(tmp, self._background_dispatch("u") + [
                self._task_notification_user_turn_with_status("agent_ack_u", "toolu_dispatch_u", "cancelled"),
            ])
            self.assertFalse(subagent_in_flight(p))

    def test_unclosed_non_terminal_block_does_not_borrow_next_status(self):
        """閉じていない終わっていないブロックも、次の開始タグで区切り、後ろの status を拾わない。"""
        with tempfile.TemporaryDirectory() as tmp:
            text = (
                "<task-notification>\n<task-id>agent_ack_v</task-id>\n<status>in_progress</status>\n"
                "<task-notification>\n<task-id>other</task-id>\n<status>completed</status>\n"
                "</task-notification>"
            )
            p = self._write(tmp, self._background_dispatch("v") + [
                {"type": "user", "message": {"content": [{"type": "text", "text": text}]}},
            ])
            self.assertTrue(subagent_in_flight(p))
            self.assertEqual(parse_transcript(p).task_notifications, [("other", None)])

    def test_adjacent_non_completed_notification_does_not_cross_match_next_block(self):
        """(HIGH-1 regression) <output-file> 等の中間タグを許容する非貪欲マッチが、
        1件目の終わっていないブロックを飛び越して2件目の completed ブロックの
        <status> に誤って一致しないこと（</task-notification> 境界超え禁止）。"""
        with tempfile.TemporaryDirectory() as tmp:
            notification_a_in_progress = (
                "<task-notification>\n"
                "<task-id>agent_ack_h1</task-id>\n"
                "<tool-use-id>toolu_dispatch_h1</tool-use-id>\n"
                "<output-file>/private/tmp/foo/agent_ack_h1.output</output-file>\n"
                "<status>in_progress</status>\n"
                "</task-notification>"
            )
            notification_b_completed = (
                "<task-notification>\n"
                "<task-id>agent_ack_h2</task-id>\n"
                "<tool-use-id>toolu_dispatch_h2</tool-use-id>\n"
                "<output-file>/private/tmp/foo/agent_ack_h2.output</output-file>\n"
                "<status>completed</status>\n"
                "</task-notification>"
            )
            p = self._write(tmp, [
                {"type": "assistant", "message": {"content": [
                    {"type": "tool_use", "id": "toolu_dispatch_h1", "name": "Task", "input": {}},
                    {"type": "tool_use", "id": "toolu_dispatch_h2", "name": "Task", "input": {}},
                ]}},
                self._launch_ack_tool_result("toolu_dispatch_h1", "agent_ack_h1"),
                self._launch_ack_tool_result("toolu_dispatch_h2", "agent_ack_h2"),
                {"type": "user", "message": {"content": [
                    {"type": "text", "text": notification_a_in_progress + "\n" + notification_b_completed},
                ]}},
            ])
            self.assertTrue(subagent_in_flight(p))
            self.assertEqual(
                parse_transcript(p).task_notifications, [("agent_ack_h2", "toolu_dispatch_h2")]
            )

    def test_sync_tool_result_containing_agent_id_substring_is_not_launch_ack(self):
        """(M3) 同期 subagent のレポート文中に偶然 "agentId:" を含んでも、
        "Async agent launched successfully." の前置きが無ければ起動応答として
        誤分類せず、通常の tool_result 残差判定に委ねる（AC-E9-4 非退行）。"""
        with tempfile.TemporaryDirectory() as tmp:
            report_text = (
                "Investigated the config loader. It reads the runtime "
                "agentId: legacy-config-key from the settings file and "
                "falls back to defaults if absent. Task complete."
            )
            p = self._write(tmp, [
                {"type": "assistant", "message": {"content": [
                    {"type": "tool_use", "id": "toolu_dispatch_g", "name": "Task", "input": {}},
                ]}},
                {"type": "user", "message": {"content": [
                    {"type": "tool_result", "tool_use_id": "toolu_dispatch_g", "content": report_text},
                ]}},
                {"type": "assistant", "message": {"content": [{"type": "text", "text": "done"}]}},
            ])
            self.assertFalse(subagent_in_flight(p))


class TestParseTranscriptBlockIsolation(unittest.TestCase):
    """1 つの block で例外が出ても、同じ record のほかの block は読む。"""

    _BAD_RESULT = {"type": "tool_result", "tool_use_id": ["x"], "content": "{}"}

    def _write(self, tmp: str, items: list[dict]) -> Path:
        p = Path(tmp) / "transcript.jsonl"
        p.write_text("\n".join(json.dumps(i) for i in items) + "\n", encoding="utf-8")
        return p

    def test_user_text_survives_malformed_sibling_block(self):
        """text block と、文字列でない tool_use_id の block が同じ record にあっても、text を
        last_user_text にする。行ごと捨てると、古い継続意図が last_user_text に残る。"""
        text = {"type": "text", "text": "次は async/await の使い方を教えて"}
        for name, content in {"text first": [text, self._BAD_RESULT],
                              "malformed first": [self._BAD_RESULT, text]}.items():
            with self.subTest(order=name), tempfile.TemporaryDirectory() as tmp:
                p = self._write(tmp, [
                    {"type": "user", "message": {"content": [{"type": "text", "text": "/gdd-dev continue"}]}},
                    {"type": "user", "message": {"content": content}},
                ])
                self.assertEqual(parse_transcript(p).last_user_text, "次は async/await の使い方を教えて")

    def test_blank_human_record_replaces_stale_continuation(self):
        """空白だけの str content・bare str の人間の record も last_user_text にする（継続意図なし）。
        捨てると、その前の `/gdd-dev continue` が last_user_text に残る。"""
        for name, content in {"str content": "   ", "bare str": ["   "]}.items():
            with self.subTest(form=name), tempfile.TemporaryDirectory() as tmp:
                p = self._write(tmp, [
                    {"type": "user", "message": {"content": [{"type": "text", "text": "/gdd-dev continue"}]}},
                    {"type": "user", "message": {"content": content}},
                ])
                self.assertEqual(parse_transcript(p).last_user_text, "   ")

    def test_launch_ack_next_to_malformed_block_is_recorded(self):
        """壊れた block の前後の起動応答も読む（dispatch が in-flight と判定できる）。"""
        ack = {"type": "tool_result", "tool_use_id": "toolu_d",
               "content": "Async agent launched successfully.\nagentId: agent_d (internal ID)"}
        for name, content in {"ack first": [ack, self._BAD_RESULT],
                              "malformed first": [self._BAD_RESULT, ack]}.items():
            with self.subTest(order=name), tempfile.TemporaryDirectory() as tmp:
                p = self._write(tmp, [
                    {"type": "assistant", "message": {"content": [
                        {"type": "tool_use", "id": "toolu_d", "name": "Agent", "input": {}}]}},
                    {"type": "user", "message": {"content": content}},
                ])
                self.assertEqual(parse_transcript(p).dispatch_agent_ids, {"toolu_d": "agent_d"})

    def test_assistant_blocks_survive_malformed_sibling_block(self):
        """assistant の record でも、壊れた tool_use の前後の text・dispatch を読む。"""
        with tempfile.TemporaryDirectory() as tmp:
            p = self._write(tmp, [
                {"type": "assistant", "message": {"content": [
                    {"type": "tool_use", "id": "toolu_ok", "name": "Agent", "input": {}},
                    {"type": "tool_use", "id": "x", "name": ["Agent"], "input": {}},
                    {"type": "text", "text": "after malformed"},
                    {"type": "tool_use", "id": "toolu_after", "name": "Agent", "input": {}},
                ]}},
            ])
            tv = parse_transcript(p)
            self.assertEqual(tv.last_assistant_text, "after malformed")
            self.assertEqual(tv.all_task_agent_ids, {"toolu_ok", "toolu_after"})

    def test_notification_in_non_last_text_block_is_read(self):
        """終わりの通知は、record の最後の text block でなくても読む。"""
        notification = (
            "<task-notification>\n<task-id>agent_n</task-id>\n"
            "<status>completed</status>\n</task-notification>"
        )
        with tempfile.TemporaryDirectory() as tmp:
            p = self._write(tmp, [
                {"type": "user", "message": {"content": [
                    {"type": "text", "text": notification},
                    {"type": "text", "text": "trailing text"},
                ]}},
            ])
            self.assertEqual(parse_transcript(p).task_notifications, [("agent_n", None)])

    def test_skipped_blocks_and_lines_are_logged(self):
        """読み飛ばした block・行は、project_root を渡すと hook-errors に 1 件だけ記録する。"""
        huge_int = '{"type": "assistant", "n": ' + "1" * 5000 + "}"
        with self.assertRaises(ValueError):  # 前提: int の桁数の上限（sys.get_int_max_str_digits）で読めない
            json.loads(huge_int)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            p = root / "transcript.jsonl"
            p.write_text(
                json.dumps({"type": "user", "message": {"content": [self._BAD_RESULT]}})
                + "\n" + huge_int + "\n", encoding="utf-8",
            )
            parse_transcript(p, root)
            log = (root / ".gdd" / "hook-errors.log").read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(log), 1, log)
            entry = json.loads(log[0])
            self.assertEqual(entry["source"], "parse_transcript")
            self.assertTrue(entry["message"].startswith("2 個の block・行を読み飛ばした"), entry)

    def test_nothing_logged_for_clean_transcript(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            p = self._write(tmp, [{"type": "assistant", "message": {"content": [{"type": "text", "text": "ok"}]}}])
            parse_transcript(p, root)
            self.assertFalse((root / ".gdd" / "hook-errors.log").exists())

    def test_deeply_nested_line_is_skipped(self):
        """再帰の上限を超える入れ子の行は、その行だけを読み飛ばす。"""
        deep = '{"type": "assistant", "n": ' + "[" * 1000000 + "]" * 1000000 + "}"
        with self.assertRaises(RecursionError):  # 前提: json.loads が RecursionError を出す
            json.loads(deep)
        later = {"type": "assistant", "message": {"content": [{"type": "text", "text": "later line"}]}}
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "transcript.jsonl"
            p.write_text(deep + "\n" + json.dumps(later) + "\n", encoding="utf-8")
            self.assertEqual(parse_transcript(p).last_assistant_text, "later line")


# ---------------------------------------------------------------------------
# OT-F1: E2E hook integration tests for in-flight suppression
# ---------------------------------------------------------------------------


def _make_inflight_transcript(path: Path, user_text: str = "/gdd-dev") -> None:
    """Transcript where last assistant turn has an unanswered tool_use."""
    lines = [
        json.dumps({"type": "user", "message": {"content": [{"type": "text", "text": user_text}]}}),
        json.dumps({"type": "assistant", "message": {"content": [
            {"type": "text", "text": "dispatching brainstorming subagent..."},
            {"type": "tool_use", "id": "inflight_id_001", "name": "Task", "input": {"prompt": "..."}},
        ]}}),
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _make_completed_subagent_transcript(path: Path, user_text: str = "/gdd-dev") -> None:
    """Transcript where tool_use has a matching tool_result."""
    lines = [
        json.dumps({"type": "user", "message": {"content": [{"type": "text", "text": user_text}]}}),
        json.dumps({"type": "assistant", "message": {"content": [
            {"type": "tool_use", "id": "done_id_001", "name": "Task", "input": {}},
        ]}}),
        json.dumps({"type": "user", "message": {"content": [
            {"type": "tool_result", "tool_use_id": "done_id_001", "content": "subagent result"},
        ]}}),
        json.dumps({"type": "assistant", "message": {"content": [
            {"type": "text", "text": "subagent returned. continuing /gdd-dev brainstorming."},
        ]}}),
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


class TestHookInflightSubagent(unittest.TestCase):
    """E2E: Stop hook suppresses continuation nudge while subagent is in-flight."""

    def _active_state(self, session_id: str = "test-session") -> dict[str, str]:
        return {
            "active": "true",
            "session_id": session_id,
            "iteration": "1",
            "workflow_runtime": "claude_code",
        }

    def test_inflight_tool_use_suppresses_nudge(self):
        """In-flight tool_use → hook exits silently (stdout empty, exit 0)."""
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            _write_state_file(workspace, self._active_state())
            transcript = workspace / "transcript.jsonl"
            _make_inflight_transcript(transcript)
            code, out, err = _run_hook(workspace, transcript_path=transcript)
            self.assertEqual(code, 0)
            self.assertEqual(out, "", f"Expected silent exit but got stdout: {out!r}")

    def test_completed_tool_use_does_not_suppress_nudge(self):
        """Completed tool_use (tool_result present) → hook outputs Continue nudge."""
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            _write_state_file(workspace, self._active_state())
            transcript = workspace / "transcript.jsonl"
            _make_completed_subagent_transcript(transcript)
            code, out, err = _run_hook(workspace, transcript_path=transcript)
            self.assertEqual(code, 0)
            self.assertIn("decision", out, f"Expected nudge but got stdout: {out!r}")

    def test_failed_background_agent_does_not_suppress_nudge(self):
        """入口から: failed で返った background agent が残っても、継続の nudge を出す。
        以前は in-flight のままになり、セッションが終わるまで継続が抑止されていた。"""
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            _write_state_file(workspace, self._active_state())
            transcript = workspace / "transcript.jsonl"
            notification = (
                "<task-notification>\n<task-id>agent_bg_1</task-id>\n"
                "<tool-use-id>toolu_bg_1</tool-use-id>\n<status>failed</status>\n"
                "<summary>Agent \"review\" failed: Agent stalled</summary>\n"
                "</task-notification>"
            )
            lines = [
                {"type": "user", "message": {"content": [{"type": "text", "text": "/gdd-dev"}]}},
                {"type": "assistant", "message": {"content": [
                    {"type": "tool_use", "id": "toolu_bg_1", "name": "Agent",
                     "input": {"run_in_background": True}},
                ]}},
                {"type": "user", "message": {"content": [
                    {"type": "tool_result", "tool_use_id": "toolu_bg_1",
                     "content": "Async agent launched successfully.\nagentId: agent_bg_1 (internal ID)"},
                ]}},
                {"type": "user", "message": {"content": [{"type": "text", "text": notification}]}},
                {"type": "assistant", "message": {"content": [
                    {"type": "text", "text": "reviewer failed. continuing /gdd-dev requirements-gating."},
                ]}},
            ]
            transcript.write_text("\n".join(json.dumps(x) for x in lines) + "\n", encoding="utf-8")
            code, out, err = _run_hook(workspace, transcript_path=transcript)
            self.assertEqual(code, 0)
            self.assertEqual(json.loads(out).get("decision"), "block", out)
            self.assertTrue(json.loads(out)["reason"].startswith("Continue the active `/gdd-dev` run"), out)

    def test_task_stopped_background_agent_does_not_suppress_nudge(self):
        """入口から: 再開の手順で TaskStop を呼び、"No task found" で返った前のプロセスの
        background agent だけが残っても、継続の nudge を出す（以前は in-flight のまま抑止された）。"""
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            _write_state_file(workspace, self._active_state())
            transcript = workspace / "transcript.jsonl"
            lines = [
                {"type": "user", "message": {"content": [{"type": "text", "text": "/gdd-dev"}]}},
                {"type": "assistant", "message": {"content": [
                    {"type": "tool_use", "id": "toolu_bg_2", "name": "Agent",
                     "input": {"run_in_background": True}},
                ]}},
                {"type": "user", "message": {"content": [
                    {"type": "tool_result", "tool_use_id": "toolu_bg_2",
                     "content": "Async agent launched successfully.\nagentId: agent_bg_2 (internal ID)"},
                ]}},
                {"type": "assistant", "message": {"content": [
                    {"type": "tool_use", "id": "toolu_stop_2", "name": "TaskStop",
                     "input": {"task_id": "agent_bg_2"}},
                ]}},
                {"type": "user", "message": {"content": [
                    {"type": "tool_result", "tool_use_id": "toolu_stop_2", "is_error": True,
                     "content": "<tool_use_error>No task found with ID: agent_bg_2</tool_use_error>"},
                ]}},
                {"type": "assistant", "message": {"content": [
                    {"type": "text", "text": "re-dispatching. continuing /gdd-dev requirements-gating."},
                ]}},
            ]
            transcript.write_text("\n".join(json.dumps(x) for x in lines) + "\n", encoding="utf-8")
            code, out, err = _run_hook(workspace, transcript_path=transcript)
            self.assertEqual(code, 0)
            self.assertEqual(json.loads(out).get("decision"), "block", out)
            self.assertTrue(json.loads(out)["reason"].startswith("Continue the active `/gdd-dev` run"), out)

    def test_denied_task_stop_keeps_the_background_agent_waiting(self):
        """入口から: TaskStop が拒否（未知のエラー）で返った background agent は、まだ動いているかもしれないので、
        継続の nudge を出さずに完了通知を待つ。"""
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            _write_state_file(workspace, self._active_state())
            transcript = workspace / "transcript.jsonl"
            lines = [
                {"type": "user", "message": {"content": [{"type": "text", "text": "/gdd-dev"}]}},
                {"type": "assistant", "message": {"content": [
                    {"type": "tool_use", "id": "toolu_bg_3", "name": "Agent",
                     "input": {"run_in_background": True}},
                ]}},
                {"type": "user", "message": {"content": [
                    {"type": "tool_result", "tool_use_id": "toolu_bg_3",
                     "content": "Async agent launched successfully.\nagentId: agent_bg_3 (internal ID)"},
                ]}},
                {"type": "assistant", "message": {"content": [
                    {"type": "tool_use", "id": "toolu_stop_3", "name": "TaskStop",
                     "input": {"task_id": "agent_bg_3"}},
                ]}},
                {"type": "user", "message": {"content": [
                    {"type": "tool_result", "tool_use_id": "toolu_stop_3", "is_error": True,
                     "content": "Permission for this action was denied by the Claude Code auto mode classifier."},
                ]}},
                {"type": "assistant", "message": {"content": [
                    {"type": "text", "text": "continuing /gdd-dev. reviewer の完了通知を待ちます。"},
                ]}},
            ]
            transcript.write_text("\n".join(json.dumps(x) for x in lines) + "\n", encoding="utf-8")
            code, out, err = _run_hook(workspace, transcript_path=transcript)
            self.assertEqual(code, 0, err)
            self.assertEqual(out, "")

    def _denied_stop_transcript(self, workspace: Path) -> Path:
        transcript = workspace / "transcript.jsonl"
        lines = [
            {"type": "user", "message": {"content": [{"type": "text", "text": "/gdd-dev"}]}},
            {"type": "assistant", "message": {"content": [
                {"type": "tool_use", "id": "toolu_bg_5", "name": "Agent", "input": {"run_in_background": True}}]}},
            {"type": "user", "message": {"content": [
                {"type": "tool_result", "tool_use_id": "toolu_bg_5",
                 "content": "Async agent launched successfully.\nagentId: agent_bg_5 (internal ID)"}]}},
            {"type": "assistant", "message": {"content": [
                {"type": "tool_use", "id": "toolu_stop_5", "name": "TaskStop", "input": {"task_id": "agent_bg_5"}}]}},
            {"type": "user", "message": {"content": [
                {"type": "tool_result", "tool_use_id": "toolu_stop_5", "is_error": True,
                 "content": "Permission for this action was denied by the Claude Code auto mode classifier."}]}},
            {"type": "assistant", "message": {"content": [
                {"type": "text", "text": "continuing /gdd-dev. reviewer の完了通知を待ちます。"}]}},
        ]
        transcript.write_text("\n".join(json.dumps(x) for x in lines) + "\n", encoding="utf-8")
        return transcript

    def test_unaccepted_task_stop_is_recorded_once_in_hook_errors(self):
        """入口から: 待ちから外さなかった TaskStop の結果を .gdd/hook-errors.log に、tool_use_id ごとに 1 回だけ書く。
        Stop が続けて発火しても書き足さない。待ちの判定（押し返さない）は変えない。"""
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            _write_state_file(workspace, self._active_state())
            transcript = self._denied_stop_transcript(workspace)
            for _ in range(2):
                code, out, err = _run_hook(workspace, transcript_path=transcript)
                self.assertEqual(code, 0, err)
                self.assertEqual(out, "")
            log = (workspace / ".gdd" / "hook-errors.log").read_text(encoding="utf-8")
            records = [json.loads(line) for line in log.splitlines() if "toolu_stop_5" in line]
            self.assertEqual(len(records), 1, log)
            self.assertEqual(records[0]["source"], "task_stop_unaccepted")
            self.assertIn("denied", records[0]["message"])

    def test_unaccepted_task_stop_with_lone_surrogate_is_recorded_once(self):
        """入口から: 本文に lone surrogate がある TaskStop の結果も、置き換えて 1 回だけ書く（Stop のたびに書き直さない）。"""
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            _write_state_file(workspace, self._active_state())
            transcript = self._denied_stop_transcript(workspace)
            transcript.write_text(transcript.read_text(encoding="utf-8").replace(
                "denied by", "denied \\ud800 by"), encoding="utf-8")
            for _ in range(2):
                code, out, err = _run_hook(workspace, transcript_path=transcript)
                self.assertEqual(code, 0, err)
            log = (workspace / ".gdd" / "hook-errors.log").read_text(encoding="utf-8")
            records = [json.loads(line) for line in log.splitlines() if "toolu_stop_5" in line]
            self.assertEqual([r["source"] for r in records], ["task_stop_unaccepted"], log)

    @unittest.skipIf(hasattr(os, "geteuid") and os.geteuid() == 0, "root は権限の無いファイルも読めるので、読めない log を作れない")
    def test_unreadable_hook_errors_still_records_unaccepted_task_stop(self):
        """入口から: hook-errors.log が読めない（書くことはできる）ときは、記録の側に倒して書く。"""
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            _write_state_file(workspace, self._active_state())
            log_path = workspace / ".gdd" / "hook-errors.log"
            log_path.parent.mkdir(parents=True, exist_ok=True)
            log_path.write_text("", encoding="utf-8")
            log_path.chmod(0o200)
            try:
                code, out, err = _run_hook(workspace, transcript_path=self._denied_stop_transcript(workspace))
            finally:
                log_path.chmod(0o600)
            self.assertEqual(code, 0, err)
            records = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]
            self.assertIn("task_stop_unaccepted", [r["source"] for r in records], records)

    def test_unwritable_hook_errors_does_not_break_the_stop_hook(self):
        """入口から: hook-errors.log が通常のファイルでない（ディレクトリ）ときも、記録で Stop hook が落ちず、
        待ちの判定は変わらない。"""
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            _write_state_file(workspace, self._active_state())
            (workspace / ".gdd" / "hook-errors.log").mkdir(parents=True)
            transcript = self._denied_stop_transcript(workspace)
            code, out, err = _run_hook(workspace, transcript_path=transcript)
            self.assertEqual(code, 0, err)
            self.assertEqual(out, "")

    def test_denied_task_stop_hands_off_with_state_keeping_stop(self):
        """入口から: TaskStop が拒否で返り、まだ動いているものとして残った background agent があっても、
        loop state を保つ clarification-needed の停止は wait watchdog が押し返さない（手順の出口）。blocked は押し返す。"""
        for reason, blocked in (("clarification-needed", False), ("blocked", True)):
            with self.subTest(reason=reason), tempfile.TemporaryDirectory() as tmp:
                workspace = Path(tmp)
                _write_state_file(workspace, self._active_state())
                transcript = workspace / "transcript.jsonl"
                lines = [
                    {"type": "user", "message": {"content": [{"type": "text", "text": "/gdd-dev"}]}},
                    {"type": "assistant", "message": {"content": [
                        {"type": "tool_use", "id": "toolu_bg_4", "name": "Agent",
                         "input": {"run_in_background": True}},
                    ]}},
                    {"type": "user", "message": {"content": [
                        {"type": "tool_result", "tool_use_id": "toolu_bg_4",
                         "content": "Async agent launched successfully.\nagentId: agent_bg_4 (internal ID)"},
                    ]}},
                    {"type": "assistant", "message": {"content": [
                        {"type": "tool_use", "id": "toolu_stop_4", "name": "TaskStop",
                         "input": {"task_id": "agent_bg_4"}},
                    ]}},
                    {"type": "user", "message": {"content": [
                        {"type": "tool_result", "tool_use_id": "toolu_stop_4", "is_error": True,
                         "content": "Permission for this action was denied by the Claude Code auto mode classifier."},
                    ]}},
                    {"type": "assistant", "message": {"content": [
                        {"type": "text", "text": (
                            f"TaskStop が拒否された。人に渡す。\n<gdd-stop reason=\"{reason}\">\n\n"
                            "## 👤 次にすること\n\n- reviewer を止めてよいか返事をください")},
                    ]}},
                ]
                transcript.write_text("\n".join(json.dumps(x) for x in lines) + "\n", encoding="utf-8")
                code, out, err = _run_hook(workspace, transcript_path=transcript)
                self.assertEqual(code, 0, err)
                if blocked:
                    self.assertTrue(json.loads(out).get("reason", "").startswith("GDD wait watchdog"), out)
                else:
                    # 停止がどの検査にも押し返されずに通る（loop state も消さない）
                    self.assertEqual(out.strip(), "", out)
                    self.assertTrue((workspace / ".claude" / "gdd-dev.local.md").exists())

    def test_malformed_line_does_not_crash_hook_on_repeated_stop(self):
        """入口から: 中身の型が変な行があっても、続けて発火した Stop（stop_hook_active）で
        hook が落ちずに継続の判定を出す。落ちると shell は何も出さず、done guard が走らない。"""
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            _write_state_file(workspace, self._active_state())
            transcript = workspace / "transcript.jsonl"
            lines = [
                {"type": "user", "message": {"content": [{"type": "text", "text": "/gdd-dev"}]}},
                {"type": "user", "message": {"content": [
                    {"type": "tool_result", "tool_use_id": ["x"], "content": "{}"}]}},
                {"type": "assistant", "message": {"content": [
                    {"type": "text", "text": "continuing /gdd-dev requirements-gating."}]}},
            ]
            transcript.write_text("\n".join(json.dumps(x) for x in lines) + "\n", encoding="utf-8")
            code, out, err = _run_hook(workspace, transcript_path=transcript, stop_hook_active=True)
            self.assertEqual(code, 0, err)
            self.assertEqual(json.loads(out).get("decision"), "block", out)
            self.assertTrue(json.loads(out)["reason"].startswith("Continue the active `/gdd-dev` run"), out)
            log = (workspace / ".gdd" / "hook-errors.log").read_text(encoding="utf-8")
            self.assertIn('"source": "parse_transcript"', log)

    def test_inflight_suppression_requires_active_gdd(self):
        """Non-active state → in-flight check not reached (early return)."""
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            _write_state_file(workspace, {"active": "false", "session_id": "test-session"})
            transcript = workspace / "transcript.jsonl"
            _make_inflight_transcript(transcript)
            code, out, err = _run_hook(workspace, transcript_path=transcript)
            self.assertEqual(code, 0)
            self.assertEqual(out, "")


if __name__ == "__main__":
    unittest.main()
