"""hook がロケールに依らず UTF-8 で動く契約テスト。

hook は利用者のロケールを受け継ぐ。UTF-8 以外のロケール（EUC-JP など）だと、python の stdin・
stdout・argv・環境変数と awk・sed がそのロケールで文字を扱う。Claude Code が渡す payload（UTF-8 の
JSON）や state.md に日本語があると、次のことが起きていた。

- pre-push gate: payload を読めずに例外を握り、push を通す（fail-open）
- pre-PR gate: `python3 -c` の本文の日本語を decode できず（Linux）、hook が exit 1 で落ちて通す。
  macOS では awk・sed が state.md の日本語で落ち、壊れた理由で block する
- worktree guard: UnicodeDecodeError を捕まえずに exit 1 で落ち、guard 全体が通る

どの hook も最初に `lib/kill-switch.sh` を source するので、そこで `LC_ALL=C.UTF-8` と
`PYTHONUTF8=1` を export し、hook の中の文字の扱いを UTF-8 にそろえる。

入口のテストは、hook の入口（run-*.sh）を EUC-JP のロケールで起動し、payload（cwd）と state.md に
日本語を入れて、block すべき操作が block されることを見る（fail-open の 3 ケース: block すべき入力が
通らない、例外で guard が落ちない、読めない値で判定を落とさない）。
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

from _git_fixture import init_repo
from _locale_support import euc_jp_locale_env
from _paths import PLUGIN_ROOT
from _pre_push_gate_support import PrePushGateFixtureMixin

SCRIPTS = PLUGIN_ROOT / "hooks" / "scripts"
KILL_SWITCH = SCRIPTS / "lib" / "kill-switch.sh"
HOOKS_JSON = PLUGIN_ROOT / "hooks" / "hooks.json"
PRE_PR_GATE = SCRIPTS / "run-pre-pr-gate-hook.sh"
WORKTREE_GUARD = SCRIPTS / "run-worktree-command-guard.sh"
# 日本語を含む作業場所（payload の cwd に入る）
JA_DIR = "リポジトリ"
JA_HANDOFF = "Last Handoff Summary: 日本語の引き継ぎ\n"


def _scripts_of(commands: list[str]) -> list[Path]:
    """hooks.json の command が起動する `.sh` の一覧。`.sh` でない command は、検査の対象から黙って外れないよう落とす。"""
    matches = {c: re.search(r"hooks/scripts/([\w.-]+\.sh)", c) for c in commands}
    unmatched = [c for c, m in matches.items() if not m]
    if unmatched:
        raise AssertionError(f"hooks/scripts/ の .sh を起動しない command がある（入口の検査に含められない）: {unmatched}")
    return [SCRIPTS / name for name in sorted({m.group(1) for m in matches.values()})]


def _hook_scripts() -> list[Path]:
    return _scripts_of([
        hook["command"]
        for entries in json.loads(HOOKS_JSON.read_text(encoding="utf-8"))["hooks"].values()
        for entry in entries
        for hook in entry["hooks"]
    ])


class HookScriptListingTests(unittest.TestCase):
    def test_a_command_that_is_not_a_hook_script_fails_the_listing(self) -> None:
        good = "bash ${CLAUDE_PLUGIN_ROOT}/hooks/scripts/run-x-hook.sh"
        self.assertEqual(_scripts_of([good, good]), [SCRIPTS / "run-x-hook.sh"])
        for bad in ("python3 ${CLAUDE_PLUGIN_ROOT}/hooks/scripts/run_x.py", "echo hi", "bash ${CLAUDE_PLUGIN_ROOT}/hooks/run-x.sh"):
            with self.subTest(command=bad), self.assertRaises(AssertionError):
                _scripts_of([good, bad])


class KillSwitchExportsUtf8Tests(unittest.TestCase):
    def test_kill_switch_exports_utf8_locale_and_python_utf8_mode(self) -> None:
        text = KILL_SWITCH.read_text(encoding="utf-8")
        self.assertRegex(text, r"(?m)^export LC_ALL=C\.UTF-8$")
        self.assertRegex(text, r"(?m)^export PYTHONUTF8=1$")

    def test_every_hook_sources_kill_switch_before_reading_text(self) -> None:
        """hooks.json の入口はすべて、python・awk・sed・grep を使う前に kill-switch.sh を source する。"""
        scripts = _hook_scripts()
        self.assertGreaterEqual(len(scripts), 15)
        uses = re.compile(r"\b(python3?|PYTHON_BIN|awk|sed|grep)\b")
        for script in scripts:
            with self.subTest(script=script.name):
                lines = [
                    line for line in script.read_text(encoding="utf-8").splitlines()
                    if line.strip() and not line.lstrip().startswith("#")
                ]
                source_at = next(
                    (i for i, line in enumerate(lines) if re.search(r"source .*lib/kill-switch\.sh", line)), None
                )
                self.assertIsNotNone(source_at, "kill-switch.sh を source していない")
                first_use = next((i for i, line in enumerate(lines) if uses.search(line)), len(lines))
                self.assertLess(source_at, first_use)


class IsolatedPythonUsesUtf8ModeTests(unittest.TestCase):
    def test_isolated_python_is_started_with_utf8_mode(self) -> None:
        """`-I`・`-E` の python には kill-switch.sh の PYTHONUTF8 が効かないので、`-X utf8` を付ける。

        kill-switch.sh の LC_ALL の上書きが効いている間は、入口のテストでは `-X utf8` の有無を見分けられない
        （C.UTF-8 が無くても C ロケールの python は UTF-8 に落ちる）ので、起動の形で固定する。見るのは
        リテラルの `python`・`python3` に空白区切りの option が続く形だけで、変数で起動する python は見ない。"""
        invocation = re.compile(r"\bpython3?((?:\s+-[A-Za-z]\w*(?:\s+utf8\S*)?)+)")
        found = 0
        # plugin の scripts/ のうち、hook と同じ lib を source して判定を写す検算スクリプトも見る
        for path in [*sorted(SCRIPTS.rglob("*")), PLUGIN_ROOT / "scripts" / "check-gate-ledger.sh"]:
            if not path.is_file() or path.suffix not in (".sh", ".py"):
                continue
            for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                if line.lstrip().startswith("#"):
                    continue
                for match in invocation.finditer(line):
                    flags = match.group(1).split()
                    if not any(f.startswith("-") and not f.startswith("-X") and set(f[1:]) & {"I", "E"} for f in flags):
                        continue
                    found += 1
                    with self.subTest(path=f"{path.name}:{number}"):
                        self.assertRegex(match.group(1), r"-X\s+utf8(?=\s|$)")
        self.assertGreaterEqual(found, 2)


class _LocaleFixture(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="gdd-locale-")
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(os.path.realpath(self._tmp.name))
        self.locale_env = euc_jp_locale_env(self, self.tmp)
        self.repo = self.tmp / JA_DIR
        self.repo.mkdir()

    def _env(self) -> dict[str, str]:
        env = {k: v for k, v in os.environ.items() if not k.startswith(("PYTHON", "LC_", "GDD_"))}
        env.update({
            "CLAUDE_PLUGIN_ROOT": str(PLUGIN_ROOT),
            "CLAUDE_CODE_SESSION_ID": "test-session",
            "GDD_HOOK_STATE_DIR": str(self.tmp / "hookstate"),
            "HOME": str(self.tmp / "home"),
        })
        env.update(self.locale_env)
        return env

    def _write_local_state(self) -> None:
        (self.repo / ".claude").mkdir(exist_ok=True)
        (self.repo / ".claude" / "gdd-dev.local.md").write_text(
            "---\nactive: true\nsession_id: test-session\n---\n", encoding="utf-8"
        )

    def _run(self, script: Path, command: str) -> subprocess.CompletedProcess[bytes]:
        payload = {"tool_name": "Bash", "tool_input": {"command": command, "cwd": str(self.repo)}}
        return subprocess.run(
            ["bash", str(script)], cwd=self.repo, input=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            capture_output=True, env=self._env(), timeout=120,
        )


class PrePushGateInEucJpTests(_LocaleFixture, PrePushGateFixtureMixin):
    def test_push_without_evidence_is_blocked(self) -> None:
        self._init_repo(self.repo)
        self._write_local_state()
        steering = self._write_steering(self.repo, evidence=None)
        with (steering / "state.md").open("a", encoding="utf-8") as state:
            state.write(JA_HANDOFF)
        payload = {"tool_name": "Bash", "tool_input": {"command": "git push origin main", "cwd": str(self.repo)}}
        from _pre_push_gate_support import HOOK
        result = subprocess.run(
            ["bash", str(HOOK)], cwd=self.repo, input=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            capture_output=True, env=self._env(), timeout=120,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        decision = json.loads(result.stdout.decode("utf-8"))
        self.assertEqual(decision["hookSpecificOutput"]["hookEventName"], "PreToolUse")
        self.assertIn("missing-evidence", decision["hookSpecificOutput"]["additionalContext"])


class PrePrGateInEucJpTests(_LocaleFixture):
    def test_pr_create_before_completion_is_blocked_with_the_right_reason(self) -> None:
        init_repo(self.repo, branch="main")
        subprocess.run(["git", "switch", "-q", "-c", "feature"], cwd=self.repo, check=True)
        self._write_local_state()
        steering = self.repo / ".steering" / "20260614-locale"
        steering.mkdir(parents=True)
        (steering / "state.md").write_text(
            "Resume From: gdd-completion-check\nHuman Check Status: approved\nRoute In Progress: none\n"
            "Task Size: quick (express)\nADR distilled: not_applicable\n"
            "ADR distillation reason: 重要判断なし\n" + JA_HANDOFF + "Started At: 2026-06-14T00:00:00Z\n",
            encoding="utf-8",
        )
        (steering / "tasklist.md").write_text(
            "# Task List\n\n## Current Task\n- なし\n\nNext Action=gdd-completion-check\n", encoding="utf-8"
        )
        result = self._run(PRE_PR_GATE, "gh pr create --title 日本語 --body ok")
        self.assertEqual(result.returncode, 0, result.stderr.decode("utf-8", "replace"))
        decision = json.loads(result.stdout.decode("utf-8"))
        self.assertEqual(decision["hookSpecificOutput"]["hookEventName"], "PreToolUse")
        self.assertIn("Next Action=gdd-completion-check", decision["hookSpecificOutput"]["additionalContext"])


class WorktreeGuardInEucJpTests(_LocaleFixture):
    def test_root_branch_creation_is_denied_without_crashing(self) -> None:
        init_repo(self.repo, branch="main")
        self._write_local_state()
        result = self._run(WORKTREE_GUARD, "git switch -c codex/20260611-root-branch")
        self.assertEqual(result.returncode, 2, result.stderr.decode("utf-8", "replace"))
        decision = json.loads(result.stderr.decode("utf-8").strip())
        self.assertEqual(decision["hookSpecificOutput"]["permissionDecision"], "deny")


if __name__ == "__main__":
    unittest.main()
