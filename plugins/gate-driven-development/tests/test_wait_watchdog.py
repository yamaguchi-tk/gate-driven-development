"""Stop hook の期限 watchdog（lib/wait_watchdog.py）のテスト。

background で起動した reviewer・gate-runner の待ちに、期限 timer（`sleep N` の background
Bash）があるか（未武装）と、上限を超えていないか（期限切れ）を Stop で確かめる。
"""
from __future__ import annotations

import contextlib
import io
import sys
import time
from datetime import datetime, timezone
from pathlib import Path as _P

sys.path.insert(0, str(_P(__file__).parent))
from _stop_hook_test_base import *  # noqa: F401,F403
from lib.transcript import inflight_dispatch_ids, parse_transcript
from lib.wait_watchdog import (
    _TASK_STOP_UNACCEPTED_EXIT, LIMITS, guard, overdue_reason, state_clear_guard, state_clear_reason,
)

NOW = 1_800_000_000.0


def _iso(t: float) -> str:
    return datetime.fromtimestamp(t, tz=timezone.utc).isoformat().replace("+00:00", "Z")


def _dispatch(n: str, at: float, subagent_type: str = "gate-driven-development:gdd-planning-reviewer",
              *, background: bool = True) -> list[dict]:
    items = [{"type": "assistant", "timestamp": _iso(at), "message": {"content": [
        {"type": "tool_use", "id": f"toolu_d_{n}", "name": "Agent",
         "input": {"subagent_type": subagent_type, "run_in_background": background, "prompt": "..."}},
    ]}}]
    if background:
        items.append({"type": "user", "timestamp": _iso(at), "message": {"content": [
            {"type": "tool_result", "tool_use_id": f"toolu_d_{n}",
             "content": f"Async agent launched successfully.\nagentId: agent_{n} (internal ID)"}]}})
    else:
        items.append({"type": "user", "timestamp": _iso(at + 60), "message": {"content": [
            {"type": "tool_result", "tool_use_id": f"toolu_d_{n}", "content": "done"}]}})
    return items


def _timer(n: str, at: float, seconds: int, command: str | None = None, *, background: bool = True,
           rejected: bool = False) -> list[dict]:
    result = {"type": "tool_result", "tool_use_id": f"toolu_t_{n}",
              "content": f"Command running in background with ID: bash_{n}. Output is being written to: /tmp/x"}
    if rejected:
        result = {"type": "tool_result", "tool_use_id": f"toolu_t_{n}", "is_error": True,
                  "content": "Permission for this action was denied by the Claude Code auto mode classifier."}
    return [
        {"type": "assistant", "timestamp": _iso(at), "message": {"content": [
            {"type": "tool_use", "id": f"toolu_t_{n}", "name": "Bash",
             "input": {"command": command or f"sleep {seconds}", "run_in_background": background}},
        ]}},
        {"type": "user", "timestamp": _iso(at), "message": {"content": [result]}},
    ]


def _notification(task_id: str, tool_use_id: str, status: str = "completed") -> dict:
    text = (
        f"<task-notification>\n<task-id>{task_id}</task-id>\n<tool-use-id>{tool_use_id}</tool-use-id>\n"
        f"<status>{status}</status>\n<summary>done</summary>\n</task-notification>"
    )
    return {"type": "user", "message": {"content": [{"type": "text", "text": text}]}}


def _task_stop(task_id: str, *, error: str | None = None) -> list[dict]:
    result = {"type": "tool_result", "tool_use_id": f"toolu_stop_{task_id}",
              "content": error if error is not None
              else json.dumps({"message": "stopped", "task_id": task_id, "task_type": "local_agent"})}
    if error is not None:
        result["is_error"] = True
    return [
        {"type": "assistant", "message": {"content": [
            {"type": "tool_use", "id": f"toolu_stop_{task_id}", "name": "TaskStop", "input": {"task_id": task_id}}]}},
        {"type": "user", "message": {"content": [result]}},
    ]


class TestOverdueReason(unittest.TestCase):
    PLANNING = LIMITS["gdd-planning-reviewer"]

    def _reason(self, items: list[dict], last_output: str = "待っています", now: float = NOW) -> str | None:
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "t.jsonl"
            p.write_text("\n".join(json.dumps(i) for i in items) + "\n", encoding="utf-8")
            return overdue_reason(parse_transcript(p), last_output, now)

    def test_limits_table(self):
        self.assertEqual(LIMITS, {
            "gdd-planning-reviewer": 1800,
            "gdd-security-reviewer": 1800,
            "gdd-completion-reviewer": 1800,
            "gdd-implementation-reviewer": 1200,
            "gdd-formal-gate-runner": 3600,
        })

    def test_no_dispatch_is_silent(self):
        self.assertIsNone(self._reason([
            {"type": "assistant", "message": {"content": [{"type": "text", "text": "ok"}]}}]))

    def test_unarmed_background_reviewer_blocks(self):
        reason = self._reason(_dispatch("a", NOW - 100))
        self.assertIsNotNone(reason)
        self.assertIn("agent_a", reason)
        self.assertIn(f"sleep {self.PLANNING - 100 + 60}", reason)

    def test_task_stop_unaccepted_exit_is_stated_once_for_many_overdue(self):
        """期限切れの dispatch が複数あっても、TaskStop が待ちから外れない結果で返ったときの出口の案内は 1 回だけ出す。"""
        items = _dispatch("a", NOW - self.PLANNING - 10) + _dispatch("b", NOW - self.PLANNING - 20)
        reason = self._reason(items)
        self.assertIn("agent_a", reason)
        self.assertIn("agent_b", reason)
        self.assertEqual(reason.count(_TASK_STOP_UNACCEPTED_EXIT), 1, reason)

    def test_task_stop_unaccepted_exit_is_absent_without_overdue(self):
        """未武装だけのときは TaskStop を求めないので、TaskStop の、待ちから外れない結果の出口も案内しない。"""
        reason = self._reason(_dispatch("a", NOW - 100))
        self.assertNotIn(_TASK_STOP_UNACCEPTED_EXIT, reason)

    def test_timer_covering_deadline_arms(self):
        items = _dispatch("a", NOW - 100) + _timer("1", NOW - 90, self.PLANNING)
        self.assertIsNone(self._reason(items))

    def test_timer_too_short_or_too_long_does_not_arm(self):
        for name, seconds in {"short": 60, "far beyond deadline": self.PLANNING + 3600}.items():
            with self.subTest(case=name):
                items = _dispatch("a", NOW - 100) + _timer("1", NOW - 90, seconds)
                self.assertIsNotNone(self._reason(items))

    def test_timer_before_dispatch_does_not_arm(self):
        items = _timer("1", NOW - 110, self.PLANNING) + _dispatch("a", NOW - 100)
        self.assertIsNotNone(self._reason(items))

    def test_finished_timer_does_not_arm(self):
        items = _dispatch("a", NOW - 100) + _timer("1", NOW - 90, self.PLANNING) + [
            _notification("bash_1", "toolu_t_1", "killed")]
        self.assertIsNotNone(self._reason(items))

    def test_non_fixed_form_or_foreground_timer_does_not_arm(self):
        cases = {
            "chained": _timer("1", NOW - 90, 0, command=f"sleep {self.PLANNING} && echo done"),
            "unit suffix": _timer("1", NOW - 90, 0, command="sleep 30m"),
            "foreground": _timer("1", NOW - 90, self.PLANNING, background=False),
        }
        for name, timer in cases.items():
            with self.subTest(case=name):
                self.assertIsNotNone(self._reason(_dispatch("a", NOW - 100) + timer))

    def test_timer_before_a_later_dispatch_does_not_cover_it(self):
        """timer は、それより前に起動した dispatch の期限だけを覆う。"""
        items = (_dispatch("a", NOW - 100) + _timer("1", NOW - 90, self.PLANNING)
                 + _dispatch("b", NOW - 50, "gdd-implementation-reviewer"))
        reason = self._reason(items)
        self.assertIsNotNone(reason)
        self.assertIn("agent_b", reason)
        self.assertNotIn("agent_a", reason)

    def test_out_of_scope_dispatches_are_ignored(self):
        cases = {
            "other agent": _dispatch("a", NOW - 100, "general-purpose"),
            "foreground": _dispatch("a", NOW - 100, background=False),
            "completed": _dispatch("a", NOW - 100) + [_notification("agent_a", "toolu_d_a")],
            "failed": _dispatch("a", NOW - 100) + [_notification("agent_a", "toolu_d_a", "failed")],
            "task stopped": _dispatch("a", NOW - 4000) + _task_stop("agent_a"),
            "task stop no task found": _dispatch("a", NOW - 4000) + _task_stop(
                "agent_a", error="<tool_use_error>No task found with ID: agent_a</tool_use_error>"),
        }
        for name, items in cases.items():
            with self.subTest(case=name):
                self.assertIsNone(self._reason(items))

    def test_task_stop_with_another_error_still_watches_the_dispatch(self):
        """TaskStop が拒否・未知のエラーで返った dispatch は、まだ動いているかもしれないので期限を見続ける。"""
        items = _dispatch("a", NOW - 4000) + _task_stop("agent_a", error="<tool_use_error>Failed</tool_use_error>")
        self.assertIn("agent_a", self._reason(items) or "")

    def test_timer_that_did_not_start_does_not_arm(self):
        """拒否・失敗で起動しなかった timer（is_error・起動応答なし）は、武装とみなさない。"""
        items = _dispatch("a", NOW - 100) + _timer("1", NOW - 90, self.PLANNING, rejected=True)
        self.assertIsNotNone(self._reason(items))
        no_result = _dispatch("a", NOW - 100) + _timer("1", NOW - 90, self.PLANNING)[:1]
        self.assertIsNotNone(self._reason(no_result))

    def test_timer_finished_by_task_id_or_task_stop_does_not_arm(self):
        """timer の終わりは、通知の <tool-use-id> だけでなく <task-id>（shell の id）と、
        その id への TaskStop の結果（本文の JSON の task_id・shell_id がその id の成功・No task found・is not running）でも判定する。"""
        cases = {
            "task-id only": [{"type": "user", "message": {"content": [{"type": "text", "text": (
                "<task-notification>\n<task-id>bash_1</task-id>\n<status>completed</status>\n"
                "</task-notification>")}]}}],
            "task stop": _task_stop("bash_1"),
            "no task found": _task_stop("bash_1", error="<tool_use_error>No task found with ID: bash_1</tool_use_error>"),
            "not running": _task_stop("bash_1", error="<tool_use_error>Task bash_1 is not running</tool_use_error>"),
        }
        for name, tail in cases.items():
            with self.subTest(case=name):
                items = _dispatch("a", NOW - 100) + _timer("1", NOW - 90, self.PLANNING) + tail
                self.assertIsNotNone(self._reason(items))

    def test_timer_stopped_with_other_error_stays_armed(self):
        """timer への TaskStop が、動いていないと答えた文面でないエラーで返ったら、timer は武装のまま。"""
        items = (_dispatch("a", NOW - 100) + _timer("1", NOW - 90, self.PLANNING)
                 + _task_stop("bash_1", error="<tool_use_error>Failed</tool_use_error>"))
        self.assertIsNone(self._reason(items))

    def test_timer_command_is_ascii_and_bounded(self):
        """timer の形は ASCII の空白と、先頭が 0 でない 6 桁までの秒数だけ。桁の多い値や全角の
        数字でも例外にならず、未武装になる。"""
        commands = ["sleep " + "9" * 400, "sleep " + "9" * 5000, "sleep \uff11\uff18\uff16\uff10",
                    "sleep\u30001860", "sleep 01860"]
        for command in commands:
            with self.subTest(command=command[:20]):
                items = _dispatch("a", NOW - 100) + _timer("1", NOW - 90, 0, command=command)
                self.assertIsNotNone(self._reason(items))

    def test_background_flag_without_launch_ack_is_ignored(self):
        """起動応答（agentId）の無い dispatch は background と認めず、対象にしない。"""
        items = _dispatch("a", NOW - 4000)[:1]
        self.assertIsNone(self._reason(items))

    def test_expired_dispatch_blocks_with_task_stop(self):
        for elapsed in (self.PLANNING, self.PLANNING + 1):
            with self.subTest(elapsed=elapsed):
                items = _dispatch("a", NOW - elapsed) + _timer("1", NOW - elapsed + 10, self.PLANNING)
                reason = self._reason(items)
                self.assertIsNotNone(reason)
                self.assertIn("TaskStop", reason)
                self.assertIn("agent_a", reason)

    def test_gate_runner_has_its_own_limit(self):
        items = _dispatch("g", NOW - 3000, "gdd-formal-gate-runner") + _timer("1", NOW - 2990, 3600)
        self.assertIsNone(self._reason(items))
        items = _dispatch("g", NOW - 3600, "gdd-formal-gate-runner") + _timer("1", NOW - 3590, 3600)
        self.assertIn("TaskStop", self._reason(items))

    def test_type_with_surrounding_spaces_is_a_target(self):
        """subagent_type の前後の空白を除いてから上限を引く（deny と同じ正規化）。"""
        reason = self._reason(_dispatch("g", NOW - 100, " gate-driven-development:gdd-formal-gate-runner "))
        self.assertIsNotNone(reason)
        self.assertIn("sleep", reason)

    def test_unreadable_or_future_timestamp_is_expired(self):
        """起動時刻が読めない・未来の dispatch は、期限を測れないので期限切れとして止めさせる。"""
        cases = {"missing": None, "garbage": "yesterday", "future": _iso(NOW + 5000),
                 "out of range": "99999-01-01T00:00:00", "not str": 12345}
        for name, ts in cases.items():
            with self.subTest(case=name):
                items = _dispatch("a", NOW - 100) + _timer("1", NOW - 90, self.PLANNING)
                if ts is None:
                    items[0].pop("timestamp")
                else:
                    items[0]["timestamp"] = ts
                reason = self._reason(items)
                self.assertIsNotNone(reason)
                self.assertIn("TaskStop", reason)

    def test_stop_marker_handing_to_human_skips_watchdog(self):
        """人間に渡す停止には当てない。自走する pause（external-review-waiting・auth-waiting）と
        done には当てる。marker は本文だけから読む（tool result の marker では外れない）。
        background の dispatch の実行中に state を消す停止は、watchdog ではなく、ほかの停止の検査
        （見出しの要求・HITL lint・done guard）より先に押し返す（TestStopWhileWaiting）。"""
        items = _dispatch("a", NOW - 4000)
        exempt = ("human-check-waiting", "blocked", "cancelled", "clarification-needed",
                  "staging-verification-blocked")
        for marker in exempt:
            with self.subTest(marker=marker):
                self.assertIsNone(self._reason(items, f'<gdd-stop reason="{marker}">'))
        for marker in ("done", "external-review-waiting", "auth-waiting", "unknown-reason"):
            with self.subTest(marker=marker):
                self.assertIn("TaskStop", self._reason(items, f'<gdd-stop reason="{marker}">'))
        tool_marker = items + [{"type": "user", "message": {"content": [
            {"type": "tool_result", "tool_use_id": "toolu_x",
             "content": '要件の確認をお願いします <gdd-stop reason="human-check-waiting">'}]}}]
        reason = self._reason(tool_marker, "確認をお願いします")
        self.assertIsNotNone(reason)
        self.assertIn("TaskStop", reason)
        # 止めた後に停止するなら、受け取った marker を本文に書くよう案内する
        self.assertIn("<gdd-stop", reason)


def _sync_result_quoting_ack(n: str, at: float) -> list[dict]:
    """同期の dispatch。回答の途中に起動応答の文言を引用している（テストの fixture を読んだ reviewer など）。"""
    return [
        {"type": "assistant", "timestamp": _iso(at), "message": {"content": [
            {"type": "tool_use", "id": f"toolu_d_{n}", "name": "Agent",
             "input": {"subagent_type": "general-purpose", "prompt": "..."}}]}},
        {"type": "user", "timestamp": _iso(at + 60), "message": {"content": [
            {"type": "tool_result", "tool_use_id": f"toolu_d_{n}", "content": (
                "レビュー結果: fixture は `Async agent launched successfully.\nagentId: agent_q` を返す。問題なし")}]}},
    ]


class TestLaunchAckParsing(unittest.TestCase):
    """起動応答は tool result の本文の先頭にあるものだけを読む（引用を background と取り違えない）。"""

    def _tv(self, items: list[dict]):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        path = Path(tmp.name) / "t.jsonl"
        path.write_text("\n".join(json.dumps(i) for i in items) + "\n", encoding="utf-8")
        return parse_transcript(path, Path(tmp.name))

    def test_quoted_ack_in_a_sync_result_is_not_a_launch(self):
        tv = self._tv(_sync_result_quoting_ack("q", NOW - 60))
        self.assertNotIn("toolu_d_q", tv.dispatch_agent_ids)
        self.assertEqual(inflight_dispatch_ids(tv), set())
        self.assertIsNone(state_clear_reason(tv, "blocked"))

    def test_ack_at_the_start_is_a_launch(self):
        for name, content in (
            ("leading whitespace", "\n  Async agent launched successfully.\nagentId: agent_a (internal ID)"),
            ("list content", [{"type": "text", "text": "Async agent launched successfully.\nagentId: agent_a"}]),
        ):
            with self.subTest(form=name):
                items = _dispatch("a", NOW - 60, "general-purpose")
                items[1]["message"]["content"][0]["content"] = content
                tv = self._tv(items)
                self.assertEqual(tv.dispatch_agent_ids.get("toolu_d_a"), "agent_a")
                self.assertIsNotNone(state_clear_reason(tv, "blocked"))


class TestStopWhileWaiting(unittest.TestCase):
    """background の dispatch が動いている間は、loop state を消す停止を、ほかの停止の検査（見出しの要求・
    HITL lint・done guard）より先に押し返す（type を問わない）。"""

    def _reason(self, items: list[dict]) -> str | None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "t.jsonl"
            path.write_text("\n".join(json.dumps(i) for i in items) + "\n", encoding="utf-8")
            return state_clear_reason(parse_transcript(path, Path(tmp)), "blocked")

    def test_running_background_dispatch_holds_the_state(self):
        reason = self._reason(_dispatch("a", NOW - 60, "general-purpose"))
        self.assertIsNotNone(reason)
        self.assertIn("agent_a", reason)
        self.assertIn("reason=blocked", reason)
        self.assertIn("目印を書かずに", reason)
        self.assertIn("TaskStop", reason)
        # TaskStop が待ちから外れない結果で返ったときの出口（reason=blocked なので、この語は出口の文からだけ入る）
        self.assertIn("clarification-needed", reason)
        # 本文に目印が無いのに止まったなら、tool result の marker を拾っている
        self.assertIn("tool result", reason)

    def test_stop_passes_after_the_dispatch_ends(self):
        for name, tail in (("TaskStop", _task_stop("agent_a")),
                           ("通知", [_notification("agent_a", "toolu_d_a")])):
            with self.subTest(ended_by=name):
                self.assertIsNone(self._reason(_dispatch("a", NOW - 60, "general-purpose") + tail))

    def test_sync_dispatch_does_not_hold_the_stop(self):
        self.assertIsNone(self._reason(_dispatch("a", NOW - 60, "general-purpose", background=False)))

    def test_exception_is_logged_and_does_not_block(self):
        """判定が例外になったときは記録して通す（watchdog と同じ）。"""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state = _write_state_file(root, {"active": "true", "session_id": "s", "iteration": "1"})
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                state_clear_guard({}, None, {}, "body", state, root, None)("blocked")
            self.assertEqual(out.getvalue(), "")
            self.assertTrue(state.exists())
            log = (root / ".gdd" / "hook-errors.log").read_text(encoding="utf-8")
            self.assertIn('"source": "wait_watchdog"', log)


class TestStopWhileWaitingFromHook(unittest.TestCase):
    """入口（gdd_stop_hook.py）から: どの経路で決まった停止理由でも、dispatch の実行中は state を残す。"""

    def _run(self, ws: Path, items: list[dict], body: str, **kw) -> tuple[dict | None, str]:
        transcript = ws / "transcript.jsonl"
        head = [{"type": "user", "message": {"content": [{"type": "text", "text": "/gdd-dev"}]}}]
        tail = [{"type": "assistant", "message": {"content": [{"type": "text", "text": body}]}}]
        transcript.write_text("\n".join(json.dumps(i) for i in head + items + tail) + "\n", encoding="utf-8")
        code, out, err = _run_hook(ws, transcript, **kw)
        self.assertEqual(code, 0, err)
        return (json.loads(out) if out.strip().startswith("{") else None), out + err

    def _active(self, ws: Path, **extra: str) -> Path:
        return _write_state_file(ws, {"active": "true", "session_id": "test-session", "iteration": "1", **extra})

    def _assert_held(self, payload: dict | None, state: Path) -> None:
        self.assertIsNotNone(payload)
        self.assertEqual(payload["decision"], "block")
        self.assertIn("agent_a", payload["reason"])
        self.assertTrue(state.exists())

    def test_state_ending_marker_in_body_is_held(self):
        for marker in ("blocked", "cancelled", "staging-verification-blocked"):
            with self.subTest(marker=marker), tempfile.TemporaryDirectory() as tmp:
                ws = Path(tmp)
                state = self._active(ws)
                payload, _ = self._run(ws, _dispatch("a", time.time() - 60, "general-purpose"),
                                       f'止めます。<gdd-stop reason="{marker}">\n\n## 👤 次にすること\n- 待つ')
                self._assert_held(payload, state)

    def test_marker_from_tool_result_is_held(self):
        """本文に目印が無くても、最後の tool result（Read した文書など）の marker で止まる経路を押し返す。"""
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            state = self._active(ws)
            items = _dispatch("a", time.time() - 60, "general-purpose") + [
                {"type": "assistant", "message": {"content": [
                    {"type": "tool_use", "id": "toolu_r", "name": "Read", "input": {"file_path": "/x"}}]}},
                {"type": "user", "message": {"content": [
                    {"type": "tool_result", "tool_use_id": "toolu_r", "content": '例: <gdd-stop reason="cancelled">'}]}},
            ]
            payload, _ = self._run(ws, items, "完了通知を待ちます。\n\n## 👤 次にすること\n- 待つ")
            self._assert_held(payload, state)
            self.assertIn("tool result", payload["reason"])

    def test_polling_cap_escalation_is_held(self):
        """external-review-waiting がポーリング上限で blocked に倒される経路を押し返す。"""
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            state = self._active(ws)
            _write_steering(ws, "20260501-test", "# Tasklist\n\n## Current Task\n### Task: T-1 | AC-01 | active\n",
                            state_content="# State\n\nResume From: external-review-waiting\n"
                                          "- PR Review Follow-up Attempts: 12\n")
            payload, _ = self._run(ws, _dispatch("a", time.time() - 60, "general-purpose"),
                                   '待ちます。<gdd-stop reason="external-review-waiting">\n\n## 👤 次にすること\n- 待つ')
            self._assert_held(payload, state)
            self.assertIn("reason=blocked", payload["reason"])

    def test_done_is_held_before_the_seed_is_written(self):
        """done の前提を満たしていても、dispatch の実行中は state を消さず、post-merge の seed も書かない。"""
        with tempfile.TemporaryDirectory() as tmp:
            _wtA, ws = _make_two_worktree_fixture(Path(tmp))
            _bind(ws)
            state = self._active(ws)
            payload, _ = self._run(ws, _dispatch("a", time.time() - 60, "general-purpose"),
                                   "マージしました: https://github.com/o/r/pull/123\n\n## 👤 次にすること\n"
                                   'レビューを依頼してください。\n\n<gdd-stop reason="done">\n')
            self._assert_held(payload, state)
            self.assertFalse((ws / ".claude" / "gdd-post-merge-continuation.json").exists())

    def test_stop_passes_after_task_stop(self):
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            state = self._active(ws)
            payload, _ = self._run(ws, _dispatch("a", time.time() - 60, "general-purpose") + _task_stop("agent_a"),
                                   '止めます。<gdd-stop reason="blocked">\n\n## 👤 次にすること\n- 待つ')
            self.assertIsNone(payload)
            self.assertFalse(state.exists())

    def test_pushback_comes_before_the_next_action_check(self):
        """見出しの無い停止でも、最初の block は待ち方の押し返しになる（見出しの要求より先）。"""
        read_blocked = [
            {"type": "assistant", "message": {"content": [
                {"type": "tool_use", "id": "toolu_r", "name": "Read", "input": {"file_path": "/x"}}]}},
            {"type": "user", "message": {"content": [
                {"type": "tool_result", "tool_use_id": "toolu_r", "content": '例: <gdd-stop reason="blocked">'}]}},
        ]
        cases = {
            "本文の blocked": ([], '止めます。<gdd-stop reason="blocked">'),
            "tool result の blocked": (read_blocked, "完了通知を待ちます。"),
            "done（見出しなし）": ([], '完了しました。<gdd-stop reason="done">'),
        }
        for name, (tail, body) in cases.items():
            with self.subTest(case=name), tempfile.TemporaryDirectory() as tmp:
                ws = Path(tmp)
                state = self._active(ws)
                payload, _ = self._run(ws, _dispatch("a", time.time() - 60, "general-purpose") + tail, body)
                self._assert_held(payload, state)
                self.assertNotIn("次にすること", payload["reason"])

    def test_pushback_comes_before_the_done_guard(self):
        """見出しがあり tasklist の検証が通らない done でも、dispatch の実行中は done guard より先に押し返す。"""
        for running, expect_pushback in ((True, True), (False, False)):
            with self.subTest(running=running), tempfile.TemporaryDirectory() as tmp:
                _wtA, ws = _make_two_worktree_fixture(Path(tmp))
                _bind(ws)
                (ws / ".steering" / "20260822-target" / "tasklist.md").write_text(_UNFINISHED_TASKLIST, encoding="utf-8")
                state = self._active(ws)
                items = _dispatch("a", time.time() - 60, "general-purpose") if running else []
                payload, _ = self._run(ws, items, _DONE_OUTPUT)
                self.assertIsNotNone(payload)
                self.assertEqual("agent_a" in payload["reason"], expect_pushback, payload["reason"][:200])
                self.assertEqual("done 前提条件" in payload["reason"], not expect_pushback, payload["reason"][:200])
                self.assertTrue(state.exists())

    def test_escalated_reason_is_used_by_the_next_action_check(self):
        """ポーリング上限で昇格した停止は、見出しの要求の文面でも reason=blocked になる。"""
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            state = self._active(ws)
            _write_steering(ws, "20260501-test", "# Tasklist\n\n## Current Task\n### Task: T-1 | AC-01 | active\n",
                            state_content="# State\n\nResume From: external-review-waiting\n"
                                          "- PR Review Follow-up Attempts: 12\n")
            payload, _ = self._run(ws, [], '待ちます。<gdd-stop reason="external-review-waiting">')
            self.assertIsNotNone(payload)
            self.assertIn("reason=blocked", payload["reason"])
            self.assertIn("次にすること", payload["reason"])
            self.assertTrue(state.exists())

    def test_state_keeping_stops_are_not_held(self):
        """state を残す停止は、dispatch の実行中でも押し返さない。"""
        for marker in ("clarification-needed", "auth-waiting", "external-review-waiting"):
            with self.subTest(marker=marker), tempfile.TemporaryDirectory() as tmp:
                ws = Path(tmp)
                state = self._active(ws)
                payload, _ = self._run(ws, _dispatch("a", time.time() - 60, "general-purpose"),
                                       f'待ちます。<gdd-stop reason="{marker}">\n\n## 👤 次にすること\n- 待つ')
                self.assertIsNone(payload)
                self.assertTrue(state.exists())

    def test_sync_result_quoting_the_ack_does_not_hold_the_stop(self):
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            state = self._active(ws)
            payload, _ = self._run(ws, _sync_result_quoting_ack("q", time.time() - 120),
                                   '止めます。<gdd-stop reason="blocked">\n\n## 👤 次にすること\n- 待つ')
            self.assertIsNone(payload)
            self.assertFalse(state.exists())

    def test_skipped_pushback_falls_to_the_next_action_check(self):
        """連続 block の上限で押し返しを飛ばしても、見出しが無ければ見出しの要求で止める（state は残る）。"""
        now = time.time()
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            state = self._active(ws, consecutive_stop_hook_blocks="6",
                                 consecutive_stop_hook_blocks_at=str(int(now)))
            payload, _ = self._run(ws, _dispatch("a", now - 60, "general-purpose"),
                                   '止めます。<gdd-stop reason="blocked">', stop_hook_active=True)
            self.assertIsNotNone(payload)
            self.assertIn("次にすること", payload["reason"])
            self.assertTrue(state.exists())

    def test_ceiling_and_peer_let_the_stop_through(self):
        """連続 block の上限を超えた Stop と、直近の実会話ターンが peer の Stop は押し返さない（watchdog と同じ）。"""
        now = time.time()
        peer = [{"type": "user", "origin": {"kind": "peer"}, "message": {"content": [
            {"type": "text", "text": "Another Claude session sent a message:\nhi"}]}}]
        cases = {
            "ceiling": ({"consecutive_stop_hook_blocks": "6", "consecutive_stop_hook_blocks_at": str(int(now))},
                        [], {"stop_hook_active": True}),
            "peer": ({}, peer, {}),
        }
        for name, (extra, tail, kw) in cases.items():
            with self.subTest(case=name), tempfile.TemporaryDirectory() as tmp:
                ws = Path(tmp)
                state = self._active(ws, **extra)
                payload, _ = self._run(ws, _dispatch("a", now - 60, "general-purpose") + tail,
                                       '止めます。<gdd-stop reason="blocked">\n\n## 👤 次にすること\n- 待つ', **kw)
                self.assertIsNone(payload)
                self.assertFalse(state.exists())


class TestGuardFailOpen(unittest.TestCase):
    def test_exception_is_logged_and_does_not_block(self):
        """判定が例外になったときは記録して何もしない（hook を落とさず、block もしない）。"""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state = _write_state_file(root, {"active": "true", "session_id": "s", "iteration": "1"})
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                guard({}, None, "", {}, "body", state, root, None)  # tv が None なので判定は例外になる
            self.assertEqual(out.getvalue(), "")
            log = (root / ".gdd" / "hook-errors.log").read_text(encoding="utf-8")
            self.assertIn('"source": "wait_watchdog"', log)


class TestWatchdogFromHook(unittest.TestCase):
    """入口（gdd_stop_hook.py）から: block、記録、連続 block の上限。"""

    def _active(self, ws: Path) -> None:
        _write_state_file(ws, {"active": "true", "session_id": "test-session", "iteration": "1"})

    def _write(self, ws: Path, items: list[dict]) -> Path:
        transcript = ws / "transcript.jsonl"
        head = [{"type": "user", "message": {"content": [{"type": "text", "text": "/gdd-dev"}]}}]
        tail = [{"type": "assistant", "message": {"content": [{"type": "text", "text": "reviewer を待ちます"}]}}]
        transcript.write_text("\n".join(json.dumps(i) for i in head + items + tail) + "\n", encoding="utf-8")
        return transcript

    def test_unarmed_wait_blocks_instead_of_silent_exit(self):
        now = time.time()
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            self._active(ws)
            transcript = self._write(ws, _dispatch("a", now - 60))
            code, out, err = _run_hook(ws, transcript)
            self.assertEqual(code, 0, err)
            payload = json.loads(out)
            self.assertEqual(payload["decision"], "block")
            self.assertIn("sleep", payload["reason"])
            self.assertIn("agent_a", payload["reason"])

    def test_armed_wait_exits_silently(self):
        now = time.time()
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            self._active(ws)
            transcript = self._write(ws, _dispatch("a", now - 60) + _timer("1", now - 50, 1800))
            code, out, err = _run_hook(ws, transcript)
            self.assertEqual(code, 0, err)
            self.assertEqual(out, "")

    def test_expired_wait_blocks_with_task_stop(self):
        now = time.time()
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            self._active(ws)
            items = _dispatch("a", now - 1900) + _timer("1", now - 1890, 1800) + [
                _notification("bash_1", "toolu_t_1")]
            transcript = self._write(ws, items)
            code, out, err = _run_hook(ws, transcript)
            self.assertEqual(code, 0, err)
            payload = json.loads(out)
            self.assertEqual(payload["decision"], "block")
            self.assertIn("TaskStop", payload["reason"])

    def test_blocked_stop_while_waiting_keeps_the_loop_state(self):
        """待っている間の blocked は block し、.claude/gdd-dev.local.md を消さない。"""
        now = time.time()
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            self._active(ws)
            items = _dispatch("a", now - 60, "gate-driven-development:gdd-formal-gate-runner") + _timer(
                "1", now - 50, 3660)
            transcript = ws / "transcript.jsonl"
            head = [{"type": "user", "message": {"content": [{"type": "text", "text": "/gdd-dev"}]}}]
            tail = [{"type": "assistant", "message": {"content": [{"type": "text", "text": (
                '完了通知を待ちます。<gdd-stop reason="blocked">\n\n## 👤 次にすること\n- 待つ')}]}}]
            transcript.write_text("\n".join(json.dumps(i) for i in head + items + tail) + "\n", encoding="utf-8")
            code, out, err = _run_hook(ws, transcript)
            self.assertEqual(code, 0, err)
            payload = json.loads(out)
            self.assertEqual(payload["decision"], "block")
            self.assertIn("目印を書かずに", payload["reason"])
            self.assertTrue((ws / ".claude" / "gdd-dev.local.md").exists())

    def test_consecutive_blocks_stop_at_ceiling(self):
        """block のたびにカウンタを state に保存し、上限（6）を超えた Stop では停止を通す。"""
        now = time.time()
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            self._active(ws)
            transcript = self._write(ws, _dispatch("a", now - 60))
            outs = []
            for _ in range(7):
                code, out, err = _run_hook(ws, transcript, stop_hook_active=True)
                self.assertEqual(code, 0, err)
                outs.append(out)
            self.assertTrue(all(json.loads(o)["decision"] == "block" for o in outs[:6]), outs)
            self.assertEqual(outs[6], "")


    def test_ceiling_hands_over_to_done_guard(self):
        """連続 block の上限を超えた Stop では、watchdog は停止を通さず後段（done guard）に任せる。
        watchdog は state を書き換えない。"""
        now = time.time()
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            _write_state_file(ws, {"active": "true", "session_id": "test-session", "iteration": "1",
                                   "consecutive_stop_hook_blocks": "6",
                                   "consecutive_stop_hook_blocks_at": str(int(now))})
            transcript = ws / "transcript.jsonl"
            items = ([{"type": "user", "message": {"content": [{"type": "text", "text": "/gdd-dev"}]}}]
                     + _dispatch("a", now - 60)
                     + [{"type": "assistant", "message": {"content": [
                         {"type": "text", "text": '完了しました。 <gdd-stop reason="done">'}]}}])
            transcript.write_text("\n".join(json.dumps(i) for i in items) + "\n", encoding="utf-8")
            code, out, err = _run_hook(ws, transcript, stop_hook_active=True)
            self.assertEqual(code, 0, err)
            self.assertNotIn("GDD wait watchdog", out)
            self.assertIn("done", out + err)

    def test_peer_turn_is_not_blocked(self):
        """直近の実会話ターンが peer なら、watchdog は block しない。"""
        now = time.time()
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            self._active(ws)
            transcript = ws / "transcript.jsonl"
            items = ([{"type": "user", "message": {"content": [{"type": "text", "text": "/gdd-dev"}]}}]
                     + _dispatch("a", now - 4000)
                     + [{"type": "user", "origin": {"kind": "peer"}, "message": {"content": [
                         {"type": "text", "text": "Another Claude session sent a message:\nhi"}]}},
                        {"type": "assistant", "message": {"content": [{"type": "text", "text": "ok"}]}}])
            transcript.write_text("\n".join(json.dumps(i) for i in items) + "\n", encoding="utf-8")
            code, out, err = _run_hook(ws, transcript)
            self.assertEqual(code, 0, err)
            self.assertNotIn("GDD wait watchdog", out)


if __name__ == "__main__":
    unittest.main()
