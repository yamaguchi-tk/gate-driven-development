"""SessionStart は post-merge continuation marker を読まない・消さない契約テスト。

marker（`.claude/gdd-post-merge-continuation.json`）は、PR を作った時点で
`status: "pending_manual_merge"`（＝マージ待ち）として書かれる。書き手は
`gdd_stop_hook.py` の `write_post_merge_continuation` で、置き場は
`<project root>/.claude/` である。読み手は 2 つある。

- `run-user-prompt-submit-hook.sh`: 「マージした」等の cue で `[gdd:post-merge-continuation]` を注入する
- `gdd_stop_hook.py` の `maybe_block_incomplete_post_merge_continuation`:
  post-merge の確認が済むまで早期停止を止め、済んだら marker を消す

SessionStart にも 3 つ目の読み手があり、`${HOME}/.claude/` を見て
`[gdd:post-merge-auto-continue]`（`/gdd-dev resume`）を注入し、marker を消していた。
project root が `${HOME}` と一致する起動を除いて書き手の出力先と読み手のパスは一致せず、
実データでは一度も注入されていなかった（2026-09-22 実測）。
パスを project root に合わせると、SessionStart が marker を消して上の 2 つの読み手を
入口ごと無効にする。marker には「マージ済みか」の情報が無く、PR が open の間ずっと
resume を注入することにもなるため、SessionStart の読み手を撤去した。

ここでは、HOME 側・project root 側のどちらに marker があっても、SessionStart が
注入も削除もしないことを固定する。
"""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from _paths import PLUGIN_ROOT as ROOT

HOOK = ROOT / "hooks" / "scripts" / "run-session-start-hook.sh"
MARKER_FILE = "gdd-post-merge-continuation.json"
SEED = {
    "session_id": "s-1",
    "created_at_epoch": 1758400000,
    "tasklist_path": "/tmp/.steering/20260922-task/tasklist.md",
    "pr_url": "https://github.com/owner/repo/pull/1",
    "status": "pending_manual_merge",
    "next_task_hint": "Task 2: implement X",
    "steering_dir": "/tmp/.steering/20260922-task",
}


class NoPostMergeSeedTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="gdd-no-post-merge-")
        self.addCleanup(self._tmp.cleanup)
        tmp = Path(os.path.realpath(self._tmp.name))
        self.home = tmp / "home"
        (self.home / ".claude").mkdir(parents=True)
        self.repo = tmp / "repo"
        (self.repo / ".claude").mkdir(parents=True)
        subprocess.run(["git", "init", "-q"], cwd=self.repo, check=True, capture_output=True)

    def _write_marker(self, root: Path) -> Path:
        marker = root / ".claude" / MARKER_FILE
        marker.write_text(json.dumps(SEED, ensure_ascii=False), encoding="utf-8")
        return marker

    def _run(self, extra_env: dict[str, str] | None = None) -> str:
        env = os.environ.copy()
        env["HOME"] = str(self.home)
        env["CLAUDE_PLUGIN_ROOT"] = str(ROOT)
        for leaked in ("GDD_STEERING_DIR", "GDD_HOOK_STATE_DIR",
                       "GDD_MAX_AUTO_CYCLES", "CLAUDE_CODE_SESSION_ID", "GDD_WORKTREES_ROOT"):
            env.pop(leaked, None)
        env.update(extra_env or {})
        result = subprocess.run(
            ["bash", str(HOOK)], input="", capture_output=True, text=True,
            env=env, cwd=str(self.repo), timeout=120,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        lines = [line for line in result.stdout.splitlines() if line.strip()]
        self.assertEqual(len(lines), 1, lines)
        return json.loads(lines[0])["hookSpecificOutput"]["additionalContext"]

    def _assert_untouched(self, additional: str, marker: Path) -> None:
        self.assertNotIn("[gdd:post-merge-auto-continue]", additional)
        self.assertNotIn("Task 2: implement X", additional)
        self.assertNotIn("/gdd-dev resume", additional)
        self.assertTrue(marker.exists(), f"{marker} must survive SessionStart")
        self.assertEqual(json.loads(marker.read_text(encoding="utf-8")), SEED)
        # 肯定側のアンカー。これが無いと、将来 SessionStart が別の理由で早期 exit する枝を
        # 持ったときに、上の assertNotIn 3 本が空振りのまま通る
        self.assertIn("gate-driven-development is available.", additional)

    def test_home_marker_is_not_injected_or_deleted(self) -> None:
        # 撤去前は、この経路だけが注入し、marker を rm -f で消していた（RED を確認した入力）
        marker = self._write_marker(self.home)

        self._assert_untouched(self._run(), marker)

    def test_project_root_marker_is_not_injected_or_deleted(self) -> None:
        # 書き手が実際に置く場所。撤去前の hook もここは読まないので、この 1 本は
        # RED にならない。読む側を再導入したら落ちる pin として置く。ここを読んで消すと、
        # UserPromptSubmit の cue 注入と stop hook の post-merge block lane が marker ごと失われる
        marker = self._write_marker(self.repo)

        self._assert_untouched(self._run(), marker)

    def test_seed_file_env_override_is_not_consumed(self) -> None:
        # 撤去前のテスト経路（GDD_POST_MERGE_SEED_FILE）も、もう効かない（RED を確認した入力）
        marker = self._write_marker(self.repo)

        additional = self._run(extra_env={"GDD_POST_MERGE_SEED_FILE": str(marker)})

        self._assert_untouched(additional, marker)


if __name__ == "__main__":
    unittest.main()
