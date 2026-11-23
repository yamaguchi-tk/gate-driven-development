"""Gate Batch 中の `Current Task` を、文脈を注入する hook が正しく読む（2026-09-30）。

Gate Batch では、実装を終えた task と実装中の task が `Current Task` に並ぶ。
UserPromptSubmit と PreToolUse（plan reread）の hook は、task 名を節の最初の task 見出しから読む。
契約は「実装中の task を先頭に置く」ことで、hook を変えずに実装中の task 名を注入させる。
ほかの field の読み方は hook ごとに違う（限界として開示している）。
- UserPromptSubmit: AC は節全体の ID、Last Error は節の最後の試行 1 件（終えた task の試行に置き換わる）
- plan reread: `- AC:` 行は最初の task から、Past Attempts は節全体から読む
本テストは hook を実際に起動し、この読み方を固定する。hook を task 単位に直したら、限界の assert を直す。
"""
from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from _paths import PLUGIN_ROOT as ROOT

HOOKS = ROOT / "hooks" / "scripts"

_STATE = (
    "Started At: 2026-09-30T00:00:00+09:00\n"
    "Resume From: gdd-subagent-driven-implementation\n"
    "Requirements Review Status=approved | evidence: req\n"
    "Design Review Status=approved | evidence: design\n"
    "Human Check Status=approved | evidence: human\n"
    "Route In Progress=none\n"
    "Last Handoff Summary: 記入済み\n"
)
_REQUIREMENTS = "### 一言\nGate Batch fixture\n\n## 受入条件\n- AC-1: x\n- AC-2: y\n"

# 契約どおりの並び: 実装中の T-2 が先頭、実装を終えた T-1 が後ろ
_TASKLIST = (
    "## Execution Plan\n- Mode: sequential\n- Gate Batch 1: T-1, T-2\n\n"
    "## Current Task\n"
    "### Task: T-2 実装中の task\n- AC: AC-2\n- Execution Status: in_progress\n"
    "#### Attempts\n- T-2 の試行\n\n"
    "### Task: T-1 実装を終えた task\n- AC: AC-1\n- Execution Status: completed\n"
    "#### Attempts\n- T-1 の試行\n\n"
    "## Pending Tasks\n- なし\n\n## Review Status\nNext Action=gdd-subagent-driven-implementation\n"
)


def _run(hook: str, payload: dict) -> dict:
    with tempfile.TemporaryDirectory(prefix="gdd-gate-batch-") as tmp:
        repo = Path(tmp)
        subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
        # 毎ターンの注入は GDD の印（active な marker）があるときだけ
        (repo / ".claude").mkdir(exist_ok=True)
        (repo / ".claude" / "gdd-dev.local.md").write_text("---\nactive: true\n---\n", encoding="utf-8")
        steering = repo / ".steering" / "20260930-gate-batch"
        steering.mkdir(parents=True)
        steering.joinpath("state.md").write_text(_STATE, encoding="utf-8")
        steering.joinpath("requirements.md").write_text(_REQUIREMENTS, encoding="utf-8")
        steering.joinpath("tasklist.md").write_text(_TASKLIST, encoding="utf-8")
        env = os.environ.copy()
        for var in ("CLAUDE_CODE_SESSION_ID", "GDD_PLUGIN_ROOT", "CLAUDE_PLUGIN_ROOT",
                    "GDD_PLAN_REREAD_DEDUP_WINDOW"):
            env.pop(var, None)
        result = subprocess.run(["bash", str(HOOKS / hook)], cwd=repo, input=json.dumps(payload),
                                capture_output=True, text=True, env=env)
        return json.loads(result.stdout)["hookSpecificOutput"]


class GateBatchHookInjectionTests(unittest.TestCase):
    def test_user_prompt_submit_injects_the_task_in_progress(self) -> None:
        context = _run("run-user-prompt-submit-hook.sh", {"prompt": "続けて"})["additionalContext"]
        self.assertIn("Current Task: T-2 実装中の task.", context)
        self.assertNotIn("T-1 実装を終えた task", context)
        # 限界: AC は節全体の ID、Last Error は節の最後の試行 1 件（終えた task の分）から読む
        self.assertIn("AC: AC-1, AC-2.", context)
        self.assertIn("Last Error: T-1 の試行.", context)
        self.assertNotIn("T-2 の試行", context)

    def test_plan_reread_injects_the_task_in_progress(self) -> None:
        context = _run("run-pre-tool-use-plan-reread-hook.sh",
                       {"tool_name": "Edit", "tool_input": {}})["additionalContext"]
        self.assertIn("Task: T-2 実装中の task.", context)
        self.assertIn("AC: AC-2.", context)
        self.assertNotIn("T-1 実装を終えた task", context)
        # 限界: Past Attempts は節全体（終えた task の分を含む）から読む
        self.assertIn("Past Attempts: T-2 の試行; T-1 の試行.", context)


if __name__ == "__main__":
    unittest.main()
