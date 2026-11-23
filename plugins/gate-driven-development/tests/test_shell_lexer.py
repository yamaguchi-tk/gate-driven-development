"""gate が共有する字句解析の芯（`hooks/scripts/lib/shell_lexer.py`）のテスト。

期待値は実 shell の読みで決めた。偽の gh・git（argv をファイルへ書くだけ）を PATH の先頭に置き、
bash 3.2 と zsh 5.9 の両方で `-c` に渡して実行した argv を正解にした。2 つの shell で読みが割れる形は、
止める側（gate が検出する・対象を決められない）を期待値にする。

- 行継続（`\\` + 改行）は、引用符の外と二重引用符の中では消え、単引用符・`$'…'` の中では残る。
  コメントの末尾の `\\` は次の行を飲まない
- 語頭の `#` だけがコメント。`$(…)`・`$((…))` を閉じる `)` の直後は語の途中で、コメントではない。
  サブシェル・case のパターンを閉じる `)` の直後はコメント
- 引用符の外の改行はコマンドの区切り。引用符の中の改行は語の一部（複数行の commit メッセージ）
- 引用符が末尾まで閉じない（bash・zsh は構文エラー）ときは、縮退として知らせる
"""
from __future__ import annotations

import sys
import unittest

from _paths import PLUGIN_ROOT

sys.path.insert(0, str(PLUGIN_ROOT / "hooks" / "scripts" / "lib"))

import shell_lexer  # noqa: E402

NL = "\n"
BS = "\\"


def _lex(text: str, fd_digits: int = 1) -> list[str]:
    tokens, _degraded = shell_lexer.lex(text, NL, fd_digits)
    return tokens


class LineContinuationTests(unittest.TestCase):
    def test_continuation_inside_a_word_joins_the_word(self) -> None:
        # bash・zsh とも `git push o m` を実行する。
        self.assertEqual(_lex("git pu" + BS + NL + "sh o m"), ["git", "push", "o", "m"])

    def test_continuation_inside_double_quotes_is_removed(self) -> None:
        # bash・zsh とも引数は `ab`。
        self.assertEqual(_lex('git commit -m "a' + BS + NL + 'b"'), ["git", "commit", "-m", "ab"])

    def test_continuation_inside_single_quotes_is_kept(self) -> None:
        # bash・zsh とも引数は `a\` + 改行 + `b`。
        self.assertEqual(
            _lex("git commit -m 'a" + BS + NL + "b'"), ["git", "commit", "-m", "a" + BS + NL + "b"]
        )

    def test_continuation_inside_ansi_c_quotes_is_kept(self) -> None:
        # bash は残す（zsh は消す。引数の中身にしか効かない）。
        normalized = shell_lexer.normalize("echo $'a" + BS + NL + "b'")
        self.assertIn(BS + NL, normalized)

    def test_backslash_at_the_end_of_a_comment_does_not_continue_the_line(self) -> None:
        # bash・zsh とも次の行の `git push o m` を実行する。
        self.assertEqual(
            _lex("echo x # c " + BS + NL + "git push o m"), ["echo", "x", NL, "git", "push", "o", "m"]
        )

    def test_continuation_then_hash_at_word_start_is_a_comment(self) -> None:
        self.assertEqual(
            _lex("echo a " + BS + NL + "#b" + NL + "git push o m"),
            ["echo", "a", NL, "git", "push", "o", "m"],
        )

    def test_continuation_then_hash_inside_a_word_is_not_a_comment(self) -> None:
        self.assertEqual(
            _lex("echo a" + BS + NL + "#b; git push o m"), ["echo", "a#b", ";", "git", "push", "o", "m"]
        )

    def test_escaped_backslash_before_newline_is_not_a_continuation(self) -> None:
        self.assertEqual(
            _lex("echo a" + BS + BS + NL + "git push o m"),
            ["echo", "a" + BS, NL, "git", "push", "o", "m"],
        )


class NestedQuoteContextTests(unittest.TestCase):
    """二重引用符の中の `$(…)`・バッククォート・`${…}` は新しい文脈で、中の `"` は外の引用を閉じない。

    bash・zsh とも、下の形はどれも後ろの `git push o m` を実行する（中の `#` はコメントにならない）。
    """

    def test_hash_inside_a_quoted_substitution_is_not_a_comment(self) -> None:
        for command in (
            'git commit -m "$(printf "fix #12")" && git push o m',
            'echo "$(echo "a #b")" && git push o m',
            'echo "`echo "a #b"`" && git push o m',
            'echo "${x:-"a #b"}" && git push o m',
            "echo \"$(echo ')' \"#\") x\" && git push o m",
        ):
            with self.subTest(command=command):
                self.assertEqual(_lex(command)[-4:], ["git", "push", "o", "m"])

    def test_comment_inside_a_backtick_substitution_ends_at_the_backtick(self) -> None:
        # bash・zsh とも `echo a` を置換し、`;` の後の push を実行する。
        self.assertEqual(_lex("echo `echo a #b`; git push o m")[-4:], ["git", "push", "o", "m"])

    def test_hash_inside_parens_inside_a_backtick_is_not_a_comment(self) -> None:
        # bash は閉じるバッククォートを先に探すので、中の `$(…)`・`(…)` の `#` はコメントにならず、
        # `;` の後の push を実行する（zsh は何も実行しない。割れる形は止める側）。
        for command in (
            "echo `echo $(echo a #b)`; git push o m",
            "`(echo a #b)`; git push o m",
            'echo `echo "$(echo a #b)"`; git push o m',
        ):
            with self.subTest(command=command):
                self.assertEqual(_lex(command)[-4:], ["git", "push", "o", "m"])

    def test_backtick_interval_closes_at_the_next_backtick(self) -> None:
        # 区間の中の `(` は外の文脈に残らず、区間の後ろの語頭の `#` はコメント。区間の中のコメントは閉じの
        # 手前で終わり、中のアポストロフィは外の引用を開かない。
        self.assertEqual(
            _lex("echo `(echo a` && ( true # ; cd /tmp" + NL + "git push o m )")[-5:],
            ["git", "push", "o", "m", ")"],
        )
        self.assertNotIn("cd", _lex("echo `(echo a` && ( true # ; cd /tmp" + NL + "git push o m )"))
        self.assertEqual(_lex("v=`git rev-parse HEAD # it's`" + NL + "git push o m # don't")[-4:], ["git", "push", "o", "m"])
        self.assertEqual(_lex('x="`echo a # it' + "'" + 's`"' + NL + "git push o m")[-4:], ["git", "push", "o", "m"])

    def test_parameter_expansion_hash_is_not_a_comment(self) -> None:
        self.assertEqual(_lex('echo "${x#a}" ${#y} && git push o m')[-4:], ["git", "push", "o", "m"])


class LeadingSeparatorTests(unittest.TestCase):
    def test_no_separator_before_the_first_token(self) -> None:
        # 先頭のコメント行・空行は区切りを残さない（`cd` がコマンドの先頭のまま）。
        self.assertEqual(shell_lexer.lex("# c" + NL + NL + "cd /tmp && x", ";", 10)[0], ["cd", "/tmp", "&&", "x"])
        self.assertEqual(shell_lexer.lex(NL + "a" + NL + NL + "b", ";", 10)[0], ["a", ";", ";", "b"])


class CommentTests(unittest.TestCase):
    def test_hash_after_command_substitution_is_not_a_comment(self) -> None:
        # bash・zsh とも `git push o m` を実行する。
        for prefix in ("echo $(echo d)#x; ", "echo $((1))#x; ", "echo `echo d`#x; "):
            with self.subTest(prefix=prefix):
                self.assertEqual(_lex(prefix + "git push o m")[-3:], ["push", "o", "m"])
                self.assertIn("git", _lex(prefix + "git push o m"))

    def test_hash_after_subshell_or_case_pattern_is_a_comment(self) -> None:
        # bash・zsh とも次の行の `git push o m` を実行する。`'` はコメントの中なので引用を始めない。
        for command in (
            "(echo a)#x'" + NL + "git push o m",
            "case x in x)#'" + NL + "git push o m;; esac",
        ):
            with self.subTest(command=command):
                tokens, degraded = shell_lexer.lex(command, NL, 1)
                self.assertFalse(degraded)
                self.assertIn("push", tokens)

    def test_hash_inside_a_word_is_not_a_comment(self) -> None:
        self.assertEqual(_lex("git commit -m fix#12 && git push"), ["git", "commit", "-m", "fix#12", "&&", "git", "push"])


class NewlineTests(unittest.TestCase):
    def test_newline_inside_quotes_does_not_split_the_command(self) -> None:
        tokens, degraded = shell_lexer.lex('git commit -m "a' + NL + 'b c" && git push o m', NL, 1)
        self.assertFalse(degraded)
        self.assertEqual(tokens, ["git", "commit", "-m", "a" + NL + "b c", "&&", "git", "push", "o", "m"])

    def test_closing_line_with_an_even_number_of_quotes_ends_the_quote(self) -> None:
        # 行ごとに割ると、閉じ側の行の `" && git push … --body "` が 1 つの引用符の token になる。
        command = (
            'git commit -m "s' + NL + NL + 'Co-Authored-By: X <x@example.com>" && git push origin HEAD'
            ' && gh pr comment 1 --body "c' + NL + 'd"'
        )
        tokens, degraded = shell_lexer.lex(command, NL, 1)
        self.assertFalse(degraded)
        self.assertEqual(tokens[4:8], ["&&", "git", "push", "origin"])

    def test_unquoted_newline_becomes_the_given_token(self) -> None:
        self.assertEqual(shell_lexer.lex("a" + NL + "b", ";", 10)[0], ["a", ";", "b"])

    def test_quote_left_open_to_the_end_is_degraded(self) -> None:
        # bash・zsh とも構文エラー（その行は実行しない）。縮退した片は引用符を見ずに割る。
        tokens, degraded = shell_lexer.lex("git push o m" + NL + 'echo "x', NL, 1)
        self.assertTrue(degraded)
        self.assertEqual(tokens[:4], ["git", "push", "o", "m"])


class OperatorAndFdTests(unittest.TestCase):
    def test_quoted_operator_is_marked(self) -> None:
        tokens = _lex('echo ";" x')
        self.assertEqual(tokens, ["echo", ";", "x"])
        self.assertIsInstance(tokens[1], shell_lexer.QuotedWord)
        self.assertFalse(shell_lexer.is_operator(tokens[1]))

    def test_quoted_newline_and_brace_are_marked(self) -> None:
        # 引用した改行・`{` も、区切りの集合と等しい token なら `QuotedWord` にする。
        for word in (NL, "{"):
            for quoted in (f"'{word}'", f'"{word}"'):
                with self.subTest(quoted=quoted):
                    tokens = _lex(f"echo {quoted} x")
                    self.assertEqual(tokens, ["echo", word, "x"])
                    self.assertIsInstance(tokens[1], shell_lexer.QuotedWord)

    def test_glued_fd_numbers_are_dropped_up_to_the_given_digits(self) -> None:
        # bash は `12>x` を fd 12、zsh は語 `12` と読む。1 桁は両方とも fd。
        self.assertEqual(_lex("git branch 2>&1", fd_digits=1), ["git", "branch", ">&", "1"])
        self.assertEqual(_lex("git branch 12>x", fd_digits=1), ["git", "branch", "12", ">", "x"])
        self.assertEqual(_lex("gh pr merge 7 12>x", fd_digits=10), ["gh", "pr", "merge", "7", ">", "x"])
        self.assertEqual(_lex("git branch 2 >x", fd_digits=1), ["git", "branch", "2", ">", "x"])

    def test_digits_inside_quotes_stay(self) -> None:
        self.assertEqual(_lex('echo "a 12>b"', fd_digits=10), ["echo", "a 12>b"])


if __name__ == "__main__":
    unittest.main()
