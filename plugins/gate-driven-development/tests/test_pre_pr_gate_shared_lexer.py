"""pre-PR gate は、merge gate と同じ字句解析（lib/gh_command_parse.py）で PR 作成を探す。

埋め込みの python が持っていた字句解析の写しは、merge gate の版より古く、語の途中の `#`
（`fix#12`）から後ろをコメントとして捨て、`bash <<EOF` の本文も落としていた。どちらも
bash は後ろの `gh pr create` を実行する。
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from _paths import PLUGIN_ROOT
import test_pre_pr_gate_contract as contract

sys.path.insert(0, str(PLUGIN_ROOT / "hooks" / "scripts"))
from lib.gh_command_parse import _split_multi_digit_fd, _tokenize, parse_gh_pr_merge  # noqa: E402


def _helpers() -> contract.PrePrGateContractTests:
    """既存の fixture の作り方を借りる（継承すると unittest が契約テストを二重に走らせる）。"""
    return contract.PrePrGateContractTests("run")


# 旧の写しが見落とし、bash は `gh pr create` を実行する形。
MISSED_BY_THE_OLD_COPY = {
    "word-internal-hash": "echo fix#12; gh pr create --title t --body ok",
    "heredoc-fed-to-bash": "bash <<EOF\ngh pr create --title t --body ok\nEOF",
}


class PrePrGateSharedLexerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.h = _helpers()
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.repo = Path(tmp.name)
        self.h._init_repo(self.repo)
        self.h._write_local_state(self.repo)
        self.h._write_steering(self.repo, next_action="gdd-completion-check")

    def test_forms_the_old_copy_missed_are_blocked(self) -> None:
        # fail-open ケース「不足として通知すべき入力が allow になる」。
        for label, command in MISSED_BY_THE_OLD_COPY.items():
            with self.subTest(form=label):
                result = self.h._run_hook(self.repo, command)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn('"hookEventName": "PreToolUse"', result.stdout)
                self.assertIn("Next Action=gdd-completion-check", result.stdout)

    def test_pr_create_found_past_redirects_and_flags(self) -> None:
        # fail-open ケース「不足として通知すべき入力が allow になる」: gh は sub-command の前後の
        # リダイレクトと flag を読み飛ばして `pr create` を実行する（merge gate と同じ探し方）。
        for command in (
            "gh 2>/dev/null pr create --title t --body ok",
            "gh pr -R o/r create --title t --body ok",
            "gh pr --repo o/r new --title t --body ok",
            "bash -c 'gh 2>/dev/null pr create --title t --body ok'",
        ):
            with self.subTest(command=command):
                result = self.h._run_hook(self.repo, command)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn('"hookEventName": "PreToolUse"', result.stdout)
                self.assertIn("Next Action=gdd-completion-check", result.stdout)

    def test_non_pr_commands_with_the_same_shapes_still_pass(self) -> None:
        for command in (
            "echo fix#12; ls new",
            "git commit -F - <<MSG\ngh pr create in prose\nMSG",
            "echo 'gh pr create && x' # create",
            # `pr create` は gh の simple command の外（`;` の後ろ）にある。
            "gh --help; pr create --title t --body ok",
            "gh 2>/dev/null pr list --search create",
        ):
            with self.subTest(command=command):
                result = self.h._run_hook(self.repo, command)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout, "")


class PrePrGateBodyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.h = _helpers()
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.repo = Path(tmp.name)
        self.h._init_repo(self.repo)
        self.h._write_local_state(self.repo)
        self.h._write_steering(self.repo)

    def test_quoted_operator_word_still_ends_the_arguments(self) -> None:
        # 区切りの判定は変更の前と同じ（引用符の中の `&&` だけの語も区切り）。後ろの --body を
        # 読まずに「検査できません」で不足として通知する側のまま（通す側に緩めない）。
        result = self.h._run_hook(self.repo, "gh pr create --title \"&&\" --body ok")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('"hookEventName": "PreToolUse"', result.stdout)
        self.assertIn("PR body をhookで検査できません", result.stdout)

    def test_digits_before_a_quoted_angle_bracket_stay_in_the_body(self) -> None:
        # fail-open ケース「不足として通知すべき入力が allow になる」: fd 番号の除去が引用符の中の
        # `123456789012<br>` から数字を消すと、本文の 12 桁数字の検査が外れる。
        for command in (
            "gh pr create --title t --body \"| 123456789012<br> |\"",
            "gh pr create --title t --body 'acct 123456789012>'",
            "gh api repos/o/r/pulls -f title=t -f head=x -f base=main -f \"body=a 123456789012<b>\"",
            # 引用符の外の 12 桁の数字は、bash でも zsh でも語として gh に渡る（bash は int に
            # 収まらない並びを fd 番号にしない。zsh は 1 桁だけを fd 番号に読む）。
            "gh pr create --title t --body 123456789012>out.txt",
            # リダイレクトは argv に入らないので、gh は後ろの語を --body の値に読む。
            "gh pr create --title t --body 2>/dev/null \"acct 123456789012\"",
            "gh pr create --title t --body >/tmp/out \"acct 123456789012\"",
        ):
            with self.subTest(command=command):
                result = self.h._run_hook(self.repo, command)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("12桁数字", result.stdout)


class FdPrefixStripTests(unittest.TestCase):
    def test_fd_numbers_up_to_ten_digits_are_dropped(self) -> None:
        # 11 桁以上は bash でも zsh でも語なので、本文の 12 桁数字は残る。
        self.assertEqual(
            _tokenize("gh pr create --body 123456789012>out.txt 12>x 2>&1"),
            ["gh", "pr", "create", "--body", "123456789012", ">", "out.txt", ">", "x", ">&", "1"],
        )

    def test_only_unquoted_fd_numbers_are_dropped(self) -> None:
        self.assertEqual(
            _tokenize("gh pr merge 7 --body \"a 3>2\" --subject 'b 4<c' 2>&1"),
            ["gh", "pr", "merge", "7", "--body", "a 3>2", "--subject", "b 4<c", ">&", "1"],
        )


class MergeGateMultiDigitFdTests(unittest.TestCase):
    """2〜10 桁の数字がリダイレクトに密着する形は、bash は fd 番号、zsh は語と読む。"""

    def test_multi_digit_fd_makes_the_merge_target_unresolvable(self) -> None:
        # fail-open ケース「不足として通知すべき入力が allow になる」: zsh で `gh pr merge 12>/tmp/x` は
        # PR #12 の merge、bash では引数の無い merge（今のブランチの PR）。どちらかに決めると、
        # もう一方の shell で別の PR を merge させる。読めた番号は、台帳の照合のために残す。
        # bash の読みで番号が無いときは、zsh の読み（`12` は語）の番号を残す。
        for command in ("gh pr merge 12>/tmp/x", "echo 10>/dev/null; gh pr merge 12>/tmp/x"):
            with self.subTest(command=command):
                result = parse_gh_pr_merge(command, "", "/repo")
                self.assertTrue(result["is_merge"])
                self.assertTrue(result["unresolvable"])
                self.assertEqual(result["pr_number"], "12")
        quoted = parse_gh_pr_merge("gh pr merge --body \"a 12>b\" 12>/tmp/x", "", "/repo")
        self.assertEqual((quoted["pr_number"], quoted["unresolvable"]), ("12", True))
        # コメントの中の引用符で、zsh の読みが引用の範囲を取り違えない（有無の判定と同じ前処理）。
        commented = parse_gh_pr_merge("# don't wait\ngh pr merge 12>/tmp/x", "", "/repo")
        self.assertEqual((commented["pr_number"], commented["unresolvable"]), ("12", True))
        self.assertEqual(
            _split_multi_digit_fd("gh pr merge --body \"a 12>b\" 12>/tmp/x"),
            "gh pr merge --body \"a 12>b\" 12 >/tmp/x",
        )
        for command in (
            "gh pr merge 7 12>/tmp/x",
            "gh 12>/dev/null pr merge 7",
            "bash -c 'gh pr merge 7 12>/tmp/x'",
            "echo ok 10>/dev/null; gh pr merge 7",
        ):
            with self.subTest(command=command):
                result = parse_gh_pr_merge(command, "", "/repo")
                self.assertTrue(result["is_merge"])
                self.assertTrue(result["unresolvable"])
                self.assertEqual(result["pr_number"], "7")

    def test_two_merges_still_drop_the_target(self) -> None:
        result = parse_gh_pr_merge("gh pr merge 7 && gh pr merge 8", "", "/repo")
        self.assertTrue(result["unresolvable"])
        self.assertIsNone(result["pr_number"])

    def test_single_digit_and_quoted_digits_keep_the_target(self) -> None:
        for command in (
            "gh pr merge 7 2>&1",
            "gh pr merge 7 --body \"a 12>b\"",
            "gh pr merge 7 >/tmp/x",
        ):
            with self.subTest(command=command):
                result = parse_gh_pr_merge(command, "", "/repo")
                self.assertTrue(result["is_merge"])
                self.assertFalse(result["unresolvable"])
                self.assertEqual(result["pr_number"], "7")
        self.assertFalse(parse_gh_pr_merge("echo 12>/dev/null", "", "/repo")["is_merge"])


class MergeGateShellOptionTests(unittest.TestCase):
    def test_shell_c_found_past_redirects_and_plus_options(self) -> None:
        # fail-open ケース「不足として通知すべき入力が allow になる」: bash は `-c` の前のリダイレクトと
        # `+e`・`+o pipefail` を読み飛ばして、後ろの script を実行する。
        for command in (
            "bash 2>/dev/null -c 'gh pr merge 7'",
            "bash </dev/null -c 'gh pr merge 7'",
            "bash +e -c 'gh pr merge 7'",
            "bash +o pipefail -c 'gh pr merge 7'",
            "sh -e +x -c 'gh pr merge 7'",
        ):
            with self.subTest(command=command):
                result = parse_gh_pr_merge(command, "", "/repo")
                self.assertTrue(result["is_merge"])
                self.assertEqual(result["pr_number"], "7")


def _run_hook_with_payload(cwd: Path, payload: dict) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.update({
        "CLAUDE_PLUGIN_ROOT": str(PLUGIN_ROOT),
        "CLAUDE_CODE_SESSION_ID": "test-session",
        "GDD_HOOK_STATE_DIR": tempfile.mkdtemp(),
    })
    return subprocess.run(
        ["bash", str(contract.HOOK)], input=json.dumps(payload), cwd=cwd, env=env,
        capture_output=True, text=True, check=False,
    )


class PrePrGateLexerImportFailureTests(unittest.TestCase):
    """lib を読めない・解析が例外で終わるとき、active GDD の中なら不足として通知し、外なら通す（merge gate と同じ向き）。"""

    def _run_copied_hook(self, break_module, *, active: bool = True, via: str = ""):
        h = _helpers()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / "repo"
            repo.mkdir()
            h._init_repo(repo)
            h._write_local_state(repo, active=active)
            h._write_steering(repo, next_action="gdd-completion-check")
            outside = root / "outside"
            outside.mkdir()
            hooks = root / "plugin" / "hooks"
            shutil.copytree(PLUGIN_ROOT / "hooks", hooks)
            break_module(hooks / "scripts" / "lib" / "gh_command_parse.py")
            original = contract.HOOK
            contract.HOOK = hooks / "scripts" / "run-pre-pr-gate-hook.sh"
            try:
                command = "gh pr create --title t --body ok"
                if via == "tool_cwd":
                    return h._run_hook(outside, command, tool_cwd=repo)
                if via == "workdir":
                    return _run_hook_with_payload(outside, {"tool_input": {"command": command, "workdir": str(repo)}})
                if via == "top_cwd":
                    return _run_hook_with_payload(outside, {"cwd": str(repo), "tool_input": {"command": command}})
                return h._run_hook(repo, command)
            finally:
                contract.HOOK = original

    def test_broken_lib_blocks_inside_active_gdd(self) -> None:
        # fail-open ケース「例外で guard 全体が落ちる」「判定できないときに通ってしまう」。
        for label, breaker in (
            ("missing", lambda path: path.unlink()),
            ("syntax-error", lambda path: path.write_text("def (:\n", encoding="utf-8")),
            ("renamed-functions", lambda path: path.write_text("X = 1\n", encoding="utf-8")),
        ):
            with self.subTest(lib=label):
                result = self._run_copied_hook(breaker)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertIn('"hookEventName": "PreToolUse"', result.stdout)
                self.assertIn("gh_command_parse", result.stdout)
                self.assertIn("gdd-hooks-disabled", result.stdout)

    def test_broken_lib_uses_the_payload_cwd(self) -> None:
        # hook のプロセスの cwd は active GDD の外でも、payload の cwd（tool_input の cwd・workdir、
        # 最上位の cwd）が active GDD の中なら不足として通知する。
        for via in ("tool_cwd", "workdir", "top_cwd"):
            with self.subTest(via=via):
                result = self._run_copied_hook(lambda path: path.unlink(), via=via)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertIn('"hookEventName": "PreToolUse"', result.stdout)
                self.assertIn("gh_command_parse", result.stdout)

    def test_broken_lib_passes_outside_active_gdd(self) -> None:
        result = self._run_copied_hook(lambda path: path.unlink(), active=False)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stdout, "")


if __name__ == "__main__":
    unittest.main()
