"""plan-reread hook の task 名 / AC 行の形式許容に関する契約テスト。

背景:
hook は `## Current Task` 節から `[[ "$line" == "### Task:"* ]]` で task 名を取り、
空なら silent exit する。正本 `task-breakdown-steps.md` のテンプレートは
`### Task: T-1 <name>` なので hook は正本に忠実だが、実データの Current Task 節には
この形式が **無く**、多数派は `### Task <N>: X` と `- Task: X` だった。
その結果、gate 判定の区切りを揃えて canonical 判定を改善しても **一度も注入されないまま**だった。

AC 行も同様で、実データの多数派は `- Covers AC: AC-2, AC-5`。
`task-breakdown-steps.md` は「既存 artifact に `Covers AC:` が残っている場合は
**legacy alias として読んでよい**」と明記しているのに、hook は読めていなかった。

方針は gate 判定の区切りを揃えたときと同じ（Postel）: **読み手は実在する形式を受理し、書き手は正準形に寄せる**。
正準形は `### Task:` / `- AC:` のまま変えない。
"""
from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from _paths import PLUGIN_ROOT as ROOT
HOOK = ROOT / "hooks" / "scripts" / "run-pre-tool-use-plan-reread-hook.sh"

_STATE = (
    "Started At: 2026-07-28T00:00:00+09:00\n"
    "Resume From: gdd-subagent-driven-implementation\n"
    "Requirements Review Status=approved | evidence: req\n"
    "Design Review Status=approved | evidence: design\n"
    "Human Check Status=approved | evidence: human\n"
    "Route In Progress=none\n"
    "Last Handoff Summary: 記入済み\n"
)
_REQUIREMENTS = "### 一言\nG-11 fixture\n\n## 受入条件\n- AC-1: x\n"


def _run(current_task_section: str) -> str:
    """Current Task 節を差し替えて hook を実行し、注入された context を返す"""
    with tempfile.TemporaryDirectory(prefix="gdd-g11-") as tmp:
        repo = Path(tmp)
        subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
        # 毎ターンの注入は GDD の印（active な marker）があるときだけ
        (repo / ".claude").mkdir(exist_ok=True)
        (repo / ".claude" / "gdd-dev.local.md").write_text("---\nactive: true\n---\n", encoding="utf-8")
        steering = repo / ".steering" / "20260728-g11"
        steering.mkdir(parents=True)
        steering.joinpath("state.md").write_text(_STATE, encoding="utf-8")
        steering.joinpath("requirements.md").write_text(_REQUIREMENTS, encoding="utf-8")
        steering.joinpath("tasklist.md").write_text(
            "## Current Task\n" + current_task_section
            + "\n## Pending Tasks\n- なし\n\n## Review Status\nNext Action=gdd-subagent-driven-implementation\n",
            encoding="utf-8",
        )
        env = os.environ.copy()
        for var in ("CLAUDE_CODE_SESSION_ID", "GDD_PLUGIN_ROOT", "CLAUDE_PLUGIN_ROOT",
                    "GDD_PLAN_REREAD_DEDUP_WINDOW"):
            env.pop(var, None)
        r = subprocess.run(["bash", str(HOOK)], cwd=repo,
                           input=json.dumps({"tool_name": "Edit", "tool_input": {}}),
                           capture_output=True, text=True, env=env)
        return r.stdout


class TaskHeadingFormatTests(unittest.TestCase):
    def test_canonical_form(self) -> None:
        """正準形 `### Task: T-1 <name>`（task-breakdown-steps.md のテンプレート）"""
        out = _run("### Task: T-1 実装する\n- AC: AC-1\n")
        self.assertIn("T-1 実装する", out, f"canonical form must be recognized: {out!r}")

    def test_numbered_heading_form(self) -> None:
        """実データ最多の `### Task <N>: <name>`"""
        out = _run("### Task 1: reference 共通規約節を追加\n- AC: AC-1\n")
        self.assertIn("reference 共通規約節を追加", out,
                      f"numbered heading form must be recognized: {out!r}")

    def test_list_form(self) -> None:
        """実データ 2 番目の `- Task: <name>`"""
        out = _run("- Task: T20 - PR creation after amended P3 passes\n- AC: AC-1\n")
        self.assertIn("T20", out, f"list form must be recognized: {out!r}")

    def test_h4_form(self) -> None:
        """`#### Task ...` も拾う（見出しレベルのゆれ）"""
        out = _run("#### Task 3: 境界値の検証\n- AC: AC-1\n")
        self.assertIn("境界値の検証", out, f"h4 form must be recognized: {out!r}")

    def test_no_task_still_exits_silently(self) -> None:
        """task 見出しが本当に無い場合は従来どおり注入しない（過剰に緩めない）"""
        out = _run("- なし（全タスク完了）\n")
        self.assertEqual(out.strip(), "",
                         f"absent task must still exit silently: {out!r}")


class AcLineFormatTests(unittest.TestCase):
    def test_canonical_ac_field(self) -> None:
        """正準形 `- AC: AC-1, AC-3`"""
        out = _run("### Task: T-1 x\n- AC: AC-1, AC-3\n")
        self.assertIn("AC-1", out)
        self.assertIn("AC-3", out)

    def test_legacy_covers_ac_alias(self) -> None:
        """legacy alias `- Covers AC: AC-2, AC-5`

        task-breakdown-steps.md が「legacy alias として読んでよい」と明記している形式。
        実データの Current Task 節ではこれが多数派だった。
        """
        out = _run("### Task: T-1 x\n- Covers AC: AC-2, AC-5\n")
        self.assertIn("AC-2", out, f"legacy `Covers AC:` alias must be read: {out!r}")
        self.assertIn("AC-5", out, f"legacy `Covers AC:` alias must be read: {out!r}")

    def test_inline_ac_bullets(self) -> None:
        """`- AC-N: <説明>` 形式（従来から対応済み・非退行）"""
        out = _run("### Task: T-1 x\n- AC-1: implement it\n- AC-2: verify it\n")
        self.assertIn("AC-1", out)
        self.assertIn("AC-2", out)


if __name__ == "__main__":
    unittest.main()
