"""done guard Check 2 は AC 検証行（`method=ac:`）を 1 件以上要求する（AC-9 第 5 形、T-9）。

実行:
  python3 -m pytest plugins/gate-driven-development/tests/test_verification_ac_row_required_contract.py -v

AC-9 の「検証行がありません」で block する形に、第 5 形として **data 行はあるが `method=ac:`
行が 0 件（`security_evidence` 行・`refactor-checkpoint` 行だけの表）** を加えた。
変更前は `_scan_verification` が method 種別を捨てて全 data 行を `verification_data_rows`
に数えていたため、AC を 1 件も検証していない節でも done が通っていた。

本ファイルが固定すること（設計: B2 追補 § 1.5 の #1〜#8）:
- #1〜#3c: AC 検証行 0 件の節は「検証行がありません」で block される
- #4 / #4b: 第 5 形に未完了/失敗行があれば件数を**併記**し（握りつぶさない）、併記行は
  `safe_for_output()` を通す（制御文字で block 理由を隠させない）
- #4c: 第 5 形 + 未完了では「散文は Notes へ移して」導線を出さず、AC 検証行を足す案内を出す
  （security scan の fail 行を Notes へ逃がす誤誘導を作らない）。違反と未完了が並ぶ判定順 2 では
  従来どおり Notes 導線を出し、AC 検証行の案内は出さない
- #5 / #6: AC 行がある場合の既存挙動（回帰防止）
- #7: 「検証行がありません」本文が第 5 形を列挙し、外部 writer 分岐（AC-20）を誤発火させない
- #8: `_scan_verification` は AC 行だけを `verification_data_rows` に数え、`unfinished` は
  method 種別に依らず数える

Contract Surface Coverage（T-9 スコープ = Check 2 の受理と block メッセージ。外部 API 呼び出しなし）:
- success path: applicable -> `AcRowPresentRegressionTests.test_ac_pass_with_evidence_pass_allows`
- no-op / silent success path: not_applicable（AC 行 0 件は block になり、黙って通る経路を消すのが本変更）
- external API response variants: not_applicable（外部 API を呼ばない）
- external API failure / unavailable path: not_applicable（同上）
- validation / sanitize / fail-closed path: applicable -> `AcRowRequiredBlocksTests` /
  `OriginalAllowFixtureNowBlocksTests` / `UnfinishedAlongsideNoAcRowsTests.test_unfinished_row_with_escape_is_sanitized`
- formatting / output schema path: applicable -> `NoRowsMessageEnumeratesFifthFormTests` /
  `NoAcRowsRecoveryHintTests`
- duplicate / idempotency / lock path: not_applicable（状態を持たない判定）
- user-visible side effect path: applicable -> hook 実起動（`_run_verification`）の block payload
"""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

# `python3 -m unittest tests.<module>` でも共有ヘルパを解決できるようにする（共通規約 13）
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "hooks" / "scripts"))

from _plugin_module_loader import load_plugin_module  # noqa: E402
from _stop_hook_test_base import _bind, _stop_done, _write_steering  # noqa: E402
from lib import done_block_message  # noqa: E402
from lib import done_guard as guard  # noqa: E402

_SLUG = "20260910-ac-row-required"

_AC_PASS = "| method=ac:AC-1 | pass | pytest 通過 | - |"
_EVIDENCE_PASS = "| method=security_evidence:sca | pass | snyk 0 | - |"
_EVIDENCE_PENDING = "| method=security_evidence:sca | pending | - | 未実施 |"
_EVIDENCE_FAIL = "| method=security_evidence:code | fail | snyk 2 issues | - |"
_REFACTOR_PASS = "| method=refactor-checkpoint | pass | log | - |"

# 本文に足す第 5 形の列挙文（#7 が pin する）
_FIFTH_FORM_PHRASE = "`security_evidence` 行・`refactor-checkpoint` 行だけの表（AC 検証行 `method=ac:` が 0 件）"
# 回復ヒント（`lib/done_block_message.py`）
_NOTES_HINT = "散文・凡例・補助表 → `## Verification Notes` へ移して"
_AC_ROW_HINT = "AC 検証行なし → `method=ac:"


def _tasklist(verification_body: str) -> str:
    """他は clean で `## Verification` 本文だけを変えた単一 steering 用 tasklist。"""
    return (
        "# Tasklist\n\n"
        "## Current Task\n- なし\n\n"
        "## Pending Tasks\n- なし\n\n"
        "## Completed Tasks\n- T1 | AC-01 | done\n\n"
        "## Verification\n"
        f"{verification_body}\n\n"
        "## Status\nNext Action=done\n"
    )


def _run_verification(verification_body: str) -> tuple[int, str, str]:
    """bind 済みの単一 steering で stop hook を実起動する（allow 経路で warn が混ざらないように bind する）。"""
    with tempfile.TemporaryDirectory() as tmp:
        ws = Path(tmp)
        _write_steering(ws, _SLUG, _tasklist(verification_body))
        _bind(ws, _SLUG)
        return _stop_done(ws)


def _hook_module():
    return load_plugin_module("hooks/scripts/gdd_stop_hook.py")


def _lines(verification_body: str) -> list[str]:
    return ("## Verification\n" + verification_body).splitlines()


class _BlockAssertions(unittest.TestCase):
    def _block_reason(self, verification_body: str) -> str:
        code, out, err = _run_verification(verification_body)
        self.assertNotEqual(
            out.strip(), "", f"allow になっている（AC 検証行 0 件で done が通る）: err={err}"
        )
        payload = json.loads(out.strip())
        self.assertEqual(payload["decision"], "block", f"out={out}\nerr={err}")
        return payload["reason"]


class AcRowRequiredBlocksTests(_BlockAssertions):
    """#1〜#3: `method=ac:` 行が無い節は、他の data 行があっても「検証行がありません」で block。"""

    def test_security_evidence_pass_only_blocks(self):
        self.assertIn("検証行がありません", self._block_reason(_EVIDENCE_PASS))

    def test_refactor_checkpoint_pass_only_blocks(self):
        self.assertIn("検証行がありません", self._block_reason(_REFACTOR_PASS))

    def test_security_evidence_na_table_blocks(self):
        # 旧 `_ALLOW_CASES` の `method_prefixed_security_evidence_na` の入力そのまま
        body = (
            "| method | status | evidence | notes |\n"
            "|---|---|---|---|\n"
            "| method=security_evidence:sca | N/A | | dependencies 変更なし |"
        )
        self.assertIn("検証行がありません", self._block_reason(body))


class OriginalAllowFixtureNowBlocksTests(_BlockAssertions):
    """#3a〜#3c: 旧 `_ALLOW_CASES` の入力（evidence 行のみ）は block へ反転した。

    regression 側の同名 case は canonical AC 行を 1 行足して「セル内の AC 参照は判定対象外」
    という本来の性質を pin し続ける。元の入力の反転はここで固定する。セル内に `AC-` や
    `method=ac:` の文字列があっても AC 行として数えないこと（行全体への正規表現で数える
    誤実装の検出）も併せて固定する。
    """

    def test_ac_reference_in_notes_cell_is_not_an_ac_row(self):
        body = (
            "| method | status | evidence | notes |\n"
            "|---|---|---|---|\n"
            "| method=security_evidence:sca | N/A | snyk 0 | AC-3 は依存追加なしのため対象外 |"
        )
        self.assertIn("検証行がありません", self._block_reason(body))

    def test_ac_reference_in_evidence_cell_is_not_an_ac_row(self):
        body = (
            "| method | status | evidence | notes |\n"
            "|---|---|---|---|\n"
            "| method=security_evidence:sca | N/A | AC-2 に関連する依存なし | |"
        )
        self.assertIn("検証行がありません", self._block_reason(body))

    def test_method_ac_literal_in_notes_cell_is_not_an_ac_row(self):
        body = "| method=security_evidence:sca | pass | ok | method=ac:AC-1 |"
        self.assertIn("検証行がありません", self._block_reason(body))


class UnfinishedAlongsideNoAcRowsTests(_BlockAssertions):
    """#4 / #4b: 第 5 形に未完了/失敗行があれば「検証行がありません」と件数を併記する。"""

    def test_pending_evidence_only_reports_both(self):
        reason = self._block_reason(_EVIDENCE_PENDING)
        self.assertIn("検証行がありません", reason)
        self.assertIn("未完了/失敗が 1 件", reason)

    def test_two_unfinished_rows_are_both_reported(self):
        # 併記の件数と本文を切り詰めない（先頭 1 行だけを併記する誤実装を検出する）
        second = "| method=security_evidence:code | pending | - | 未実施 |"
        reason = self._block_reason(_EVIDENCE_PENDING + "\n" + second)
        self.assertIn("検証行がありません", reason)
        self.assertIn("未完了/失敗が 2 件", reason)
        self.assertIn(_EVIDENCE_PENDING, reason)
        self.assertIn(second, reason)

    def test_unfinished_row_with_escape_is_sanitized(self):
        body = "| method=security_evidence:sca | pending | \x1b[2K\x1b[1Gforged | 未実施 |"
        reason = self._block_reason(body)
        self.assertIn("検証行がありません", reason)
        self.assertIn("(invalid: control characters)", reason)
        self.assertNotIn("\x1b", reason)


class NoAcRowsRecoveryHintTests(_BlockAssertions):
    """#4c: 第 5 形 + 未完了では Notes 導線を出さず、AC 検証行を足す案内を出す。

    #4d（PR #65 review）: AC 検証行 0 件なら未完了の有無にかかわらず AC 行の追加を案内し、
    「唯一の回復手順」は schema 違反のときだけ出す。
    """

    def test_failed_evidence_only_does_not_suggest_moving_to_notes(self):
        reason = self._block_reason(_EVIDENCE_FAIL)
        self.assertNotIn(_NOTES_HINT, reason)
        self.assertIn(_AC_ROW_HINT, reason)
        self.assertIn("移してはいけません", reason)

    def test_schema_violation_with_unfinished_keeps_notes_hint(self):
        # 違反（散文行）と未完了が並ぶとき（判定順 2）は従来どおり Notes 導線を出し、
        # 「AC 検証行なし」は出さない。ヒント条件の前半（"schema 違反行が" in msg）を守る。
        # これが無いと、条件を「未完了なら AC 行ヒント」へ単純化する誤ったリファクタで、
        # AC 行があるのに「AC 検証行なし」と案内し散文の逃がし先（AC-6）が消えても検出できない
        reason = self._block_reason("| method=ac:AC-1 | pending | - | 未実施 |\n検証コマンド: pytest -q")
        self.assertIn(_NOTES_HINT, reason)
        self.assertNotIn(_AC_ROW_HINT, reason)

    def test_pass_only_fifth_form_suggests_adding_ac_row(self):
        # PR #65 review（2026-09-11）: 既存行がすべて canonical な pass 行でも AC 検証行が 0 件なら
        # 解除条件は `method=ac:` 行の追加だけ。「書き直しが唯一の回復手順」は解除条件と矛盾する
        reason = self._block_reason(_EVIDENCE_PASS + "\n" + _REFACTOR_PASS)
        self.assertIn(_AC_ROW_HINT, reason)
        self.assertNotIn("唯一の回復手順", reason)

    def test_empty_forms_suggest_adding_ac_row_and_keep_notes_escape(self):
        # 空節 4 形も AC 検証行 0 件。AC 行の追加を案内し、散文の逃がし先（AC-6）は残し、
        # 「唯一の回復手順」は出さない（本文は第 5 形と同じ文面なのでヒント側で見分けない）
        for name, body in (
            ("empty", ""),
            ("nashi", "- なし"),
            ("header_only", "| method | status | evidence | notes |"),
            ("header_separator", "| method | status | evidence | notes |\n|---|---|---|---|"),
        ):
            with self.subTest(form=name):
                reason = self._block_reason(body)
                self.assertIn("検証行がありません", reason)
                self.assertIn(_AC_ROW_HINT, reason)
                self.assertIn(_NOTES_HINT, reason)
                self.assertNotIn("唯一の回復手順", reason)

    def test_schema_violation_without_ac_rows_keeps_rewrite_instruction(self):
        # 散文 1 行だけの節は AC 検証行 0 件だが判定順 2（schema 違反）が先に返る。
        # ここで AC 行の案内を出したり「唯一の回復手順」を落としたりしない
        # （AC 行 0 件の判定をヒント側で取り違える退行を検出する）
        reason = self._block_reason("検証コマンド: pytest -q")
        self.assertIn("schema 違反行が", reason)
        self.assertIn("唯一の回復手順", reason)
        self.assertNotIn(_AC_ROW_HINT, reason)

    def test_user_text_saying_no_rows_does_not_switch_schema_violation_hint(self):
        # impl-gate R17 low 1: 違反行・未完了行の本文は block 理由に載る。利用者の行に
        # 「検証行がありません」と書かれていても、AC 行がある schema 違反を AC 行 0 件と
        # 取り違えない（Notes 逃がし先を残し、「AC 検証行なし」を出さない）
        reason = self._block_reason(
            "| method=ac:AC-1 | pending | - | 検証行がありません |\n検証コマンド: pytest -q"
        )
        self.assertIn("schema 違反行が", reason)
        self.assertIn(_NOTES_HINT, reason)
        self.assertNotIn(_AC_ROW_HINT, reason)

    def test_user_text_saying_schema_violation_does_not_restore_notes_hint(self):
        # impl-gate R17 security A-1: 第 5 形 + fail の行本文に「schema 違反行が」と書いても、
        # security scan の fail 行を Notes へ逃がす導線（AC-9）を復活させない
        reason = self._block_reason(
            "| method=security_evidence:code | fail | snyk 2 issues | schema 違反行が |"
        )
        self.assertIn("検証行がありません", reason)
        self.assertNotIn(_NOTES_HINT, reason)
        self.assertIn(_AC_ROW_HINT, reason)

    def test_user_text_saying_no_rows_in_unfinished_only_adds_no_shape_hints(self):
        # impl-gate R18 A-1: AC 行があり未完了行だけの節で、未完了行の本文に「検証行がありません」と
        # 書かれていても、schema 違反 / AC 行 0 件向けのヒント一式（canonical 形・Notes 導線・AC 行追加）を
        # 出さない。`_build_recovery_hints` の入口条件だけを短い語（`検証行がありません`）の部分一致へ
        # 戻す退行を検出する。`_NOTES_HINT` は他のテストが正で pin しているので、文言が変わっても
        # この否定 assert は空振りしない（impl-gate R19 A-1）
        reason = self._block_reason("| method=ac:AC-1 | pending | - | 検証行がありません |")
        self.assertIn("未完了/失敗が 1 件", reason)
        self.assertNotIn("canonical 形 →", reason)
        self.assertNotIn(_NOTES_HINT, reason)
        self.assertNotIn(_AC_ROW_HINT, reason)


class AcRowPresentRegressionTests(_BlockAssertions):
    """#5 / #6: AC 行がある場合の既存挙動。"""

    def test_ac_pass_with_evidence_pass_allows(self):
        code, out, err = _run_verification(_AC_PASS + "\n" + _EVIDENCE_PASS)
        self.assertEqual(out.strip(), "", f"out={out}\nerr={err}")
        self.assertEqual(code, 0, f"out={out}\nerr={err}")

    def test_ac_pass_with_evidence_pending_blocks_as_unfinished(self):
        # unfinished を AC 行に限定する誤実装を検出する
        reason = self._block_reason(_AC_PASS + "\n" + _EVIDENCE_PENDING)
        self.assertIn("未完了/失敗が 1 件", reason)
        self.assertNotIn("検証行がありません", reason)


class NoRowsMessageEnumeratesFifthFormTests(unittest.TestCase):
    """#7: `_verification_errors()` の戻り値を直接見る。

    hook 実起動の reason は回復ヒントを連結しており、ヒントが既に `security_evidence` /
    `refactor-checkpoint` の語を含むため、reason で語の有無を見ると実装前から緑になる。
    """

    def test_no_rows_message_lists_fifth_form(self):
        module = _hook_module()
        message = "\n".join(module._verification_errors(*guard._scan_verification(_lines(_EVIDENCE_PASS))))
        self.assertIn("検証行がありません", message)
        self.assertIn(_FIFTH_FORM_PHRASE, message)
        # 第 5 形の文言が外部 writer 分岐（Snyk の global 無効化案内）を誤発火させない
        self.assertFalse(done_block_message._has_legacy_security_evidence_writer_shape(message))


class ScanVerificationCountsOnlyAcRowsTests(unittest.TestCase):
    """#8: `verification_data_rows` は AC 行だけ、`unfinished` は method 種別に依らない。"""

    def test_non_ac_rows_are_not_counted_as_verification_rows(self):
        for name, body in (
            ("evidence_pass", _EVIDENCE_PASS),
            ("refactor_pass", _REFACTOR_PASS),
            ("method_ac_literal_in_notes", "| method=security_evidence:sca | pass | ok | method=ac:AC-1 |"),
        ):
            with self.subTest(case=name):
                found, rows, violations, unfinished = guard._scan_verification(_lines(body))
                self.assertTrue(found)
                self.assertEqual(violations, [])
                self.assertEqual(rows, [])
                self.assertEqual(unfinished, [])

    def test_unfinished_counts_non_ac_rows(self):
        _found, rows, _violations, unfinished = guard._scan_verification(_lines(_EVIDENCE_PENDING))
        self.assertEqual(rows, [])
        self.assertEqual(unfinished, [_EVIDENCE_PENDING])

    def test_ac_rows_are_counted(self):
        _found, rows, _violations, _unfinished = guard._scan_verification(
            _lines(_AC_PASS + "\n" + _EVIDENCE_PASS)
        )
        self.assertEqual(rows, [_AC_PASS])


if __name__ == "__main__":
    unittest.main()
