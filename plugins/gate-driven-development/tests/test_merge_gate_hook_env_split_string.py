"""`env` の split-string オプション本体を、実 env と同じく env の argv に
差し込んだ後の argv として再走査する経路の契約テスト
（`lib/gh_command_parse.py`）。

既存の `tests/test_merge_gate_hook_command_parse.py` は関数数の上限に
達しているため、本ファイルへ新規テストを追加する
（`tests/test_merge_gate_hook_command_parse.py` の docstring・
`_merge_gate_support.py` と同じ import 方法に合わせる）。
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

from _timing_budget import hook_timeout_seconds, timing_budget
from _merge_gate_support import (
    PLUGIN_ROOT,
    _init_repo,
    _run_hook,
    _write_marker_only,
)

sys.path.insert(0, str(PLUGIN_ROOT / "hooks" / "scripts"))

from lib.gh_command_parse import (  # noqa: E402
    _extract_cd_target,
    _tokenize,
    parse_gh_pr_merge,
)


# 解析時間は CPU 時間で測り、壁時計は hook の timeout の半分を backstop にする（テスト時間の ADR の二本立て）。
WALL_BACKSTOP_SEC = hook_timeout_seconds("run-merge-gate-hook.sh") / 2


class EnvSplitStringSpliceDetectionTests(unittest.TestCase):
    """AC-1: 差し込み後の argv を再走査することで、素通りしていた 3 形
    （impl-gate Task 1 Round 1 の IG-1）と、後続引数由来の値（repo_flag /
    pr_number / admin）が既存経路で解決できることを固定する。
    """

    def test_previously_undetected_forms_are_now_detected(self):
        for command in (
            "env -S 'gh pr' merge 7",
            'env -S \'-S "gh pr merge 7"\'',
            'env -S \'-i -S "gh pr merge 7"\'',
        ):
            with self.subTest(command=command):
                result = parse_gh_pr_merge(command, "", "/repo")
                self.assertTrue(result["is_merge"], command)
                self.assertEqual(result["pr_number"], "7", command)
                self.assertFalse(result["degraded"], command)

    def test_trailing_repo_flag_after_the_split_string_value_is_resolved(self):
        result = parse_gh_pr_merge(
            "env -S 'gh pr merge 7' -R other/repo", "", "/repo",
        )
        self.assertEqual(result["repo_flag"], "other/repo")

    def test_trailing_pr_number_after_the_split_string_value_is_resolved(self):
        result = parse_gh_pr_merge("env -S 'gh pr merge' 7", "", "/repo")
        self.assertTrue(result["is_merge"])
        self.assertEqual(result["pr_number"], "7")

    def test_trailing_admin_flag_after_the_split_string_value_is_detected(self):
        result = parse_gh_pr_merge(
            "env -S 'gh pr merge 7' --admin", "", "/repo",
        )
        self.assertTrue(result["admin"])


class EnvSplitStringNoDoubleCountingTests(unittest.TestCase):
    """AC-3(a): 既存経路が既に数えている `gh pr merge` を env 分岐が重複して
    数えないこと（二重計上の打ち切り。ADR-2）。origin/main と同一の判定を保つ。
    """

    def test_visible_merge_forms_stay_resolvable(self):
        for command in (
            "env -S '' gh pr merge 7",
            "env -S 'VAR=x' gh pr merge 7",
            "env -S gh pr merge 7",
        ):
            with self.subTest(command=command):
                result = parse_gh_pr_merge(command, "", "/repo")
                self.assertTrue(result["is_merge"], command)
                self.assertEqual(result["pr_number"], "7", command)
                self.assertFalse(result["unresolvable"], command)


class EnvSplitStringQuotePreservationTests(unittest.TestCase):
    """AC-3(b)(e): 後続引数を 1 token ずつ quote して連結するので、散文引数の
    クォート境界が壊れて誤検出を生まないこと。
    """

    def test_prose_argument_after_the_split_string_value_keeps_its_quoting(self):
        result = parse_gh_pr_merge(
            "env -S 'x' git commit -m 'a gh pr merge b'", "", "/repo",
        )
        self.assertFalse(result["is_merge"])
        self.assertFalse(result["degraded"])


class EnvSplitStringNestedDepthTests(unittest.TestCase):
    """AC-4: 本体中の `-S` が既存の深さ予算（`MAX_NESTED_SHELL_DEPTH`=3）の
    範囲で解けること。
    """

    def test_three_levels_of_nested_split_string_are_detected(self):
        result = parse_gh_pr_merge(
            'env -S \'-S "-S \\"gh pr merge 7\\""\'', "", "/repo",
        )
        self.assertTrue(result["is_merge"])


class EnvSplitStringChdirAndRepoConflictSignalTests(unittest.TestCase):
    """本体中の env option・代入が既存 signal（cd_intent / env_repo_conflict）
    に波及すること。打ち切りで二重計上を避けても本体の option・代入は
    argv に残る（security レビュー R3 の F-1 指摘への処置。basename が `gh` の
    最後の token の手前まで残す規則。人間承認 2026-09-11T07:36:36+09:00）。

    この節の一部の入力は、本体の生文字列全体の basename がたまたま `gh`
    になる（末尾が `/…/gh` のパス）ため、`720f60f` 時点でも既に正しい値を
    返す（`_scan_simple_command` のトップレベル走査が本体 token 自身を
    `gh` として拾う偶然の一致）。ここでは新しい差し込み実装がその一致を
    壊さないことの回帰ガードとして固定する。
    """

    def test_chdir_flag_inside_the_body_sets_intent_without_a_target(self):
        result = parse_gh_pr_merge(
            "env -S '-u X -C /x' gh pr merge 7", "", "/repo",
        )
        self.assertIsNone(result["cd_target"])
        self.assertTrue(result["cd_intent"])

    def test_body_ending_in_gh_keeps_its_chdir_option(self):
        result = parse_gh_pr_merge(
            "env -S '-i -C /other/repo /opt/homebrew/bin/gh' pr merge 7",
            "", "/repo",
        )
        self.assertTrue(result["cd_intent"])
        self.assertTrue(result["is_merge"])
        self.assertEqual(result["pr_number"], "7")
        self.assertFalse(result["unresolvable"])

    def test_body_ending_in_gh_keeps_its_repo_assignment(self):
        result = parse_gh_pr_merge(
            "env -S '-i GH_REPO=o/r /usr/bin/gh' pr merge 7", "", "/repo",
        )
        self.assertTrue(result["env_repo_conflict"])
        self.assertTrue(result["is_merge"])
        self.assertEqual(result["pr_number"], "7")
        self.assertFalse(result["unresolvable"])

    def test_repo_assignment_before_an_earlier_gh_value_keeps_the_last_gh_rule(self):
        # `GH_REPO=o/gh` の値自身が basename `gh` を持つ形。「最後の」gh の
        # 手前まで残す規則でなければ代入が落ちる（R3b の 1 語変更の理由）。
        result = parse_gh_pr_merge(
            "env -S '-i GH_REPO=o/gh /usr/bin/gh' pr merge 7", "", "/repo",
        )
        self.assertTrue(result["env_repo_conflict"])

    def test_chdir_flag_before_an_earlier_gh_value_keeps_the_last_gh_rule(self):
        result = parse_gh_pr_merge(
            "env -S '-u gh -C /other/repo /usr/bin/gh' pr merge 7", "", "/repo",
        )
        self.assertTrue(result["cd_intent"])
        self.assertTrue(result["is_merge"])
        self.assertEqual(result["pr_number"], "7")
        self.assertFalse(result["unresolvable"])


class EnvSplitStringSameTokenFormsTests(unittest.TestCase):
    """planning R3 advisory A-1: 本体が option token 自身に密着した形
    （`-S<str>` / `--split-string=<str>`）でも、後続引数の始点
    （`body_pos + 1`）がずれないこと。
    """

    def test_densely_attached_forms_with_trailing_arguments_are_detected(self):
        for command in (
            "env -S'gh pr' merge 7",
            "env --split-string='gh pr merge' 7",
        ):
            with self.subTest(command=command):
                result = parse_gh_pr_merge(command, "", "/repo")
                self.assertTrue(result["is_merge"], command)
                self.assertEqual(result["pr_number"], "7", command)


class EnvSplitStringDisclosedLimitsTests(unittest.TestCase):
    """planning R3 advisory A-2: 開示した限界（4 個目以降の `-S` は検出でき
    ない / 後続引数に入れ子の起点があると過剰な通知になる）をテストで
    固定する。開示と挙動が食い違ったら本テストが落ちる。
    """

    def test_a_fourth_split_string_layer_is_not_detected(self):
        for command in (
            "env -S-S-S-Sgh pr merge 7",
            "env -S -i -S -i -S -i -S 'gh pr merge 7'",
        ):
            with self.subTest(command=command):
                result = parse_gh_pr_merge(command, "", "/repo")
                self.assertFalse(result["is_merge"], command)
                self.assertFalse(result["degraded"], command)

    def test_three_split_string_layers_stay_within_budget(self):
        result = parse_gh_pr_merge("env -S-S-Sgh pr merge 7", "", "/repo")
        self.assertTrue(result["is_merge"])

    def test_nested_shell_starters_in_trailing_arguments_double_count(self):
        # origin/main では前 2 形が is_merge=True / unresolvable=False
        # （正しく解決していた）。今回の差し込み方式では、env 分岐が
        # 同じ `bash -c` / `eval` 本体をもう一度露出させるため、既存の
        # bash-c / eval 分岐と合わせて 2 回数え、unresolvable=True になる
        # （人間承認 2026-09-10T23:58:31+09:00 で開示して受容。ADR-2）。
        # 3 形目の連鎖形は origin/main では is_merge=False だった
        # （fail-open）ものを新しく検出する。
        for command in (
            "env -S 'VAR=x' bash -c 'gh pr merge 7'",
            "env -S '' eval 'gh pr merge 7'",
            "env -S 'VAR=1' env -S 'gh pr merge 7'",
        ):
            with self.subTest(command=command):
                result = parse_gh_pr_merge(command, "", "/repo")
                self.assertTrue(result["is_merge"], command)
                self.assertTrue(result["unresolvable"], command)


class EnvSplitStringPerfBudgetTests(unittest.TestCase):
    """AC-5: 1 つの simple command に `env -S 'true'` を区切り演算子なしで
    並べた敵対的入力が既存の perf 予算に収まること（既存 `eval` × 20 / × 60
    と同じ閾値を流用する）。
    """

    def test_repeated_split_string_within_one_simple_command_stays_in_budget(self):
        command = "cd /A && " + "env -S 'true' " * 20 + "gh pr merge 7"
        with timing_budget() as timing:
            result = parse_gh_pr_merge(command, "", "/repo")
        elapsed = timing.cpu_seconds
        self.assertLess(timing.wall_seconds, WALL_BACKSTOP_SEC, f"wall {timing.wall_seconds:.2f}s")
        self.assertTrue(result["is_merge"])
        self.assertLess(
            elapsed, 1.0,
            f"env -S x20（区切りなし）の parse に {elapsed:.2f}s",
        )

    def test_repeated_split_string_cd_target_extraction_stays_in_budget(self):
        command = "cd /A && " + "env -S 'true' " * 60 + "gh pr merge 7"
        tokens = _tokenize(command)
        with timing_budget() as timing:
            _extract_cd_target(tokens)
        elapsed = timing.cpu_seconds
        self.assertLess(timing.wall_seconds, WALL_BACKSTOP_SEC, f"wall {timing.wall_seconds:.2f}s")
        self.assertLess(
            elapsed, 0.5,
            f"env -S x60（区切りなし）の cd_target 抽出に {elapsed:.2f}s",
        )


class EnvSplitStringSimpleCommandBoundaryTests(unittest.TestCase):
    """差し込み後の argv を組み立てるときの gh 探索は、同じ simple command の
    中だけを読む（design.md § `_nested_shell_commands` への接続 の手順 3・4）。
    制御演算子の向こうの `pr merge` を、後続引数にある gh の sub-command と
    読み違えない。
    """

    def test_gh_search_does_not_cross_a_control_operator(self):
        # 実シェルは `env gh pr merge gh -R x` を実行し、repo x の branch gh の
        # PR を merge する（`&& pr merge` は別のコマンド）。探索が `&&` を越えると、
        # 後続引数の gh を `gh … pr merge` と誤認して argv を打ち切り、
        # repo 指定を読み落として「引数省略形」になる（対象 repo の読み違い）。
        # 期待値は `&&` の無い形、および env を使わないトップ層の読みと同じ。
        result = parse_gh_pr_merge(
            "env -S 'gh pr merge' gh -R x && pr merge", "", "/repo",
        )
        self.assertTrue(result["is_merge"])
        self.assertEqual(result["repo_flag"], "x")
        self.assertEqual(result["branch_arg"], "gh")
        self.assertTrue(result["unresolvable"])


class EnvSplitStringUnverifiedCutoffTests(unittest.TestCase):
    """impl-gate Task 1 Round 2 IG2-1 の処置: 手順 4 の打ち切りは、既存経路
    （トップ層）が見つけた gh が実際に対応する token かどうかを検証しない
    まま信用していた。`env -S 'gh -R' o/gh pr merge 7` は `-R` の値
    `o/gh`（basename が `gh`）をトップ層が gh 本体と誤読し、打ち切りが
    その誤読をそのまま採用するため、実 env が o/gh の #7 を merge するのに
    現 repo の #7 として証跡判定されていた（origin/main と同値。本 PR に
    よる退行ではない）。

    打ち切る前に、差し込み後の argv を同じ gh 探索でもう一度読み、見つかる
    gh がトップ層の読みと同じ token に対応するときだけ打ち切るよう限定する
    （対応しなければ二重に数えて `unresolvable=True` に倒す。fail-closed）。
    """

    def test_repo_flag_value_shaped_like_gh_becomes_unresolvable(self):
        for command in (
            "env -S 'gh -R' o/gh pr merge 7",
            "env -S 'gh --repo' o/gh pr merge 7",
            "env -S '/usr/bin/gh -R' o/gh pr merge 7",
            "env -S'gh -R' o/gh pr merge 7",
            'bash -c "env -S \'gh -R\' o/gh pr merge 7"',
            "env -S '/usr/bin/gh -R o/gh' pr merge 7",
        ):
            with self.subTest(command=command):
                result = parse_gh_pr_merge(command, "", "/repo")
                self.assertTrue(result["is_merge"], command)
                self.assertEqual(result["repo_flag"], "o/gh", command)
                self.assertIsNone(result["pr_number"], command)
                self.assertTrue(result["unresolvable"], command)

    def test_repo_flag_in_both_body_and_trailing_arguments_becomes_unresolvable(self):
        # 本体と後続引数の両方に `-R` を書く不自然な形。origin/main は偶然
        # 正しく `o/r` を解決していたが（退行）、対応確認により打ち切らず
        # 二重に数える（開示した過剰な通知。人間承認 2026-09-11T09:33:23+09:00）。
        result = parse_gh_pr_merge(
            "env -S 'gh -R o/gh' -R o/r pr merge 7", "", "/repo",
        )
        self.assertTrue(result["is_merge"])
        self.assertTrue(result["unresolvable"])

    def test_repo_flag_value_not_shaped_like_gh_still_resolves(self):
        # 対照形: `-R` の値の basename が `gh` でなければ、従来どおり
        # 打ち切って解決する（origin/main と同値。退行なし）。
        result = parse_gh_pr_merge(
            "env -S 'gh -R' o/r pr merge 7", "", "/repo",
        )
        self.assertEqual(result["repo_flag"], "o/r")
        self.assertEqual(result["pr_number"], "7")
        self.assertFalse(result["unresolvable"])


class EnvSplitStringWordStartCommentCutoffTests(unittest.TestCase):
    """本体の末尾に語頭 `#` で始まる語を置く形: bash 準拠のコメント除去で
    `#` 以降が本体 token 列から丸ごと落ち、見かけ上「最後の gh」が繰り
    上がる。実 env も `#` で始まる語から後ろを捨てる（本ホストの `man env`）ので、
    実行されるのは繰り上がった gh とその後ろの flag（`-R` 等）なのに、トップ層は
    生文字列全体の basename（末尾の `#/gh`）を gh と読む。この食い違いを対応ありと
    誤認して打ち切ると、後ろの flag が argv 差し込みから消え、別 repo の PR を
    現 repo の PR と読み違える（人間承認 2026-09-11T13:36:09+09:00）。
    """

    def test_word_start_comment_after_the_last_gh_prevents_the_cutoff(self):
        for command in (
            "env -S '/usr/bin/gh -R o/x #/gh' pr merge 7",
            "env -S'/usr/bin/gh -R o/x #/gh' pr merge 7",
            "env --split-string='/usr/bin/gh -R o/x #/gh' pr merge 7",
            "env -S '/usr/bin/gh --repo=o/x #/gh' pr merge 7",
        ):
            with self.subTest(command=command):
                result = parse_gh_pr_merge(command, "", "/repo")
                self.assertEqual(result["repo_flag"], "o/x", command)
                self.assertTrue(result["unresolvable"], command)


class EnvSplitStringBackslashCEscapeCutoffTests(unittest.TestCase):
    """`#` の代わりに `\\c` を使う形: `\\c` は実 env にとって文字列の
    残りを無視する打ち切り記号だが、tokenize 側はバックスラッシュ
    エスケープとして `c` を普通の文字に戻すため、最後の gh は token 列の
    末尾に残ってしまう。本体を持つ token 自身に `\\c` が含まれているかを
    別条件で見ないと対応ありの誤判定が残る（人間承認 2026-09-11T14:14:53+09:00）。
    """

    def test_backslash_c_after_the_last_gh_prevents_the_cutoff(self):
        result = parse_gh_pr_merge(
            "env -S '/usr/bin/gh -R o/x \\c/gh' pr merge 7", "", "/repo",
        )
        self.assertIsNone(result["repo_flag"])
        self.assertTrue(result["unresolvable"])


class EnvSplitStringExpansionBudgetTests(unittest.TestCase):
    """1 層で展開する env split-string の個数に上限 8 を設け、超えたら
    解析せず不足として通知する（人間承認 2026-09-11T14:14:53+09:00。AC-5 注記）。
    """

    def test_exactly_the_budget_still_resolves(self):
        command = "env -S 'true' " * 8 + "gh pr merge 7"
        result = parse_gh_pr_merge(command, "", "/repo")
        self.assertEqual(result["pr_number"], "7")
        self.assertFalse(result["unresolvable"])

    def test_one_past_the_budget_blocks_without_parsing(self):
        command = "env -S 'true' " * 9 + "gh pr merge 7"
        result = parse_gh_pr_merge(command, "", "/repo")
        self.assertTrue(result["is_merge"])
        self.assertIsNone(result["pr_number"])
        self.assertTrue(result["unresolvable"])

    def test_cd_target_extraction_returns_none_past_the_budget(self):
        command = "cd /A && " + "env -S 'true' " * 9 + "gh pr merge 7"
        tokens = _tokenize(command)
        self.assertIsNone(_extract_cd_target(tokens))

    def test_a_hundred_split_strings_block_in_under_one_second(self):
        command = "env -Sx " * 100 + "gh pr merge 7"
        with timing_budget() as timing:
            result = parse_gh_pr_merge(command, "", "/repo")
        elapsed = timing.cpu_seconds
        self.assertLess(timing.wall_seconds, WALL_BACKSTOP_SEC, f"wall {timing.wall_seconds:.2f}s")
        self.assertTrue(result["is_merge"])
        self.assertTrue(result["unresolvable"])
        self.assertLess(elapsed, 1.0, f"env -Sx x100 の parse に {elapsed:.2f}s")

    def test_split_strings_inside_a_bash_c_body_block_in_under_one_second(self):
        command = 'bash -c "' + "env -Sx " * 100 + 'gh pr merge 7"'
        with timing_budget() as timing:
            result = parse_gh_pr_merge(command, "", "/repo")
        elapsed = timing.cpu_seconds
        self.assertLess(timing.wall_seconds, WALL_BACKSTOP_SEC, f"wall {timing.wall_seconds:.2f}s")
        self.assertTrue(result["is_merge"])
        self.assertTrue(result["unresolvable"])
        self.assertLess(elapsed, 1.0, f"bash -c 内 env -Sx x100 の parse に {elapsed:.2f}s")

    def test_split_strings_after_eval_block_in_under_one_second(self):
        command = "eval " + "env -Sx " * 100 + "gh pr merge 7"
        with timing_budget() as timing:
            result = parse_gh_pr_merge(command, "", "/repo")
        elapsed = timing.cpu_seconds
        self.assertLess(timing.wall_seconds, WALL_BACKSTOP_SEC, f"wall {timing.wall_seconds:.2f}s")
        self.assertTrue(result["is_merge"])
        self.assertTrue(result["unresolvable"])
        self.assertLess(elapsed, 1.0, f"eval 後 env -Sx x100 の parse に {elapsed:.2f}s")


class EnvSplitStringExpansionBudgetChdirIntentTests(unittest.TestCase):
    """impl-gate Task 5 Round 1 IG5-1: 展開個数の上限超過を「対象を決められ
    ない」の既存表現へ倒す際、`cd_target` だけでなく `cd_intent` も既定の
    `False` のまま残していた。`_chdir_signals` が `_EnvSplitStringBudgetExceeded`
    を送出するのは `_scan_tokens` より前（`parse_gh_pr_merge` の同じ try 節）
    なので、`cd_intent=False` のまま不足の通知を返すと、hook 側の AC-18
    （`CD_INTENT=true` かつ `CD_TARGET` 空のときだけ働く「実行先を確定できない」
    遮断）を通り抜けてしまう。GDD セッションの repo に steering が無いと、その
    まま無出力 allow になる（origin/main は不足として通知していた。人間承認
    2026-09-11T17:40:42+09:00）。
    """

    OTHER_REPO = "/tmp/ig5-1-other-repo"
    NINE_SPLIT_STRINGS = "env -S '' " * 9
    EIGHT_SPLIT_STRINGS = "env -S '' " * 8

    def test_budget_exceeded_with_chdir_still_signals_cd_intent(self):
        for command in (
            f"cd {self.OTHER_REPO} && {self.NINE_SPLIT_STRINGS}gh pr merge 7",
            f"env -C {self.OTHER_REPO} {self.NINE_SPLIT_STRINGS}gh pr merge 7",
            "bash -c 'cd " + self.OTHER_REPO + " && "
            + self.NINE_SPLIT_STRINGS + "gh pr merge 7'",
        ):
            with self.subTest(command=command):
                result = parse_gh_pr_merge(command, "", "/repo")
                self.assertTrue(result["unresolvable"], command)
                self.assertTrue(result["cd_intent"], command)

    def test_within_budget_with_chdir_is_unaffected(self):
        # 対照: 上限ちょうど（8 個）は従来どおり正常解決し、cd_intent も
        # 上限超過の分岐を経由せず True になる（既存 `_chdir_signals` 経路）。
        command = f"cd {self.OTHER_REPO} && {self.EIGHT_SPLIT_STRINGS}gh pr merge 7"
        result = parse_gh_pr_merge(command, "", "/repo")
        self.assertEqual(result["pr_number"], "7")
        self.assertFalse(result["unresolvable"])
        self.assertTrue(result["cd_intent"])


class EnvSplitStringBackslashCGeneralFormTests(unittest.TestCase):
    """impl-gate Task 5 Round 1 SEC5-1: R6 で足した `\\c` 条件は、本体全体の
    basename が `gh` になり打ち切り経路に入る 1 形（`\\c/gh` のような形）でしか
    評価されない。`\\c` の後ろが `gh` にならない一般形（`env -S 'gh \\cx' pr
    merge 7` 等）は打ち切り経路に入らず、tokenize が `\\c` を普通の文字 `c` として
    残すため、`gh cx pr merge 7` と読まれて merge を検出できない。本ホストの
    `man env`: `\\c` は「文字列の残りを無視する」記号で、実 env は `gh` の 1 引数
    に縮んだ本体と後続引数を合わせて `gh pr merge 7`（現 repo の #7）を実行する
    （人間承認 2026-09-11T17:40:42+09:00。requirements.md の R6 時点の主張
    「`\\c` の形も含めて実態に合う」はこの一般形を判断材料に含めておらず誤り
    だった）。
    """

    def test_backslash_c_general_form_is_detected_as_unresolvable(self):
        for command in (
            "env -S 'gh \\cx' pr merge 7",
            "env -S 'gh\\c' pr merge 7",
            "env -S 'gh \\c' pr merge 7",
            "env -S 'gh \\cfoo bar' pr merge 7",
            "env -S 'gh pr \\cx' merge 7",
            "env -S 'gh -R o/x \\cx' pr merge 7",
        ):
            with self.subTest(command=command):
                result = parse_gh_pr_merge(command, "", "/repo")
                self.assertTrue(result["is_merge"], command)
                self.assertTrue(result["unresolvable"], command)

    def test_backslash_c_free_form_is_unaffected(self):
        # 対照: `\c` を含まない本体は従来どおり正常解決する。
        result = parse_gh_pr_merge("env -S 'gh' pr merge 7", "", "/repo")
        self.assertEqual(result["pr_number"], "7")
        self.assertFalse(result["unresolvable"])

    def test_merge_free_command_with_backslash_c_still_over_blocks(self):
        # 上限超過と同じ扱いに倒すため、gh を含まないコマンドも
        # is_merge=True / unresolvable=True になる（上限超過時の既存の
        # 過剰な通知（Known limitations 既載）と同じ性質を \c にも広げる。
        # gh 探索より前に例外を送出するため、gh の有無を見分けられない）。
        result = parse_gh_pr_merge("env -S 'echo \\cx' merge-notes", "", "/repo")
        self.assertTrue(result["is_merge"])
        self.assertTrue(result["unresolvable"])

    def test_backslash_c_in_a_degenerate_body_is_detected_before_the_degeneracy_check(self):
        # impl-gate Task 5 Round 2 IG5-2: Known limitations F-2（本体が shlex
        # で割れない縮退形は、後続引数で merge が完成しても検出しない）の例示に
        # `env -S 'gh pr \c"' merge 7` を使っていたが、`\c` の有無を見る判定が
        # 縮退の判定より前に走るため、この形は F-2 の限界に当たらず不足として通知される。
        # 対照の `env -S 'gh pr "' merge 7`（\c を含まない同型の縮退形）は F-2 の
        # 限界どおり is_merge=False のまま。ドキュメントの例示をこの区別に合わせて
        # 訂正した（`\c` 無し版に差し替え）。
        result = parse_gh_pr_merge("env -S 'gh pr \\c\"' merge 7", "", "/repo")
        self.assertTrue(result["is_merge"])
        self.assertTrue(result["unresolvable"])

    def test_degenerate_body_without_backslash_c_is_still_a_known_limitation(self):
        # 対照: \c を含まない縮退形は、F-2 の限界どおり検出しない（origin/main と
        # 同じ判定。歯止めの例外として人間承認済み）。
        result = parse_gh_pr_merge("env -S 'gh pr \"' merge 7", "", "/repo")
        self.assertFalse(result["is_merge"])


class EnvSplitStringExpansionBudgetHookBehaviorTests(unittest.TestCase):
    """impl-gate Task 5 Round 2 IG5-3（IG5-1 の hook レベル固定。人間承認
    2026-09-11T17:40:53+09:00 の既定案で「hook を実際に起動するテストを 1 本
    足す」と約束していたもの）。

    GDD セッションの repo（marker あり）に steering が無い状態で、別 repo へ
    chdir してから展開個数の上限を超える split-string を並べて merge する形は、
    parser 単体では `unresolvable=True` になっていても、`cd_intent` が既定の
    `False` のままだと hook の AC-18 遮断（chdir intent はあるが実行先を 1 つに
    決められない形を不足として通知する既存の仕組み）を通り抜け、無出力 allow になって
    いた（origin/main は不足の通知）。`cd_intent=True` を立てる修正後は、この遮断に
    乗って不足として通知される。
    """

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.home = self.tmp / "home"
        (self.home / ".claude").mkdir(parents=True)
        self.repo = _init_repo(self.tmp)
        _write_marker_only(self.repo, active=True, session_id="test-session")

    def test_budget_exceeded_with_chdir_blocks_via_hook(self):
        other_repo = str(self.tmp / "other-repo")
        command = (
            f"cd {other_repo} && " + "env -S '' " * 9 + "gh pr merge 7"
        )
        result = _run_hook({"tool_input": {"command": command}}, self.repo, self.home)
        self.assertIn('"hookEventName": "PreToolUse"', result.stdout, result.stdout)
        self.assertIn("reason code: pr-target-unresolvable", result.stdout, result.stdout)
