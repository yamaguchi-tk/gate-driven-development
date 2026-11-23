"""compact 自動復帰をやめた後の、compaction の前後の hook の契約テスト。

compaction の hook（PreCompact・SessionStart(compact)）は、main の compaction か subagent の
compaction かを入力から見分けられない（Claude Code 2.1.280。agent_id が無く、subagent の
compaction でも payload の session_id は main のもの）。そこで、compaction の前後で「再開せよ」
「再開するな」のどちらも注入しない。

- SessionStart は、payload の source が compact なら何も出さない。active な steering があっても、
  `[gdd:reboot]`（do not auto-resume）・`[gdd:paused]`（do not resume）・自動復帰の文を出さない。
  自律実行の途中の main に「再開するな」が入ると、作業が止まる。前の turn の失敗の記録は消費せず、
  次の SessionStart に回す
- source が読めない（payload が無い・壊れている・python3 が無い）ときは、今までどおり通常の流れで
  案内を出す（startup と区別できないため。compaction でこれに当たると、通常の案内が入る）
- PreCompact は state.md に書かない。要約器に渡す文（systemMessage。exit 0 の stdout は要約器への
  指示になる）は、役割を問わない事実（state.md の場所・Resume From・Next Action）だけにする。
  subagent の要約にも入るので、「委譲せよ」「再開せよ」のような指示を入れない

どのテストも hook のスクリプトを実プロセスで起動する（入口から効果までの到達経路）。
"""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import time
import unittest
from pathlib import Path

from _locale_support import euc_jp_locale_env
from _paths import PLUGIN_ROOT as ROOT

SESSION_START = ROOT / "hooks" / "scripts" / "run-session-start-hook.sh"
PRE_COMPACT = ROOT / "hooks" / "scripts" / "run-pre-compact-hook.sh"

CURRENT = "11111111-2222-3333-4444-555555555555"
STEERING_NAME = "20260928-compact-silent"
COMPACT_PAYLOAD = json.dumps({"hook_event_name": "SessionStart", "source": "compact", "session_id": CURRENT})
STARTUP_PAYLOAD = json.dumps({"hook_event_name": "SessionStart", "source": "startup", "session_id": CURRENT})
PRE_COMPACT_PAYLOAD = json.dumps({"hook_event_name": "PreCompact", "trigger": "auto", "session_id": CURRENT})

# 自動復帰があった頃の印を残した state.md。読み手がいなくなっても、行が残っているだけで
# 何かが発火したり書き換わったりしないことを見る
STATE_WITH_OLD_MARKS = (
    "Resume From: gdd-test-driven-development\n"
    "Human Check Status: approved\n"
    "Route In Progress: none\n"
    "Next Action: gdd-implementation-gating\n"
    "Status: paused\n"
    f"CompactSessionId: {CURRENT}\n"
    "CompactTranscriptOffset: 0\n"
    "CompactSource: pre-compact\n"
    "AutoCycleCount: 0\n"
    f"Task ID: {STEERING_NAME}\n"
)
_LEAKED_ENV = (
    "GDD_STEERING_DIR", "GDD_HOOK_STATE_DIR", "GDD_MAX_AUTO_CYCLES",
    "CLAUDE_CODE_SESSION_ID", "GDD_WORKTREES_ROOT", "GDD_DISABLE",
)


class _Fixture(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="gdd-compact-silent-")
        self.addCleanup(self._tmp.cleanup)
        tmp = Path(os.path.realpath(self._tmp.name))
        self.home = tmp / "home"
        self.home.mkdir()
        self.repo = tmp / "repo"
        self.repo.mkdir()
        # commit しない（HEAD が無いので、既定ブランチ・branch 名の判定を通らずに session の判定に届く）
        subprocess.run(["git", "init", "-q"], cwd=self.repo, check=True)
        self.steering = self.repo / ".steering" / STEERING_NAME
        self.state = self.steering / "state.md"

    def _make_steering(self, local_session: str = CURRENT) -> None:
        self.steering.mkdir(parents=True)
        self.state.write_text(STATE_WITH_OLD_MARKS, encoding="utf-8")
        (self.repo / ".claude").mkdir()
        (self.repo / ".claude" / "gdd-dev.local.md").write_text(
            f"---\nactive: true\nsession_id: {local_session}\n---\n", encoding="utf-8"
        )

    def _env(self, path: str | None = None, extra: dict[str, str] | None = None) -> dict[str, str]:
        env = os.environ.copy()
        env["HOME"] = str(self.home)
        env["CLAUDE_PLUGIN_ROOT"] = str(ROOT)
        for leaked in _LEAKED_ENV:
            env.pop(leaked, None)
        env["CLAUDE_CODE_SESSION_ID"] = CURRENT
        if path is not None:
            env["PATH"] = path
        env.update(extra or {})
        return env

    def _run(
        self, script: Path, payload: str, path: str | None = None, extra: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess:
        result = subprocess.run(
            ["bash", str(script)], input=payload, capture_output=True, text=True,
            env=self._env(path, extra), cwd=str(self.repo), timeout=120,
        )
        # 例外で hook 全体が落ちない
        self.assertEqual(result.returncode, 0, result.stderr)
        return result

    def _additional(self, result: subprocess.CompletedProcess) -> str:
        lines = [line for line in result.stdout.splitlines() if line.strip()]
        self.assertEqual(len(lines), 1, lines)
        return json.loads(lines[0])["hookSpecificOutput"]["additionalContext"]

    def _write_failure_record(self) -> Path:
        record = self.home / ".claude" / ".gdd-hook-state" / "last-turn-failure.json"
        record.parent.mkdir(parents=True, exist_ok=True)
        record.write_text(json.dumps({
            "error": "api_error",
            "error_details": "detail",
            "session_id": "abc123ef",
            "timestamp": "2026-09-28T01:10:00Z",
            "project_root": str(self.repo),
        }), encoding="utf-8")
        return record

    def _bin_without_python(self) -> str:
        """python3 / python だけを外した PATH。hook が使うほかのコマンドはそのまま見える。"""
        bindir = Path(self._tmp.name) / "bin-no-python"
        bindir.mkdir()
        for directory in os.environ.get("PATH", "").split(os.pathsep):
            if not directory or not os.path.isdir(directory):
                continue
            for name in os.listdir(directory):
                if name.startswith("python") or (bindir / name).exists():
                    continue
                target = os.path.join(directory, name)
                if os.path.isfile(target) and os.access(target, os.X_OK):
                    (bindir / name).symlink_to(target)
        return str(bindir)


class SessionStartCompactIsSilentTests(_Fixture):
    def test_control_startup_injects_reboot_for_the_same_steering(self) -> None:
        """対照: 同じ fixture で startup なら通常の案内（[gdd:reboot]）が出る。"""
        self._make_steering()
        additional = self._additional(self._run(SESSION_START, STARTUP_PAYLOAD))
        self.assertIn("[gdd:reboot]", additional)

    def test_compact_with_active_steering_outputs_nothing(self) -> None:
        """block すべき入力（compact）で、再開・再開禁止のどちらの文も出ない。"""
        self._make_steering()
        result = self._run(SESSION_START, COMPACT_PAYLOAD)
        self.assertEqual(result.stdout.strip(), "")

    def test_compact_with_safe_resume_candidate_outputs_nothing(self) -> None:
        """startup なら [gdd:paused] になる別 session の steering でも、compact では何も出さない。"""
        self._make_steering(local_session="other-session")
        control = self._additional(self._run(SESSION_START, STARTUP_PAYLOAD))
        self.assertIn("[gdd:paused]", control)
        result = self._run(SESSION_START, COMPACT_PAYLOAD)
        self.assertEqual(result.stdout.strip(), "")

    def test_compact_without_steering_outputs_nothing(self) -> None:
        control = self._additional(self._run(SESSION_START, STARTUP_PAYLOAD))
        self.assertIn("gate-driven-development is available", control)
        result = self._run(SESSION_START, COMPACT_PAYLOAD)
        self.assertEqual(result.stdout.strip(), "")

    def test_compact_does_not_touch_state_or_lock(self) -> None:
        """古い印が残っていても、消費・加算・ロックの作成をしない。"""
        self._make_steering()
        before = self.state.read_bytes()
        self._run(SESSION_START, COMPACT_PAYLOAD)
        self.assertEqual(self.state.read_bytes(), before)
        self.assertFalse((self.steering / ".gdd_is_running").exists())

    def test_compact_keeps_last_failure_record_for_the_next_session_start(self) -> None:
        self._make_steering()
        record = self._write_failure_record()
        self._run(SESSION_START, COMPACT_PAYLOAD)
        self.assertTrue(record.exists(), "compact では前の turn の失敗の記録を消費しない")
        additional = self._additional(self._run(SESSION_START, STARTUP_PAYLOAD))
        self.assertIn("[gdd:last-turn-failed]", additional)
        self.assertFalse(record.exists())

    def test_unreadable_source_falls_back_to_the_normal_guidance(self) -> None:
        """判定できないとき: source が読めなければ startup と区別できないので、通常の案内を出す。"""
        self._make_steering()
        for name, payload in (("payload 無し", ""), ("壊れた JSON", "{not json"), ("source 無し", json.dumps({"session_id": CURRENT}))):
            with self.subTest(name):
                self.assertIn("[gdd:reboot]", self._additional(self._run(SESSION_START, payload)))

    def test_only_a_compact_source_string_is_silent(self) -> None:
        """compact 以外の source、source が文字列でない、compact が別の場所にあるだけの payload は、
        通常の案内を出す（文字列一致に崩す・resume / clear まで黙らせる変異を落とす）。"""
        self._make_steering()
        payloads = {
            "resume": json.dumps({"source": "resume", "session_id": CURRENT}),
            "clear": json.dumps({"source": "clear", "session_id": CURRENT}),
            "source が配列": json.dumps({"source": ["compact"], "session_id": CURRENT}),
            "payload が配列": json.dumps(["compact"]),
            "compact を含む壊れた JSON": '{"source": "compact", ',
            "cwd に compact": json.dumps({
                "source": "startup", "session_id": CURRENT,
                "cwd": "/w/x-compact-y", "transcript_path": "/w/compact.jsonl",
            }),
            "session_id が compact": json.dumps({"session_id": "compact"}),
            "大文字の Compact": json.dumps({"source": "Compact", "session_id": CURRENT}),
        }
        for name, payload in payloads.items():
            with self.subTest(name):
                self.assertIn("[gdd:reboot]", self._additional(self._run(SESSION_START, payload)))

    def test_compact_is_silent_in_a_non_utf8_locale(self) -> None:
        """payload は UTF-8 で届く。利用者のロケールが EUC-JP で、payload の cwd が非 ASCII でも、入口から
        沈黙する（kill-switch.sh がロケールを上書きし、python は `-X utf8` でも起動する）。"""
        locale_env = euc_jp_locale_env(self, Path(self._tmp.name))
        self._make_steering()
        payload = json.dumps({"source": "compact", "session_id": CURRENT, "cwd": "/w/日本語"}, ensure_ascii=False)
        result = subprocess.run(
            ["bash", str(SESSION_START)], input=payload.encode("utf-8"), capture_output=True,
            env=self._env(extra=locale_env), cwd=str(self.repo), timeout=120,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), b"")

    def test_stdin_left_open_does_not_hang(self) -> None:
        """stdin が閉じられない起動でも、hook の timeout（hooks.json の 5 秒）より前に通常の案内を出す。"""
        self._make_steering()
        proc = subprocess.Popen(
            ["bash", str(SESSION_START)], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, text=True, env=self._env(), cwd=str(self.repo),
        )
        started = time.monotonic()
        try:
            # stdin を閉じずに終わりを待つ（communicate は stdin を閉じてしまう）
            proc.wait(timeout=30)
            stdout, stderr = proc.communicate()
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.communicate()
            self.fail("stdin が開いたままだと SessionStart hook が終わらない")
        self.assertEqual(proc.returncode, 0, stderr)
        self.assertLess(time.monotonic() - started, 4.5)
        self.assertIn("[gdd:reboot]", stdout)

    def test_compact_without_python_falls_back_to_the_normal_guidance(self) -> None:
        """python3 が無いと source を読めない。hook は落ちず、startup と同じ通常の案内を出す。"""
        self._make_steering()
        path = self._bin_without_python()
        control = self._additional(self._run(SESSION_START, STARTUP_PAYLOAD, path=path))
        additional = self._additional(self._run(SESSION_START, COMPACT_PAYLOAD, path=path))
        self.assertEqual(additional, control)


class PreCompactHandsOnlyFactsTests(_Fixture):
    FORMS = (
        ("Resume From: {r}\nNext Action: {n}\n"),
        ("- Resume From: {r}\n- Next Action: {n}\n"),
        ("Resume From={r}\nNext Action={n}\n"),
        ("- Resume From={r}\n- Next Action={n}\n"),
    )

    def _state(self, body: str) -> None:
        self.steering.mkdir(parents=True, exist_ok=True)
        self.state.write_text(body, encoding="utf-8")

    def _message(self, result: subprocess.CompletedProcess) -> str:
        lines = [line for line in result.stdout.splitlines() if line.strip()]
        self.assertEqual(len(lines), 1, lines)
        return json.loads(lines[0])["systemMessage"]

    def test_reminder_carries_resume_from_and_next_action_in_every_line_form(self) -> None:
        for form in self.FORMS:
            with self.subTest(form=form):
                self._state("Human Check Status: approved\n" + form.format(r="gdd-test-driven-development", n="gdd-implementation-gating"))
                message = self._message(self._run(PRE_COMPACT, PRE_COMPACT_PAYLOAD))
                self.assertIn("gdd-test-driven-development", message)
                self.assertIn("gdd-implementation-gating", message)
                self.assertIn(str(self.state), message)

    def test_reminder_has_no_fixed_instruction_text(self) -> None:
        """subagent の要約にも入るので、hook が固定で足す文に委譲・再開の指示を入れない。
        state.md の値は skill 名でもそのまま渡す（値は事実で、どの skill を使うかの指示ではない）。"""
        self._state("Resume From: gdd-task-breakdown\nNext Action: gdd-task-breakdown\n")
        message = self._message(self._run(PRE_COMPACT, PRE_COMPACT_PAYLOAD))
        # 文は入力（場所と 2 つの値）だけで決まるので、全文で固定する（固定の文に指示を足すと落ちる）
        self.assertEqual(
            message,
            f"compaction 前の GDD の状態（{self.state}）: Resume From = gdd-task-breakdown、Next Action = gdd-task-breakdown。",
        )
        for instruction in ("gdd-subagent-driven-implementation", "/gdd-dev", "<gdd-phase>", "委譲", "再開"):
            self.assertNotIn(instruction, message)
        self._state("Resume From: gdd-subagent-driven-implementation\nNext Action: gdd-task-breakdown\n")
        self.assertIn("gdd-subagent-driven-implementation", self._message(self._run(PRE_COMPACT, PRE_COMPACT_PAYLOAD)))

    def test_pre_compact_does_not_write_state(self) -> None:
        for body in (STATE_WITH_OLD_MARKS, "Resume From: gdd-task-breakdown\nNext Action: gdd-task-breakdown\n"):
            with self.subTest(body=body.splitlines()[0]):
                self._state(body)
                before = self.state.read_bytes()
                self._run(PRE_COMPACT, PRE_COMPACT_PAYLOAD)
                self.assertEqual(self.state.read_bytes(), before)

    def test_no_routing_fields_means_no_output(self) -> None:
        self._state("Human Check Status: approved\n")
        self.assertEqual(self._run(PRE_COMPACT, PRE_COMPACT_PAYLOAD).stdout.strip(), "")

    def test_control_characters_do_not_break_the_json(self) -> None:
        self._state("Resume From: gdd-task\x07-breakdown\nNext Action: a\x1bb\n")
        message = self._message(self._run(PRE_COMPACT, PRE_COMPACT_PAYLOAD))
        self.assertIn("gdd-task-breakdown", message)
        self.assertNotIn("\x07", message)

    def test_without_python_outputs_nothing_and_does_not_fail(self) -> None:
        """steering の検出を飛ばして（GDD_STEERING_DIR を渡して）、文を組み立てる段まで python3 無しで届かせる。"""
        self._state(STATE_WITH_OLD_MARKS)
        # 非 ASCII と不正な UTF-8 のバイトを値に混ぜる（python3 が無くても hook が落ちない）
        self.state.write_bytes(self.state.read_bytes().replace(b"gdd-implementation-gating", b"gdd-\xe3\x81\x82\xff-gating"))
        result = self._run(
            PRE_COMPACT, PRE_COMPACT_PAYLOAD, path=self._bin_without_python(),
            extra={"GDD_STEERING_DIR": str(self.steering)},
        )
        self.assertEqual(result.stdout.strip(), "")

    def test_next_action_comes_from_the_canonical_tasklist(self) -> None:
        """build 中（3 つの承認が揃い tasklist.md がある）は、SessionStart・UserPromptSubmit と同じく
        tasklist.md の Next Action を先に読み、`|` 以降（evidence など）を落とす。"""
        self._state(
            "Resume From: gdd-subagent-driven-implementation\n"
            "Requirements Review Status: approved\nDesign Review Status: approved\nHuman Check Status: approved\n"
            "Next Action: gdd-task-breakdown | evidence: old\n"
        )
        (self.steering / "tasklist.md").write_text(
            "## Current Task\n### Task: T1\n- Next Action: gdd-test-driven-development | evidence: t1\n", encoding="utf-8"
        )
        message = self._message(self._run(PRE_COMPACT, PRE_COMPACT_PAYLOAD))
        self.assertIn("Next Action = gdd-test-driven-development。", message)
        self.assertNotIn("gdd-task-breakdown", message)
        self.assertNotIn("evidence", message)

    def test_state_next_action_is_used_before_the_tasklist_is_canonical(self) -> None:
        """承認が揃う前の tasklist.md（stale の可能性がある）は読まない。state.md の値の `|` 以降は落とす。"""
        self._state("Resume From: gdd-task-breakdown\nNext Action: gdd-task-breakdown | evidence: e\n")
        (self.steering / "tasklist.md").write_text("- Next Action: gdd-test-driven-development\n", encoding="utf-8")
        message = self._message(self._run(PRE_COMPACT, PRE_COMPACT_PAYLOAD))
        self.assertIn("Next Action = gdd-task-breakdown。", message)
        self.assertNotIn("evidence", message)

    def test_resume_from_drops_the_pipe_tail(self) -> None:
        """Resume From も Next Action と同じく `|` 以降（evidence など）を落とす（SessionStart と同じ）。"""
        self._state("Resume From: gdd-task-breakdown | evidence: e\nNext Action: gdd-design\n")
        message = self._message(self._run(PRE_COMPACT, PRE_COMPACT_PAYLOAD))
        self.assertIn("Resume From = gdd-task-breakdown、", message)
        self.assertNotIn("evidence", message)

    def test_steering_of_another_session_is_not_handed_to_the_summarizer(self) -> None:
        """別 session の steering の状態は要約器へ渡さない（UserPromptSubmit・plan-reread の
        gdd_session_continuity_ok と同じ）。同じ session なら渡す。"""
        self._make_steering(local_session="other-session")
        self.assertEqual(self._run(PRE_COMPACT, PRE_COMPACT_PAYLOAD).stdout.strip(), "")

    def test_steering_of_the_same_session_is_handed_to_the_summarizer(self) -> None:
        self._make_steering()
        self.assertIn("gdd-test-driven-development", self._message(self._run(PRE_COMPACT, PRE_COMPACT_PAYLOAD)))

    def test_state_path_is_sanitized(self) -> None:
        """state.md の場所も外部入力として扱う。制御文字を除き、不正な UTF-8 でも文を出す。"""
        for name in ("ctl\x07name\x1b", "bad\udcffutf8"):
            with self.subTest(name=name.encode("unicode_escape").decode()):
                steering = self.repo / ".steering" / name
                try:
                    steering.mkdir(parents=True)
                except (OSError, UnicodeEncodeError):
                    self.skipTest("このファイルシステムは不正な UTF-8 のファイル名を作れない")
                (steering / "state.md").write_text("Resume From: gdd-task-breakdown\n", encoding="utf-8")
                result = subprocess.run(
                    ["bash", str(PRE_COMPACT)], input=PRE_COMPACT_PAYLOAD.encode(), capture_output=True,
                    env=self._env(extra={"GDD_STEERING_DIR": os.fsdecode(os.fsencode(str(steering)))}),
                    cwd=str(self.repo), timeout=120,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                message = json.loads(result.stdout.decode("utf-8"))["systemMessage"]
                self.assertIn("gdd-task-breakdown", message)
                self.assertNotIn("\x07", message)
                self.assertNotIn("\x1b", message)
                self.assertNotRegex(message, "[\ud800-\udfff]")
                cleaned = "".join(ch for ch in name if ch.isprintable() and not "\ud800" <= ch <= "\udfff")
                self.assertIn(f"/.steering/{cleaned}/state.md", message)

    def test_reminder_is_utf8_text_in_any_locale(self) -> None:
        """stdout は要約器への指示として読まれるので、非 ASCII を \\uXXXX にせず UTF-8 のまま出す。"""
        self._state("Resume From: gdd-task-breakdown\nNext Action: 設計の確認\n")
        for locale in ("C", "en_US.UTF-8"):
            with self.subTest(locale=locale):
                result = subprocess.run(
                    ["bash", str(PRE_COMPACT)], input=PRE_COMPACT_PAYLOAD.encode(), capture_output=True,
                    env=self._env(extra={"LC_ALL": locale, "GDD_STEERING_DIR": str(self.steering)}),
                    cwd=str(self.repo), timeout=120,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("compaction 前の GDD の状態".encode("utf-8"), result.stdout)
                self.assertIn("設計の確認".encode("utf-8"), result.stdout)
                json.loads(result.stdout.decode("utf-8"))

    def test_reminder_is_utf8_text_in_a_non_utf8_locale(self) -> None:
        """利用者のロケールが EUC-JP でも、入口から、日本語の固定の文・場所・値を UTF-8 のまま出す。"""
        locale_env = euc_jp_locale_env(self, Path(self._tmp.name))
        steering = self.repo / ".steering" / "20260928-日本語"
        steering.mkdir(parents=True)
        (steering / "state.md").write_text("Resume From: gdd-task-breakdown\nNext Action: 設計の確認\n", encoding="utf-8")
        result = subprocess.run(
            ["bash", str(PRE_COMPACT)], input=PRE_COMPACT_PAYLOAD.encode(), capture_output=True,
            env=self._env(extra={**locale_env, "GDD_STEERING_DIR": str(steering)}),
            cwd=str(self.repo), timeout=120,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        message = json.loads(result.stdout.decode("utf-8"))["systemMessage"]
        self.assertIn("compaction 前の GDD の状態", message)
        self.assertIn("Next Action = 設計の確認", message)
        self.assertIn("/.steering/20260928-日本語/state.md", message)


if __name__ == "__main__":
    unittest.main()
