"""`done_guard.py` Check 2 の閉じた文法パーサ契約テスト（AC-4 / AC-7 / AC-8 / AC-9、T-3）。

実行:
  python3 -m pytest plugins/gate-driven-development/tests/test_done_guard_closed_grammar_contract.py -v

対象は `lib.done_guard._scan_verification()` / `_classify_verification_line()` の
**受理面と違反分類**（design.md § 4 / § 5）。block メッセージの文言・reason 文字列の
組み立ては `gdd_stop_hook.py` 側（T-4）の責務なので、本ファイルは
`_scan_verification()` が返す `(verification_section_found, verification_data_rows,
violations, unfinished)` の構造化データのみを pin する。

Contract Surface Coverage（T-3 スコープ = 純粋なパース関数。外部 API 呼び出しなし）:
- success path: applicable -> canonical 3 method 種の受理
- no-op / silent success path: applicable -> 空節 / `- なし` / header のみ / separator のみ
- external API response variants: not_applicable（外部 API を呼ばない）
- external API failure / unavailable path: not_applicable（同上）
- validation / sanitize / fail-closed path: applicable -> 列挙外の行 14 形の violation 化
- formatting / output schema path: not_applicable（block メッセージ整形は T-4 の責務）
- duplicate / idempotency / lock path: not_applicable（状態を持たない純粋関数）
- user-visible side effect path: not_applicable（副作用なし。block メッセージ表示は T-4）
"""
from __future__ import annotations

import sys
import unittest

from _paths import PLUGIN_ROOT
_HOOKS_SCRIPTS = str(PLUGIN_ROOT / "hooks" / "scripts")
if _HOOKS_SCRIPTS not in sys.path:
    sys.path.insert(0, _HOOKS_SCRIPTS)

import lib.done_guard as done_guard  # noqa: E402


# ---------------------------------------------------------------------------
# AC-8: 16 シンボル + D3 の 2 シンボルが削除されていること
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# AC-4 / AC-8: `_classify_verification_line()` の行分類（新設）
# ---------------------------------------------------------------------------


class ClassifyVerificationLineTests(unittest.TestCase):
    def test_canonical_ac_row_is_data(self):
        kind, payload = done_guard._classify_verification_line(
            "| method=ac:AC-1 | pass | ok | - |"
        )
        self.assertEqual((kind, payload), ("data", ("ac", "pass")))

    def test_canonical_security_evidence_row_is_data(self):
        kind, payload = done_guard._classify_verification_line(
            "| method=security_evidence:code | unsupported | ok | - |"
        )
        self.assertEqual((kind, payload), ("data", ("security_evidence", "unsupported")))

    def test_canonical_security_evidence_row_accepts_pending(self):
        kind, payload = done_guard._classify_verification_line(
            "| method=security_evidence:code | pending | - | 初期値 |"
        )
        self.assertEqual((kind, payload), ("data", ("security_evidence", "pending")))

    def test_canonical_refactor_checkpoint_row_is_data(self):
        kind, payload = done_guard._classify_verification_line(
            "| method=refactor-checkpoint | pass | ok | - |"
        )
        self.assertEqual((kind, payload), ("data", ("refactor-checkpoint", "pass")))

    def test_ac_row_rejects_na_status(self):
        # AC-1 (e): AC 検証行の status は pending/pass/fail のみ。n/a は External
        # Security Evidence 専用（AC-4 が要求する method 種別ごとの status 制約）
        kind, _ = done_guard._classify_verification_line(
            "| method=ac:AC-1 | n/a | ok | - |"
        )
        self.assertEqual(kind, "violation")

    def test_refactor_checkpoint_row_rejects_unsupported_status(self):
        kind, _ = done_guard._classify_verification_line(
            "| method=refactor-checkpoint | unsupported | ok | - |"
        )
        self.assertEqual(kind, "violation")

    def test_blank_line_is_blank(self):
        kind, _ = done_guard._classify_verification_line("")
        self.assertEqual(kind, "blank")

    def test_none_marker_is_empty_marker(self):
        kind, _ = done_guard._classify_verification_line("- なし")
        self.assertEqual(kind, "empty_marker")

    def test_header_row_is_header(self):
        kind, _ = done_guard._classify_verification_line(
            "| method | status | evidence | notes |"
        )
        self.assertEqual(kind, "header")

    def test_separator_row_is_separator(self):
        kind, _ = done_guard._classify_verification_line("|---|---|---|---|")
        self.assertEqual(kind, "separator")

    def test_status_column_only_governs_unfinished_literal_in_other_cells(self):
        # block→done 方向（design.md § 5 最下段）: status 列以外に literal な
        # `pending`/`fail` を含んでいても data 行として受理し、status は cells[1] のみで判定する
        kind, payload = done_guard._classify_verification_line(
            "| method=ac:AC-1 | pass | fail | - |"
        )
        self.assertEqual((kind, payload), ("data", ("ac", "pass")))


class ClassifyVerificationLineViolationFormsTests(unittest.TestCase):
    """AC-4 / AC-5（detection 側）: 列挙外 14 形はすべて violation になる（design.md § 5）。"""

    def _assert_violation(self, line: str, msg: str):
        kind, _ = done_guard._classify_verification_line(line)
        self.assertEqual(kind, "violation", msg)

    def test_decorative_status_backtick(self):
        self._assert_violation(
            "| method=ac:AC-1 | `pass` | ok | - |", "装飾 status（コードスパン）"
        )

    def test_decorative_status_bold(self):
        self._assert_violation(
            "| method=ac:AC-1 | **pass** | ok | - |", "装飾 status（太字）"
        )

    def test_annotated_status(self):
        self._assert_violation(
            "| method=ac:AC-1 | pass（2026-08-30 実施） | ok | - |", "注記付き status"
        )

    def test_status_label_form_inside_cell(self):
        self._assert_violation(
            "| method=ac:AC-1 | status=pass | ok | - |", "`status=pass` ラベル形"
        )

    def test_method_colon_label_form(self):
        self._assert_violation(
            "| method: ac:AC-1 | pass | ok | - |", "`method:` コロン + 空白形"
        )

    def test_japanese_header_table_is_not_header(self):
        self._assert_violation(
            "| ステータス | 状態 | 判定 | 項目 |", "日本語 header 表は header 4 語一致しない"
        )

    def test_code_span_pipe_in_evidence_becomes_five_cells(self):
        self._assert_violation(
            "| method=ac:AC-1 | pass | `rg a | sort` | - |",
            "D3: コードスパン内の | を保護しないので 5 セルになり violation",
        )

    def test_list_row(self):
        self._assert_violation(
            "- method=ac:AC-1 | pass | ok | -", "list 行（外側パイプなし）"
        )

    def test_quote_row(self):
        self._assert_violation(
            "> | method=ac:AC-1 | pass | ok | - |", "引用行"
        )

    def test_indented_row(self):
        self._assert_violation(
            "  | method=ac:AC-1 | pass | ok | - |", "インデント行"
        )

    def test_outer_pipe_omitted_row(self):
        self._assert_violation(
            "method=ac:AC-1 | pass | ok | -", "外側パイプ省略行"
        )

    def test_full_width_pipe_row(self):
        self._assert_violation(
            "｜method=ac:AC-1｜pass｜ok｜-｜", "全角パイプ行"
        )

    def test_legend_list_row(self):
        self._assert_violation(
            "- 許容 status: pending, pass, fail, n/a, unsupported", "凡例 list"
        )

    def test_h3_heading_prose(self):
        self._assert_violation("### 判定基準", "H3 見出し / 散文")

    def test_five_column_row_id_table(self):
        self._assert_violation(
            "| V-01 | unit_test | pending | - | - |", "5 列 ROW-ID 表 / list"
        )

    def test_escaped_pipe_joined_pending_is_column_count_violation(self):
        self._assert_violation(
            "| method=ac:AC-1 \\| pending | ok | - | - |",
            "`\\|` で結合した pending は列数不正",
        )


# ---------------------------------------------------------------------------
# AC-4 / AC-8 第 2 条項: 正規化を `ws`（半角空白 / タブ）と ASCII 語彙に閉じる
#
# impl-gate R3 IMPL-R3-H1 の回帰検出器。削除した `_CELL_TRIM_CHARS`（全角空白を含む）や
# `str.lower()` の Unicode 畳み込みが、Python 既定関数の**別名**（`str.strip()` /
# `\d` / `$`）で復活していないことを両方向で pin する。
# 正本: design.md § 1.2（`ws` = 半角空白 / タブ。全角空白・制御文字は除去しない）/
# § 5（「全角空白 padding の status」= done→block）/ § 1.1（`AC_ID` の `DIGIT` は ASCII）。
# ---------------------------------------------------------------------------

_FULLWIDTH_SPACE = "　"
_NBSP = " "
_LINE_SEPARATOR = " "


class CellNormalizationIsAsciiOnlyTests(unittest.TestCase):
    """`ws` は半角空白 / タブのみ。Unicode 空白・Unicode 数字は正規化に含めない。"""

    def _assert_violation(self, line: str, msg: str):
        kind, _ = done_guard._classify_verification_line(line)
        self.assertEqual(kind, "violation", msg)

    # --- 拒否側: Unicode 空白 padding（`str.strip()` を使うと全部通ってしまう） ---

    def test_fullwidth_space_padded_pass_status_is_violation(self):
        # design.md § 5: 「全角空白 padding の status」= ALLOW → violation（done→block）。
        # `pass` 側は 149 case にも fixture が無く、ここが唯一の検出器
        self._assert_violation(
            f"| method=ac:AC-1 |{_FULLWIDTH_SPACE}pass{_FULLWIDTH_SPACE}| ok | - |",
            "全角空白 padding の pass は violation",
        )

    def test_fullwidth_space_padded_pending_status_is_violation(self):
        self._assert_violation(
            f"| method=ac:AC-1 |{_FULLWIDTH_SPACE}pending{_FULLWIDTH_SPACE}| ok | - |",
            "全角空白 padding の pending は violation",
        )

    def test_nbsp_padded_status_is_violation(self):
        self._assert_violation(
            f"| method=ac:AC-1 |{_NBSP}pass{_NBSP}| ok | - |",
            "NBSP padding の status は violation",
        )

    def test_line_separator_padded_status_is_violation(self):
        self._assert_violation(
            f"| method=ac:AC-1 |{_LINE_SEPARATOR}pass{_LINE_SEPARATOR}| ok | - |",
            "U+2028 padding の status は violation",
        )

    def test_fullwidth_space_padded_method_cell_is_violation(self):
        self._assert_violation(
            f"| {_FULLWIDTH_SPACE}method=ac:AC-1{_FULLWIDTH_SPACE} | pass | ok | - |",
            "全角空白 padding の method セルは violation",
        )

    def test_fullwidth_space_padded_header_is_violation(self):
        kind, _ = done_guard._classify_verification_line(
            f"| method |{_FULLWIDTH_SPACE}status{_FULLWIDTH_SPACE}| evidence | notes |"
        )
        self.assertEqual(kind, "violation", "全角空白 padding の header は 4 語完全一致しない")

    def test_fullwidth_space_padded_separator_is_violation(self):
        kind, _ = done_guard._classify_verification_line(
            f"| --- |{_FULLWIDTH_SPACE}---{_FULLWIDTH_SPACE}| --- | --- |"
        )
        self.assertEqual(kind, "violation", "全角空白 padding の separator は `:?-+:?` に一致しない")

    def test_empty_marker_with_trailing_fullwidth_space_is_violation(self):
        kind, _ = done_guard._classify_verification_line(f"- なし{_FULLWIDTH_SPACE}")
        self.assertEqual(
            kind, "violation", "`- なし` は完全一致。全角空白の末尾 padding は empty_marker にしない"
        )

    # --- 拒否側: ASCII に閉じていない語彙 / 末尾改行 ---

    def test_fullwidth_digit_in_ac_id_is_violation(self):
        # `AC_ID := "AC-" [A-Za-z]? DIGIT+ …` の DIGIT は ASCII。`\d` だと全角数字を拾う
        self._assert_violation(
            "| method=ac:AC-１ | pass | ok | - |", "全角数字の AC ID は violation"
        )

    def test_fullwidth_digit_in_ac_id_suffix_is_violation(self):
        self._assert_violation(
            "| method=ac:AC-1-２ | pass | ok | - |", "複合サフィックスの全角数字も violation"
        )

    def test_trailing_newline_in_method_cell_is_violation(self):
        # regex 末尾が `$` だと `method=ac:AC-1\n` が完全一致として通る（`\Z` なら通らない）
        self._assert_violation(
            "| method=ac:AC-1\n | pass | ok | - |", "method セル末尾の改行は完全一致にしない"
        )

    # --- 拒否側: エスケープされた閉じパイプ ---

    def test_escaped_closing_pipe_is_violation(self):
        # 行末の `\|` は cell の中身であって区切りではないので、4 セルの data 行にならない
        self._assert_violation(
            "| method=ac:AC-1 | pass | ok | -\\|", "エスケープされた閉じパイプは data 行にしない"
        )

    # --- 受理側（過剰締め付けの negative control） ---

    def test_ascii_space_padding_is_still_accepted(self):
        kind, payload = done_guard._classify_verification_line(
            "|   method=ac:AC-1   |   pass   | ok | - |"
        )
        self.assertEqual((kind, payload), ("data", ("ac", "pass")), "半角空白 padding は `ws`")

    def test_tab_padding_is_still_accepted(self):
        # design.md § 1.1 の `ws := " " | TAB`（A6 決着 (2) で文法ブロックへ明文化）。
        # § 5 の「タブ padding」行は A6 決着 (1) で ALLOW / 不変へ訂正済み（adr.md ADR-10）
        kind, payload = done_guard._classify_verification_line(
            "| method=ac:AC-1 |\tpass\t| ok | - |"
        )
        self.assertEqual((kind, payload), ("data", ("ac", "pass")), "タブ padding は `ws`")

    def test_empty_marker_with_trailing_ascii_space_is_still_empty_marker(self):
        kind, _ = done_guard._classify_verification_line("- なし   ")
        self.assertEqual(kind, "empty_marker", "行末の半角空白だけは落とす（§ 1.2 手順 1）")

    def test_escaped_pipe_inside_notes_cell_is_still_data(self):
        kind, payload = done_guard._classify_verification_line(
            "| method=ac:AC-1 | pass | ok | a\\|b |"
        )
        self.assertEqual(
            (kind, payload), ("data", ("ac", "pass")), "セル内の `\\|` は区切りにしない（§ 1.1 cell）"
        )

    def test_compound_ac_id_suffix_is_still_data(self):
        kind, payload = done_guard._classify_verification_line(
            "| method=ac:AC-3-d | pass | ok | - |"
        )
        self.assertEqual((kind, payload), ("data", ("ac", "pass")), "`AC-3-d` 形は受理する")


# ---------------------------------------------------------------------------
# AC-4 / AC-9: `_scan_verification()` 新シグネチャと 4 値タプル
# ---------------------------------------------------------------------------


def _lines(*rows: str) -> list[str]:
    return ["## Verification", *rows, "## Next"]


class ScanVerificationSignatureTests(unittest.TestCase):

    def test_returns_four_tuple_without_fence_arguments(self):
        result = done_guard._scan_verification(
            _lines("| method=ac:AC-1 | pass | ok | - |")
        )
        self.assertEqual(len(result), 4)
        found, data_rows, violations, unfinished = result
        self.assertTrue(found)
        self.assertEqual(len(data_rows), 1)
        self.assertEqual(violations, [])
        self.assertEqual(unfinished, [])


# ---------------------------------------------------------------------------
# AC-9: 検証行ゼロ系（空節 / なし / header のみ / separator のみ）と
#       schema 違反系（列数不正 / 補助表）の区別
# ---------------------------------------------------------------------------


class ScanVerificationZeroRowReasonBasisTests(unittest.TestCase):
    """`_scan_verification` の出力から「検証行がありません」系と
    「schema 違反」系を区別できるだけの情報（violations の有無）が
    得られることを pin する。実際の reason 文字列組み立ては T-4 の責務。
    """

    def test_empty_section_has_zero_violations_and_zero_rows(self):
        found, data_rows, violations, unfinished = done_guard._scan_verification(
            _lines()
        )
        self.assertTrue(found)
        self.assertEqual((data_rows, violations, unfinished), ([], [], []))

    def test_none_marker_only_has_zero_violations_and_zero_rows(self):
        found, data_rows, violations, unfinished = done_guard._scan_verification(
            _lines("- なし")
        )
        self.assertTrue(found)
        self.assertEqual((data_rows, violations, unfinished), ([], [], []))

    def test_header_only_has_zero_violations_and_zero_rows(self):
        found, data_rows, violations, unfinished = done_guard._scan_verification(
            _lines("| method | status | evidence | notes |")
        )
        self.assertTrue(found)
        self.assertEqual((data_rows, violations, unfinished), ([], [], []))

    def test_separator_only_has_zero_violations_and_zero_rows(self):
        found, data_rows, violations, unfinished = done_guard._scan_verification(
            _lines("|---|---|---|---|")
        )
        self.assertTrue(found)
        self.assertEqual((data_rows, violations, unfinished), ([], [], []))

    def test_two_column_separator_is_a_violation_not_empty(self):
        # design.md § 5: separator のみ（2 列）は「検証行がありません」ではなく violation
        found, data_rows, violations, unfinished = done_guard._scan_verification(
            _lines("|:---|:---|")
        )
        self.assertTrue(found)
        self.assertEqual(data_rows, [])
        self.assertNotEqual(violations, [], "2 列 separator は schema 違反として扱う")

    def test_truncated_header_is_a_violation_not_empty(self):
        found, data_rows, violations, unfinished = done_guard._scan_verification(
            _lines("| method |")
        )
        self.assertTrue(found)
        self.assertEqual(data_rows, [])
        self.assertNotEqual(violations, [], "列を削った header は schema 違反として扱う")

    def test_auxiliary_table_is_a_violation_not_empty(self):
        found, data_rows, violations, unfinished = done_guard._scan_verification(
            _lines(
                "| # | severity | 内容 | 対応 |",
                "|---|---|---|---|",
                "| 1 | high | 説明 | 対応済み |",
            )
        )
        self.assertTrue(found)
        self.assertEqual(data_rows, [])
        self.assertNotEqual(
            violations, [], "補助表は method 値域外のため schema 違反として扱う（非計上のまま消えない）"
        )


# ---------------------------------------------------------------------------
# AC-7: 節に重なる fence / fence 内 `## Verification` 見出し
# ---------------------------------------------------------------------------


class ScanVerificationFenceViolationTests(unittest.TestCase):
    def test_section_fence_overlap_becomes_violation(self):
        # F-12 の再現形: 節内の閉じた fence が pending 行を包む
        lines = _lines("```", "| method=ac:AC-1 | pending | - | - |", "```")
        # fence_before[i] は「kept 側 index i の直前に開始した fence の開始行番号」の list。
        # `_lines()` の index=1 の直前（節見出し直後）に fence が開始したことを模す
        fence_before: list[list[int]] = [[] for _ in range(len(lines) + 1)]
        fence_before[1] = [10]
        found, data_rows, violations, unfinished = done_guard._scan_verification(
            lines, fence_before=fence_before, fenced_heading_lines=[]
        )
        self.assertIn(("section_fence", 10), violations)

    def test_trailing_fence_before_next_heading_is_violation(self):
        # design.md § D4「右端 inclusive」の判別力（impl-gate R3 IMPL-R3-M1）。
        # 節末尾の閉じ fence の**直後に空行なしで `## ` 見出し**が来る形（§ 1.5 の推奨形）
        # では、fence が落とした行は `fence_before[e]`（e = 次の `## ` の kept index）に
        # 溜まる。`range(h+1, e+1)` を `range(h+1, e)` に縮めるとこの形が範囲外に落ち、
        # security R1 H-1 が PoC で実測した fail-open が戻る
        lines = _lines("| method=ac:AC-1 | pass | ok | - |")
        e_index = lines.index("## Next")
        fence_before: list[list[int]] = [[] for _ in range(len(lines) + 1)]
        fence_before[e_index] = [20]
        _, _, violations, _ = done_guard._scan_verification(
            lines, fence_before=fence_before, fenced_heading_lines=[]
        )
        self.assertEqual(
            violations,
            [("section_fence", 20)],
            "節末尾 fence + 直後の `## ` 見出しは section_fence 違反（右端 inclusive）",
        )

    def test_trailing_fence_at_end_of_document_is_violation(self):
        # 節が本文末尾にある形（e = len(structural_lines) の sentinel）。
        # `fence_before` は長さ `len(kept)+1` で、最終要素が「最終行より後ろ」を表す
        lines = ["## Verification", "| method=ac:AC-1 | pass | ok | - |"]
        fence_before: list[list[int]] = [[] for _ in range(len(lines) + 1)]
        fence_before[len(lines)] = [31]
        _, _, violations, _ = done_guard._scan_verification(
            lines, fence_before=fence_before, fenced_heading_lines=[]
        )
        self.assertEqual(
            violations, [("section_fence", 31)], "末尾 sentinel の fence も節に重なる"
        )

    def test_two_fences_in_one_gap_are_counted_separately(self):
        # D4 が `int | None` ではなく `list[int]` を選んだ理由そのもの。
        # 同一 gap に潰れた 2 本の fence を 1 件へ丸めると「直した → まだ block」になる
        lines = _lines("| method=ac:AC-1 | pass | ok | - |")
        fence_before: list[list[int]] = [[] for _ in range(len(lines) + 1)]
        fence_before[1] = [10, 14]
        _, _, violations, _ = done_guard._scan_verification(
            lines, fence_before=fence_before, fenced_heading_lines=[]
        )
        self.assertEqual(
            violations,
            [("section_fence", 10), ("section_fence", 14)],
            "1 gap に 2 本の fence があれば fence 単位で 2 件（gap 単位に丸めない）",
        )

    def test_fence_outside_the_section_is_not_a_violation(self):
        # negative control（§ 5「節の前 / 次の `## ` より後の fence」= 不変・誤 block しない）。
        # 右端を広げすぎる方向の mutation（`range(h+1, e+2)`）をここで殺す
        lines = _lines("| method=ac:AC-1 | pass | ok | - |")
        e_index = lines.index("## Next")
        fence_before: list[list[int]] = [[] for _ in range(len(lines) + 1)]
        fence_before[0] = [3]
        fence_before[e_index + 1] = [40]
        _, _, violations, _ = done_guard._scan_verification(
            lines, fence_before=fence_before, fenced_heading_lines=[]
        )
        self.assertEqual(violations, [], "節の前 / 次の `## ` より後の fence は違反にしない")

    def test_fenced_heading_becomes_violation(self):
        lines = _lines("| method=ac:AC-1 | pass | ok | - |")
        found, data_rows, violations, unfinished = done_guard._scan_verification(
            lines, fence_before=None, fenced_heading_lines=[7]
        )
        self.assertIn(("fenced_heading", 7), violations)

    def test_fenced_heading_violation_is_independent_of_section_presence(self):
        # 節外（`#### Steps` 等）の fence に `## Verification` 見出しを含む記入例
        # → 位置非依存で violation になる（section が無くても検出される）
        found, data_rows, violations, unfinished = done_guard._scan_verification(
            ["何もない本文"], fence_before=None, fenced_heading_lines=[3]
        )
        self.assertIn(("fenced_heading", 3), violations)


if __name__ == "__main__":
    unittest.main()
