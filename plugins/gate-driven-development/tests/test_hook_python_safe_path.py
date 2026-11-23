"""hook の python は、hook の cwd（repo）の .py を標準ライブラリや plugin の module より先に読まない。

repo に json.py や lib/__init__.py があると、`python3 -c` の import がそれに置き換わり、block gate が例外で
素通りしていた。どの hook も最初に source する lib/kill-switch.sh が、`python3` を `-I -X utf8` で起動する
関数にする（cwd・PYTHONPATH・PYTHONHOME を読まない。Python 3.4 以上）。関数を通らない起動（`exec python3`、
python3 が無いときの `python`、hook が起動したプロセスの子の python）のために、PYTHONSAFEPATH=1 も export する
（3.11 以上で `-c`・標準入力の起動に cwd を入れない。PYTHONPATH の要素は止めない）。
`-I`・PYTHONSAFEPATH の下ではファイルで起動したスクリプトのディレクトリも sys.path に入らないので、自分の
ディレクトリの lib を読むスクリプトは、自分でそのディレクトリを入れる。
3.11 未満の python で確かめるケースは /usr/bin/python3 が 3.11 未満のときだけ走り、無ければ skip として残す。
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from _paths import PLUGIN_ROOT
from _pre_push_gate_support import PrePushGateFixtureMixin
from _root_branch_guard_support import init_git_repo
from _stop_hook_test_base import _make_transcript_jsonl, _run_hook as _run_stop_hook, _write_state_file
import test_active_gdd_skill_gate_contract as active_skill
import test_pre_pr_gate_contract as pre_pr

KILL_SWITCH = PLUGIN_ROOT / "hooks" / "scripts" / "lib" / "kill-switch.sh"
HOOK_SCRIPTS = PLUGIN_ROOT / "hooks" / "scripts"
HITL_FIXTURES = Path(__file__).parent / "fixtures" / "hitl-lint-gate"
NEEDS_SAFE_PATH = unittest.skipIf(sys.version_info < (3, 11), "PYTHONSAFEPATH は Python 3.11 以上でだけ効く")
OLD_PYTHON = Path("/usr/bin/python3")
NO_OLD_PYTHON = "/usr/bin/python3 が 3.11 未満でないので、3.11 未満の python のケースは確かめていない"


def _old_python_available() -> bool:
    if not OLD_PYTHON.is_file():
        return False
    proc = subprocess.run([str(OLD_PYTHON), "-c", "import sys; print(sys.version_info < (3, 11))"],
                          capture_output=True, text=True, check=False)
    return proc.stdout.strip() == "True"


def _path_python3_reads_safe_path() -> bool:
    # hook と _stop_hook_test_base は PATH の python3 で動くので、テストを動かす python の版では決めない
    proc = subprocess.run(["python3", "-c", "import sys; print(getattr(sys.flags, 'safe_path', False))"],
                          env=dict(os.environ, PYTHONSAFEPATH="1"), capture_output=True, text=True, check=False)
    return proc.stdout.strip() == "True"


def _shadow_stdlib(directory: Path) -> None:
    (directory / "json.py").write_text("raise ImportError('repo json')\n", encoding="utf-8")
    (directory / "lib").mkdir(exist_ok=True)
    (directory / "lib" / "__init__.py").write_text("", encoding="utf-8")


def _file_launched_scripts() -> list[Path]:
    """hook や gate がファイルとして起動しうる .py（固定の一覧ではなく、置き場所と run-*.sh の参照から拾う）。"""
    scripts = {*HOOK_SCRIPTS.glob("*.py"), *(PLUGIN_ROOT / "scripts").glob("*.py")}
    for hook in HOOK_SCRIPTS.glob("*.sh"):
        for line in hook.read_text(encoding="utf-8").splitlines():
            if line.lstrip().startswith("#"):
                continue
            for name in re.findall(r"\blib/([\w-]+\.py)\b", line):
                scripts.add(HOOK_SCRIPTS / "lib" / name)
    return sorted(scripts)


class SafePathLaunchTests(unittest.TestCase):
    @NEEDS_SAFE_PATH
    def test_kill_switch_keeps_cwd_out_of_sys_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            proc = subprocess.run(
                ["bash", "-c", 'source "$1"; "$2" -c "import sys; print(sys.flags.safe_path); print(sys.path[0])"',
                 "x", str(KILL_SWITCH), sys.executable],
                cwd=tmp, capture_output=True, text=True, check=True,
            )
            safe_path, first = proc.stdout.splitlines()
            self.assertEqual(safe_path, "True")
            self.assertNotIn(first, ("", tmp, os.path.realpath(tmp)))

    def test_python3_after_kill_switch_ignores_repo_modules_and_pythonpath(self):
        # リテラル・変数・標準入力のどの起動の形でも、PYTHONPATH の空・相対の要素でも、repo の json.py を読まない
        launches = {
            "literal": 'python3 -c "import json; print(1)"',
            "variable": 'P=python3; "$P" -c "import json; print(1)"',
            "stdin": 'printf "import json\\nprint(1)\\n" | python3 -',
        }
        with tempfile.TemporaryDirectory() as tmp:
            _shadow_stdlib(Path(tmp))
            for pythonpath in (None, ":", ".", ":/x"):
                env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
                if pythonpath is not None:
                    env["PYTHONPATH"] = pythonpath
                for name, launch in launches.items():
                    with self.subTest(pythonpath=pythonpath, launch=name):
                        proc = subprocess.run(["bash", "-c", f'source "$1"; {launch}', "x", str(KILL_SWITCH)],
                                              cwd=tmp, env=env, capture_output=True, text=True, check=False)
                        self.assertEqual((proc.returncode, proc.stdout.strip()), (0, "1"), proc.stderr)

    def _assert_scripts_import_their_lib(self, argv: list[str], env: dict[str, str]) -> None:
        scripts = _file_launched_scripts()
        self.assertIn(HOOK_SCRIPTS / "lib" / "stop-failure-record.py", scripts)
        with tempfile.TemporaryDirectory() as tmp:
            for script in scripts:
                with self.subTest(script=script.name):
                    proc = subprocess.run([*argv, str(script), "--help"], cwd=tmp, env=env,
                                          stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=60)
                    self.assertNotIn("ModuleNotFoundError", proc.stderr)

    def test_plugin_scripts_import_their_own_lib_under_isolation(self):
        self._assert_scripts_import_their_lib([sys.executable, "-I", "-X", "utf8"], dict(os.environ))

    @NEEDS_SAFE_PATH
    def test_plugin_scripts_import_their_own_lib_under_safe_path(self):
        self._assert_scripts_import_their_lib([sys.executable], dict(os.environ, PYTHONSAFEPATH="1"))

    def test_plugin_scripts_import_their_own_lib_under_isolation_before_3_11(self):
        # 3.11 未満の -I は sys.flags.safe_path を持たないので、sys.flags.isolated の分岐だけが lib を入れる
        if not _old_python_available():
            self.skipTest(NO_OLD_PYTHON)
        self._assert_scripts_import_their_lib([str(OLD_PYTHON), "-I", "-X", "utf8"], dict(os.environ))

    def test_hook_scripts_launch_python3_only_through_the_kill_switch_function(self):
        # exec・timeout・env・nohup・xargs・command・絶対パスで起動する python は、kill-switch.sh の関数を通らず
        # -I が付かない（`command -v python3` の存在の確かめと、kill-switch.sh 自身の関数の定義は除く）。
        # 正規表現で並べた形だけを見る。引用符つきの絶対パス、名前に python を含まない変数、オプションや行継続を
        # 挟む形は拾わない
        bypass = re.compile(
            r"(?:^|[\s;&|(`])(?:exec|timeout(?:\s+-\S+)*\s+\S+|env(?:\s+\S+=\S*)*|nohup|xargs|command(?!\s+-v\b))"
            r"\s+(?:\"?\$\{?\w*(?:python|PYTHON)\w*\}?\"?|python3?\b)"
            r"|(?:^|[\s;&|(`])/\S*/python3?\b"
        )
        sources = [*HOOK_SCRIPTS.glob("*.sh"), *(HOOK_SCRIPTS / "lib").glob("*.sh"),
                   PLUGIN_ROOT / "scripts" / "check-gate-ledger.sh"]
        found = []
        for source in sources:
            for number, line in enumerate(source.read_text(encoding="utf-8").splitlines(), 1):
                code = line.split("#", 1)[0] if line.lstrip().startswith("#") else line
                if source == KILL_SWITCH and "command python3 -I" in code:
                    continue
                if bypass.search(code):
                    found.append(f"{source.relative_to(PLUGIN_ROOT)}:{number}: {line.strip()}")
        self.assertEqual(found, [])


@unittest.skipUnless(_path_python3_reads_safe_path(), "PATH の python3 が PYTHONSAFEPATH を読まない（3.11 未満）")
class StopHookHitlLintUnderSafePathTests(unittest.TestCase):
    """Stop hook と、そこから起動する HITL lint は、PYTHONSAFEPATH の下でも判定する。"""

    def _run(self, text: str) -> tuple[int, str, str]:
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            _write_state_file(ws, {"active": "true", "session_id": "test-session", "iteration": "1"})
            transcript = ws / "transcript.jsonl"
            _make_transcript_jsonl(transcript, assistant_text=text)
            return _run_stop_hook(ws, transcript, session_id="test-session",
                                  env_overrides={"GDD_PLUGIN_ROOT": str(PLUGIN_ROOT), "PYTHONSAFEPATH": "1"})

    def test_clean_hitl_is_not_blocked(self):
        code, out, err = self._run((HITL_FIXTURES / "gold-pass.md").read_text(encoding="utf-8"))
        self.assertEqual(code, 0, err)
        self.assertNotIn('"decision": "block"', out)
        self.assertNotIn("ModuleNotFoundError", out + err)

    def test_failing_hitl_is_reported_by_the_lint(self):
        code, out, err = self._run((HITL_FIXTURES / "quality-fail.md").read_text(encoding="utf-8"))
        self.assertEqual(code, 0, err)
        payload = json.loads(out.strip())
        self.assertNotIn("decision", payload)
        self.assertIn("lint-hitl-display-integrity", payload["systemMessage"])
        # lint が import に失敗すると traceback が警告文に載る。名前だけでは見分けられない
        self.assertNotIn("Traceback", payload["systemMessage"])


class StopHookEntryIgnoresRepoModulesTests(unittest.TestCase):
    """本番の入口（run-gdd-stop-hook.sh、python3 関数で -I）から、cwd の json.py と PYTHONPATH=: でも Stop hook 本体が
    落ちずに HITL lint の結果を返す。HITL lint が起動する子の python が -I かは見分けない（lint は json を import しない）。"""

    def _run(self, text: str) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as tmp:
            ws = Path(tmp)
            _write_state_file(ws, {"active": "true", "session_id": "test-session", "iteration": "1"})
            transcript = ws / "transcript.jsonl"
            _make_transcript_jsonl(transcript, assistant_text=text)
            _shadow_stdlib(ws)
            env = {k: v for k, v in os.environ.items()
                   if k not in ("CLAUDE_PLUGIN_ROOT", "GDD_PLUGIN_ROOT", "GDD_STOP_HOOK_MAX_CONSECUTIVE_BLOCKS",
                                "GDD_SKIP_HITL_LINT")}
            env.update(CLAUDE_CODE_SESSION_ID="test-session", PYTHONPATH=":")
            hook_input = {"cwd": str(ws), "session_id": "test-session", "transcript_path": str(transcript)}
            return subprocess.run(["bash", str(HOOK_SCRIPTS / "run-gdd-stop-hook.sh")], cwd=ws,
                                  input=json.dumps(hook_input), capture_output=True, text=True, env=env,
                                  check=False, timeout=60)

    def test_failing_hitl_is_reported_by_the_lint(self):
        result = self._run((HITL_FIXTURES / "quality-fail.md").read_text(encoding="utf-8"))
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout.strip())
        self.assertNotIn("decision", payload, result.stderr)
        self.assertIn("lint-hitl-display-integrity", payload["systemMessage"])
        self.assertNotIn("Traceback", payload["systemMessage"])

    def test_clean_hitl_is_not_blocked(self):
        result = self._run((HITL_FIXTURES / "gold-pass.md").read_text(encoding="utf-8"))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn('"decision": "block"', result.stdout)
        self.assertNotIn("Python スクリプトがエラーで終了しました", result.stdout)


class BlockGatesIgnoreRepoModulesTests(PrePushGateFixtureMixin, unittest.TestCase):
    """cwd（repo の toplevel）に json.py と lib/ があっても、block gate は block する。"""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.ws = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def _repo(self, name: str) -> Path:
        repo = self.ws / name
        repo.mkdir()
        return repo

    def _assert_all_gates_block(self, name: str, extra: dict[str, str]) -> None:
        self._assert_pre_push_blocks(name, extra)
        self._assert_pre_pr_blocks(name, extra)
        self._assert_skill_gates_block(name, extra)
        self._assert_worktree_guard_denies(name, extra)

    def test_gates_block(self):
        self._assert_all_gates_block("default", {})

    def test_gates_block_with_empty_pythonpath_element(self):
        self._assert_all_gates_block("pythonpath", {"PYTHONPATH": ":"})

    def test_gates_block_with_python3_before_3_11_first_on_path(self):
        if not _old_python_available():
            self.skipTest(NO_OLD_PYTHON)
        old_bin = self.ws / "oldbin"
        old_bin.mkdir()
        (old_bin / "python3").symlink_to(OLD_PYTHON)
        self._assert_all_gates_block("old", {"PATH": f"{old_bin}{os.pathsep}{os.environ.get('PATH', '')}"})

    def _assert_pre_push_blocks(self, name: str, extra: dict[str, str]) -> None:
        with self.subTest(gate="pre-push"):
            repo = self._repo(f"push-{name}")
            self._init_repo(repo)
            self._write_local_state(repo, active=True)
            self._write_steering(repo, resume_from="gdd-implementation-gating",
                                 next_action="gdd-implementation-gating", task_size="standard", evidence=None)
            _shadow_stdlib(repo)
            result = self._run_hook(repo, "git push origin main",
                                    extra_env={"GDD_HOOK_STATE_DIR": str(self.ws / "hookstate"), **extra})
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(self._decision(result), "notice", result.stderr)

    def _assert_pre_pr_blocks(self, name: str, extra: dict[str, str]) -> None:
        helper = pre_pr.PrePrGateContractTests("test_hooks_json_registers_bash_pre_pr_gate")
        with self.subTest(gate="pre-PR"):
            repo = self._repo(f"pr-{name}")
            helper._init_repo(repo)
            helper._write_local_state(repo)
            helper._write_steering(repo, next_action="gdd-completion-check")
            _shadow_stdlib(repo)
            result = helper._run_hook(repo, "gh pr create --title test --body ok", extra_env=extra)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["hookSpecificOutput"]["hookEventName"], "PreToolUse", result.stderr)

    def _assert_skill_gates_block(self, name: str, extra: dict[str, str]) -> None:
        # active_skill の _run_hook は PATH を渡さず /usr/bin/python3（3.9 のことがある）で動くので、PATH を引き継ぐ
        helper = active_skill.ActiveGddSkillGateContractTests("test_hooks_json_registers_skill_matcher")
        env = dict(os.environ, CLAUDE_PLUGIN_ROOT=str(PLUGIN_ROOT), CLAUDE_CODE_SESSION_ID="test-session", **extra)
        repo = self._repo(f"skill-{name}")
        helper._init_repo(repo)
        helper._write_active_state(repo)
        _shadow_stdlib(repo)
        for gate, hook, payload in (
            ("skill", "run-active-gdd-skill-gate-hook.sh",
             {"tool_name": "Skill", "tool_input": {"name": "superpowers:writing-plans"}}),
            ("expansion", "run-active-gdd-skill-expansion-gate-hook.sh", {"prompt": "/superpowers:writing-plans"}),
        ):
            result = subprocess.run(["bash", str(HOOK_SCRIPTS / hook)], cwd=repo, input=json.dumps(payload),
                                    capture_output=True, text=True, env=env, check=False)
            with self.subTest(gate=gate):
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(json.loads(result.stdout)["decision"], "block", result.stderr)

    def _assert_worktree_guard_denies(self, name: str, extra: dict[str, str]) -> None:
        with self.subTest(gate="worktree-command-guard"):
            repo = self._repo(f"guard-{name}")
            init_git_repo(repo)
            (repo / ".claude").mkdir()
            (repo / ".claude" / "gdd-dev.local.md").write_text(
                "---\nactive: true\nsession_id: test-session\n---\n", encoding="utf-8")
            _shadow_stdlib(repo)
            payload = {"tool_name": "Bash",
                       "tool_input": {"command": "git switch -c codex/20260611-root-branch", "cwd": str(repo)}}
            result = subprocess.run(["bash", str(HOOK_SCRIPTS / "run-worktree-command-guard.sh")], cwd=repo,
                                    input=json.dumps(payload), capture_output=True, text=True, check=False,
                                    env=dict(os.environ, CLAUDE_PLUGIN_ROOT=str(PLUGIN_ROOT), **extra))
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertEqual(json.loads(result.stderr.strip())["hookSpecificOutput"]["permissionDecision"], "deny")


if __name__ == "__main__":
    unittest.main()
