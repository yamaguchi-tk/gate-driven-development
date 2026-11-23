"""`push_command_parse` の push 対象の解決（`push` subcommand の位置・候補 root・`cd` 走査・refspec の分類）の単体テスト。

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


class PushSubcommandIndexTests(unittest.TestCase):
    """`push` subcommand の位置を API から取得できること（T-4 の refspec 走査起点）。"""

    def test_plain_form(self) -> None:
        tokens = pcp.tokenize("git push origin main")
        _, git_index = pcp.is_git_push(tokens)
        self.assertEqual(pcp.push_subcommand_index(tokens, git_index), 1)

    def test_global_option_form(self) -> None:
        tokens = pcp.tokenize("git -C /repo/a push origin main")
        _, git_index = pcp.is_git_push(tokens)
        index = pcp.push_subcommand_index(tokens, git_index)
        self.assertEqual(tokens[index], "push")
        self.assertEqual(tokens[index + 1 :], ["origin", "main"])

    def test_returns_minus_one_when_not_a_push(self) -> None:
        tokens = pcp.tokenize("git rev-parse HEAD")
        self.assertEqual(pcp.push_subcommand_index(tokens, 0), -1)

    def test_ambiguous_arity_takes_the_earliest_push(self) -> None:
        # 未知 flag は arity 不明なので push 候補が 2 つ出る。refspec 走査は手前を採り、
        # 余分な token を refspec として数える = ambiguous 側（fail-closed）に倒す
        tokens = pcp.tokenize("git --totally-unknown push push")
        _, git_index = pcp.is_git_push(tokens)
        self.assertEqual(pcp.push_subcommand_index(tokens, git_index), 2)


class ResolveCandidateRootsTests(unittest.TestCase):
    def test_dash_c_wins_over_payload_cwd(self) -> None:
        tokens = pcp.tokenize("git -C /repo/a push origin main")
        is_push, git_index = pcp.is_git_push(tokens)
        result = pcp.resolve_candidate_roots(
            tokens, git_index, payload_cwd="/repo/b", process_cwd="/repo/c"
        )
        self.assertEqual(result["roots"], ["/repo/a"])
        self.assertFalse(result["unresolvable"])

    def test_dash_c_equals_form(self) -> None:
        tokens = pcp.tokenize("git -C=/repo/a push origin main")
        is_push, git_index = pcp.is_git_push(tokens)
        result = pcp.resolve_candidate_roots(
            tokens, git_index, payload_cwd="/repo/b", process_cwd="/repo/c"
        )
        self.assertEqual(result["roots"], ["/repo/a"])

    def test_cd_prefix_used_when_no_dash_c(self) -> None:
        tokens = pcp.tokenize("cd /repo/a && git push origin main")
        is_push, git_index = pcp.is_git_push(tokens)
        result = pcp.resolve_candidate_roots(
            tokens, git_index, payload_cwd="/repo/b", process_cwd="/repo/c"
        )
        self.assertEqual(result["roots"], ["/repo/a"])

    def test_falls_back_to_payload_cwd(self) -> None:
        tokens = pcp.tokenize("git push origin main")
        is_push, git_index = pcp.is_git_push(tokens)
        result = pcp.resolve_candidate_roots(
            tokens, git_index, payload_cwd="/repo/b", process_cwd="/repo/c"
        )
        self.assertEqual(result["roots"], ["/repo/b"])

    def test_falls_back_to_process_cwd_when_no_payload_cwd(self) -> None:
        tokens = pcp.tokenize("git push origin main")
        is_push, git_index = pcp.is_git_push(tokens)
        result = pcp.resolve_candidate_roots(
            tokens, git_index, payload_cwd="", process_cwd="/repo/c"
        )
        self.assertEqual(result["roots"], ["/repo/c"])

    def test_git_dir_marks_unresolvable_and_adds_candidate(self) -> None:
        tokens = pcp.tokenize("git --git-dir=/gdd-repo/.git push origin main")
        is_push, git_index = pcp.is_git_push(tokens)
        result = pcp.resolve_candidate_roots(
            tokens, git_index, payload_cwd="/other", process_cwd="/other"
        )
        self.assertTrue(result["unresolvable"])
        self.assertIn("/gdd-repo", result["roots"])

    def test_work_tree_marks_unresolvable(self) -> None:
        tokens = pcp.tokenize("git --work-tree=/gdd-repo push origin main")
        is_push, git_index = pcp.is_git_push(tokens)
        result = pcp.resolve_candidate_roots(
            tokens, git_index, payload_cwd="/other", process_cwd="/other"
        )
        self.assertTrue(result["unresolvable"])

    def test_brace_group_cd_ignored_with_default_cd_separators(self) -> None:
        # 既定値（run-pre-push-gate-hook.sh と共有）は不変であることを固定する。
        # `{` は既定の COMMAND_SEPARATOR_TOKENS には含まれないため、brace
        # group 内の `cd` は「コマンド先頭」と見なされず候補にならない。
        tokens = pcp.tokenize("{ cd /other/repo; git push; }")
        is_push, git_index = pcp.is_git_push_at_command_start(tokens, len(tokens))
        self.assertTrue(is_push)
        result = pcp.resolve_candidate_roots(
            tokens, git_index, payload_cwd="/payload", process_cwd="/proc"
        )
        self.assertEqual(result["roots"], ["/payload"])

    def test_brace_group_cd_used_with_widened_cd_separators(self) -> None:
        # PR #88 人間レビュー round 5 指摘 Medium: push 検出は `{` を command-
        # start に含めているのに、cd 解決が既定の狭い集合のままだと
        # `{ cd /other/repo; git push; }` が誤った root（payload/process cwd）
        # を候補にし、無関係な repo の PR 有無で `gh` を呼んでしまう。
        # `PUSH_DETECTION_CD_SEPARATORS` を明示すれば brace group 内の `cd`
        # も正しく拾えることを固定する。
        tokens = pcp.tokenize("{ cd /other/repo; git push; }")
        is_push, git_index = pcp.is_git_push_at_command_start(tokens, len(tokens))
        self.assertTrue(is_push)
        result = pcp.resolve_candidate_roots(
            tokens,
            git_index,
            payload_cwd="/payload",
            process_cwd="/proc",
            cd_separators=pcp.PUSH_DETECTION_CD_SEPARATORS,
        )
        self.assertEqual(result["roots"], ["/other/repo"])


class CdScanCommandStartTests(unittest.TestCase):
    """`cd` 走査のコマンド先頭規律と引数検証（impl-gate Attempt 1 の M-1）。

    区切り token / option token をそのまま候補 root に採ると、hook 側の
    `[[ -d "$_root" ]]` で候補が全滅して `ANY_ACTIVE=false` になり、
    **無記録の exit 0（fail-open）** になる。AC-17 の「`cd` が使えなければ
    payload cwd → process cwd へ落ちる」優先順にも反する。
    """

    #: (command, 期待 roots)。gate が実測した誤解決 5 形 + 肯定形。
    CASES = (
        # 引数を取らない `cd`（区切り token を root にしない）
        ("cd && git push origin main", ["/payload"]),
        ("cd; git push origin main", ["/payload"]),
        # option だけの `cd`（`cd -` は直前ディレクトリへ戻るので root を決められない）
        ("cd - && git push origin main", ["/payload"]),
        # option を読み飛ばして本来の引数を採る
        ("cd -P /repo/a && git push origin main", ["/repo/a"]),
        # コマンド先頭でない `cd`（`echo` の引数なので cd は実行されない）
        ("echo cd /tmp && git push origin main", ["/payload"]),
        # 後のコマンド先頭 `cd` が勝つ（bash は直前 = payload cwd へ戻る）
        ("cd /repo/a; cd - && git push origin main", ["/payload"]),
        # 肯定形: 真の `cd` は従来どおり候補 root になる
        ("cd /repo/a && git push origin main", ["/repo/a"]),
    )

    def test_cd_candidate_roots(self) -> None:
        for command, expected in self.CASES:
            with self.subTest(command=command):
                tokens = pcp.tokenize(command)
                is_push, git_index = pcp.is_git_push(tokens)
                self.assertTrue(is_push, msg=f"push 非検出: {command!r}")
                result = pcp.resolve_candidate_roots(
                    tokens, git_index, payload_cwd="/payload", process_cwd="/proc"
                )
                self.assertEqual(result["roots"], expected)

    def test_rejects_cd_root_disguised_by_unenumerated_glued_redirect(self) -> None:
        # PR #88 人間レビュー round 6 指摘 High（`find_optout` と同型）:
        # `>|cd /tmp/evil && git push origin main` の `>|` は実 bash では
        # noclobber 上書き付き redirect 演算子で、`cd` はコマンド先頭には
        # 無くその引数扱いにもならない（`cd` はここでは実行されない別の
        # 語）。是正前は `>|` が `>`+`|` に割れ、末尾の `|` が既定の区切り
        # 集合に一致してしまい、実行されない `cd /tmp/evil` を候補 root に
        # してしまっていた（誤った root は hook 側のディレクトリ実在
        # チェックで候補が全滅すると無記録の exit 0 = pre-push gate の
        # fail-open になりうる）。`_find_cd_root` は `token in separators`
        # の完全一致に留め、payload cwd へ安全に fallback することを固定する。
        tokens = pcp.tokenize(">|cd /tmp/evil && git push origin main")
        is_push, git_index = pcp.is_git_push(tokens)
        self.assertTrue(is_push)
        result = pcp.resolve_candidate_roots(
            tokens, git_index, payload_cwd="/payload", process_cwd="/proc"
        )
        self.assertEqual(result["roots"], ["/payload"])


class ClassifyRefspecTests(unittest.TestCase):
    """AC-16: push 対象 ref の tip を一意解決できるかを判定する（tasklist T-4 Step 1）。"""

    def _classify(self, command: str) -> dict:
        tokens = pcp.tokenize(command)
        is_push, git_index = pcp.is_git_push(tokens)
        self.assertTrue(is_push, msg=f"push として検出されない: {command!r}")
        return pcp.classify_refspec(tokens, git_index)

    def test_plain_push_u_origin_branch_not_ambiguous(self) -> None:
        # `ambiguous` だけでなく `explicit_ref` まで assert する。`-u` を値を取る
        # flag として誤登録すると次 token（remote 名）が読み飛ばされ、refspec が
        # 丸ごと落ちて `explicit_ref=None`（= ref 省略 → HEAD 解決）になる
        for command in (
            "git push -u origin feature-x",
            "git push --set-upstream origin feature-x",
        ):
            with self.subTest(command=command):
                result = self._classify(command)
                self.assertFalse(result["ambiguous"])
                self.assertEqual(result["explicit_ref"], "feature-x")

    def test_set_upstream_with_colon_refspec_keeps_explicit_ref(self) -> None:
        # design.md § fail-open 経路 5: `feature-x:main` は local tip と remote が
        # ずれる形。`-u` を前置しただけで explicit_ref が落ちてはならない
        result = self._classify("git push -u origin feature-x:main")
        self.assertFalse(result["ambiguous"])
        self.assertEqual(result["explicit_ref"], "feature-x")

    def test_set_upstream_with_multiple_refspecs_is_ambiguous(self) -> None:
        result = self._classify("git push -u origin main feature-x")
        self.assertTrue(result["ambiguous"])
        self.assertIsNone(result["explicit_ref"])

    def test_set_upstream_after_global_option_keeps_explicit_ref(self) -> None:
        result = self._classify("git -C /repo/a push -u origin feature-x")
        self.assertFalse(result["ambiguous"])
        self.assertEqual(result["explicit_ref"], "feature-x")

    def test_refspec_scan_stops_at_command_separator(self) -> None:
        # 区切り以降の token は別コマンドなので refspec に数えない。数えると
        # 後続コマンドの語数で ambiguous に転ぶ（無関係な over-block）
        result = self._classify("git push origin feature-x && echo done")
        self.assertFalse(result["ambiguous"])
        self.assertEqual(result["explicit_ref"], "feature-x")

    def test_glued_redirect_operator_does_not_truncate_refspec_scan(self) -> None:
        # PR #88 独立レビュー round 7 指摘 High/blocking: round 5 の tokenizer
        # 修正を token 列全体（`_lex_segment`）に適用すると、`&>` のような
        # 複合 redirection 演算子が `&`（区切り）+ `>` に割れ、`--all` の
        # 手前で走査が打ち切られて `ambiguous` が真の False に退行していた
        # （実 bash は `git push --all origin` を実行する）。token 列は
        # 変更せず command-start 判定だけを局所的に広げる方式に是正した。
        result = self._classify("git push &>/dev/null --all origin")
        self.assertTrue(result["ambiguous"])
        self.assertIsNone(result["explicit_ref"])

    def test_branches_flag_is_ambiguous(self) -> None:
        # 実 git で `--all` の alias（`git push -h`: `--[no-]branches  alias of --all`）
        result = self._classify("git push --branches origin")
        self.assertTrue(result["ambiguous"])
        self.assertIsNone(result["explicit_ref"])

    def test_ref_omitted_not_ambiguous(self) -> None:
        tokens = pcp.tokenize("git push")
        is_push, git_index = pcp.is_git_push(tokens)
        result = pcp.classify_refspec(tokens, git_index)
        self.assertFalse(result["ambiguous"])
        self.assertIsNone(result["explicit_ref"])

    def test_explicit_local_colon_remote_refspec_not_ambiguous(self) -> None:
        tokens = pcp.tokenize("git push origin feature-x:main")
        is_push, git_index = pcp.is_git_push(tokens)
        result = pcp.classify_refspec(tokens, git_index)
        self.assertFalse(result["ambiguous"])
        self.assertEqual(result["explicit_ref"], "feature-x")

    def test_all_flag_is_ambiguous(self) -> None:
        tokens = pcp.tokenize("git push --all origin")
        is_push, git_index = pcp.is_git_push(tokens)
        result = pcp.classify_refspec(tokens, git_index)
        self.assertTrue(result["ambiguous"])

    def test_mirror_flag_is_ambiguous(self) -> None:
        tokens = pcp.tokenize("git push --mirror origin")
        is_push, git_index = pcp.is_git_push(tokens)
        result = pcp.classify_refspec(tokens, git_index)
        self.assertTrue(result["ambiguous"])

    def test_multiple_refspecs_are_ambiguous(self) -> None:
        tokens = pcp.tokenize("git push origin main feature-x")
        is_push, git_index = pcp.is_git_push(tokens)
        result = pcp.classify_refspec(tokens, git_index)
        self.assertTrue(result["ambiguous"])

    def test_redirection_is_not_counted_as_a_refspec(self) -> None:
        """shell のリダイレクト token を refspec と数えない（2026-08-30 実測）。

        `git push origin <branch> 2>&1 | tail -15` が `refspec-ambiguous` で
        block されていた。`_lex` は `2>&1` を `2` / `>&` / `1` の 3 token に割るため、
        fd 番号 `2` と転送先 `1` が positional に積まれて refspec が 3 個に見える。
        リダイレクトは push 対象 ref を変えないので、演算子と転送先（および
        直前の fd 番号）は refspec 判定から除外する。
        """
        for command, expected in (
            ("git push origin feature-x 2>&1 | tail -15", "feature-x"),
            ("git push origin feature-x > /tmp/out.log", "feature-x"),
            ("git push origin feature-x 2> /tmp/err.log", "feature-x"),
            ("git push origin feature-x &> /tmp/all.log", "feature-x"),
            ("git push origin feature-x >>/tmp/out.log 2>&1", "feature-x"),
            ("git push -u origin feature-x 2>&1", "feature-x"),
            # リダイレクトを挟んでも本物の refspec は positional として残る
            ("git push origin > /tmp/out.log feature-x", "feature-x"),
        ):
            with self.subTest(command=command):
                tokens = pcp.tokenize(command)
                is_push, git_index = pcp.is_git_push(tokens)
                self.assertTrue(is_push, msg=command)
                result = pcp.classify_refspec(tokens, git_index)
                self.assertFalse(result["ambiguous"], msg=command)
                self.assertEqual(result["explicit_ref"], expected, msg=command)

    def test_redirection_does_not_hide_a_second_refspec(self) -> None:
        """リダイレクト読み飛ばしで本物の複数 refspec を取りこぼさない（fail-open 側）。"""
        tokens = pcp.tokenize("git push origin main > /tmp/out.log feature-x")
        _, git_index = pcp.is_git_push(tokens)
        self.assertTrue(pcp.classify_refspec(tokens, git_index)["ambiguous"])

    def test_global_option_before_push_not_ambiguous(self) -> None:
        # global option を伴う形（gdd advisory A-11 隣接の同型リスク: git_index から
        # 単純に +2 すると `-C <dir>` の `<dir>` / `push` を refspec と誤認して
        # over-block する）。push_subcommand_index 経由の解決を固定する。
        tokens = pcp.tokenize("git -C /repo/a push origin feature-x")
        is_push, git_index = pcp.is_git_push(tokens)
        result = pcp.classify_refspec(tokens, git_index)
        self.assertFalse(result["ambiguous"])
        self.assertEqual(result["explicit_ref"], "feature-x")


if __name__ == "__main__":
    unittest.main()
