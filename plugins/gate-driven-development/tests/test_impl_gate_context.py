"""impl-gate-context.py の振る舞いテスト。

implementation-gating の runner は、Steps ごとに tasklist.md・state.md・handoff・
worklog.md の別の節を読み直していた（2026-10-02〜10-16 の実測で、1 回の gate で何度も）。
script はその節を行番号つきで 1 回に出す。必須の節（Current Task・Pending Tasks）を
特定できないときは、「なし」と出さずに exit 1 で止め、runner を従来の読み方に戻す
（Pending Tasks を取りこぼすと、残りの task があるのに completion へ進む）。
"""
from __future__ import annotations

import importlib.util
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "hooks" / "scripts"))

from _paths import PLUGIN_ROOT  # noqa: E402
from lib import done_guard  # noqa: E402

SCRIPT = PLUGIN_ROOT / "scripts" / "impl-gate-context.py"
SKILL = PLUGIN_ROOT / "skills" / "gdd-implementation-gating" / "SKILL.md"

TASKLIST = """\
# tasklist
- Approved Direction: HEADER-MARKER

## Execution Plan
- sequential

## Implementation Reviewer Selection
- gdd-implementation-reviewer: selected | reason: always | updated_at: 2026-10-16T10:00:00+09:00

## Review Status
- gdd-implementation-reviewer: pending | evidence: none

## Current Task
### Task: T-2 二つ目
- Gate Rounds: 1
#### RED Evidence
- Worktree: /tmp/wt

## Pending Tasks
- T-3 | AC-3 | 三つ目

## Completed Tasks
### Task: T-1 一つ目
#### Attempts
- Attempt 1: changes_requested
- [Review Calibration] implementation-reviewer checklist / 命名: invalid
  - finding: 名前が紛らわしい
  - was_valid: false
- [Review Calibration] implementation-reviewer checklist / 境界: valid
  - finding: VALID-TRUE-MARKER
  - was_valid: true
- Attempt 2: approved
### Task 4: 採番つき
- Task: 箇条書きの task
- T5 | AC-5 | 表の task
完了の長い記録 COMPLETED-BODY-MARKER

## Refactor Gate Status
- pending

## Verification
- なし
"""

#: Step 11 が起点と同じ時点で書く Completed Tasks の数（TASKLIST の Completed Tasks は 4 task）
COMPLETED_AT_BASE = "- Impl Gate Completed: 4\n"
STATE = """\
# state
- Task Size: standard
- Route In Progress: implementation_fix_only
- Active Worktree Path: /tmp/wt
"""

LEARNED = """\
# learned

## Rejected Alternatives
- 命名の指摘は false positive が多い

## Other
- OTHER-MARKER
"""

WORKLOG = "".join(f"- line {i}\n" for i in range(1, 31))

SMI = """\
# tdd handoff
### State Machine Impact（実装由来の波及）
- **ADR 起票**: 不要
- **Routing 提案**: `gdd-implementation-gating`
"""

PREVIOUS_GATE = """\
# implementation_gating
## Round 1
- 判定: changes_requested
```bash
# FENCED-COMMENT-MARKER
```
本文 PREVIOUS-BODY-MARKER
"""


def _write_steering(root: Path, tasklist: str = TASKLIST, *, with_optional: bool = True) -> Path:
    steering = root / ".steering" / "task"
    (steering / "handoff").mkdir(parents=True)
    (steering / "tasklist.md").write_text(tasklist, encoding="utf-8")
    (steering / "state.md").write_text(STATE, encoding="utf-8")
    if with_optional:
        # 置き場の正本（references/cross-task-learning.md）: worktree 直下の docs/
        (root / "docs").mkdir()
        (root / "docs" / "learned-patterns.md").write_text(LEARNED, encoding="utf-8")
        (steering / "worklog.md").write_text(WORKLOG, encoding="utf-8")
        (steering / "handoff" / "tdd.md").write_text(SMI, encoding="utf-8")
        (steering / "handoff" / "implementation_gating.md").write_text(PREVIOUS_GATE, encoding="utf-8")
    return steering


def _run(steering: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--steering-dir", str(steering)],
        capture_output=True,
        text=True,
        timeout=30,
    )


class ImplGateContextTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_prints_gate_sections_with_line_numbers(self) -> None:
        result = _run(_write_steering(self.root))
        self.assertEqual(result.returncode, 0, result.stderr)
        out = result.stdout
        # Current Task の全文（Gate Rounds・RED Evidence の Worktree 行）を行番号つきで出す
        self.assertIn("14\t### Task: T-2 二つ目", out)
        self.assertIn("15\t- Gate Rounds: 1", out)
        self.assertIn("17\t- Worktree: /tmp/wt", out)
        self.assertIn("20\t- T-3 | AC-3 | 三つ目", out)
        self.assertIn("gdd-implementation-reviewer: selected", out)
        self.assertIn("gdd-implementation-reviewer: pending | evidence: none", out)
        self.assertIn("39\t- pending", out)  # Refactor Gate Status 節
        # 冒頭の Header と Execution Plan、全節の索引
        self.assertIn("2\t- Approved Direction: HEADER-MARKER", out)
        self.assertIn("5\t- sequential", out)
        self.assertIn("41〜42\t## Verification", out)

    def test_completed_tasks_only_headings_and_calibration_entries(self) -> None:
        out = _run(_write_steering(self.root)).stdout
        self.assertIn("23\t### Task: T-1 一つ目", out)
        self.assertIn("[Review Calibration] implementation-reviewer checklist / 命名", out)
        self.assertIn("  - was_valid: false", out)
        self.assertNotIn("COMPLETED-BODY-MARKER", out)
        # was_valid=false の entry だけを出す
        self.assertNotIn("VALID-TRUE-MARKER", out)
        # 実データの task 行の 3 形
        self.assertIn("\t### Task 4: 採番つき", out)
        self.assertIn("\t- Task: 箇条書きの task", out)
        self.assertIn("\t- T5 | AC-5 | 表の task", out)

    def test_state_learned_worklog_and_handoff(self) -> None:
        out = _run(_write_steering(self.root)).stdout
        self.assertIn("Route In Progress: implementation_fix_only", out)
        self.assertIn("Active Worktree Path: /tmp/wt", out)
        self.assertIn("Task Size: standard", out)
        self.assertIn("命名の指摘は false positive が多い", out)
        self.assertNotIn("OTHER-MARKER", out)
        # worklog は末尾 20 行
        self.assertIn("- line 30", out)
        self.assertIn("- line 11", out)
        self.assertNotIn("- line 10\n", out)
        # State Machine Impact の block
        self.assertIn("**Routing 提案**: `gdd-implementation-gating`", out)
        # 前回の gate の handoff は見出しと行番号だけ
        self.assertIn("## Round 1", out)
        self.assertIn("- 判定: changes_requested", out)
        self.assertNotIn("PREVIOUS-BODY-MARKER", out)
        self.assertNotIn("FENCED-COMMENT-MARKER", out)

    def test_optional_files_absent_are_reported_not_failed(self) -> None:
        result = _run(_write_steering(self.root, with_optional=False))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("learned-patterns.md: ファイルが無い", result.stdout)

    def test_missing_pending_tasks_section_exits_1(self) -> None:
        tasklist = TASKLIST.replace("## Pending Tasks\n- T-3 | AC-3 | 三つ目\n", "")
        result = _run(_write_steering(self.root, tasklist))
        self.assertEqual(result.returncode, 1)
        self.assertIn("Pending Tasks", result.stderr)
        self.assertEqual(result.stdout, "")

    def test_reopened_pending_section_is_not_dropped(self) -> None:
        # done guard は `## Pending Tasks（再オープン）` も Pending の節と読む（前方一致）
        tasklist = TASKLIST.replace(
            "## Pending Tasks\n- T-3 | AC-3 | 三つ目\n",
            "## Pending Tasks\n- なし\n\n## Pending Tasks（再オープン）\n### Task 1: 一つ目\n",
        )
        _completed, pending, _current, _name = done_guard._tally_task_sections(tasklist.splitlines())
        self.assertGreater(pending, 0)
        result = _run(_write_steering(self.root, tasklist))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("\t### Task 1: 一つ目", result.stdout)
        self.assertIn("## Pending Tasks（再オープン）", result.stdout)

    def test_open_task_mismatch_with_done_guard_count_exits_1(self) -> None:
        # 見出しの読み方が done guard 側とずれて task を落としたら止める
        spec = importlib.util.spec_from_file_location("impl_gate_context", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        lines, closed, spans = module._sections(TASKLIST)
        current = module._named(lines, spans, "Current Task")
        with self.assertRaises(module.ContextError):
            module._check_open_tasks(TASKLIST, lines, closed, current)  # Pending の節を渡し忘れた形
        module._check_open_tasks(TASKLIST, lines, closed, current + module._named(lines, spans, "Pending Tasks"))

    def test_section_heading_with_suffix_is_read(self) -> None:
        tasklist = TASKLIST.replace("## Completed Tasks", "## Completed Tasks（1 件）")
        result = _run(_write_steering(self.root, tasklist))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("[Review Calibration] implementation-reviewer checklist / 命名", result.stdout)

    def test_missing_reviewer_selection_exits_1(self) -> None:
        tasklist = TASKLIST.replace("## Implementation Reviewer Selection", "## 別の節")
        result = _run(_write_steering(self.root, tasklist))
        self.assertEqual(result.returncode, 1)
        self.assertIn("Implementation Reviewer Selection", result.stderr)

    def test_pending_tasks_heading_only_inside_fence_exits_1(self) -> None:
        tasklist = TASKLIST.replace(
            "## Pending Tasks\n- T-3 | AC-3 | 三つ目\n",
            "```markdown\n## Pending Tasks\n- なし\n```\n",
        )
        result = _run(_write_steering(self.root, tasklist))
        self.assertEqual(result.returncode, 1)
        self.assertIn("Pending Tasks", result.stderr)

    def test_duplicate_current_task_prints_both(self) -> None:
        # done guard は前方一致した節を足して数える。script も両方を出す
        tasklist = TASKLIST.replace("## Pending Tasks", "## Current Task\n### Task: T-9 古い\n\n## Pending Tasks")
        result = _run(_write_steering(self.root, tasklist))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("\t### Task: T-2 二つ目", result.stdout)
        self.assertIn("\t### Task: T-9 古い", result.stdout)

    def test_unclosed_fence_exits_1(self) -> None:
        tasklist = TASKLIST.replace("## Completed Tasks", "```\n## Completed Tasks")
        result = _run(_write_steering(self.root, tasklist))
        self.assertEqual(result.returncode, 1)
        self.assertIn("fence", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_missing_tasklist_exits_1_without_traceback(self) -> None:
        steering = _write_steering(self.root)
        (steering / "tasklist.md").unlink()
        result = _run(steering)
        self.assertEqual(result.returncode, 1)
        self.assertIn("tasklist.md", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_review_line_runs_without_the_declaration(self) -> None:
        # 入口: gate はこの固定行で review を外すかを決める（正本: references/task-breakdown-steps.md § Judgment Change）
        out = _run(_write_steering(self.root)).stdout
        self.assertIn("impl-gate-review: run", out)
        self.assertNotIn("impl-gate-review: skip", out)

    def _git_steering(self, *, base: bool = True, extra: str = "") -> tuple[Path, str]:
        # 入口から: worktree の git の差分を、state.md の Impl Gate Base を起点に読む
        tasklist = TASKLIST.replace("- Gate Rounds: 1\n", "- Judgment Change: no\n- Files: src/a.py\n")
        steering = _write_steering(self.root, tasklist)
        git = ["git", "-C", str(self.root), "-c", "user.name=t", "-c", "user.email=t@example.com"]
        subprocess.run([*git, "init", "-q"], check=True)
        (self.root / "src").mkdir()
        (self.root / "src" / "a.py").write_text("x = 1\n", encoding="utf-8")
        subprocess.run([*git, "add", "-A"], check=True)
        subprocess.run([*git, "commit", "-qm", "base"], check=True)
        sha = subprocess.run([*git, "rev-parse", "HEAD"], check=True, capture_output=True, text=True).stdout.strip()
        (self.root / "src" / "a.py").write_text("x = 2\n", encoding="utf-8")
        (steering / "state.md").write_text(STATE + "- Task Note: 起点が変わっても steering の変更は数えない\n", encoding="utf-8")
        if extra:
            (self.root / extra).parent.mkdir(parents=True, exist_ok=True)
            (self.root / extra).write_text("y = 1\n", encoding="utf-8")
        if base:
            (steering / "state.md").write_text(STATE + f"- Impl Gate Base: {sha}\n{COMPLETED_AT_BASE}", encoding="utf-8")
        return steering, sha

    def _state_with(self, steering: Path, sha: str, completed: str) -> None:
        (steering / "state.md").write_text(STATE + f"- Impl Gate Base: {sha}\n{completed}", encoding="utf-8")

    def test_review_line_runs_without_the_completed_count(self) -> None:
        # 判定できないとき: 起点はあるのに Impl Gate Completed が無い（書き忘れ）
        steering, sha = self._git_steering()
        self._state_with(steering, sha, "")
        out = _run(steering).stdout
        self.assertIn("impl-gate-review: run", out)
        self.assertNotIn("impl-gate-review: skip", out)

    def test_review_line_runs_for_an_unreadable_completed_count(self) -> None:
        steering, sha = self._git_steering()
        self._state_with(steering, sha, "- Impl Gate Completed: four\n")
        out = _run(steering).stdout
        self.assertIn("impl-gate-review: run", out)
        self.assertNotIn("impl-gate-review: skip", out)

    def test_review_line_runs_inside_a_parallel_batch_without_an_execution_plan(self) -> None:
        # 並列の batch の最後の 1 task: Execution Plan を見出しでない形で書いても、起点の後に兄弟の task が
        # Completed へ移ったので数が合わない（4 つのうち 1 つは起点の後に移った）
        steering, sha = self._git_steering()
        tasklist = (steering / "tasklist.md").read_text(encoding="utf-8")
        (steering / "tasklist.md").write_text(tasklist.replace("## Execution Plan\n- sequential\n", "**Execution Plan**\n- Mode: parallel\n"), encoding="utf-8")
        self._state_with(steering, sha, "- Impl Gate Completed: 3\n")
        out = _run(steering).stdout
        self.assertIn("impl-gate-review: run", out)
        self.assertNotIn("impl-gate-review: skip", out)

    def test_review_line_counts_zero_before_the_first_gate_unit(self) -> None:
        # 起点も欄も無い最初の gate 単位は 0 とみなす（起点は default branch との merge-base）
        steering, sha = self._git_steering(base=False)
        git = ["git", "-C", str(self.root)]
        subprocess.run([*git, "update-ref", "refs/remotes/origin/HEAD", sha], check=True)
        tasklist = (steering / "tasklist.md").read_text(encoding="utf-8")
        head, _sep, rest = tasklist.partition("## Completed Tasks\n")
        (steering / "tasklist.md").write_text(head + "## Completed Tasks\n- なし\n\n## Refactor Gate Status" + rest.partition("## Refactor Gate Status")[2], encoding="utf-8")
        result = _run(steering)
        self.assertIn(f"impl-gate-review: skip T-2 二つ目（差分の起点 {sha}）\n", result.stdout)
        tasklist = (steering / "tasklist.md").read_text(encoding="utf-8")
        (steering / "tasklist.md").write_text(tasklist.replace("## Completed Tasks\n- なし\n", "## Completed Tasks\n### Task: T-1 一つ目\n"), encoding="utf-8")
        out = _run(steering).stdout
        self.assertIn("impl-gate-review: run", out)
        self.assertNotIn("impl-gate-review: skip", out)

    def test_review_line_skips_a_task_declared_no(self) -> None:
        steering, sha = self._git_steering()
        result = _run(steering)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(f"impl-gate-review: skip T-2 二つ目（差分の起点 {sha}）\n", result.stdout)

    def test_review_line_runs_for_a_file_outside_the_declaration(self) -> None:
        # untracked のファイルも差分に入れる
        out = _run(self._git_steering(extra="hooks/guard.py")[0]).stdout
        self.assertIn("impl-gate-review: run", out)
        self.assertNotIn("impl-gate-review: skip", out)

    def test_review_line_runs_when_the_declared_files_are_not_in_the_diff(self) -> None:
        # 並列の batch で起点が task の変更より後に進んだ形: 宣言した src/a.py が差分に出ない
        steering, _sha = self._git_steering()
        git = ["git", "-C", str(self.root), "-c", "user.name=t", "-c", "user.email=t@example.com"]
        subprocess.run([*git, "commit", "-qam", "task"], check=True)
        head = subprocess.run([*git, "rev-parse", "HEAD"], check=True, capture_output=True, text=True).stdout.strip()
        (steering / "state.md").write_text(STATE + f"- Impl Gate Base: {head}\n{COMPLETED_AT_BASE}", encoding="utf-8")
        out = _run(steering).stdout
        self.assertIn("impl-gate-review: run", out)
        self.assertNotIn("impl-gate-review: skip", out)

    def test_review_line_runs_for_a_parallel_execution_plan(self) -> None:
        # 並列の batch の最後の 1 task: Current Task に 1 task しか残らなくても、Execution Plan で外さない
        steering, _sha = self._git_steering()
        tasklist = (steering / "tasklist.md").read_text(encoding="utf-8")
        (steering / "tasklist.md").write_text(tasklist.replace("## Execution Plan\n- sequential\n", "## Execution Plan\n- Mode: parallel\n- Batch 1: T-2, T-9\n"), encoding="utf-8")
        out = _run(steering).stdout
        self.assertIn("impl-gate-review: run", out)
        self.assertNotIn("impl-gate-review: skip", out)

    def test_review_line_runs_without_a_resolvable_base(self) -> None:
        steering, _sha = self._git_steering()
        (steering / "state.md").write_text(STATE + "- Impl Gate Base: 0123456789abcdef0123456789abcdef01234567\n", encoding="utf-8")
        out = _run(steering).stdout
        self.assertIn("impl-gate-review: run", out)
        self.assertNotIn("impl-gate-review: skip", out)

    def test_review_line_runs_after_a_changes_requested(self) -> None:
        # 差し戻しを受けた gate 単位（Gate Rounds がある）の再 gate は、宣言によらず review を回す
        tasklist = TASKLIST.replace("- Gate Rounds: 1\n", "- Gate Rounds: 1\n- Judgment Change: no\n")
        out = _run(_write_steering(self.root, tasklist)).stdout
        self.assertIn("impl-gate-review: run", out)
        self.assertNotIn("impl-gate-review: skip", out)

    def test_review_line_runs_for_express(self) -> None:
        steering, sha = self._git_steering()
        (steering / "state.md").write_text(STATE.replace("standard", "quick (express)") + f"- Impl Gate Base: {sha}\n{COMPLETED_AT_BASE}", encoding="utf-8")
        out = _run(steering).stdout
        self.assertIn("impl-gate-review: run（Task Size=quick (express)）", out)
        self.assertNotIn("impl-gate-review: skip", out)

    def test_scripts_named_by_skill_exist(self) -> None:
        # 入口: runner が読む SKILL.md が名指す plugin の script が、実在するファイルに解決する
        text = SKILL.read_text(encoding="utf-8")
        names = re.findall(r"\$\{CLAUDE_PLUGIN_ROOT\}/scripts/([\w.-]+)", text)
        self.assertIn(SCRIPT.name, names)
        for name in names:
            self.assertTrue((PLUGIN_ROOT / "scripts" / name).is_file(), name)


if __name__ == "__main__":
    unittest.main()
