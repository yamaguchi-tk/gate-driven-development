"""名前が改行で終わる repo では、block hook が marker を見ずに止める側に倒す。

bash の `$(pwd)`・`$(git rev-parse --show-toplevel)` は末尾の改行を全部落とすので、`<repo>\\n`
の toplevel が `<repo>` になり、別のパスの marker で判定していた。marker の書き手
（`setup-gdd-loop.sh`）も同じ落とし方で書くので、正しいパスで読むと標準の流れで marker を
見失う。書き手と読み手をそろえるまでは、改行で終わる toplevel を判定できないものとして止める
（merge gate と同じ）。
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from _git_fixture import init_repo
from _paths import PLUGIN_ROOT

SCRIPTS = PLUGIN_ROOT / "hooks" / "scripts"
SESSION = "test-session"

# (hook, payload, 止める形)。どれも active な GDD の repo で止める入力。形は `decision: block` か
# PreToolUse の `permissionDecision: deny` で、hook ごとにその形だけを止めたとみなす。
HOOKS = (
    ("run-block-plan-mode-hook.sh", {"tool_name": "EnterPlanMode", "tool_input": {}}, "block"),
    ("run-block-enter-worktree-hook.sh", {"tool_name": "EnterWorktree", "tool_input": {}}, "block"),
    (
        "run-active-gdd-skill-gate-hook.sh",
        {"tool_name": "Skill", "tool_input": {"skill": "superpowers:writing-plans"}},
        "block",
    ),
    ("run-active-gdd-skill-expansion-gate-hook.sh", {"prompt": "/superpowers:writing-plans"}, "block"),
    (
        "run-background-dispatch-gate-hook.sh",
        {"tool_name": "Agent", "tool_input": {"subagent_type": "gdd-formal-gate-runner", "prompt": "x"}},
        "deny",
    ),
)


def _blocked(stdout: str, form: str) -> bool:
    if not stdout.strip():
        return False
    out = json.loads(stdout)
    if form == "deny":
        return out.get("hookSpecificOutput", {}).get("permissionDecision") == "deny"
    return out.get("decision") == "block"


def _repo(path: Path, *, active: bool | None) -> Path:
    path.mkdir(parents=True)
    init_repo(path)
    if active is not None:
        marker = path / ".claude" / "gdd-dev.local.md"
        marker.parent.mkdir()
        marker.write_text(
            f"---\nactive: {'true' if active else 'false'}\nsession_id: {SESSION}\n---\n",
            encoding="utf-8",
        )
    return path


def _run(script: str, payload: dict, cwd: Path, home: Path) -> subprocess.CompletedProcess:
    # HOME を空のディレクトリにする（手元の kill switch で判定を見ずに通らないように）。
    env = {**os.environ, "CLAUDE_PLUGIN_ROOT": str(PLUGIN_ROOT), "CLAUDE_CODE_SESSION_ID": SESSION,
           "HOME": str(home)}
    env.pop("GDD_DISABLE", None)
    return subprocess.run(
        ["bash", str(SCRIPTS / script)], cwd=cwd, input=json.dumps(payload),
        capture_output=True, text=True, env=env, timeout=60, check=False,
    )


class _Base(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = Path(tmp.name).resolve()
        self.n = 0
        self.home = self.tmp / "home"
        self.home.mkdir()

    def _case(self) -> Path:
        self.n += 1
        base = self.tmp / f"case{self.n}"
        base.mkdir()
        return base


class BlockHookTests(_Base):
    def assertBlocked(self, result, form):
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(_blocked(result.stdout, form), result.stdout)

    def test_repo_whose_name_ends_with_a_newline_blocks_whatever_the_marker(self):
        # marker の有無・値、末尾を落とした同名の repo の有無、サブディレクトリからの起動に
        # かかわらず止める。5 本の hook はどれも marker を読む前に同じ
        # `gdd_marker_state_at`（lib/exact-path.sh）で止めるので、組み合わせの
        # 全部は先頭の hook で見て、ほかの hook は呼んでいることだけを 2 通りで見る。
        grid = [(a, t, s) for a in (True, False, None) for t in (None, True, False) for s in (False, True)]
        wiring = [(False, False, False), (None, None, True)]
        for index, (script, payload, form) in enumerate(HOOKS):
            for active, twin, sub in (grid if index == 0 else wiring):
                with self.subTest(hook=script, active=active, twin=twin, sub=sub):
                    base = self._case()
                    if twin is not None:
                        _repo(base / "repo", active=twin)
                    cwd = _repo(base / "repo\n", active=active)
                    if sub:
                        cwd = cwd / "sub"
                        cwd.mkdir()
                    self.assertBlocked(_run(script, payload, cwd, self.home), form)

    def test_directory_outside_git_whose_name_ends_with_a_newline_blocks(self):
        # git の外では cwd を toplevel とみなす。cwd の末尾の改行も落とさずに読む。
        for script, payload, form in HOOKS:
            with self.subTest(hook=script):
                cwd = self._case() / "dir\n"
                cwd.mkdir()
                self.assertBlocked(_run(script, payload, cwd, self.home), form)

    def test_repo_without_a_newline_keeps_the_marker_decision(self):
        # 対照: 名前が改行で終わらない repo は、今までどおり marker で決める。
        for script, payload, form in HOOKS:
            for active in (True, False):
                with self.subTest(hook=script, active=active):
                    result = _run(script, payload, _repo(self._case() / "repo", active=active), self.home)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertEqual(_blocked(result.stdout, form), active, result.stdout)


class LocalStateActiveTests(_Base):
    """Stop hook の bash 入口（python が無いときの判定）が使う `gdd_local_state_active`。"""

    def _active(self, cwd: Path) -> int:
        return subprocess.run(
            ["bash", "-c", 'source "$1"; gdd_local_state_active', "_",
             str(SCRIPTS / "lib" / "gdd-active-check.sh")],
            cwd=cwd, capture_output=True, text=True, timeout=30, check=False,
        ).returncode

    def test_repo_whose_name_ends_with_a_newline_is_active_whatever_the_marker(self):
        for active in (True, False, None):
            for twin in (None, False):
                with self.subTest(active=active, twin=twin):
                    base = self._case()
                    if twin is not None:
                        _repo(base / "repo", active=twin)
                    self.assertEqual(self._active(_repo(base / "repo\n", active=active)), 0)

    def test_repo_without_a_newline_keeps_the_marker_decision(self):
        for active in (True, False):
            with self.subTest(active=active):
                expected = 0 if active else 1
                self.assertEqual(self._active(_repo(self._case() / "repo", active=active)), expected)


class LastTurnFailureTests(_Base):
    """StopFailure の記録（書き手）を、名前が改行で終わる repo で SessionStart（読み手）が注入する。"""

    def _quiet_path(self) -> str:
        # 通知コマンド（osascript・notify-send）を含まない PATH。テストで実機の通知を出さない。
        bin_dir = self.tmp / "quiet-bin"
        if not bin_dir.exists():
            bin_dir.mkdir()
            for command in ("bash", "git", "cat", "mkdir", "mktemp", "rm", "mv", "chmod",
                            "dirname", "basename", "head", "tr", "sed", "grep", "date",
                            "printf", "realpath", "python3", "env", "ls", "find", "sort",
                            "wc", "cut", "awk", "uname", "id", "stat", "touch", "tail"):
                resolved = shutil.which(command)
                if resolved:
                    (bin_dir / command).symlink_to(resolved)
        return str(bin_dir)

    def test_record_is_injected_in_a_repo_whose_name_ends_with_a_newline(self):
        for suffix in ("", "\n", " "):
            with self.subTest(suffix=repr(suffix)):
                base = self._case()
                home = base / "home"
                home.mkdir()
                repo = _repo(base / f"repo{suffix}", active=None)
                env = {**os.environ, "HOME": str(home), "CLAUDE_PLUGIN_ROOT": str(PLUGIN_ROOT),
                       "PATH": self._quiet_path()}
                for key in ("GDD_HOOK_STATE_DIR", "GDD_DISABLE"):
                    env.pop(key, None)
                written = subprocess.run(
                    ["bash", str(SCRIPTS / "run-stop-failure-hook.sh")],
                    input=json.dumps({"session_id": "deadbeefcafe0000", "cwd": str(repo),
                                      "error": "api_error", "error_details": "x"}),
                    capture_output=True, text=True, env=env, cwd=repo, timeout=60,
                )
                self.assertEqual(written.returncode, 0, written.stderr)
                result = subprocess.run(
                    ["bash", str(SCRIPTS / "run-session-start-hook.sh")],
                    input=json.dumps({"session_id": "s", "source": "startup", "cwd": str(repo)}),
                    capture_output=True, text=True, env=env, cwd=repo, timeout=60,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("gdd:last-turn-failed", result.stdout, result.stdout[-500:])


if __name__ == "__main__":
    unittest.main()
