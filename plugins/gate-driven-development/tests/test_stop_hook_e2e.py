"""Stop hook の E2E テスト（実 hook を起動する）: 基本の流れ・done guard・worktree の分離・継続の guard・terminal の除外・fallback 1 と 3・done guard の検査対象。

確かめる本体は `hooks/scripts/gdd_stop_hook.py`。
"""
from __future__ import annotations
# isort: skip_file
# ruff: noqa: F401,F811
import sys
from pathlib import Path as _P
sys.path.insert(0, str(_P(__file__).parent))
from _stop_hook_test_base import *  # noqa: F401,F403

class TestHookE2EBasicFlow(unittest.TestCase):
    """End-to-end: top-level guards and exit conditions."""

    def test_no_state_file_exits_silently(self):
        """No .claude/gdd-dev.local.md → SystemExit(0), no output."""
        with tempfile.TemporaryDirectory() as tmp:
            code, out, err = _run_hook(Path(tmp))
            self.assertEqual(code, 0)
            self.assertEqual(out, "")

    def test_active_false_exits_silently_preserves_file(self):
        """Fix #1: active: false → SystemExit(0), file kept (not deleted)."""
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            state_file = _write_state_file(ws, {
                "active": "false",
                "session_id": "abc-123",
                "iteration": "1",
            })
            transcript = ws / "transcript.jsonl"
            _make_transcript_jsonl(transcript, assistant_text="some text")
            code, out, _ = _run_hook(ws, transcript, session_id="abc-123")
            self.assertEqual(code, 0)
            self.assertEqual(out, "")
            self.assertTrue(state_file.exists(), "Fix #1 should preserve state file")

    def test_corrupt_frontmatter_fails_open_and_preserves_state(self):
        """Malformed local state → fail-open: no block injected, stderr warning, state preserved (AC-E8-3)."""
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            claude_dir = ws / ".claude"
            claude_dir.mkdir()
            state_file = claude_dir / "gdd-dev.local.md"
            state_file.write_text("not a valid frontmatter at all\n")
            code, out, err = _run_hook(ws)
            self.assertEqual(code, 0)
            self.assertTrue(state_file.exists(), "Corrupt state file should be preserved")
            self.assertNotIn("GDD Stop hook integrity failure", out, "fail-open must not inject a block")
            self.assertIn("GDD Stop hook: parse_state:", err, "fail-open must warn on stderr")
            self.assertTrue((ws / ".gdd" / "hook-errors.log").exists())

    def test_session_mismatch_exits_silently(self):
        """state_session != hook_session → SystemExit(0), no continuation."""
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            _write_state_file(ws, {
                "active": "true",
                "session_id": "state-owns",
                "iteration": "1",
            })
            transcript = ws / "transcript.jsonl"
            _make_transcript_jsonl(transcript, assistant_text="ok")
            code, out, _ = _run_hook(ws, transcript, session_id="different-session")
            self.assertEqual(code, 0)
            self.assertEqual(out, "", "Cross-session must not fire continuation")

    def test_active_true_empty_session_id_non_cursor_exits_silently(self):
        """active:true + empty session_id + non-cursor runtime → suppress continuation."""
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            _write_state_file(ws, {
                "active": "true",
                "session_id": "",
                "iteration": "1",
            })
            transcript = ws / "transcript.jsonl"
            _make_transcript_jsonl(transcript, assistant_text="text")
            code, out, err = _run_hook(ws, transcript, session_id="any")
            self.assertEqual(code, 0)
            self.assertEqual(out, "")
            self.assertIn("session_id が空", err)

    def test_active_true_empty_session_id_cursor_falls_through(self):
        """active:true + empty session_id + cursor → no block, falls through."""
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            _write_state_file(ws, {
                "active": "true",
                "session_id": "",
                "iteration": "1",
                "workflow_runtime": "cursor",
            })
            transcript = ws / "transcript.jsonl"
            _make_transcript_jsonl(transcript, assistant_text="text", user_text="random text")
            code, out, _ = _run_hook(
                ws,
                transcript,
                session_id="",
                claude_code_session_id=None,
            )
            self.assertEqual(code, 0)
            # No block payload — Cursor empty session_id is treated as valid
            self.assertNotIn('"decision": "block"', out)

    def test_invalid_iteration_blocks_and_preserves_state(self):
        """Non-integer iteration → fail-closed block, state preserved."""
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            state_file = _write_state_file(ws, {
                "active": "true",
                "session_id": "abc",
                "iteration": "not-a-number",
            })
            code, _, _ = _run_hook(ws, session_id="abc")
            self.assertEqual(code, 0)
            self.assertTrue(state_file.exists())
            self.assertTrue((ws / ".gdd" / "hook-errors.log").exists())

    def test_missing_transcript_path_exits_fully_silently_and_preserves_state(self):
        """No transcript_path → fully silent exit, avoiding side-window warning loops."""
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            state_file = _write_state_file(ws, {
                "active": "true",
                "session_id": "abc",
                "iteration": "1",
            })
            # No transcript_path passed
            code, out, err = _run_hook(ws, transcript_path=None, session_id="abc")
            self.assertEqual(code, 0)
            self.assertTrue(state_file.exists())
            self.assertEqual(out, "")
            self.assertEqual(err, "")
            self.assertFalse((ws / ".gdd" / "hook-errors.log").exists())

    def test_nonexistent_transcript_file_exits_silently_and_preserves_state(self):
        """Non-existent transcript_path → log and suppress continuation, not block-loop."""
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            state_file = _write_state_file(ws, {
                "active": "true",
                "session_id": "abc",
                "iteration": "1",
            })
            code, out, err = _run_hook(ws, Path(tmp) / "nope.jsonl", session_id="abc")
            self.assertEqual(code, 0)
            self.assertTrue(state_file.exists())
            self.assertTrue((ws / ".gdd" / "hook-errors.log").exists())
            self.assertEqual(out, "")
            self.assertIn("not found", err)
            self.assertIn("自動継続を抑止", err)

    def test_stale_cursor_state_without_transcript_does_not_emit_integrity_block(self):
        """Regression: stale Cursor state with empty session_id must not spam integrity blocks."""
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            state_file = _write_state_file(ws, {
                "active": "true",
                "session_id": "",
                "iteration": "1",
                "workflow_runtime": "cursor",
            })
            code, out, err = _run_hook(
                ws,
                transcript_path=None,
                session_id="",
                claude_code_session_id=None,
            )
            self.assertEqual(code, 0)
            self.assertTrue(state_file.exists())
            self.assertEqual(out, "")
            self.assertEqual(err, "")
            self.assertFalse((ws / ".gdd" / "hook-errors.log").exists())


class TestHookE2EDoneGuard(unittest.TestCase):
    """End-to-end: <gdd-stop reason='done'> validation against tasklist."""

    # OT-F10: all stop outputs must include a '👤 次にすること' block.
    _NEXT_ACTION = "\n\n## 👤 次にすること\n完了（追加対応なし）"

    def _setup_active_session(self, ws: Path, assistant_text: str) -> Path:
        """Common helper: state file + transcript with given assistant text."""
        _write_state_file(ws, {
            "active": "true",
            "session_id": "test-session",
            "iteration": "1",
        })
        transcript = ws / "transcript.jsonl"
        _make_transcript_jsonl(transcript, assistant_text=assistant_text)
        return transcript

    def test_done_with_no_tasklist_allowed(self):
        """No .steering/ at all → done allowed (trivial task path)."""
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            state_file = _write_state_file(ws, {
                "active": "true",
                "session_id": "test-session",
                "iteration": "1",
            })
            transcript = self._setup_active_session(
                ws, '<gdd-stop reason="done">' + self._NEXT_ACTION
            )
            code, out, _ = _run_hook(ws, transcript, session_id="test-session")
            self.assertEqual(code, 0)
            self.assertNotIn('"decision": "block"', out)
            self.assertFalse(state_file.exists(), "done success should delete state file")

    def test_done_with_clean_tasklist_allowed(self):
        """All conditions met → done succeeds and deletes state file."""
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            state_file = _write_state_file(ws, {
                "active": "true",
                "session_id": "test-session",
                "iteration": "1",
            })
            _write_steering(ws, "20260501-test", _CLEAN_TASKLIST, _CLEAN_STATE)
            # done guard の検査対象は bind 済み steering だけ。
            # bind を書かないと unbound 扱いになり warn へ降格して block しない。
            _write_binding(ws, "20260501-test")
            transcript = self._setup_active_session(
                ws, '<gdd-stop reason="done">' + self._NEXT_ACTION
            )
            code, out, _ = _run_hook(ws, transcript, session_id="test-session")
            self.assertEqual(code, 0)
            self.assertNotIn('"decision": "block"', out)
            self.assertFalse(state_file.exists())

    def test_done_with_pending_task_blocked(self):
        """Remaining task in Pending → block payload printed."""
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            _write_state_file(ws, {
                "active": "true",
                "session_id": "test-session",
                "iteration": "1",
            })
            tasklist = textwrap.dedent("""\
                # Tasklist

                ## Current Task
                - なし

                ## Pending Tasks
                - T2 | AC-02 | まだ未着手

                ## Completed Tasks
                - T1 | AC-01 | done

                ## Verification
                - V-01 | unit_test | pass | ok | -

                ## Status
                Next Action=done
            """)
            _write_steering(ws, "20260501-test", tasklist, _CLEAN_STATE)
            # done guard の検査対象は bind 済み steering だけ。
            # bind を書かないと unbound 扱いになり warn へ降格して block しない。
            _write_binding(ws, "20260501-test")
            transcript = self._setup_active_session(
                ws, '<gdd-stop reason="done">' + self._NEXT_ACTION
            )
            code, out, _ = _run_hook(ws, transcript, session_id="test-session")
            self.assertEqual(code, 0)
            payload = json.loads(out.strip())
            self.assertEqual(payload["decision"], "block")
            self.assertIn("未完了タスク", payload["reason"])

    def test_done_with_no_verification_section_blocked(self):
        """Tasklist missing Verification section → block."""
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            _write_state_file(ws, {
                "active": "true",
                "session_id": "test-session",
                "iteration": "1",
            })
            tasklist = textwrap.dedent("""\
                # Tasklist

                ## Current Task
                - なし

                ## Pending Tasks
                - なし

                ## Completed Tasks
                - T1 | AC-01 | done

                ## Status
                Next Action=done
            """)
            _write_steering(ws, "20260501-test", tasklist, _CLEAN_STATE)
            # done guard の検査対象は bind 済み steering だけ。
            # bind を書かないと unbound 扱いになり warn へ降格して block しない。
            _write_binding(ws, "20260501-test")
            transcript = self._setup_active_session(
                ws, '<gdd-stop reason="done">' + self._NEXT_ACTION
            )
            code, out, _ = _run_hook(ws, transcript, session_id="test-session")
            self.assertEqual(code, 0)
            payload = json.loads(out.strip())
            self.assertEqual(payload["decision"], "block")
            self.assertIn("Verification セクションが存在しません", payload["reason"])

    def test_done_with_pending_verification_blocked(self):
        """Verification has pending row → block."""
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            _write_state_file(ws, {
                "active": "true",
                "session_id": "test-session",
                "iteration": "1",
            })
            tasklist = textwrap.dedent("""\
                # Tasklist

                ## Current Task
                - なし

                ## Pending Tasks
                - なし

                ## Completed Tasks
                - T1 | AC-01 | done

                ## Verification
                | method | status | evidence | notes |
                |---|---|---|---|
                | method=ac:AC-01 | pending | 未実行 | - |

                ## Status
                Next Action=done
            """)
            # 維持: canonical 表行にしても status=pending は「未完了/失敗」で
            # block のまま（design.md § 5「canonical に pending / fail → 不変」）。
            # decision/reason は変わらず、fixture の list 形だけが schema 違反
            # だったので canonical 化のみで RED が解消する（Category A2）。
            _write_steering(ws, "20260501-test", tasklist, _CLEAN_STATE)
            # done guard の検査対象は bind 済み steering だけ。
            # bind を書かないと unbound 扱いになり warn へ降格して block しない。
            _write_binding(ws, "20260501-test")
            transcript = self._setup_active_session(
                ws, '<gdd-stop reason="done">' + self._NEXT_ACTION
            )
            code, out, _ = _run_hook(ws, transcript, session_id="test-session")
            self.assertEqual(code, 0)
            payload = json.loads(out.strip())
            self.assertEqual(payload["decision"], "block")
            self.assertIn("未完了/失敗", payload["reason"])

    def test_done_with_route_in_progress_blocked(self):
        """state.md Route In Progress != none → block."""
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            _write_state_file(ws, {
                "active": "true",
                "session_id": "test-session",
                "iteration": "1",
            })
            state_with_route = "# State\nRoute In Progress=systematic_debugging\n"
            _write_steering(ws, "20260501-test", _CLEAN_TASKLIST, state_with_route)
            # done guard の検査対象は bind 済み steering だけ。
            # bind を書かないと unbound 扱いになり warn へ降格して block しない。
            _write_binding(ws, "20260501-test")
            transcript = self._setup_active_session(
                ws, '<gdd-stop reason="done">' + self._NEXT_ACTION
            )
            code, out, _ = _run_hook(ws, transcript, session_id="test-session")
            self.assertEqual(code, 0)
            payload = json.loads(out.strip())
            self.assertEqual(payload["decision"], "block")
            self.assertIn("Route In Progress=systematic_debugging", payload["reason"])

    def test_human_check_waiting_does_not_run_done_guard(self):
        """human-check-waiting reason doesn't validate tasklist (it's a pause, not done)."""
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            state_file = _write_state_file(ws, {
                "active": "true",
                "session_id": "test-session",
                "iteration": "1",
            })
            # Even with un-clean tasklist (no Verification), human-check-waiting passes.
            tasklist_dirty = textwrap.dedent("""\
                # Tasklist

                ## Current Task
                ### Task: T-1 | AC-01 | active task

                ## Pending Tasks
                - T2 | AC-02 | next

                ## Completed Tasks
                - なし
            """)
            _write_steering(ws, "20260501-test", tasklist_dirty)
            transcript = self._setup_active_session(
                ws,
                '<gdd-stop reason="human-check-waiting">'
                "\n\n## 👤 次にすること\nOKで承認してください",
            )
            code, out, _ = _run_hook(ws, transcript, session_id="test-session")
            self.assertEqual(code, 0)
            self.assertNotIn('"decision": "block"', out)
            self.assertTrue(
                state_file.exists(),
                "human-check-waiting must preserve state.md (it's a pause, not terminal)",
            )

    def test_external_review_waiting_is_pause_and_preserves_state(self):
        """OT-F3 Change A: external-review-waiting is a recognized pause reason.

        No done-guard runs (it's not done), no continuation nudge fires (the stop
        tag is recognized), and state.md is preserved so the review loop can resume.
        """
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            state_file = _write_state_file(ws, {
                "active": "true",
                "session_id": "test-session",
                "iteration": "1",
            })
            # Un-clean tasklist must not matter: this is a pause, not done.
            tasklist_dirty = textwrap.dedent("""\
                # Tasklist

                ## Current Task
                ### Task: T-1 | AC-01 | active task

                ## Pending Tasks
                - T2 | AC-02 | next

                ## Completed Tasks
                - なし
            """)
            _write_steering(ws, "20260501-test", tasklist_dirty)
            # The phase marker makes looks_like_gdd_continuation() return True,
            # so without recognizing external-review-waiting the hook would fire a
            # "Continue" nudge. Recognizing the reason must suppress that.
            transcript = self._setup_active_session(
                ws,
                "<gdd-phase>gdd-pr-review-followup</gdd-phase>\n"
                "レビュー収束を待っています。\n\n"
                '<gdd-stop reason="external-review-waiting">'
                "\n\n## 👤 次にすること\nレビュー収束を待っています。中断するには「中断」と言ってください。",
            )
            code, out, _ = _run_hook(ws, transcript, session_id="test-session")
            self.assertEqual(code, 0)
            self.assertNotIn('"decision": "block"', out)
            self.assertNotIn("Continue to terminal state", out)
            self.assertTrue(
                state_file.exists(),
                "external-review-waiting must preserve state.md (pause, not terminal)",
            )

    def test_cancelled_does_not_run_done_guard(self):
        """cancelled reason skips done validation and deletes state."""
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            state_file = _write_state_file(ws, {
                "active": "true",
                "session_id": "test-session",
                "iteration": "1",
            })
            # Dirty tasklist — cancelled should still allow stop
            tasklist_dirty = textwrap.dedent("""\
                # Tasklist

                ## Current Task
                ### Task: T-1 | AC-01 | abandoned task

                ## Pending Tasks
                - T2 | AC-02 | abandoned

                ## Completed Tasks
                - なし
            """)
            _write_steering(ws, "20260501-test", tasklist_dirty)
            transcript = self._setup_active_session(ws, '<gdd-stop reason="cancelled">')
            code, out, _ = _run_hook(ws, transcript, session_id="test-session")
            self.assertEqual(code, 0)
            self.assertNotIn('"decision": "block"', out)
            self.assertFalse(state_file.exists(), "cancelled must delete state file")


class TestHookE2EWorktreeIsolation(unittest.TestCase):
    """End-to-end: ensure stop hook scoping respects worktree boundaries."""

    def test_sibling_worktree_state_is_ignored_for_stop_fallback(self):
        """state.md in a sibling directory must not trigger stop in current cwd.

        This is the worktree isolation contract: a different chat's
        Resume From: human-check-waiting should not affect this hook firing."""
        with tempfile.TemporaryDirectory() as tmp:
            current = Path(tmp) / "current"
            sibling = Path(tmp) / "sibling"
            current.mkdir()
            sibling.mkdir()
            # sibling has a steering with human-check-waiting Resume From
            sibling_steering = sibling / ".steering" / "20260501-other"
            sibling_steering.mkdir(parents=True)
            (sibling_steering / "state.md").write_text(
                "# State\n- Resume From: human-check-waiting\n", encoding="utf-8"
            )
            # current has an active session but no steering of its own
            _write_state_file(current, {
                "active": "true",
                "session_id": "test-session",
                "iteration": "1",
            })
            transcript = current / "transcript.jsonl"
            _make_transcript_jsonl(
                transcript, assistant_text="無関係な発話", user_text="無関係な質問"
            )
            code, out, err = _run_hook(current, transcript, session_id="test-session")
            self.assertEqual(code, 0)
            # Sibling state must not fire the human-check-waiting stop
            self.assertNotIn("human-check", out)
            # And should not fire continuation (user/assistant text is unrelated)
            self.assertIn("自動継続を抑止しました", err)


class TestHookE2EContinuationGuard(unittest.TestCase):
    """End-to-end: stale active:true file does not hijack unrelated chats."""

    def test_unrelated_chat_with_stale_active_true_no_continuation(self):
        """Stale gdd-dev.local.md + unrelated user text → no continuation."""
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            _write_state_file(ws, {
                "active": "true",
                "session_id": "test-session",
                "iteration": "1",
            })
            transcript = ws / "transcript.jsonl"
            _make_transcript_jsonl(
                transcript,
                assistant_text="JavaScript の Promise について説明しました。",
                user_text="次は async/await の使い方を教えて",
            )
            code, out, err = _run_hook(ws, transcript, session_id="test-session")
            self.assertEqual(code, 0)
            # No continuation block injected — unrelated user text is ignored
            self.assertNotIn("Continue the active /gdd-dev run", out)
            self.assertIn("自動継続を抑止しました", err)

    def test_peer_turn_after_gdd_dev_does_not_revive_stale_continuation(self):
        """pr-review 是正 (Finding Z): `parse_transcript()` は peer turn を
        `last_user_text` 候補から除外するため、直近の実会話ターンが peer 由来の
        ときは `last_user_text` が「1 つ前の人間本人の発話」のまま stale で残る。
        `[human: "/gdd-dev continue", peer: "中止"]` では `last_user_text` が
        古い `/gdd-dev continue` のままなので、`looks_like_gdd_continuation()`
        だけで判定すると peer 受信を契機に古い継続意図が復活してしまう。
        `last_user_turn_is_peer()` を先行判定し、直近が peer なら継続を抑止する。
        """
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            _write_state_file(ws, {
                "active": "true",
                "session_id": "test-session",
                "iteration": "1",
            })
            transcript = ws / "transcript.jsonl"
            records = [
                {
                    "type": "user",
                    "message": {"content": [{"type": "text", "text": "/gdd-dev continue"}]},
                },
                {
                    "type": "assistant",
                    "message": {"content": [{"type": "text", "text": "了解しました。続けます。"}]},
                },
                {
                    "type": "user",
                    "isMeta": True,
                    "origin": {"kind": "peer", "from": "other-session"},
                    "message": {"content": [{"type": "text", "text": "中止"}]},
                },
            ]
            transcript.write_text(
                "\n".join(json.dumps(r) for r in records) + "\n", encoding="utf-8"
            )
            code, out, err = _run_hook(ws, transcript, session_id="test-session")
            self.assertEqual(code, 0)
            if out.strip():
                self.assertNotEqual(json.loads(out).get("decision"), "block", out)
            self.assertIn("peer", err)

    def test_peer_turn_followed_by_unreadable_line_does_not_revive_continuation(self):
        """peer のターンの後に json.loads が JSONDecodeError 以外で失敗する行（桁の多い整数）
        があっても、古い継続意図で継続しない。peer の判定が例外で終わったときは、peer と
        同じく止める側に倒す（続けて発火した Stop でも同じ）。"""
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            _write_state_file(ws, {
                "active": "true",
                "session_id": "test-session",
                "iteration": "1",
            })
            transcript = ws / "transcript.jsonl"
            records = [
                {"type": "user", "message": {"content": [{"type": "text", "text": "/gdd-dev continue"}]}},
                {"type": "assistant", "message": {"content": [{"type": "text", "text": "了解しました。続けます。"}]}},
                {"type": "user", "isMeta": True, "origin": {"kind": "peer", "from": "other-session"},
                 "message": {"content": [{"type": "text", "text": "中止"}]}},
            ]
            unreadable = '{"type": "assistant", "n": ' + "1" * 5000 + "}"
            with self.assertRaises(ValueError):  # 前提: int の桁数の上限（sys.get_int_max_str_digits）で読めない
                json.loads(unreadable)
            transcript.write_text(
                "\n".join(json.dumps(r) for r in records) + "\n" + unreadable + "\n", encoding="utf-8"
            )
            for active in (False, True):
                with self.subTest(stop_hook_active=active):
                    code, out, err = _run_hook(ws, transcript, session_id="test-session",
                                               stop_hook_active=active)
                    self.assertEqual(code, 0, err)
                    if out.strip():
                        self.assertNotEqual(json.loads(out).get("decision"), "block", out)
                    self.assertIn("判定できない", err)
            log = (ws / ".gdd" / "hook-errors.log").read_text(encoding="utf-8")
            self.assertIn('"source": "last_user_turn_is_peer"', log)

    def test_human_text_with_malformed_sibling_block_does_not_revive_continuation(self):
        """人間の発話の record に文字列でない tool_use_id の block が混ざっても、その発話で
        継続意図を判定する。record ごと捨てると、古い `/gdd-dev continue` で継続の block が出る。"""
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            _write_state_file(ws, {
                "active": "true",
                "session_id": "test-session",
                "iteration": "1",
            })
            transcript = ws / "transcript.jsonl"
            records = [
                {"type": "user", "message": {"content": [{"type": "text", "text": "/gdd-dev continue"}]}},
                {"type": "assistant", "message": {"content": [{"type": "text", "text": "了解しました。続けます。"}]}},
                {"type": "user", "message": {"content": [
                    {"type": "text", "text": "次は async/await の使い方を教えて"},
                    {"type": "tool_result", "tool_use_id": ["x"], "content": "{}"},
                ]}},
                {"type": "assistant", "message": {"content": [{"type": "text", "text": "説明しました。"}]}},
            ]
            transcript.write_text("\n".join(json.dumps(r) for r in records) + "\n", encoding="utf-8")
            for active in (False, True):
                with self.subTest(stop_hook_active=active):
                    code, out, err = _run_hook(ws, transcript, session_id="test-session",
                                               stop_hook_active=active)
                    self.assertEqual(code, 0, err)
                    if out.strip():
                        self.assertNotEqual(json.loads(out).get("decision"), "block", out)
                    self.assertIn("継続意図が見えない", err)
            log = (ws / ".gdd" / "hook-errors.log").read_text(encoding="utf-8")
            self.assertIn('"source": "parse_transcript"', log)

    def test_blank_human_record_does_not_revive_continuation(self):
        """空白だけの人間の発話（str content・bare str）の後は、その前の `/gdd-dev continue` で
        継続しない。"""
        for name, content in {"str content": "   ", "bare str": ["   "]}.items():
            with self.subTest(form=name), tempfile.TemporaryDirectory() as tmp:
                ws = Path(tmp)
                _write_state_file(ws, {"active": "true", "session_id": "test-session", "iteration": "1"})
                transcript = ws / "transcript.jsonl"
                records = [
                    {"type": "user", "message": {"content": [{"type": "text", "text": "/gdd-dev continue"}]}},
                    {"type": "assistant", "message": {"content": [{"type": "text", "text": "了解しました。"}]}},
                    {"type": "user", "message": {"content": content}},
                    {"type": "assistant", "message": {"content": [{"type": "text", "text": "説明しました。"}]}},
                ]
                transcript.write_text("\n".join(json.dumps(r) for r in records) + "\n", encoding="utf-8")
                code, out, err = _run_hook(ws, transcript, session_id="test-session")
                self.assertEqual(code, 0, err)
                if out.strip():
                    self.assertNotEqual(json.loads(out).get("decision"), "block", out)
                self.assertIn("継続意図が見えない", err)

    def test_ok_reply_after_human_check_pause_continues(self):
        """OK reply after human-check pause → continuation fires (intended behavior)."""
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            _write_state_file(ws, {
                "active": "true",
                "session_id": "test-session",
                "iteration": "1",
            })
            transcript = ws / "transcript.jsonl"
            # The last assistant message is the human-check pause template.
            _make_transcript_jsonl(
                transcript,
                assistant_text='## 🔍 確認をお願いします\n承認ポイント: ...\n<gdd-stop reason="human-check-waiting">',
                user_text="OK",
            )
            code, out, err = _run_hook(ws, transcript, session_id="test-session")
            self.assertEqual(code, 0)
            # Continuation should NOT be suppressed here. The hook either
            # blocks for human-check-waiting or injects a continuation prompt;
            # in either case the suppression message must NOT appear.
            self.assertNotIn("自動継続を抑止しました", err)


class TestHookE2ETerminalExclusion(unittest.TestCase):
    """Steering lookup: terminal task (Next Action=done) exclusion (e2e).

    A steering dir whose tasklist already declares Next Action=done/cancelled
    must not hijack the hook's lookups for a new task started after it.
    Measured end-to-end through the hook process (the module-level helper this
    class used to name was removed in T-5 together with record_debug_bounce())."""

    def test_completed_steering_skipped_for_active_lookup(self):
        """A finished steering dir must not block a new active session.

        Setup: two steering dirs. Newer one has Next Action=done (terminal),
        older has an active task. With a brand-new top-level run that emits
        <gdd-stop reason="human-check-waiting">, the hook's various lookups
        should not get confused by the terminal one."""
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            _write_state_file(ws, {
                "active": "true",
                "session_id": "test-session",
                "iteration": "1",
            })
            # Older steering dir (alphabetically earlier) — active
            active_tasklist = textwrap.dedent("""\
                # Tasklist
                ## Current Task
                ### Task: T-1 | AC-01 | active task

                ## Pending Tasks
                - なし

                ## Completed Tasks
                - なし

                ## Status
                Next Action=gdd-test-driven-development
            """)
            _write_steering(ws, "20260101-old-active", active_tasklist)
            # Newer steering dir — terminal (Next Action=done)
            done_tasklist = textwrap.dedent("""\
                # Tasklist
                ## Current Task
                - なし

                ## Pending Tasks
                - なし

                ## Completed Tasks
                - T1 | AC-01 | done

                ## Verification
                - V-01 | unit_test | pass | ok | -

                ## Status
                Next Action=done
            """)
            _write_steering(ws, "20260601-new-done", done_tasklist)
            # Use human-check-waiting so we exercise the lookup path through
            # the steering scan without triggering the done guard validation.
            transcript = ws / "transcript.jsonl"
            _make_transcript_jsonl(
                transcript,
                assistant_text='## 🔍 確認をお願いします\n<gdd-stop reason="human-check-waiting">',
            )
            code, out, _ = _run_hook(ws, transcript, session_id="test-session")
            # Should pause for human-check-waiting (not crash, not pick wrong dir)
            self.assertEqual(code, 0)


class TestHookE2EFallback1ToolResult(unittest.TestCase):
    """Fallback 1: <gdd-stop> in last tool_result (subagent dispatch).

    When a phase skill runs as Agent() subagent, its <gdd-stop> appears as
    tool_result content (role=user), not in main session's assistant text.
    The hook must still detect and act on it."""

    def test_stop_marker_in_tool_result_triggers_pause(self):
        """human-check-waiting marker only in tool_result still triggers pause behavior."""
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            state_file = _write_state_file(ws, {
                "active": "true",
                "session_id": "test-session",
                "iteration": "1",
            })
            transcript = ws / "transcript.jsonl"
            # Subagent emitted the marker via tool_result; main assistant text
            # is generic (no marker).
            transcript.write_text(
                json.dumps({
                    "type": "user",
                    "message": {"content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": "tu1",
                            "content": '## 🔍 確認をお願いします\n<gdd-stop reason="human-check-waiting">',
                        }
                    ]},
                }) + "\n" +
                json.dumps({
                    "type": "assistant",
                    "message": {"content": [
                        {"type": "text", "text": "承認待ちです。"}
                    ]},
                }) + "\n",
                encoding="utf-8",
            )
            code, out, err = _run_hook(ws, transcript, session_id="test-session")
            self.assertEqual(code, 0)
            # Must NOT inject a continuation block (paused for human check)
            self.assertNotIn("Continue to terminal state", out)
            # state file must be preserved (human-check-waiting is a pause)
            self.assertTrue(state_file.exists())

    def test_clarification_needed_marker_triggers_pause(self):
        """clarification-needed marker pauses instead of autonomous continuation."""
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            state_file = _write_state_file(ws, {
                "active": "true",
                "session_id": "test-session",
                "iteration": "1",
            })
            transcript = ws / "transcript.jsonl"
            _make_transcript_jsonl(
                transcript,
                user_text="/gdd-dev 通知改善をしたい",
                assistant_text=(
                    "要件を固めるため、先に確認します。\n"
                    "1. 対象はどの通知ですか？\n"
                    "<gdd-stop reason=\"clarification-needed\">"
                ),
            )
            code, out, err = _run_hook(ws, transcript, session_id="test-session")
            self.assertEqual(code, 0)
            self.assertNotIn("Continue to terminal state", out)
            self.assertTrue(state_file.exists())

    def test_done_marker_in_tool_result_runs_done_guard(self):
        """`<gdd-stop reason="done">` in tool_result still triggers done validation."""
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            _write_state_file(ws, {
                "active": "true",
                "session_id": "test-session",
                "iteration": "1",
            })
            # No tasklist → done allowed (trivial)
            # Main assistant text must also carry the 👤 次にすること block (OT-F10).
            transcript = ws / "transcript.jsonl"
            transcript.write_text(
                json.dumps({
                    "type": "user",
                    "message": {"content": [{
                        "type": "tool_result",
                        "tool_use_id": "tu1",
                        "content": '<gdd-stop reason="done">',
                    }]},
                }) + "\n" +
                json.dumps({
                    "type": "assistant",
                    "message": {"content": [
                        {"type": "text", "text": "完了\n\n## 👤 次にすること\n完了（追加対応なし）"},
                    ]},
                }) + "\n",
                encoding="utf-8",
            )
            code, out, _ = _run_hook(ws, transcript, session_id="test-session")
            self.assertEqual(code, 0)
            self.assertNotIn('"decision": "block"', out)


class TestHookE2EFallback3SteeringResumeFrom(unittest.TestCase):
    """Fallback 3: Resume From: human-check-waiting in .steering/*/state.md.

    Markerless state fallback is allowed only when the current output also
    looks like a human-check surface. Explicit <gdd-stop> remains primary."""

    def test_resume_from_human_check_waiting_with_hitl_surface_triggers_pause(self):
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            state_file = _write_state_file(ws, {
                "active": "true",
                "session_id": "test-session",
                "iteration": "1",
            })
            steering = ws / ".steering" / "20260501-task"
            steering.mkdir(parents=True)
            (steering / "state.md").write_text(
                "# State\n\n## Gate Status\n- Resume From: human-check-waiting\n",
                encoding="utf-8",
            )
            transcript = ws / "transcript.jsonl"
            # No <gdd-stop> in assistant text or tool_result.
            _make_transcript_jsonl(
                transcript,
                assistant_text="## 確認\n### 判断ポイント\n1. Scope を確認してください。\n承認ポイント: ...",
                user_text="",
            )
            code, out, _ = _run_hook(ws, transcript, session_id="test-session")
            self.assertEqual(code, 0)
            # Pause path: state.md preserved, no continuation injected.
            self.assertTrue(state_file.exists())
            self.assertNotIn("Continue to terminal state", out)

    def test_resume_from_backtick_format_with_hitl_surface_triggers_pause(self):
        r"""gdd-requirements-gating writes `- \`Resume From=human-check-waiting\`` (backtick).
        This format must also be detected."""
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            state_file = _write_state_file(ws, {
                "active": "true",
                "session_id": "test-session",
                "iteration": "1",
            })
            steering = ws / ".steering" / "20260501-task"
            steering.mkdir(parents=True)
            (steering / "state.md").write_text(
                "# State\n\n- `Resume From=human-check-waiting`\n",
                encoding="utf-8",
            )
            transcript = ws / "transcript.jsonl"
            _make_transcript_jsonl(transcript, assistant_text="判断ポイント\nOKでも許可されないこと\n")
            code, out, _ = _run_hook(ws, transcript, session_id="test-session")
            self.assertEqual(code, 0)
            self.assertTrue(state_file.exists())
            self.assertNotIn("Continue to terminal state", out)

    def test_resume_from_human_check_waiting_without_hitl_surface_is_suppressed(self):
        """state.md alone is not enough; markerless fallback needs HITL-shaped output."""
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            state_file = _write_state_file(ws, {
                "active": "true",
                "session_id": "test-session",
                "iteration": "1",
            })
            steering = ws / ".steering" / "20260501-task"
            steering.mkdir(parents=True)
            (steering / "state.md").write_text(
                "# State\n\n## Gate Status\n- Resume From: human-check-waiting\n",
                encoding="utf-8",
            )
            transcript = ws / "transcript.jsonl"
            _make_transcript_jsonl(transcript, assistant_text="承認をお願いします。", user_text="")
            code, out, err = _run_hook(ws, transcript, session_id="test-session")
            self.assertEqual(code, 0)
            self.assertTrue(state_file.exists())
            self.assertNotIn("Continue to terminal state", out)
            self.assertIn("markerless state fallback suppressed", err)

    def test_stop_hook_active_chain_bounded_by_ceiling(self):
        """Sanity check for enforce_consecutive_block_ceiling: a same-turn
        stop_hook_active=true chain (no <gdd-stop> marker, continuation
        intent present) must self-stop once it exceeds
        STOP_HOOK_MAX_CONSECUTIVE_BLOCKS, instead of looping forever."""
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            _write_state_file(ws, {
                "active": "true",
                "session_id": "test-session",
                "iteration": "1",
            })
            transcript = ws / "transcript.jsonl"
            _make_transcript_jsonl(
                transcript,
                assistant_text="作業を継続します。",
                user_text="/gdd-dev",
            )
            stopped = False
            for _ in range(8):
                code, out, err = _run_hook(
                    ws, transcript, session_id="test-session", stop_hook_active=True,
                )
                self.assertEqual(code, 0)
                if "consecutive stop-hook blocks reached" in err:
                    stopped = True
                    break
                self.assertIn('"decision": "block"', out)
            self.assertTrue(stopped, "ceiling never triggered a self-stop")

    def test_fresh_turn_human_check_loophole_stops_immediately(self):
        """Regression for the reported infinite-loop bug: state.md is stuck
        at human-check-waiting, the current output does not look like a
        human-check surface (markerless fallback suppressed), and each call
        is a genuinely fresh turn (stop_hook_active=false) that still shows
        GDD continuation intent (e.g. an autonomous driver re-invoking
        /gdd-dev). enforce_consecutive_block_ceiling alone never trips here
        because it only counts stop_hook_active=true chains and resets on
        every fresh turn — so the hook must stop on the very first fresh
        turn it sees this exact condition, not loop forever."""
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            _write_state_file(ws, {
                "active": "true",
                "session_id": "test-session",
                "iteration": "1",
            })
            steering = ws / ".steering" / "20260501-task"
            steering.mkdir(parents=True)
            (steering / "state.md").write_text(
                "# State\n\n## Gate Status\n- Resume From: human-check-waiting\n",
                encoding="utf-8",
            )
            transcript = ws / "transcript.jsonl"
            _make_transcript_jsonl(
                transcript,
                assistant_text="作業を継続します。",
                user_text="/gdd-dev",
            )
            code, out, err = _run_hook(
                ws, transcript, session_id="test-session", stop_hook_active=False,
            )
            self.assertEqual(code, 0)
            self.assertNotIn("Continue to terminal state", out)
            self.assertIn("Stopping immediately", err)


class TestHookE2EActiveTaskScoping(unittest.TestCase):
    """done guard の検査対象が **binding.json だけ**で決まること（bind 限定の変更で契約変更）。

    旧契約は「`gdd-dev.local.md` の `task_id` hint を優先し、無ければ逆ソート先頭」
    という**推測ベースの選択**で、`.steering/` に 2 タスクが並ぶと別タスクの
    pending verification で done がブロックされた（OT-F2）。
    bind 限定の変更以降は hint も逆ソートも使わず、bind された steering だけを見る。

    hint 機構（`_resolve_active_slug` / `_find_active_tasklist`）は
    `record_debug_bounce()` からのみ使われていたため、**T-5 で同関数ごと削除済み**。
    hint を直接測っていた `TestLegacySlugHintUnit` も同時に削除した（測る対象が無い）。
    """

    _ACTIVE_SLUG = "20260614-example-bootstrap-task"
    _DORMANT_SLUG = "20260614-pr-template-maintenance"

    _ACTIVE_TASKLIST = textwrap.dedent("""\
        # Tasklist

        ## Current Task
        - なし

        ## Pending Tasks
        - なし

        ## Completed Tasks
        - T1 | AC-01 | done

        ## Verification
        | method | status | evidence | notes |
        |---|---|---|---|
        | method=ac:AC-01 | pass | テスト通過 | - |

        ## Status
        Next Action=done
    """)
    # 維持: canonical 表行の全 pass は allow のまま（design.md § 5「canonical
    # 全 pass → allow / 不変」）。旧 list 形は schema 違反で誤 block していた
    # ため、canonical 化のみで
    # `test_bound_steering_is_checked_even_when_reverse_sort_would_pick_another`
    # の RED が解消する（Category A2。テスト本文の主張は bind 選択であり
    # Verification 文法とは無関係）。

    # pending タスクあり → done-guard がこちらを選ぶとブロックされる
    _DORMANT_TASKLIST = textwrap.dedent("""\
        # Tasklist

        ## Current Task
        - なし

        ## Pending Tasks
        - T2 | AC-01 | 実装待ち

        ## Completed Tasks
        - なし

        ## Verification
        | method | status | evidence | notes |
        |---|---|---|---|
        | method=ac:AC-01 | pending | 未実施 | - |

        ## Status
        Next Action=gdd-implementation-gating
    """)
    # 維持: このクラスの全テストは dormant 側の block を「## Pending Tasks」の
    # 未完了タスク（Check 1）で成立させており、Verification の内容には依存
    # しない。canonical 化しても block 判定は変わらない（Category A2）。

    _DONE_OUTPUT = '## 👤 次にすること\n- 完了（追加対応なし）'

    def test_unbound_does_not_guess_a_steering_dir(self):
        """bind が無ければ **どの steering も選ばない**（bind 限定の変更で挙動を変更）。

        旧挙動は「task_id hint が無ければ逆ソート先頭を選ぶ」で、
        本テストはそれを「既存動作の記録」として固定していた。これは
        **推測で検査対象を決める**という bind 限定で塞ぐ欠陥そのものなので、
        新契約（bind 不能なら block せず warn + 候補提示）に置き換える。

        判別力: 逆ソート選択に戻る退行は dormant（pending あり）を選んで
        block するため、この assert が落ちる。
        """
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            _write_steering(ws, self._DORMANT_SLUG, self._DORMANT_TASKLIST)
            _write_steering(ws, self._ACTIVE_SLUG, self._ACTIVE_TASKLIST)
            _write_state_file(ws, {
                "active": "true",
                "session_id": "test-session",
                "iteration": "1",
            })
            transcript = ws / "transcript.jsonl"
            _make_transcript_jsonl(
                transcript,
                assistant_text='<gdd-stop reason="done">\n\n' + self._DONE_OUTPUT,
            )
            code, out, err = _run_hook(ws, transcript, session_id="test-session")
            self.assertEqual(code, 0)
            self.assertNotIn('"decision": "block"', out,
                "bind が無いのに steering を推測して block してはいけない")
            self.assertIn("gdd:bind-unresolved", out + err)

    def test_bound_steering_is_checked_even_when_reverse_sort_would_pick_another(self):
        """positive control: bind 済みなら**その steering だけ**を検査する。

        上のテストだけだと「常に block しない」実装でも緑になる。
        dormant（逆ソート先頭・pending あり）が並存する状態で active に bind し、
        **block されない**こと（= dormant を見ていない）を測る。
        さらに dormant 側に bind し直すと block される（= 選択が bind に従っている）。
        """
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            _write_steering(ws, self._DORMANT_SLUG, self._DORMANT_TASKLIST)
            _write_steering(ws, self._ACTIVE_SLUG, self._ACTIVE_TASKLIST)
            _write_state_file(ws, {
                "active": "true", "session_id": "test-session", "iteration": "1",
            })
            transcript = ws / "transcript.jsonl"
            _make_transcript_jsonl(
                transcript,
                assistant_text='<gdd-stop reason="done">\n\n' + self._DONE_OUTPUT,
            )
            _write_binding(ws, self._ACTIVE_SLUG)
            code, out, _ = _run_hook(ws, transcript, session_id="test-session")
            self.assertEqual(code, 0)
            self.assertNotIn('"decision": "block"', out, f"out={out}")

            # bind 先を dormant に差し替えると、今度は block される
            (ws / ".gdd" / "tasks" / self._ACTIVE_SLUG / "binding.json").unlink()
            _write_binding(ws, self._DORMANT_SLUG)
            _write_state_file(ws, {
                "active": "true", "session_id": "test-session", "iteration": "1",
            })
            code, out, _ = _run_hook(ws, transcript, session_id="test-session")
            self.assertIn('"decision": "block"', out, f"out={out}")
            self.assertIn(self._DORMANT_SLUG, out)

    def test_task_id_hint_cannot_redirect_the_done_guard(self):
        """`gdd-dev.local.md` の `task_id` が done guard の検査対象を動かせないこと。

        旧挙動では hint が検査対象の選択に効き、パストラバーサル文字列を
        サニタイズしたうえで legacy fallback に落とす、という形で守っていた。
        bind 限定の変更以降、検査対象は **binding.json だけ**で決まるので、
        hint は安全な値でも敵対的な値でも結果を変えない ―― 守り方が
        「サニタイズ」から「そもそも入力にしない」に変わった。

        判別力: hint を再び選択に使う退行は、下の 2 つの assert のどちらかを落とす。
        """
        transcript_text = '<gdd-stop reason="done">\n\n' + self._DONE_OUTPUT
        results = {}
        for label, task_id in (
            ("traversal", "../../evil-traversal"),
            ("other-slug", self._ACTIVE_SLUG),
            ("absent", None),
        ):
            with tempfile.TemporaryDirectory() as tmp:
                ws = Path(tmp)
                _write_steering(ws, self._DORMANT_SLUG, self._DORMANT_TASKLIST)
                _write_steering(ws, self._ACTIVE_SLUG, self._ACTIVE_TASKLIST)
                # bind は dormant（pending あり）に固定する
                _write_binding(ws, self._DORMANT_SLUG)
                frontmatter = {
                    "active": "true", "session_id": "test-session", "iteration": "1",
                }
                if task_id is not None:
                    frontmatter["task_id"] = task_id
                _write_state_file(ws, frontmatter)
                transcript = ws / "transcript.jsonl"
                _make_transcript_jsonl(transcript, assistant_text=transcript_text)
                _code, out, _ = _run_hook(ws, transcript, session_id="test-session")
                results[label] = out
        # hint の値によらず、bind 先（dormant）を見て block する
        for label, out in results.items():
            with self.subTest(hint=label):
                self.assertIn('"decision": "block"', out, f"{label}: out={out}")
                self.assertIn(self._DORMANT_SLUG, out, f"{label}: 検査対象が bind 先でない")
                self.assertNotIn(self._ACTIVE_SLUG, out, f"{label}: hint が検査対象を動かしている")
                self.assertNotIn("evil-traversal", out)


if __name__ == "__main__":
    unittest.main()
