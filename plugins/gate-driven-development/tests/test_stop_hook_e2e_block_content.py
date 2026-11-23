"""Stop hook の E2E テスト（実 hook を起動する）: hook が出す continuation block と、「次にすること」「次の計画」のブロックの中身。

`test_stop_hook_e2e.py` から分けた。確かめる本体は `hooks/scripts/gdd_stop_hook.py`・`hooks/scripts/lib/next_action_check.py`・`hooks/scripts/lib/next_plan_check.py`・`hooks/scripts/lib/post_merge_continuation.py`・`hooks/scripts/lib/constants.py`。
"""
from __future__ import annotations
# isort: skip_file
# ruff: noqa: F401,F811
import sys
from pathlib import Path as _P
sys.path.insert(0, str(_P(__file__).parent))
from _stop_hook_test_base import *  # noqa: F401,F403

class TestHookE2EContinuationBlockContent(unittest.TestCase):
    """When the hook DOES inject a continuation block, verify its content.

    The block is JSON with decision=block, reason=<compact continuation
    directive> (NOT the state body — the body is replayed verbatim at every
    continuation otherwise, spamming both the UI and the model context; the
    ~60-line body was replayed at every continuation of a long session),
    systemMessage that contains [GDD #N] phase task_progress (model: ...).
    Continue to terminal state. Optionally a phase transition warning suffix."""

    def test_continuation_block_format_basic(self):
        """OK reply continues the workflow → block JSON injected with systemMessage."""
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            _write_state_file(ws, {
                "active": "true",
                "session_id": "test-session",
                "iteration": "3",
                "detected_phase": "gdd-design-gating",
            }, body="次のステップを実行してください。")
            transcript = ws / "transcript.jsonl"
            _make_transcript_jsonl(
                transcript,
                assistant_text="<gdd-phase>gdd-design-gating</gdd-phase>\n設計案を提示しました。",
                user_text="OK",
            )
            code, out, _ = _run_hook(ws, transcript, session_id="test-session")
            self.assertEqual(code, 0)
            self.assertTrue(out.strip(), "Continuation block must be printed")
            payload = json.loads(out.strip())
            self.assertEqual(payload["decision"], "block")
            reason = payload["reason"]
            # Compact continuation contract: continue instruction + terminal
            # markers + pointer to the full contract on disk.
            self.assertIn("Continue the active `/gdd-dev` run", reason)
            self.assertIn('<gdd-stop reason="done">', reason)
            self.assertIn('<gdd-stop reason="human-check-waiting">', reason)
            self.assertIn(".claude/gdd-dev.local.md", reason)
            sys_msg = payload["systemMessage"]
            # Iteration is incremented from 3 → 4
            self.assertIn("[GDD #4]", sys_msg)
            self.assertIn("Continue to terminal state", sys_msg)

    def test_continuation_block_reason_is_compact_not_body_replay(self):
        """The state body must NOT be replayed verbatim as the block reason.

        The body carries the one-time bootstrap contract (~60 lines written by
        setup-gdd-loop.sh). Replaying it on every Stop-hook continuation spams
        the user-visible transcript and the model context with identical text.
        The reason must stay compact and reference the body instead."""
        boilerplate_marker = "Operate from canonical workflow state"
        long_body = (
            "Continue the active `/gdd-dev` run.\n\n"
            "User intent: 何かのタスク\n\n"
            f"{boilerplate_marker}, not from the last status summary.\n"
            + "filler line\n" * 50
        )
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            _write_state_file(ws, {
                "active": "true",
                "session_id": "test-session",
                "iteration": "1",
            }, body=long_body)
            transcript = ws / "transcript.jsonl"
            _make_transcript_jsonl(
                transcript,
                assistant_text="<gdd-phase>gdd-design-gating</gdd-phase>\n作業中。",
                user_text="OK",
            )
            code, out, _ = _run_hook(ws, transcript, session_id="test-session")
            self.assertEqual(code, 0)
            payload = json.loads(out.strip())
            self.assertEqual(payload["decision"], "block")
            reason = payload["reason"]
            self.assertNotIn(boilerplate_marker, reason)
            self.assertNotIn("filler line", reason)
            self.assertLess(
                len(reason), 800,
                "continuation reason must stay compact (pointer, not replay)",
            )

    def test_continuation_block_requests_brief_hitl_recheck(self):
        """Continuation must briefly re-evaluate whether HITL is required."""
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            _write_state_file(ws, {
                "active": "true",
                "session_id": "test-session",
                "iteration": "1",
                "detected_phase": "gdd-implementation-gating",
            }, body="次のステップを実行してください。")
            transcript = ws / "transcript.jsonl"
            _make_transcript_jsonl(
                transcript,
                assistant_text="<gdd-phase>gdd-implementation-gating</gdd-phase>\nレビュー差し戻しを確認しました。",
                user_text="OK",
            )

            code, out, _ = _run_hook(ws, transcript, session_id="test-session")

            self.assertEqual(code, 0)
            payload = json.loads(out.strip())
            sys_msg = payload["systemMessage"]
            self.assertIn("HITL recheck", sys_msg)
            self.assertIn("human-check-waiting", sys_msg)
            self.assertIn("AC semantics", sys_msg)
            self.assertIn("scope", sys_msg)
            self.assertIn("security boundary", sys_msg)
            self.assertIn("approval boundary", sys_msg)
            self.assertIn("autonomy ceiling", sys_msg)

    def test_continuation_block_includes_task_progress(self):
        """Active tasklist → systemMessage includes 'tasks: X/Y done' progress."""
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
                ### Task: T-2 | AC-02 | doing now

                ## Pending Tasks
                - T3 | AC-03 | next

                ## Completed Tasks
                - T1 | AC-01 | done

                ## Status
                Next Action=gdd-test-driven-development
            """)
            _write_steering(ws, "20260501-task", tasklist)
            transcript = ws / "transcript.jsonl"
            _make_transcript_jsonl(
                transcript,
                assistant_text="<gdd-phase>gdd-test-driven-development</gdd-phase>\n作業中。",
                user_text="続けて",
            )
            code, out, _ = _run_hook(ws, transcript, session_id="test-session")
            self.assertEqual(code, 0)
            payload = json.loads(out.strip())
            sys_msg = payload["systemMessage"]
            self.assertIn("tasks: 1/3 done", sys_msg)
            self.assertIn("current: T-2", sys_msg)

    def test_phase_transition_warning_when_handoff_missing(self):
        """Phase changed without Context Handoff → warning in systemMessage."""
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            _write_state_file(ws, {
                "active": "true",
                "session_id": "test-session",
                "iteration": "1",
                "detected_phase": "gdd-design-gating",
            })
            transcript = ws / "transcript.jsonl"
            # Last assistant text marks phase transition WITHOUT a handoff block
            _make_transcript_jsonl(
                transcript,
                assistant_text="<gdd-phase>gdd-task-breakdown</gdd-phase>\nタスクに分解します。",
                user_text="OK",
            )
            code, out, _ = _run_hook(ws, transcript, session_id="test-session")
            self.assertEqual(code, 0)
            payload = json.loads(out.strip())
            sys_msg = payload["systemMessage"]
            self.assertIn("[context-budget]", sys_msg)
            self.assertIn("gdd-design-gating -> gdd-task-breakdown", sys_msg)

    def test_stale_phase_oscillation_suppressed_when_disk_resume_from_unchanged(self):
        """E-6: detected_phase の heuristic 揺れが、disk 上の Resume From
        （canonical SSOT）が変化していない間は handoff_missing_warning を
        再発火させないことを確認する。"""
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            tasklist_content = (
                "# Tasklist\n\n"
                "## Current Task\n- なし\n\n"
                "## Pending Tasks\n- なし\n\n"
                "## Completed Tasks\n- なし\n"
            )
            state_content = (
                "# State\n"
                "- Resume From: gdd-task-breakdown\n"
                "- Next Action: gdd-task-breakdown\n"
            )
            _write_steering(
                ws,
                "20260701-e6-oscillation",
                tasklist_content,
                state_content=state_content,
            )

            # 1st hook run: baseline を確立する
            # （detected_phase を gdd-task-breakdown へ遷移させる。disk Resume
            # From と一致するので baseline 更新は正当な遷移として扱われる）。
            _write_state_file(ws, {
                "active": "true",
                "session_id": "test-session",
                "iteration": "1",
                "detected_phase": "gdd-design-gating",
            })
            transcript = ws / "transcript.jsonl"
            _make_transcript_jsonl(
                transcript,
                assistant_text=(
                    "<gdd-phase>gdd-task-breakdown</gdd-phase>\n"
                    "タスクに分解します。"
                ),
                user_text="OK",
            )
            code, _out, _err = _run_hook(ws, transcript, session_id="test-session")
            self.assertEqual(code, 0)

            # 2nd hook run: heuristic のテキスト一致で detected_phase が
            # gdd-design-gating に揺れ戻る（<gdd-phase> マーカーなし、本文中に
            # 候補文字列が偶然含まれるケース）。disk 上の Resume From は
            # gdd-task-breakdown のまま変化していない。
            _make_transcript_jsonl(
                transcript,
                assistant_text="gdd-design-gating の内容を再確認しています。",
                user_text="/gdd-dev 続けて",
            )
            code, out, _err = _run_hook(ws, transcript, session_id="test-session")
            self.assertEqual(code, 0)
            payload = json.loads(out.strip())
            sys_msg = payload.get("systemMessage", "")
            self.assertNotIn("[context-budget]", sys_msg)


class TestContinuationDoneGuardSync(unittest.TestCase):
    """AC-E9-2: continuation メッセージが要求する見出しと done guard が
    検査する見出しが同一定数 (NEXT_ACTION_HEADING) 由来であることを
    閉ループで検証する。文字列複製ドリフト（バグ3の根本原因）の再発防止。"""

    def test_next_action_heading_constant_passes_done_guard(self):
        from lib.next_action_check import NEXT_ACTION_HEADING, has_next_action_block
        self.assertTrue(has_next_action_block(NEXT_ACTION_HEADING))

    def test_continuation_message_contains_next_action_heading(self):
        from lib.next_action_check import NEXT_ACTION_HEADING
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            _write_state_file(ws, {
                "active": "true",
                "session_id": "test-session",
                "iteration": "1",
                "detected_phase": "gdd-design-gating",
            }, body="次のステップを実行してください。")
            transcript = ws / "transcript.jsonl"
            _make_transcript_jsonl(
                transcript,
                assistant_text="<gdd-phase>gdd-design-gating</gdd-phase>\n設計案を提示しました。",
                user_text="OK",
            )
            code, out, _ = _run_hook(ws, transcript, session_id="test-session")
            self.assertEqual(code, 0)
            payload = json.loads(out.strip())
            self.assertEqual(payload["decision"], "block")
            self.assertIn(NEXT_ACTION_HEADING, payload["reason"])


class TestHookE2ENextActionBlock(unittest.TestCase):
    """OT-F10 D2: 停止許可前に '👤 次にすること:' ブロックを検査する。

    各 reason（human-check-waiting / clarification-needed / blocked / done）で、
    対応する人間向け文言が無いと block、有ると通過する。
    cancelled は免除（ユーザー明示中止のため案内不要）。
    """

    _NEXT_ACTION = "\n\n## 👤 次にすること\nOKで承認してください"

    def _setup(self, ws: Path, assistant_text: str) -> Path:
        _write_state_file(ws, {
            "active": "true",
            "session_id": "test-session",
            "iteration": "1",
        })
        transcript = ws / "transcript.jsonl"
        _make_transcript_jsonl(transcript, assistant_text=assistant_text)
        return transcript

    # ── human-check-waiting ───────────────────────────────────────────────

    def test_human_check_waiting_without_next_action_blocked(self):
        """human-check-waiting + 次にすること欠落 → block。"""
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            transcript = self._setup(
                ws,
                '## 確認\n判断ポイント: ...\n<gdd-stop reason="human-check-waiting">',
            )
            code, out, _ = _run_hook(ws, transcript, session_id="test-session")
            self.assertEqual(code, 0)
            payload = json.loads(out.strip())
            self.assertEqual(payload["decision"], "block")
            self.assertIn("👤 次にすること", payload["reason"])

    def test_human_check_waiting_with_next_action_passes(self):
        """human-check-waiting + 次にすること有り → pause（block なし）。"""
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            transcript = self._setup(
                ws,
                '## 確認\n判断ポイント: ...\n<gdd-stop reason="human-check-waiting">'
                + self._NEXT_ACTION,
            )
            state_file = ws / ".claude" / "gdd-dev.local.md"
            code, out, _ = _run_hook(ws, transcript, session_id="test-session")
            self.assertEqual(code, 0)
            self.assertNotIn('"decision": "block"', out)
            self.assertTrue(state_file.exists(), "pause は state.md を保持する")

    # ── blocked ───────────────────────────────────────────────────────────

    def test_blocked_without_next_action_blocked(self):
        """blocked + 次にすること欠落 → block。"""
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            transcript = self._setup(
                ws,
                '## 停止\n外部前提が不足しています。\n<gdd-stop reason="blocked">',
            )
            code, out, _ = _run_hook(ws, transcript, session_id="test-session")
            self.assertEqual(code, 0)
            payload = json.loads(out.strip())
            self.assertEqual(payload["decision"], "block")
            self.assertIn("👤 次にすること", payload["reason"])

    def test_blocked_with_next_action_passes(self):
        """blocked + 次にすること有り → stop 許可（state 削除）。"""
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            transcript = self._setup(
                ws,
                '## 停止\n外部前提が不足しています。\n<gdd-stop reason="blocked">'
                + self._NEXT_ACTION,
            )
            state_file = ws / ".claude" / "gdd-dev.local.md"
            code, out, _ = _run_hook(ws, transcript, session_id="test-session")
            self.assertEqual(code, 0)
            self.assertNotIn('"decision": "block"', out)
            self.assertFalse(state_file.exists(), "blocked は state.md を削除する")

    # ── done（後続なし、tasklist なし） ──────────────────────────────────

    def test_done_without_next_action_blocked(self):
        """done + 次にすること欠落 → block（done guard より先に検査）。"""
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            transcript = self._setup(ws, '<gdd-stop reason="done">')
            code, out, _ = _run_hook(ws, transcript, session_id="test-session")
            self.assertEqual(code, 0)
            payload = json.loads(out.strip())
            self.assertEqual(payload["decision"], "block")
            self.assertIn("👤 次にすること", payload["reason"])

    def test_done_with_next_action_passes(self):
        """done + 次にすること有り + tasklist なし → done 許可。"""
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            transcript = self._setup(
                ws,
                '<gdd-stop reason="done">' + self._NEXT_ACTION,
            )
            state_file = ws / ".claude" / "gdd-dev.local.md"
            code, out, _ = _run_hook(ws, transcript, session_id="test-session")
            self.assertEqual(code, 0)
            self.assertNotIn('"decision": "block"', out)
            self.assertFalse(state_file.exists(), "done 成功は state.md を削除する")

    # ── done（clean tasklist） ────────────────────────────────────────────

    def test_done_with_next_action_and_clean_tasklist_passes(self):
        """done + 次にすること有り + clean tasklist → done 許可（done guard も通過）。"""
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            _write_steering(ws, "20260601-task", _CLEAN_TASKLIST, _CLEAN_STATE)
            transcript = self._setup(
                ws,
                '<gdd-stop reason="done">' + self._NEXT_ACTION,
            )
            state_file = ws / ".claude" / "gdd-dev.local.md"
            code, out, _ = _run_hook(ws, transcript, session_id="test-session")
            self.assertEqual(code, 0)
            self.assertNotIn('"decision": "block"', out)
            self.assertFalse(state_file.exists())

    # ── clarification-needed ──────────────────────────────────────────────

    def test_clarification_needed_without_next_action_blocked(self):
        """clarification-needed + 次にすること欠落 → block。"""
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            transcript = self._setup(
                ws,
                '## 確認が必要です\n質問があります。\n<gdd-stop reason="clarification-needed">',
            )
            code, out, _ = _run_hook(ws, transcript, session_id="test-session")
            self.assertEqual(code, 0)
            payload = json.loads(out.strip())
            self.assertEqual(payload["decision"], "block")
            self.assertIn("👤 次にすること", payload["reason"])

    def test_clarification_needed_with_next_action_passes(self):
        """clarification-needed + 次にすること有り → pause（block なし）。"""
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            transcript = self._setup(
                ws,
                '## 確認が必要です\n質問があります。\n<gdd-stop reason="clarification-needed">'
                + self._NEXT_ACTION,
            )
            state_file = ws / ".claude" / "gdd-dev.local.md"
            code, out, _ = _run_hook(ws, transcript, session_id="test-session")
            self.assertEqual(code, 0)
            self.assertNotIn('"decision": "block"', out)
            self.assertTrue(state_file.exists(), "pause は state.md を保持する")

    # ── cancelled（免除） ─────────────────────────────────────────────────

    def test_cancelled_without_next_action_passes(self):
        """cancelled は 次にすること なしでも stop 許可（ユーザー明示中止のため免除）。"""
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            transcript = self._setup(ws, '<gdd-stop reason="cancelled">')
            state_file = ws / ".claude" / "gdd-dev.local.md"
            code, out, _ = _run_hook(ws, transcript, session_id="test-session")
            self.assertEqual(code, 0)
            self.assertNotIn('"decision": "block"', out)
            self.assertFalse(state_file.exists(), "cancelled は state.md を削除する")


class TestHookE2ENextPlanBlock(unittest.TestCase):
    """OT-F9 E2: done + 未完 stage 残のとき '### 次の計画' ブロックを検査する。

    requirements.md の `Planned Follow-up Stage Lane` に `- [ ]` 項目が残る場合、
    done 停止出力に '### 次の計画' 見出しが必要。
    `Registry: created` 主張時は実ファイルの存在も検査する。
    """

    _NEXT_ACTION = "\n\n## 👤 次にすること\n完了（追加対応なし）"
    _NEXT_PLAN = (
        "\n\n### 次の計画\n"
        "現在: Phase A 完了\n"
        "次: stage-b（Phase B の実装）\n"
        "「次に進んで」で開始できます。"
    )

    _REQUIREMENTS_WITH_STAGES = textwrap.dedent("""\
        # Requirements

        ## Planned Follow-up Stage Lane

        - [ ] stage-b: Phase B の実装
        - [ ] stage-c: Phase C の CI 自動化
    """)

    _REQUIREMENTS_ALL_DONE = textwrap.dedent("""\
        # Requirements

        ## Planned Follow-up Stage Lane

        - [x] stage-b: Phase B の実装
    """)

    _REQUIREMENTS_NO_STAGES = "# Requirements\n\n単一フェーズ作業。\n"

    _REQUIREMENTS_TABLE_LANE = textwrap.dedent("""\
        # Requirements

        ## Planned Follow-up Stage Lane

        | Pending Stage ID | Origin Steering | Next Planned Stage |
        |---|---|---|
        | S-2 | .steering/20260620-task | Phase B の実装 |
    """)

    _REQUIREMENTS_STAGE_AFTER_FENCED_HEADING = textwrap.dedent("""\
        # Requirements

        ## Planned Follow-up Stage Lane

        ```markdown
        ## 例
        ```

        - [ ] stage-b: Phase B の実装
    """)

    def _setup(
        self,
        ws: Path,
        requirements: str | None = None,
    ) -> Path:
        _write_state_file(ws, {
            "active": "true",
            "session_id": "test-session",
            "iteration": "1",
        })
        steering_dir = _write_steering(ws, "20260620-task", _CLEAN_TASKLIST, _CLEAN_STATE)
        # Follow-up Stage Lane の検査も **bind された steering の requirements.md** を読む。
        # bind が無いと（done guard と同様に）検査対象なしとして no-op になる。
        _write_binding(ws, "20260620-task")
        if requirements is not None:
            (steering_dir / "requirements.md").write_text(requirements, encoding="utf-8")
        transcript = ws / "transcript.jsonl"
        return transcript

    # ── 未完 stage あり ────────────────────────────────────────────────────

    def test_done_with_incomplete_stages_no_next_plan_blocked(self):
        """done + 未完 stage + 次の計画なし → block。"""
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            transcript = self._setup(ws, requirements=self._REQUIREMENTS_WITH_STAGES)
            _make_transcript_jsonl(
                transcript,
                assistant_text='<gdd-stop reason="done">' + self._NEXT_ACTION,
            )
            code, out, _ = _run_hook(ws, transcript, session_id="test-session")
            self.assertEqual(code, 0)
            payload = json.loads(out.strip())
            self.assertEqual(payload["decision"], "block")
            self.assertIn("次の計画", payload["reason"])

    def test_done_with_table_lane_no_next_plan_blocked(self):
        """テンプレートの書式（表）で書いた Lane の行も、未完の Stage として block する。"""
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            transcript = self._setup(ws, requirements=self._REQUIREMENTS_TABLE_LANE)
            _make_transcript_jsonl(
                transcript,
                assistant_text='<gdd-stop reason="done">' + self._NEXT_ACTION,
            )
            code, out, _ = _run_hook(ws, transcript, session_id="test-session")
            self.assertEqual(code, 0)
            payload = json.loads(out.strip())
            self.assertEqual(payload["decision"], "block")
            self.assertIn("次の計画", payload["reason"])

    def test_done_with_undecodable_requirements_no_next_plan_blocked(self):
        """requirements.md に UTF-8 として読めないバイトがあっても、Lane を読んで block する。"""
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            transcript = self._setup(ws, requirements="")
            req = ws / ".steering" / "20260620-task" / "requirements.md"
            req.write_bytes(self._REQUIREMENTS_WITH_STAGES.encode("utf-8") + b"\xff\n")
            _make_transcript_jsonl(
                transcript,
                assistant_text='<gdd-stop reason="done">' + self._NEXT_ACTION,
            )
            code, out, _ = _run_hook(ws, transcript, session_id="test-session")
            self.assertEqual(code, 0)
            payload = json.loads(out.strip())
            self.assertEqual(payload["decision"], "block")
            self.assertIn("次の計画", payload["reason"])

    def test_done_with_unreadable_requirements_no_next_plan_blocked(self):
        """requirements.md が読めない（自分を指す symlink で ELOOP）なら、未完として block する。"""
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            transcript = self._setup(ws)
            os.symlink("requirements.md", ws / ".steering" / "20260620-task" / "requirements.md")
            _make_transcript_jsonl(
                transcript,
                assistant_text='<gdd-stop reason="done">' + self._NEXT_ACTION,
            )
            code, out, _ = _run_hook(ws, transcript, session_id="test-session")
            self.assertEqual(code, 0)
            payload = json.loads(out.strip())
            self.assertEqual(payload["decision"], "block")
            self.assertIn("次の計画", payload["reason"])

    def test_done_with_stage_after_fenced_heading_no_next_plan_blocked(self):
        """Lane の中のフェンスに `## ` 行があっても、後ろの未完 stage で block する。"""
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            transcript = self._setup(ws, requirements=self._REQUIREMENTS_STAGE_AFTER_FENCED_HEADING)
            _make_transcript_jsonl(
                transcript,
                assistant_text='<gdd-stop reason="done">' + self._NEXT_ACTION,
            )
            code, out, _ = _run_hook(ws, transcript, session_id="test-session")
            self.assertEqual(code, 0)
            payload = json.loads(out.strip())
            self.assertEqual(payload["decision"], "block")
            self.assertIn("次の計画", payload["reason"])

    def test_done_with_incomplete_stages_with_next_plan_passes(self):
        """done + 未完 stage + 次の計画あり → done 許可。"""
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            transcript = self._setup(ws, requirements=self._REQUIREMENTS_WITH_STAGES)
            _make_transcript_jsonl(
                transcript,
                assistant_text='<gdd-stop reason="done">' + self._NEXT_ACTION + self._NEXT_PLAN,
            )
            state_file = ws / ".claude" / "gdd-dev.local.md"
            code, out, _ = _run_hook(ws, transcript, session_id="test-session")
            self.assertEqual(code, 0)
            self.assertNotIn('"decision": "block"', out)
            self.assertFalse(state_file.exists())

    # ── 全 stage 完了 ───────────────────────────────────────────────────────

    def test_done_with_all_stages_complete_passes(self):
        """done + 全 stage [x] → 次の計画不要。"""
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            transcript = self._setup(ws, requirements=self._REQUIREMENTS_ALL_DONE)
            _make_transcript_jsonl(
                transcript,
                assistant_text='<gdd-stop reason="done">' + self._NEXT_ACTION,
            )
            code, out, _ = _run_hook(ws, transcript, session_id="test-session")
            self.assertEqual(code, 0)
            self.assertNotIn('"decision": "block"', out)

    # ── Follow-up Stage Lane なし ──────────────────────────────────────────

    def test_done_with_no_stage_lane_passes(self):
        """done + Follow-up Stage Lane なし → 次の計画不要。"""
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            transcript = self._setup(ws, requirements=self._REQUIREMENTS_NO_STAGES)
            _make_transcript_jsonl(
                transcript,
                assistant_text='<gdd-stop reason="done">' + self._NEXT_ACTION,
            )
            code, out, _ = _run_hook(ws, transcript, session_id="test-session")
            self.assertEqual(code, 0)
            self.assertNotIn('"decision": "block"', out)

    # ── requirements.md なし ───────────────────────────────────────────────

    def test_done_with_no_requirements_passes(self):
        """done + requirements.md なし → stage チェックをスキップ（fail-open）。"""
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            transcript = self._setup(ws)
            _make_transcript_jsonl(
                transcript,
                assistant_text='<gdd-stop reason="done">' + self._NEXT_ACTION,
            )
            code, out, _ = _run_hook(ws, transcript, session_id="test-session")
            self.assertEqual(code, 0)
            self.assertNotIn('"decision": "block"', out)

    # ── Registry 虚偽防止 ──────────────────────────────────────────────────

    def test_done_registry_created_claimed_but_file_missing_blocked(self):
        """done + Registry: created 主張 + ファイルなし → block。"""
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            transcript = self._setup(ws, requirements=self._REQUIREMENTS_WITH_STAGES)
            _make_transcript_jsonl(
                transcript,
                assistant_text=(
                    '<gdd-stop reason="done">' + self._NEXT_ACTION + self._NEXT_PLAN
                    + "\nRegistry: created → `.claude/gdd-continuations/stage-b.json`"
                ),
            )
            code, out, _ = _run_hook(ws, transcript, session_id="test-session")
            self.assertEqual(code, 0)
            payload = json.loads(out.strip())
            self.assertEqual(payload["decision"], "block")
            self.assertIn("gdd-continuations", payload["reason"])

    def test_done_registry_created_and_file_exists_passes(self):
        """done + Registry: created 主張 + ファイルあり → done 許可。"""
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            transcript = self._setup(ws, requirements=self._REQUIREMENTS_WITH_STAGES)
            cont_dir = ws / ".claude" / "gdd-continuations"
            cont_dir.mkdir(parents=True, exist_ok=True)
            (cont_dir / "stage-b.json").write_text('{"id": "stage-b"}', encoding="utf-8")
            _make_transcript_jsonl(
                transcript,
                assistant_text=(
                    '<gdd-stop reason="done">' + self._NEXT_ACTION + self._NEXT_PLAN
                    + "\nRegistry: created → `.claude/gdd-continuations/stage-b.json`"
                ),
            )
            state_file = ws / ".claude" / "gdd-dev.local.md"
            code, out, _ = _run_hook(ws, transcript, session_id="test-session")
            self.assertEqual(code, 0)
            self.assertNotIn('"decision": "block"', out)
            self.assertFalse(state_file.exists())


class TestHookE2ENextPlanMerge(unittest.TestCase):
    """OT-F9 E3: 「マージした」 + post-merge verification 完了後、未完 stage 残なら '### 次の計画' を検査。"""

    _POST_MERGE_TEXT = "post-merge verification を実施しました。state/tasklist を re-read しました。"
    _NEXT_PLAN = (
        "\n\n### 次の計画\n"
        "現在: Phase A 完了\n"
        "次: stage-b（Phase B の実装）\n"
        "「次に進んで」で開始できます。"
    )
    _NEXT_ACTION = "\n\n## 👤 次にすること\n完了（追加対応なし）"

    _REQUIREMENTS_WITH_STAGES = textwrap.dedent("""\
        # Requirements

        ## Planned Follow-up Stage Lane

        - [ ] stage-b: Phase B の実装
    """)

    def _setup_with_continuation(
        self,
        ws: Path,
        requirements: str | None = None,
    ) -> tuple[Path, Path]:
        """Set up workspace with gdd-post-merge-continuation.json."""
        _write_state_file(ws, {
            "active": "true",
            "session_id": "test-session",
            "iteration": "1",
        })
        steering_dir = _write_steering(ws, "20260620-task", _CLEAN_TASKLIST, _CLEAN_STATE)
        # Follow-up Stage Lane の検査も **bind された steering の requirements.md** を読む。
        # bind が無いと（done guard と同様に）検査対象なしとして no-op になる。
        _write_binding(ws, "20260620-task")
        if requirements is not None:
            (steering_dir / "requirements.md").write_text(requirements, encoding="utf-8")
        # Create post-merge continuation file
        claude_dir = ws / ".claude"
        claude_dir.mkdir(parents=True, exist_ok=True)
        cont_file = claude_dir / "gdd-post-merge-continuation.json"
        cont_file.write_text(json.dumps({
            "session_id": "test-session",
            "tasklist_path": str(steering_dir / "tasklist.md"),
            "pr_url": "https://github.com/org/repo/pull/125",
            "status": "pending_manual_merge",
        }), encoding="utf-8")
        transcript = ws / "transcript.jsonl"
        return transcript, cont_file

    def test_merge_with_incomplete_stages_no_next_plan_blocked(self):
        """「マージした」 + post-merge done + 未完 stage + 次の計画なし → block。"""
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            transcript, _ = self._setup_with_continuation(
                ws, requirements=self._REQUIREMENTS_WITH_STAGES
            )
            _make_transcript_jsonl(
                transcript,
                user_text="マージした",
                assistant_text=(
                    self._POST_MERGE_TEXT
                    + '<gdd-stop reason="done">'
                    + self._NEXT_ACTION
                ),
            )
            code, out, _ = _run_hook(ws, transcript, session_id="test-session")
            self.assertEqual(code, 0)
            payload = json.loads(out.strip())
            self.assertEqual(payload["decision"], "block")
            self.assertIn("次の計画", payload["reason"])

    def test_merge_with_undecodable_requirements_no_next_plan_blocked(self):
        """requirements.md が UTF-8 として読めなくても、post-merge の停止を block し marker を残す。"""
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            transcript, cont_file = self._setup_with_continuation(ws, requirements="")
            req = ws / ".steering" / "20260620-task" / "requirements.md"
            req.write_bytes(self._REQUIREMENTS_WITH_STAGES.encode("utf-8") + b"\xff\n")
            _make_transcript_jsonl(
                transcript,
                user_text="マージした",
                assistant_text=(
                    self._POST_MERGE_TEXT
                    + '<gdd-stop reason="done">'
                    + self._NEXT_ACTION
                ),
            )
            code, out, _ = _run_hook(ws, transcript, session_id="test-session")
            self.assertEqual(code, 0)
            payload = json.loads(out.strip())
            self.assertEqual(payload["decision"], "block")
            self.assertIn("次の計画", payload["reason"])
            self.assertTrue(cont_file.exists())

    def test_merge_with_unreadable_requirements_no_next_plan_blocked(self):
        """requirements.md が読めないなら、post-merge の停止を block し marker を残す。"""
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            transcript, cont_file = self._setup_with_continuation(ws)
            os.symlink("requirements.md", ws / ".steering" / "20260620-task" / "requirements.md")
            _make_transcript_jsonl(
                transcript,
                user_text="マージした",
                assistant_text=(
                    self._POST_MERGE_TEXT
                    + '<gdd-stop reason="done">'
                    + self._NEXT_ACTION
                ),
            )
            code, out, _ = _run_hook(ws, transcript, session_id="test-session")
            self.assertEqual(code, 0)
            payload = json.loads(out.strip())
            self.assertEqual(payload["decision"], "block")
            self.assertIn("次の計画", payload["reason"])
            self.assertTrue(cont_file.exists())

    def test_merge_with_incomplete_stages_with_next_plan_passes(self):
        """「マージした」 + post-merge done + 未完 stage + 次の計画あり → stop 許可。"""
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            transcript, cont_file = self._setup_with_continuation(
                ws, requirements=self._REQUIREMENTS_WITH_STAGES
            )
            _make_transcript_jsonl(
                transcript,
                user_text="マージした",
                assistant_text=(
                    self._POST_MERGE_TEXT
                    + self._NEXT_PLAN
                    + '<gdd-stop reason="done">'
                    + self._NEXT_ACTION
                    + self._NEXT_PLAN
                ),
            )
            code, out, _ = _run_hook(ws, transcript, session_id="test-session")
            self.assertEqual(code, 0)
            self.assertNotIn('"decision": "block"', out)
            self.assertFalse(cont_file.exists(), "continuation ファイルは削除される")

    def test_merge_with_no_stages_passes(self):
        """「マージした」 + post-merge done + stage なし → 次の計画不要。"""
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            transcript, _ = self._setup_with_continuation(ws)
            _make_transcript_jsonl(
                transcript,
                user_text="マージした",
                assistant_text=(
                    self._POST_MERGE_TEXT
                    + '<gdd-stop reason="done">'
                    + self._NEXT_ACTION
                ),
            )
            code, out, _ = _run_hook(ws, transcript, session_id="test-session")
            self.assertEqual(code, 0)
            self.assertNotIn('"decision": "block"', out)


if __name__ == "__main__":
    unittest.main()
