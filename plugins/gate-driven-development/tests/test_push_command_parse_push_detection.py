"""`push_command_parse` の `git push` の検出（global option を伴う形・コマンド先頭の判定）の単体テスト。

`test_push_command_parse.py` から分けた。

確かめる本体は `hooks/scripts/lib/push_command_parse.py`・`hooks/scripts/lib/git_command_parse.py`
（`tokenize` などは `git_command_parse` の定義を `push_command_parse` が再公開している）。
"""
from __future__ import annotations

import sys
import unittest

from _paths import PLUGIN_ROOT
sys.path.insert(0, str(PLUGIN_ROOT / "hooks" / "scripts" / "lib"))

import push_command_parse as pcp  # noqa: E402


class IsGitPushTests(unittest.TestCase):
    def test_detects_plain_git_push(self) -> None:
        tokens = pcp.tokenize("git push origin main")
        is_push, index = pcp.is_git_push(tokens)
        self.assertTrue(is_push)
        self.assertEqual(tokens[index], "git")

    def test_detects_absolute_git_path(self) -> None:
        tokens = pcp.tokenize("/usr/bin/git push -u origin HEAD")
        is_push, index = pcp.is_git_push(tokens)
        self.assertTrue(is_push)
        self.assertEqual(index, 0)

    def test_rejects_non_push_git_command(self) -> None:
        tokens = pcp.tokenize("git rev-parse HEAD")
        is_push, _ = pcp.is_git_push(tokens)
        self.assertFalse(is_push)

    def test_rejects_non_git_command(self) -> None:
        tokens = pcp.tokenize("npm run push")
        is_push, _ = pcp.is_git_push(tokens)
        self.assertFalse(is_push)


class IsGitPushGlobalOptionTests(unittest.TestCase):
    """git global option を伴う push の検出（design.md §判定順 step 3 / AC-17）。

    step 3 が非検出だと step 4（候補 root 列挙）・step 5（`--git-dir` の block）に
    到達せず gate 全体が素通りする。global option の読み飛ばしを固定する。
    """

    def test_detects_dash_capital_c_directory(self) -> None:
        tokens = pcp.tokenize("git -C /repo/a push origin main")
        is_push, index = pcp.is_git_push(tokens)
        self.assertTrue(is_push)
        self.assertEqual(index, 0)

    def test_detects_dash_capital_c_equals_form(self) -> None:
        tokens = pcp.tokenize("git -C=/repo/a push origin main")
        is_push, index = pcp.is_git_push(tokens)
        self.assertTrue(is_push)
        self.assertEqual(index, 0)

    def test_detects_git_dir_equals_form(self) -> None:
        tokens = pcp.tokenize("git --git-dir=/gdd/.git push origin main")
        is_push, index = pcp.is_git_push(tokens)
        self.assertTrue(is_push)
        self.assertEqual(index, 0)

    def test_detects_git_dir_separate_argument(self) -> None:
        tokens = pcp.tokenize("git --git-dir /gdd/.git push origin main")
        is_push, _ = pcp.is_git_push(tokens)
        self.assertTrue(is_push)

    def test_detects_work_tree_form(self) -> None:
        tokens = pcp.tokenize("git --work-tree=/gdd --git-dir=/gdd/.git push")
        is_push, _ = pcp.is_git_push(tokens)
        self.assertTrue(is_push)

    def test_detects_config_override(self) -> None:
        tokens = pcp.tokenize("git -c user.name=x push")
        is_push, _ = pcp.is_git_push(tokens)
        self.assertTrue(is_push)

    def test_detects_combined_global_options(self) -> None:
        tokens = pcp.tokenize("git -c a=b --no-pager -C /repo/a push origin main")
        is_push, index = pcp.is_git_push(tokens)
        self.assertTrue(is_push)
        self.assertEqual(index, 0)

    def test_detects_global_options_inside_nested_shell(self) -> None:
        tokens = pcp.tokenize("bash -c 'git -C /repo/a push origin main'")
        is_push, index = pcp.is_git_push(tokens)
        self.assertTrue(is_push)
        self.assertEqual(tokens[index], "git")

    def test_rejects_dash_capital_c_without_subcommand(self) -> None:
        tokens = pcp.tokenize("git -C /repo/a")
        is_push, _ = pcp.is_git_push(tokens)
        self.assertFalse(is_push)

    def test_rejects_push_consumed_as_dash_capital_c_argument(self) -> None:
        # `git -C push` は `-C` の引数が push であり subcommand ではない
        tokens = pcp.tokenize("git -C push")
        is_push, _ = pcp.is_git_push(tokens)
        self.assertFalse(is_push)

    def test_rejects_global_options_with_non_push_subcommand(self) -> None:
        tokens = pcp.tokenize("git -C /repo/a rev-parse HEAD")
        is_push, _ = pcp.is_git_push(tokens)
        self.assertFalse(is_push)


class IsGitPushAtCommandStartTests(unittest.TestCase):
    """外部副作用（認証付き `gh` 呼び出し）を伴う hook 専用の狭い判定。

    `is_git_push` は pre-push gate 向けに token 列全体を fail-closed で走査する
    （`echo git push` 等の過検出を意図的に許容: design.md § Honest
    Limitations）。この広い判定をネットワーク I/O を伴う hook にそのまま使うと、
    実行されないコマンド文面（echo 経由 / コメント代わりの行頭以外の出現）でも
    認証付き `gh` が呼ばれる（PR #88 人間レビュー指摘 High-2）。この関数は
    「git token がコマンド先頭（index 0、または区切り token 直後）に現れる」
    場合だけを対象にする。
    """

    def test_accepts_plain_command_start_push(self) -> None:
        tokens = pcp.tokenize("git push origin main")
        is_push, index = pcp.is_git_push_at_command_start(tokens, len(tokens))
        self.assertTrue(is_push)
        self.assertEqual(index, 0)

    def test_accepts_dash_capital_c_command_start_push(self) -> None:
        tokens = pcp.tokenize("git -C /repo/a push origin main")
        is_push, index = pcp.is_git_push_at_command_start(tokens, len(tokens))
        self.assertTrue(is_push)
        self.assertEqual(index, 0)

    def test_accepts_env_assignment_prefixed_push(self) -> None:
        # `NAME=VALUE git push ...` は実 bash が実際に実行する標準的な形
        # （opt-out の command-prefix 形と同じ）であり、過検出ではない。
        # find_optout と矛盾させないため、代入列は command-start 判定を
        # 妨げない。
        tokens = pcp.tokenize("GDD_SKIP_PRE_PUSH_GATE=1 git push origin main")
        is_push, index = pcp.is_git_push_at_command_start(tokens, len(tokens))
        self.assertTrue(is_push)
        self.assertEqual(tokens[index], "git")

    def test_rejects_echo_prefixed_push(self) -> None:
        tokens = pcp.tokenize("echo git push origin main")
        is_push, _ = pcp.is_git_push_at_command_start(tokens, len(tokens))
        self.assertFalse(is_push)

    def test_rejects_hash_prefixed_push(self) -> None:
        # 実 bash と同じく、語頭の `#` から行末まではコメントとして落ちる
        # （git は実行されない）。
        tokens = pcp.tokenize("# git push origin main")
        is_push, _ = pcp.is_git_push_at_command_start(tokens, len(tokens))
        self.assertFalse(is_push)

    def test_accepts_push_after_and_separator(self) -> None:
        tokens = pcp.tokenize("echo hi && git push origin main")
        is_push, index = pcp.is_git_push_at_command_start(tokens, len(tokens))
        self.assertTrue(is_push)
        self.assertEqual(tokens[index], "git")

    def test_accepts_push_after_newline(self) -> None:
        tokens = pcp.tokenize("cd .\ngit push origin main")
        is_push, _ = pcp.is_git_push_at_command_start(tokens, len(tokens))
        self.assertTrue(is_push)

    def test_finds_real_push_after_earlier_false_match(self) -> None:
        # 先頭の `echo git push foo` は過検出源だが command-start ではない。
        # `&&` の直後にある 2 つ目の `git push` は本物なので見逃してはならない
        # （is_git_push の最初の一致だけを見ると誤って False になる）。
        tokens = pcp.tokenize("echo git push foo && git push origin bar")
        is_push, index = pcp.is_git_push_at_command_start(tokens, len(tokens))
        self.assertTrue(is_push)
        self.assertEqual(index, 5)

    def test_rejects_when_only_non_command_start_match_exists(self) -> None:
        tokens = pcp.tokenize("echo git push foo")
        is_push, _ = pcp.is_git_push_at_command_start(tokens, len(tokens))
        self.assertFalse(is_push)

    def test_rejects_bash_c_expansion(self) -> None:
        tokens, raw_count = pcp.tokenize_with_boundary("bash -c 'git push origin main'")
        is_push, _ = pcp.is_git_push_at_command_start(tokens, raw_count)
        self.assertFalse(is_push)

    def test_rejects_push_after_then_reserved_word_documented_limitation(self) -> None:
        # Honest Limitations（未対応、既知。独立レビュー round 4 で指摘）:
        # `then` は実 bash では実際にコマンドを実行する位置だが、shell 予約語
        # （then/do/else/elif/!）の一覧化は際限が無いため対応を見送った。
        # fail-safe 側（nudge が出ないだけ）に倒れることを固定する。
        tokens = pcp.tokenize("if [ -d .git ]; then git push origin main; fi")
        is_push, _ = pcp.is_git_push_at_command_start(tokens, len(tokens))
        self.assertFalse(is_push)

    def test_accepts_push_inside_brace_group(self) -> None:
        tokens = pcp.tokenize("{ git push origin main; }")
        is_push, _ = pcp.is_git_push_at_command_start(tokens, len(tokens))
        self.assertTrue(is_push)

    def test_accepts_push_after_subshell_close_paren(self) -> None:
        tokens = pcp.tokenize("(cd /tmp) && git push origin main")
        is_push, _ = pcp.is_git_push_at_command_start(tokens, len(tokens))
        self.assertTrue(is_push)

    def test_accepts_push_after_glued_separator_cluster(self) -> None:
        # PR #88 人間レビュー round 5 指摘 Medium: `shlex(punctuation_chars=True)`
        # は隣接する区切り文字を無条件に 1 token へ集約するため、`)` と `;` の
        # 間に空白が無いと `);` という未知の複合 token になり、区切り集合との
        # 完全一致を要求する `_at_true_command_start` を素通りして「git push が
        # 検出されない」fail-open になっていた（nudge が出ないだけで block は
        # しないが、review-followup nudge の目的である「push 追従の取りこぼし」を再発させる）。
        for command in (
            "(cd /repo); git push origin main",
            "(cd /repo);;git push origin main",
            "(cd /repo))git push origin main",
            "(cd /repo)&&git push origin main",
            "(cd /repo)||git push origin main",
        ):
            with self.subTest(command=command):
                tokens = pcp.tokenize(command)
                is_push, _ = pcp.is_git_push_at_command_start(tokens, len(tokens))
                self.assertTrue(is_push, msg=f"push 非検出: {command!r} tokens={tokens!r}")

    def test_start_parameter_skips_earlier_command_start_matches(self) -> None:
        # 呼び出し側（hook）が「1 つ目の command-start 一致は除外対象の flag
        # 付きだったので続きを探す」形で反復できるようにするための `start`。
        tokens = pcp.tokenize(
            "git push --dry-run origin main && git push origin main"
        )
        first_is_push, first_index = pcp.is_git_push_at_command_start(
            tokens, len(tokens)
        )
        self.assertTrue(first_is_push)
        second_is_push, second_index = pcp.is_git_push_at_command_start(
            tokens, len(tokens), start=first_index + 1
        )
        self.assertTrue(second_is_push)
        self.assertGreater(second_index, first_index)

    def test_start_parameter_returns_false_when_no_further_match(self) -> None:
        tokens = pcp.tokenize("git push origin main")
        is_push, _ = pcp.is_git_push_at_command_start(tokens, len(tokens), start=1)
        self.assertFalse(is_push)

    def test_rejects_non_push_command(self) -> None:
        tokens = pcp.tokenize("git rev-parse HEAD")
        is_push, _ = pcp.is_git_push_at_command_start(tokens, len(tokens))
        self.assertFalse(is_push)

    def test_push_inside_quoted_string_with_embedded_newline_is_not_at_command_start(
        self,
    ) -> None:
        # 二重引用符の中の実改行は区切りではない（字句解析は引用符を行をまたいで追う）。
        # bash・zsh とも `echo` だけを実行し、`git push` は引数の文字列の中にある。
        tokens = pcp.tokenize('echo "手順\ngit push origin x\nです"')
        is_push, _ = pcp.is_git_push_at_command_start(tokens, len(tokens))
        self.assertFalse(is_push)


if __name__ == "__main__":
    unittest.main()
