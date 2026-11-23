"""lint-plan-consistency.py の振る舞いテスト。

planning reviewer が計画 doc 全文を読んで手で突合していた機械的な整合
（AC ID は受入条件で定義し、Summary Brief・Implementation Sequence Plan・
design.md では引用だけにする / 引用先の AC が実在する / 同じ AC の数値が
食い違わない）を script に移す。reviewer の入力を狭める前提になる。
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

### 一言
AC-1 と AC-2 を満たす。

## 受入条件
- AC-1: reviewer は 30 分で返る
- AC-2: 再実行は 1 回まで

## Implementation Sequence Plan
| Stage | AC |
|---|---|
| S-1 | AC-1 |
| S-2 | AC-2 |
"""

DESIGN_OK = """\
# design

AC-1 は timer で測る。AC-2 は再実行 1 回で閉じる。
"""


def run(steering: Path, *extra: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--steering-dir", str(steering), "--entry", "design", *extra],
        capture_output=True,
        text=True,
    )


class LintPlanConsistencyTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def write(self, requirements: str, design: str | None = None) -> None:
        (self.dir / "requirements.md").write_text(requirements, encoding="utf-8")
        if design is not None:
            (self.dir / "design.md").write_text(design, encoding="utf-8")

    def test_consistent_plan_passes(self) -> None:
        self.write(REQUIREMENTS_OK, DESIGN_OK)
        result = run(self.dir)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn("ERROR", result.stdout)
        self.assertNotIn("WARN", result.stdout)

    def test_unknown_ac_cited_in_summary_is_error(self) -> None:
        self.write(REQUIREMENTS_OK.replace("AC-1 と AC-2 を満たす。", "AC-1 と AC-9 を満たす。"))
        result = run(self.dir)
        self.assertEqual(result.returncode, 1)
        self.assertIn("AC-9", result.stdout)
        self.assertIn("Summary Brief", result.stdout)

    def test_unknown_ac_cited_in_sequence_plan_is_error(self) -> None:
        self.write(REQUIREMENTS_OK.replace("| S-2 | AC-2 |", "| S-2 | AC-3 |"))
        result = run(self.dir)
        self.assertEqual(result.returncode, 1)
        self.assertIn("AC-3", result.stdout)
        self.assertIn("Implementation Sequence Plan", result.stdout)

    def test_unknown_ac_cited_in_design_is_error(self) -> None:
        self.write(REQUIREMENTS_OK, DESIGN_OK + "AC-7 も満たす。\n")
        result = run(self.dir)
        self.assertEqual(result.returncode, 1)
        self.assertIn("AC-7", result.stdout)
        self.assertIn("design.md", result.stdout)

    def test_ac_redefined_outside_acceptance_section_is_error(self) -> None:
        # 引用だけにすべき場所で `- AC-1: ...` と書き直すと、定義が 2 つになって食い違う
        self.write(REQUIREMENTS_OK, DESIGN_OK + "\n- AC-1: reviewer は 20 分で返る\n")
        result = run(self.dir)
        self.assertEqual(result.returncode, 1)
        self.assertIn("AC-1", result.stdout)
        self.assertIn("design.md", result.stdout)

    def test_ac_redefined_in_summary_is_error(self) -> None:
        self.write(REQUIREMENTS_OK.replace("AC-1 と AC-2 を満たす。", "- AC-1: reviewer は 30 分で返る"))
        result = run(self.dir)
        self.assertEqual(result.returncode, 1)
        self.assertIn("Summary Brief", result.stdout)

    def test_missing_acceptance_section_is_error(self) -> None:
        # AC を引用しない入力にして、引用先の欠落の ERROR と区別する
        self.write("# requirements\n\n## 目的\nfoo\n")
        result = run(self.dir)
        self.assertEqual(result.returncode, 1)
        self.assertIn("節が無い", result.stdout)

    def test_numbers_are_compared_only_on_single_ac_lines(self) -> None:
        self.write(REQUIREMENTS_OK, DESIGN_OK + "AC-1 と AC-2 の上限は 20 分にする。\n")
        result = run(self.dir)
        self.assertEqual(result.returncode, 0)
        self.assertNotIn("WARN", result.stdout)

    def test_heading_inside_code_fence_does_not_split_acceptance(self) -> None:
        requirements = REQUIREMENTS_OK.replace(
            "- AC-2: 再実行は 1 回まで",
            "```markdown\n## Round 1\n```\n- AC-2: 再実行は 1 回まで",
        )
        self.write(requirements, DESIGN_OK)
        result = run(self.dir)
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_definition_inside_code_fence_in_design_is_not_redefinition(self) -> None:
        self.write(REQUIREMENTS_OK, DESIGN_OK + "```\n- AC-1: 例\n```\n")
        result = run(self.dir)
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_unclosed_fence_does_not_hide_later_errors(self) -> None:
        # 閉じ忘れの fence から後ろを読み飛ばすと、再定義と未定義の引用が素通りする
        self.write(REQUIREMENTS_OK, DESIGN_OK + "```mermaid\ngraph TD\n\n- AC-1: reviewer は 20 分で返る\nAC-9 も満たす。\n")
        result = run(self.dir)
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("AC-9", result.stdout)

    def test_unclosed_fence_in_requirements_does_not_hide_sequence_plan(self) -> None:
        requirements = REQUIREMENTS_OK.replace("## Implementation Sequence Plan", "```\n\n## Implementation Sequence Plan").replace(
            "| S-2 | AC-2 |", "| S-2 | AC-8 |"
        )
        self.write(requirements, DESIGN_OK)
        result = run(self.dir)
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("AC-8", result.stdout)

    def test_example_inside_unclosed_fence_is_not_counted_as_definition(self) -> None:
        # 閉じ忘れの fence の後ろを残すと、記入例の `- AC-9:` が定義に数えられ、未定義の引用が素通りする
        requirements = (
            "## Summary Brief\nAC-9 を満たす。\n~~~\n## 受入条件\n- AC-1: reviewer は 30 分で返る\n"
            "```markdown\n- AC-9: <記入例>\n```\n"
        )
        self.write(requirements)
        result = run(self.dir)
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("requirements.md line 3: コード fence が閉じていない", result.stdout)

    def test_unclosed_fence_in_design_reports_its_line(self) -> None:
        self.write(REQUIREMENTS_OK, DESIGN_OK + "```mermaid\ngraph TD\n")
        result = run(self.dir)
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("design.md line 4: コード fence が閉じていない", result.stdout)

    def test_backtick_line_inside_tilde_fence_does_not_close_it(self) -> None:
        self.write(REQUIREMENTS_OK, DESIGN_OK + "~~~\n```\n~~~\n- AC-1: reviewer は 20 分で返る\n")
        result = run(self.dir)
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("定義し直している", result.stdout)

    def test_shorter_backtick_line_inside_longer_fence_does_not_close_it(self) -> None:
        self.write(REQUIREMENTS_OK, DESIGN_OK + "````\n```\n````\n- AC-1: reviewer は 20 分で返る\n")
        result = run(self.dir)
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertIn("定義し直している", result.stdout)

    def test_sequence_plan_table_rows_are_not_compared(self) -> None:
        # Implementation Sequence Plan は Stage ごとに見積もり diff 行数を書く
        requirements = REQUIREMENTS_OK.replace("reviewer は 30 分で返る", "変更は 100 行以内").replace(
            "| S-1 | AC-1 |", "| S-1 | AC-1 | 120 行 |"
        )
        self.write(requirements, DESIGN_OK)
        result = run(self.dir)
        self.assertEqual(result.returncode, 0)
        self.assertNotIn("WARN", result.stdout)

    def test_bunkatsu_is_not_a_minute_value(self) -> None:
        self.write(REQUIREMENTS_OK, DESIGN_OK + "AC-1 の作業は 3 分割する。\n")
        result = run(self.dir)
        self.assertEqual(result.returncode, 0)
        self.assertNotIn("WARN", result.stdout)

    def test_number_mismatch_for_same_ac_is_warning_only(self) -> None:
        self.write(REQUIREMENTS_OK, DESIGN_OK + "AC-1 の上限は 20 分にする。\n")
        result = run(self.dir)
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("WARN", result.stdout)
        self.assertIn("AC-1", result.stdout)
        self.assertIn("20分", result.stdout.replace(" ", ""))

    def test_number_match_for_same_ac_is_silent(self) -> None:
        self.write(REQUIREMENTS_OK, DESIGN_OK + "AC-1 の上限は 30 分にする。\n")
        result = run(self.dir)
        self.assertEqual(result.returncode, 0)
        self.assertNotIn("WARN", result.stdout)

    def test_number_with_different_unit_is_not_compared(self) -> None:
        self.write(REQUIREMENTS_OK, DESIGN_OK + "AC-1 の変更は 120 行に収める。\n")
        result = run(self.dir)
        self.assertEqual(result.returncode, 0)
        self.assertNotIn("WARN", result.stdout)

    def test_design_missing_is_skipped(self) -> None:
        self.write(REQUIREMENTS_OK)
        result = run(self.dir)
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_requirements_missing_is_usage_error(self) -> None:
        result = run(self.dir)
        self.assertEqual(result.returncode, 2)


if __name__ == "__main__":
    unittest.main()
