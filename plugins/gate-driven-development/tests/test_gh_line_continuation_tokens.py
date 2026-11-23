"""pre-PR gate・merge gate: 行継続（`\\` + 改行）の後ろの gh を見落とさない。

shlex（posix）は `\\` + 改行を、次の語の先頭に付いた改行の文字にする。Claude Code が
既定で書く `cd <worktree> && \\` + 改行 + `gh pr create …` では `gh` が `"\\ngh"` という
token になり、basename が `gh` にならないので、2 つの gate とも PR 作成・merge と
判定せずに通していた（2026-09-29 実測: transcript の Bash コマンドのうち gh と create/new/pulls/graphql/merge を含むものに、
行継続を含む `gh pr create`・`gh pr merge` があった）。字句解析の前に、行継続を空白 + 改行に
置き換える（語の途中の行継続は置き換えない）。
"""
from __future__ import annotations

import json
import shlex
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import test_pre_pr_gate_contract as contract
from _merge_gate_support import (
    PLUGIN_ROOT,
    _approval_line,
    _head_sha,
    _init_repo,
    _run_hook,
    _write_local_state,
    _write_state,
)

sys.path.insert(0, str(PLUGIN_ROOT / "hooks" / "scripts"))

from lib.gh_command_parse import parse_gh_pr_merge  # noqa: E402

SECRET = "機密候補"


class PrePrGateLineContinuationTests(unittest.TestCase):
    _init_repo = contract.PrePrGateContractTests._init_repo
    _write_local_state = contract.PrePrGateContractTests._write_local_state
    _write_steering = contract.PrePrGateContractTests._write_steering
    _head_sha = contract.PrePrGateContractTests._head_sha
    _independent_review_line = contract.PrePrGateContractTests._independent_review_line
    _run_hook = contract.PrePrGateContractTests._run_hook

    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = Path(tmp.name)
        self.repo = self.tmp / "repo"
        self.repo.mkdir()
        self._init_repo(self.repo)
        self._write_local_state(self.repo)
        self._write_steering(self.repo)
        (self.repo / "feature.py").write_text("print('ok')\n", encoding="utf-8")
        subprocess.run(["git", "add", "feature.py"], cwd=self.repo, check=True)
        subprocess.run(["git", "commit", "-q", "-m", "add feature"], cwd=self.repo, check=True)
        (self.repo / "pr.md").write_text("token: x\n", encoding="utf-8")

    def _reason(self, cwd: Path, command: str) -> str | None:
        result = self._run_hook(cwd, command)
        self.assertEqual(result.returncode, 0, result.stderr[-2000:])
        if not result.stdout.strip():
            return None
        payload = json.loads(result.stdout)
        self.assertEqual(payload["hookSpecificOutput"]["hookEventName"], "PreToolUse")
        return payload["hookSpecificOutput"]["additionalContext"]

    def test_pr_create_after_line_continuation_is_inspected(self) -> None:
        # fail-open ケース「block すべき入力が allow になる」。
        for command in (
            "git status && \\\ngh pr create --title t --body 'token: x'",
            "git status && \\\n  gh pr create --title t --body 'token: x'",
            "bash -c 'true && \\\ngh pr create --title t --body \"token: x\"'",
            "eval 'true && \\\ngh pr create --title t --body \"token: x\"'",
        ):
            with self.subTest(command=command):
                self.assertIn(SECRET, self._reason(self.repo, command) or "")

    def test_cd_before_line_continuation_sets_the_command_cwd(self) -> None:
        # `cd <worktree> && \` の形では、本文ファイルの相対パスを cd の先で読む。
        outside = self.tmp / "outside"
        outside.mkdir()
        command = f"cd {self.repo} && \\\ngh pr create --title t --body-file pr.md"
        self.assertIn(SECRET, self._reason(outside, command) or "")

    def test_quoted_newline_and_operator_stays_a_word(self) -> None:
        # 引用符の中の改行 + `&&` は、改行を落としても区切りにしない（後ろの --body を見る）。
        command = "gh pr create --title \"\n&&\" --body 'token: x'"
        self.assertIn(SECRET, self._reason(self.repo, command) or "")

    def test_empty_or_newline_only_values_keep_their_position(self) -> None:
        # 空の値（`""`・`''`）と改行だけの値を token ごと消すと、flag が次の語を値として
        # 取り込み、PR 作成・head を見落とす。
        for command in (
            "gh --repo \"\" pr create --title t --body 'token: x'",
            "gh -R '' pr create --title t --body 'token: x'",
            "gh --repo \"\n\" pr create --title t --body 'token: x'",
        ):
            with self.subTest(command=command):
                self.assertIn(SECRET, self._reason(self.repo, command) or "")
        reason = self._reason(self.repo, "gh pr create --title t --body \"\" --head other")
        self.assertIn("--head", reason or "")

    def test_unusual_spacing_or_quotes_reach_the_check(self) -> None:
        # 前段の照合を 2 語の字面で絞ると、gh では PR 作成になる形が python に届かない。
        for command in (
            "gh pr  create --title t --body 'token: x'",
            "gh pr \"create\" --title t --body 'token: x'",
            "gh pr\tcreate --title t --body 'token: x'",
            "gh pr \\\ncreate --title t --body 'token: x'",
        ):
            with self.subTest(command=command):
                self.assertIn(SECRET, self._reason(self.repo, command) or "")

    def test_nested_shell_splits_operators_like_the_top_level(self) -> None:
        for command in (
            "bash -c 'true&&gh pr create --title t --body \"token: x\"'",
            "bash -c 'true;gh pr create --title t --body \"token: x\"'",
            "eval 'true;gh pr create --title t --body \"token: x\"'",
            "eval \"gh pr\" create --title t --body 'token: x'",
        ):
            with self.subTest(command=command):
                self.assertIn(SECRET, self._reason(self.repo, command) or "")

    def test_nested_shell_body_keeps_hash_inside_words(self) -> None:
        # 語の途中の `#` はコメントではない（bash と同じ）。入れ子の本体で後ろを捨てない。
        for command in (
            "bash -c 'echo $#; gh pr create --title t --body \"token: x\"'",
            "eval 'n=${#a}; gh pr create --title t --body \"token: x\"'",
            "bash -c 'echo a#b && gh pr create --title t --body \"token: x\"'",
        ):
            with self.subTest(command=command):
                self.assertIn(SECRET, self._reason(self.repo, command) or "")

    def test_indented_line_continuation_inside_the_command(self) -> None:
        # 字下げ付きの行継続が gh と pr の間などに来ても、PR 作成として読む。
        for command in (
            "gh pr \\\n  create --title t --body 'token: x'",
            "gh \\\n  pr create --title t --body 'token: x'",
            "bash -c \\\n  'gh pr create --title t --body \"token: x\"'",
            "gh pr create --title t \\\n  --body \\\n  'token: x'",
        ):
            with self.subTest(command=command):
                self.assertIn(SECRET, self._reason(self.repo, command) or "")
        reason = self._reason(self.repo, "gh pr create --title t --body x --head \\\n  other")
        self.assertIn("--head", reason or "")

    def test_nested_shell_body_ignores_word_start_comments(self) -> None:
        # 語頭の `#` から行末までは bash が捨てる。コメントの中の flag が後勝ちで効くと、
        # PR 作成の検出（-X GET）と head の照合が外れる。
        reason = self._reason(
            self.repo,
            "bash -c 'gh api repos/o/r/pulls -f title=t -f \"body=token: x\" # -X GET'",
        )
        self.assertIn(SECRET, reason or "")
        branch = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=self.repo, capture_output=True, text=True, check=True
        ).stdout.strip()
        reason = self._reason(
            self.repo, f"bash -c 'gh pr create --title t --body x --head other # --head {branch}'"
        )
        self.assertIn("--head", reason or "")
        # コメントの中の gh は実行されない。
        command = "bash -c 'echo hi # gh pr create --title t --body \"token: x\"'"
        self.assertIsNone(self._reason(self.repo, command))

    def test_escaped_separator_before_a_line_continuation_keeps_the_word(self) -> None:
        # `a\ ` + 行継続 + `#x` は bash では 1 語 `a #x`（`#` は語頭ではない）。エスケープした
        # 空白を区切りと見て置き換えると、`#x; gh …` をコメントとして捨てて gh を見落とす。
        command = "bash -c 'echo a\\ \\\n#x; gh pr create --title t --body \"token: x\"'"
        self.assertIn(SECRET, self._reason(self.repo, command) or "")

    def test_nested_comment_strip_knows_ansi_c_quotes(self) -> None:
        # `$'a\' #'` は bash では 1 語（中の `\'` はエスケープで、引用は閉じない）。
        body = "echo $'a\\' #' ; gh pr create --title t --body \"token: x\""
        self.assertIn(SECRET, self._reason(self.repo, "bash -c " + shlex.quote(body)) or "")

    def test_doubled_dollar_before_a_quote_is_not_ansi_c(self) -> None:
        # bash は `$$`（PID）を 2 文字まとめて読む。後ろの単引用符は通常の引用で、
        # `$$'\\'' #'` は「PID + `\\` + 引用 ` #`」。ANSI-C と読むと、後ろの gh を捨てる。
        # 後ろの行で引用の数が釣り合う形にして、shlex の縮退に頼らず判定を固定する。
        body = "echo $$'\\'' #'; gh pr create --title t --body \"token: x\"\necho \\'"
        self.assertIn(SECRET, self._reason(self.repo, "bash -c " + shlex.quote(body)) or "")

    def test_line_continuation_between_dollar_and_quote_is_ansi_c(self) -> None:
        # bash は `$` の次の文字を読む前に行継続を消す。`$` + 行継続 + `'…'` は ANSI-C 引用。
        body = "echo $\\\n'a\\' #' ; gh pr create --title t --body \"token: x\""
        self.assertIn(SECRET, self._reason(self.repo, "bash -c " + shlex.quote(body)) or "")

    def test_consecutive_line_continuations_inside_a_word_do_not_split_it(self) -> None:
        # `cd /a` + 行継続 2 つ + `b` は bash では /ab。2 語に割ると /a を基準にしてしまう。
        outside = self.tmp / "outside"
        outside.mkdir()
        command = f"cd {self.repo}\\\n\\\nx && gh pr create --title t --body-file pr.md"
        self.assertIsNone(self._reason(outside, command))

    def test_trailing_line_continuation_is_still_pr_creation(self) -> None:
        # fail-open ケース「判定できないときに通ってしまう」「例外で guard 全体が落ちる」。
        self.assertIsNotNone(self._reason(self.repo, "gh pr create \\\n"))


class MergeGateLineContinuationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.home = self.tmp / "home"
        (self.home / ".claude").mkdir(parents=True)
        self.repo = _init_repo(self.tmp)

    def test_merge_after_line_continuation_is_parsed(self) -> None:
        for command in (
            "gh pr review 7 --approve && \\\ngh pr merge 7",
            "gh pr review 7 --approve && \\\n  gh pr merge 7 --squash",
        ):
            with self.subTest(command=command):
                result = parse_gh_pr_merge(command, "", "/repo")
                self.assertTrue(result["is_merge"])
                self.assertEqual(result["pr_number"], "7")
        result = parse_gh_pr_merge("cd /wt && \\\ngh pr merge 7", "", "/repo")
        self.assertTrue(result["is_merge"])
        self.assertEqual(result["cd_target"], "/wt")

    def test_quoted_newline_and_operator_stays_a_word(self) -> None:
        # 引用符の中の改行 + `&&` を区切りにすると、後ろの `-R` を落として別の repo を見る。
        result = parse_gh_pr_merge("gh pr merge 7 -t \"\n&&\" -R o/x", "", "/repo")
        self.assertEqual(result["repo_flag"], "o/x")

    def test_merge_after_line_continuation_reaches_the_evidence_gate(self) -> None:
        _write_state(self.repo, active=True, session_id="other-session")
        payload = {"tool_input": {"command": "gh pr review 7 --approve && \\\ngh pr merge 7"}}
        result = _run_hook(payload, self.repo, self.home)
        self.assertIn('"hookEventName": "PreToolUse"', result.stdout)
        self.assertIn("approval-missing", result.stdout)

    def test_empty_or_newline_only_values_keep_their_position(self) -> None:
        for command in ('gh pr merge --squash --body "" 999', "gh pr merge -t '\n' 999"):
            with self.subTest(command=command):
                self.assertEqual(parse_gh_pr_merge(command, "", "/repo")["pr_number"], "999")
        for command in ("gh -R '' pr merge 7", 'gh --repo "" pr merge 7'):
            with self.subTest(command=command):
                self.assertTrue(parse_gh_pr_merge(command, "", "/repo")["is_merge"])

    def test_empty_value_does_not_borrow_the_approval_of_another_pr(self) -> None:
        _write_local_state(self.repo, extra_lines=[_approval_line(7, _head_sha(self.repo))])
        payload = {"tool_input": {"command": 'gh pr merge --squash --body "" 999'}}
        result = _run_hook(payload, self.repo, self.home)
        self.assertIn("approval-pr-mismatch", result.stdout)

    def test_indented_line_continuation_inside_the_command(self) -> None:
        for command in (
            "gh pr \\\n  merge 7",
            "gh \\\n  pr merge 7",
            "gh -R o/r \\\n  pr merge 7",
            "bash -lc \\\n  'gh pr merge 7'",
            "gh pr merge 7 \\\n  --squash",
        ):
            with self.subTest(command=command):
                result = parse_gh_pr_merge(command, "", "/repo")
                self.assertTrue(result["is_merge"])
                self.assertEqual(result["pr_number"], "7")
                self.assertFalse(result["unresolvable"])

    def test_line_continuation_inside_a_word_does_not_split_it(self) -> None:
        # bash・zsh とも `1\` + 改行 + `23` を 123 と読む。2 語に割ると PR 23 と読み違えて
        # 別の PR の承認を借りるので、行継続を消して 1 語にする。
        for command, number, url in (
            ("gh pr merge 1\\\n23 --squash", "123", None),
            ("gh pr merge https://github.com/o/r/pull/1\\\n23", None, "https://github.com/o/r/pull/123"),
        ):
            with self.subTest(command=command):
                result = parse_gh_pr_merge(command, "", "/repo")
                self.assertTrue(result["is_merge"])
                self.assertEqual((result["pr_number"], result["pr_url"]), (number, url))
                self.assertFalse(result["unresolvable"])

    def test_consecutive_line_continuations_inside_a_word_do_not_split_it(self) -> None:
        # bash・zsh とも `1` + 行継続 2 つ + `23` を 123 と読む。行継続ごとに判定すると 2 つ目だけが
        # 置き換わり、PR 23 と読み違える。
        for command in (
            "gh pr merge 1\\\n\\\n23",
            "bash -c 'gh pr merge 1\\\n\\\n23'",
            "gh pr merge 1\\\n\\\n\\\n23",
        ):
            with self.subTest(command=command):
                result = parse_gh_pr_merge(command, "", "/repo")
                self.assertEqual(result["pr_number"], "123")
                self.assertFalse(result["unresolvable"])

    def test_escaped_separator_before_a_line_continuation_keeps_the_word(self) -> None:
        # bash では `a\ ` + 行継続 + `#x` は 1 語で、`#` はコメントではない。後ろの merge を見る。
        result = parse_gh_pr_merge("echo a\\ \\\n#x; gh pr merge 123", "", "/repo")
        self.assertTrue(result["is_merge"])
        self.assertEqual(result["pr_number"], "123")

    def test_comment_strip_knows_ansi_c_quotes(self) -> None:
        result = parse_gh_pr_merge("echo $'a\\' #' ; gh pr merge 7", "", "/repo")
        self.assertTrue(result["is_merge"])
        self.assertEqual(result["pr_number"], "7")

    def test_doubled_dollar_before_a_quote_is_not_ansi_c(self) -> None:
        command = "echo $$'\\'' #'; gh pr merge 7\necho \\'"
        result = parse_gh_pr_merge(command, "", "/repo")
        self.assertTrue(result["is_merge"])
        self.assertEqual(result["pr_number"], "7")

    def test_line_continuation_between_dollar_and_quote_is_ansi_c(self) -> None:
        command = "echo $\\\n'a\\' #' ; gh pr merge 7"
        result = parse_gh_pr_merge(command, "", "/repo")
        self.assertTrue(result["is_merge"])
        self.assertEqual(result["pr_number"], "7")

    def test_consecutive_line_continuations_do_not_borrow_another_pr(self) -> None:
        # done 後（active: false）でも、PR を特定できない merge は不足として通知する。
        _write_state(self.repo, active=False, pr_url="https://github.com/acme/widgets/pull/123")
        payload = {"tool_input": {"command": "gh pr merge 1\\\n\\\n23"}}
        result = _run_hook(payload, self.repo, self.home)
        self.assertIn('"hookEventName": "PreToolUse"', result.stdout)

    def test_newline_or_continuation_only_input_is_not_a_merge(self) -> None:
        # fail-open ケース「例外で guard 全体が落ちる」。
        for command in ("\\\n", "\n"):
            with self.subTest(command=command):
                self.assertFalse(parse_gh_pr_merge(command, "", "/repo")["is_merge"])

    def test_trailing_line_continuation_is_still_a_merge(self) -> None:
        # fail-open ケース「判定できないときに通ってしまう」「例外で guard 全体が落ちる」。
        result = parse_gh_pr_merge("gh pr merge \\\n", "", "/repo")
        self.assertTrue(result["is_merge"])
        self.assertIsNone(result["pr_number"])


if __name__ == "__main__":
    unittest.main()
