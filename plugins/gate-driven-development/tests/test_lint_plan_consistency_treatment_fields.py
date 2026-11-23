"""lint-plan-consistency.py の、reviews.md の最新 Round の `処置:` の欄の検査。

planning reviewer の再入（Round 2）で出る blocking の多くは、Round 1 の処置で
新しく生まれたもの（処置の文が確かめていない事実に当たった・直した事実が他の節に
伝わっていない）だった。処置の 1 件ごとに `根拠:` と `伝播:` の欄を書かせ、
reviewer を起動する前に欄の有無だけを確かめる（中身は解析しない）。
再入かどうかは gate が `--entry` で宣言する（reviews.md の判定の行からは推さない）。
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _paths import PLUGIN_ROOT  # noqa: E402

SCRIPT = PLUGIN_ROOT / "scripts" / "lint-plan-consistency.py"

REQUIREMENTS_OK = """\
# requirements

## Summary Brief
AC-1 を満たす。

### 承認ポイント
1. **方向性**: 承認

## 受入条件
- AC-1: reviewer は 30 分で返る / 根拠: src/app.py:12 / 計測: 所要時間、30 分以内
"""

ROUND1_HEAD = """\
# Reviews

## Round 1（2026-10-27 / reviewer: gdd-planning-reviewer / 所要: 20 分・呼び出し 50 回）
- 判定: changes_requested
- blocking:
  - B1（High・AC の意味）: AC-1 の母集団が無い
- advisory: なし
"""

GOOD_ITEM = "  - B1: AC-1 に母集団を書いた / 根拠: src/app.py:12 / 伝播: 母集団 → Summary Brief・design.md の主要フロー\n"


def run(steering: Path, entry: str | None = "requirements-reentry") -> subprocess.CompletedProcess[str]:
    extra = ["--entry", entry] if entry else []
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--steering-dir", str(steering), *extra],
        capture_output=True,
        text=True,
    )


class TreatmentFieldsTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)
        (self.dir / "requirements.md").write_text(REQUIREMENTS_OK, encoding="utf-8")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def reviews(self, text: str | bytes) -> None:
        path = self.dir / "reviews.md"
        if isinstance(text, bytes):
            path.write_bytes(text)
        else:
            path.write_text(text, encoding="utf-8")

    def assert_ok(self, result: subprocess.CompletedProcess[str]) -> None:
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn("ERROR", result.stdout)
        self.assertNotIn("Traceback", result.stderr)

    def assert_error(self, result: subprocess.CompletedProcess[str], *needles: str) -> None:
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        for needle in needles:
            self.assertIn(needle, result.stdout)

    def test_items_with_both_fields_pass(self) -> None:
        self.reviews(ROUND1_HEAD + "- 処置:\n" + GOOD_ITEM)
        self.assert_ok(run(self.dir))

    def test_item_without_evidence_is_error(self) -> None:
        # block すべき入力: 処置の文の事実を確かめた場所が無い
        self.reviews(ROUND1_HEAD + "- 処置:\n  - B1: AC-1 に母集団を書いた / 伝播: なし\n")
        self.assert_error(run(self.dir), "reviews.md", "根拠:", "B1")

    def test_item_without_propagation_is_error(self) -> None:
        self.reviews(ROUND1_HEAD + "- 処置:\n  - B1: AC-1 に母集団を書いた / 根拠: src/app.py:12\n")
        self.assert_error(run(self.dir), "伝播:", "B1")

    def test_each_item_is_checked(self) -> None:
        self.reviews(ROUND1_HEAD + "- 処置:\n" + GOOD_ITEM + "  - B2: 非スコープを直した\n")
        result = run(self.dir)
        self.assert_error(result, "B2")
        self.assertNotIn("B1:", result.stdout)

    def test_unmeasured_and_none_values_pass(self) -> None:
        self.reviews(ROUND1_HEAD + "- 処置:\n  - B1: 直した / 根拠: 未測（本番の env は読めない） / 伝播: なし\n")
        self.assert_ok(run(self.dir))

    def test_full_width_colon_passes(self) -> None:
        self.reviews(ROUND1_HEAD + "- 処置：\n  - B1: 直した / 根拠：src/app.py:12 / 伝播：なし\n")
        self.assert_ok(run(self.dir))

    def test_field_name_inside_other_words_is_not_a_field(self) -> None:
        # block すべき入力: 欄名の部分一致で欄があるとみなさない（AC の欄と同じ判定）
        for item in (
            "  - B1: 直した（判断根拠: 小さい） / 伝播: なし\n",
            "  - B1: `根拠:` を足した / 伝播: なし\n",
        ):
            with self.subTest(item=item):
                self.reviews(ROUND1_HEAD + "- 処置:\n" + item)
                self.assert_error(run(self.dir), "根拠:", "B1")

    def test_continuation_line_is_error(self) -> None:
        # 1 件 1 行。深い字下げの行を前の項目の続きにすると、別の処置が前の項目の欄で通る
        self.reviews(ROUND1_HEAD + "- 処置:\n" + GOOD_ITEM + "    ・B2: 非スコープを直した\n")
        self.assert_error(run(self.dir), "B2")

    def test_numbered_items_are_checked(self) -> None:
        self.reviews(ROUND1_HEAD + "- 処置:\n  1. AC-1 を直した / 根拠: src/app.py:12 / 伝播: なし\n  2. 非スコープを直した\n")
        self.assert_error(run(self.dir), "非スコープを直した")

    def test_items_not_in_item_shape_are_error(self) -> None:
        for line in ("  ・B2: 非スコープを直した", "  + B2: 非スコープを直した", "  B2: 非スコープを直した", "  1）B2: 非スコープを直した"):
            with self.subTest(line=line):
                self.reviews(ROUND1_HEAD + "- 処置:\n" + GOOD_ITEM + line + "\n")
                self.assert_error(run(self.dir), "B2")

    def test_inline_treatment_is_one_item(self) -> None:
        self.reviews(ROUND1_HEAD + "- 処置: B1 を直した\n")
        self.assert_error(run(self.dir), "B1 を直した")

    def test_header_with_note_is_checked(self) -> None:
        for header in ("- 処置（main の採否に従う）:", "- 処置 (main の採否に従う):"):
            with self.subTest(header=header):
                self.reviews(ROUND1_HEAD + header + "\n  - B1: 直した\n")
                self.assert_error(run(self.dir), "B1")

    def test_header_variants_are_error(self) -> None:
        # 見出しの揺れを素通りさせない（実データにある形）
        for header in ("- **処置**:", "-処置:", "* 処置:", "  - 処置:", "### 処置", "処置:", "- 処置確認:", "- 処置案（未反映）:"):
            with self.subTest(header=header):
                self.reviews(ROUND1_HEAD + header + "\n" + GOOD_ITEM)
                self.assert_error(run(self.dir), "処置")

    def test_reentry_without_treatment_is_error(self) -> None:
        self.reviews(ROUND1_HEAD)
        self.assert_error(run(self.dir), "処置")

    def test_treatment_in_separate_h2_section_is_error(self) -> None:
        self.reviews(ROUND1_HEAD + "\n## 処置（Round 1）\n- 処置:\n" + GOOD_ITEM)
        self.assert_error(run(self.dir), "処置")

    def test_empty_treatment_is_error(self) -> None:
        self.reviews(ROUND1_HEAD + "- 処置:\n\n## メモ\n")
        self.assert_error(run(self.dir), "処置")

    def test_only_latest_round_is_checked(self) -> None:
        # 前の Round（この版より前の形の処置）は直させない
        text = (
            ROUND1_HEAD
            + "- 処置:\n  - B1: 直した\n\n"
            + "## Round 2（2026-10-27 / reviewer: gdd-planning-reviewer / 所要: 10 分・呼び出し 30 回）\n"
            + "- 判定: changes_requested\n- blocking:\n  - B2: 伝播漏れ\n- advisory: なし\n- 処置:\n"
            + GOOD_ITEM.replace("B1", "B2")
        )
        self.reviews(text)
        self.assert_ok(run(self.dir))

    def test_verdict_line_is_not_needed(self) -> None:
        # 判定の行は読まない（`- **判定**:` でも、無くても検査する）
        self.reviews("## Round 1（2026-10-27）\n- **判定**: changes_requested\n- 処置:\n  - B1: 直した\n")
        self.assert_error(run(self.dir), "B1")

    def test_treatment_inside_unclosed_fence_is_still_checked(self) -> None:
        self.reviews(ROUND1_HEAD + "```\n- 処置:\n  - B1: 直した\n")
        self.assert_error(run(self.dir), "B1")

    def test_unindented_item_after_treatment_is_error(self) -> None:
        # 処置は Round の最後の塊。見出しの後ろに字下げなしで書いた処置を素通りさせない
        self.reviews(ROUND1_HEAD + "- 処置:\n" + GOOD_ITEM + "- B2: 非スコープを直した\n")
        self.assert_error(run(self.dir), "B2")

    def test_note_after_treatment_is_error(self) -> None:
        self.reviews(ROUND1_HEAD + "- 処置:\n" + GOOD_ITEM + "- 備考: 承認ポイントは変えていない\n")
        self.assert_error(run(self.dir), "備考")

    def test_h2_section_after_treatment_is_error(self) -> None:
        self.reviews(ROUND1_HEAD + "- 処置:\n" + GOOD_ITEM + "\n## 処置（追記）\n- B2: 直した\n")
        self.assert_error(run(self.dir), "B2")

    def test_fence_after_treatment_is_error(self) -> None:
        self.reviews(ROUND1_HEAD + "- 処置:\n" + GOOD_ITEM + "  ```\n  - B2: 直した\n  ```\n")
        self.assert_error(run(self.dir), "```")

    def test_second_treatment_header_with_items_passes(self) -> None:
        self.reviews(ROUND1_HEAD + "- 処置:\n" + GOOD_ITEM + "- 処置（追記）:\n" + GOOD_ITEM.replace("B1", "B2"))
        self.assert_ok(run(self.dir))

    def test_design_entry_does_not_check_treatments(self) -> None:
        # design の起動は処置を見ない（前の gate の最後の Round で止めない）
        self.reviews(ROUND1_HEAD + "- 処置: B3 は accepted-as-known-risk\n")
        result = run(self.dir, entry="design")
        self.assert_ok(result)
        self.assertNotIn("WARN", result.stdout)

    def test_missing_entry_with_rounds_is_usage_error(self) -> None:
        # 判定できないときに通さない（宣言の付け忘れは止める）
        self.reviews(ROUND1_HEAD + "- 処置:\n" + GOOD_ITEM)
        result = run(self.dir, entry=None)
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("--entry", result.stderr)

    def test_missing_entry_without_rounds_is_usage_error(self) -> None:
        # Round が無くても --entry は要る（requirements の初回で AC の欄の検査が抜けない）
        for reviews in (None, "# Reviews\n"):
            with self.subTest(reviews=reviews):
                if reviews is not None:
                    self.reviews(reviews)
                result = run(self.dir, entry=None)
                self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                self.assertIn("--entry", result.stderr)

    def test_missing_reviews_md_on_reentry_is_error(self) -> None:
        self.assert_error(run(self.dir), "reviews.md")

    def test_undecodable_bytes_do_not_crash(self) -> None:
        # 例外で検査全体が落ちない
        self.reviews(ROUND1_HEAD.encode("utf-8") + b"- \xe5\x87\xa6\xe7\xbd\xae:\n  - B1: \xff\n")
        self.assert_error(run(self.dir), "B1")

    def test_reviews_md_that_is_a_directory_is_not_passed(self) -> None:
        # 読めないときは通さない
        (self.dir / "reviews.md").mkdir()
        for entry in ("requirements-reentry", None):
            with self.subTest(entry=entry):
                result = run(self.dir, entry=entry)
                self.assertNotEqual(result.returncode, 0, result.stdout)
                self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()
