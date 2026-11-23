"""learned-patterns.md を読む script が、書く側と同じ置き場を読むことのテスト。

書く側（completion-check の Post-Completion Learning）は worktree 直下の
`docs/learned-patterns.md` に書く（正本: references/cross-task-learning.md）。
読む側の impl-gate-context.py（implementation-gating Step 5）と
collect-gdd-telemetry.py は `.steering/` の中を探していて、書いた記録を読めなかった。
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
IMPL_GATE_CONTEXT = PLUGIN_ROOT / "scripts" / "impl-gate-context.py"
TELEMETRY = PLUGIN_ROOT / "scripts" / "collect-gdd-telemetry.py"

TASKLIST = """\
# Tasklist

## Current Task
- T-1 | AC-1 | 一つ目

## Pending Tasks
- なし

## Implementation Reviewer Selection
- なし
"""

DOCS_LEARNED = """\
# Learned Patterns

## Rejected Alternatives
- DOCS-MARKER: 命名の指摘は false positive が多い
- DOCS-MARKER-2
"""

STEERING_LEARNED = """\
# Learned Patterns

## Rejected Alternatives
- STEERING-MARKER
- STEERING-MARKER-2
- STEERING-MARKER-3
- STEERING-MARKER-4
"""


def _worktree(root: Path, *, docs: bool, steering_copy: bool) -> Path:
    steering = root / ".steering" / "task"
    (steering / "handoff").mkdir(parents=True)
    (steering / "tasklist.md").write_text(TASKLIST, encoding="utf-8")
    (steering / "state.md").write_text("# State\n- Task Size: standard\n", encoding="utf-8")
    if docs:
        (root / "docs").mkdir()
        (root / "docs" / "learned-patterns.md").write_text(DOCS_LEARNED, encoding="utf-8")
    if steering_copy:
        # 置き場ではない場所（task の steering 直下と、.steering/ 直下）
        (steering / "learned-patterns.md").write_text(STEERING_LEARNED, encoding="utf-8")
        (root / ".steering" / "learned-patterns.md").write_text(STEERING_LEARNED, encoding="utf-8")
    return steering


def _impl_gate_context(steering: Path) -> str:
    result = subprocess.run(
        [sys.executable, str(IMPL_GATE_CONTEXT), "--steering-dir", str(steering)],
        capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 0, result.stderr
    return result.stdout


def _telemetry_entries(root: Path) -> int:
    result = subprocess.run(
        [sys.executable, str(TELEMETRY), "--root", str(root), "--format", "json"],
        capture_output=True, text=True, timeout=120,
    )
    assert result.returncode == 0, result.stderr
    tasks = json.loads(result.stdout)["tasks"]
    assert len(tasks) == 1, tasks
    return tasks[0]["learned_patterns_entries"]


class ImplGateContextTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_reads_docs_learned_patterns(self) -> None:
        out = _impl_gate_context(_worktree(self.root, docs=True, steering_copy=True))
        self.assertIn("DOCS-MARKER: 命名の指摘は false positive が多い", out)
        self.assertNotIn("STEERING-MARKER", out)

    def test_steering_copy_alone_is_not_read(self) -> None:
        out = _impl_gate_context(_worktree(self.root, docs=False, steering_copy=True))
        self.assertNotIn("STEERING-MARKER", out)
        self.assertIn("learned-patterns.md: ファイルが無い", out)
        self.assertIn(str(Path("docs") / "learned-patterns.md"), out)


class TelemetryTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_counts_docs_learned_patterns(self) -> None:
        _worktree(self.root, docs=True, steering_copy=True)
        self.assertEqual(_telemetry_entries(self.root), 2)

    def test_steering_copy_alone_is_not_counted(self) -> None:
        _worktree(self.root, docs=False, steering_copy=True)
        self.assertEqual(_telemetry_entries(self.root), 0)


if __name__ == "__main__":
    unittest.main()
