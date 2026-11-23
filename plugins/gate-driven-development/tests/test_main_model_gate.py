"""main が Sonnet・Haiku のときに GDD の入口（`/gdd-dev`・`/gdd-resume` の Skill、setup-gdd-loop.sh の実行
、手動の手順で run を始める `.claude/gdd-dev.local.md` への書き込みの 3 つ）を止める gate のテスト。

入口（hooks.json に登録した run-main-model-gate-hook.sh）から、transcript の fixture を
読ませて効果まで通す。
"""
from __future__ import annotations

import json
import subprocess
import tempfile
import time
import unittest
from pathlib import Path

from _paths import PLUGIN_ROOT

HOOK = PLUGIN_ROOT / "hooks" / "scripts" / "run-main-model-gate-hook.sh"
SETUP = PLUGIN_ROOT / "scripts" / "setup-gdd-loop.sh"


def assistant(model: str, sidechain: bool = False) -> dict:
    return {"type": "assistant", "isSidechain": sidechain, "message": {"model": model, "content": []}}


def prompt(text: str = "/gdd-dev x") -> dict:
    return {"type": "user", "message": {"content": text}}


def tool_call(model: str, tool_id: str) -> dict:
    # Claude Code は 1 つの返事の text と tool_use を、同じ message.id の別の行に書く
    return {"type": "assistant", "message": {"model": model, "id": "m-" + tool_id,
                                             "content": [{"type": "tool_use", "id": tool_id, "name": "Bash", "input": {}}]}}


def tool_result(tool_id: str) -> dict:
    return {"type": "user", "message": {"content": [{"type": "tool_result", "tool_use_id": tool_id, "content": "ok"}]}}


def model_attachment(model_id: str) -> dict:
    return {"type": "attachment", "attachment": {"type": "model", "identity": {"modelId": model_id}}}


def set_model(name: str) -> dict:
    return {
        "type": "user",
        "message": {
            "content": f"<local-command-stdout>Set model to \u001b[1m{name}\u001b[22m and saved as your default</local-command-stdout>"
        },
    }


class MainModelGateTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.home = self.tmp / "home"
        (self.home / ".claude").mkdir(parents=True)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _transcript(self, records: list, raw_lines: list[str] | None = None) -> Path:
        path = self.tmp / "t.jsonl"
        lines = [json.dumps(r, ensure_ascii=False) for r in records]
        if raw_lines:
            lines = raw_lines + lines
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return path

    def _run(self, event: str, payload: dict, extra_env: dict | None = None) -> subprocess.CompletedProcess[str]:
        env = {
            "HOME": str(self.home),
            "PATH": "/usr/bin:/bin:/opt/homebrew/bin:/usr/local/bin",
            "CLAUDE_PLUGIN_ROOT": str(PLUGIN_ROOT),
            "CLAUDE_CODE_ENTRYPOINT": "cli",
        }
        env.update(extra_env or {})
        payload = {"session_id": "s-1", "hook_event_name": event, **payload}
        return subprocess.run(
            ["bash", str(HOOK)],
            cwd=self.tmp,
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            env=env,
            check=False,
        )

    def _skill(self, transcript: Path, skill: str = "gate-driven-development:gdd-dev", **kw) -> subprocess.CompletedProcess[str]:
        payload = {"tool_name": "Skill", "tool_input": {"skill": skill}, "transcript_path": str(transcript)}
        for key in ("tool_use_id", "agent_id"):
            if key in kw:
                payload[key] = kw.pop(key)
        return self._run("PreToolUse", payload, **kw)

    def _expansion(self, transcript: Path | None, command: str = "gate-driven-development:gdd-dev") -> subprocess.CompletedProcess[str]:
        payload = {"expansion_type": "slash_command", "command_name": command, "prompt": f"/{command} x"}
        if transcript is not None:
            payload["transcript_path"] = str(transcript)
        return self._run("UserPromptExpansion", payload)

    def _setup(self, records: list, extra_env: dict | None = None, raw_lines: list[str] | None = None,
               command: list[str] | None = None) -> subprocess.CompletedProcess[str]:
        """setup-gdd-loop.sh を、Claude Code の Bash と同じく CLAUDE_CODE_SESSION_ID を渡して実行する。"""
        project = self.home / ".claude" / "projects" / "-r"
        project.mkdir(parents=True, exist_ok=True)
        lines = (raw_lines or []) + [json.dumps(r, ensure_ascii=False) for r in records]
        (project / "sid-1.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")
        repo = self.tmp / "repo"
        repo.mkdir(exist_ok=True)
        env = {"HOME": str(self.home), "PATH": "/usr/bin:/bin:/opt/homebrew/bin:/usr/local/bin",
               "CLAUDE_CODE_SESSION_ID": "sid-1"}
        env.update(extra_env or {})
        return subprocess.run(command or ["bash", str(SETUP), "x"], cwd=repo, capture_output=True, text=True,
                              env=env, check=False)

    def _assert_setup_stopped(self, proc: subprocess.CompletedProcess[str], hint: bool = False) -> None:
        out = proc.stderr + proc.stdout
        self.assertEqual(proc.returncode, 1, out)
        self.assertIn("/model opus", out)
        self.assertEqual("一言送って" in out, hint, out)
        self.assertFalse((self.tmp / "repo" / ".claude" / "gdd-dev.local.md").exists())

    def _assert_setup_ran(self, proc: subprocess.CompletedProcess[str]) -> None:
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertNotIn("/model opus", proc.stderr)
        self.assertTrue((self.tmp / "repo" / ".claude" / "gdd-dev.local.md").exists())

    def _log_path(self) -> Path:
        return self.home / ".claude" / ".gdd-hook-state" / "main-model-gate.log"

    def _log(self) -> str:
        path = self._log_path()
        return path.read_text(encoding="utf-8") if path.exists() else ""

    @staticmethod
    def _out(proc: subprocess.CompletedProcess[str]) -> dict:
        return json.loads(proc.stdout) if proc.stdout.strip() else {}

    def _assert_denied(self, proc: subprocess.CompletedProcess[str]) -> None:
        out = self._out(proc)
        self.assertEqual(out["hookSpecificOutput"]["permissionDecision"], "deny", proc.stdout)
        self.assertIn("/model opus", out["systemMessage"])

    def _assert_hint(self, proc: subprocess.CompletedProcess[str], shown: bool) -> None:
        # 今の返事の行が読めず、前の信号で判定したときだけ「一言送ってからやり直す」を出す
        self.assertEqual("一言送って" in self._out(proc)["systemMessage"], shown, proc.stdout)

    # --- 止める（block すべき入力が allow にならない）

    def test_skill_gdd_dev_is_denied_when_main_is_sonnet(self) -> None:
        self._assert_denied(self._skill(self._transcript([assistant("claude-opus-5-5"), assistant("claude-sonnet-5-5")])))

    def test_skill_gdd_resume_and_haiku_are_denied(self) -> None:
        t = self._transcript([assistant("claude-haiku-4-5")])
        self._assert_denied(self._skill(t, skill="gdd-resume"))
        self._assert_denied(self._skill(t, skill="gate-driven-development:gdd-dev"))

    # --- setup-gdd-loop.sh の実行（script の中で判定する）

    def test_setup_stops_when_the_reply_is_sonnet(self) -> None:
        self._assert_setup_stopped(self._setup([prompt(), tool_call("claude-sonnet-5-5", "tu1")]))
        self._assert_setup_stopped(self._setup([prompt(), tool_call("claude-haiku-4-5", "tu1")]))

    def test_setup_runs_when_switched_to_opus_on_screen(self) -> None:
        # 前の turn は Sonnet。画面で Opus に切り替えて打った /gdd-dev は、今の返事の Opus で判定する
        self._assert_setup_ran(self._setup([assistant("claude-sonnet-5-5"), prompt(), tool_call("claude-opus-5-5", "tu1")]))
        self.assertIn("\tsetup\tcurrent_turn\t", self._log())

    def test_setup_is_judged_in_any_shell_form(self) -> None:
        # Bash の文字列を解析しないので、どう包んで実行しても判定する
        for command in (["bash", "-x", str(SETUP)], ["/bin/bash", "-c", f'if true; then "{SETUP}" x; fi'],
                        ["/bin/bash", "-c", f'S="{SETUP}"; "$S" x 2>&1 | tail -50; exit "${{PIPESTATUS[0]}}"']):
            self._assert_setup_stopped(self._setup([prompt(), tool_call("claude-sonnet-5-5", "tu1")], command=command))

    def test_setup_without_the_current_reply_uses_the_last_signal_with_the_hint(self) -> None:
        self._assert_setup_stopped(self._setup([assistant("claude-sonnet-5-5"), prompt()]), hint=True)
        self.assertIn("\tsetup\tfallback\t", self._log())

    def test_setup_continuing_in_the_next_turn_is_judged_again(self) -> None:
        records = [prompt(), tool_call("claude-sonnet-5-5", "tu1")]
        self._assert_setup_stopped(self._setup(records))
        self._assert_setup_stopped(self._setup(records + [tool_result("tu1"), prompt("続けて"),
                                                          tool_call("claude-sonnet-5-5", "tu2")]))

    def test_setup_opt_out_is_read_only_from_the_settings_files(self) -> None:
        # 外し方は settings のファイルの env だけ。コマンドの前に付けた環境変数では外れない
        records = [prompt(), tool_call("claude-sonnet-5-5", "tu1")]
        self._assert_setup_stopped(self._setup(records, extra_env={"GDD_ALLOW_NON_OPUS_MAIN": "1"}))
        state = self.tmp / "repo" / ".claude" / "gdd-dev.local.md"
        for settings in (self.home / ".claude" / "settings.json",
                         self.tmp / "repo" / ".claude" / "settings.json",
                         self.tmp / "repo" / ".claude" / "settings.local.json"):
            settings.parent.mkdir(parents=True, exist_ok=True)
            settings.write_text(json.dumps({"env": {"GDD_ALLOW_NON_OPUS_MAIN": "1"}}), encoding="utf-8")
            self._assert_setup_ran(self._setup(records))
            settings.unlink()
            state.unlink()
        for value in ("0", "true", 1):
            settings = self.home / ".claude" / "settings.json"
            settings.write_text(json.dumps({"env": {"GDD_ALLOW_NON_OPUS_MAIN": value}}), encoding="utf-8")
            self._assert_setup_stopped(self._setup(records))
        settings.write_text("{broken", encoding="utf-8")  # 読めない settings は外し方にならない
        self._assert_setup_stopped(self._setup(records))

    def test_setup_kill_switch(self) -> None:
        (self.home / ".claude" / "gdd-hooks-disabled").write_text("", encoding="utf-8")
        self._assert_setup_ran(self._setup([prompt(), tool_call("claude-sonnet-5-5", "tu1")]))

    def test_setup_runtime_env_does_not_skip_the_judgment(self) -> None:
        # GDD_RUNTIME をコマンドの前に付けても、判定は process tree と session id で決める
        records = [prompt(), tool_call("claude-sonnet-5-5", "tu1")]
        self._assert_setup_stopped(self._setup(records, extra_env={"GDD_RUNTIME": "cursor"}))

    def test_setup_without_a_transcript_runs_with_a_notice(self) -> None:
        proc = self._setup([], extra_env={"CLAUDE_CODE_SESSION_ID": "other"})
        self._assert_setup_ran(proc)
        self.assertIn("判定できません", proc.stderr)

    def test_setup_log_failure_does_not_drop_the_stop(self) -> None:
        # ログを encode できない名前（孤立サロゲート）でも、ログを書けない場所でも止める
        self._assert_setup_stopped(self._setup([], raw_lines=[json.dumps(prompt()),
                                                              '{"type":"assistant","message":{"model":"claude-sonnet-\\ud800","content":[]}}']))
        self._assert_setup_stopped(self._setup([prompt(), tool_call("claude-sonnet-5-5", "tu1")],
                                               extra_env={"GDD_HOOK_STATE_DIR": "/dev/null/x"}))

    def test_large_transcript_is_judged_from_the_tail(self) -> None:
        filler = [json.dumps(tool_result("f")) .replace('"ok"', '"' + "x" * 1000 + '"')] * 6000
        start = time.monotonic()
        self._assert_setup_stopped(self._setup([prompt(), tool_call("claude-sonnet-5-5", "tu1")],
                                               raw_lines=[json.dumps(assistant("claude-opus-5-5"))] + filler))
        self.assertLess(time.monotonic() - start, 4)

    # --- 手動の手順で run を始める書き込み（Write・Edit・MultiEdit）

    def _write(self, transcript: Path, tool: str, tool_input: dict) -> subprocess.CompletedProcess[str]:
        return self._run("PreToolUse", {"tool_name": tool, "tool_input": tool_input, "cwd": str(self.tmp),
                                        "transcript_path": str(transcript)})

    def _state(self, text: str | None) -> Path:
        path = self.tmp / ".claude" / "gdd-dev.local.md"
        path.parent.mkdir(exist_ok=True)
        if text is None:
            path.unlink(missing_ok=True)
        else:
            path.write_text(text, encoding="utf-8")
        return path

    def test_creating_the_state_file_is_denied_when_sonnet(self) -> None:
        t = self._transcript([assistant("claude-sonnet-5-5")])
        path = self._state(None)
        for file_path in (str(path), ".claude/gdd-dev.local.md"):
            self._assert_denied(self._write(t, "Write", {"file_path": file_path, "content": "---\nactive: false\n---\n"}))
        self.assertIn("\tWrite\t", self._log())
        self.assertEqual(self._out(self._write(self._transcript([assistant("claude-opus-5-5")]), "Write",
                                               {"file_path": str(path), "content": "---\nactive: false\n---\n"})), {})

    def test_activating_the_state_file_is_denied_when_sonnet(self) -> None:
        t = self._transcript([assistant("claude-sonnet-5-5")])
        path = self._state("---\nactive: false\nsession_id:\n---\n")
        self._assert_denied(self._write(t, "Write", {"file_path": str(path), "content": "---\nactive: true\nsession_id: s\n---\n"}))
        self._assert_denied(self._write(t, "Edit", {"file_path": str(path), "old_string": "active: false",
                                                    "new_string": "active: true"}))
        self._assert_denied(self._write(t, "MultiEdit", {"file_path": str(path), "edits": [
            {"old_string": "session_id:", "new_string": "session_id: s"},
            {"old_string": "active: false", "new_string": "active:  true"}]}))

    def test_other_spellings_of_the_state_path_are_judged(self) -> None:
        # 解決すると .claude/gdd-dev.local.md になるパスは、綴りによらず判定する（大文字小文字は問わない。名前の違う file symlink は除く）
        t = self._transcript([assistant("claude-sonnet-5-5")])
        path = self._state(None)
        (self.tmp / ".claude" / "x").mkdir(exist_ok=True)
        (self.tmp / "alias").symlink_to(self.tmp / ".claude")
        content = {"content": "---\nactive: false\n---\n"}
        for file_path, cwd in ((str(self.tmp / ".claude" / "x" / ".." / "gdd-dev.local.md"), str(self.tmp)),
                               ("gdd-dev.local.md", str(path.parent)),
                               (str(self.tmp / ".claude" / "GDD-DEV.local.md"), str(self.tmp)),
                               (str(self.tmp / ".CLAUDE" / "gdd-dev.local.md"), str(self.tmp)),
                               (str(self.tmp / "alias" / "gdd-dev.local.md"), str(self.tmp))):
            with self.subTest(file_path=file_path):
                self._assert_denied(self._run("PreToolUse", {"tool_name": "Write", "cwd": cwd,
                                                             "tool_input": {"file_path": file_path, **content},
                                                             "transcript_path": str(t)}))
        # .claude 自体が別名のディレクトリへの symlink でも、今までどおり判定する
        real = self.tmp / "real"
        real.mkdir()
        (self.tmp / ".claude").rename(self.tmp / "claude-old")
        (self.tmp / ".claude").symlink_to(real)
        self._assert_denied(self._write(t, "Write", {"file_path": str(self.tmp / ".claude" / "gdd-dev.local.md"), **content}))

    def test_any_spelling_of_active_is_judged(self) -> None:
        # ディスクが active でなければ、書く内容を見ずに判定する（Stop hook は active を大文字小文字を問わず読む）
        t = self._transcript([assistant("claude-sonnet-5-5")])
        path = self._state("---\nactive: false\nsession_id:\n---\n")
        for tool, tool_input in (("Edit", {"file_path": str(path), "old_string": "active: false", "new_string": "active: True"}),
                                 ("Write", {"file_path": str(path), "content": "---\nactive: TRUE\n---\n"}),
                                 ("Write", {"file_path": str(path), "content": "---\n active : true # x\n---\n"}),
                                 ("Edit", {"file_path": str(path), "old_string": "a", "new_string": "b"})):
            self._assert_denied(self._write(t, tool, tool_input))
        self._state("---\nActive: True\n---\nactive: true\n")  # 本文の行ではなく frontmatter で読む
        self._assert_denied(self._write(t, "Edit", {"file_path": str(path), "old_string": "a", "new_string": "b"}))

    def test_updating_a_running_state_is_not_judged(self) -> None:
        # run の途中の更新（ディスクの frontmatter が active: true）は止めない
        t = self._transcript([assistant("claude-sonnet-5-5")])
        for text in ("---\nactive: true\nsession_id: s\n---\n", "---\nactive: True\n---\n"):
            path = self._state(text)
            for tool, tool_input in (("Write", {"file_path": str(path), "content": "---\nactive: true\nphase: x\n---\n"}),
                                     ("Edit", {"file_path": str(path), "old_string": "active: true", "new_string": "active: false"})):
                self.assertEqual(self._out(self._write(t, tool, tool_input)), {}, tool)

    def test_other_writes_bash_and_reads_are_not_judged_by_the_hook(self) -> None:
        t = self._transcript([assistant("claude-sonnet-5-5")])
        for tool, tool_input in (("Bash", {"command": "/p/scripts/setup-gdd-loop.sh x"}),
                                 ("Write", {"file_path": str(self.tmp / "gdd-dev.local.md"), "content": "active: true"}),
                                 ("Write", {"file_path": str(self.tmp / "a.md"), "content": "active: true"}),
                                 ("Read", {"file_path": str(self.tmp / ".claude" / "gdd-dev.local.md")})):
            self.assertEqual(self._out(self._write(t, tool, tool_input)), {}, tool)

    def test_broken_write_payload_does_not_crash_the_hook(self) -> None:
        t = self._transcript([assistant("claude-sonnet-5-5")])
        for tool_input in ("x", {"file_path": 3}):
            proc = self._write(t, "MultiEdit", tool_input)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertNotIn("Traceback", proc.stderr)
        # 読めない・判定できないときは、run を始める書き込みとして判定する
        self._state(None)
        (self.tmp / ".claude" / "gdd-dev.local.md").mkdir()
        for tool_input in ({"file_path": ".claude/gdd-dev.local.md", "edits": "x"},
                           {"file_path": "/r/\ud800/.claude/gdd-dev.local.md", "content": "active: true"}):
            proc = self._write(t, "MultiEdit", tool_input)
            self.assertNotIn("Traceback", proc.stderr)
            self._assert_denied(proc)

    def test_subagent_skill_call_is_judged_by_the_main_reply(self) -> None:
        t = self._transcript([assistant("claude-sonnet-5-5")])
        self._assert_denied(self._skill(t, agent_id="sub-1"))

    def test_typed_command_is_not_judged_before_the_reply(self) -> None:
        # 返事の前（UserPromptExpansion）の transcript の最後の信号は前のターンのモデルなので、ここでは判定しない
        self.assertEqual(self._out(self._expansion(self._transcript([assistant("claude-sonnet-5-5")]))), {})

    # --- 今の返事のモデル（道具の呼び出しの id、今の turn の行、最後の信号の順）

    def test_switched_to_opus_on_screen_passes(self) -> None:
        # 前の turn は Sonnet。画面で Opus に切り替えて打った /gdd-dev は、今の返事の Opus で判定する
        t = self._transcript([assistant("claude-sonnet-5-5"), prompt(), tool_call("claude-opus-5-5", "tu1")])
        self.assertEqual(self._out(self._skill(t, tool_use_id="tu1")), {})
        self.assertIn("tool_use_id", self._log())

    def test_switched_to_sonnet_on_screen_is_denied_without_the_hint(self) -> None:
        t = self._transcript([assistant("claude-opus-5-5"), prompt(), tool_call("claude-sonnet-5-5", "tu1")])
        proc = self._skill(t, tool_use_id="tu1")
        self._assert_denied(proc)
        self._assert_hint(proc, shown=False)

    def test_current_turn_line_is_used_without_the_tool_use_id(self) -> None:
        t = self._transcript([assistant("claude-sonnet-5-5"), prompt(), assistant("claude-opus-5-5")])
        self.assertEqual(self._out(self._skill(t)), {})
        self.assertIn("current_turn", self._log())
        t = self._transcript([assistant("claude-opus-5-5"), prompt(), assistant("claude-sonnet-5-5")])
        self._assert_hint(self._skill(t), shown=False)

    def test_line_written_while_waiting_is_read(self) -> None:
        # transcript は非同期に書かれ、hook の時点で今の返事がまだ無いことがある（文書）。短く読み直す
        t = self._transcript([assistant("claude-sonnet-5-5"), prompt()])
        env = {"HOME": str(self.home), "PATH": "/usr/bin:/bin:/opt/homebrew/bin:/usr/local/bin",
               "CLAUDE_PLUGIN_ROOT": str(PLUGIN_ROOT), "CLAUDE_CODE_ENTRYPOINT": "cli"}
        payload = {"session_id": "s-1", "hook_event_name": "PreToolUse", "tool_name": "Skill", "tool_use_id": "tu1",
                   "tool_input": {"skill": "gdd-dev"}, "transcript_path": str(t)}
        proc = subprocess.Popen(["bash", str(HOOK)], cwd=self.tmp, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, text=True, env=env)
        proc.stdin.write(json.dumps(payload))
        proc.stdin.close()
        time.sleep(0.6)  # 1 回目の走査の後、読み直しの間に書く
        with t.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(tool_call("claude-opus-5-5", "tu1")) + "\n")
        out = proc.stdout.read()
        proc.wait(timeout=10)
        self.assertEqual(out.strip(), "")
        self.assertIn("\ttool_use_id\t", self._log())

    def test_log_failure_does_not_drop_the_deny(self) -> None:
        # ログを encode できない名前（孤立サロゲート）でも deny を出す
        t = self._transcript([], raw_lines=['{"type":"assistant","message":{"model":"claude-sonnet-\\ud800","content":[]}}'])
        self._assert_denied(self._skill(t))
        state = self.home / ".claude" / ".gdd-hook-state"
        state.mkdir(parents=True, exist_ok=True)
        self._log_path().unlink(missing_ok=True)
        self._log_path().mkdir()  # ログの場所がディレクトリで書けない
        self._assert_denied(self._skill(self._transcript([assistant("claude-sonnet-5-5")])))

    def test_log_follows_the_state_dir_rules(self) -> None:
        state = self.tmp / "state"
        self._skill(self._transcript([assistant("claude-sonnet-5-5")]), extra_env={"GDD_HOOK_STATE_DIR": str(state)})
        log = state / "main-model-gate.log"
        self.assertEqual(log.stat().st_mode & 0o777, 0o600)
        text = log.read_text(encoding="utf-8")
        self.assertNotIn("s-1", text)  # session はハッシュで書く
        self.assertIn("\tSkill\tcurrent_turn\t", text)

    def test_previous_turn_only_is_denied_with_the_hint(self) -> None:
        # 読み直しても今の返事の行が無ければ、前の信号で判定し、切り替えた直後の案内を出す
        t = self._transcript([assistant("claude-sonnet-5-5"), prompt()])
        proc = self._skill(t, tool_use_id="tu1")
        self._assert_denied(proc)
        self._assert_hint(proc, shown=True)
        self.assertIn("fallback", self._log())

    def test_latest_signal_wins(self) -> None:
        t = self._transcript([assistant("claude-opus-5-5"), set_model("Sonnet 5.5")])
        self._assert_denied(self._skill(t))
        t = self._transcript([assistant("claude-opus-5-5"), model_attachment("claude-sonnet-5-5")])
        self._assert_denied(self._skill(t))

    def test_sidechain_and_synthetic_are_not_signals(self) -> None:
        t = self._transcript([assistant("claude-sonnet-5-5"), assistant("claude-opus-5-5", sidechain=True), assistant("<synthetic>")])
        self._assert_denied(self._skill(t))

    def test_set_model_text_outside_local_command_stdout_is_not_a_signal(self) -> None:
        for content in (
            "This session is being continued ... Set model to Opus 5.5 ...",
            "<local-command-stdout>status: ok. Set model to Opus 5.5</local-command-stdout>",
        ):
            t = self._transcript([assistant("claude-sonnet-5-5"), {"type": "user", "message": {"content": content}}])
            self._assert_denied(self._skill(t))

    def test_sidechain_model_attachment_is_not_a_signal(self) -> None:
        att = model_attachment("claude-opus-5-5")
        att["isSidechain"] = True
        self._assert_denied(self._skill(self._transcript([assistant("claude-sonnet-5-5"), att])))

    def test_set_model_plain_and_backtick_forms(self) -> None:
        for content in (
            "<local-command-stdout>Set model to claude-opus-5-5</local-command-stdout>",
            "<local-command-stdout>Set model to `claude-opus-5-5`</local-command-stdout>",
        ):
            t = self._transcript([assistant("claude-sonnet-5-5"), {"type": "user", "message": {"content": content}}])
            self.assertEqual(self._out(self._skill(t)), {}, content)

    # --- 例外で guard 全体が落ちない

    def test_broken_lines_do_not_drop_the_guard(self) -> None:
        t = self._transcript([assistant("claude-sonnet-5-5")], raw_lines=["{not json", "[1,2]", '{"type":"assistant","message":null}'])
        self._assert_denied(self._skill(t))

    def test_deeply_nested_line_does_not_drop_the_guard(self) -> None:
        t = self._transcript([assistant("claude-sonnet-5-5")], raw_lines=["[" * 10**6 + "]" * 10**6])
        self._assert_denied(self._skill(t))

    # --- 通す

    def test_opus_and_fable_are_allowed(self) -> None:
        for model in ("claude-opus-5-5", "claude-fable-5-1"):
            proc = self._skill(self._transcript([assistant("claude-sonnet-5-5"), assistant(model)]))
            self.assertEqual(proc.returncode, 0)
            self.assertEqual(self._out(proc), {}, model)

    def test_set_model_to_opus_after_sonnet_is_allowed(self) -> None:
        proc = self._skill(self._transcript([assistant("claude-sonnet-5-5"), set_model("Opus 5.5")]))
        self.assertEqual(self._out(proc), {})

    def test_other_skills_are_not_gated(self) -> None:
        proc = self._skill(self._transcript([assistant("claude-sonnet-5-5")]), skill="gdd-status")
        self.assertEqual(self._out(proc), {})

    def test_opt_out_env_only_with_value_1(self) -> None:
        t = self._transcript([assistant("claude-sonnet-5-5")])
        self.assertEqual(self._out(self._skill(t, extra_env={"GDD_ALLOW_NON_OPUS_MAIN": "1"})), {})
        for value in ("0", "true", " 1", ""):
            self._assert_denied(self._skill(t, extra_env={"GDD_ALLOW_NON_OPUS_MAIN": value}))

    def test_kill_switch(self) -> None:
        (self.home / ".claude" / "gdd-hooks-disabled").write_text("", encoding="utf-8")
        t = self._transcript([assistant("claude-sonnet-5-5")])
        self.assertEqual(self._out(self._skill(t)), {})
        self.assertEqual(self._out(self._skill(t)), {})

    def test_opt_out_covers_every_entry(self) -> None:
        t = self._transcript([assistant("claude-sonnet-5-5")])
        env = {"GDD_ALLOW_NON_OPUS_MAIN": "1"}
        self.assertEqual(self._out(self._skill(t, extra_env=env)), {})

    def test_entry_is_judged_without_home(self) -> None:
        t = self._transcript([assistant("claude-sonnet-5-5")])
        env = {"PATH": "/usr/bin:/bin:/opt/homebrew/bin:/usr/local/bin", "CLAUDE_PLUGIN_ROOT": str(PLUGIN_ROOT)}
        payload = {"session_id": "s-1", "hook_event_name": "PreToolUse", "tool_name": "Skill",
                   "tool_input": {"skill": "gdd-dev"}, "transcript_path": str(t)}
        proc = subprocess.run(["bash", str(HOOK)], cwd=self.tmp, input=json.dumps(payload), capture_output=True,
                              text=True, env=env, check=False)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self._assert_denied(proc)

    # --- 判定できないとき（止めず、Claude Code なら知らせる）

    def test_undeterminable_is_allowed_with_notice_in_claude_code(self) -> None:
        for transcript in (self.tmp / "missing.jsonl", self._transcript([{"type": "user", "message": {"content": "hi"}}])):
            for proc in (self._skill(transcript), self._skill(transcript)):
                out = self._out(proc)
                self.assertNotIn("hookSpecificOutput", out)
                self.assertIn("判定できません", out.get("systemMessage", ""))

    def test_undeterminable_is_silent_outside_claude_code(self) -> None:
        proc = self._skill(self.tmp / "missing.jsonl", extra_env={"CLAUDE_CODE_ENTRYPOINT": ""})
        self.assertEqual(self._out(proc), {})

    def test_unreadable_payload_is_allowed(self) -> None:
        env = {"HOME": str(self.home), "PATH": "/usr/bin:/bin:/opt/homebrew/bin", "CLAUDE_PLUGIN_ROOT": str(PLUGIN_ROOT)}
        proc = subprocess.run(["bash", str(HOOK)], cwd=self.tmp, input="not json", capture_output=True, text=True, env=env, check=False)
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(proc.stdout.strip(), "")

    # --- 相談の段での通知（返事の後の Stop、セッションにつき 1 回）

    def test_stop_notice_once_per_session_when_sonnet(self) -> None:
        t = self._transcript([assistant("claude-sonnet-5-5")])
        payload = {"transcript_path": str(t)}
        first = self._out(self._run("Stop", payload))
        self.assertIn("Opus", first["systemMessage"])
        self.assertNotIn("decision", first)
        self.assertEqual(self._out(self._run("Stop", payload)), {})

    def test_stop_notice_not_for_opus(self) -> None:
        t = self._transcript([assistant("claude-opus-5-5")])
        self.assertEqual(self._out(self._run("Stop", {"transcript_path": str(t)})), {})

    def test_stop_reads_the_model_that_just_replied(self) -> None:
        # 画面での切り替えは記録に残らないことがある。返事の後なら、最後の信号は今答えたモデルになる
        t = self._transcript([assistant("claude-sonnet-5-5"), {"type": "user", "message": {"content": "続けて"}},
                              assistant("claude-opus-5-5")])
        self.assertEqual(self._out(self._run("Stop", {"transcript_path": str(t)})), {})

    def test_user_prompt_submit_does_not_notify(self) -> None:
        # 返事の前は、最後の信号が前のターンのモデルなので、ここでは知らせない
        t = self._transcript([assistant("claude-sonnet-5-5")])
        self.assertEqual(self._out(self._run("UserPromptSubmit", {"prompt": "x", "transcript_path": str(t)})), {})

    def test_session_start_notice_from_payload_model(self) -> None:
        out = self._out(self._run("SessionStart", {"source": "startup", "model": "claude-sonnet-5-5"}))
        self.assertIn("Opus", out["systemMessage"])
        t = self._transcript([assistant("claude-sonnet-5-5")])
        self.assertEqual(self._out(self._run("Stop", {"transcript_path": str(t)})), {})

    def test_session_start_on_resume_waits_for_the_reply(self) -> None:
        # 再開の時点の transcript の最後の信号は再開の前のモデルで、画面で別のモデルを選ぶと食い違う。
        # 再開の後の最初の返事の Stop で知らせる
        t = self._transcript([assistant("claude-haiku-4-5")])
        self.assertEqual(self._out(self._run("SessionStart", {"source": "resume", "transcript_path": str(t)})), {})
        out = self._out(self._run("Stop", {"transcript_path": str(t)}))
        self.assertIn("claude-haiku-4-5", out["systemMessage"])

    def test_session_start_does_not_use_env_or_settings_default(self) -> None:
        # Desktop はセッションごとにモデルを選ぶので、env と settings の既定は実際のモデルと食い違う
        # （30 日の通知 555 件のうち、直後の main が Opus だったのが 250 件）。既定では知らせない
        (self.home / ".claude" / "settings.json").write_text('{"model": "global.anthropic.claude-sonnet-5"}', encoding="utf-8")
        (self.tmp / ".claude").mkdir()
        (self.tmp / ".claude" / "settings.local.json").write_text('{"model": "sonnet"}', encoding="utf-8")
        payload = {"source": "startup"}
        self.assertEqual(self._out(self._run("SessionStart", payload, extra_env={"ANTHROPIC_MODEL": "claude-sonnet-5-5"})), {})

    def test_notice_comes_from_stop_after_default_was_ignored(self) -> None:
        (self.home / ".claude" / "settings.json").write_text('{"model": "sonnet"}', encoding="utf-8")
        self.assertEqual(self._out(self._run("SessionStart", {"source": "startup"})), {})
        t = self._transcript([assistant("claude-sonnet-5-5")])
        out = self._out(self._run("Stop", {"transcript_path": str(t)}))
        self.assertIn("claude-sonnet-5-5", out["systemMessage"])

    def test_session_start_settings_do_not_drive_the_block(self) -> None:
        (self.home / ".claude" / "settings.json").write_text('{"model": "sonnet"}', encoding="utf-8")
        self.assertEqual(self._out(self._skill(self.tmp / "missing.jsonl", extra_env={"CLAUDE_CODE_ENTRYPOINT": ""})), {})

    def test_session_start_silent_for_opus_or_unknown(self) -> None:
        self.assertEqual(self._out(self._run("SessionStart", {"source": "startup", "model": "claude-opus-5-5"})), {})
        self.assertEqual(self._out(self._run("SessionStart", {"source": "startup"})), {})

    # --- 配線

    def test_registered_on_the_entries_and_notice_events(self) -> None:
        hooks = json.loads((PLUGIN_ROOT / "hooks" / "hooks.json").read_text(encoding="utf-8"))["hooks"]
        found = {
            (event, entry.get("matcher"), h["command"])
            for event, entries in hooks.items()
            for entry in entries
            for h in entry.get("hooks", [])
            if "run-main-model-gate-hook.sh" in h["command"]
        }
        command = 'bash "${CLAUDE_PLUGIN_ROOT}/hooks/scripts/run-main-model-gate-hook.sh"'
        self.assertEqual(found, {("PreToolUse", "Skill|Write|Edit|MultiEdit", command),
                                 ("Stop", "*", command), ("SessionStart", "*", command)})


if __name__ == "__main__":
    unittest.main()
