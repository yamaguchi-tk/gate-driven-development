"""merge gate: 言い換えた chdir（zsh の `chdir`）。

`cd`・`pushd`・`popd` の語だけを見ていたので、zsh の `chdir` で cwd を変える形を
「chdir が無い」として通していた。
marker の無い git の cwd では、実行先を決められない番号形のマージを台帳と照合でき
ず（unknown）、台帳の PR でも通していた。
"""
from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from _merge_gate_support import _new_repo_with_marker_and_pr, _run_hook
from _paths import PLUGIN_ROOT
from test_merge_gate_hook_non_gdd_merge import _clone_like, _register

sys.path.insert(0, str(PLUGIN_ROOT / "hooks" / "scripts"))
from lib.gh_command_parse import parse_gh_pr_merge  # noqa: E402

M = "gh pr merge 7"


def _parse(command):
    return parse_gh_pr_merge(command, "", "/repo")


class HiddenChdirParseTests(unittest.TestCase):
    def test_chdir_is_an_intent(self):
        for command in (f"chdir /x; {M}", f"builtin chdir /x; {M}"):
            with self.subTest(command=command):
                result = _parse(command)
                self.assertTrue(result["cd_intent"])
                self.assertIsNone(result["cd_target"])

    def test_reading_code_is_not_examined(self):
        # `.`・`source`・`alias` で cwd を変える形は見ない（base と同じ。限界）。
        # 読み込みの語の後でも、先頭の `cd` の先を実行先にする。
        self.assertFalse(_parse(f"source ./env.sh && {M}")["cd_intent"])
        self.assertEqual(_parse(f"cd /W && source ./env.sh && {M}")["cd_target"], "/W")

    def test_cd_with_a_redirection_is_still_the_target(self):
        for command in (f"cd /W >/dev/null && {M}", f"cd /W 2>/dev/null && {M}", f"cd /W && {M}"):
            with self.subTest(command=command):
                self.assertEqual(_parse(command)["cd_target"], "/W")


class UnresolvedTargetLedgerTests(unittest.TestCase):
    """marker の無い git の cwd で、実行先を決められない番号形のマージを番号で台帳と照合する。"""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp()).resolve()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.home = self.tmp / "home"
        (self.home / ".claude").mkdir(parents=True)
        # GDD worktree（PR URL: https://github.com/acme/infra-gdd/pull/7）。
        self.gdd = _new_repo_with_marker_and_pr(self.tmp, "infra-gdd", pr=7, commit=False)
        self.cwd = _clone_like(self.tmp, "other", "https://github.com/acme/other.git")
        _register(self.home, self.gdd)

    def _decision(self, command):
        result = _run_hook({"tool_input": {"command": command}}, self.cwd, self.home)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def test_ledger_number_blocks_when_the_target_is_unresolved(self):
        for command in (
            f"chdir {self.gdd}; gh pr merge 7",
            f"cd {self.gdd} && cd {self.cwd} && gh pr merge 7",
        ):
            with self.subTest(command=command):
                self.assertIn('"hookEventName": "PreToolUse"', self._decision(command))

    def test_cd_into_the_gdd_worktree_before_reading_code_still_gates(self):
        # cd 先の worktree を root にして証跡を見る（marker の無い cwd の経路で通過扱いにしない）。
        for command in (
            f"cd {self.gdd} && source ./env.sh && gh pr merge",
            f"cd {self.gdd} && gh pr merge\n. ./x",
        ):
            with self.subTest(command=command):
                self.assertIn('"hookEventName": "PreToolUse"', self._decision(command))

    def test_other_number_or_explicit_repo_still_passes(self):
        for command in (
            f"chdir {self.gdd}; gh pr merge 8",
            f"chdir {self.gdd}; gh pr merge -R acme/other 7",
            f"chdir {self.gdd}; gh pr merge https://github.com/acme/other/pull/7",
            "gh pr merge 7",
        ):
            with self.subTest(command=command):
                self.assertNotIn('"hookEventName"', self._decision(command))


if __name__ == "__main__":
    unittest.main()
