"""`Status` と compact 自動復帰の印を廃したことの契約テスト。

背景:
`Status` は PreCompact hook が書き（`paused`）、SessionStart が読む（compact 自動復帰の条件）
hook 所有の field だった。compact 自動復帰は 2026-09-28 に廃した（compaction の hook は main と
subagent の compaction を見分けられない）。今は hook が書きも読みもしない。

方針: **一覧として記録するが enforce しない**。既存の state.md に残る印の行は害が無い。
実データでは LLM が `Status` を自由記述していた（`Requirements Drafted` など）。write hook に
deny category を足すと、既存の free-text `Status` を持つファイルで `MAX_CONSECUTIVE_DENIES` の
escape hatch が連発してノイズになるため追加しない。
"""
from __future__ import annotations

import io
import contextlib
import importlib.util
import json
import sys
import unittest

from _paths import PLUGIN_ROOT
WRITE_HOOK = PLUGIN_ROOT / "hooks" / "scripts" / "validate-steering-write.py"


class StatusEnforcementBoundaryTests(unittest.TestCase):
    """free-text `Status` を write hook で deny しない方針を固定する。

    2 つ目の deny category を既存 23 ファイルに当てると escape hatch が連発する。
    方針が黙って変わったら検出する。
    """

    def test_write_hook_does_not_deny_free_text_status(self) -> None:
        spec = importlib.util.spec_from_file_location("vsw_status", WRITE_HOOK)
        mod = importlib.util.module_from_spec(spec)
        sys.modules["vsw_status"] = mod
        spec.loader.exec_module(mod)

        payload = {
            "tool_name": "Write",
            "tool_input": {
                "file_path": "/tmp/.steering/20260728-x/state.md",
                "content": (
                    "Resume From: gdd-task-breakdown\n"
                    "Human Check Status: approved\n"
                    "Route In Progress: none\n"
                    "Started At: 2026-07-28T00:00:00Z\n"
                    "- Status: Requirements Drafted\n"
                ),
            },
        }
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr), contextlib.redirect_stdout(io.StringIO()):
            original, sys.stdin = sys.stdin, io.StringIO(json.dumps(payload))
            try:
                code = mod.main()
            finally:
                sys.stdin = original
        self.assertEqual(
            code, 0,
            f"free-text Status must not be denied (documented, not enforced): {stderr.getvalue()}",
        )


if __name__ == "__main__":
    unittest.main()
