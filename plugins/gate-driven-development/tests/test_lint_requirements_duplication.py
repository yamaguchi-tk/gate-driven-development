"""lint-requirements-duplication.py の契約テスト。

AC を単一の正本にする運用（requirements-template.md § 事実は AC に 1 回だけ書く）で、
AC の欄名の列挙（backtick で囲んだ語が 2 つ以上）を AC 以外の節や design.md に
書き直している箇所を warn-only で出す。

背景: GDD を使う別の repo のタスク（2026-10-02）で、許可欄名を 3 つから 2 つに
減らしたのに AC-6 と Route / Ownership Matrix に古い欄名が残り、requirements
レビュー 2 回目の blocking がすべてこの書き換え漏れだった。
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from _paths import PLUGIN_ROOT

LINT = PLUGIN_ROOT / "scripts" / "lint-requirements-duplication.py"
HOOK = PLUGIN_ROOT / "hooks" / "scripts" / "validate-steering-write.py"

REQ_WITH_AC = (
    "# Requirements\n"
    "\n"
    "## Summary Brief\n"
    "\n"
    "{summary}\n"
    "\n"
    "## 受入条件\n"
    "\n"
    "- AC-1: 何もしない\n"
    "- AC-6: 許可欄は `allow_read` と `allow_write` の 2 つにする\n"
    "  - 例: `allow_read` / `allow_write` が無い行は拒否する\n"
    "\n"
    "## Route / Ownership Matrix\n"
    "\n"
    "{matrix}\n"
)


class LintRequirementsDuplicationTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = Path(tempfile.mkdtemp()).resolve()
        self.addCleanup(shutil.rmtree, self._tmp, ignore_errors=True)
        self.steering = self._tmp / ".steering" / "20261002-dup-test"
        self.steering.mkdir(parents=True)

    def _write(self, name: str, text: str) -> Path:
        p = self.steering / name
        p.write_text(text, encoding="utf-8")
        return p

    def _req(self, summary: str = "AC-6 参照", matrix: str = "AC-6 参照") -> Path:
        return self._write("requirements.md", REQ_WITH_AC.format(summary=summary, matrix=matrix))

    def _lint(self) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(LINT), "--steering-dir", str(self.steering)],
            capture_output=True,
            text=True,
        )

    def test_same_field_list_in_summary_warns(self) -> None:
        self._req(summary="- 確定事項: 許可欄は `allow_read` / `allow_write`")
        result = self._lint()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("WARN:", result.stdout)
        self.assertIn("AC-6", result.stdout)
        self.assertIn("requirements.md:5", result.stdout)

    def test_stale_superset_list_in_matrix_warns(self) -> None:
        """AC を 2 つに減らした後も 3 つのまま残った列挙（S-1a の実例）を出す。"""
        self._req(matrix="| 許可欄 | `allow_read`, `allow_write`, `allow_admin` |")
        result = self._lint()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("WARN:", result.stdout)
        self.assertIn("requirements.md:15", result.stdout)

    def test_ac_reference_only_is_clean(self) -> None:
        self._req()
        result = self._lint()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("WARN:", result.stdout)

    def test_single_shared_token_is_not_a_list(self) -> None:
        """行に backtick の語が 2 つあっても、AC と重なるのが 1 つなら出さない。"""
        self._req(summary="- 既存の `allow_read` と `deny_all` の扱いは AC-6 参照")
        result = self._lint()
        self.assertNotIn("WARN:", result.stdout)

    def test_tokens_below_ac_line_count_as_the_ac(self) -> None:
        """AC の定義行の下に続く行（同じ節）の語も、その AC の語として数える。"""
        self._write(
            "requirements.md",
            "## Summary Brief\n\n- `allow_read` / `allow_write`\n\n## 受入条件\n\n"
            "- AC-6: 許可欄は `allow_read` を含む\n  - もう 1 つは `allow_write`\n",
        )
        result = self._lint()
        self.assertIn("requirements.md:3", result.stdout)
        self.assertIn("AC-6", result.stdout)

    def test_reference_sections_are_not_checked(self) -> None:
        """照合元（スコープの原文・Express Minimal Trace）と hook が読む Lane の値は書き直しに数えない。"""
        listed = "- `allow_read` / `allow_write`"
        self._write(
            "requirements.md",
            f"## スコープ\n\n{listed}\n\n"
            f"## Express Minimal Trace\n\n{listed}\n\n"
            f"## Planned Follow-up Stage Lane\n\n{listed}\n\n"
            "## 受入条件\n\n- AC-6: `allow_read` と `allow_write`\n",
        )
        result = self._lint()
        self.assertNotIn("WARN:", result.stdout)

    def test_express_scope_is_checked(self) -> None:
        """express の `## Scope` は `AC-1 参照` と書かせる欄で、照合元ではない。"""
        self._write(
            "requirements.md",
            "## Scope\n\n- Change: `allow_read` / `allow_write` にする\n\n"
            "## Acceptance Criteria\n\n- AC-1: `allow_read` と `allow_write`\n",
        )
        result = self._lint()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("requirements.md:3", result.stdout)

    def test_exclusion_covers_subsections_until_same_level_heading(self) -> None:
        """外した節の下の小見出し・コードフェンスの中の `#` 行も外し、同じ階層の次の見出しで戻る。"""
        listed = "- `allow_read` / `allow_write`"
        self._write(
            "requirements.md",
            f"## スコープ\n\n### 完了条件\n\n{listed}\n\n"
            f"## Planned Follow-up Stage Lane\n\n### S-2\n\n{listed}\n\n"
            f"```\n# コメント\n```\n\n{listed}\n\n"
            "## 受入条件\n\n- AC-6: `allow_read` と `allow_write`\n\n"
            f"## Route / Ownership Matrix\n\n{listed}\n",
        )
        result = self._lint()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.count("WARN:"), 1, result.stdout)
        self.assertIn("requirements.md:25", result.stdout)

    def test_exclusion_ends_at_higher_level_heading(self) -> None:
        listed = "- `allow_read` / `allow_write`"
        self._write(
            "requirements.md",
            f"## スコープ\n\n# 付録\n\n{listed}\n\n"
            "## 受入条件\n\n- AC-6: `allow_read` と `allow_write`\n",
        )
        result = self._lint()
        self.assertIn("requirements.md:5", result.stdout)

    def test_tilde_fence_heading_line_does_not_end_exclusion(self) -> None:
        listed = "- `allow_read` / `allow_write`"
        self._write(
            "requirements.md",
            f"## スコープ\n\n~~~\n## x\n~~~\n\n{listed}\n\n"
            "## 受入条件\n\n- AC-6: `allow_read` と `allow_write`\n",
        )
        result = self._lint()
        self.assertNotIn("WARN:", result.stdout)

    def test_info_string_line_does_not_close_fence(self) -> None:
        """info string 付きの行は閉じのフェンスにならない（CommonMark）。以後の見出しを失わない。"""
        self._write(
            "requirements.md",
            "## スコープ\n```markdown\n```bash\n## x\n```\n- `a` / `b`\n"
            "## 受入条件\n- AC-1: `a` と `b`\n",
        )
        result = self._lint()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("WARN:", result.stdout)

    def test_unclosed_fence_falls_back_to_plain_headings(self) -> None:
        self._write(
            "requirements.md",
            "## Summary Brief\n```\n## 受入条件\n- AC-1: `a` と `b`\n## Route / Ownership Matrix\n- `a` / `b`\n",
        )
        result = self._lint()
        self.assertIn("requirements.md:6", result.stdout)

    def test_unclosed_fence_keeps_earlier_closed_fences(self) -> None:
        """閉じないフェンスがあっても、それより前の閉じたフェンスの中の `#` 行は見出しにしない。"""
        self._write(
            "requirements.md",
            "## スコープ\n```bash\n# 実行例\n```\n- `allow_read` / `allow_write`\n"
            "## 受入条件\n- AC-6: `allow_read` と `allow_write`\n## メモ\n```\n",
        )
        result = self._lint()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("WARN:", result.stdout)

    def test_design_md_closed_fence_line_is_checked_despite_unclosed_fence(self) -> None:
        self._req()
        self._write("design.md", "# Design\n```bash\n# `allow_read` / `allow_write` を設定する\n```\n```\n")
        result = self._lint()
        self.assertIn("design.md:3", result.stdout)

    def test_fence_opener_follows_tasklist_parse(self) -> None:
        """フェンスの開きは `lib/tasklist_parse.py` と同じ規則（字下げは半角空白とタブ、backtick の info string に backtick を含まない）。"""
        for opener in ("```bash``` で実行する", "\u3000```"):
            with self.subTest(opener=opener):
                self._write(
                    "requirements.md",
                    f"## Summary Brief\n{opener}\n## 受入条件\n- AC-1: `a` と `b`\n"
                    "## Route / Ownership Matrix\n- `a` / `b`\n```\necho hi\n```\n",
                )
                result = self._lint()
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("requirements.md:6", result.stdout)

    def test_design_md_heading_like_line_inside_fence_is_checked(self) -> None:
        self._req()
        self._write("design.md", "# Design\n\n```\n# `allow_read` / `allow_write`\n```\n")
        result = self._lint()
        self.assertIn("design.md:4", result.stdout)

    def test_warning_names_the_exceptions(self) -> None:
        self._req(summary="- `allow_read` / `allow_write`")
        result = self._lint()
        self.assertIn("照合元と Lane の値は除く", result.stdout)

    def test_output_is_capped(self) -> None:
        """WARN は先頭の 5 件と残りの件数だけを出す（write のたびに context へ全件を載せない）。"""
        rows = "\n".join(f"- 行{i}: `allow_read` / `allow_write`" for i in range(8))
        self._req(summary=rows)
        result = self._lint()
        self.assertEqual(result.stdout.count("WARN:"), 5)
        self.assertIn("ほか 3 件", result.stdout)

    def test_design_md_duplication_warns(self) -> None:
        self._req()
        self._write(
            "design.md",
            "# Design\n\n## 変更点の要約\n\n- `allow_write` と `allow_read` を検査する\n",
        )
        result = self._lint()
        self.assertIn("WARN:", result.stdout)
        self.assertIn("design.md:5", result.stdout)

    def test_missing_requirements_is_silent(self) -> None:
        result = self._lint()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "")


class SteeringWriteHookWiresDuplicationLintTests(unittest.TestCase):
    """実際の入口（PreToolUse の steering write hook）から advisory に出るまでを通す。"""

    def setUp(self) -> None:
        self._state_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self._state_dir, ignore_errors=True)
        self._tmp = Path(tempfile.mkdtemp()).resolve()
        self.addCleanup(shutil.rmtree, self._tmp, ignore_errors=True)
        self.steering = self._tmp / ".steering" / "20261002-dup-hook"
        self.steering.mkdir(parents=True)

    def _run(self, target: Path, content: str) -> subprocess.CompletedProcess[str]:
        env = dict(os.environ)
        env["GDD_HOOK_STATE_DIR"] = self._state_dir
        # 配布時と同じく CLAUDE_PLUGIN_ROOT を明示して、plugin の lint を探させる
        env["CLAUDE_PLUGIN_ROOT"] = str(PLUGIN_ROOT)
        payload = {"tool_name": "Write", "tool_input": {"file_path": str(target), "content": content}}
        return subprocess.run(
            [sys.executable, str(HOOK)],
            input=json.dumps(payload),
            env=env,
            capture_output=True,
            text=True,
        )

    def test_design_write_surfaces_duplication_advisory(self) -> None:
        (self.steering / "requirements.md").write_text(
            REQ_WITH_AC.format(
                summary="- 確定事項: `allow_read` / `allow_write`", matrix="AC-6 参照"
            ),
            encoding="utf-8",
        )
        result = self._run(self.steering / "design.md", "# Design\n")
        self.assertEqual(result.returncode, 0, result.stderr)
        message = json.loads(result.stdout)["systemMessage"]
        self.assertIn("[duplication lint]", message)
        self.assertIn("AC-6", message)

    def test_empty_plugin_root_env_falls_back_to_script_location(self) -> None:
        """CLAUDE_PLUGIN_ROOT が空でも、cwd ではなく hook の位置から lint を探す。"""
        (self.steering / "requirements.md").write_text(
            REQ_WITH_AC.format(
                summary="- 確定事項: `allow_read` / `allow_write`", matrix="AC-6 参照"
            ),
            encoding="utf-8",
        )
        env = dict(os.environ)
        env["GDD_HOOK_STATE_DIR"] = self._state_dir
        env["CLAUDE_PLUGIN_ROOT"] = ""
        payload = {
            "tool_name": "Write",
            "tool_input": {"file_path": str(self.steering / "design.md"), "content": "# Design\n"},
        }
        result = subprocess.run(
            [sys.executable, str(HOOK)],
            input=json.dumps(payload),
            env=env,
            cwd=str(self._tmp),
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("[duplication lint]", json.loads(result.stdout)["systemMessage"])

    def test_clean_requirements_has_no_duplication_advisory(self) -> None:
        (self.steering / "requirements.md").write_text(
            REQ_WITH_AC.format(summary="AC-6 参照", matrix="AC-6 参照"), encoding="utf-8"
        )
        result = self._run(self.steering / "design.md", "# Design\n")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("[duplication lint]", result.stdout)


if __name__ == "__main__":
    unittest.main()
