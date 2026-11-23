"""lint-plan-consistency.py の、requirements の AC と承認ポイントの `根拠:`・`計測:` の欄の検査。

requirements gate の Round 1 の blocking は、AC に書いた事実がコード・データと食い違う（根拠の誤り）か、
AC の合否の測り方が決まっていない（測り方の未定）ものが多かった。AC ごとに `根拠:` と `計測:`、
承認ポイントの項目ごとに `根拠:` を書かせ、reviewer を起動する前に欄の有無だけを確かめる（値は読まない）。
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

APPROVAL_OK = """\
## Summary Brief

### 承認ポイント
1. **方向性**: 承認
2. **scope**: 既存の helper を使う
   - 背景: 既存の helper がある
   - 根拠: src/helper.py:12
"""

AC_OK = "- AC-1: reviewer は 30 分で返る / 根拠: src/app.py:12 / 計測: reviews.md の所要時間、直近 10 Round、30 分以内\n"


def requirements(acceptance: str, approval: str = APPROVAL_OK) -> str:
    return approval + "\n## 受入条件\n" + acceptance


def run(steering: Path, entry: str | None = "requirements") -> subprocess.CompletedProcess[str]:
    extra = ["--entry", entry] if entry else []
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--steering-dir", str(steering), *extra],
        capture_output=True,
        text=True,
    )


class AcFieldsTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def req(self, text: str) -> None:
        (self.dir / "requirements.md").write_text(text, encoding="utf-8")

    def assert_ok(self, result: subprocess.CompletedProcess[str]) -> None:
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn("ERROR", result.stdout)
        self.assertNotIn("Traceback", result.stderr)

    def assert_error(self, result: subprocess.CompletedProcess[str], *needles: str) -> None:
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        for needle in needles:
            self.assertIn(needle, result.stdout)

    def test_ac_and_approval_with_fields_pass(self) -> None:
        self.req(requirements(AC_OK))
        self.assert_ok(run(self.dir))

    def test_ac_without_evidence_is_error(self) -> None:
        self.req(requirements("- AC-1: reviewer は 30 分で返る / 計測: 所要時間、30 分以内\n"))
        self.assert_error(run(self.dir), "AC-1 に `根拠:` の欄が無い")

    def test_ac_without_measurement_is_error(self) -> None:
        self.req(requirements("- AC-1: reviewer は 30 分で返る / 根拠: src/app.py:12\n"))
        self.assert_error(run(self.dir), "AC-1 に `計測:` の欄が無い")

    def test_fields_on_continuation_lines_pass(self) -> None:
        self.req(requirements("- **AC-1**（人間承認済み）: reviewer は 30 分で返る\n  - 根拠: なし（新規の機能）\n  - 計測：所要時間、30 分以内\n"))
        self.assert_ok(run(self.dir))

    def test_fields_of_next_ac_do_not_count(self) -> None:
        # block すべき入力: 次の AC の欄で前の AC が通らない
        self.req(requirements("- AC-1: 返る\n" + AC_OK.replace("AC-1", "AC-2")))
        result = run(self.dir)
        self.assert_error(result, "AC-1")
        self.assertNotIn("AC-2", result.stdout)

    def test_word_without_colon_is_not_a_field(self) -> None:
        self.req(requirements("- AC-1: 根拠は src/app.py、計測は所要時間\n"))
        self.assert_error(run(self.dir), "AC-1")

    def test_fields_in_next_section_do_not_count(self) -> None:
        self.req(requirements("- AC-1: 返る\n\n## 実装方針\n- 根拠: src/app.py:12 / 計測: 所要時間\n"))
        self.assert_error(run(self.dir), "AC-1")

    def test_fields_inside_closed_fence_do_not_count(self) -> None:
        self.req(requirements("- AC-1: 返る\n  ```\n  根拠: src/app.py:12 / 計測: 所要時間\n  ```\n"))
        self.assert_error(run(self.dir), "AC-1")

    def test_approval_item_without_evidence_is_error(self) -> None:
        approval = "## Summary Brief\n\n### 承認ポイント\n1. **方向性**: 承認\n2. **scope**: 既存の helper を使う\n   - 背景: 既存の helper がある\n"
        self.req(requirements(AC_OK, approval))
        self.assert_error(run(self.dir), "承認ポイント", "scope")

    def test_direction_item_is_not_checked(self) -> None:
        self.req(requirements(AC_OK, "### 承認ポイント\n1. **方向性**: 承認\n"))
        self.assert_ok(run(self.dir))

    def test_direction_word_in_other_item_is_checked(self) -> None:
        # 方向性の除外はカテゴリの位置だけ。本文に太字の方向性がある項目は検査する
        self.req(requirements(AC_OK, APPROVAL_OK + "3. **scope**: **方向性** の自走範囲を狭める\n"))
        self.assert_error(run(self.dir), "承認ポイント 3. **scope**")

    def test_each_approval_item_is_checked(self) -> None:
        approval = APPROVAL_OK + "3. **rollback**: 戻せる\n"
        self.req(requirements(AC_OK, approval))
        result = run(self.dir)
        self.assert_error(result, "rollback")
        self.assertNotIn("scope", result.stdout)

    def test_human_check_questions_are_not_checked(self) -> None:
        self.req(requirements(AC_OK) + "\n## Human Check Questions\n1. **scope**: 既存の helper を使う\n")
        self.assert_ok(run(self.dir))

    def test_reentry_checks_ac_fields(self) -> None:
        self.req(requirements("- AC-1: 返る\n"))
        (self.dir / "reviews.md").write_text(
            "## Round 1\n- 判定: changes_requested\n- 処置:\n  - B1: 直した / 根拠: src/app.py:1 / 伝播: なし\n",
            encoding="utf-8",
        )
        self.assert_error(run(self.dir, entry="requirements-reentry"), "AC-1")

    def test_design_entry_does_not_check_fields(self) -> None:
        # design の起動では AC の欄を見ない（承認の後に合否の欄を書き足させない）
        self.req(requirements("- AC-1: 返る\n", "### 承認ポイント\n1. **scope**: x\n"))
        self.assert_ok(run(self.dir, entry="design"))

    def test_old_other_entry_is_usage_error(self) -> None:
        # 前の意味（requirements の初回も含む）で `other` を渡しても欄の検査が抜けない
        self.req(requirements("- AC-1: 返る\n"))
        result = run(self.dir, entry="other")
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_field_name_inside_other_words_is_not_a_field(self) -> None:
        # block すべき入力: 欄名の部分一致で欄があるとみなさない
        for line in (
            "- AC-1: 返る / 判断根拠: 小さい / 計測: 所要時間",
            "- AC-1: 返る / 狭める根拠: 小さい / 計測: 所要時間",
            "- AC-1: 処置に `根拠:` が無ければ止まる / 計測: テスト",
            "- AC-1: 返る / 根拠: src/app.py:1 / 再計測: 所要時間",
        ):
            with self.subTest(line=line):
                self.req(requirements(line + "\n"))
                self.assert_error(run(self.dir), "AC-1")

    def test_field_positions_are_accepted(self) -> None:
        for acceptance in (
            "- AC-1: 返る / 根拠: src/app.py:1 / 計測: 所要時間\n",
            "- AC-1: 返る ／根拠：src/app.py:1 ／計測：所要時間\n",
            "- AC-1: 返る\n  - **根拠**: src/app.py:1\n  - **計測**：所要時間\n",
            "- AC-1: 返る\n  * 根拠: src/app.py:1\n  * 計測: 所要時間\n",
        ):
            with self.subTest(acceptance=acceptance):
                self.req(requirements(acceptance))
                self.assert_ok(run(self.dir))

    def test_no_ac_is_error(self) -> None:
        # 判定できないときに通さない: AC を 1 件も認識できなければ止める
        for acceptance in ("1. AC-1: 返る / 根拠: x / 計測: y\n", "### AC-1: 返る\n", "返る\n"):
            with self.subTest(acceptance=acceptance):
                self.req(requirements(acceptance))
                self.assert_error(run(self.dir), "AC")

    def test_no_approval_section_is_error(self) -> None:
        self.req("## Summary Brief\n\n## 受入条件\n" + AC_OK)
        self.assert_error(run(self.dir), "承認ポイント")

    def test_approval_without_numbered_items_is_error(self) -> None:
        # HCQ を参照するだけ・箇条だけ・小見出しの承認ポイントは、項目 0 件として止める
        for approval in (
            "### 承認ポイント\n`Human Check Questions` の 1〜3 を参照（方向性を含む）。\n",
            "### 承認ポイント\n- **scope**: 既存の helper を使う\n",
            "### 承認ポイント\n#### 1. scope\n- 根拠: y\n",
        ):
            with self.subTest(approval=approval):
                self.req(requirements(AC_OK, approval))
                self.assert_error(run(self.dir), "承認ポイント")

    def test_approval_heading_with_note_is_checked(self) -> None:
        # 見出しの `（…）` の付記は承認ポイントとして読む（`### 承認ポイントの補足` は別の節）
        self.req(requirements(AC_OK, "### 承認ポイント（再確認）\n1. **scope**: x\n"))
        self.assert_error(run(self.dir), "scope")
        self.req(requirements(AC_OK, "### 承認ポイントの補足\n1. **scope**: x / 根拠: y\n"))
        self.assert_error(run(self.dir), "番号つき項目")

    def test_sub_numbered_approval_items_are_checked(self) -> None:
        # `3a.`・`3-1.` を前の項目の続きにして、前の項目の欄で通さない
        for item in ("3a. **rollback**: 戻せる\n", "3-1. **rollback**: 戻せる\n"):
            with self.subTest(item=item):
                self.req(requirements(AC_OK, APPROVAL_OK + item))
                self.assert_error(run(self.dir), "rollback")

    def test_design_entry_does_not_count_items(self) -> None:
        self.req("## Summary Brief\n\n## 受入条件\n返る\n")
        self.assert_ok(run(self.dir, entry="design"))

    def test_missing_entry_is_usage_error(self) -> None:
        # 判定できないときに通さない（--entry の付け忘れで欄の検査が抜けない）
        self.req(requirements("- AC-1: 返る\n"))
        result = run(self.dir, entry=None)
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("--entry", result.stderr)

    def test_undecodable_bytes_do_not_crash(self) -> None:
        # 例外で検査全体が落ちない
        (self.dir / "requirements.md").write_bytes(requirements("- AC-1: 返る \xff\n").encode("utf-8", "surrogateescape") + b"\xff\n")
        self.assert_error(run(self.dir), "AC-1")


if __name__ == "__main__":
    unittest.main()
