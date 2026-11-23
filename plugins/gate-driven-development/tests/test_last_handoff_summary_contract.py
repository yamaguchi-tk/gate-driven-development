"""`Last Handoff Summary` の記入を build 中に促す契約テスト。

背景:
`Last Handoff Summary` は compaction や別セッションの後に「何をしていたか」を戻せる唯一の context source
（`state-field-tiers.md` § Tier 3 / context source）。だが実運用の state.md では
ほとんど書かれていなかった。reference と skill の指示だけでは守られていない。

そこで、既に build 中の Write/Edit 前に Current Task + AC を再注入している plan-reread hook
（Manus の recitation 原則に相当）に、欠落時だけ一行の促しを足す。新しい hook は追加しない。
"""
from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from _paths import PLUGIN_ROOT
HOOK = PLUGIN_ROOT / "hooks" / "scripts" / "run-pre-tool-use-plan-reread-hook.sh"

_STATE_BASE = (
    "Started At: 2026-07-27T00:00:00+09:00\n"
    "Resume From: gdd-subagent-driven-implementation\n"
    "Requirements Review Status=approved | evidence: req\n"
    "Design Review Status=approved | evidence: design\n"
    "Human Check Status=approved | evidence: human\n"
    "Route In Progress=none\n"
)
_REQUIREMENTS = "### 一言\nhandoff summary fixture\n\n## 受入条件\n- AC-1: x\n"
_TASKLIST = (
    "## Current Task\n"
    "### Task: T-1 | implement\n"
    "- AC-1: implement it\n\n"
    "## Pending Tasks\n- なし\n\n"
    "## Review Status\nNext Action=gdd-subagent-driven-implementation\n"
)


def _setup(repo: Path, state_extra: str = "") -> None:
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    # 毎ターンの注入は GDD の印（active な marker）があるときだけ
    (repo / ".claude").mkdir(exist_ok=True)
    (repo / ".claude" / "gdd-dev.local.md").write_text("---\nactive: true\n---\n", encoding="utf-8")
    steering = repo / ".steering" / "20260727-handoff"
    steering.mkdir(parents=True, exist_ok=True)
    steering.joinpath("state.md").write_text(_STATE_BASE + state_extra, encoding="utf-8")
    steering.joinpath("requirements.md").write_text(_REQUIREMENTS, encoding="utf-8")
    steering.joinpath("tasklist.md").write_text(_TASKLIST, encoding="utf-8")


def _run(repo: Path) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    for var in ("CLAUDE_CODE_SESSION_ID", "GDD_PLUGIN_ROOT", "CLAUDE_PLUGIN_ROOT", "GDD_PLAN_REREAD_DEDUP_WINDOW"):
        env.pop(var, None)
    return subprocess.run(
        ["bash", str(HOOK)],
        cwd=repo,
        input=json.dumps({"tool_name": "Edit", "tool_input": {}}),
        capture_output=True,
        text=True,
        env=env,
    )


class LastHandoffSummaryPromptTests(unittest.TestCase):
    def test_prompts_when_field_absent(self) -> None:
        """未記入なら注入 context に促しが含まれる"""
        with tempfile.TemporaryDirectory(prefix="gdd-handoff-") as tmp:
            repo = Path(tmp)
            _setup(repo)
            result = _run(repo)
            self.assertEqual(result.returncode, 0)
            self.assertIn(
                "Last Handoff Summary", result.stdout,
                f"absent field must be prompted: {result.stdout!r}",
            )

    def test_no_prompt_when_field_present(self) -> None:
        """記入済みなら促しを出さない（注入を無駄に太らせない）"""
        with tempfile.TemporaryDirectory(prefix="gdd-handoff-") as tmp:
            repo = Path(tmp)
            _setup(repo, "Last Handoff Summary: AC-1 の実装中、境界値のテストが残り\n")
            result = _run(repo)
            self.assertEqual(result.returncode, 0)
            self.assertNotIn(
                "Last Handoff Summary が未記入", result.stdout,
                f"present field must not be prompted: {result.stdout!r}",
            )

    def test_existing_injection_still_intact(self) -> None:
        """促しを足しても既存の Task / AC 注入は壊れない"""
        with tempfile.TemporaryDirectory(prefix="gdd-handoff-") as tmp:
            repo = Path(tmp)
            _setup(repo)
            result = _run(repo)
            self.assertIn("Task: T-1", result.stdout)
            self.assertIn("AC-1", result.stdout)
            # JSON として妥当であること（エスケープ崩れの検出）
            payload = json.loads(result.stdout)
            self.assertEqual(
                payload["hookSpecificOutput"]["hookEventName"], "PreToolUse"
            )


if __name__ == "__main__":
    unittest.main()
