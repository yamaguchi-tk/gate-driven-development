"""merge gate と pre-push gate: steering の列挙から落ちるものを「無い」として通さない。

PR #218 の独立-3 の H1・H2（限界の節の先頭に書いた、直していない常時 High）。

- H1: pre-push gate は、共有の resolver（`gdd_pre_push_resolve_steering`）が候補 0 件の
  none を返すと、読めない steering（一覧できない task dir など）があっても検査せずに
  通していた。merge gate は #218 で止めるようになったので非対称だった
- H2: 「読めない」の判定は `-d`・`-f` で symlink を辿るが、resolver と本体の
  `find -type f`（-P）は symlink の先を列挙しない。symlink で置いた steering は、
  列挙からも「読めない」の判定からも落ちて通っていた

「読めない」は、`find -P -type f` が列挙しない形に揃える（`.steering` やその下の entry が
symlink、task dir が一覧できない、state.md が在るのに列挙されない・読めない）。

state.md が FIFO の形は、binding の resolver（python）が開いて待ち、hook の timeout で
通っていた。resolver は通常ファイルでない state.md を開かず、pre-push gate は判定を
resolver より前で行う。
"""
from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

from _merge_gate_support import _init_named_repo, _write_marker_only
from _plugin_module_loader import load_plugin_module
from _stop_hook_test_base import _bind, _make_two_worktree_fixture
from _timing_budget import hang_guard_seconds
from _pre_push_gate_support import PrePushGateFixtureMixin
from test_merge_gate_ledger_fail_closed import _LedgerCase, _hook, _is_block, _is_pass
from test_merge_gate_hook_non_gdd_merge import _register

# pre-push gate の FIFO のテストの壁時計の打ち切り（止まったときの保険）。merge gate の FIFO のテストは
# `_hook` の既定（`_merge_gate_support.HANG_GUARD`）で打ち切る。
PRE_PUSH_GATE_HANG_GUARD = hang_guard_seconds("run-pre-push-gate-hook.sh")

DONE_PR7 = (
    "## Gate Status\n- Resume From: done\n- Next Action: done\n"
    "- PR URL: https://github.com/acme/widgets/pull/7\n"
)


def _task(parent: Path, name: str = "20260103-target") -> Path:
    task = parent / name
    task.mkdir(parents=True)
    (task / "state.md").write_text(DONE_PR7, encoding="utf-8")
    return task


class MergeGateSymlinkSteeringTests(_LedgerCase):
    """merge gate の none の分岐（steering が 1 件も解決できない）。"""

    def _repo(self, name: str) -> Path:
        repo = _init_named_repo(self.tmp, name)
        _write_marker_only(repo, active=False, session_id=None)
        return repo

    def _assert_state_unreadable(self, repo: Path) -> None:
        result = _hook("gh pr merge 7", repo, self.home)
        self.assertTrue(_is_block(result), result.stdout)
        self.assertIn("state-unreadable", result.stdout)

    def test_symlinked_steering_dir_blocks(self):
        repo = self._repo("widgets")
        real = self.tmp / "real-steering"
        _task(real)
        (repo / ".steering").symlink_to(real)
        self._assert_state_unreadable(repo)

    def test_symlinked_task_dir_blocks(self):
        repo = self._repo("widgets")
        (repo / ".steering").mkdir()
        target = _task(self.tmp / "elsewhere")
        (repo / ".steering" / "20260103-target").symlink_to(target)
        self._assert_state_unreadable(repo)

    def test_symlinked_state_md_blocks(self):
        repo = self._repo("widgets")
        task = repo / ".steering" / "20260103-target"
        task.mkdir(parents=True)
        real = self.tmp / "state-real.md"
        real.write_text(DONE_PR7, encoding="utf-8")
        (task / "state.md").symlink_to(real)
        self._assert_state_unreadable(repo)

    def test_fifo_state_md_blocks_without_waiting(self):
        for shape in ("fifo", "symlink-to-fifo"):
            with self.subTest(shape=shape):
                repo = self._repo(f"widgets-{shape}")
                task = repo / ".steering" / "20260103-target"
                task.mkdir(parents=True)
                if shape == "fifo":
                    os.mkfifo(task / "state.md")
                else:
                    fifo = self.tmp / f"fifo-{shape}"
                    os.mkfifo(fifo)
                    (task / "state.md").symlink_to(fifo)
                result = _hook("gh pr merge 7", repo, self.home)
                self.assertTrue(_is_block(result), result.stdout)
                self.assertIn("state-unreadable", result.stdout)

    def test_steering_as_regular_file_blocks(self):
        repo = self._repo("widgets")
        (repo / ".steering").write_text("not a dir\n", encoding="utf-8")
        self._assert_state_unreadable(repo)

    def test_unlistable_steering_blocks(self):
        for mode in (0o000, 0o311, 0o600):
            with self.subTest(mode=oct(mode)):
                repo = self._repo(f"widgets-{mode:o}")
                _task(repo / ".steering")
                self._lock(repo / ".steering", mode)
                self._assert_state_unreadable(repo)

    def test_readable_shapes_still_pass(self):
        # 従来どおり通す形: `.steering` が無い、README など task 以外のファイルだけ、
        # state.md の無い task dir（実データの task dir にも多い）。
        bare = self._repo("bare")
        self.assertTrue(_is_pass(_hook("gh pr merge 7", bare, self.home)))
        files_only = self._repo("files-only")
        (files_only / ".steering").mkdir()
        (files_only / ".steering" / "README.md").write_text("x\n", encoding="utf-8")
        (files_only / ".steering" / "learned-patterns.md").write_text("x\n", encoding="utf-8")
        (files_only / ".steering" / "20260103-empty").mkdir()
        self.assertTrue(_is_pass(_hook("gh pr merge 7", files_only, self.home)))


class LedgerSymlinkSteeringTests(_LedgerCase):
    """台帳の照合も同じ基準で「読めない」と決める。"""

    def test_symlinked_task_dir_in_ledger_root_is_unreadable(self):
        target = _task(self.tmp / "elsewhere")
        (self.gdd / ".steering" / "20260104-link").symlink_to(target)
        _register(self.home, self.gdd)
        self._unreadable_verdict()

    def test_symlinked_ledger_file_still_hits(self):
        # 台帳のファイル自体が symlink でも、指す先の通常ファイルは読める（従来どおり）。
        # marker の無い git repo の経路は hit のときだけ不足として通知するので、hit と unreadable を分ける。
        real = self.tmp / "ledger-real"
        real.write_text(f"{self.gdd}\n", encoding="utf-8")
        ledger = self.home / ".claude" / ".gdd-hook-state" / "gdd-pr-roots"
        ledger.parent.mkdir(parents=True)
        ledger.symlink_to(real)
        self.assertTrue(_is_block(self._from_checkout("gh pr merge 7")))


class PrePushUnreadableSteeringTests(PrePushGateFixtureMixin, unittest.TestCase):
    """pre-push gate も、読めない steering があれば steering の解決の結果によらず不足として通知する。"""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self._locked: list[tuple[Path, int]] = []

    def tearDown(self):
        for path, mode in reversed(self._locked):
            path.chmod(mode)

    def _lock(self, path: Path, mode: int) -> None:
        if os.geteuid() == 0:
            self.skipTest("root は権限を落としても読めてしまう")
        self._locked.append((path, path.stat().st_mode & 0o7777))
        path.chmod(mode)

    def _repo(self, name: str, *, trivial_active: bool) -> Path:
        repo = self.tmp / name
        repo.mkdir()
        self._init_repo(repo)
        self._write_local_state(repo, active=True)
        if trivial_active:
            # found（作業中が 1 件）で Task Size が trivial。今までは検査せずに通っていた。
            self._write_steering(repo, task_size="trivial")
        return repo

    def _push(self, repo: Path):
        return self._run_hook(
            repo, "git push -u origin main",
            extra_env={"GDD_HOOK_STATE_DIR": str(self.tmp / f"hookstate-{repo.name}")},
        )

    def _assert_blocks(self, repo: Path) -> None:
        result = self._push(repo)
        self.assertEqual(self._decision(result), "notice", result.stdout + result.stderr)
        reason = json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"]
        self.assertIn("steering-unreadable", reason)
        self.assertIn("GDD_SKIP_PRE_PUSH_GATE=1", reason)

    def _assert_passes(self, repo: Path) -> None:
        result = self._push(repo)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIsNone(self._decision(result), result.stdout)

    def test_unlistable_task_dir_blocks_on_none_and_found(self):
        for trivial_active in (False, True):
            for mode in (0o000, 0o311, 0o600):
                with self.subTest(found=trivial_active, mode=oct(mode)):
                    repo = self._repo(f"r-{trivial_active}-{mode:o}", trivial_active=trivial_active)
                    locked = _task(repo / ".steering", "20260816-locked")
                    self._lock(locked, mode)
                    self._assert_blocks(repo)

    def test_unlistable_steering_blocks(self):
        for mode in (0o000, 0o311, 0o600):
            with self.subTest(mode=oct(mode)):
                repo = self._repo(f"s-{mode:o}", trivial_active=False)
                _task(repo / ".steering")
                self._lock(repo / ".steering", mode)
                self._assert_blocks(repo)

    def test_symlink_shapes_block_on_none_and_found(self):
        for trivial_active in (False, True):
            with self.subTest(found=trivial_active, shape="task-dir"):
                repo = self._repo(f"l-{trivial_active}", trivial_active=trivial_active)
                target = _task(self.tmp / f"elsewhere-{trivial_active}")
                (repo / ".steering").mkdir(exist_ok=True)
                (repo / ".steering" / "20260816-link").symlink_to(target)
                self._assert_blocks(repo)
            with self.subTest(found=trivial_active, shape="state-md"):
                repo = self._repo(f"m-{trivial_active}", trivial_active=trivial_active)
                task = repo / ".steering" / "20260816-link"
                task.mkdir(parents=True)
                real = self.tmp / f"state-real-{trivial_active}.md"
                real.write_text(DONE_PR7, encoding="utf-8")
                (task / "state.md").symlink_to(real)
                self._assert_blocks(repo)

    def test_symlinked_steering_dir_blocks(self):
        repo = self._repo("sym-steering", trivial_active=False)
        real = self.tmp / "real-steering"
        _task(real)
        (repo / ".steering").symlink_to(real)
        self._assert_blocks(repo)

    def test_fifo_state_md_blocks_without_waiting(self):
        for trivial_active in (False, True):
            with self.subTest(found=trivial_active):
                repo = self._repo(f"fifo-{trivial_active}", trivial_active=trivial_active)
                task = repo / ".steering" / "20260816-fifo"
                task.mkdir(parents=True)
                os.mkfifo(task / "state.md")
                result = self._run_hook(
                    repo, "git push -u origin main",
                    extra_env={"GDD_HOOK_STATE_DIR": str(self.tmp / f"hs-fifo-{trivial_active}")},
                    timeout=PRE_PUSH_GATE_HANG_GUARD,
                )
                self.assertEqual(self._decision(result), "notice", result.stdout + result.stderr)
                self.assertIn("steering-unreadable", json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"])

    def test_readable_shapes_still_pass(self):
        bare = self._repo("bare", trivial_active=False)
        self._assert_passes(bare)
        trivial = self._repo("trivial", trivial_active=True)
        (trivial / ".steering" / "README.md").write_text("x\n", encoding="utf-8")
        (trivial / ".steering" / "learned-patterns.md").write_text("x\n", encoding="utf-8")
        (trivial / ".steering" / "20260816-empty").mkdir()
        self._assert_passes(trivial)
        # 候補の無い（none の）steering も、読めるなら従来どおり通す。
        none = self._repo("none", trivial_active=False)
        self._write_steering(none, resume_from="cancelled", next_action="cancelled")
        self._assert_passes(none)

    def test_relative_root_still_checks_the_steering(self):
        # `cd repo && git push`・`git -C repo push` では root が相対パスのまま入る。hook は
        # root へ cd 済みなので、判定が `repo/.steering` を cd 先から見ると「無い」になる。
        ws = self.tmp / "ws"
        ws.mkdir()
        repo = ws / "repo"
        repo.mkdir()
        self._init_repo(repo)
        self._write_local_state(repo, active=True)
        (ws / "link").symlink_to(repo)
        locked = _task(repo / ".steering", "20260816-locked")
        self._lock(locked, 0o000)
        commands = (
            "cd repo && git push -u origin main",
            "git -C repo push -u origin main",
            "cd link && git push -u origin main",
            "git -C link push -u origin main",
        )
        for trivial_active in (False, True):
            if trivial_active:
                self._write_steering(repo, task_size="trivial")
            for command in commands:
                with self.subTest(found=trivial_active, command=command):
                    result = self._run_hook(
                        ws, command, extra_env={"GDD_HOOK_STATE_DIR": str(self.tmp / "hs-rel")}
                    )
                    self.assertEqual(self._decision(result), "notice", result.stdout + result.stderr)
                    reason = json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"]
                    self.assertIn("steering-unreadable", reason)
                    self.assertIn("GDD_SKIP_PRE_PUSH_GATE=1", reason)

    def test_relative_root_without_unreadable_steering_passes(self):
        ws = self.tmp / "ws2"
        ws.mkdir()
        for name, readme in (("bare", False), ("files", True)):
            with self.subTest(shape=name):
                repo = ws / name
                repo.mkdir()
                self._init_repo(repo)
                self._write_local_state(repo, active=True)
                if readme:
                    (repo / ".steering").mkdir()
                    (repo / ".steering" / "README.md").write_text("x\n", encoding="utf-8")
                result = self._run_hook(
                    ws, f"cd {name} && git push -u origin main",
                    extra_env={"GDD_HOOK_STATE_DIR": str(self.tmp / f"hs-{name}")},
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIsNone(self._decision(result), result.stdout)

    def test_names_with_glob_and_space_characters_do_not_crash(self):
        # fail-open ケース「例外で guard 全体が落ちる」: set -euo pipefail の下で、空の
        # `.steering`（glob が 0 件）と、glob の文字・空白を含む名前でも落ちずに判定する。
        empty = self._repo("empty", trivial_active=False)
        (empty / ".steering").mkdir()
        self._assert_passes(empty)
        odd = self._repo("odd", trivial_active=True)
        self._write_steering(odd, slug="20260816-a b*[x]?", resume_from="cancelled",
                             next_action="cancelled")
        self._assert_passes(odd)
        # LF を含む名前も、列挙の出力の中の同じ並びと一致するので読める側に入る。
        lf = self._repo("lf", trivial_active=True)
        self._write_steering(lf, slug="20260816-a\nb", resume_from="cancelled",
                             next_action="cancelled")
        self._assert_passes(lf)


class ResolverPermissionErrorTests(unittest.TestCase):
    """binding の resolver は、state.md の種類を確かめるときの権限エラーでも落ちない。

    Python 3.12 の `Path.is_file()` は EACCES を投げる（r はあるが x の無い task dir の
    下の state.md。3.13 以降は False を返す）。resolver が例外で抜けると、Stop hook の
    done guard は bind を失って warn に下がり、未完了の tasklist でも done を通す。
    CI（3.14）で同じ入力を作れないので、`is_file` が投げる形を patch で作る。
    """

    def test_permission_error_from_is_file_keeps_the_bind_resolved(self):
        module = load_plugin_module("hooks/scripts/gdd_stop_hook.py")
        original = Path.is_file

        def _raising(path, *args, **kwargs):
            if path.name == "state.md":
                raise PermissionError(13, "Permission denied", str(path))
            return original(path, *args, **kwargs)

        with tempfile.TemporaryDirectory() as tmp:
            _wt_a, wt_b = _make_two_worktree_fixture(Path(tmp))
            _bind(wt_b)
            # binding の無い（legacy の）steering。resolver の診断用の走査が state.md を見る。
            legacy = wt_b / ".steering" / "20260801-legacy"
            legacy.mkdir(parents=True)
            (legacy / "state.md").write_text(
                "Resume From: gdd-implementation\nNext Action: gdd-implementation\n",
                encoding="utf-8",
            )
            module._BIND_CACHE.clear()
            Path.is_file = _raising
            try:
                bind = module._resolve_bind_memoized(wt_b)
            finally:
                Path.is_file = original
                module._BIND_CACHE.clear()
            self.assertEqual(bind.status, "resolved", bind)
            self.assertEqual(Path(bind.steering_dir).name, "20260822-target")


if __name__ == "__main__":
    unittest.main()
