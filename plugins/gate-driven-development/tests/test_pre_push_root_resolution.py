"""pre-push gate: 相対パス・`~`・`$HOME` で書いた root も、絶対パスと同じに判定する。

PR #222 の限界の節の先頭に書いた、直していない常時 High 3 件（review-log の M1〜M3）。

- M1: `cd repo && git push`・`git -C repo push` では root が相対パスのまま入り、hook が
  root へ cd した後も同じ相対パスで resolver・`git -C`・`find` を呼ぶ。done の steering を
  見つけずに通し、読める found は tip が決まらず止めていた
- M2: pre-push gate は CDPATH を外していない。相対パスの `cd` が stdout に絶対パスを印字し、
  通知の JSON が壊れて効かない。CDPATH の先の別の場所へも移る
- M3: `~`・`$HOME` を展開しないので、step 5 で active と判定されずに通していた

候補 root は、hook の python で展開して絶対パスにしてから使う（pre-PR gate と同じ
`expanduser`・`expandvars`）。`-` で始まる root も、絶対パスなら `cd` の option に化けない。
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

from _paths import PLUGIN_ROOT
from _pre_push_gate_support import PrePushGateFixtureMixin
from _timing_budget import hang_guard_seconds

# pre-push gate を起動するテストの壁時計の打ち切り（止まったときの保険）
PRE_PUSH_HANG_GUARD = hang_guard_seconds("run-pre-push-gate-hook.sh")
PUSH = "git push -u origin main"


class PrePushRootResolutionTests(PrePushGateFixtureMixin, unittest.TestCase):
    def setUp(self):
        self.ws = Path(tempfile.mkdtemp())
        self._locked: list[tuple[Path, int]] = []

    def tearDown(self):
        for path, mode in reversed(self._locked):
            path.chmod(mode)

    def _gdd_repo(self, name: str = "repo", *, parent: Path | None = None, **steering) -> Path:
        repo = (parent or self.ws) / name
        repo.mkdir(parents=True)
        self._init_repo(repo)
        self._write_local_state(repo, active=True)
        if steering:
            self._write_steering(repo, **steering)
        return repo

    def _done_repo(self, name: str = "repo", **kw) -> Path:
        # 作業中の steering は無く、done の steering が 1 件（resolver の union が拾う形）。
        return self._gdd_repo(name, resume_from="done", next_action="done", **kw)

    def _push(self, command: str, **env):
        extra = {"GDD_HOOK_STATE_DIR": str(self.ws / "hookstate")}
        extra.update(env)
        return self._run_hook(self.ws, command, extra_env=extra, timeout=PRE_PUSH_HANG_GUARD)

    def _code(self, result) -> str | None:
        self.assertEqual(result.returncode, 0, result.stderr)
        if not result.stdout.strip():
            return None
        # stdout は JSON 1 つだけ（CDPATH の印字などが混ざると decision が効かない）。
        payload = json.loads(result.stdout)
        self.assertEqual(payload["hookSpecificOutput"]["hookEventName"], "PreToolUse")
        return re.search(r"reason code: ([a-z-]+)", payload["hookSpecificOutput"]["additionalContext"]).group(1)

    def test_relative_root_finds_the_done_steering(self):
        self._done_repo()
        (self.ws / "link").symlink_to(self.ws / "repo")
        for command in (f"cd repo && {PUSH}", "git -C repo push -u origin main",
                        f"cd link && {PUSH}", f"cd ./repo && {PUSH}"):
            with self.subTest(command=command):
                self.assertEqual(self._code(self._push(command)), "missing-evidence")

    def test_relative_root_is_judged_like_the_absolute_root(self):
        # 読める作業中の trivial の steering は、絶対パスでも相対パスでも通す。
        repo = self._gdd_repo(task_size="trivial")
        for command in (f"cd {repo} && {PUSH}", f"cd repo && {PUSH}", "git -C repo push -u origin main"):
            with self.subTest(command=command):
                self.assertIsNone(self._code(self._push(command)))

    def test_home_and_tilde_roots_are_expanded(self):
        self._done_repo()
        for command in (f"cd ~/repo && {PUSH}", "git -C $HOME/repo push -u origin main",
                        f"cd ${{HOME}}/repo && {PUSH}"):
            with self.subTest(command=command):
                self.assertEqual(self._code(self._push(command, HOME=str(self.ws))), "missing-evidence")

    def test_git_dir_with_tilde_is_unresolvable(self):
        self._done_repo()
        result = self._push("git --git-dir=~/repo/.git push -u origin main", HOME=str(self.ws))
        self.assertEqual(self._code(result), "unresolvable-root")

    def test_cdpath_does_not_break_the_block(self):
        self._done_repo()
        other = self.ws / "other"
        other.mkdir()
        (other / "repo").mkdir()
        for cdpath in (".", str(other)):
            with self.subTest(cdpath=cdpath):
                result = self._push(f"cd repo && {PUSH}", CDPATH=cdpath)
                self.assertEqual(self._code(result), "missing-evidence")

    def test_dash_prefixed_root_is_not_an_option_of_cd(self):
        # `cd -P` は option として $HOME へ移る。絶対パスにしてから cd する。
        self._done_repo("-P")
        result = self._push("git -C -P push -u origin main", HOME=str(self.ws / "nowhere"))
        self.assertEqual(self._code(result), "missing-evidence")

    def test_relative_root_with_unreadable_steering_blocks(self):
        if os.geteuid() == 0:
            self.skipTest("root は権限を落としても読めてしまう")
        repo = self._gdd_repo(task_size="trivial")
        locked = repo / ".steering" / "20260816-locked"
        locked.mkdir()
        (locked / "state.md").write_text("Resume From: done\n", encoding="utf-8")
        self._locked.append((locked, 0o755))
        locked.chmod(0)
        for cdpath in (None, "."):
            with self.subTest(cdpath=cdpath):
                env = {"CDPATH": cdpath} if cdpath else {}
                self.assertEqual(self._code(self._push(f"cd repo && {PUSH}", **env)), "steering-unreadable")

    def test_unexpandable_roots_do_not_abort_the_guard(self):
        # fail-open ケース「例外で guard 全体が落ちる」: 展開できない root があっても、
        # 同じコマンドのほかの root の判定まで進む。
        repo = self._done_repo()
        for weird in ("~nosuchuser-gdd/x", "${GDD_UNDEFINED_VAR_X}/x"):
            with self.subTest(root=weird):
                result = self._push(f"git -C {weird} --work-tree={repo} push -u origin main")
                self.assertEqual(self._code(result), "unresolvable-root")
                alone = self._push(f"cd {weird} && {PUSH}")
                self.assertIsNone(self._code(alone))

    def test_empty_git_dir_value_does_not_become_the_process_cwd(self):
        # `--git-dir=` の空の値は候補にしない（process の cwd に化けさせない）。
        self._done_repo()
        nongdd = self.ws / "nongdd"
        nongdd.mkdir()
        self._init_repo(nongdd)
        result = self._run_hook(self.ws / "repo", f"git -C {nongdd} --git-dir= push -u origin main",
                                extra_env={"GDD_HOOK_STATE_DIR": str(self.ws / "hs2")}, timeout=PRE_PUSH_HANG_GUARD)
        self.assertIsNone(self._code(result))

    def test_subdirectory_root_is_judged_at_the_toplevel(self):
        # marker は repo の toplevel にある。サブディレクトリを指す root も toplevel で判定する。
        repo = self._done_repo()
        sub = repo / "plugins" / "x"
        sub.mkdir(parents=True)
        for command in (f"cd repo/plugins/x && {PUSH}", "git -C repo/plugins/x push -u origin main",
                        f"cd {sub} && {PUSH}"):
            with self.subTest(command=command):
                self.assertEqual(self._code(self._push(command)), "missing-evidence")
        result = self._run_hook(sub, PUSH, extra_env={"GDD_HOOK_STATE_DIR": str(self.ws / "hs3")},
                                timeout=PRE_PUSH_HANG_GUARD)
        self.assertEqual(self._code(result), "missing-evidence")

    def test_unresolvable_root_falls_back_to_the_process_cwd(self):
        # cd 先を解決できない（コマンド置換・存在しないパス）と、push は process の cwd で走る。
        repo = self._done_repo()
        for command in (f'cd "$(git rev-parse --show-toplevel)" && {PUSH}',
                        f"cd /nonexistent-gdd-root-x; {PUSH}",
                        "git -C ${GDD_UNDEFINED_VAR_X}/x push -u origin main"):
            with self.subTest(command=command):
                result = self._run_hook(repo, command,
                                        extra_env={"GDD_HOOK_STATE_DIR": str(self.ws / "hs4")},
                                        timeout=PRE_PUSH_HANG_GUARD)
                self.assertEqual(self._code(result), "missing-evidence")

    def test_unresolvable_root_falls_back_to_the_payload_cwd(self):
        # payload に cwd（tool_input.cwd、Codex は tool_input.workdir）があると、コマンドはそこで走る。
        # fallback も payload の cwd を見る（process の cwd だけを足すと、その片方を見落とす）。
        repo = self._done_repo()
        nongdd = self.ws / "nongdd"
        nongdd.mkdir()
        for key in ("cwd", "workdir"):
            with self.subTest(key=key):
                result = self._run_hook(nongdd, f"cd /nonexistent-gdd-root-x; {PUSH}", tool_cwd=repo,
                                        tool_cwd_key=key,
                                        extra_env={"GDD_HOOK_STATE_DIR": str(self.ws / f"hs6-{key}")},
                                        timeout=PRE_PUSH_HANG_GUARD)
                self.assertEqual(self._code(result), "missing-evidence")

    def test_lone_surrogate_does_not_drop_the_roots(self):
        # fail-open ケース「例外で guard 全体が落ちる」: JSON の `\ud800` は UTF-8 に符号化
        # できない。python の出力が例外になると、root も fallback も出ずに通していた。
        repo = self._done_repo()
        for command in (f"cd /nonexistent\ud800; {PUSH}", "git push -u origin main\ud800"):
            with self.subTest(command=command):
                result = self._run_hook(repo, command,
                                        extra_env={"GDD_HOOK_STATE_DIR": str(self.ws / "hs7")},
                                        timeout=PRE_PUSH_HANG_GUARD)
                self.assertIsNotNone(self._code(result))

    def test_expansion_error_keeps_the_other_roots(self):
        # fail-open ケース「例外で guard 全体が落ちる」: `~` の後の user 名に NUL があると
        # expanduser が ValueError を投げる。その root も絶対パスにして、ほかの root の判定へ進む。
        repo = self._done_repo()
        result = self._push(f"git -C '~a\x00b/x' --work-tree={repo} push -u origin main")
        self.assertEqual(self._code(result), "unresolvable-root")

    def test_cdpath_is_unset_before_the_hook_resolves_its_own_directory(self):
        # hook を相対パスで起動すると、SCRIPT_DIR の `cd` が CDPATH を見る。印字や別の場所への
        # 移動で lib を読めずに落ちると、検査されずに通る。
        repo = self._done_repo()
        fake = self.ws / "fake"
        (fake / "hooks" / "scripts").mkdir(parents=True)
        env = os.environ.copy()
        env.update({"CLAUDE_PLUGIN_ROOT": str(PLUGIN_ROOT), "CLAUDE_CODE_SESSION_ID": "test-session",
                    "GDD_HOOK_STATE_DIR": str(self.ws / "hs5"), "CDPATH": f"{fake}:."})
        payload = {"tool_name": "Bash", "tool_input": {"command": f"cd {repo} && {PUSH}"}}
        result = subprocess.run(["bash", "hooks/scripts/run-pre-push-gate-hook.sh"], cwd=PLUGIN_ROOT,
                                input=json.dumps(payload), capture_output=True, text=True, env=env,
                                timeout=PRE_PUSH_HANG_GUARD, check=False)
        self.assertEqual(self._code(result), "missing-evidence")


if __name__ == "__main__":
    unittest.main()
