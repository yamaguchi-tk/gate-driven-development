"""`gh pr merge` コマンドライン文字列パーサ（`lib/gh_command_parse.py`）の契約テスト。

shell の引用・リダイレクト・パイプ・入れ子 interpreter 越しの実行など、
「対象コマンドを 1 つに決められるか」という parse 精度そのものを検査する。
state.md の証跡フィールド parser（`gdd_parse_merge_gate_field`）とは扱う対象が
異なるため別ファイルへ分けた（`tests/test_merge_gate_hook.py` 分割）。
"""
from __future__ import annotations

import os
import sys
import unittest

from _merge_gate_support import PLUGIN_ROOT
from _timing_budget import hook_timeout_seconds, timing_budget

sys.path.insert(0, str(PLUGIN_ROOT / "hooks" / "scripts"))

from lib.gh_command_parse import (  # noqa: E402
    _collect_nested_shell_layers,
    _extract_cd_target,
    _tokenize,
    parse_gh_pr_merge,
)

#: #4/#5 の壁時計 backstop。`run-merge-gate-hook.sh` の運用 timeout ÷ 2。
#: hook 予算全体ではなく parse 部分だけを in-process で測るため「hook
#: 予算の部分集合に対する上限」という弱い意味になる（design.md 閾値
#: マトリクス参照）。それでも hook timeout から導出する形は崩さない。
WALL_BACKSTOP_SEC = hook_timeout_seconds("run-merge-gate-hook.sh") / 2


class GhCommandParseTests(unittest.TestCase):
    def test_plain_pr_merge_with_number(self):
        result = parse_gh_pr_merge("gh pr merge 123", "", "/repo")
        self.assertTrue(result["is_merge"])
        self.assertEqual(result["pr_number"], "123")
        self.assertIsNone(result["repo_flag"])

    def test_pr_merge_with_repo_flag(self):
        result = parse_gh_pr_merge("gh pr merge -R org/other 123", "", "/repo")
        self.assertTrue(result["is_merge"])
        self.assertEqual(result["repo_flag"], "org/other")

    def test_pr_merge_with_url_argument(self):
        url = "https://github.com/acme/widgets/pull/42"
        result = parse_gh_pr_merge(f"gh pr merge {url}", "", "/repo")
        self.assertTrue(result["is_merge"])
        self.assertEqual(result["pr_url"], url)

    def test_branch_name_argument_is_unresolvable(self):
        result = parse_gh_pr_merge("gh pr merge feature-branch", "", "/repo")
        self.assertTrue(result["is_merge"])
        self.assertTrue(result["unresolvable"])

    def test_heredoc_body_is_not_a_command(self):
        cmd = 'git commit -F - <<MSG\nwrites about gh pr merge in prose\nMSG'
        result = parse_gh_pr_merge(cmd, "", "/repo")
        self.assertFalse(result["is_merge"])

    def test_interpreter_heredoc_body_is_a_command(self):
        # gate #16 M-A: heredoc は「データを渡す形」であると同時に「コマンドを
        # 実行する形」でもある。introducer 行が interpreter なら本文は実行される。
        for cmd in (
            "bash <<'EOF'\ngh pr merge 42\nEOF",
            "bash -s <<EOF\ngh pr merge 42\nEOF",
        ):
            with self.subTest(cmd=cmd):
                result = parse_gh_pr_merge(cmd, "", "/repo")
                self.assertTrue(result["is_merge"])
                self.assertEqual(result["pr_number"], "42")

    def test_executed_heredoc_body_through_ampersand_redirect_is_detected(self):
        # git_command_parse.py の同型 `_PIPELINE_BOUNDARY_RE` に見つかった欠陥
        # （PR #28 Copilot review）と同じバグ。`|&`/`&>`/`<&` に含まれる `&` を
        # 無条件に heredoc 所有 pipeline の境界として扱うと、interpreter 名
        # （`bash`）が走査範囲外に落ち、heredoc 本文内の `gh pr merge` が
        # merge-gate から不可視になる（guard bypass）。
        for cmd in (
            "cat <<'EOF' |& bash\ngh pr merge 999\nEOF",
            "bash <<'EOF' &> /tmp/gdd-probe.log\ngh pr merge 999\nEOF",
            "cat <<'EOF' 3<&0 | bash\ngh pr merge 999\nEOF",
        ):
            with self.subTest(cmd=cmd):
                result = parse_gh_pr_merge(cmd, "", "/repo")
                self.assertTrue(result["is_merge"])
                self.assertEqual(result["pr_number"], "999")

    def test_non_merge_gh_command_is_ignored(self):
        result = parse_gh_pr_merge("gh pr view 123", "", "/repo")
        self.assertFalse(result["is_merge"])

    def test_gh_repo_env_flags_conflict(self):
        os.environ["GH_REPO"] = "acme/widgets"
        try:
            result = parse_gh_pr_merge("gh pr merge 123", "", "/repo")
            self.assertTrue(result["env_repo_conflict"])
        finally:
            del os.environ["GH_REPO"]

    def test_admin_flag_still_detected_as_merge(self):
        result = parse_gh_pr_merge("gh pr merge --admin 123", "", "/repo")
        self.assertTrue(result["is_merge"])

    def test_repo_flag_before_subcommand_short_form_is_captured(self):
        # F-1: gh 2.93.0 実測で sub-command 前の -R は受理される
        # （gate #10 handoff: `gh -R foo/bar pr merge 999999 --dry-run` は
        # `unknown flag: --dry-run` = -R は受理済み）。
        result = parse_gh_pr_merge("gh -R org/other pr merge 123", "", "/repo")
        self.assertTrue(result["is_merge"])
        self.assertEqual(result["repo_flag"], "org/other")
        self.assertEqual(result["pr_number"], "123")

    def test_repo_flag_before_subcommand_long_form_is_captured(self):
        result = parse_gh_pr_merge("gh --repo org/other pr merge 123", "", "/repo")
        self.assertEqual(result["repo_flag"], "org/other")

    def test_repo_flag_before_subcommand_equals_form_is_captured(self):
        result = parse_gh_pr_merge("gh --repo=org/other pr merge 123", "", "/repo")
        self.assertEqual(result["repo_flag"], "org/other")

    def test_env_repo_command_prefix_sets_conflict(self):
        # F-2: プロセス env だけでなく token 列の command-prefix も検出する
        result = parse_gh_pr_merge("GH_REPO=org/other gh pr merge 123", "", "/repo")
        self.assertTrue(result["env_repo_conflict"])

    def test_env_host_command_prefix_with_env_builtin_sets_conflict(self):
        result = parse_gh_pr_merge("env GH_HOST=example.com gh pr merge 123", "", "/repo")
        self.assertTrue(result["env_repo_conflict"])

    def test_env_repo_conflict_is_false_when_absent(self):
        # advisory-1: 否定側 assert（ambient env 汚染の検出漏れ防止）
        result = parse_gh_pr_merge("gh pr merge 123", "", "/repo")
        self.assertFalse(result["env_repo_conflict"])

    def test_subject_flag_value_is_not_read_as_branch_arg(self):
        # F-3: 値を取る flag の値が branch 名として unresolvable に倒れない
        result = parse_gh_pr_merge(
            'gh pr merge 123 --squash --subject "feat: x"', "", "/repo"
        )
        self.assertEqual(result["pr_number"], "123")
        self.assertFalse(result["unresolvable"])
        self.assertIsNone(result["branch_arg"])

    def test_body_flag_value_is_not_read_as_branch_arg(self):
        result = parse_gh_pr_merge(
            'gh pr merge --squash --body "body text" 123', "", "/repo"
        )
        self.assertEqual(result["pr_number"], "123")
        self.assertFalse(result["unresolvable"])

    # --- gate #14 M-1: リダイレクションを位置引数と誤読しない --------------------
    #
    # `shlex(punctuation_chars=True)` は `<` `>` `>&` を独立 token として返す。
    # 打ち切り集合が `&&`/`;`/`||`/`|` だけだと、これらが「ブランチ名」として
    # 読まれて `unresolvable=True` が立ち、全証跡が valid でも恒久の不足通知になる。
    def test_redirection_operators_are_not_positional_arguments(self):
        for command in (
            "gh pr merge 7 </dev/null",
            "gh pr merge 7 > /tmp/x.log",
            "gh pr merge 7 >> /tmp/x.log",
            "gh pr merge 7 2> /tmp/x.log",
            "gh pr merge 7 2>&1",
            "gh pr merge 7 | tee /tmp/x.log",
        ):
            with self.subTest(command=command):
                result = parse_gh_pr_merge(command, "", "/repo")
                self.assertTrue(result["is_merge"])
                self.assertEqual(result["pr_number"], "7")
                self.assertIsNone(result["branch_arg"])
                self.assertFalse(result["unresolvable"])

    def test_bare_fd_prefix_is_not_read_as_a_pr_number(self):
        # `gh pr merge 2>&1`（引数省略 + リダイレクト）の `2` は fd 番号。
        # PR 番号として読むと別 PR への承認で通る経路になる。
        result = parse_gh_pr_merge("gh pr merge 2>&1", "", "/repo")
        self.assertTrue(result["is_merge"])
        self.assertIsNone(result["pr_number"])
        self.assertFalse(result["unresolvable"])

    # --- gate #15 H-1: 演算子で打ち切らず、segment ごとに走査する ----------------
    #
    # shell は simple command の **任意位置** にリダイレクトを置ける。最初の演算子で
    # 走査を打ち切ると、演算子より後ろの位置引数が見えず `pr_number` / `branch_arg`
    # が空 = 「引数省略形」と誤認され、hook 側が state.md の PR 番号を対象とみなす
    # （= 別 PR / ブランチ名指定のマージが、別 PR 向けの承認で allow される）。
    def test_redirection_before_a_positional_argument_is_not_swallowed(self):
        for command, expected in (
            ("gh pr merge </dev/null other-branch", ("branch", None)),
            ("gh pr merge 2>&1 999", ("number", "999")),
            ("gh pr merge >/tmp/x.log 999", ("number", "999")),
            ("gh pr merge 2> /tmp/x.log other-branch", ("branch", None)),
        ):
            with self.subTest(command=command):
                result = parse_gh_pr_merge(command, "", "/repo")
                self.assertTrue(result["is_merge"])
                kind, number = expected
                if kind == "number":
                    self.assertEqual(result["pr_number"], number)
                    self.assertFalse(result["unresolvable"])
                else:
                    self.assertIsNone(result["pr_number"])
                    self.assertTrue(result["unresolvable"])

    def test_redirection_before_the_subcommand_is_not_swallowed(self):
        result = parse_gh_pr_merge("gh 2>&1 pr merge 999", "", "/repo")
        self.assertTrue(result["is_merge"])
        self.assertEqual(result["pr_number"], "999")

    def test_every_chained_command_is_evaluated(self):
        # 2 本目を落とすと「1 本目の承認で 2 本目も通る」形になる。対象を 1 つの
        # result で表現できないので fail-closed（unresolvable）に倒す。
        for command in (
            "gh pr merge 7 && gh pr merge 999",
            "gh pr merge 7; gh pr merge other-branch",
            "gh pr merge 7 || gh pr merge 999",
            # 入れ子 shell 側も「見つかったら打ち切り」にしない。
            "gh pr merge 7 && bash -c 'gh pr merge 999'",
            "bash -c 'gh pr merge 7' && bash -c 'gh pr merge 999'",
        ):
            with self.subTest(command=command):
                result = parse_gh_pr_merge(command, "", "/repo")
                self.assertTrue(result["is_merge"])
                self.assertTrue(result["unresolvable"], f"{command} が fail-open")

    def test_single_merge_chained_with_other_commands_stays_resolvable(self):
        # 過検出の否定側: merge が 1 本だけなら連結されていても対象は決まる。
        for command in (
            "git fetch && gh pr merge 7",
            "gh pr merge 7 && echo done",
            "gh pr merge 7 | tee /tmp/x.log",
        ):
            with self.subTest(command=command):
                result = parse_gh_pr_merge(command, "", "/repo")
                self.assertTrue(result["is_merge"])
                self.assertEqual(result["pr_number"], "7")
                self.assertFalse(result["unresolvable"])

    # --- gate #14 M-3: shell interpreter 越しの実行を検出する --------------------
    def test_nested_shell_invocations_are_detected(self):
        for command in (
            "bash -c 'gh pr merge 7'",
            'sh -c "gh pr merge 7"',
            "eval 'gh pr merge 7'",
            "$(echo gh) pr merge 7",
            "bash -lc 'gh pr merge 7'",
        ):
            with self.subTest(command=command):
                result = parse_gh_pr_merge(command, "", "/repo")
                self.assertTrue(result["is_merge"], f"{command} が検出されない")
                self.assertEqual(result["pr_number"], "7")

    # --- gate #15 M-3: interpreter のフラグ列を取り違えて `-c` を見失わない -------
    def test_nested_shell_flag_forms_still_expose_the_script(self):
        # 旧判定 `startswith("-") and endswith("c")` は `--norc` を `-c` と誤認し、
        # 値を取る短フラグの値（`-euo pipefail` の `pipefail`）で走査を打ち切った。
        for command in (
            "bash --norc -c 'gh pr merge 7'",
            "bash --noprofile --norc -c 'gh pr merge 7'",
            "bash -euo pipefail -c 'gh pr merge 7'",
            "bash -e -o pipefail -c 'gh pr merge 7'",
            "bash -x -c 'gh pr merge 7'",
        ):
            with self.subTest(command=command):
                result = parse_gh_pr_merge(command, "", "/repo")
                self.assertTrue(result["is_merge"], f"{command} が検出されない")
                self.assertEqual(result["pr_number"], "7")

    def test_interpreter_flag_values_are_not_rescanned_as_scripts(self):
        # 過検出の否定側: 値を取るフラグの **値** は script 本体ではない。
        for command in (
            "bash --rcfile 'gh pr merge 7' -i",
            "bash -o 'gh pr merge 7'",
            "bash -x script.sh",
        ):
            with self.subTest(command=command):
                self.assertFalse(parse_gh_pr_merge(command, "", "/repo")["is_merge"])

    def test_nested_shell_detection_keeps_repo_decision_inputs(self):
        result = parse_gh_pr_merge("bash -c 'GH_REPO=org/other gh pr merge 7'", "", "/repo")
        self.assertTrue(result["is_merge"])
        self.assertTrue(result["env_repo_conflict"])

    def test_hash_inside_word_is_not_a_comment(self):
        # T-8 (completion-check Round2 H-1): bash は語中の `#`（`x#y` 等）を
        # コメント開始として扱わないが、`_tokenize` が shlex 既定の
        # `commenters='#'` を残していると `#` 以降を行末まで捨ててしまう。
        # sibling `git_command_parse.py:69` は `lexer.commenters = ""` で
        # 同一原因を既に塞いでいる（本ファイルにも同型修正が必要）。
        tokens = _tokenize("echo x#y ; cd /repoB")
        self.assertIn("/repoB", tokens)

    def test_hash_at_word_start_is_a_comment(self):
        # impl-gate T-8/T-9 F-2（承認案 (a)(2)）: bash は **語頭**（空白 / 行頭 /
        # 制御演算子の直後）の `#` だけをコメント開始として扱う。T-8 の
        # `commenters = ""` は語中を正しく扱えるようになった代わりに語頭コメントまで
        # token として残し、`gh pr merge 7 # comment` の `#` 以降を位置引数として
        # 拾って `unresolvable` を立てていた（main で allow だった 4 形の新規の不足通知）。
        self.assertEqual(_tokenize("gh pr merge 7 # squash after CI"), ["gh", "pr", "merge", "7"])
        self.assertEqual(_tokenize("gh pr merge 7 --squash # ok"), ["gh", "pr", "merge", "7", "--squash"])
        self.assertEqual(_tokenize("gh pr merge 7 #"), ["gh", "pr", "merge", "7"])
        self.assertEqual(_tokenize("gh pr merge 7\t# tab"), ["gh", "pr", "merge", "7"])
        # 制御演算子の直後も語頭（bash 実測: `echo a;#x` は `a` を出力する）。
        # 改行はコマンドの区切り（`;`）として残る。
        self.assertEqual(_tokenize("echo a;#x\ncd /repoB"), ["echo", "a", ";", ";", "cd", "/repoB"])
        # 行頭コメントは行ごと消える（次行は生きる）。最初の token の前には区切りを置かない。
        self.assertEqual(_tokenize("# gh pr merge 9\ngh pr merge 7"), ["gh", "pr", "merge", "7"])
        # 語中の `#` と特殊パラメータは残る（T-8 が塞いだ面を開け直さない）。
        self.assertEqual(_tokenize("echo x#y && gh pr merge 7"), ["echo", "x#y", "&&", "gh", "pr", "merge", "7"])
        self.assertEqual(_tokenize("echo $# ${#a}"), ["echo", "$#", "${#a}"])

    def test_quoted_hash_is_not_a_comment(self):
        # クォート内の `#` はコメントではない。素朴に「`#` で始まる token 以降を捨てる」
        # 実装だと `-t "#1 fix"` の後ろにある 2 本目の merge や `--admin` を落として
        # fail-open になる（impl-gate T-8/T-9 F-2 が指摘した反例）。
        result = parse_gh_pr_merge('gh pr merge 7 -t "#1 fix" && gh pr merge 999', "", "/repo")
        self.assertTrue(result["is_merge"])
        self.assertTrue(result["unresolvable"])
        result = parse_gh_pr_merge("gh pr merge 7 '#' --admin", "", "/repo")
        self.assertTrue(result["admin"])
        self.assertEqual(_tokenize("echo 'a # b' \"c # d\" e"), ["echo", "a # b", "c # d", "e"])

    def test_trailing_comment_does_not_make_the_merge_unresolvable(self):
        # F-2 の 4 形（hook 実起動 A/B で main ALLOW → HEAD 不足通知に反転していた形）。
        for command in (
            "gh pr merge 7 # squash after CI",
            "gh pr merge 7 --squash # ok",
            "gh pr merge 7 #",
            "cd /repo && gh pr merge 7 # done",
        ):
            with self.subTest(command=command):
                result = parse_gh_pr_merge(command, "", "/repo")
                self.assertTrue(result["is_merge"])
                self.assertEqual(result["pr_number"], "7")
                self.assertFalse(result["unresolvable"])
                self.assertIsNone(result["branch_arg"])

    def test_hash_inside_word_still_detects_the_merge(self):
        # T-8 が塞いだ main の gate 全面素通り（`is_merge=false` で無検査 ALLOW）を
        # `#` の扱いを直しても開け直さない固定。
        for command in (
            "echo x#y && gh pr merge 7",
            "echo x#y ; gh pr merge 7",
            "bash -c 'echo a#b && gh pr merge 7'",
        ):
            with self.subTest(command=command):
                result = parse_gh_pr_merge(command, "", "/repo")
                self.assertTrue(result["is_merge"])
                self.assertEqual(result["pr_number"], "7")

    def test_prose_argument_mentioning_the_command_is_not_detected(self):
        # 再帰対象を shell interpreter の引数に限定していることの否定側。
        # 本 PR 自身が `gh pr merge` を CHANGELOG / design に書くため、散文引数まで
        # 再走査すると自分の commit が誤って不足として通知される。
        for command in (
            'git commit -m "gh pr merge の block 条件を追加"',
            "bash -c 'git commit -m \"gh pr merge の block 条件を追加\"'",
            'echo "gh pr merge 7"',
        ):
            with self.subTest(command=command):
                self.assertFalse(parse_gh_pr_merge(command, "", "/repo")["is_merge"])


class EnvSplitStringDetectionTests(unittest.TestCase):
    """AC-1 / AC-3(e)(f)(g) / AC-4 / AC-5: `env` の split-string オプション
    （`-S` / `--split-string`）で包んだ本体を merge 検出の再走査対象にする。

    origin/main（64e33e0）ではこの分岐が無く、
    `env -S 'gh pr merge 7'` は `is_merge=False` で hook が不発火になって
    いた（merge gate 完全素通り）。
    """

    def test_split_string_spellings_are_all_detected_as_merge(self):
        # AC-1: 対象綴り 9 形（design.md § テスト方針表・M-4 の列挙のまま）。
        for command in (
            "env -S 'gh pr merge 7'",
            "env -S'gh pr merge 7'",
            "env -iS 'gh pr merge 7'",
            "env -iS'gh pr merge 7'",
            "env -vS 'gh pr merge 7'",
            "env - -S 'gh pr merge 7'",
            "env --split-string='gh pr merge 7'",
            "env --split-string 'gh pr merge 7'",
            "env --split-str 'gh pr merge 7'",
        ):
            with self.subTest(command=command):
                result = parse_gh_pr_merge(command, "", "/repo")
                self.assertTrue(result["is_merge"], command)
                self.assertEqual(result["pr_number"], "7", command)

    def test_bare_dash_env_form_is_unaffected(self):
        # AC-1 否定側: 単独 `-` の後ろに split-string が続かない形は従来どおり
        # `env` を起動コマンドと見なさず、次の operand（`gh`）から検出される。
        result = parse_gh_pr_merge("env - gh pr merge 7", "", "/repo")
        self.assertTrue(result["is_merge"])
        self.assertEqual(result["pr_number"], "7")

    def test_new_false_positive_class_from_non_env_short_options_is_excluded(self):
        # AC-3(e): `env` より後ろの別プログラムの `-…S…` を split-string と
        # 誤認しない。
        for command in (
            'env FOO=1 grep -S "… gh pr merge …" file',
            "env FOO=1 rsync -aS src dst",
            'env VAR=x git commit -S -m "… gh pr merge …"',
        ):
            with self.subTest(command=command):
                result = parse_gh_pr_merge(command, "", "/repo")
                self.assertFalse(result["is_merge"], command)
                self.assertFalse(result["degraded"], command)

    def test_boundary_forms_complete_without_raising(self):
        # AC-3(f): 値の無い境界形で例外を投げず解析を完走する。
        for command in (
            "env -S",
            "env -S ''",
            "env --split-string",
        ):
            with self.subTest(command=command):
                result = parse_gh_pr_merge(command, "", "/repo")
                self.assertFalse(result["is_merge"], command)
                self.assertFalse(result["degraded"], command)

    def test_bundled_order_and_optional_argument_forms_are_detected(self):
        # AC-3(g): 束ね順（`-u S` の後の `-S`）と optional-argument
        # （`--block-signal` は値を取らない token として読み飛ばす）。
        for command in (
            "env -uS -S 'gh pr merge 7'",
            "env --block-signal -S 'gh pr merge 7'",
        ):
            with self.subTest(command=command):
                result = parse_gh_pr_merge(command, "", "/repo")
                self.assertTrue(result["is_merge"], command)
                self.assertEqual(result["pr_number"], "7", command)

    def test_split_string_body_is_rescanned_within_existing_depth_budget(self):
        # AC-4: `env -S` 本体の多段形は既存の MAX_NESTED_SHELL_DEPTH を共有する。
        result = parse_gh_pr_merge(
            'env -S \'bash -c "gh pr merge 7"\'', "", "/repo",
        )
        self.assertTrue(result["is_merge"])
        self.assertEqual(result["pr_number"], "7")

    def test_split_string_occurrences_stay_within_the_existing_perf_budget(self):
        # AC-5: `env -S` を n 個並べた敵対的入力が既存の perf 予算に収まる
        # （既存 eval x20/x60 テストと同じ 1.0s 閾値を流用する）。
        for n in (20, 60):
            command = "cd /A && " + "env -S 'true' && " * n + "gh pr merge 7"
            with timing_budget() as timing:
                result = parse_gh_pr_merge(command, "", "/repo")
            elapsed = timing.cpu_seconds
            self.assertLess(timing.wall_seconds, WALL_BACKSTOP_SEC, f"wall {timing.wall_seconds:.2f}s")
            self.assertTrue(result["is_merge"], f"n={n}")
            self.assertLess(elapsed, 1.0, f"env -S x{n} の parse に {elapsed:.2f}s")

    def test_split_string_mixed_with_eval_stays_within_the_existing_perf_budget(self):
        # AC-5: `env -S` と `eval` の混在形が既存 perf 予算に収まる。
        command = "cd /A && " + "env -S 'true' && " * 20 + "eval " * 20 + "gh pr merge 7"
        with timing_budget() as timing:
            result = parse_gh_pr_merge(command, "", "/repo")
        elapsed = timing.cpu_seconds
        self.assertLess(timing.wall_seconds, WALL_BACKSTOP_SEC, f"wall {timing.wall_seconds:.2f}s")
        self.assertTrue(result["is_merge"])
        self.assertLess(elapsed, 1.0, f"env -S x20 + eval x20 の混在 parse に {elapsed:.2f}s")

    def test_cd_target_stays_none_when_split_string_carries_a_chdir_flag(self):
        # 既存 signal への波及: `-C` を含む env -S 本体でも cd_target は
        # 条件 (h) により必ず None のまま、cd_intent は True になる。
        result = parse_gh_pr_merge(
            "env -S '-C /private/tmp gh pr merge 7'", "", "/repo",
        )
        self.assertIsNone(result["cd_target"])
        self.assertTrue(result["cd_intent"])

    def test_two_identical_split_string_bodies_are_unresolvable(self):
        result = parse_gh_pr_merge(
            "env -S 'gh pr merge 7' && env -S 'gh pr merge 7'", "", "/repo",
        )
        self.assertTrue(result["unresolvable"])

    def test_unparseable_split_string_body_does_not_leak_into_output_degraded(self):
        # `-S` 本体が shlex で割れない形は出力 degraded に伝播せず、
        # cd_intent だけが True になる（`_chdir_signals` の入れ子縮退分岐の既存境界）。
        result = parse_gh_pr_merge(
            "env -S \"echo don't\"", "", "/repo",
        )
        self.assertFalse(result["degraded"])
        self.assertTrue(result["cd_intent"])


class CdTargetExtractionTests(unittest.TestCase):
    """AC-4 (a)〜(i) / AC-5: `cd_target` 抽出の受理・不採用条件。"""

    def _cd(self, command):
        return parse_gh_pr_merge(command, "", "/repo")["cd_target"]

    def _assert_within_budget(self, timing, label, cpu_budget_sec):
        """所要時間が CPU 予算と壁時計 backstop の両方に収まることを検証する。

        なぜ CPU 時間（厳）と壁時計（緩）の二本立てにするか: CPU 時間は
        計算量の退行を CPU 律速のまま検出でき（従来の閾値を据え置ける）、
        壁時計 backstop は hook timeout 予算の逸脱という別の性質を守る。
        1 本の壁時計だけで両方を担うのが並列負荷下の flaky の構造的原因
        だった（ADR-1）。
        """
        self.assertLess(
            timing.cpu_seconds,
            cpu_budget_sec,
            f"{label} に CPU {timing.cpu_seconds:.2f}s"
            f"（wall {timing.wall_seconds:.2f}s, 閾値 {cpu_budget_sec}s）",
        )
        self.assertLess(
            timing.wall_seconds,
            WALL_BACKSTOP_SEC,
            f"{label} に wall {timing.wall_seconds:.2f}s"
            f"（CPU {timing.cpu_seconds:.2f}s, backstop {WALL_BACKSTOP_SEC}s）",
        )

    def test_plain_cd_and_gh_pr_merge_is_captured(self):
        self.assertEqual(self._cd("cd /repo && gh pr merge 7"), "/repo")

    def test_semicolon_separator_is_captured(self):
        # AC-1: `;` 区切りでも `&&` と同じ結果になる。
        self.assertEqual(self._cd("cd /repo; gh pr merge 7"), "/repo")

    def test_cd_followed_by_other_commands_is_still_captured(self):
        # AC-5: `cd` の後に `gh pr merge` 以外が挟まる正当形。
        self.assertEqual(self._cd("cd /repo && git fetch && gh pr merge 7"), "/repo")

    def test_relative_path_is_rejected(self):
        # AC-4(c)
        self.assertIsNone(self._cd("cd repo && gh pr merge 7"))

    def test_tilde_path_is_rejected(self):
        # AC-4(c): `~/repo` は展開前の raw command では絶対パスにならない。
        self.assertIsNone(self._cd("cd ~/repo && gh pr merge 7"))

    def test_dotdot_path_component_is_rejected(self):
        # AC-4(d)
        self.assertIsNone(self._cd("cd /A/../B && gh pr merge 7"))

    def test_glob_characters_are_rejected(self):
        # AC-4(e)
        self.assertIsNone(self._cd("cd /A/* && gh pr merge 7"))
        self.assertIsNone(self._cd("cd /A/? && gh pr merge 7"))

    def test_dash_dash_option_is_rejected(self):
        # AC-4(c): `cd --` の次 token は絶対パスではなく `--` 自身。
        self.assertIsNone(self._cd("cd -- /A && gh pr merge 7"))

    def test_dash_capital_p_option_is_rejected(self):
        self.assertIsNone(self._cd("cd -P /A && gh pr merge 7"))

    def test_multiple_cwd_change_tokens_at_top_level_are_rejected(self):
        # AC-4(a)
        self.assertIsNone(self._cd("cd /A && pushd /B && gh pr merge 7"))

    def test_hash_inside_word_does_not_hide_a_second_cd_token(self):
        # T-8 (completion-check Round2 H-1 / AC-18): `x#y` の `#` が既定の
        # shlex commenters により行末までコメント扱いされると、実際には
        # `cd /repoA && echo x#y ; cd /repoB` に `cd` が 2 回あるのに 1 回
        # しか見えず、`cd_target` が `/repoA` へ誤って単独確定する。
        # 実際に `gh` が走るのは `/repoB` なので、AC-18 の
        # 「root と実行先が一致しない形は pr-target-unresolvable」が
        # 発火しなくなる（不足として通知されるべき形が通過扱いになる）。
        command = "cd /repoA && echo x#y ; cd /repoB\ngh pr merge 7"
        self.assertIsNone(self._cd(command))

    # --- (a) 拡張（impl-gate T-8/T-9 F-1、人間承認 2026-09-08T08:32:20+09:00）:
    # 走査範囲に chdir intent（cwd 変更 token）があるのに AC-4 で不採用にした形は
    # `cd_target=None` のまま `cd_intent=True` を返し、hook が「解決できない実行先」
    # として `pr-target-unresolvable` へ倒す。従来は None = 「実行先の signal が無い」
    # と扱われ、プロセス cwd 由来 root で判定されて allow に抜けていた。
    def test_chdir_intent_is_reported_when_cd_target_is_rejected(self):
        for command in (
            "cd /A && cd /B && gh pr merge 7",
            "cd /A && echo x#y ; cd /B\ngh pr merge 7",
            "builtin cd /B && gh pr merge 7",
            "command cd /B && gh pr merge 7",
            "cd -- /B && gh pr merge 7",
            "cd -P /B && gh pr merge 7",
            "cd /A && CD=cd && $CD /B && gh pr merge 7",
            "cd /A && env --chdir=/B gh pr merge 7",
            "env --chdir=/B gh pr merge 7",
            "env -C /B gh pr merge 7",
            "pushd /B && gh pr merge 7",
            "cd /A && pushd /B && gh pr merge 7",
            "cd /A && bash -c 'cd /B && gh pr merge 7'",
            "eval 'cd /B && gh pr merge 7'",
            "bash -c 'cd /B && gh pr merge 7'",
            "(cd /B && gh pr merge 7)",
            "cd ./B && gh pr merge 7",
            "cd /A/../B && gh pr merge 7",
            "cd ~/repo && gh pr merge 7",
            "cd /A && gh pr merge 7 --title \"$T\"",
        ):
            with self.subTest(command=command):
                result = parse_gh_pr_merge(command, "", "/repo")
                self.assertIsNone(result["cd_target"])
                self.assertTrue(result["cd_intent"])

    def test_chdir_intent_survives_env_options_that_take_a_separate_argument(self):
        # `env` の走査が `-u NAME` の `NAME`（`-` で始まらず
        # `=` を含まない）を「起動するコマンド名」と誤認して打ち切り、その後ろの
        # `-C` / `--chdir` を見落としていた。`env` があれば AC-4 (h) で cd_target は
        # 必ず None なので intent が落ちると (a‴) の不足通知が発火せず、root ≠ 実行先の
        # merge が allow される。BSD env（macOS）/ GNU env とも `-u` と `-C` を実装。
        for command in (
            "env -u X -C /B gh pr merge 7",
            "env -u X --chdir=/B gh pr merge 7",
            "/usr/bin/env -u X -C /B gh pr merge 7",
        ):
            with self.subTest(command=command):
                result = parse_gh_pr_merge(command, "", "/repo")
                self.assertIsNone(result["cd_target"])
                self.assertTrue(result["cd_intent"])

    def test_chdir_intent_survives_bundled_env_short_options(self):
        # `env` の短オプションは束ねて書ける。macOS 実測で
        # `env -iC <DIR> pwd` / `env -iC<DIR> pwd` / `env -vC <DIR> pwd` は
        # いずれも `<DIR>` へ chdir する。`-C` の接頭一致だけで判定すると束ね形
        # （`-iC` / `-vC`）と値密着形（`-iC<DIR>`）を chdir と認識できず、`env` が
        # あれば AC-4 (h) で cd_target は必ず None なので intent が落ち、
        # root ≠ 実行先の merge が allow される。非束ね形 `env -i -C <DIR>` が
        # 不足として通知される一方で束ね形が抜けるのは同一 guard 内の非対称。
        for command in (
            "env -iC /B gh pr merge 7",
            "env -iC/B gh pr merge 7",
            "env -vC /B gh pr merge 7",
        ):
            with self.subTest(command=command):
                result = parse_gh_pr_merge(command, "", "/repo")
                self.assertIsNone(result["cd_target"])
                self.assertTrue(result["cd_intent"])

    def test_chdir_intent_survives_abbreviated_env_long_options(self):
        # GNU coreutils env は getopt_long なので、長オプションの一意な省略形を
        # 受理する（`--chdir` は `--ch` まで縮めても一意）。`--chdir` の接頭一致
        # だけで判定すると Linux 上の `env --ch=/B` / `env --c /B` を chdir と
        # 認識できず、束ね短オプションと同じ形で intent が落ちる。macOS の BSD
        # env は長オプションを持たないので本機では実行不能形だが、判定は
        # 実行環境に依存させない（不足の通知側にのみ倒れる）。
        for command in (
            "env --ch=/B gh pr merge 7",
            "env --c /B gh pr merge 7",
            "env --chd /B gh pr merge 7",
        ):
            with self.subTest(command=command):
                result = parse_gh_pr_merge(command, "", "/repo")
                self.assertIsNone(result["cd_target"])
                self.assertTrue(result["cd_intent"])

    def test_tokenizer_degradation_is_reported_as_its_own_signal(self):
        # shlex は閉じないクォートで ValueError を投げ、`text.split()` へ縮退する。
        # 縮退した token 列は演算子と密着した token を割らないので、`;gh` は token
        # `gh` にならず `is_merge` が落ち、`;cd` も chdir 語彙として数えられない。
        # どちらの消費者も数え落とすので、縮退そのものを signal として返し、hook が
        # 解析未完走と同じ family へ倒せるようにする。
        for command in (
            "x=$'\\'' ;gh pr merge 7",
            "x=$'\\'' ;cd /B ;gh pr merge 7",
        ):
            with self.subTest(command=command):
                result = parse_gh_pr_merge(command, "", "/repo")
                self.assertTrue(result["degraded"])

    def test_nested_degradation_does_not_adopt_a_wrong_cd_target(self):
        # 入れ子本体だけが縮退すると、その中の `cd` が語彙として数えられない。
        # 数え落としたまま先頭の `cd` を「唯一の cwd 変更」として採用すると、実
        # シェルが別の場所へ chdir しているのに実行先の照合が「一致」で通り、
        # 先頭側の承認証跡で別 repo の merge が評価される。
        command = "cd /A && bash -c \";cd /B; gh pr merge 7 --x 'q\""
        result = parse_gh_pr_merge(command, "", "/repo")
        self.assertTrue(result["is_merge"])
        self.assertIsNone(result["cd_target"])
        self.assertTrue(result["cd_intent"])

    def test_valid_bash_with_nested_apostrophe_does_not_degrade(self):
        # `bash -c "echo don't"` は **bash として valid**（アポストロフィが二重引用符
        # の内側）。入れ子本体まで縮退判定に含めると、この形が不足として通知されて日常操作
        # が妨げられる。判定はトップレベルの tokenize だけを見る。
        for command in (
            'bash -c "echo don\'t"',
            'bash -lc "echo it\'s fine; git status"',
        ):
            with self.subTest(command=command):
                self.assertFalse(parse_gh_pr_merge(command, "", "/repo")["degraded"])

    def test_heredoc_forms_do_not_raise_the_degradation_signal(self):
        # heredoc があるとどちらを基準にしても不足の通知側の誤検知が出る（切り落とし
        # 後を基準にすると引用符の内側で introducer に一致する形、元コマンドを基準に
        # すると実行されない本文のアポストロフィ）。誤検知を出すくらいなら signal を
        # 立てない（この形の扱いは origin/main と同じ）。
        for command in (
            "bash -lc 'git commit -F - <<MSG\nfix: gh pr merge を修正\nMSG'",
            "git commit -F - <<'MSG'\nDon't merge yet\nMSG",
        ):
            with self.subTest(command=command):
                result = parse_gh_pr_merge(command, "", "/repo")
                self.assertFalse(result["degraded"])

    def test_ordinary_apostrophe_does_not_degrade_the_tokenizer(self):
        # 過剰な通知を避ける側の固定。通常のクォート内アポストロフィは縮退しない。
        for command in ('gh pr merge 7 -t "it\'s done"', "gh pr merge 7"):
            with self.subTest(command=command):
                result = parse_gh_pr_merge(command, "", "/repo")
                self.assertFalse(result["degraded"])
                self.assertTrue(result["is_merge"])

    def test_chdir_intent_is_false_without_any_chdir_token(self):
        # 誤爆しない側: chdir 語彙が無ければ intent は立たない（語頭コメント内 /
        # クォートされた散文の一部 / `git -C` / chdir しない `env` は対象外）。
        for command in (
            "gh pr merge 7",
            "gh pr merge 7 # cd later",
            "git fetch && gh pr merge 7",
            'gh pr merge 7 -t "cd into the dir"',
            "git -C /repo fetch && gh pr merge 7",
            "env GH_TOKEN=x gh pr merge 7",
            "env -u X gh pr merge 7",
            "env -i gh pr merge 7",
        ):
            with self.subTest(command=command):
                result = parse_gh_pr_merge(command, "", "/repo")
                self.assertFalse(result["cd_intent"])
                self.assertIsNone(result["cd_target"])

    def test_chdir_intent_accompanies_an_adopted_cd_target(self):
        # AC-4 / AC-5 の正当形は intent あり + cd_target 採用（hook 側は AC-18 の
        # toplevel 比較だけを行い、intent 単独では通知しない）。
        for command in (
            "cd /repo && gh pr merge 7",
            "cd /repo && git fetch && gh pr merge 7",
            "cd /repo; gh pr merge 7",
            "cd /repo && gh pr merge 7 # done",
        ):
            with self.subTest(command=command):
                result = parse_gh_pr_merge(command, "", "/repo")
                self.assertEqual(result["cd_target"], "/repo")
                self.assertTrue(result["cd_intent"])

    def test_cd_not_at_top_level_leading_position_is_rejected(self):
        # AC-4(b): `(` が先頭 token になるため `cd` はトップレベル先頭ではない。
        self.assertIsNone(self._cd("(cd /A && gh pr merge 7)"))

    def test_cd_inside_nested_subshell_combined_with_top_level_cd_is_rejected(self):
        # AC-4(a): トップレベルの `cd /A` と subshell 内の `cd /B` で計 2 つ。
        self.assertIsNone(self._cd("cd /A && (cd /B && gh pr merge 7)"))

    def test_cd_inside_nested_bash_c_is_rejected(self):
        # AC-4(a)(f): 入れ子 `bash -c` 本体の chdir token が計数に加わる。
        self.assertIsNone(self._cd("cd /A && bash -c 'cd /B && gh pr merge 7'"))

    def test_cd_inside_eval_is_rejected(self):
        # AC-4(b)(f)
        self.assertIsNone(self._cd("eval 'cd /B && gh pr merge 7'"))

    def test_cd_inside_doubly_nested_bash_c_is_rejected(self):
        # IG-1: `_extract_cd_target` の入れ子走査は `_scan_tokens`
        # （MAX_NESTED_SHELL_DEPTH=3 まで再帰）と同一の走査範囲でなければ
        # ならない（AC-4 の受理条件）。1 段しか見ないと depth 2 の
        # `cd /B` を見落とし、トップレベルの `cd /A` を誤って単独採用する。
        self.assertIsNone(
            self._cd("cd /A && bash -c 'bash -c \"cd /B && gh pr merge 7\"'")
        )

    def test_cd_at_max_nested_depth_is_still_counted(self):
        # IG-5: `MAX_NESTED_SHELL_DEPTH=3` の境界。depth 3 は走査範囲内なので
        # `_scan_tokens` が `gh pr merge` を見つけるのと対称に `cd /B` も計数する。
        depth3 = "cd /A && bash -c 'bash -c \"bash -c \\\"cd /B && gh pr merge 7\\\"\"'"
        result = parse_gh_pr_merge(depth3, "", "/repo")
        self.assertTrue(result["is_merge"])
        self.assertIsNone(result["cd_target"])

    def test_cd_beyond_max_nested_depth_is_outside_both_scans(self):
        # IG-5: depth 4 は `_scan_tokens` も走査外（is_merge=False）なので、
        # cd_target 側だけが深く見る／浅く見る非対称を作らない。
        depth4 = (
            "cd /A && bash -c 'bash -c \"bash -c \\\"bash -c "
            "\\\\\\\"cd /B && gh pr merge 7\\\\\\\"\\\"\"'"
        )
        result = parse_gh_pr_merge(depth4, "", "/repo")
        self.assertFalse(result["is_merge"])

    def test_repeated_eval_bodies_do_not_blow_up_parse_time(self):
        """IG-4: `eval` の本体は「残り token 全部」なので、入れ子層の展開で本体を
        1 本の frontier へ平坦化すると層をまたいで乗算的に膨張する。hook は
        `hooks/hooks.json` で timeout 10 秒なので、parse が遅いと通知を返す前に
        kill され merge gate が不発になる（fail-open）。`_scan_tokens` と同じく
        本体ごとに再帰すれば n=20 でも閾値よりずっと短く返る。
        """
        command = "cd /A && " + "eval " * 20 + "gh pr merge 7"
        with timing_budget() as timing:
            result = parse_gh_pr_merge(command, "", "/repo")
        self.assertTrue(result["is_merge"])
        self.assertEqual(result["cd_target"], "/A")
        self._assert_within_budget(timing, "eval x20 の parse", 1.0)

    def test_pushd_alone_is_rejected(self):
        # AC-4(i): 唯一の cwd 変更 token が `cd` 以外。
        self.assertIsNone(self._cd("pushd /A && gh pr merge 7"))

    def test_dollar_variable_indirection_is_rejected(self):
        # Round 3 human recheck B-1: 走査範囲全体に `$` があれば不採用。
        self.assertIsNone(self._cd("cd /A && CD=cd && $CD /B && gh pr merge 7"))

    def test_ifs_expansion_forms_are_rejected(self):
        # Round 3 human recheck B-1: `cd$IFS` / `cd${IFS}` 形。
        self.assertIsNone(self._cd("cd /A && bash -c 'cd$IFS/B; gh pr merge 7'"))
        self.assertIsNone(self._cd("cd /A && bash -c 'cd${IFS}/B; gh pr merge 7'"))

    def test_env_chdir_form_is_rejected(self):
        # Round 3 human recheck B-1: `env` の basename 一致で走査範囲全体を見る。
        self.assertIsNone(self._cd("cd /A && env --chdir=/B gh pr merge 7"))

    def test_backtick_indirection_is_rejected(self):
        self.assertIsNone(self._cd("cd /A && echo `x` && gh pr merge 7"))

    def test_no_cd_present_returns_none(self):
        self.assertIsNone(self._cd("gh pr merge 7"))

    def test_nested_layer_collection_keeps_each_eval_body_once(self):
        """IG-6: `eval` の本体は「残り token 全部」なので、`eval×n` では各層の本体が
        互いの suffix になる。本体ごと DFS で全層を保持すると本体数が n^3 オーダー
        （n=8 で 92 本。n を大きくするとメモリ使用量も急に増える）に膨らむが、同一本体文字列は
        最浅の層で 1 回展開すれば走査する本体の集合は変わらない（条件 (f)(g)(h) は
        本体集合に対する存在検査）。保持する本体は n 本で済まなければならない。
        """
        tokens = _tokenize("cd /A && " + "eval " * 8 + "gh pr merge 7")
        bodies, _, _ = _collect_nested_shell_layers(tokens)
        self.assertEqual(len(bodies), 8, f"bodies={len(bodies)}")

    def test_cd_target_extraction_does_not_repeat_the_nested_scan(self):
        """IG-6: `_extract_cd_target` が `_scan_tokens` と同型の走査を独立にもう 1 回
        行うと、`parse_gh_pr_merge` の所要が main より大きく延び、hook timeout
        （`hooks/hooks.json` の 10 秒）を超えて通知を返せない入力域が広がる
        （fail-open）。`_scan_tokens` を含まない `_extract_cd_target` 単体は
        n=60 でも 0.5 秒未満で返ること（重複展開ありではこれを超える）。
        """
        tokens = _tokenize("cd /A && " + "eval " * 60 + "gh pr merge 7")
        with timing_budget() as timing:
            cd_target = _extract_cd_target(tokens)
        self.assertEqual(cd_target, "/A")
        self._assert_within_budget(timing, "eval x60 の cd_target 抽出", 0.5)
