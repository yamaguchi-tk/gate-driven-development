"""merge gate parser の引用符付き演算子（クォート・バックスラッシュで守られた
`;` `|` `&&` 等）を裸の演算子と区別する tokenizer 修正の契約テスト。

`test_merge_gate_hook_command_parse.py` は 72 test あり、health の関数数
閾値 80 に近いため、本修正のテストは別ファイルに置く（design.md § テスト方針）。
"""
from __future__ import annotations

import random
import shlex
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from _merge_gate_input_classes import once_per_input_class
from _merge_gate_support import (
    PLUGIN_ROOT,
    _head_sha,
    _init_repo,
    _run_hook,
    _valid_evidence_lines,
    _write_state,
)

sys.path.insert(0, str(PLUGIN_ROOT / "hooks" / "scripts"))

from lib.gh_command_parse import (  # noqa: E402
    _pick_operator_masks,
    _tokenize_checked,
    parse_gh_pr_merge,
)

SHLEX_SPECIAL_CHARS = frozenset(" \t\r\n'\"\\();<>|&")
ONE_BYTE_FREE_CHARS = frozenset(chr(p) for p in range(0x0001, 0x0100)) - SHLEX_SPECIAL_CHARS


class QuotedOperatorAc1Tests(unittest.TestCase):
    """AC-1: 引用符・バックスラッシュで守られた演算子文字は区切り・
    リダイレクトの読み飛ばしのどちらにもならない。"""

    def test_quoted_operator_does_not_split_or_get_skipped(self):
        cases = [
            ("gh pr merge -t ';' 8", "8", None),
            ('gh pr merge -t ";" 8', "8", None),
            (r"gh pr merge -t \; 8", "8", None),
            ("gh pr merge -b '|' 8", "8", None),
            ("gh pr merge -t '&&' 8", "8", None),
            ('bash -c "gh pr merge -t \';\' 8"', "8", None),
        ]
        for command, pr_number, repo_flag in cases:
            with self.subTest(command=command):
                result = parse_gh_pr_merge(command, "", "/repo")
                self.assertEqual(result["pr_number"], pr_number)
                self.assertFalse(result["unresolvable"])
                self.assertEqual(result["repo_flag"], repo_flag)

    def test_quoted_operator_with_repo_flag(self):
        result = parse_gh_pr_merge(
            "gh pr merge -t ';' 8 -R other/repo", "", "/repo",
        )
        self.assertEqual(result["pr_number"], "8")
        self.assertEqual(result["repo_flag"], "other/repo")

    def test_quoted_operator_as_positional_argument_is_unresolvable(self):
        # 承認ポイント 2: 位置引数に引用符付き演算子を置く形は、語として
        # 数えられるため unresolvable=True に変わる（gh 自身が拒否する形）。
        for command in ("gh pr merge '<' 8", "gh pr merge 8 ';'"):
            with self.subTest(command=command):
                result = parse_gh_pr_merge(command, "", "/repo")
                self.assertTrue(result["unresolvable"])


class QuotedOperatorAc2Tests(unittest.TestCase):
    """AC-2: 裸の演算子の意味は変わらない（origin/main と同じ絶対値）。"""

    def test_bare_operators_unchanged(self):
        result = parse_gh_pr_merge(
            "gh pr merge 7 ; gh pr merge 8", "", "/repo",
        )
        self.assertTrue(result["unresolvable"])
        result = parse_gh_pr_merge(
            "gh pr merge 7 && gh pr merge 999", "", "/repo",
        )
        self.assertTrue(result["unresolvable"])

    def test_bare_redirect_unchanged(self):
        self.assertEqual(
            parse_gh_pr_merge("gh pr merge 7 2>&1", "", "/repo")["pr_number"],
            "7",
        )
        self.assertEqual(
            parse_gh_pr_merge("gh pr merge 7 </dev/null", "", "/repo")["pr_number"],
            "7",
        )

    def test_command_substitution_prefix_still_detected(self):
        self.assertTrue(
            parse_gh_pr_merge("$(echo gh) pr merge 7", "", "/repo")["is_merge"]
        )

    def test_nested_bash_c_bare_semicolon_still_splits(self):
        result = parse_gh_pr_merge(
            "bash -c 'cd /B; gh pr merge 7'", "", "/repo",
        )
        self.assertEqual(result["pr_number"], "7")
        self.assertIsNone(result["cd_target"])
        self.assertTrue(result["cd_intent"])

    def test_operator_token_before_subcommand_is_pinned(self):
        # sub-command（`pr`）より前に演算子文字だけの引用付き token を置く形。
        # `(` `)` は is_merge を False にする（gh 自身が未知の sub-command として
        # 拒否するため merge は起きない。docs/adr 55 行 1 文字形 6 形の代表例）。
        # `-R` / `--hostname` の値に置いた `;` は is_merge を True にする
        # （不足の通知側。docs/adr 55 行の 21 形のうち値が制御演算子 3 種の 9 形）。
        for command, expected_is_merge in (
            ("gh '(' pr merge 8", False),
            ("gh ')' pr merge 8", False),
            (r"gh \( pr merge 8", False),
            ("gh -R ';' pr merge 8", True),
            ("gh --hostname ';' pr merge 8", True),
        ):
            with self.subTest(command=command):
                result = parse_gh_pr_merge(command, "", "/repo")
                self.assertIs(result["is_merge"], expected_is_merge)


class QuotedOperatorAc4cTests(unittest.TestCase):
    """AC-4(c): 引用付きと裸の演算子が混在する形・引用の境界の形（絶対値）。

    クォート走査の誤り 3 種（引用内の別種の引用符を閉じとみなす / 引用外の
    `\\` を無視する / 二重引用符内の `\\` を無視する）を mutation として
    当てると、それぞれ 1 件以上が赤くなる（design.md § テスト方針）。
    Task 8 で足した単引用符内 `\\` の検出（mutation #8）も、
    `test_fail_open_forms_resolve_the_trailing_pr` /
    `test_over_block_forms_stay_resolvable` の追加 subTest で同様に赤くなる。
    """

    def test_over_block_forms_stay_resolvable(self):
        # 過剰な通知を検出する側: 引用の扱いを誤ると、正当な merge まで
        # unresolvable=True に倒れてしまう。
        cases = [
            "gh pr merge -t ';' 7 && echo done",
            "gh pr merge 7 -t 'fix' && echo done",
            'gh pr merge 7 -t "a\'b" && echo done',
            "gh pr merge 7 -t 'a\"b' && echo done",
            r"gh pr merge 7 -t \' && echo done",
            r'gh pr merge 7 -t "\"" && echo done',
            r"gh pr merge 7 -t 'a\' && echo done",
            r"gh pr merge 7 -t '\' && echo done",
        ]
        for command in cases:
            with self.subTest(command=command):
                result = parse_gh_pr_merge(command, "", "/repo")
                self.assertEqual(result["pr_number"], "7")
                self.assertFalse(result["unresolvable"])

    def test_fail_open_forms_resolve_the_trailing_pr(self):
        # fail-open を検出する側: 値を取る flag の値がクォート境界を誤読
        # すると、後ろの `-b ';'` が読み飛ばされず PR 番号を見失う。
        cases = [
            ('gh pr merge -t "\'" -b \';\' 8', "8"),
            ('gh pr merge -t \'a"b\' -b ";" 8', "8"),
            (r"gh pr merge -t \' -b ';' 8", "8"),
            (r"gh pr merge -t 'a\' -b ';' 8", "8"),
            (r"gh pr merge -t '\' -b ';' 8", "8"),
        ]
        for command, pr_number in cases:
            with self.subTest(command=command):
                result = parse_gh_pr_merge(command, "", "/repo")
                self.assertEqual(result["pr_number"], pr_number)
                self.assertFalse(result["unresolvable"])

    def test_quoted_operator_before_bare_separator(self):
        result = parse_gh_pr_merge(
            "gh pr merge -t ';' 7 ; gh pr merge 8", "", "/repo",
        )
        self.assertTrue(result["unresolvable"])

    def test_quoted_operator_after_cd_prefix(self):
        result = parse_gh_pr_merge(
            "cd /A && gh pr merge -t ';' 7", "", "/repo",
        )
        self.assertEqual(result["pr_number"], "7")
        self.assertEqual(result["cd_target"], "/A")
        self.assertTrue(result["cd_intent"])

    def test_quoted_operator_inside_heredoc_interpreter_body(self):
        cmd = "bash <<EOF\ngh pr merge -t ';' 8\nEOF"
        result = parse_gh_pr_merge(cmd, "", "/repo")
        self.assertEqual(result["pr_number"], "8")

    def test_quoted_operator_inside_eval(self):
        result = parse_gh_pr_merge(
            "eval \"gh pr merge -t ';' 8\"", "", "/repo",
        )
        self.assertEqual(result["pr_number"], "8")


class QuotedOperatorHookSubprocessTests(unittest.TestCase):
    """AC-3: hook サブプロセスの判定表（PR #7 の承認・証跡が揃った fixture）。"""

    # 別 PR（#8）宛ての merge を、引用付き演算子で PR 番号の手前に隠した形。
    QUOTED_OPERATOR_FORMS = (
        "gh pr merge -t ';' 8",
        "gh pr merge -t ';' 8 -R other/repo",
        "gh pr merge -b '|' 8",
        "gh pr merge -t '&&' 8",
        'gh pr merge -t ";" 8',
        r"gh pr merge -t \; 8",
        'bash -c "gh pr merge -t \';\' 8"',
    )
    # 引用付き演算子を含まない別 PR 宛て（修正の前後とも不足の通知の対照）。
    CONTROL_FORMS = ("gh pr merge 8", "gh pr merge -t 'x' 8")
    # 承認済み PR（#7）宛て。引用付き演算子があっても allow のまま。
    APPROVED_FORMS = ("gh pr merge 7", "gh pr merge -t ';' 7", "gh pr merge 7 -b '|'")

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.home = self.tmp / "home"
        (self.home / ".claude").mkdir(parents=True)
        self.repo = _init_repo(self.tmp)
        self.head = _head_sha(self.repo)
        # repo の状態は active の値だけで決まるので、active ごとに、hook に同じ入力が渡る行は 1 回だけ起動する
        self._hooks = {
            active: once_per_input_class(
                lambda payload: _run_hook(payload, self.repo, self.home), self.repo)
            for active in (True, False)
        }

    def _run(self, command, *, active):
        _write_state(
            self.repo, active=active,
            extra_lines=_valid_evidence_lines(self.head),
        )
        return self._hooks[active]({"tool_input": {"command": command}})

    def test_active_true_quoted_operator_forms_block_approval_pr_mismatch(self):
        for command in self.QUOTED_OPERATOR_FORMS:
            with self.subTest(command=command):
                result = self._run(command, active=True)
                self.assertIn('"hookEventName": "PreToolUse"', result.stdout, command)
                self.assertIn("approval-pr-mismatch", result.stdout, command)
                if "-R other/repo" in command:
                    self.assertIn("pr-target-unresolvable", result.stdout, command)

    def test_active_true_control_forms_still_block_approval_pr_mismatch(self):
        for command in self.CONTROL_FORMS:
            with self.subTest(command=command):
                result = self._run(command, active=True)
                self.assertIn('"hookEventName": "PreToolUse"', result.stdout, command)
                self.assertIn("approval-pr-mismatch", result.stdout, command)

    def test_active_true_approved_pr_with_quoted_operator_still_allows(self):
        for command in self.APPROVED_FORMS:
            with self.subTest(command=command):
                result = self._run(command, active=True)
                self.assertNotIn('"hookEventName": "PreToolUse"', result.stdout, command)

    def test_active_false_matches_origin_main_jurisdiction_rules(self):
        # active: false（管轄外）では、上の全形（単一の merge）が修正の前後とも
        # allow。管轄外でも不足として通知するのは複数 merge の `7 ; 8` だけ。
        for command in self.QUOTED_OPERATOR_FORMS + self.CONTROL_FORMS + self.APPROVED_FORMS:
            with self.subTest(command=command):
                result = self._run(command, active=False)
                self.assertNotIn('"hookEventName": "PreToolUse"', result.stdout, command)
        result = self._run("gh pr merge 7 ; gh pr merge 8", active=False)
        self.assertIn('"hookEventName": "PreToolUse"', result.stdout)


class QuotedOperatorAc5UnitTests(unittest.TestCase):
    """AC-5 群 1・群 2: 内部表現に使いうる文字が入力に含まれていても、
    それらが含まれない場合と同じ規則で決まる。"""

    def test_representative_private_use_char_does_not_change_result(self):
        # 群 1: U+E03B（design.md の代表例）。回帰の保険として機械的に確認する
        # だけで、AC-5 群 1（内部表現の候補選びが入力と衝突しないこと）の
        # 主要な検出力は群 2（衝突を実際に発生させる下の test）が担う。
        # この test は「除外を外す」変異（実装が私用領域の別の文字を
        # 選んだ場合の衝突漏れ）は検出しない（正しい実装では期待どおり
        # 通る。adr.md ADR-1 Consequences）。
        filler = chr(0xE03B)
        for command in (
            f"bash -c \"gh pr merge -t {filler} 8\"",
            f"bash -c \"gh pr merge -t {filler} 8\"; cat <<EOF\nx\nEOF",
        ):
            with self.subTest(command=repr(command)):
                result = parse_gh_pr_merge(command, "", "/repo")
                self.assertTrue(result["is_merge"])
                self.assertEqual(result["pr_number"], "8")

    def test_exclusion_detection_chars_do_not_change_result(self):
        # 群 2: 実装が「入力に現れる文字」を除外せずに割り当てると、
        # U+0004（`;` の既定割当）/ U+0007（`|` の既定割当）を含む入力で
        # 衝突が起きる（design.md §1、adr.md ADR-7）。
        for codepoint in (0x0004, 0x0007):
            filler = chr(codepoint)
            for command in (
                f'bash -c "gh pr merge -t {filler} 8"',
                f'bash -c "gh pr merge -t {filler} 8"; cat <<EOF\nx\nEOF',
            ):
                with self.subTest(command=repr(command)):
                    result = parse_gh_pr_merge(command, "", "/repo")
                    self.assertEqual(result["pr_number"], "8")


class QuotedOperatorAc5RealisticExhaustionTests(unittest.TestCase):
    """AC-5 群 3: 私用領域 U+E000–U+F8FF の 6400 文字全部を入力に含めても、
    候補は U+F8FF で打ち切らない実装なら使い切らない。"""

    def test_full_private_use_area_does_not_exhaust_masks(self):
        # 1 段目の 241 文字を含めないと、1 段目で候補が見つかり、2 段目の
        # 打ち切りを検出できない（design.md § テスト方針）。
        filler = "".join(sorted(ONE_BYTE_FREE_CHARS)) + "".join(
            chr(p) for p in range(0xE000, 0xF900)
        )
        self.assertEqual(len(filler), 241 + 6400)
        # 二重引用符の中のバッククォートは置換を開く（bash は閉じない置換で構文エラー）ので、`\\` で
        # エスケープして文字のまま nested shell に渡す。
        quoted_filler = filler.replace("`", "\\`")
        for command in (
            f"gh pr merge -t ';' 8 -b '{filler}'",
            f"bash -c \"gh pr merge -t ';' 8 -b '{quoted_filler}'\"",
        ):
            with self.subTest(command=f"<len={len(command)}>"):
                result = parse_gh_pr_merge(command, "", "/repo")
                self.assertEqual(result["pr_number"], "8")
                self.assertFalse(result["degraded"])


class QuotedOperatorAc5FullExhaustionUnitTests(unittest.TestCase):
    """AC-5 群 4 前半: 候補の開始点を `unittest.mock.patch` で
    0x10FFF0 に差し替え、U+10FFF0–U+10FFFF の 16 文字を全部含む入力で
    parser が `ValueError` を出すこと（parser の外まで例外が伝播すること）。
    """

    def _high_chars(self):
        return "".join(chr(p) for p in range(0x10FFF0, 0x110000))

    def test_full_exhaustion_raises_value_error(self):
        filler = "".join(sorted(ONE_BYTE_FREE_CHARS)) + self._high_chars()
        self.assertEqual(len(filler), 241 + 16)
        escaped_semicolon = chr(0x5C) + ";"
        cases = [
            f"gh pr merge -t ';' 8 -b '{filler}'",
            f'gh pr merge -t ";" 8 -b \'{filler}\'',
            f"gh pr merge -t {escaped_semicolon} 8 -b '{filler}'",
            f"bash -c 'gh pr merge 8' '{filler}'; cat <<EOF\nx\nEOF",
            f"echo '{filler}';gh pr merge 8; cat <<EOF\nx\nEOF",
        ]
        with mock.patch("lib.shell_lexer.OPERATOR_MASK_START", 0x10FFF0):
            for command in cases:
                with self.subTest(command=f"<len={len(command)}>"):
                    # メッセージを `chr()` 由来（候補の使い切り）に限定する。
                    # shlex の閉じないクォート由来の ValueError は
                    # `_tokenize_checked` の try 節が捕捉して degraded=True に
                    # 変換するため、ここまで伝播しない（parse_gh_pr_merge の外へ
                    # 出る ValueError は `_pick_operator_masks` 由来だけのはず）。
                    with self.assertRaisesRegex(ValueError, r"^chr\(\) arg not in range"):
                        parse_gh_pr_merge(command, "", "/repo")

    def test_partial_sixteen_chars_does_not_exhaust(self):
        # 対照: 241 文字 + 16 文字のうち 7 文字だけ含む入力は使い切らない（退避するのは演算子文字 7 種と
        # 改行・`{` の 9 文字）。
        filler = "".join(sorted(ONE_BYTE_FREE_CHARS)) + self._high_chars()[:7]
        command = f"gh pr merge -t ';' 8 -b '{filler}'"
        with mock.patch("lib.shell_lexer.OPERATOR_MASK_START", 0x10FFF0):
            result = parse_gh_pr_merge(command, "", "/repo")
        self.assertEqual(result["pr_number"], "8")
        self.assertFalse(result["degraded"])


class QuotedOperatorAc5FullExhaustionHookTests(unittest.TestCase):
    """AC-5 群 4 後半: hook サブプロセスでの完全な使い切り（実入力）。

    使い切りの 2 件は約 4.2MB の入力を hook に渡すので、`_run_hook` に
    `timeout=60` を渡す。確かめたいのは「候補を使い切ると例外が parser の外へ
    伝播し、hook が parse-error として不足を通知する」経路で、所要時間ではない。
    当時の既定の 10 秒（本番の merge gate の timeout と同じ）では、並列回帰
    （`pytest -n auto`）の負荷で時間切れになった。この大きさの入力は argv では
    実行できない（ARG_MAX を超える）。今の既定の打ち切りは `HANG_GUARD`
    （hooks.json の timeout の 6 倍）で、渡す 60 秒と同じ値になった。対照の
    小さい入力は既定の打ち切りのまま。
    """

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.home = self.tmp / "home"
        (self.home / ".claude").mkdir(parents=True)
        self.repo = _init_repo(self.tmp)
        self.head = _head_sha(self.repo)
        _write_state(
            self.repo, active=True,
            extra_lines=_valid_evidence_lines(self.head),
        )

    def _exhausting_filler(self):
        # ONE_BYTE_FREE_CHARS（241 文字）と、U+E000–U+10FFFF を 8 文字ずつの
        # 「語」に分けた入力（約 119 万文字）を空白でつなぐ。
        chars = [chr(p) for p in range(0xE000, 0x110000)]
        words = [
            "".join(chars[i:i + 8]) for i in range(0, len(chars), 8)
        ]
        return "".join(sorted(ONE_BYTE_FREE_CHARS)) + " " + " ".join(words)

    def test_bash_c_form_blocks_with_parse_error(self):
        filler = self._exhausting_filler()
        command = f"bash -c 'gh pr merge 8' '{filler}'; cat <<EOF\nx\nEOF"
        result = _run_hook(
            {"tool_input": {"command": command}}, self.repo, self.home, timeout=60,
        )
        self.assertIn('"hookEventName": "PreToolUse"', result.stdout)
        self.assertIn("parse-error", result.stdout)

    def test_echo_form_blocks_with_parse_error(self):
        filler = self._exhausting_filler()
        command = f"echo '{filler}';gh pr merge 8; cat <<EOF\nx\nEOF"
        result = _run_hook(
            {"tool_input": {"command": command}}, self.repo, self.home, timeout=60,
        )
        self.assertIn('"hookEventName": "PreToolUse"', result.stdout)
        self.assertIn("parse-error", result.stdout)

    def test_control_form_still_allows(self):
        result = _run_hook({"tool_input": {"command": "gh pr merge 7"}}, self.repo, self.home)
        self.assertNotIn('"hookEventName": "PreToolUse"', result.stdout)


class OperatorMaskChoiceTests(unittest.TestCase):
    """AC 外・Task 7 H-1 の再発防止: 内部表現の候補の選び方の不変条件。

    候補は 2 段（design.md § 詳細設計 1）。1 段目は U+0001〜U+00FF のうち
    shlex が特別扱いしない 241 文字（`ONE_BYTE_FREE_CHARS`）。2 段目は
    `OPERATOR_MASK_START`（U+E000）以降。
    """

    def test_masking_is_transparent_to_tokenize(self):
        # マスキング（内部表現への一時退避 + 復元）は tokenize の結果（token の
        # 境界・文字面）に対して透過であるべき不変条件。`_tokenize_checked` の
        # 復元後 token 列を素の str に戻したものは、マスキングを経由しない
        # 素の shlex（同じ設定）の token 列と一致するはず（ここの生成入力は行継続を
        # 含まない。行継続は `shell_lexer.normalize` が先に消す。独立レビュー実測、
        # 2026-09-11。実装で 122,016 件の fuzz 入力に対して差分 0 件を確認済み。
        # ここでは決定的な生成入力 300 件で同じ不変条件を固定する）。
        words = ["gh", "pr", "merge", "8", "7", "-t", "-b", "-R", "owner/repo", "a", "あ"]
        quotes = ["", "'", '"']
        operators = [";", "|", "&", "&&", "||", "(", ")", "<", ">"]
        rng = random.Random(20260911)
        cases: list[str] = []
        for _ in range(300):
            piece_count = rng.randint(1, 5)
            pieces = []
            for _ in range(piece_count):
                kind = rng.choice(("word", "quoted_op", "bare_op", "escaped_op"))
                if kind == "word":
                    pieces.append(rng.choice(words))
                elif kind == "quoted_op":
                    q = rng.choice(quotes) or "'"
                    pieces.append(f"{q}{rng.choice(operators)}{q}")
                elif kind == "bare_op":
                    pieces.append(rng.choice(operators))
                else:
                    pieces.append("\\" + rng.choice([o for o in operators if len(o) == 1]))
            cases.append(" ".join(pieces))

        for command in cases:
            with self.subTest(command=repr(command)):
                tokens, degraded = _tokenize_checked(command)
                if degraded:
                    # 縮退経路は `_tokenize_checked` 自身の別の不変条件
                    # （`shell_lexer.FALLBACK_TOKEN_RE` へのフォールバック）が対象なのでここでは skip
                    continue
                plain_lexer = shlex.shlex(command, posix=True, punctuation_chars=True)
                plain_lexer.whitespace_split = True
                plain_lexer.commenters = ""
                try:
                    plain_tokens = list(plain_lexer)
                except ValueError:
                    self.fail(
                        f"_tokenize_checked did not degrade but plain shlex raised for {command!r}"
                    )
                self.assertEqual([str(tok) for tok in tokens], plain_tokens)

    def test_module_shlex_special_chars_matches_this_file_copy(self):
        # 本ファイル冒頭の `SHLEX_SPECIAL_CHARS` は、実装の定数を無条件に
        # 信じないための独立定義（意図的な重複）。ただし実装側で
        # `COMMAND_OPERATOR_CHARS` 等が増減しても本ファイルの定義だけ古いまま
        # 残ると、上とテスト全体が気づかずに緑のまま古い集合を検証し続ける
        # （独立レビュー実測、2026-09-11）。ここで両者の一致を 1 本 pin する。
        from lib.gh_command_parse import _SHLEX_SPECIAL_CHARS

        self.assertEqual(SHLEX_SPECIAL_CHARS, _SHLEX_SPECIAL_CHARS)

    def test_masks_stay_one_byte_wide_when_one_byte_candidates_remain(self):
        # 不変条件 1: 1 段目に空きがある入力では、選ばれる内部表現は
        # すべて U+00FF 以下（1 byte 幅）になる。旧設計（Task 7 未修正）では
        # 候補が U+E000 から始まるため、この 3 subTest はすべて赤くなる。
        cases = [
            "gh pr merge -t ';' 8",
            "gh pr merge -t ';' 8 -b 'あ😀'",
            "gh pr merge -t ';' 8 -b '"
            + "".join(chr(p) for p in range(0xE000, 0xE007))
            + "'",
        ]
        for command in cases:
            with self.subTest(command=repr(command)):
                masks = _pick_operator_masks(command)
                self.assertEqual(len(masks), 9)
                for char in masks.values():
                    self.assertLessEqual(ord(char), 0xFF)

    def test_masks_never_use_shlex_special_chars(self):
        # 不変条件 2: 選ばれる内部表現は SHLEX_SPECIAL_CHARS を含まない。
        cases = [
            "".join(chr(p) for p in range(0x0001, 0x0009)),
            "".join(sorted(ONE_BYTE_FREE_CHARS)),
        ]
        for text in cases:
            with self.subTest(text=repr(text)):
                masks = _pick_operator_masks(text)
                self.assertEqual(len(masks), 9)
                for char in masks.values():
                    self.assertNotIn(char, SHLEX_SPECIAL_CHARS)


if __name__ == "__main__":
    unittest.main()
