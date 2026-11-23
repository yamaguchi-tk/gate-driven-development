"""実行先のパスが改行で終わるときに、別 repo を root と同じ repo と見なさない。

`$()` は末尾の改行をすべて落とす。名前が改行で終わるディレクトリ（`<root>\\n`）を
実行先にすると、toplevel や git の共通ディレクトリが root と同じ文字列になり、
AC-18 を通っていた（実データには無い。#268 の独立レビューで見つかった既存の穴）。
"""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from _merge_gate_support import (
    _init_named_repo,
    _run_hook,
    _write_marker_only,
    _write_state,
)

URL = "https://github.com/acme/widgets/pull/7"


def _git(*args):
    subprocess.run(["git", *args], check=True, capture_output=True)


class TrailingNewlineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp()).resolve()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.home = self.tmp / "home"
        (self.home / ".claude").mkdir(parents=True)
        self.launch = _init_named_repo(self.tmp, "launch")
        _write_marker_only(self.launch, active=False)
        # 名前が root の名前 + 改行の別 repo。
        self.other = _init_named_repo(self.tmp, "launch\n")

    def _run(self, command="gh pr merge 7 --merge", cwd=None, process_cwd=None,
             extra_env=None):
        tool_input = {"command": command}
        if cwd is not None:
            tool_input["cwd"] = cwd
        return _run_hook(
            {"tool_input": tool_input}, process_cwd or self.launch, self.home,
            extra_env=extra_env,
        )

    def assertBlocked(self, result, reason="pr-target-unresolvable"):
        self.assertIn('"hookEventName": "PreToolUse"', result.stdout, result.stderr)
        if reason:
            self.assertIn(reason, result.stdout)

    def test_payload_cwd_ending_with_a_newline_blocks(self):
        # payload の値そのものが改行で終わる（抽出の `$()` で落ちる）。
        self.assertBlocked(self._run(cwd=str(self.other)))

    def test_toplevel_ending_with_a_newline_blocks(self):
        # payload の値は改行で終わらず、toplevel だけが改行で終わる（`rev-parse` の
        # `$()` で落ちる）。`/`・`/.` で終わる形は、絶対化の `pwd` の出力が改行で終わる。
        sub = self.other / "sub"
        sub.mkdir()
        for cwd in (str(sub), f"{self.other}/", f"{self.other}/.", f"{sub}/.."):
            with self.subTest(cwd=cwd):
                self.assertBlocked(self._run(cwd=cwd))

    def test_cd_through_a_symlink_to_a_newline_repo_blocks(self):
        # `cd` 先の文字列は改行を含まないが、toplevel が改行で終わる。
        link = self.tmp / "link"
        link.symlink_to(self.other)
        self.assertBlocked(self._run(f"cd {link} && gh pr merge 7 --merge"))
        self.assertBlocked(self._run(cwd=str(link)))

    def test_common_dir_ending_with_a_newline_blocks(self):
        # root と、共通ディレクトリの名前が root のもの + 改行の別 repo の worktree。
        # 共通ディレクトリの一致（同じ repo の別 worktree として通す条件）を
        # 末尾の改行で満たさない。
        src = _init_named_repo(self.tmp, "src")
        bare, bare_nl = self.tmp / "r.git", self.tmp / "r.git\n"
        for path in (bare, bare_nl):
            _git("clone", "-q", "--bare", str(src), str(path))
        root, sibling = self.tmp / "wt-root", self.tmp / "wt-other"
        _git("-C", str(bare), "worktree", "add", "-q", "-b", "a", str(root))
        _git("-C", str(bare_nl), "worktree", "add", "-q", "-b", "b", str(sibling))
        _write_marker_only(root, active=False)
        for command, cwd in (
            (f"cd {sibling} && gh pr merge 7 --merge", None),
            ("gh pr merge 7 --merge", str(sibling)),
        ):
            with self.subTest(command=command, cwd=cwd):
                self.assertBlocked(self._run(command, cwd=cwd, process_cwd=root))

    def test_non_string_payload_cwd_still_blocks(self):
        # 文字列でない cwd は、値が消えて signal が無くなる形にしない。
        for cwd in (123, ["/x"], True):
            with self.subTest(cwd=cwd):
                self.assertBlocked(self._run(cwd=cwd))

    def test_newline_inside_the_path_keeps_the_current_verdicts(self):
        # 途中の改行は今どおり採り、今不足として通知される形を通さない。
        root_checkout = _init_named_repo(self.tmp, "plain")
        dedicated = self.tmp / "dedi"
        _git("-C", str(root_checkout), "worktree", "add", "-q", "-b", "w",
             str(dedicated))
        _write_state(dedicated, active=False, pr_url=URL)
        inner = dedicated / "a\nb"
        inner.mkdir()
        # marker の無い root checkout から、marker と PR 7 の steering を持つ
        # worktree の、途中に改行のあるサブディレクトリを指す。
        self.assertBlocked(
            self._run(cwd=str(inner), process_cwd=root_checkout), "approval-missing",
        )
        # toplevel の途中に改行がある、marker を持つ worktree。
        tricky = self.tmp / "d\nx"
        _git("-C", str(root_checkout), "worktree", "add", "-q", "-b", "t", str(tricky))
        _write_state(tricky, active=False, pr_url=URL)
        result = self._run(cwd=str(tricky), process_cwd=root_checkout)
        self.assertIn('"hookEventName": "PreToolUse"', result.stdout, result.stderr)

    def test_unreadable_toplevel_blocks(self):
        # 判定できないとき: toplevel を取る呼び出しが失敗する・末尾の改行を出さない
        # git では、実行先を解決できないものとみなして不足として通知する（shim はプロセス cwd にも
        # 効くので、reason は root を解決できない側になる）。
        shim = self.tmp / "shim"
        shim.mkdir()
        real_git = shutil.which("git")
        sibling = self.tmp / "sib"
        _git("-C", str(self.launch), "worktree", "add", "-q", "-b", "s", str(sibling))
        cases = {
            "failing": 'for a in "$@"; do [ "$a" = --show-toplevel ] && exit 128; done\n',
            "no-newline": (
                'for a in "$@"; do [ "$a" = --show-toplevel ] && {\n'
                f'  printf %s "$("{real_git}" "$@")"; exit 0; }}; done\n'
            ),
        }
        for name, body in cases.items():
            with self.subTest(shim=name):
                (shim / "git").write_text(f'#!/bin/bash\n{body}exec "{real_git}" "$@"\n')
                (shim / "git").chmod(0o755)
                env = {"PATH": f"{shim}{os.pathsep}{os.environ['PATH']}"}
                self.assertBlocked(self._run(cwd=str(sibling), extra_env=env), None)

    def test_newline_gdd_worktree_from_a_session_without_a_marker_blocks(self):
        # marker の無い root checkout から、名前が改行で終わる GDD の worktree
        # （marker と PR 7 の steering、承認なし）を指す。改行を落とした同名の
        # worktree がある形・無い形の両方で、台帳の照合に頼らず不足として通知する。
        root_checkout = _init_named_repo(self.tmp, "plain")
        target = self.tmp / "gdd\n"
        _git("-C", str(root_checkout), "worktree", "add", "-q", "-b", "g", str(target))
        _write_state(target, active=False, pr_url=URL)
        link = self.tmp / "gdd-link"
        link.symlink_to(target)
        forms = (
            ("gh pr merge 7 --merge", str(target)),
            (f"cd {link} && gh pr merge 7 --merge", None),
        )
        for twin in (False, True):
            if twin:
                _git("-C", str(root_checkout), "worktree", "add", "-q", "-b", "h",
                     str(self.tmp / "gdd"))
                _write_state(self.tmp / "gdd", active=False, pr_url=URL)
            for command, cwd in forms:
                with self.subTest(twin=twin, command=command):
                    self.assertBlocked(
                        self._run(command, cwd=cwd, process_cwd=root_checkout),
                    )

    def test_degraded_merge_toward_a_newline_gdd_worktree_blocks(self):
        # merge かを判定できない（解析が縮退する）コマンドでも、改行で終わる実行先は
        # 素通りさせない。
        root_checkout = _init_named_repo(self.tmp, "plain")
        target = self.tmp / "gdd\n"
        _git("-C", str(root_checkout), "worktree", "add", "-q", "-b", "g", str(target))
        _write_state(target, active=False, pr_url=URL)
        result = self._run(
            "x=$'\\'' ;gh pr merge 7 --merge", cwd=str(target), process_cwd=root_checkout,
        )
        self.assertBlocked(result, None)

    def test_process_cwd_ending_with_a_newline_blocks(self):
        # プロセス cwd の取得（`$(pwd)`）でも末尾の改行を落とさない。
        self.assertBlocked(self._run(process_cwd=self.other))

    def test_cd_target_with_a_control_character_blocks(self):
        # parser の出力は改行・タブを空白に置き換える。`cd` 先が制御文字を含むと、
        # 照合するパス（空白入り）と実際に移る先が別になる。照合するパスを root の
        # 中に置き、実際の移動先を別 repo への symlink にする。
        for matched, real, command in (
            ("sub ", "sub\n", f'cd "{self.launch}/sub\n" && gh pr merge 7 --merge'),
            ("a b", "ab", f"cd {self.launch}/a\\\nb && gh pr merge 7 --merge"),
            ("t b", "t\tb", f'cd "{self.launch}/t\tb" && gh pr merge 7 --merge'),
        ):
            with self.subTest(command=command):
                (self.launch / matched).mkdir()
                (self.launch / real).symlink_to(self.other)
                self.assertBlocked(self._run(command))

    def test_payload_cwd_in_the_root_itself_still_allows(self):
        # 対照: 改行を含まない同じ root を指す形は今までどおり通す。
        result = self._run(cwd=str(self.launch))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "")


if __name__ == "__main__":
    unittest.main()
