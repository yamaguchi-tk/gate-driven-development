"""merge gate: gh の実行先の repo の binding（root checkout と各 worktree の registry）から、
対象 PR の steering を GDD worktree で引く。

事象（2026-10-13、GDD を使う別の repo の PR）: launch worktree（marker 無し）の
セッションが `cd <root checkout> && gh pr merge 1328 -R <repo> --merge` を打つと、root に
残った別セッションの marker で root が untrusted root になり、root の `.steering/` に対象 PR が
無いので `untrusted-root-unverified` で止まった。steering は GDD worktree にあり、root の
`.gdd/tasks/<task_id>/binding.json` がそこを指していた。逆に GDD worktree（marker 無し）で
打った merge は、PR 台帳の照合が外れて証跡を見ずに通っていた。

契約: 対象 PR を明示した merge で、実行先の repo（git の共通ディレクトリから求める）の
root checkout と各 worktree の registry の binding が指す state.md の `PR URL` が対象 PR に
1 件だけ当たれば、その worktree の証跡で判定する（root・GDD worktree・同じ repo の別 worktree の
どこから打っても同じ binding を引く。引かない形と例外は lib/merge-gate-binding.sh のコメントのとおり）。
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from _plugin_module_loader import load_plugin_module
from _merge_gate_support import (
    _head_sha,
    _init_named_repo,
    _run_hook,
    _valid_evidence_lines,
    _write_marker_only,
)

URL = "https://github.com/acme/widgets/pull/7"
REPO = "acme/widgets"
TASK = "20261010-task"


def _write_steering(worktree: Path, *, slug=TASK, pr_url=URL, extra_lines=()):
    steering = worktree / ".steering" / slug
    steering.mkdir(parents=True, exist_ok=True)
    lines = ([f"- PR URL: {pr_url}"] if pr_url else []) + list(extra_lines)
    (steering / "state.md").write_text(
        "## Gate Status\n- Resume From: done\n- Next Action: done\n" + "\n".join(lines) + "\n"
    )
    return steering


def _write_binding(root: Path, worktree: Path, *, task_id=TASK, slug=TASK):
    steering = worktree / ".steering" / slug
    path = root / ".gdd" / "tasks" / task_id / "binding.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({
        "binding_version": 1,
        "branch": f"feat/{task_id}",
        "repo_root": str(root),
        "state_path": str(steering / "state.md"),
        "steering_path": str(steering),
        "task_id": task_id,
        "worktree_path": str(worktree),
    }))
    return path


class BindingSteeringTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp()).resolve()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.home = self.tmp / "home"
        (self.home / ".claude").mkdir(parents=True)
        self.root = _init_named_repo(self.tmp, "root")
        subprocess.run(
            ["git", "-C", str(self.root), "remote", "add", "origin",
             f"https://github.com/{REPO}.git"], check=True,
        )
        # セッションの起動ディレクトリ（desktop の launch worktree。marker 無し）。
        self.launch = self._add_worktree("launch")
        # GDD worktree（marker 無し。steering と証跡を持つ）。
        self.gdd = self._add_worktree("gdd")
        # PR の head は root の HEAD と違う（証跡は GDD worktree の HEAD で照合する）。
        subprocess.run(["git", "-C", str(self.gdd), "commit", "-q", "--allow-empty", "-m", "pr"],
                       check=True)
        self.other = _init_named_repo(self.tmp, "other")

    def _add_worktree(self, name, repo=None):
        path = self.tmp / name
        subprocess.run(
            ["git", "-C", str(repo or self.root), "worktree", "add", "-q", "-b",
             f"feat/{name}", str(path)],
            check=True,
        )
        return path

    def _gdd_task(self, *, approval=True, pr_url=URL, worktree=None, root=None):
        worktree = worktree or self.gdd
        lines = _valid_evidence_lines(_head_sha(worktree))
        if not approval:
            lines = [ln for ln in lines if "Merge Approval" not in ln]
        _write_steering(worktree, pr_url=pr_url, extra_lines=lines)
        _write_binding(root or self.root, worktree)

    def _stale_root_marker(self):
        # 別のセッションが root で /gdd-dev を始めたときに残った marker。
        _write_marker_only(self.root, active=True, session_id="stale-session")

    def _run(self, command, cwd=None):
        return _run_hook({"tool_input": {"command": command}}, cwd or self.launch, self.home)

    def assertAllowed(self, result):
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "", result.stdout)

    def assertBlocked(self, result, reason):
        self.assertIn('"hookEventName": "PreToolUse"', result.stdout)
        self.assertIn(reason, result.stdout)

    # --- root checkout（他セッションの marker あり。事象の形） ---------------

    def test_root_with_a_stale_marker_judges_the_bound_worktree_evidence(self):
        self._stale_root_marker()
        self._gdd_task()
        for target in (f"7 -R {REPO}", URL, "7"):
            with self.subTest(target=target):
                self.assertAllowed(self._run(f"cd {self.root} && gh pr merge {target} --merge"))

    def test_root_with_a_stale_marker_still_blocks_without_approval(self):
        self._stale_root_marker()
        self._gdd_task(approval=False)
        result = self._run(f"cd {self.root} && gh pr merge 7 -R {REPO} --merge")
        self.assertBlocked(result, "approval-missing")
        self.assertNotIn("untrusted-root-unverified", result.stdout)

    def test_root_without_a_matching_binding_keeps_blocking(self):
        self._stale_root_marker()
        cases = {
            "no binding": lambda: _write_steering(self.gdd, extra_lines=_valid_evidence_lines(_head_sha(self.gdd))),
            "binding records another PR": lambda: self._gdd_task(pr_url=URL.replace("/7", "/8")),
            # PR URL 欄の外で対象 PR に触れているだけの steering は当たりにしない。
            "binding mentions the PR outside PR URL": lambda: (
                self._gdd_task(pr_url=URL.replace("/7", "/8")),
                (self.gdd / ".steering" / TASK / "state.md").open("a").write(f"- メモ: 前の PR {URL}\n"),
            ),
            "binding records another repo": lambda: self._gdd_task(
                pr_url="https://github.com/acme/other/pull/7"),
        }
        for name, prepare in cases.items():
            with self.subTest(case=name):
                shutil.rmtree(self.root / ".gdd", ignore_errors=True)
                shutil.rmtree(self.gdd / ".steering", ignore_errors=True)
                prepare()
                result = self._run(f"cd {self.root} && gh pr merge 7 -R {REPO} --merge")
                self.assertBlocked(result, "untrusted-root-unverified")

    def test_binding_to_a_worktree_of_another_repo_is_not_used(self):
        self._stale_root_marker()
        foreign = self._add_worktree("foreign", repo=self.other)
        self._gdd_task(worktree=foreign)
        result = self._run(f"cd {self.root} && gh pr merge 7 -R {REPO} --merge")
        self.assertBlocked(result, "untrusted-root-unverified")

    def test_binding_whose_state_path_is_outside_steering_is_not_used(self):
        self._stale_root_marker()
        notes = self.gdd / "notes"
        notes.mkdir()
        lines = _valid_evidence_lines(_head_sha(self.gdd))
        (notes / "state.md").write_text("- PR URL: " + URL + "\n" + "\n".join(lines) + "\n")
        path = _write_binding(self.root, self.gdd)
        data = json.loads(path.read_text())
        data["state_path"] = str(notes / "state.md")
        path.write_text(json.dumps(data))
        result = self._run(f"cd {self.root} && gh pr merge 7 -R {REPO} --merge")
        self.assertBlocked(result, "untrusted-root-unverified")

    def test_binding_that_only_mentions_the_pr_is_not_counted(self):
        # 本文で対象 PR に触れているだけの binding を数えると、2 件として不足の通知にしてしまう。
        self._stale_root_marker()
        self._gdd_task()
        second = self._add_worktree("gdd2")
        _write_steering(second, slug="20261011-task", pr_url=URL.replace("/7", "/8"),
                        extra_lines=[f"- メモ: 前の PR {URL}"])
        _write_binding(self.root, second, task_id="20261011-task", slug="20261011-task")
        self.assertAllowed(self._run(f"cd {self.root} && gh pr merge 7 -R {REPO} --merge"))

    def test_two_bindings_for_the_same_pr_are_ambiguous(self):
        self._stale_root_marker()
        self._gdd_task()
        second = self._add_worktree("gdd2")
        _write_steering(second, slug="20261011-task",
                        extra_lines=_valid_evidence_lines(_head_sha(second)))
        _write_binding(self.root, second, task_id="20261011-task", slug="20261011-task")
        result = self._run(f"cd {self.root} && gh pr merge 7 -R {REPO} --merge")
        self.assertIn("⛔ merge gate（reason code: steering-ambiguous）: ユーザーに確認して", result.stdout)

    def test_root_steering_without_a_pr_url_is_not_overtaken_by_a_binding(self):
        # root の判定材料が欠けている（PR URL 未記録の steering がある）ときは、binding で
        # 追い越さない（件数しだいで不足の通知が出ない側に反転しないように）。
        self._stale_root_marker()
        _write_steering(self.root, slug="20260101-unrecorded", pr_url=None)
        self._gdd_task()
        result = self._run(f"cd {self.root} && gh pr merge 7 -R {REPO} --merge")
        self.assertBlocked(result, "pr-url-unrecorded")

    def test_session_started_in_the_root_also_judges_the_bound_evidence(self):
        # 自セッションの marker がある root（trusted）でも、steering が対象 PR を記録して
        # いなければ binding の worktree の証跡で判定する（今までは台帳の照合だけで通った）。
        _write_marker_only(self.root, active=True)
        self._gdd_task(approval=False)
        self.assertBlocked(
            self._run(f"gh pr merge 7 -R {REPO} --merge", cwd=self.root), "approval-missing")
        self._gdd_task()
        self.assertAllowed(self._run(f"gh pr merge 7 -R {REPO} --merge", cwd=self.root))

    # --- marker の無い実行先（GDD worktree・root・同じ repo の別 worktree） ----

    def test_merge_in_the_gdd_worktree_judges_its_evidence(self):
        self._gdd_task(approval=False)
        for command, cwd in (
            (f"cd {self.gdd} && gh pr merge 7 -R {REPO} --merge", None),
            (f"gh pr merge 7 -R {REPO} --merge", self.gdd),
            (f"cd {self.root} && gh pr merge 7 --merge", None),
            (f"gh pr merge {URL} --merge", self.launch),
        ):
            with self.subTest(command=command, cwd=cwd):
                self.assertBlocked(self._run(command, cwd=cwd), "approval-missing")
        self._gdd_task()
        for command, cwd in (
            (f"cd {self.gdd} && gh pr merge 7 -R {REPO} --merge", None),
            (f"gh pr merge 7 -R {REPO} --merge", self.gdd),
            (f"cd {self.root} && gh pr merge 7 --merge", None),
        ):
            with self.subTest(command=command, cwd=cwd, evidence=True):
                self.assertAllowed(self._run(command, cwd=cwd))

    def test_unrelated_merges_are_not_affected(self):
        self._gdd_task(approval=False)
        for command in (
            # 別の repo の同じ番号（binding は gh の実行先の repo から引く）。
            f"cd {self.other} && gh pr merge 7 --merge",
            # binding が記録していない PR。
            f"cd {self.root} && gh pr merge 9 -R {REPO} --merge",
            # 別の repo を名指しした同じ番号。
            f"gh pr merge 7 -R acme/other --merge",
        ):
            with self.subTest(command=command):
                self.assertAllowed(self._run(command))

    def test_unreadable_binding_falls_back_to_the_previous_verdict(self):
        # 壊れた binding で hook ごと落ちない（落ちると通知を出せず素通りになる）。
        self._stale_root_marker()
        self._gdd_task()
        (self.root / ".gdd" / "tasks" / TASK / "binding.json").write_text("{not json")
        result = self._run(f"cd {self.root} && gh pr merge 7 -R {REPO} --merge")
        self.assertBlocked(result, "untrusted-root-unverified")

    # --- root の判定材料・remote・通常のファイルでない入力・registry の分かれ方 ---

    @unittest.skipIf(os.geteuid() == 0, "root は chmod(0) のファイルも読める")
    def test_unreadable_root_steering_is_not_overtaken_by_a_binding(self):
        self._stale_root_marker()
        steering = _write_steering(self.root, slug="20260101-locked", pr_url=URL.replace("/7", "/9"))
        (steering / "state.md").chmod(0)
        self.addCleanup((steering / "state.md").chmod, 0o644)
        self._gdd_task()
        result = self._run(f"cd {self.root} && gh pr merge 7 -R {REPO} --merge")
        self.assertBlocked(result, "state-unreadable")

    def test_number_only_merge_is_not_bound_when_gh_may_pick_another_remote(self):
        # gh は origin 以外の remote（upstream など）や GH_REPO を選びうる。そのとき番号だけの
        # merge は、origin の PR の証跡で通過扱いにしない（今までの判定のまま）。
        self._stale_root_marker()
        self._gdd_task()
        git = ["git", "-C", str(self.root)]
        command = f"cd {self.root} && gh pr merge 7 --merge"
        subprocess.run(git + ["remote", "add", "upstream", "https://github.com/up/widgets.git"],
                       check=True)
        with self.subTest(remotes="origin+upstream"):
            self.assertBlocked(self._run(command), "untrusted-root-unverified")
        subprocess.run(git + ["config", "remote.upstream.gh-resolved", "base"], check=True)
        with self.subTest(remotes="upstream is set-default"):
            self.assertBlocked(self._run(command), "untrusted-root-unverified")
        subprocess.run(git + ["config", "--unset", "remote.upstream.gh-resolved"], check=True)
        subprocess.run(git + ["config", "remote.origin.gh-resolved", "base"], check=True)
        with self.subTest(remotes="origin is set-default"):
            self.assertAllowed(self._run(command))
        with self.subTest(env="GH_REPO"):
            result = _run_hook({"tool_input": {"command": command}}, self.launch, self.home,
                               extra_env={"GH_REPO": REPO})
            self.assertBlocked(result, "untrusted-root-unverified")

    def test_fifo_binding_or_state_does_not_hang_the_hook(self):
        # 通常のファイルでない binding・state.md で hook が timeout すると、通知を出せず素通りになる。
        # FIFO の binding は GDD worktree の registry に置く（root の registry の binding は steering の
        # 解決〔scripts/gdd_task_binding.py〕も読むので、そちらの読み方とは切り分ける）。
        self._stale_root_marker()
        state = self.gdd / ".steering" / TASK / "state.md"
        for name, registry in (("binding", self.gdd), ("state", self.root)):
            shutil.rmtree(self.root / ".gdd", ignore_errors=True)
            shutil.rmtree(self.gdd / ".gdd", ignore_errors=True)
            self._gdd_task(root=registry)
            target = registry / ".gdd" / "tasks" / TASK / "binding.json" if name == "binding" else state
            with self.subTest(fifo=name):
                original = target.read_text()
                target.unlink()
                os.mkfifo(target)
                try:
                    result = self._run(f"cd {self.root} && gh pr merge 7 -R {REPO} --merge")
                    self.assertIn('"hookEventName": "PreToolUse"', result.stdout)
                finally:
                    target.unlink()
                    target.write_text(original)

    def _fifo(self, path):
        path.parent.mkdir(parents=True, exist_ok=True)
        os.mkfifo(path)
        self.addCleanup(lambda: path.unlink(missing_ok=True))

    def test_fifo_beside_the_bound_binding_does_not_hang_the_hook(self):
        # 切り替えた後の steering の解決（scripts/gdd_task_binding.py の load_bindings）は、
        # 切り替え先の registry を読む。別の task の binding.json が FIFO でも止まらない。
        self._gdd_task(approval=False, root=self.gdd)
        self._fifo(self.gdd / ".gdd" / "tasks" / "other-task" / "binding.json")
        result = self._run(f"cd {self.root} && gh pr merge 7 -R {REPO} --merge")
        self.assertBlocked(result, "approval-missing")

    def test_fifo_in_the_root_registry_does_not_hang_the_hook(self):
        # root を root のまま判定するとき（stale marker）も、root の registry の FIFO で止まらない。
        self._stale_root_marker()
        self._gdd_task(approval=False)
        self._fifo(self.root / ".gdd" / "tasks" / "other-task" / "binding.json")
        result = self._run(f"cd {self.root} && gh pr merge 7 -R {REPO} --merge")
        self.assertBlocked(result, "approval-missing")

    def test_fifo_marker_at_the_launch_does_not_hang_the_hook(self):
        # 実行先の marker が通常のファイルでないとき、binding で切り替えた後の marker の読みで止まらない。
        self._gdd_task(approval=False)
        self._fifo(self.launch / ".claude" / "gdd-dev.local.md")
        result = self._run(f"gh pr merge 7 -R {REPO} --merge")
        self.assertBlocked(result, "approval-missing")

    def test_undecodable_binding_beside_the_bound_one_does_not_crash_the_resolver(self):
        # UTF-8 でない binding.json は、その 1 件だけを飛ばす（解決全体が失敗すると、binding を
        # 使う hook がそろって fallback に入り、done guard は warn に下がる）。
        self._gdd_task(approval=False, root=self.gdd)
        broken = self.gdd / ".gdd" / "tasks" / "other-task" / "binding.json"
        broken.parent.mkdir(parents=True)
        broken.write_bytes(b"\xff\xfe{")
        bindings = load_plugin_module("scripts/gdd_task_binding.py").load_bindings(self.gdd)
        self.assertEqual([b["task_id"] for b in bindings], [TASK])
        result = self._run(f"cd {self.root} && gh pr merge 7 -R {REPO} --merge")
        self.assertBlocked(result, "approval-missing")

    def _register_gdd_in_ledger(self):
        ledger = self.home / ".claude" / ".gdd-hook-state" / "gdd-pr-roots"
        ledger.parent.mkdir(parents=True, exist_ok=True)
        ledger.write_text(f"{self.gdd}\n")

    def test_backgrounded_cd_to_a_bound_repo_is_not_trusted(self):
        # `cd R & gh pr merge 7`・`cd R | gh pr merge 7` では gh が元の cwd（別の repo）で走るので、
        # R の binding の証跡で通過扱いにしない（cd 先の repo が元の cwd の repo と違う、番号だけの merge）。
        self._gdd_task()
        self._stale_root_marker()
        for op in ("&", "|"):
            with self.subTest(op=op, root="stale marker"):
                result = _run_hook({"tool_input": {"command": f"cd {self.root} {op} gh pr merge 7 --merge"}},
                                   self.other, self.home)
                self.assertBlocked(result, "untrusted-root-unverified")
        (self.root / ".claude" / "gdd-dev.local.md").unlink()
        self._register_gdd_in_ledger()
        for op in ("&", "|"):
            with self.subTest(op=op, root="no marker"):
                result = _run_hook({"tool_input": {"command": f"cd {self.root} {op} gh pr merge 7 --merge"}},
                                   self.other, self.home)
                self.assertBlocked(result, "repo-root-unresolvable")

    def test_backgrounded_cd_within_the_same_repo_still_uses_the_binding(self):
        self._gdd_task(approval=False)
        self.assertBlocked(self._run(f"cd {self.gdd} & gh pr merge 7 --merge"), "approval-missing")

    def test_session_in_another_repo_with_a_marker_uses_the_target_repo_binding(self):
        # marker のある別の repo のセッションから、対象を repo つきで明示して打つ merge も、gh の実行先の
        # repo の binding で判定する（marker の無いセッションから打つときと同じ判定）。
        _write_marker_only(self.other, active=True)
        command = f"cd {self.root} && gh pr merge 7 -R {REPO} --merge"
        self._gdd_task(approval=False)
        self.assertBlocked(_run_hook({"tool_input": {"command": command}}, self.other, self.home),
                           "approval-missing")
        self._gdd_task()
        self.assertAllowed(_run_hook({"tool_input": {"command": command}}, self.other, self.home))

    def test_binding_in_the_gdd_worktree_registry_is_found(self):
        # registry は root checkout と各 worktree に分かれる（`.gdd/` は gitignore）。
        self._stale_root_marker()
        self._gdd_task(approval=False, root=self.gdd)
        result = self._run(f"cd {self.root} && gh pr merge 7 -R {REPO} --merge")
        self.assertBlocked(result, "approval-missing")

    def test_same_steering_bound_twice_is_counted_once(self):
        self._stale_root_marker()
        self._gdd_task()
        _write_binding(self.gdd, self.gdd)
        _write_binding(self.root, self.gdd, task_id="renamed-task")
        self.assertAllowed(self._run(f"cd {self.root} && gh pr merge 7 -R {REPO} --merge"))

    def test_session_in_another_repo_merging_a_bound_pr(self):
        # 別の repo（marker 無し）のセッションから binding のある repo へ cd した merge。対象を repo つきで
        # 明示すれば binding の証跡で判定する。番号だけなら、cd 先で gh が走るかを決められない
        # （`cd X & gh` と同じ扱い）ので binding を引かず、PR 台帳で決まる。
        explicit = f"cd {self.root} && gh pr merge 7 -R {REPO} --merge"
        self._gdd_task()
        self.assertAllowed(_run_hook({"tool_input": {"command": explicit}}, self.other, self.home))
        self._gdd_task(approval=False)
        self.assertBlocked(_run_hook({"tool_input": {"command": explicit}}, self.other, self.home),
                           "approval-missing")
        self._register_gdd_in_ledger()
        result = _run_hook({"tool_input": {"command": f"cd {self.root} && gh pr merge 7 --merge"}},
                           self.other, self.home)
        self.assertBlocked(result, "repo-root-unresolvable")

    def test_launch_worktree_url_merge_allows_with_evidence(self):
        self._gdd_task()
        self.assertAllowed(self._run(f"gh pr merge {URL} --merge"))

    def test_root_recording_another_pr_judges_the_bound_evidence(self):
        # 自セッションの marker がある root の steering が別の PR を記録しているときも、
        # binding の worktree の証跡で判定する。
        _write_marker_only(self.root, active=True)
        _write_steering(self.root, slug="20260101-other", pr_url=URL.replace("/7", "/8"))
        self._gdd_task(approval=False)
        self.assertBlocked(
            self._run(f"gh pr merge 7 -R {REPO} --merge", cwd=self.root), "approval-missing")
        # 切り替えが無ければ、root の PR 8 の steering（証跡なし）で不足として通知される。
        self._gdd_task()
        self.assertAllowed(self._run(f"gh pr merge 7 -R {REPO} --merge", cwd=self.root))


    # --- lookup の分岐（binding の値・対象の読み方・実行先の決め方） -----------

    def _binding_before_the_bound_one(self, **fields):
        # 正しい binding（task_id = TASK）より先に並ぶ binding を、同じ state.md を指して足す。
        path = _write_binding(self.root, self.gdd, task_id="0000-first")
        data = json.loads(path.read_text())
        data.update(fields)
        path.write_text(json.dumps(data))
        return path

    def test_binding_with_a_relative_worktree_before_the_bound_one_does_not_hide_it(self):
        # 同じ state.md を指す binding が先に並んでも、検査に落ちる binding で正しい方を数えから外さない
        # （実測: 同じ state.md を指す binding も、相対の worktree_path も実データにある）。
        # hook の cwd（root）から解決すると同じ worktree になる相対パスで、並び順も正しい binding より先にする。
        self._stale_root_marker()
        self._gdd_task(approval=False)
        self._binding_before_the_bound_one(worktree_path="../gdd")
        result = self._run(f"cd {self.root} && gh pr merge 7 -R {REPO} --merge")
        self.assertBlocked(result, "approval-missing")

    def test_binding_whose_worktree_does_not_hold_the_state_before_the_bound_one(self):
        # worktree が state.md を `.steering/` の下に持たない binding は当たりにしない（その worktree へ
        # 切り替えると、対象 PR の steering を照合できない）。正しい方は数える。
        self._stale_root_marker()
        self._gdd_task(approval=False)
        self._binding_before_the_bound_one(worktree_path=str(self.launch))
        result = self._run(f"cd {self.root} && gh pr merge 7 -R {REPO} --merge")
        self.assertBlocked(result, "approval-missing")

    def test_unencodable_binding_before_the_bound_one_does_not_hide_it(self):
        # 出力できない worktree_path（孤立サロゲート）で列挙全体が止まると、後ろの binding が落ちる。
        self._stale_root_marker()
        self._gdd_task(approval=False)
        path = self._binding_before_the_bound_one()
        path.write_text(path.read_text().replace(json.dumps(str(self.gdd)), '"\\ud800"', 1))
        result = self._run(f"cd {self.root} && gh pr merge 7 -R {REPO} --merge")
        self.assertBlocked(result, "approval-missing")

    def test_binding_with_a_newline_in_the_state_path_is_skipped(self):
        self._stale_root_marker()
        self._gdd_task(approval=False)
        # 名前に改行を含む実ファイルを置く（行に分けて出すと、正しい binding が 2 件目に数えられる）。
        state = self.gdd / ".steering" / TASK / "state.md"
        Path(f"{state}\n").write_text(f"- PR URL: {URL}\n")
        self._binding_before_the_bound_one(state_path=f"{state}\n")
        result = self._run(f"cd {self.root} && gh pr merge 7 -R {REPO} --merge")
        self.assertBlocked(result, "approval-missing")

    def test_binding_is_not_used_when_it_cannot_decide(self):
        # 当たりにできない binding は引かず、今の判定のまま。
        self._stale_root_marker()
        cases = {
            # hook の cwd（root）から解決できる相対パスでも、絶対パスでなければ当たりにしない。
            "relative worktree_path": lambda: self._binding_before_the_bound_one(worktree_path="../gdd"),
            "PR URL longer than the limit": lambda: (
                _write_binding(self.root, self.gdd),
                (self.gdd / ".steering" / TASK / "state.md").write_text(f"- PR URL: {URL}#{'a' * 600}\n")),
        }
        for name, prepare in cases.items():
            with self.subTest(case=name):
                shutil.rmtree(self.root / ".gdd", ignore_errors=True)
                _write_steering(self.gdd, extra_lines=[ln for ln in _valid_evidence_lines(_head_sha(self.gdd))
                                                       if "Merge Approval" not in ln])
                prepare()
                result = self._run(f"cd {self.root} && gh pr merge 7 -R {REPO} --merge")
                self.assertNotIn("approval-missing", result.stdout)
                self.assertBlocked(result, "untrusted-root-unverified")

    def test_merge_whose_target_cannot_be_decided_does_not_use_the_binding(self):
        # 位置引数が 2 つの merge は、gh がどちらを対象にするかを決められない。読めた番号の binding で判定しない。
        self._gdd_task(approval=False)
        result = self._run(f"gh pr merge 8 7 -R {REPO} --merge", cwd=self.gdd)
        self.assertNotIn("approval-missing", result.stdout)

    def test_session_outside_git_is_not_rescued_by_cd_to_the_worktree(self):
        # cwd が git の外のセッションからは、marker の無い GDD worktree へ cd しても root が決まらず、
        # binding を引かない。台帳に載った PR は repo-root-unresolvable のまま。
        self._gdd_task(approval=False)
        self._register_gdd_in_ledger()
        outside = self.tmp / "nogit"
        outside.mkdir()
        result = _run_hook({"tool_input": {"command": f"cd {self.gdd} && gh pr merge 7 -R {REPO} --merge"}},
                           outside, self.home)
        self.assertBlocked(result, "repo-root-unresolvable")

    def _run_with_payload_cwd(self, command, payload_cwd, key="cwd"):
        # payload の cwd（tool_input.cwd、Codex は tool_input.workdir）。プロセスの cwd は別の repo にする。
        return _run_hook({"tool_input": {"command": command, key: str(payload_cwd)}},
                         self.other, self.home)

    def test_payload_cwd_picks_the_repo_to_look_up(self):
        # payload の cwd が gh の実行先。プロセスの cwd が別の repo でも、payload の cwd の repo の
        # binding で判定する。hook は tool_input の cwd と workdir のどちらも読む。
        for key in ("cwd", "workdir"):
            with self.subTest(key=key):
                self._gdd_task(approval=False)
                self.assertBlocked(self._run_with_payload_cwd("gh pr merge 7 --merge", self.gdd, key),
                                   "approval-missing")
                # cd 先は、payload の cwd（プロセスの cwd ではない）と同じ repo のときに実行先として信じる。
                self.assertBlocked(
                    self._run_with_payload_cwd(f"cd {self.gdd} & gh pr merge 7 --merge", self.root, key),
                    "approval-missing")
                self._gdd_task()
                self.assertAllowed(self._run_with_payload_cwd("gh pr merge 7 --merge", self.gdd, key))

    def test_bound_state_outside_the_worktree_steering_keeps_the_root_verdict(self):
        # root の steering に対象 PR が無いとき、`.steering/` の外の state を指す binding では切り替えず、
        # root の判定（別のセッションの marker なので untrusted-root-unverified）のまま。
        self._stale_root_marker()
        for slug, pr in (("20260101-a", 8), ("20260102-b", 9)):
            steering = _write_steering(self.root, slug=slug, pr_url=URL.replace("/7", f"/{pr}"))
            (steering / "state.md").write_text(
                f"## Gate Status\n- Resume From: impl\n- Next Action: impl\n- PR URL: {URL.replace('/7', f'/{pr}')}\n")
        notes = self.gdd / "notes"
        notes.mkdir()
        (notes / "state.md").write_text(f"- PR URL: {URL}\n")
        path = _write_binding(self.root, self.gdd)
        data = json.loads(path.read_text())
        data["state_path"] = str(notes / "state.md")
        path.write_text(json.dumps(data))
        result = self._run(f"cd {self.root} && gh pr merge 7 -R {REPO} --merge")
        self.assertBlocked(result, "untrusted-root-unverified")

    def _outside_state(self, *, approval=False, registry=None, task_id=TASK, resume="done"):
        # `.steering/` の外（notes/）の state を指す binding。
        notes = self.gdd / "notes" / task_id
        notes.mkdir(parents=True)
        lines = _valid_evidence_lines(_head_sha(self.gdd))
        if not approval:
            lines = [ln for ln in lines if "Merge Approval" not in ln]
        (notes / "state.md").write_text(
            f"## Gate Status\n- Resume From: {resume}\n- Next Action: {resume}\n"
            f"- PR URL: {URL}\n" + "\n".join(lines) + "\n")
        path = _write_binding(registry or self.gdd, self.gdd, task_id=task_id)
        data = json.loads(path.read_text())
        data["state_path"] = str(notes / "state.md")
        data["steering_path"] = str(notes)
        data["branch"] = "feat/gdd"
        path.write_text(json.dumps(data))

    def test_worktree_own_binding_outside_steering_still_judges_its_evidence(self):
        # marker の無い GDD worktree で、その worktree の registry の binding が `.steering/` の外の state を
        # 指すときも、その state の証跡で判定する（steering の解決が binding 先を見つける）。
        self._outside_state(resume="gdd-completion-check")
        self.assertBlocked(self._run("gh pr merge 7 --merge", cwd=self.gdd), "approval-missing")

    def test_root_with_its_own_steering_does_not_switch_to_an_outside_state(self):
        # 自セッションの marker がある root が別の PR の steering を持つとき、`.steering/` の外の state を
        # 指す binding へ切り替えない（切り替えると、新しい root で対象 PR の steering を照合できず、
        # 台帳だけで通る）。
        _write_marker_only(self.root, active=True)
        steering = _write_steering(self.root, slug="20260101-a", pr_url=URL.replace("/7", "/8"))
        (steering / "state.md").write_text(
            f"## Gate Status\n- Resume From: impl\n- Next Action: impl\n- PR URL: {URL.replace('/7', '/8')}\n")
        self._outside_state(registry=self.root)
        result = self._run(f"gh pr merge 7 -R {REPO} --merge", cwd=self.root)
        self.assertIn('"hookEventName": "PreToolUse"', result.stdout)

    def test_root_with_its_own_steering_does_not_switch_to_a_non_state_file_in_steering(self):
        # `.steering/<slug>/` の下でも state.md でないファイルを指す binding へは切り替えない（切り替えた後の
        # 求め直しは state.md しか見ないので、steering が見つからず台帳だけで通る）。
        _write_marker_only(self.root, active=True)
        steering = _write_steering(self.root, slug="20260101-a", pr_url=URL.replace("/7", "/8"))
        (steering / "state.md").write_text(
            f"## Gate Status\n- Resume From: impl\n- Next Action: impl\n- PR URL: {URL.replace('/7', '/8')}\n")
        other = self.gdd / ".steering" / TASK / "other.md"
        other.parent.mkdir(parents=True)
        other.write_text(f"- PR URL: {URL}\n")
        path = _write_binding(self.root, self.gdd)
        data = json.loads(path.read_text())
        data["state_path"] = str(other)
        path.write_text(json.dumps(data))
        result = self._run(f"gh pr merge 7 -R {REPO} --merge", cwd=self.root)
        self.assertIn('"hookEventName": "PreToolUse"', result.stdout)

    def test_two_bindings_for_the_same_pr_with_one_outside_are_ambiguous(self):
        self._stale_root_marker()
        self._gdd_task()
        self._outside_state(registry=self.root, task_id="20261011-task")
        result = self._run(f"cd {self.root} && gh pr merge 7 -R {REPO} --merge")
        self.assertBlocked(result, "steering-ambiguous")


if __name__ == "__main__":
    unittest.main()
