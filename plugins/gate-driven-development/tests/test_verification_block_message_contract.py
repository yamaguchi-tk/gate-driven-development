"""`gdd_stop_hook.py` の Check 2 block メッセージ契約テスト（AC-5 / AC-6 / AC-7 secondary / AC-20、T-4）。

実行:
  python3 -m pytest plugins/gate-driven-development/tests/test_verification_block_message_contract.py -v

対象は `_verification_errors()` の**新 4 引数 API**（`lib.done_guard._scan_verification()` が
返す `(verification_section_found, verification_data_rows, violations, unfinished)` を
そのまま受け取る）と、`_build_recovery_hints()` / `_has_legacy_security_evidence_writer_shape`
相当の挙動。`_scan_verification()` 自体のパース・分類契約（AC-1/AC-4/AC-7/AC-8/AC-9）は
`test_done_guard_closed_grammar_contract.py`（T-3）の責務なので、本ファイルは**メッセージ整形
（D5 判定順・文言 pin・無害化・fail-open 配線）だけ**を扱う。

Carry Forward からの必須事項:
- `_verification_errors(verification_section_found, verification_data_rows, violations, unfinished)`
  の D5 判定順（節無し → 違反種別 → 検証行 0 件 → unfinished）を先に固定する
- `_scan_verification` の `fence_before` / `fenced_heading_lines` は既定値 `None` -> `[]` を持つ
  （T-3 の単体テスト用）。production 呼び出し（`gdd_stop_hook.py`）がこれを明示的に渡さないと
  fence 違反が常に 0 件になる fail-open の面になる。本ファイルはこの配線漏れを検出する RED を
  静的・動的の両方で持つ
- AC-20: `method=security_evidence:*` の手書き禁止トリガーは**行頭アンカー付き**でなければならず、
  部分一致（散文中の `security_evidence:` 言及）で発火してはならない

Contract Surface Coverage（T-4 スコープ = block メッセージ整形。外部 API 呼び出しなし）:
- success path: applicable -> `test_no_violations_and_no_unfinished_returns_empty_list`
- no-op / silent success path: applicable -> `test_empty_section_with_no_data_rows_reports_missing_rows`
- external API response variants: not_applicable（外部 API を呼ばない。violations は呼び出し元が渡す構造化データ）
- external API failure / unavailable path: not_applicable（同上）
- validation / sanitize / fail-closed path: applicable ->
  `test_fail_open_wiring_passes_fence_kwargs_explicitly`（配線漏れ検出）/
  `SecurityEvidenceWriterAnchorTests`（部分一致で発火しないこと）
- formatting / output schema path: applicable -> `RecoveryHintsCanonicalContentTests` /
  `test_violation_lines_are_capped_at_five_and_truncated_to_eighty_chars`
- duplicate / idempotency / lock path: not_applicable（状態を持たない純粋なメッセージ整形）
- user-visible side effect path: applicable ->
  `test_end_to_end_fenced_heading_swallow_still_blocks_when_wired_correctly`
  （E2E は配線 smoke に残し、他は本ファイルの unit/contract で固定する）
"""
from __future__ import annotations

import ast
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "hooks" / "scripts"))

from _plugin_module_loader import load_plugin_module  # noqa: E402

HOOK_PATH = Path(__file__).resolve().parent.parent / "hooks" / "scripts" / "gdd_stop_hook.py"
HOOK_SRC = HOOK_PATH.read_text(encoding="utf-8")


def _hook_module():
    return load_plugin_module("hooks/scripts/gdd_stop_hook.py")


# ---------------------------------------------------------------------------
# D5 判定順（節無し(1) → 違反種別(2) → 検証行 0 件(3) → unfinished(4)）
# ---------------------------------------------------------------------------


class VerificationErrorsPriorityOrderTests(unittest.TestCase):
    """`_verification_errors(section_found, data_rows, violations, unfinished)` の
    4 引数シグネチャと D5 判定順を pin する。"""

    def test_section_not_found_reports_missing_section(self):
        module = _hook_module()
        result = module._verification_errors(False, [], [], [])
        self.assertEqual(len(result), 1)
        self.assertIn("## Verification セクションが存在しません", result[0])

    def test_section_not_found_still_surfaces_fenced_heading_violation(self):
        """判定順 1（節無し）でも fenced_heading 違反は握り潰さない（design.md D4 併記 / R4 M-4）。

        節見出し自体が fence に飲まれていると `verification_section_found=False` になるが、
        この場合こそ「Notes へ移しても解除されない」回復手順が無いと、書き手は
        何が起きているか分からないまま block され続ける。
        """
        module = _hook_module()
        result = module._verification_errors(False, [], [("fenced_heading", 42)], [])
        self.assertGreaterEqual(len(result), 2, f"fenced_heading 違反が握り潰されている: {result!r}")
        joined = "\n".join(result)
        self.assertIn("## Verification セクションが存在しません", joined)
        # `starts` は `strip_fenced_lines_marked()` の 0 始まり原文 index のまま渡るが、
        # メッセージ層は design.md:200 / :498 の「原文行番号」（人間可読・1 始まり）へ
        # 提示直前に変換する（impl-gate R7 A20 / T-6 carry-in で実装済み）。
        self.assertIn("43", joined)
        self.assertIn("見出し", joined)

    def test_line_violations_take_priority_over_unfinished_when_both_present(self):
        module = _hook_module()
        result = module._verification_errors(
            True,
            ["- V-01 | unit_test | pending | - | -"],
            [("line", "- V-01 | unit_test | pending | - | -")],
            ["- V-01 | unit_test | pending | - | -"],
        )
        joined = "\n".join(result)
        self.assertIn("schema 違反行が", joined, "違反種別(2)が unfinished(4)より先に出るべき")
        self.assertIn("未完了/失敗が", joined, "unfinished は schema 違反と併記される（消えない）")

    def test_zero_data_rows_without_violations_reports_no_verification_rows(self):
        module = _hook_module()
        result = module._verification_errors(True, [], [], [])
        self.assertEqual(len(result), 1)
        self.assertIn("検証行がありません", result[0])

    def test_unfinished_only_reports_unfinished_and_is_not_empty(self):
        """design.md § 6 文言 pin (h): 違反 0 件の種別で空リストを出さない。"""
        module = _hook_module()
        result = module._verification_errors(
            True,
            ["- method=ac:AC-1 | pending | - | - |"],
            [],
            ["- method=ac:AC-1 | pending | - | - |"],
        )
        self.assertNotEqual(result, [], "unfinished のみでも空リストを返してはいけない（(h)）")
        self.assertIn("未完了/失敗が", "\n".join(result))

    def test_no_violations_and_no_unfinished_returns_empty_list(self):
        module = _hook_module()
        result = module._verification_errors(
            True, ["- method=ac:AC-1 | pass | 例 | - |"], [], []
        )
        self.assertEqual(result, [])

    def test_empty_section_with_no_data_rows_reports_missing_rows(self):
        module = _hook_module()
        result = module._verification_errors(True, [], [], [])
        self.assertIn("検証行がありません", result[0])


# ---------------------------------------------------------------------------
# AC-5: 違反行の無害化（safe_for_output + 80 文字打ち切り + 最大 5 件）
# ---------------------------------------------------------------------------


class ViolationLineSanitizationTests(unittest.TestCase):
    def test_violation_lines_are_capped_at_five_and_truncated_to_eighty_chars(self):
        module = _hook_module()
        many = [("line", f"- VIOLATION-MARKER-{i}") for i in range(1, 8)]  # 7 件
        long_raw = "- " + ("x" * 200)
        violations = many + [("line", long_raw)]
        result = module._verification_errors(True, [], violations, [])
        joined = "\n".join(result)
        self.assertIn("8 件", joined, "件数は全件（8）を報告する")
        for i in range(1, 6):
            self.assertIn(f"VIOLATION-MARKER-{i}", joined, f"先頭 5 件目までは提示される: #{i}")
        for i in range(6, 8):
            self.assertNotIn(f"VIOLATION-MARKER-{i}", joined, f"6 件目以降は提示しない: #{i}")
        self.assertNotIn("x" * 200, joined, "80 文字を超える生テキストをそのまま出してはいけない")

    def test_control_characters_in_violation_line_are_scrubbed(self):
        module = _hook_module()
        raw = "- \x1b[2K\x1b[1Gevil"
        result = module._verification_errors(True, [], [("line", raw)], [])
        joined = "\n".join(result)
        self.assertNotIn("\x1b", joined, "ESC が残っている")
        self.assertIn("(invalid: control characters)", joined)


# ---------------------------------------------------------------------------
# design.md § 6 文言 pin (d): 違反行の 2 ラベルが行内容に応じて選ばれる
# ---------------------------------------------------------------------------


class ViolationLineLabelDifferentiationTests(unittest.TestCase):
    def test_legacy_pending_row_is_labeled_as_possibly_unfinished(self):
        module = _hook_module()
        legacy_5col_pending = "- V-01 | unit_test | pending | - | -"
        result = module._verification_errors(True, [], [("line", legacy_5col_pending)], [])
        joined = "\n".join(result)
        self.assertIn("未完了の可能性がある検証行", joined)
        self.assertIn(legacy_5col_pending, joined)

    def test_heading_or_prose_row_is_labeled_as_schema_violation(self):
        module = _hook_module()
        heading_line = "### Verification の書き方"
        result = module._verification_errors(True, [], [("line", heading_line)], [])
        joined = "\n".join(result)
        self.assertIn("schema 違反行", joined)
        self.assertNotIn("未完了の可能性がある検証行", joined)

    def test_ac_id_and_evidence_status_rows_are_labeled_as_possibly_unfinished(self):
        # 独立レビュー R20 IR-1: 設計 D5 はラベル判定語に AC ID を明記している。
        # AC ID だけの行や N/A / unsupported を含む行に「Notes へ移す」ラベルが付くと、
        # 未検証の AC 行を移すと done が通る（判定は変えない。提示ラベルのみ）
        module = _hook_module()
        for row in (
            "| AC-2 | 未実施 | - | - |",
            "- AC-3: N/A (対象外)",
            "- AC-4 未検証（保留）",
            "| x | unsupported | - | - |",
            "| x | N/A | - | - |",
        ):
            with self.subTest(row=row):
                joined = "\n".join(module._verification_errors(True, [], [("line", row)], []))
                self.assertIn("未完了の可能性がある検証行", joined)

    def test_default_label_puts_rewriting_before_moving(self):
        # R12 (B3) SEC S-3: 判定語に一致しない検証行（V-01 行）にも「書き直す」を先に届け、
        # Notes への移動を断定しない（判定語を増やす方向は開いたコーパスへの分類器で閉じない）
        module = _hook_module()
        for row in ("| V-01 | 未実施 | - | - |", "- V-01 | unit_test | 未実施 | - |"):
            with self.subTest(row=row):
                joined = "\n".join(module._verification_errors(True, [], [("line", row)], []))
                self.assertNotIn("未完了の可能性がある検証行", joined)
                self.assertIn("canonical 表行へ書き直す", joined)
                # 書き直しを移動より先に案内する（順序を入れ替えた文言を検出する）
                self.assertLess(
                    joined.index("canonical 表行へ書き直す"), joined.index("Verification Notes へ移す")
                )

    def test_ac_id_boundary_does_not_match_embedded_tokens(self):
        # 前後に英数字が続く形は AC ID として拾わない（`_AC_ID_CORE` の境界）
        module = _hook_module()
        for row in ("MAC-1 の設定メモ", "AC-12x3 のメモ"):
            with self.subTest(row=row):
                joined = "\n".join(module._verification_errors(True, [], [("line", row)], []))
                self.assertNotIn("未完了の可能性がある検証行", joined)


# ---------------------------------------------------------------------------
# design.md § 6 文言 pin (a)(b)(c)(i): canonical / 逃がし先 / 移動禁止 carve-out / エスケープ
# ---------------------------------------------------------------------------


class RecoveryHintsCanonicalContentTests(unittest.TestCase):
    def _schema_violation_error_msg(self) -> str:
        module = _hook_module()
        return "\n".join(
            module._verification_errors(True, [], [("line", "### 見出しの例")], [])
        )

    def test_canonical_three_lines_are_present(self):
        module = _hook_module()
        hints = module._build_recovery_hints(self._schema_violation_error_msg())
        self.assertIn("| method | status | evidence | notes |", hints)
        self.assertIn("|---|---|---|---|", hints)
        self.assertIn("method=ac:AC-1", hints)

    def test_prose_escape_hatch_to_verification_notes_is_offered(self):
        module = _hook_module()
        hints = module._build_recovery_hints(self._schema_violation_error_msg())
        self.assertIn("## Verification Notes", hints)
        self.assertIn("移", hints, "「移す」旨が読み取れる語が必要")

    def test_move_prohibition_names_ledger_file_and_history_section_with_carveout(self):
        """(c-1)/(c-2)/(c-3): 一般形 + 退避と読める語 + carve-out。"""
        module = _hook_module()
        hints = module._build_recovery_hints(self._schema_violation_error_msg())
        self.assertIn("`ac-ledger.md`", hints, "(c-1) 一般形に Ledger（専用ファイル）を含める")
        self.assertNotIn("## AC Trace Ledger", hints, "(c-1) tasklist.md の Ledger の節を正規の置き場所として案内しない")
        self.assertIn("## Verification History", hints, "(c-1) 一般形に History を含める")
        self.assertTrue(
            any(t in hints for t in ("退避", "移して")),
            "(c-2) 禁止しているのが退避であることが読み取れる語が必要",
        )
        self.assertTrue(
            any(t in hints for t in ("正規の記録", "対象外")),
            "(c-3) carve-out（正規の記録は禁止対象外）が必要",
        )

    def test_escaped_pipe_hint_is_present(self):
        module = _hook_module()
        hints = module._build_recovery_hints(self._schema_violation_error_msg())
        self.assertIn("\\|", hints, "(i) セル内の `|` エスケープ方法のヒントが必要")


# ---------------------------------------------------------------------------
# AC-20 / design.md § 6 文言 pin (e)(f): security_evidence 手書き禁止 + 行頭アンカー
# ---------------------------------------------------------------------------


class SecurityEvidenceWriterAnchorTests(unittest.TestCase):
    def test_anchored_legacy_writer_row_triggers_the_dedicated_hint(self):
        module = _hook_module()
        anchored_row = "- SECURITY-CODE | security_evidence:code | pending | - | -"
        error_msg = "\n".join(
            module._verification_errors(True, [], [("line", anchored_row)], [])
        )
        hints = module._build_recovery_hints(error_msg)
        self.assertIn("手書き", hints)
        self.assertIn("security_evidence", hints)
        # (f): 再生成の明示 + writer 修正 2 点 + local 設定ファイルの enabled: false
        self.assertIn("method=", hints)
        self.assertIn("4 列", hints)
        self.assertIn(".claude/<plugin 名>.local.md", hints)
        self.assertIn("enabled: false", hints)
        # (f) 副作用 3 点
        self.assertIn("解除され", hints, "設定を置いただけでは block は解除されない旨が必要")
        self.assertIn("Stop ゲート", hints, "Snyk の Stop ゲート停止の副作用が必要")
        self.assertIn("verifier を再実行", hints, "writer 修正後の再実行手順が必要")

    def test_legacy_writer_hint_leaves_the_decision_to_a_human(self):
        # 独立レビュー R20 IR-2 / AC-20（2026-09-10 改訂）/ R12 (B3) SEC S-1・S-2:
        # 暫定回避は人間が判断して行う操作。fail / pending の行は削除も移動もしない。
        # writer 修正までは agent の正規手順では解除できないので停止して人間へ報告する。
        # 「こうすれば解除される」と読める括弧や開示文書への参照を置かない
        module = _hook_module()
        for row in (
            "- SECURITY-CODE | security_evidence:code | pending | - | -",
            "- SECURITY-CODE | security_evidence:code | fail | 3 high issues | x",
        ):
            with self.subTest(row=row):
                error_msg = "\n".join(module._verification_errors(True, [], [("line", row)], []))
                # impl-gate R15 M-1: legacy 行そのもののラベルも「書き直せ」と言わない
                # （下の案内の「手書きは契約違反 / 削除も移動もせず / 停止して報告」と矛盾させない）
                self.assertNotIn("canonical 表行へ書き直す", error_msg)
                self.assertIn("書き直さず", error_msg)
                hints = module._build_recovery_hints(error_msg)
                for phrase in (
                    "人間が判断して行う操作",
                    "agent は自分で設定しない",
                    "削除も移動もせず",
                    "残るのが legacy 形式の行だけなら",
                    '<gdd-stop reason="blocked">',
                    "人間へ報告",
                    "設定を戻し",
                ):
                    self.assertIn(phrase, hints)
                for phrase in (
                    "手で削除",
                    "解除しないでください",
                    "CHANGELOG",
                    "docs/adr",
                    "Known Limitations",
                    "唯一の回復手順",
                ):
                    self.assertNotIn(phrase, hints)

    def test_non_legacy_schema_violation_keeps_the_rewrite_instruction(self):
        # legacy 分岐でなければ「唯一の回復手順」は従来どおり出す。Notes ヒントが挙げる
        # 検証行の例は、既定ラベルと同じく「検証の結果・予定・未実施を書いた行」まで含む
        module = _hook_module()
        error_msg = "\n".join(
            module._verification_errors(True, [], [("line", "検証コマンド: pytest -q")], [])
        )
        hints = module._build_recovery_hints(error_msg)
        self.assertIn("唯一の回復手順", hints)
        self.assertIn("検証の結果・予定・未実施を書いた行", hints)

    def test_label_and_hint_use_the_same_legacy_detection(self):
        """impl-gate R16 advisory: 違反行ラベルと外部 writer 分岐の案内は、legacy 行かどうかを
        同じ文字列（無害化・80 文字切り詰め後の表示行）で判定する。制御文字を含む legacy 行で
        ラベルだけが「外部 writer の legacy 行 — …案内を参照」と言い、参照先の案内が出ない
        食い違いを作らない。散文中の言及には専用ラベルも案内も付かない。"""
        module = _hook_module()
        for row in (
            "- SECURITY-CODE | security_evidence:code | fail | scan\tfailed | x",
            "- SECURITY-CODE | security_evidence:code | fail | \x1b[31m3 high\x1b[0m | x",
            "- SECURITY-CODE | security_evidence:code | fail | 3 high issues | x",
            "- 補足: security_evidence: は外部 hook が書く",
        ):
            with self.subTest(row=row):
                error_msg = "\n".join(module._verification_errors(True, [], [("line", row)], []))
                hints = module._build_recovery_hints(error_msg)
                self.assertEqual(
                    "外部 writer の legacy 行" in error_msg,
                    "人間が判断して行う操作" in hints,
                    f"ラベルと案内の legacy 判定が食い違っています: {error_msg!r}",
                )
        prose = "- 補足: security_evidence: は外部 hook が書く"
        error_msg = "\n".join(module._verification_errors(True, [], [("line", prose)], []))
        self.assertNotIn("外部 writer の legacy 行", error_msg)

    def test_partial_mention_of_security_evidence_does_not_trigger_hint(self):
        """AC-20: 部分一致（散文中の言及）では発火しない（行頭アンカー必須）。"""
        module = _hook_module()
        prose_row = "- 補足: security_evidence: は外部 hook が書く"
        error_msg = "\n".join(module._verification_errors(True, [], [("line", prose_row)], []))
        hints = module._build_recovery_hints(error_msg)
        self.assertNotIn(
            ".claude/<plugin 名>.local.md",
            hints,
            "無関係な散文行で global 無効化の導線を出してはいけない（AC-20）",
        )

    # T-9（AC-9 第 5 形）で削除: 旧 `test_canonical_data_row_is_not_a_violation_and_does_not_trigger_hint`
    # は evidence 行を `verification_data_rows` として直接渡していたが、`_scan_verification` は
    # AC 行だけをそこへ数えるようになり、この入力は本番で起きない。AC 行へ差し替えると
    # `test_no_violations_and_no_unfinished_returns_empty_list` の複製になる。
    # 第 5 形の文言が外部 writer 分岐（AC-20）を誤発火させないことは
    # `test_verification_ac_row_required_contract.py` の `NoRowsMessageEnumeratesFifthFormTests` が、
    # canonical な evidence 行が違反にならないことは同 `AcRowRequiredBlocksTests` が固定する
    # （違反があれば判定順 2 が先に返り「検証行がありません」は出ないため）。


# ---------------------------------------------------------------------------
# design.md § 6 文言 pin (g): fence 違反 2 種の回復ヒント
# ---------------------------------------------------------------------------


class FenceViolationRecoveryHintTests(unittest.TestCase):
    def test_section_fence_hint_names_start_line_and_notes_escape(self):
        module = _hook_module()
        error_msg = "\n".join(
            module._verification_errors(True, [], [("section_fence", 12)], [])
        )
        # 0 始まり原文 index 12 は、メッセージ層で 1 始まり人間可読行番号 13 へ
        # 変換されて出力される（impl-gate R7 A20 / T-6 carry-in で実装済み）。
        self.assertIn("13", error_msg)
        hints = module._build_recovery_hints(error_msg)
        self.assertIn("## Verification Notes", hints)

    def test_fenced_heading_hint_says_moving_to_notes_does_not_resolve_it(self):
        module = _hook_module()
        error_msg = "\n".join(
            module._verification_errors(False, [], [("fenced_heading", 7)], [])
        )
        # 0 始まり原文 index 7 は 1 始まり人間可読行番号 8 へ変換されて出力される
        # （impl-gate R7 A20 / T-6 carry-in で実装済み）。
        self.assertIn("8", error_msg)
        hints = module._build_recovery_hints(error_msg)
        self.assertIn("解除されません", hints)
        self.assertIn("書き換え", hints, "fence 内の見出し行そのものを書き換える例が必要")


# ---------------------------------------------------------------------------
# fail-open 配線漏れの検出（★ Carry Forward 必須事項）
# ---------------------------------------------------------------------------


class ScanVerificationFailOpenWiringTests(unittest.TestCase):
    """`_scan_verification` の `fence_before` / `fenced_heading_lines` は
    keyword-only + 既定値 `None` を持つ（T-3 の単体テスト用）。production 呼び出しが
    これを明示しないと fence 違反が常に 0 件になる（design.md § 6 planning R8 advisory 1）。
    """

    def test_production_call_site_passes_both_fence_kwargs_explicitly(self):
        tree = ast.parse(HOOK_SRC, filename=str(HOOK_PATH))
        target_fn = None
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "validate_done_preconditions":
                target_fn = node
                break
        self.assertIsNotNone(target_fn, "validate_done_preconditions が見つからない")

        calls = [
            n
            for n in ast.walk(target_fn)
            if isinstance(n, ast.Call)
            and isinstance(n.func, ast.Name)
            and n.func.id == "_scan_verification"
        ]
        # 陽性対照: 呼び出し自体が消えていないこと（vacuous pass 防止）
        self.assertEqual(len(calls), 1, f"_scan_verification 呼び出しが 1 件のはず: {len(calls)} 件")

        kwarg_names = {kw.arg for kw in calls[0].keywords if kw.arg is not None}
        missing = {"fence_before", "fenced_heading_lines"} - kwarg_names
        self.assertEqual(
            missing,
            set(),
            f"production 呼び出しが fence 引数を明示していない（fail-open）: 渡された keyword={kwarg_names!r}",
        )


class EndToEndFencedHeadingFailOpenTests(unittest.TestCase):
    """節見出し自体が fence に飲まれていても、他に canonical な `## Verification` 節が
    あるだけで done が通ってしまう fail-open（design.md § 5「fence が見出しごと飲む」行）
    を、実際の `validate_done_preconditions` 経由で再現する。配線（Step 1）とメッセージ
    整形（Step 2）の両方が揃って初めて block されることを pin する E2E RED。
    """

    def test_end_to_end_fenced_heading_swallow_still_blocks_when_wired_correctly(self):
        module = _hook_module()
        tasklist_body = (
            "# Tasklist\n\n"
            "## Current Task\n- なし\n\n"
            "## Pending Tasks\n- なし\n\n"
            "## Completed Tasks\n- T1 | AC-01 | done\n\n"
            "## Verification Notes\n"
            "記入例:\n"
            "```\n"
            "## Verification\n"
            "| method | status | evidence | notes |\n"
            "|---|---|---|---|\n"
            "| method=ac:AC-1 | pass | 例 | - |\n"
            "```\n\n"
            "## Verification\n"
            "| method | status | evidence | notes |\n"
            "|---|---|---|---|\n"
            "| method=ac:AC-1 | pass | npm test 通過 | - |\n\n"
            "## Status\nNext Action=done\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            wt = Path(tmp) / "wt"
            wt.mkdir()
            subprocess.run(["git", "init", "-q", str(wt)], check=True)
            d = wt / ".steering" / "20260101-mine"
            d.mkdir(parents=True)
            (d / "tasklist.md").write_text(tasklist_body, encoding="utf-8")
            module._BIND_CACHE.clear()
            try:
                is_valid, err, _checked = module.validate_done_preconditions(wt)
            finally:
                module._BIND_CACHE.clear()
        self.assertFalse(
            is_valid,
            "fence に飲まれた ## Verification 見出しは、外に canonical 節が残っていても "
            "block しなければならない（fail-open の再現）",
        )
        self.assertIn("見出し", err)


# ---------------------------------------------------------------------------
# Step 4: dead code（"[status 判別不能]" 分岐）削除の pin
# ---------------------------------------------------------------------------


class LegacyWriterBeyondDisplayLimitTests(unittest.TestCase):
    """独立レビュー R23 #2 / D-14: legacy 行が違反の 6 件目以降でも外部 writer 分岐を出す。

    違反行の表示は先頭 5 件だけなので、表示行だけで legacy 行を判定すると 6 件目以降の
    legacy 行で専用の案内が消え「唯一の回復手順」が出ていた（AC-20）。
    """

    _LEGACY = "- SECURITY-CODE | security_evidence:code | fail | tool=x | updated"

    def _hints(self, raw_lines: list[str]) -> tuple[str, str]:
        module = _hook_module()
        error_msg = "\n".join(
            module._verification_errors(True, [], [("line", r) for r in raw_lines], [])
        )
        return error_msg, module._build_recovery_hints(error_msg)

    def test_legacy_row_after_five_violations_still_gets_writer_guidance(self):
        error_msg, hints = self._hints([f"散文 {i}" for i in range(6)] + [self._LEGACY])
        self.assertNotIn("SECURITY-CODE", error_msg)  # 表示の先頭 5 件には入らない
        self.assertIn("外部 writer の legacy 行が 1 件", error_msg)
        self.assertIn("外部 security evidence 行 →", hints)
        self.assertIn('<gdd-stop reason="blocked">', hints)
        self.assertNotIn("唯一の回復手順", hints)

    def test_legacy_row_within_display_limit_is_counted_once(self):
        error_msg, hints = self._hints([self._LEGACY, "散文 0"])
        self.assertIn("外部 writer の legacy 行が 1 件", error_msg)
        self.assertIn("外部 security evidence 行 →", hints)
        self.assertNotIn("唯一の回復手順", hints)

    def test_violation_text_resembling_headline_does_not_trigger_writer_guidance(self):
        # impl-gate R21 M-2: 見出しの判定は行頭一致。違反行の本文に見出しと同じ文言があっても
        # （違反行は字下げして表示される）外部 writer 分岐（Snyk の暫定回避の提示を含む）を出さない
        error_msg, hints = self._hints(["外部 writer の legacy 行が 9 件あります"])
        self.assertNotIn("外部 security evidence 行 →", hints)
        self.assertIn("唯一の回復手順", hints)

    def test_no_legacy_row_emits_no_headline(self):
        error_msg, hints = self._hints([f"散文 {i}" for i in range(7)])
        self.assertNotIn("外部 writer の legacy 行が", error_msg)
        self.assertNotIn("外部 security evidence 行 →", hints)
        self.assertIn("唯一の回復手順", hints)


class LineBreakHeadlineAnchorTests(unittest.TestCase):
    """impl-gate R22 M-1: 行区切り文字の案内は hook の見出し行への行頭一致で出す。

    違反行は字下げして表示されるので、違反行の本文に見出しと同じ文言があっても案内を出さず、
    「唯一の回復手順」も抑止しない。
    """

    def test_violation_text_resembling_line_break_headline_is_ignored(self):
        module = _hook_module()
        error_msg = "\n".join(
            module._verification_errors(
                True, [], [("line", "tasklist.md に LF / CR 以外の行区切り文字（U+2028）が含まれています")], []
            )
        )
        hints = module._build_recovery_hints(error_msg)
        self.assertNotIn("行区切り文字 →", hints)
        self.assertIn("唯一の回復手順", hints)


class SoleInstructionSuppressionIsTasklistOnlyTests(unittest.TestCase):
    """Issue #119 / D-28: 行区切り文字の案内は tasklist.md と state.md の両方の見出しで出す。
    「唯一の回復手順」の抑止は **tasklist.md** の見出しだけを根拠にする。

    抑止の理屈は「区切り文字で割れた断片が schema 違反になっているだけなので、解除手順は
    文字の削除」で、tasklist.md にその文字がある場合にしか成り立たない。state.md の見出しでも
    抑止すると、「state.md に U+2028 / tasklist.md には本物の schema 違反」の複合ケースで
    正しい回復手順が黙って消える。
    """

    _SOLE = "canonical 表行への書き直しが唯一の回復手順です。"

    def _hints(self, line_break_filename: str | None) -> str:
        module = _hook_module()
        parts: list[str] = []
        if line_break_filename is not None:
            # 行区切り理由は実装の生成関数から取る（文言を test 側にハードコードしない）
            parts.append(module._line_break_char_error("x\u2028y\n", line_break_filename))
        parts.extend(module._verification_errors(True, [], [("line", "## 散文の見出し")], []))
        error_msg = "\n".join(parts)
        self.assertIn("schema 違反行が", error_msg)
        return module._build_recovery_hints(error_msg)

    def test_state_md_line_break_emits_hint_and_keeps_the_sole_rewrite_instruction(self):
        hints = self._hints("state.md")
        self.assertIn("行区切り文字 →", hints)
        self.assertIn("state.md", hints)
        self.assertIn(self._SOLE, hints)

    def test_tasklist_md_line_break_still_suppresses_the_sole_rewrite_instruction(self):
        hints = self._hints("tasklist.md")
        self.assertIn("行区切り文字 →", hints)
        self.assertNotIn(self._SOLE, hints)

    def test_baseline_without_line_break_keeps_the_sole_rewrite_instruction(self):
        hints = self._hints(None)
        self.assertNotIn("行区切り文字 →", hints)
        self.assertIn(self._SOLE, hints)

    def test_violation_text_resembling_state_md_headline_is_ignored(self):
        # 行頭一致の対称性: state.md 側の見出しに似た違反行でも案内を出さない
        module = _hook_module()
        error_msg = "\n".join(
            module._verification_errors(
                True, [], [("line", "state.md に LF / CR 以外の行区切り文字（U+2028）が含まれています")], []
            )
        )
        hints = module._build_recovery_hints(error_msg)
        self.assertNotIn("行区切り文字 →", hints)
        self.assertIn(self._SOLE, hints)


if __name__ == "__main__":
    unittest.main()
