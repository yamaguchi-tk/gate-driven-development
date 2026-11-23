"""merge gate: 連結した `gh pr merge` も、読めた番号・URL を merge ごとに台帳と照合する（Issue #438）。

1 回の Bash に `gh pr merge` が 2 つ以上あると、parser は対象を決められないとして番号・URL を
空にする。marker の無い checkout の経路は台帳に当たったときだけ不足として通知するので、照合する番号が無いと
unknown として通っていた。parser は merge ごとの組（`-R` の値・番号・URL）を `ledger_targets` に
集め、hook は番号・URL が読めないときにその組で照合する。
"""
from __future__ import annotations

import sys
import unittest

from _merge_gate_support import PLUGIN_ROOT, _write_marker_only, _write_state
from _timing_budget import timing_budget
from test_merge_gate_hook_non_gdd_merge import _clone_like, _register
from test_merge_gate_ledger_fail_closed import HANG_GUARD, HOOK_TIMEOUT, _LedgerCase, _hook, _is_block, _is_pass

sys.path.insert(0, str(PLUGIN_ROOT / "hooks" / "scripts"))
from lib.gh_command_parse import parse_gh_pr_merge  # noqa: E402


class ParserLedgerTargetsTests(unittest.TestCase):
    def test_targets_are_collected_per_merge(self):
        result = parse_gh_pr_merge("gh pr merge -R a/x 7 && gh pr merge 8", "", "/repo")
        self.assertEqual(result["ledger_targets"], [("a/x", "7", None), (None, "8", None)])
        # 1 つの result の値は今までどおり（番号は空、-R は読めた値）。
        self.assertIsNone(result["pr_number"])
        self.assertEqual(result["repo_flag"], "a/x")

    def test_repo_flag_before_pr_belongs_to_its_merge(self):
        result = parse_gh_pr_merge("gh -R a/x pr merge 7 && gh pr merge -R b/y 8", "", "/repo")
        self.assertEqual(result["ledger_targets"], [("a/x", "7", None), ("b/y", "8", None)])

    def test_nested_shell_merge_is_collected(self):
        result = parse_gh_pr_merge("gh pr merge 7 && bash -c 'gh pr merge 8'", "", "/repo")
        self.assertEqual(sorted(t[1] for t in result["ledger_targets"]), ["7", "8"])

    def test_single_merge_keeps_result_unchanged(self):
        result = parse_gh_pr_merge("gh pr merge -R a/x 7", "", "/repo")
        self.assertEqual(result["ledger_targets"], [("a/x", "7", None)])
        self.assertEqual((result["pr_number"], result["repo_flag"]), ("7", "a/x"))


class ChainedMergeFromCheckoutTests(_LedgerCase):
    """marker の無い root checkout（git cwd の経路。hit だけ不足として通知する）。台帳の PR は acme/infra-gdd#7。"""

    def setUp(self):
        super().setUp()
        _register(self.home, self.gdd)

    def test_chained_merge_with_ledger_pr_is_blocked(self):
        for command in (
            "gh pr merge 6 --squash && gh pr merge 7 --squash",
            "gh pr merge 7 --squash && gh pr merge 6 --squash",
            "gh pr merge 6; gh pr merge https://github.com/acme/infra-gdd/pull/7",
            "gh pr merge 6 && bash -c 'gh pr merge 7'",
            "gh -R acme/infra-gdd pr merge 7 && gh pr merge 6",
            "gh pr merge 6 && gh pr merge 8 && gh pr merge 7",
            # 区切り文字（\x1e・\x1f）を値に含めても、組がずれて hook が落ちたり台帳の PR を外したりしない。
            "gh pr merge -R 'a\x1fb' 6 && gh pr merge 7",
            "gh pr merge -R 'a\x1e9\x1fz' 6 && gh pr merge 7",
            "gh pr merge -R 'acme/other\x1f7\x1f\x1eacme/other' 7 && gh pr merge 5",
            # 改行で区切った merge は 1 本の merge（位置引数 2 つ以上）として読まれる。番号は全部、番号だけで照合する。
            "gh pr merge 7 --squash\ngh pr merge 6 --squash",
            "gh pr merge 6 --repo acme/other\ngh pr merge 7",
            "gh pr merge https://github.com/acme/infra-gdd/pull/7\ngh pr merge 6",
            # slash の無い未展開の -R は repo を決められない。番号だけで照合する。
            'gh pr merge -R "$R" 7',
            'gh pr merge -R "$R" 6 && gh pr merge -R "$R" 7',
        ):
            with self.subTest(command=command):
                result = self._from_checkout(command)
                self.assertTrue(_is_block(result), result.stdout + result.stderr)

    def test_chained_merge_without_ledger_pr_passes(self):
        for command in (
            "gh pr merge 5 && gh pr merge 6",
            # merge ごとの -R で組む。7 を acme/infra-gdd と組み違えない。
            "gh pr merge -R other/x 7 && gh pr merge -R acme/infra-gdd 8",
        ):
            with self.subTest(command=command):
                result = self._from_checkout(command)
                self.assertTrue(_is_pass(result), result.stdout + result.stderr)

    def test_cd_between_merges_matches_number_only(self):
        # cd が merge の間に入ると実行先を決められない。-R の無い番号は番号だけで照合する
        # （実行先の origin は別 repo なので、origin で組むと外れる）。
        unrelated = _clone_like(self.tmp, "unrelated", "https://github.com/acme/unrelated.git")
        result = _hook(f"gh pr merge 6 && cd {self.non_repo} && gh pr merge 7", unrelated, self.home)
        self.assertTrue(_is_block(result), result.stdout + result.stderr)

    def test_leading_cd_pairs_with_cd_target_origin(self):
        # 先頭の cd は全部の merge の実行先になる。cd 先の origin で組む。
        unrelated = _clone_like(self.tmp, "unrelated", "https://github.com/acme/unrelated.git")
        blocked = _hook(f"cd {self.checkout} && gh pr merge 6 && gh pr merge 7", unrelated, self.home)
        self.assertTrue(_is_block(blocked), blocked.stdout + blocked.stderr)
        passed = self._from_checkout(f"cd {unrelated} && gh pr merge 7 && gh pr merge 6")
        self.assertTrue(_is_pass(passed), passed.stdout + passed.stderr)

    def test_long_values_do_not_time_out(self):
        # 長い値で展開が 2 乗に効くと timeout で通る（hooks.json の timeout 10 秒）。
        long_url = "https://github.com/acme/" + "x" * 400_000 + "/pull/7"
        for cwd, command in (
            (self.non_repo, "gh pr merge -R " + "a" * 400_000 + " 1 && gh pr merge -R acme/infra-gdd 7"),
            (self.checkout, "gh pr merge 5 && gh pr merge " + long_url),
            (self.checkout, " && ".join(["gh pr merge 5"] * 2000) + " && gh pr merge 7"),
        ):
            with self.subTest(cwd=cwd.name, size=len(command)):
                with timing_budget() as timing:
                    result = _hook(command, cwd, self.home, timeout=HANG_GUARD)
                self.assertTrue(_is_block(result), result.stdout[:500])
                self.assertLess(timing.cpu_seconds, HOOK_TIMEOUT, f"wall {timing.wall_seconds:.2f}s")

    def test_zsh_multi_digit_fd_number_is_matched(self):
        # Issue #438 の 2 つ目の形（zsh は `12` を番号、bash は fd と読む）。連結した形も zsh の読みの組で照合する。
        _write_state(self.gdd, active=False, pr_url="https://github.com/acme/infra-gdd/pull/12")
        for command in ("gh pr merge 12>/tmp/x", "gh pr merge 5 && gh pr merge 12>/tmp/x"):
            with self.subTest(command=command):
                result = self._from_checkout(command)
                self.assertTrue(_is_block(result), result.stdout + result.stderr)

    def test_from_non_git_cwd_stays_blocked(self):
        # root 未解決の経路は miss だけ通す。連結 merge は unknown のままで、今までどおり不足として通知する。
        result = self._from_non_git("gh pr merge -R acme/infra-gdd 5 && gh pr merge -R acme/infra-gdd 6")
        self.assertTrue(_is_block(result), result.stdout + result.stderr)


class ChainedMergeAtExitTests(_LedgerCase):
    """marker はあるが steering が無い checkout の素通りの出口（`_mg_ledger_check_at_exit`）。"""

    def test_chained_merge_with_ledger_pr_is_blocked_at_exit(self):
        _register(self.home, self.gdd)
        _write_marker_only(self.checkout, active=True)
        result = self._from_checkout("gh pr merge 6 && gh pr merge 7")
        self.assertTrue(_is_block(result), result.stdout + result.stderr)
        self.assertTrue(_is_pass(self._from_checkout("gh pr merge 5 && gh pr merge 6")))


if __name__ == "__main__":
    unittest.main()
