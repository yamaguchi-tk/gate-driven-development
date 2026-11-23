"""判断ポイントの固定フィールド（decision-quality の固定フィールドの検査と `依頼との差:`）だけを見る lint。

Stop hook の `HITL_LINT_WARN_SCRIPTS`（記録だけ。止めない）に配線する。判定は新しく書かず、
`lint-hitl-decision-quality.py` の固定フィールドの検査と `hooks/scripts/lib/request_diff_approval.py` を呼ぶ。
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from _paths import PLUGIN_ROOT

LINT = PLUGIN_ROOT / "scripts" / "lint-hitl-decision-fields.py"
sys.path.insert(0, str(PLUGIN_ROOT / "hooks" / "scripts"))
from lib.hitl_lint_gate import HITL_LINT_WARN_SCRIPTS  # noqa: E402


def sample(diff: str) -> str:
    return "\n".join([
        "### 判断ポイント",
        "承認ポイント数: 1",
        "1. 欄を足す — 変更前: 無い / 変更後: ある / 採用しない案: 足さない",
        "   - 判断に影響する前提: 書き手が差に気づくこと",
        f"   - 依頼との差: {diff}",
        "   - 無回答時のデフォルト: 欄を足して進める",
        "",
        "完了条件の変換",
        "延期・削除: なし",
        '<gdd-hitl-fields request-diff="none">',
        '<gdd-stop reason="human-check-waiting">',
    ])


def run(text: str) -> subprocess.CompletedProcess:
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as fh:
        fh.write(text)
    try:
        return subprocess.run([sys.executable, "-I", str(LINT), fh.name], capture_output=True, text=True)
    finally:
        Path(fh.name).unlink()


class DecisionFieldsLintTest(unittest.TestCase):
    def test_all_none_passes(self) -> None:
        result = run(sample("なし"))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_value_outside_the_two_forms_fails(self) -> None:
        result = run(sample("全レーンに入れる"))
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("依頼との差", result.stdout + result.stderr)

    def test_declared_difference_fails_like_the_stop_hook(self) -> None:
        """差を `あり: <項目>` と宣言した点は、表示した Stop で request-diff の hook が出し直させる。表示の前の lint も同じ判定で落とす。"""
        result = run(sample("あり: 全レーンに入れる"))
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("なし以外の点がある", result.stdout + result.stderr)

    def test_missing_existing_fixed_field_fails(self) -> None:
        text = sample("なし").replace("   - 判断に影響する前提: 書き手が差に気づくこと\n", "")
        self.assertEqual(run(text).returncode, 1)

    def test_wired_as_record_only(self) -> None:
        self.assertIn(("lint-hitl-decision-fields", "lint-hitl-decision-fields.py"), HITL_LINT_WARN_SCRIPTS)


if __name__ == "__main__":
    unittest.main()
