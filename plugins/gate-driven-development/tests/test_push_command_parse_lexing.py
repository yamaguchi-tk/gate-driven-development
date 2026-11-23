"""`push_command_parse` / `git_command_parse` の字句解析とセグメント分割の単体テスト。

`test_push_command_parse.py` から分けた。

確かめる本体は `hooks/scripts/lib/push_command_parse.py`・`hooks/scripts/lib/git_command_parse.py`。
"""
from __future__ import annotations

import sys
import unittest

from _paths import PLUGIN_ROOT
sys.path.insert(0, str(PLUGIN_ROOT / "hooks" / "scripts" / "lib"))

import push_command_parse as pcp  # noqa: E402
import git_command_parse as gcp  # noqa: E402


class GitCommandParseExtractionTests(unittest.TestCase):
    """design.md ADR-1/ADR-2: 汎用解析の正本は git_command_parse で、
    push_command_parse は re-export するだけであることを固定する。"""

    def test_reexported_symbols_are_identical_objects(self):
        for name in [
            "NEWLINE_TOKEN",
            "COMMAND_SEPARATOR_TOKENS",
            "GIT_GLOBAL_FLAGS_WITH_ARGUMENT",
            "tokenize",
            "tokenize_with_boundary",
        ]:
            with self.subTest(name=name):
                self.assertIs(getattr(pcp, name), getattr(gcp, name))

    def test_is_git_token(self):
        self.assertTrue(gcp.is_git_token("/usr/bin/git"))
        self.assertFalse(gcp.is_git_token("gitk"))


class TokenizeTests(unittest.TestCase):
    def test_simple_git_push(self) -> None:
        tokens = pcp.tokenize("git push origin main")
        self.assertEqual(tokens, ["git", "push", "origin", "main"])

    def test_nested_bash_c_expands(self) -> None:
        tokens = pcp.tokenize("bash -c 'git push origin main'")
        # 展開 token は末尾へ append される（expand_nested_shell_tokens と同型）
        self.assertIn("git", tokens)
        self.assertIn("push", tokens)


class TokenizeBoundaryTests(unittest.TestCase):
    """原文 token 境界の公開（design.md §opt-out 受理面の機械定義 item 4）。

    T-2 の受理面が別 tokenizer の再計算に依存しないよう、境界値を同一 tokenizer
    から返す。
    """

    def test_returns_original_token_count(self) -> None:
        tokens, original_count = pcp.tokenize_with_boundary("git push origin main")
        self.assertEqual(original_count, 4)
        self.assertEqual(len(tokens), 4)

    def test_expanded_tokens_are_beyond_boundary(self) -> None:
        tokens, original_count = pcp.tokenize_with_boundary(
            "bash -c 'git push origin main'"
        )
        self.assertEqual(original_count, 3)
        self.assertEqual(tokens[:original_count], ["bash", "-c", "git push origin main"])
        self.assertEqual(tokens[original_count:], ["git", "push", "origin", "main"])

    def test_boundary_counts_separator_tokens_like_tokenize(self) -> None:
        # `shlex.split` 再計算では 4 token になり境界がずれるケース
        tokens, original_count = pcp.tokenize_with_boundary("echo hi; git push")
        self.assertEqual(original_count, len(tokens))
        self.assertEqual(tokens, ["echo", "hi", ";", "git", "push"])

    def test_tokenize_returns_same_tokens_as_boundary_variant(self) -> None:
        raw = "bash -c 'git push origin main'"
        self.assertEqual(pcp.tokenize(raw), pcp.tokenize_with_boundary(raw)[0])


class LexicalSurfaceTests(unittest.TestCase):
    """字句レベルで実 bash が実行する文字列を取りこぼさないこと。

    root cause クラス「検出面が実 bash / 実 git の受理面と一致していない」のうち、
    tokenizer が原文を**破棄・結合**してしまう欠陥を固定する。
    """

    def test_hash_inside_word_is_not_a_comment(self) -> None:
        # bash は語中の `#` をコメント開始として扱わない
        command = "git commit -m fix#12 && git push origin main"
        tokens = pcp.tokenize(command)
        self.assertIn("push", tokens)
        self.assertTrue(pcp.is_git_push(tokens)[0])

    def test_hash_inside_word_before_separator(self) -> None:
        tokens = pcp.tokenize("true a#b; git push --force origin main")
        self.assertTrue(pcp.is_git_push(tokens)[0])

    def test_standalone_hash_word_is_not_dropped(self) -> None:
        tokens = pcp.tokenize("git push origin main # ship it")
        self.assertTrue(pcp.is_git_push(tokens)[0])

    def test_line_continuation_joins_command(self) -> None:
        # `\` + 改行は行継続であり、bash では 1 コマンドとして実行される
        tokens = pcp.tokenize("git \\\npush origin main")
        self.assertEqual(tokens, ["git", "push", "origin", "main"])
        self.assertTrue(pcp.is_git_push(tokens)[0])

    def test_line_continuation_between_global_flag_and_subcommand(self) -> None:
        tokens = pcp.tokenize("git -C /repo/a \\\npush origin main")
        self.assertTrue(pcp.is_git_push(tokens)[0])

    def test_raw_newline_becomes_separator_token(self) -> None:
        # design.md § opt-out 受理面の機械定義 item 1 が要求する「改行 token」
        tokens, original_count = pcp.tokenize_with_boundary(
            "GDD_SKIP_PRE_PUSH_GATE=1 env\ngit push origin main"
        )
        self.assertEqual(
            tokens,
            [
                "GDD_SKIP_PRE_PUSH_GATE=1",
                "env",
                "\n",
                "git",
                "push",
                "origin",
                "main",
            ],
        )
        self.assertEqual(original_count, len(tokens))

    def test_raw_newline_separates_git_from_push(self) -> None:
        # `git` 改行 `push` は 2 コマンドであり push ではない
        tokens = pcp.tokenize("git\npush")
        self.assertEqual(tokens, ["git", "\n", "push"])
        self.assertFalse(pcp.is_git_push(tokens)[0])

    def test_push_after_raw_newline_is_detected(self) -> None:
        tokens = pcp.tokenize("echo hi\ngit push origin main")
        self.assertTrue(pcp.is_git_push(tokens)[0])


class LineContinuationEscapeTests(unittest.TestCase):
    """行末バックスラッシュの**エスケープを数える**こと。

    bash では行末の `\\` が**それ自体エスケープされていない**ときだけ行継続になる。
    連続バックスラッシュが偶数個ならすべてリテラルのバックスラッシュであり、
    続く改行はコマンド区切りとして残る。無条件に 1 組を除去すると 2 行が癒着し、
    次行の `git push` が前の token に飲まれて非検出（fail-open）になる。

    奇数個 / 偶数個を**対**で固定し、片側だけ通る実装を許さない。
    """

    def test_one_backslash_is_line_continuation(self) -> None:
        self.assertEqual(
            pcp.tokenize("git \\\npush origin main"),
            ["git", "push", "origin", "main"],
        )

    def test_two_backslashes_keep_the_newline_separator(self) -> None:
        # 実 bash: `echo a\\` は `a\` を出力し、改行は次コマンドへの区切り
        tokens = pcp.tokenize("echo a\\\\\ngit push origin main")
        self.assertEqual(
            tokens, ["echo", "a\\", pcp.NEWLINE_TOKEN, "git", "push", "origin", "main"]
        )
        self.assertTrue(pcp.is_git_push(tokens)[0])

    def test_three_backslashes_are_literal_plus_line_continuation(self) -> None:
        # 3 個 = リテラル 1 個 + 行継続 1 個。実 bash: `echo a\\\`+改行+`b` → `a\b`
        tokens = pcp.tokenize("echo a\\\\\\\nb && git push origin main")
        self.assertEqual(
            tokens, ["echo", "a\\b", "&&", "git", "push", "origin", "main"]
        )
        self.assertNotIn(pcp.NEWLINE_TOKEN, tokens)
        self.assertTrue(pcp.is_git_push(tokens)[0])

    def test_four_backslashes_keep_the_newline_separator(self) -> None:
        tokens = pcp.tokenize("echo a\\\\\\\\\ngit push origin main")
        self.assertIn(pcp.NEWLINE_TOKEN, tokens)
        self.assertTrue(pcp.is_git_push(tokens)[0])

    def test_even_run_does_not_extend_optout_assignment_prefix(self) -> None:
        """opt-out 過大受理の別形（以前に閉じた形の復活）を塞ぐ。

        実 bash では `env` と `git push` は別コマンドで、代入は継承されない。
        改行 token が消えると代入列が `git` に直結し、opt-out が別コマンドへ波及する。
        """
        tokens, original_count = pcp.tokenize_with_boundary(
            "GDD_SKIP_PRE_PUSH_GATE=1 env \\\\\ngit push origin main"
        )
        self.assertEqual(original_count, len(tokens))
        self.assertIn(pcp.NEWLINE_TOKEN, tokens)
        self.assertLess(tokens.index(pcp.NEWLINE_TOKEN), tokens.index("git"))

    def test_backslash_run_not_followed_by_newline_is_preserved(self) -> None:
        # 行継続でないバックスラッシュ列を落とさない（過剰除去の防止）
        tokens = pcp.tokenize("echo a\\\\b && git push origin main")
        self.assertTrue(pcp.is_git_push(tokens)[0])

    def test_crlf_is_not_treated_as_line_continuation(self) -> None:
        """Attempt 5 advisory A-3（T-1 Carry Forward）: `\\` + CRLF は行継続として

        除去しない。実 bash は `\\` で **CR だけ**をエスケープし、続く LF は
        コマンド区切りとして残る（実測: `env \\`+CRLF+`git push` は env 非継承）。
        旧仕様（`\\`+CRLF も `\\`+LF と同様に完全除去）は改行 token が消えるため
        opt-out 受理面（T-2 `find_optout`）を過大受理させる。名前を
        `test_crlf_line_continuation_still_removed` から変更し、期待値を反転した。
        """
        tokens = pcp.tokenize("git \\\r\npush origin main")
        self.assertFalse(pcp.is_git_push(tokens)[0])


class NestedShellSurfaceTests(unittest.TestCase):
    """nested shell 展開が実 shell の `-c` 解釈と一致すること。"""

    def test_long_option_before_dash_c_is_not_mistaken(self) -> None:
        tokens = pcp.tokenize("bash --norc -c 'git push origin main'")
        self.assertTrue(pcp.is_git_push(tokens)[0])

    def test_double_dash_between_dash_c_and_command(self) -> None:
        tokens = pcp.tokenize("bash -c -- 'git push origin main'")
        self.assertTrue(pcp.is_git_push(tokens)[0])

    def test_clustered_short_options_still_expand(self) -> None:
        tokens = pcp.tokenize("bash -lc 'git push origin main'")
        self.assertTrue(pcp.is_git_push(tokens)[0])

    def test_two_level_nesting_expands(self) -> None:
        tokens = pcp.tokenize("bash -c 'bash -c \"git push origin main\"'")
        self.assertTrue(pcp.is_git_push(tokens)[0])

    def test_other_posix_shells_expand(self) -> None:
        for shell in ("sh", "zsh", "dash", "ksh"):
            with self.subTest(shell=shell):
                tokens = pcp.tokenize(f"{shell} -c 'git push origin main'")
                self.assertTrue(pcp.is_git_push(tokens)[0])

    def test_newline_inside_nested_command_string(self) -> None:
        tokens = pcp.tokenize("bash -c 'echo hi\ngit push origin main'")
        self.assertTrue(pcp.is_git_push(tokens)[0])

    def test_dash_c_after_command_separator_is_not_the_shell_argument(self) -> None:
        # `bash` と `-c` が別コマンドなら、その引数は shell に渡らない
        tokens = pcp.tokenize("bash; -c 'git push origin main'")
        self.assertNotIn("git", tokens)
        self.assertFalse(pcp.is_git_push(tokens)[0])


class SplitSegmentsTests(unittest.TestCase):
    """ADR-5: 区切り token + nested shell 展開グループでセグメントを切る。"""

    def test_separator_splits_into_independent_segments(self):
        segments = gcp.split_segments(
            "git worktree add /tmp/w -b codex/20260903-x origin/main && "
            "git switch -c codex/20260903-y"
        )
        self.assertEqual(len(segments), 2)
        self.assertIn("worktree", segments[0])
        self.assertIn("switch", segments[1])

    def test_nested_shell_expansion_becomes_its_own_segment(self):
        segments = gcp.split_segments(
            "bash -c 'git log HEAD' && "
            "git worktree add /tmp/w -b codex/20260903-x origin/main"
        )
        # 展開結果 ['git', 'log', 'HEAD'] が末尾へ融合せず、独立した
        # セグメントになっていること（融合すると origin/main の後段に
        # HEAD が混入し、正規手順が誤 deny される）
        worktree_segment = next(seg for seg in segments if "worktree" in seg)
        self.assertNotIn("HEAD", worktree_segment)

    def test_heredoc_body_is_stripped(self):
        segments = gcp.split_segments(
            "git commit -F - <<MSG\nuse git switch -c codex/x instead\nMSG"
        )
        joined = [" ".join(seg) for seg in segments]
        self.assertFalse(any("switch" in seg for seg in joined))

    def test_unknown_glued_punctuation_never_splits_git_segment(self):
        # PR #88 人間レビュー round 6 指摘 High: round 7 の regression test
        # (`test_glued_redirect_operator_does_not_truncate_refspec_scan`) は
        # `&>` 1 リテラルだけを固定しており、`_TWO_CHAR_OPERATORS` に列挙
        # されていない他の組み合わせ（`>|` 等）では、`_lex_segment` が
        # token 列全体を再分割していた当時の実装のまま同型の guard bypass
        # が残っていた（実 bash で再現確認: `git switch >|/dev/null -c
        # <branch>` は branch 作成を実行するが、`>|` を `>`+`|` に誤分割
        # すると `|` が区切りに一致し、branch 名を含む segment から git が
        # 消える）。単一リテラルではなく、`_TWO_CHAR_OPERATORS`（既知の複合
        # 演算子）にも実区切り（`COMMAND_SEPARATOR_TOKENS`）にも属さない
        # 全ての 2 文字 punctuation の組み合わせについて、`git switch` と
        # `-c <branch>` の間に割り込ませても同じ segment に留まることを
        # 固定する（現在の是正: `_lex_segment` は token 列を一切再分割
        # しないため、この性質は個々の演算子の網羅性に依存しない）。
        # 独立レビュー round 8 指摘 advisory: 除外集合をこの場でハード
        # コードすると、正本（`git_command_parse._TWO_CHAR_OPERATORS` /
        # `.COMMAND_SEPARATOR_TOKENS`）が変わってもテスト側の複製が追従
        # せず drift しうる。正本から直接参照する。
        punctuation_chars = "();<>|&"
        for first in punctuation_chars:
            for second in punctuation_chars:
                pair = first + second
                if pair in gcp.COMMAND_SEPARATOR_TOKENS or pair in gcp._TWO_CHAR_OPERATORS:
                    continue
                branch = f"codex/prop-{ord(first)}-{ord(second)}"
                command = f"git switch {pair}sentinel -c {branch}"
                with self.subTest(pair=pair):
                    segments = gcp.split_segments(command)
                    git_segments = [seg for seg in segments if "git" in seg]
                    self.assertTrue(
                        git_segments and branch in git_segments[0],
                        f"pair={pair!r} split git away from -c branch: {segments}",
                    )


if __name__ == "__main__":
    unittest.main()
