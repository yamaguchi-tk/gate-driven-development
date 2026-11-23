"""AC-11: 見積もり diff 行数列の必須化と lint 実行経路の非空洞化。

実測（design.md § D9）: scripts/lint-hitl-stage-plan.py が実際に読むのは
human-check draft の `### 段階実装案` テーブルであり、requirements.md の
`Implementation Sequence Plan` ではない。lint を実行する test・skill 呼び出しが
repo 内に存在しなかったため、本テストが実行経路を新設する。
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from _paths import PLUGIN_ROOT
LINT_SCRIPT = PLUGIN_ROOT / "scripts" / "lint-hitl-stage-plan.py"

VALID_TABLE = """### 段階実装案

| Stage | この段階でやること | このPR/後続 | このOKで承認する範囲 | 完了確認 | 次に進む条件 / 人間に戻す条件 | 後続の追跡先 | 見積もり diff 行数 |
|---|---|---|---|---|---|---|---|
| S-1 | 契約テストを追加する | current-pr | このPRで実施許可 | pytest pass | AC 変更時に戻る | なし | 300〜500 行 |
"""

MISSING_COLUMN_TABLE = """### 段階実装案

| Stage | この段階でやること | このPR/後続 | このOKで承認する範囲 | 完了確認 | 次に進む条件 / 人間に戻す条件 | 後続の追跡先 |
|---|---|---|---|---|---|---|
| S-1 | 実装する | current-pr | このPRで実施許可 | pytest pass | AC 変更時に戻る | なし |
"""

VAGUE_ESTIMATE_TABLE = """### 段階実装案

| Stage | この段階でやること | このPR/後続 | このOKで承認する範囲 | 完了確認 | 次に進む条件 / 人間に戻す条件 | 後続の追跡先 | 見積もり diff 行数 |
|---|---|---|---|---|---|---|---|
| S-1 | 実装する | current-pr | このPRで実施許可 | pytest pass | AC 変更時に戻る | なし | 適切に |
"""


def _run_lint(markdown: str) -> subprocess.CompletedProcess:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "draft.md"
        path.write_text(markdown, encoding="utf-8")
        return subprocess.run(
            [sys.executable, str(LINT_SCRIPT), str(path), "--expected-stage", "S-1"],
            capture_output=True, text=True,
        )


class LintHitlStagePlanContractTests(unittest.TestCase):

    def test_full_table_exits_zero(self) -> None:
        result = _run_lint(VALID_TABLE)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_missing_estimate_column_exits_one(self) -> None:
        result = _run_lint(MISSING_COLUMN_TABLE)
        self.assertEqual(result.returncode, 1)
        self.assertIn("見積もり diff 行数", result.stderr)

    def test_vague_estimate_value_exits_one(self) -> None:
        result = _run_lint(VAGUE_ESTIMATE_TABLE)
        self.assertEqual(result.returncode, 1)
        self.assertIn("見積もり diff 行数", result.stderr)


if __name__ == "__main__":
    unittest.main()
