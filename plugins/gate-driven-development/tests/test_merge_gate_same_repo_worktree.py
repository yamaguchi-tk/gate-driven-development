"""AC-18 の照合: 同じ repo の別 worktree・root checkout への `cd` を別 repo と誤認しない。

worktree 同士は remote 設定（`gh` が対象 repo を決める材料）を共有するので、git の
共通ディレクトリが同じなら、通常は `gh` の対象 repo も同じになる。toplevel だけで比べると、
launch worktree のセッションから root checkout や GDD の専用 worktree へ `cd` した
merge が `pr-target-unresolvable` で不足と判定されていた（2026-09-29〜10-01 の実データで
merge の deny の主な原因の一つだった。当時の merge gate は deny していた）。
"""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from _merge_gate_support import (
    _head_sha,
    _init_named_repo,
    _run_hook,
    _valid_evidence_lines,
    _write_marker_only,
    _write_state,
    _write_two_done_steerings,
)
from test_merge_gate_hook_non_gdd_merge import _ledger, _register

URL = "https://github.com/acme/widgets/pull/7"


class SameRepoWorktreeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp()).resolve()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.home = self.tmp / "home"
        (self.home / ".claude").mkdir(parents=True)
        # root checkout（marker なし）と、そこから作った launch worktree（marker あり・
        # steering なし。Claude Code desktop の worktree セッションと同じ形）。
        self.root = _init_named_repo(self.tmp, "root")
        subprocess.run(
            ["git", "-C", str(self.root), "remote", "add", "origin",
             "https://github.com/acme/widgets.git"], check=True,
        )
        self.launch = self._add_worktree("launch")
        _write_marker_only(self.launch, active=False)
        self.other = _init_named_repo(self.tmp, "other")

    def _add_worktree(self, name, branch=None):
        path = self.tmp / name
        subprocess.run(
            ["git", "-C", str(self.root), "worktree", "add", "-q", "-b", branch or name,
             str(path)],
            check=True,
        )
        return path

    def _run(self, command, extra_env=None, cwd=None):
        tool_input = {"command": command}
        if cwd is not None:
            tool_input["cwd"] = str(cwd)
        return _run_hook(
            {"tool_input": tool_input}, self.launch, self.home, extra_env=extra_env,
        )

    def assertAllowed(self, result):
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "")

    def assertBlocked(self, result, reason):
        self.assertIn('"hookEventName": "PreToolUse"', result.stdout)
        self.assertIn(reason, result.stdout)

    def test_control_merge_in_the_launch_worktree_allows(self):
        self.assertAllowed(self._run(f"gh pr merge {URL} --merge"))

    def test_cd_to_the_root_checkout_with_an_explicit_pr_allows(self):
        for target in ("7", URL):
            with self.subTest(target=target):
                self.assertAllowed(
                    self._run(f"cd {self.root} && gh pr merge {target} --merge")
                )

    def test_cd_to_a_sibling_worktree_without_a_marker_allows(self):
        sibling = self._add_worktree("sibling")
        self.assertAllowed(self._run(f"cd {sibling} && gh pr merge 7 --merge"))
        # 実行先を `cd` ではなく payload の tool_input.cwd で渡す（Codex の tool_input.workdir は
        # test_merge_gate_binding_steering.py が送る）。
        self.assertAllowed(self._run("gh pr merge 7 --merge", cwd=sibling))

    def test_cd_to_another_repo_still_blocks(self):
        result = self._run(f"cd {self.other} && gh pr merge 7 --merge")
        self.assertIn('"hookEventName": "PreToolUse"', result.stdout)
        self.assertIn("pr-target-unresolvable", result.stdout)

    def test_merge_without_an_explicit_pr_still_blocks(self):
        # 対象 PR を省いた merge は、cd 先のブランチの PR を gh が選ぶ。root の
        # steering の PR と同じとは言えないので、toplevel の一致だけで通す。
        result = self._run(f"cd {self.root} && gh pr merge --merge")
        self.assertIn('"hookEventName": "PreToolUse"', result.stdout)
        self.assertIn("pr-target-unresolvable", result.stdout)

    def _dedicated_worktree(self, *, evidence):
        """GDD の専用 worktree（marker + PR 7 の steering）。evidence=False は証跡なし。"""
        dedicated = self._add_worktree("dedicated")
        extra = _valid_evidence_lines(_head_sha(dedicated)) if evidence else ()
        _write_state(dedicated, active=False, extra_lines=extra, pr_url=URL)
        return dedicated

    def test_cd_to_a_dedicated_worktree_with_evidence_allows(self):
        dedicated = self._dedicated_worktree(evidence=True)
        self.assertAllowed(self._run(f"cd {dedicated} && gh pr merge 7 --merge"))

    def test_cd_to_a_dedicated_worktree_judges_its_evidence(self):
        # cd 先を root にしたので、証跡が無ければそこで不足として通知される（素通りしない）。
        dedicated = self._dedicated_worktree(evidence=False)
        result = self._run(f"cd {dedicated} && gh pr merge 7 --merge")
        self.assertIn('"hookEventName": "PreToolUse"', result.stdout)
        self.assertNotIn("pr-target-unresolvable", result.stdout)

    def test_payload_cwd_pointing_at_a_dedicated_worktree_still_blocks(self):
        # root は `cd` 先にだけ切り替わる。payload の cwd が marker のある同じ repo の
        # worktree を指すときは、そこの証跡を見ずに通さず不足として通知する（番号だけの merge。対象を
        # repo つきで明示した merge は test_merge_gate_explicit_target.py で見る）。
        dedicated = self._dedicated_worktree(evidence=False)
        result = self._run("gh pr merge 7 --merge", cwd=dedicated)
        self.assertBlocked(result, "pr-target-unresolvable")

    def test_toplevel_with_a_newline_is_not_cut_at_the_newline(self):
        # 改行を含む worktree の toplevel を最初の改行で切ると、root と同じ文字列に
        # なって AC-18 を通ってしまう。
        tricky = self._add_worktree("launch\nx", branch="tricky")
        result = self._run("gh pr merge 7 --merge", cwd=tricky)
        self.assertBlocked(result, "pr-target-unresolvable")

    def test_cd_to_the_root_checkout_still_checks_the_pr_ledger(self):
        # marker の無い実行先を共通ディレクトリで通した merge も、root checkout で
        # 直接打ったときと同じく、GDD の PR 台帳に載った PR なら不足として通知する。
        dedicated = self._dedicated_worktree(evidence=False)
        _register(self.home, dedicated)
        for command, cwd in (
            (f"cd {self.root} && gh pr merge 7 --merge", None),
            ("gh pr merge 7 --merge", self.root),
        ):
            with self.subTest(command=command, cwd=cwd):
                self.assertBlocked(self._run(command, cwd=cwd), "repo-root-unresolvable")

    def test_ledger_verdicts_other_than_miss_block_via_the_common_dir(self):
        # 共通ディレクトリで通した経路は、台帳の照合が miss のときだけ通す。対象 PR を
        # 特定できない（unknown）・台帳を読めない（unreadable）ときは不足として通知する。素通りの
        # exit はセッションの steering の形で 3 つある（無い・別の PR を 1 件・複数件）。
        dedicated = self._dedicated_worktree(evidence=False)
        command = f"cd {self.root} && gh pr merge 8 --merge"
        for name, write in (
            ("none", lambda: None),
            ("one", lambda: _write_state(
                self.launch, active=False, pr_url=URL.replace("/7", "/9"))),
            ("many", lambda: _write_two_done_steerings(self.launch)),
        ):
            shutil.rmtree(self.launch / ".steering", ignore_errors=True)
            write()
            ledger = _ledger(self.home)
            if ledger.is_dir():
                ledger.rmdir()
            _register(self.home, dedicated)
            with self.subTest(steerings=name, verdict="miss"):
                self.assertAllowed(self._run(command))
            with self.subTest(steerings=name, verdict="unknown"):
                result = self._run(command, extra_env={"GH_REPO": "acme/other"})
                self.assertBlocked(result, "repo-root-unresolvable")
            with self.subTest(steerings=name, verdict="unreadable"):
                ledger.unlink()
                ledger.mkdir()
                self.assertBlocked(self._run(command), "repo-root-unresolvable")

    def test_ledger_is_checked_when_the_session_records_other_prs(self):
        # セッションの steering が別の PR を記録している素通りの exit（1 件・複数件）
        # でも照合する。
        dedicated = self._dedicated_worktree(evidence=False)
        _register(self.home, dedicated)
        for name, write in (
            ("one", lambda: _write_state(
                self.launch, active=False, pr_url=URL.replace("/7", "/9"))),
            ("many", lambda: _write_two_done_steerings(self.launch)),
        ):
            with self.subTest(steerings=name):
                shutil.rmtree(self.launch / ".steering", ignore_errors=True)
                write()
                result = self._run(f"cd {self.root} && gh pr merge 7 --merge")
                self.assertBlocked(result, "repo-root-unresolvable")

    def test_own_pr_in_the_ledger_still_allows_via_the_root_checkout(self):
        # セッションの worktree が対象 PR の証跡を持つなら、自分が台帳に載って
        # いても不足として通知しない（台帳は steering に対象 PR が無いときだけ引く）。
        _write_state(
            self.launch, active=False, pr_url=URL,
            extra_lines=_valid_evidence_lines(_head_sha(self.launch)),
        )
        _register(self.home, self.launch)
        self.assertAllowed(self._run(f"cd {self.root} && gh pr merge 7 --merge"))

    def test_dedicated_worktree_does_not_take_over_unsafe_forms(self):
        # 証跡がそろった worktree でも、gh がプロセス cwd で走りうる無引数形と、
        # 別 repo を指す形は通さない（不足として通知する）。
        dedicated = self._dedicated_worktree(evidence=True)
        for command in (
            f"cd {dedicated} & gh pr merge --merge",
            f"cd {dedicated} && gh pr merge --merge",
            f"cd {dedicated} && gh pr merge -R evil/other 7 --merge",
            f"cd {dedicated} && gh pr merge https://github.com/evil/other/pull/7",
        ):
            with self.subTest(command=command):
                result = self._run(command)
                self.assertIn('"hookEventName": "PreToolUse"', result.stdout)

    def test_unreadable_common_dir_blocks(self):
        # fail-open 側: 共通ディレクトリを読めない（git が古い・失敗する）ときは
        # 不一致に倒す。古い git は未知の `--path-format=absolute` をそのまま出力し、
        # 共通ディレクトリを相対パスで返す（行の位置で読むと全候補が同じ値になる）。
        shim = self.tmp / "shim"
        shim.mkdir()
        real_git = shutil.which("git")
        cases = {
            # 古い git: toplevel は取れるので、共通ディレクトリだけが読めない経路。
            "old-git": (
                'for a in "$@"; do [ "$a" = --git-common-dir ] && {\n'
                f'  "{real_git}" "${{@:1:$#-2}}" 2>/dev/null | head -1\n'
                "  echo --path-format=absolute; echo .git; exit 0; }; done\n",
                "pr-target-unresolvable",
            ),
            # 共通ディレクトリを取る呼び出しが失敗する経路。toplevel は単独の
            # 呼び出しで取り直すので、root は決まり、照合は不一致で不足として通知される。
            "failing": (
                'for a in "$@"; do [ "$a" = --git-common-dir ] && exit 128; done\n',
                "pr-target-unresolvable",
            ),
        }
        for name, (body, reason) in cases.items():
            with self.subTest(shim=name):
                (shim / "git").write_text(
                    f'#!/bin/bash\n{body}exec "{real_git}" "$@"\n'
                )
                (shim / "git").chmod(0o755)
                env = {"PATH": f"{shim}{os.pathsep}{os.environ['PATH']}"}
                result = self._run(f"cd {self.root} && gh pr merge 7 --merge", env)
                self.assertBlocked(result, reason)


if __name__ == "__main__":
    unittest.main()
