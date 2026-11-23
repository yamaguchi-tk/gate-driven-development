"""新しいセッションで再開するときの context 引き継ぎ契約テスト。

以前の変更で、compaction 後の復帰プロンプトに `Approved Direction` / `Last Handoff Summary` を
注入するようにした（compaction の後の復帰プロンプトは 2026-09-28 に廃止した）。しかし
**別セッション（新しいチャット）で再開する経路**には同じ手当が無かった。

- SessionStart の active steering パスは routing 指示（「state.md を workflow owner として使え」）
  しか出さず、state.md の中身を注入しない
- UserPromptSubmit が active steering の context を組み立てる唯一の場所だが、
  Goal / Current Task / AC / Next Action / Route In Progress までで、
  **「何をしていたか」（Last Handoff Summary）と「どの方針で承認されたか」（Approved Direction）が無い**

会話履歴が丸ごと無い分、別セッションの方が compaction 復帰より引き継ぎの必要性は高い。
compaction 側の対称的な穴として同じ 2 field を注入する。
"""
from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from _paths import PLUGIN_ROOT as ROOT
HOOK = ROOT / "hooks" / "scripts" / "run-user-prompt-submit-hook.sh"

_TASKLIST = (
    "## Current Task\n"
    "### Task: T-1 実装する\n"
    "- AC: AC-1\n\n"
    "## Review Status\nNext Action=gdd-subagent-driven-implementation\n"
)


def _setup(repo: Path, extra_state: str = "") -> None:
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    # 毎ターンの注入は GDD の印（active な marker）があるときだけ
    (repo / ".claude").mkdir(exist_ok=True)
    (repo / ".claude" / "gdd-dev.local.md").write_text("---\nactive: true\n---\n", encoding="utf-8")
    steering = repo / ".steering" / "20260728-cross-session"
    steering.mkdir(parents=True, exist_ok=True)
    steering.joinpath("state.md").write_text(
        "Started At: 2026-07-28T00:00:00+09:00\n"
        "Resume From: gdd-subagent-driven-implementation\n"
        "Requirements Review Status=approved | evidence: r\n"
        "Design Review Status=approved | evidence: d\n"
        "Human Check Status=approved | evidence: h\n"
        "Route In Progress=none\n"
        "Next Action: gdd-subagent-driven-implementation\n" + extra_state,
        encoding="utf-8",
    )
    steering.joinpath("requirements.md").write_text(
        "### 一言\ncross session fixture\n\n## 受入条件\n- AC-1: x\n", encoding="utf-8")
    steering.joinpath("tasklist.md").write_text(_TASKLIST, encoding="utf-8")


def _run(repo: Path) -> str:
    env = os.environ.copy()
    for var in ("CLAUDE_CODE_SESSION_ID", "GDD_PLUGIN_ROOT", "CLAUDE_PLUGIN_ROOT"):
        env.pop(var, None)
    r = subprocess.run(["bash", str(HOOK)], cwd=repo,
                       input=json.dumps({"prompt": "続きをお願い"}),
                       capture_output=True, text=True, env=env)
    return r.stdout


class CrossSessionContextTests(unittest.TestCase):
    def test_injects_last_handoff_summary(self) -> None:
        """別セッションでも「何をしていたか」が復元される"""
        with tempfile.TemporaryDirectory(prefix="gdd-xs-") as tmp:
            repo = Path(tmp)
            _setup(repo, "Last Handoff Summary: AC-1 の境界値テストが残り\n")
            out = _run(repo)
            self.assertIn(
                "AC-1 の境界値テストが残り", out,
                f"a fresh session must recover what was in progress: {out!r}",
            )

    def test_injects_approved_direction(self) -> None:
        """承認された方針が復元される（別セッションで方針を取り違えない）"""
        with tempfile.TemporaryDirectory(prefix="gdd-xs-") as tmp:
            repo = Path(tmp)
            _setup(repo, "Approved Direction: 既存 hook を拡張し新規 hook は足さない\n")
            out = _run(repo)
            self.assertIn("既存 hook を拡張し新規 hook は足さない", out)

    def test_absent_fields_are_omitted(self) -> None:
        """未記入ならラベルごと省く（既存の注入内容を壊さない）"""
        with tempfile.TemporaryDirectory(prefix="gdd-xs-") as tmp:
            repo = Path(tmp)
            _setup(repo)
            out = _run(repo)
            self.assertNotIn("Last Handoff Summary", out)
            self.assertNotIn("Approved Direction", out)
            # 既存項目は維持されること
            self.assertIn("Next Action", out)

    def test_output_stays_valid_json(self) -> None:
        """自由記述に改行や引用符が入っても JSON が壊れない"""
        with tempfile.TemporaryDirectory(prefix="gdd-xs-") as tmp:
            repo = Path(tmp)
            _setup(repo, 'Last Handoff Summary: "quoted" と \\ バックスラッシュ入り\n')
            out = _run(repo)
            payload = json.loads(out)
            self.assertEqual(
                payload["hookSpecificOutput"]["hookEventName"], "UserPromptSubmit")


if __name__ == "__main__":
    unittest.main()
