"""pre-PR gate は、コマンドの解析の結果を 1 回の python3 で key/value として受け取る。

解析の python3 が出した JSON を、欄ごとに別の python3 で読み直していた（PR 作成の
コマンド 1 回で 13 回）。cwd の展開と本文の機密検査も、解析と同じ python3 で行う。
"""
from __future__ import annotations

import os
import shutil
import tempfile
import unittest
from pathlib import Path

from _paths import PLUGIN_ROOT
import test_pre_pr_gate_contract as contract


def _helpers() -> contract.PrePrGateContractTests:
    """既存の fixture の作り方を借りる（継承すると unittest が契約テストを二重に走らせる）。"""
    return contract.PrePrGateContractTests("run")


class _ActiveRepo(unittest.TestCase):
    def setUp(self) -> None:
        self.h = _helpers()
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.repo = self.root / "repo"
        self.repo.mkdir()
        self.h._init_repo(self.repo)
        self.h._write_local_state(self.repo)
        self.h._write_steering(self.repo)

    def assertBlocked(self, result, words: str) -> None:
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('"hookEventName": "PreToolUse"', result.stdout)
        self.assertIn(words, result.stdout)


class PythonLaunchCountTests(_ActiveRepo):
    def _count(self, command: str) -> int:
        real = shutil.which("python3")
        shim = self.root / "shim"
        shim.mkdir(exist_ok=True)
        log = self.root / "python3.log"
        log.write_text("", encoding="utf-8")
        wrapper = shim / "python3"
        wrapper.write_text(f'#!/bin/sh\necho x >> "{log}"\nexec "{real}" "$@"\n', encoding="utf-8")
        wrapper.chmod(0o755)
        result = self.h._run_hook(
            self.repo, command, extra_env={"PATH": f"{shim}{os.pathsep}{os.environ['PATH']}"}
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return len(log.read_text(encoding="utf-8").splitlines())

    def test_non_pr_command_runs_python_once(self) -> None:
        self.assertEqual(self._count("ls create"), 1)

    def test_pr_create_does_not_reread_the_parse_result(self) -> None:
        # 変更の前は 18 回（読み直し 13 回を含む）。
        self.assertLessEqual(self._count("gh pr create --title t --body ok"), 5)


class BodyCheckTests(_ActiveRepo):
    """fail-open ケース「不足として通知すべき入力が allow になる」。"""

    def test_nul_between_digits_is_still_found(self) -> None:
        body = self.root / "body.md"
        body.write_bytes(b"acct 123456\x00789012\n")
        result = self.h._run_hook(self.repo, f"gh pr create --title t --body-file {body}")
        self.assertBlocked(result, "12桁")

    def test_label_and_value_across_a_newline_are_found(self) -> None:
        body = self.root / "body.md"
        body.write_text("password\n= hunter22\n", encoding="utf-8")
        result = self.h._run_hook(self.repo, f"gh pr create --title t --body-file {body}")
        self.assertBlocked(result, "token/key/password")

    def test_lone_surrogate_does_not_empty_the_body(self) -> None:
        # 変更の前は、本文を bash に渡すときの符号化で落ち、本文が空として検査を通っていた。
        result = self.h._run_hook(self.repo, "gh pr create --title t --body 'x\ud800 password=abc'")
        self.assertBlocked(result, "token/key/password")

    def test_lone_surrogate_does_not_skip_the_head_check(self) -> None:
        result = self.h._run_hook(self.repo, "gh pr create --title t --body ok --head other\ud800")
        self.assertBlocked(result, "--head")


class ParseFailureTests(unittest.TestCase):
    """fail-open ケース「例外で guard 全体が落ちる」「判定できないときに通ってしまう」。"""

    def _run_with_lib(self, lib_tail: str):
        h = _helpers()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / "repo"
            repo.mkdir()
            h._init_repo(repo)
            h._write_local_state(repo)
            h._write_steering(repo)
            hooks = root / "plugin" / "hooks"
            shutil.copytree(PLUGIN_ROOT / "hooks", hooks)
            lib = hooks / "scripts" / "lib" / "gh_command_parse.py"
            lib.write_text(lib.read_text(encoding="utf-8") + lib_tail, encoding="utf-8")
            original = contract.HOOK
            contract.HOOK = hooks / "scripts" / "run-pre-pr-gate-hook.sh"
            try:
                return h._run_hook(repo, "gh pr create --title t --body ok")
            finally:
                contract.HOOK = original

    def test_exception_during_the_parse_blocks(self) -> None:
        result = self._run_with_lib(
            "\ndef _find_sub_command(*args, **kwargs):\n    raise RuntimeError(\"boom\")\n"
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('"hookEventName": "PreToolUse"', result.stdout)
        self.assertIn("gh_command_parse", result.stdout)

    def test_parse_that_ends_without_a_result_blocks(self) -> None:
        # 0 で終わっても、最後の parsed が届かなければ判定できないものとして不足として通知する。
        result = self._run_with_lib(
            "\ndef _find_sub_command(*args, **kwargs):\n    raise SystemExit(0)\n"
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('"hookEventName": "PreToolUse"', result.stdout)
        self.assertIn("gh_command_parse", result.stdout)


if __name__ == "__main__":
    unittest.main()
