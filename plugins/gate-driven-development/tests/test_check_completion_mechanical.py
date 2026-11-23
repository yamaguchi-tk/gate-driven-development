"""`scripts/check-completion-mechanical.py`（completion-check の機械検査）のテスト。

実行: `python3 -m pytest plugins/gate-driven-development/tests/test_check_completion_mechanical.py -q`

steering と差分に変異を入れ、スクリプトの行の状態と exit code を見る。行の述語は既存の実装
（done guard・check-gate-ledger.sh・lint-ac.py・gdd-codebase-health.py）のものなので、
同じ変異で既存の実装も止めることを一部で突き合わせる。
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from _paths import PLUGIN_ROOT
from _git_fixture import init_repo

SCRIPT = PLUGIN_ROOT / "scripts" / "check-completion-mechanical.py"
LEDGER = PLUGIN_ROOT / "scripts" / "check-gate-ledger.sh"
SLUG = "20261021-mechanical"
NOT_OK = {"missing", "invalid", "error"}
REQUIREMENTS = ("reviewed-by", "remaining-tasks", "route-in-progress", "ac-coverage", "codebase-health",
                "follow-up-stage", "ac-ids")
LANE_HEADER = (
    "| Pending Stage ID | Origin Steering | Base Branch | Base Commit | Next Planned Stage | Follow-up Trigger "
    "| Stage Files | In-flight PR | Continuation Mode | Tracking Destination | Human Recheck |\n"
    "|---|---|---|---|---|---|---|---|---|---|---|\n"
)


def lane_row(base_branch: str = "main", tracking: str = "new steering seed") -> str:
    return (f"| S-2 | .steering/x | {base_branch} | abc1234 | S-2: 後続 | post-merge | a.py | - | manual "
            f"| {tracking} | not required + 理由 |\n")


def ledger_row(ac: str = "AC-1", command: str = "`pytest t.py` -> pass", status: str = "verified") -> str:
    return f"| {ac} | Task 1 | {command} | {status} | gdd-completion-check @ 2026-10-21 | なし |\n"


LEDGER_HEADER = (
    "## AC Trace Ledger\n\n| AC ID | 対応タスク | 検証コマンド/結果 | status | last verified at/phase | 未解決リスク |\n"
    "|---|---|---|---|---|---|\n"
)


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), *args], check=True, capture_output=True, text=True
    ).stdout.strip()


class Fixture:
    """全項目がそろった standard の steering と、feature branch の差分を作る。"""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.repo = root / "repo"
        self.repo.mkdir()
        init_repo(self.repo, branch="main")
        _git(self.repo, "switch", "-q", "-c", "feature")
        (self.repo / "app.py").write_text("def f():\n    return 1\n", encoding="utf-8")
        _git(self.repo, "add", "app.py")
        _git(self.repo, "commit", "-q", "-m", "add app")
        self.steering = self.repo / ".steering" / SLUG
        self.steering.mkdir(parents=True)
        self.state = {
            "Task Size": "standard",
            "Route In Progress": "none",
        }
        self.reviewed_by = "- Reviewed by: gdd-implementation-reviewer (approved)"
        self.pending = "- なし"
        self.requirements_acs = ["AC-1"]
        self.verification_acs = ["AC-1"]
        self.covers = "- Covers AC: AC-1"
        self.lane: str | None = None  # requirements.md の末尾に足す Planned Follow-up Stage Lane の節
        self.ledger: str | None = None  # ac-ledger.md の中身（AC Trace Ledger の専用ファイル）
        self.tasklist_extra: str | None = None  # tasklist.md の末尾に足す行（旧来の置き場所の Ledger など）
        self.plan: str | None = None  # requirements.md の末尾に足す Implementation Sequence Plan の節
        self.requirements_extra = ""  # requirements.md の受入条件の節の末尾に足す行

    def write(self) -> None:
        self.steering.joinpath("state.md").write_text(
            "".join(f"{k}: {v}\n" for k, v in self.state.items() if v is not None),
            encoding="utf-8",
        )
        self.steering.joinpath("requirements.md").write_text(
            "# Requirements\n\n## 受入条件\n\n"
            + "".join(f"- {ac}: 条件\n" for ac in self.requirements_acs)
            + self.requirements_extra
            + (f"\n## Implementation Sequence Plan\n\n{self.plan}" if self.plan is not None else "")
            + (f"\n## Planned Follow-up Stage Lane\n\n{self.lane}" if self.lane is not None else ""),
            encoding="utf-8",
        )
        reviewed = f"{self.reviewed_by}\n" if self.reviewed_by else ""
        rows = "".join(f"| method=ac:{ac} | pending | - | - |\n" for ac in self.verification_acs)
        self.steering.joinpath("tasklist.md").write_text(
            "# Task List\n\nNext Action: gdd-completion-check\n\n"
            "## Current Task\n\n- なし\n\n"
            f"## Pending Tasks\n\n{self.pending}\n\n"
            f"## Completed Tasks\n\n### Task 1: 一つ目\n\n{self.covers}\n"
            f"{reviewed}\n"
            "## Verification\n\n| method | status | evidence | notes |\n|---|---|---|---|\n"
            f"{rows}"
            + (f"\n{self.tasklist_extra}" if self.tasklist_extra is not None else ""),
            encoding="utf-8",
        )
        if self.ledger is not None:
            self.steering.joinpath("ac-ledger.md").write_text(self.ledger, encoding="utf-8")

    def run(self, *extra: str, steering: Path | None = None) -> tuple[int, list[tuple[str, str, str, str]], str]:
        args = ["--steering", str(steering or self.steering), "--root", str(self.repo), "--base", "main"]
        result = subprocess.run(
            [sys.executable, str(SCRIPT), *args, *extra], cwd=self.repo,
            capture_output=True, text=True, env={**os.environ, "CLAUDE_PLUGIN_ROOT": str(PLUGIN_ROOT)},
            check=False,
        )
        rows = []
        for line in result.stdout.splitlines():
            parts = line.split("\t")
            assert len(parts) == 4, line
            rows.append((parts[0], parts[1], parts[2], parts[3]))
        return result.returncode, rows, result.stderr


def _statuses(rows, requirement: str) -> list[str]:
    return [status for status, req, _gate, _detail in rows if req == requirement]


class CheckCompletionMechanicalTests(unittest.TestCase):
    def _run(self, mutate=None):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        fx = Fixture(Path(tmp.name))
        if mutate:
            mutate(fx)
        fx.write()
        return fx, *fx.run()

    def assert_fails(self, mutate, requirement: str, status: str):
        _fx, code, rows, err = self._run(mutate)
        self.assertIn(status, _statuses(rows, requirement), (rows, err))
        self.assertEqual(code, 1, (rows, err))
        # 変異を入れていない項目は ok のまま（1 つの変異が別の行を巻き込まない）
        for req in REQUIREMENTS:
            if req != requirement:
                self.assertNotIn("missing", _statuses(rows, req), (req, rows))
                self.assertNotIn("invalid", _statuses(rows, req), (req, rows))
        return rows

    def test_all_present(self):
        _fx, code, rows, err = self._run()
        self.assertEqual(code, 0, (rows, err))
        for req in REQUIREMENTS:
            self.assertEqual(_statuses(rows, req) and set(_statuses(rows, req)), {"ok"}, (req, rows))
        # gate 列は completion-check の Step を名指す
        gates = {req: gate for _s, req, gate, _d in rows}
        self.assertEqual(rows[-1][:3], ("ok", "end", "completion-check:0"), rows)
        self.assertEqual(gates["reviewed-by"], "completion-check:2a")
        self.assertEqual(gates["remaining-tasks"], "completion-check:3")
        self.assertEqual(gates["route-in-progress"], "completion-check:4")
        self.assertEqual(gates["ac-ids"], "completion-check:5")
        self.assertEqual(gates["codebase-health"], "completion-check:4c-3")
        self.assertEqual(gates["ac-coverage"], "completion-check:4c")
        self.assertEqual(gates["follow-up-stage"], "completion-check:4d")
        # Ledger は Part B の後に --ledger で回す。既定の実行には出さない
        self.assertNotIn("ac-ledger", gates)
        # 行は gate の Step の順（2a → 3 → 4 → 4c → 4c-3 → 4d → 5）。main は最初の ok 以外の行で差し戻し先を決める
        order = [gate for _s, _r, gate, _d in rows[:-1]]
        steps = ["completion-check:2a", "completion-check:3", "completion-check:4", "completion-check:4c",
                 "completion-check:4c-3", "completion-check:4d", "completion-check:5"]
        self.assertEqual(sorted(order, key=steps.index), order, rows)

    def test_verification_pending_is_not_a_failure(self):
        # Verification は completion-check の Part B が埋める。gate の前の pending で止めない
        _fx, code, rows, err = self._run()
        self.assertEqual(code, 0, (rows, err))

    def test_reviewed_by_removed(self):
        def mutate(fx):
            fx.reviewed_by = ""
        self.assert_fails(mutate, "reviewed-by", "missing")

    def test_reviewed_by_without_implementation_reviewer(self):
        def mutate(fx):
            fx.reviewed_by = "- Reviewed by: gdd-security-reviewer"
        self.assert_fails(mutate, "reviewed-by", "invalid")

    def test_reviewed_by_agrees_with_ledger(self):
        # 述語は check-gate-ledger.sh のもの。同じ steering で ledger の reviewed-by 行と一致する
        fx, _code, rows, _err = self._run(lambda f: setattr(f, "reviewed_by", ""))
        ledger = subprocess.run(
            ["bash", str(LEDGER), "--root", str(fx.repo), "--steering", str(fx.steering)],
            cwd=fx.repo, capture_output=True, text=True, check=False,
        )
        ledger_status = [ln.split("\t")[0] for ln in ledger.stdout.splitlines()
                         if ln.split("\t")[1:2] == ["reviewed-by"]]
        self.assertEqual(_statuses(rows, "reviewed-by"), ledger_status, (rows, ledger.stdout))

    def test_pending_task_left(self):
        def mutate(fx):
            fx.pending = "### Task 2: 二つ目"
        self.assert_fails(mutate, "remaining-tasks", "invalid")

    def test_route_in_progress_left(self):
        def mutate(fx):
            fx.state["Route In Progress"] = "implementation_fix_only"
        self.assert_fails(mutate, "route-in-progress", "invalid")

    def test_route_in_progress_missing(self):
        def mutate(fx):
            fx.state["Route In Progress"] = None
        self.assert_fails(mutate, "route-in-progress", "invalid")

    def test_ac_orphan_reference(self):
        def mutate(fx):
            fx.verification_acs = ["AC-1", "AC-9"]
        self.assert_fails(mutate, "ac-ids", "invalid")

    def test_codebase_health_high(self):
        def mutate(fx):
            body = "".join(f"x{i} = {i}\n" for i in range(1700))
            (fx.repo / "big.py").write_text(body, encoding="utf-8")
            _git(fx.repo, "add", "big.py")
            _git(fx.repo, "commit", "-q", "-m", "big")
        self.assert_fails(mutate, "codebase-health", "invalid")


    # --- ac-coverage（Step 4c）---

    def test_ac_not_covered(self):
        def mutate(fx):
            fx.requirements_acs = ["AC-1", "AC-2"]
            fx.verification_acs = ["AC-1", "AC-2"]
        rows = self.assert_fails(mutate, "ac-coverage", "invalid")
        detail = [d for _s, r, _g, d in rows if r == "ac-coverage"][0]
        self.assertIn("AC-2", detail)
        self.assertNotIn("AC-1,", detail)

    def test_ac_line_counts_as_coverage(self):
        # `AC:` が正本で、`Covers AC:` は legacy alias（references/task-breakdown-steps.md）。どちらも数える
        _fx, code, rows, err = self._run(lambda fx: setattr(fx, "covers", "- AC: AC-1"))
        self.assertEqual(code, 0, (rows, err))
        self.assertEqual(_statuses(rows, "ac-coverage"), ["ok"], rows)

    def test_ac_field_after_pipe_counts_as_coverage(self):
        # `- Execution Status: completed | AC: AC-1 (primary)` の形（実データ）
        _fx, code, rows, err = self._run(
            lambda fx: setattr(fx, "covers", "- **Execution Status: completed** | Steps: 3/3 | AC: AC-1(c) (primary)"))
        self.assertEqual(code, 0, (rows, err))
        self.assertEqual(_statuses(rows, "ac-coverage"), ["ok"], rows)

    def test_ac_range_counts_as_coverage(self):
        def mutate(fx):
            fx.requirements_acs = ["AC-1", "AC-2", "AC-3"]
            fx.verification_acs = ["AC-1", "AC-2", "AC-3"]
            fx.covers = "Covers AC: AC-1..AC-3"
        _fx, code, rows, err = self._run(mutate)
        self.assertEqual(code, 0, (rows, err))
        self.assertEqual(_statuses(rows, "ac-coverage"), ["ok"], rows)

    def test_ac_range_does_not_cover_outside(self):
        def mutate(fx):
            fx.requirements_acs = ["AC-1", "AC-2", "AC-3"]
            fx.verification_acs = ["AC-1", "AC-2", "AC-3"]
            fx.covers = "Covers AC: AC-1〜AC-2"
        rows = self.assert_fails(mutate, "ac-coverage", "invalid")
        self.assertIn("AC-3", [d for _s, r, _g, d in rows if r == "ac-coverage"][0])

    def test_archived_task_in_worklog_counts_as_coverage(self):
        # 完了タスクは容量の上限で worklog.md へ退避される
        def mutate(fx):
            fx.covers = "- 退避済み"
            fx.steering.joinpath("worklog.md").write_text("# Worklog\n\n### Task 1: 一つ目\n\n- AC: AC-1\n", encoding="utf-8")
        _fx, code, rows, err = self._run(mutate)
        self.assertEqual(code, 0, (rows, err))
        self.assertEqual(_statuses(rows, "ac-coverage"), ["ok"], rows)

    def test_ac_line_under_non_task_heading_in_task_list_counts(self):
        # Completed Tasks の節の中の `### T1:` のような見出しの下も task の範囲（実データの形）
        _fx, code, rows, err = self._run(lambda fx: setattr(fx, "covers", "### T1: 調査\n\nCovers AC: AC-1"))
        self.assertEqual(code, 0, (rows, err))
        self.assertEqual(_statuses(rows, "ac-coverage"), ["ok"], rows)

    def test_ac_line_outside_task_is_not_coverage(self):
        # task の節の外（Verification Notes など）の `AC:` 行は被覆にしない
        def mutate(fx):
            fx.covers = "- 補足"
            fx.ledger = "## Verification Notes\n\n- AC: AC-1 は E2E 待ち\n"
        self.assert_fails(mutate, "ac-coverage", "invalid")

    def test_worklog_ac_line_outside_task_is_not_coverage(self):
        def mutate(fx):
            fx.covers = "- 退避済み"
            fx.steering.joinpath("worklog.md").write_text("# Worklog\n\n## メモ\n\n- AC: AC-1 のテストは未作成\n",
                                                          encoding="utf-8")
        self.assert_fails(mutate, "ac-coverage", "invalid")

    def test_ac_deferred_to_follow_up_stage_is_excluded(self):
        # Implementation Sequence Plan で current-pr でない Stage に置いた AC は、この PR の task に無くてよい
        def mutate(fx):
            fx.requirements_acs = ["AC-1", "AC-2"]
            fx.verification_acs = ["AC-1", "AC-2"]
            fx.plan = ("| Stage ID | Covers AC | PR Boundary |\n|---|---|---|\n"
                       "| S-1 | AC-1 | current-pr |\n| S-2 | AC-2 | follow-up-pr |\n")
        _fx, code, rows, err = self._run(mutate)
        self.assertEqual(code, 0, (rows, err))
        self.assertEqual(_statuses(rows, "ac-coverage"), ["ok"], rows)

    def test_ac_in_current_stage_is_not_excluded(self):
        def mutate(fx):
            fx.requirements_acs = ["AC-1", "AC-2"]
            fx.verification_acs = ["AC-1", "AC-2"]
            fx.plan = ("| Stage ID | Covers AC | PR Boundary |\n|---|---|---|\n"
                       "| S-1 | AC-1, AC-2 | current-pr |\n")
        self.assert_fails(mutate, "ac-coverage", "invalid")

    def test_this_pr_boundary_is_not_excluded(self):
        # 除くのは follow-up-pr・post-merge-verification で始まる値だけ。this-pr は current-pr と同じく除かない
        def mutate(fx):
            fx.requirements_acs = ["AC-1", "AC-2"]
            fx.verification_acs = ["AC-1", "AC-2"]
            fx.plan = ("| Stage ID | Covers AC | PR Boundary |\n|---|---|---|\n"
                       "| S-1 | AC-1 | current-pr |\n| S-2 | AC-2 | this-pr |\n")
        self.assert_fails(mutate, "ac-coverage", "invalid")

    def test_unknown_pr_boundary_goes_to_gate(self):
        # 空・記入例・未知の値は読めないので、除かずに gate へ返す
        for value in ("", "<current-pr | follow-up-pr>", "この PR"):
            with self.subTest(value=value):
                def mutate(fx, v=value):
                    fx.requirements_acs = ["AC-1", "AC-2"]
                    fx.verification_acs = ["AC-1", "AC-2"]
                    fx.plan = ("| Stage ID | Covers AC | PR Boundary |\n|---|---|---|\n"
                               f"| S-1 | AC-1 | current-pr |\n| S-2 | AC-2 | {v} |\n")
                self._assert_ac_source(mutate)

    def test_ac_in_current_and_follow_up_is_not_excluded(self):
        def mutate(fx):
            fx.requirements_acs = ["AC-1", "AC-2"]
            fx.verification_acs = ["AC-1", "AC-2"]
            fx.plan = ("| Stage ID | Covers AC | PR Boundary |\n|---|---|---|\n"
                       "| S-1 | AC-1, AC-2 | current-pr |\n| S-2 | AC-2 | post-merge-verification |\n")
        self.assert_fails(mutate, "ac-coverage", "invalid")

    def test_plan_without_pr_boundary_excludes_nothing(self):
        def mutate(fx):
            fx.requirements_acs = ["AC-1", "AC-2"]
            fx.verification_acs = ["AC-1", "AC-2"]
            fx.plan = "| Stage ID | Covers AC |\n|---|---|\n| S-2 | AC-2 |\n"
        self.assert_fails(mutate, "ac-coverage", "invalid")

    # --- ac-source（AC を閉じた形で読めないときは gate が読む）---

    def _assert_ac_source(self, mutate, *extra):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        fx = Fixture(Path(tmp.name))
        mutate(fx)
        fx.write()
        code, rows, err = fx.run(*extra)
        self.assertEqual(code, 1, (rows, err))
        self.assertIn("invalid", _statuses(rows, "ac-source"), rows)
        # 読めない AC 集合で ok を出さない
        self.assertNotIn("ok", _statuses(rows, "ac-coverage") + _statuses(rows, "ac-ledger"), rows)
        return rows

    def test_no_ac_definition_goes_to_gate(self):
        def mutate(fx):
            fx.requirements_acs = []
            fx.verification_acs = []
        self._assert_ac_source(mutate)

    def test_ac_in_section_not_readable_goes_to_gate(self):
        # 受入条件の節にあるが箇条書きの定義として読めない AC（表で書いた AC-2）
        def mutate(fx):
            fx.requirements_extra = "\n| AC-2 | 表で書いた条件 |\n"
        rows = self._assert_ac_source(mutate)
        self.assertIn("AC-2", " ".join(d for _s, r, _g, d in rows if r == "ac-source"))

    def test_no_ac_definition_goes_to_gate_in_ledger_mode(self):
        def mutate(fx):
            fx.requirements_acs = []
            fx.verification_acs = []
            fx.ledger = LEDGER_HEADER + ledger_row()
        self._assert_ac_source(mutate, "--ledger")

    def test_covers_in_fence_is_not_coverage(self):

        # fence の中は記入例で、現在値ではない
        self.assert_fails(lambda fx: setattr(fx, "covers", "```\n- Covers AC: AC-1\n```"), "ac-coverage", "invalid")

    def test_ac_id_in_other_text_is_not_coverage(self):
        # `AC:` の行の外で AC ID を書いても被覆にしない
        self.assert_fails(lambda fx: setattr(fx, "covers", "- メモ: AC-1 は後で"), "ac-coverage", "invalid")

    # --- follow-up-stage（Step 4d）---

    def test_follow_up_stage_filled(self):
        _fx, code, rows, err = self._run(lambda fx: setattr(fx, "lane", LANE_HEADER + lane_row()))
        self.assertEqual(code, 0, (rows, err))
        self.assertEqual(_statuses(rows, "follow-up-stage"), ["ok"], rows)

    def test_follow_up_stage_empty_field(self):
        self.assert_fails(lambda fx: setattr(fx, "lane", LANE_HEADER + lane_row(base_branch=" ")),
                          "follow-up-stage", "invalid")

    def test_follow_up_stage_placeholder_field(self):
        # テンプレートの `<...>` のままは埋まっていない
        self.assert_fails(lambda fx: setattr(fx, "lane", LANE_HEADER + lane_row(base_branch="<現在の base branch>")),
                          "follow-up-stage", "invalid")

    def test_follow_up_stage_none_without_reason(self):
        self.assert_fails(lambda fx: setattr(fx, "lane", LANE_HEADER + lane_row(tracking="none")),
                          "follow-up-stage", "invalid")

    def test_follow_up_stage_none_with_reason(self):
        _fx, code, rows, err = self._run(
            lambda fx: setattr(fx, "lane", LANE_HEADER + lane_row(tracking="none + この PR で完結する")))
        self.assertEqual(code, 0, (rows, err))
        self.assertEqual(_statuses(rows, "follow-up-stage"), ["ok"], rows)

    def test_follow_up_stage_missing_column(self):
        header = LANE_HEADER.replace("| Human Recheck |", "|").replace("|---|---|---|---|---|---|---|---|---|---|---|",
                                                                        "|---|---|---|---|---|---|---|---|---|---|")
        row = lane_row().replace("| not required + 理由 |", "|")
        self.assert_fails(lambda fx: setattr(fx, "lane", header + row), "follow-up-stage", "invalid")

    def test_follow_up_stage_not_a_table(self):
        # 表でない Lane は欄を読めないので止める側に倒す
        self.assert_fails(lambda fx: setattr(fx, "lane", "- S-2 を後で行う\n"), "follow-up-stage", "invalid")

    def test_follow_up_stage_prose_after_table(self):
        # 表の後ろの散文の注記は欄の判定に入れない（実データの形）
        _fx, code, rows, err = self._run(lambda fx: setattr(fx, "lane", LANE_HEADER + lane_row() + "\nS-2 は運用前提。\n"))
        self.assertEqual(code, 0, (rows, err))
        self.assertEqual(_statuses(rows, "follow-up-stage"), ["ok"], rows)

    def test_follow_up_stage_completed_lane_with_notes(self):
        # `- [x]` の下の字下げの行は、その項目の続き（実データの形）
        _fx, code, rows, err = self._run(lambda fx: setattr(fx, "lane", "- [x] S-2 済み\n  - 補足\n"))
        self.assertEqual(code, 0, (rows, err))
        self.assertEqual(_statuses(rows, "follow-up-stage"), ["ok"], rows)

    def test_follow_up_stage_indented_unchecked_item(self):
        # `- [x]` の下に字下げした `- [ ]` も未完の Stage（next_plan_check と同じく済みにしない）
        self.assert_fails(lambda fx: setattr(fx, "lane", "- [x] S-2 済み\n  - [ ] S-3 マージ後の確認\n"),
                          "follow-up-stage", "invalid")

    def test_follow_up_stage_unchecked_item_after_table(self):
        self.assert_fails(lambda fx: setattr(fx, "lane", LANE_HEADER + lane_row() + "\n- [ ] S-4\n"),
                          "follow-up-stage", "invalid")

    def test_follow_up_stage_unchecked_item(self):
        self.assert_fails(lambda fx: setattr(fx, "lane", "- [x] S-2 済み\n- [ ] S-3\n"), "follow-up-stage", "invalid")

    def test_follow_up_stage_completed_lane(self):
        # 済みの Stage だけの Lane（`- [x]`）は next_plan_check と同じく未完了でない
        _fx, code, rows, err = self._run(lambda fx: setattr(fx, "lane", "- [x] S-2 済み\n"))
        self.assertEqual(code, 0, (rows, err))
        self.assertEqual(_statuses(rows, "follow-up-stage"), ["ok"], rows)

    def test_follow_up_stage_line_separator(self):
        # LF・CR 以外の行区切りで行の境界が崩れたまま ok にしない
        _fx, code, rows, err = self._run(
            lambda fx: setattr(fx, "lane", LANE_HEADER + lane_row(tracking="none\u2028+ 理由")))
        self.assertEqual(code, 1, (rows, err))
        self.assertIn("invalid", _statuses(rows, "follow-up-stage"), rows)

    # --- ac-ledger（AC Trace Ledger Gate。--ledger）---

    def _ledger(self, mutate=None):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        fx = Fixture(Path(tmp.name))
        if mutate:
            mutate(fx)
        fx.write()
        code, rows, err = fx.run("--ledger")
        self.assertEqual(rows[-1][:3], ("ok", "end", "completion-check:0"), rows)
        self.assertLessEqual({r for _s, r, _g, _d in rows[:-1]}, {"ac-ledger", "ac-source"}, rows)
        self.assertEqual({g for _s, _r, g, _d in rows[:-1]}, {"completion-check:ledger"}, rows)
        return code, _statuses(rows, "ac-ledger"), rows

    def test_ledger_verified(self):
        code, statuses, rows = self._ledger(lambda fx: setattr(fx, "ledger", LEDGER_HEADER + ledger_row()))
        self.assertEqual((code, statuses), (0, ["ok"]), rows)

    def test_ledger_status_prefix(self):
        code, statuses, rows = self._ledger(
            lambda fx: setattr(fx, "ledger", LEDGER_HEADER + ledger_row(status="status=verified")))
        self.assertEqual((code, statuses), (0, ["ok"]), rows)

    def test_ledger_missing(self):
        code, statuses, rows = self._ledger()
        self.assertEqual((code, statuses), (1, ["missing"]), rows)

    def test_ledger_last_row_unverified(self):
        # append-only なので、AC ごとに最後の行で判定する
        ledger = LEDGER_HEADER + ledger_row() + ledger_row(status="status=unverified")
        code, statuses, rows = self._ledger(lambda fx: setattr(fx, "ledger", ledger))
        self.assertEqual((code, statuses), (1, ["invalid"]), rows)

    def test_ledger_later_row_verified(self):
        ledger = LEDGER_HEADER + ledger_row(status="failed") + ledger_row()
        code, statuses, rows = self._ledger(lambda fx: setattr(fx, "ledger", ledger))
        self.assertEqual((code, statuses), (0, ["ok"]), rows)

    def test_ledger_blocked_and_deferred(self):
        for status in ("blocked", "deferred-human", "failed", "unverified", "pass"):
            with self.subTest(status=status):
                code, statuses, rows = self._ledger(
                    lambda fx, s=status: setattr(fx, "ledger", LEDGER_HEADER + ledger_row(status=s)))
                self.assertEqual((code, statuses), (1, ["invalid"]), rows)

    def test_ledger_empty_command(self):
        code, statuses, rows = self._ledger(
            lambda fx: setattr(fx, "ledger", LEDGER_HEADER + ledger_row(command=" ")))
        self.assertEqual((code, statuses), (1, ["invalid"]), rows)

    def test_ledger_ac_without_row(self):
        def mutate(fx):
            fx.requirements_acs = ["AC-1", "AC-2"]
            fx.ledger = LEDGER_HEADER + ledger_row()
        code, statuses, rows = self._ledger(mutate)
        self.assertEqual((code, statuses), (1, ["invalid"]), rows)
        self.assertIn("AC-2", rows[0][3])

    def test_ledger_in_fence_goes_to_gate(self):
        # ac-ledger.md の fence の行は許可リストの外。中の行を読まずに ok にも missing にもしない
        self._assert_ledger_to_gate("```\n" + LEDGER_HEADER + ledger_row() + "```\n")

    def test_ledger_without_status_column(self):
        header = LEDGER_HEADER.replace("| status ", "| state ")
        code, statuses, rows = self._ledger(lambda fx: setattr(fx, "ledger", header + ledger_row()))
        self.assertEqual((code, set(statuses)), (1, {"invalid"}), rows)
        self.assertIn("欄が無い: status", rows[0][3])

    # --- 旧来の置き場所（tasklist.md・worklog.md）の Ledger の見出し ---

    def _assert_legacy_to_gate(self, mutate):
        code, statuses, rows = self._ledger(mutate)
        self.assertEqual((code, statuses), (1, []), rows)
        self.assertEqual({s for s, r, _g, _d in rows[:-1] if r == "ac-source"}, {"invalid"}, rows)
        self.assertTrue(any("ac-ledger.md の外に Ledger の見出し" in d for _s, _r, _g, d in rows[:-1]), rows)

    def test_ledger_heading_left_in_tasklist_goes_to_gate(self):
        # ac-ledger.md が verified でも、tasklist.md に残った Ledger の節の failed の行を読まずに ok にしない
        def mutate(fx):
            fx.ledger = LEDGER_HEADER + ledger_row()
            fx.tasklist_extra = LEDGER_HEADER + ledger_row(status="failed")
        self._assert_legacy_to_gate(mutate)

    def test_ledger_heading_left_in_worklog_goes_to_gate(self):
        # ac-ledger.md が無くても missing にしない（旧来の Ledger を gate が読む）
        for ledger in (LEDGER_HEADER + ledger_row(), None):
            with self.subTest(ac_ledger=ledger is not None):
                def mutate(fx, ledger=ledger):
                    fx.ledger = ledger
                    fx.steering.joinpath("worklog.md").write_text(
                        "# Worklog\n\n" + LEDGER_HEADER + ledger_row(status="failed"), encoding="utf-8")
                self._assert_legacy_to_gate(mutate)

    def test_ledger_heading_variants_left_in_tasklist_go_to_gate(self):
        # 見出しの階層・前後の語・大文字小文字・字下げ・引用・setext によらず、見出しに AC Trace Ledger があれば gate に返す
        for heading in ("# AC Trace Ledger", "#### AC Trace Ledger", "## Archived AC Trace Ledger",
                        "## AC Trace Ledger（Round 1 の退避）", "## ac trace ledger", "   ## AC Trace Ledger",
                        "> ## AC Trace Ledger", "> > ## AC Trace Ledger", "AC Trace Ledger\n===",
                        "AC Trace Ledger\n---", "> AC Trace Ledger\n> ---",
                        # 変更前の読み手（^#{2,3}\s+AC Trace Ledger）が節として読んだ形。\s は全角スペース・NBSP・改行にも当たる
                        "##\u3000AC Trace Ledger", "##\u00a0AC Trace Ledger", "##\nAC Trace Ledger",
                        "##\n\nAC Trace Ledger", "###\u3000AC Trace Ledger"):
            with self.subTest(heading=heading):
                def mutate(fx, heading=heading):
                    fx.ledger = LEDGER_HEADER + ledger_row()
                    fx.tasklist_extra = heading + "\n\n" + LEDGER_HEADER.split("\n\n", 1)[1] + ledger_row(status="failed")
                self._assert_legacy_to_gate(mutate)

    def test_ledger_heading_in_unclosed_fence_in_tasklist_goes_to_gate(self):
        # 閉じていない fence は残すので、その中の見出しも gate に返す（止まる側）
        def mutate(fx):
            fx.ledger = LEDGER_HEADER + ledger_row()
            fx.tasklist_extra = "```\n" + LEDGER_HEADER + ledger_row(status="failed")
        self._assert_legacy_to_gate(mutate)

    def test_ledger_example_in_fence_in_tasklist_is_ignored(self):
        # tasklist.md の閉じた fence の中の Ledger の記入例は、旧来の Ledger に数えない
        def mutate(fx):
            fx.ledger = LEDGER_HEADER + ledger_row()
            fx.tasklist_extra = "## Notes\n\n```markdown\n" + LEDGER_HEADER + ledger_row(status="failed") + "```\n"
        code, statuses, rows = self._ledger(mutate)
        self.assertEqual((code, statuses), (0, ["ok"]), rows)

    def test_ledger_other_ac_tables_in_tasklist_are_ok(self):
        # tasklist.md・worklog.md の、Ledger の見出しの下でない AC の表は読まない（今 ok の steering を gate に回さない）
        def mutate(fx):
            fx.ledger = LEDGER_HEADER + ledger_row()
            fx.tasklist_extra = ("## 確認\n\n| AC | method | status | evidence |\n|---|---|---|---|\n"
                                 "| AC-1 | pytest | pass | 1 passed |\n\n- AC Trace Ledger は ac-ledger.md に書く\n")
            fx.steering.joinpath("worklog.md").write_text(
                "# Worklog\n\n## Error Log\n\n| a | b |\n|---|---|\n| 1 | 2 |\n", encoding="utf-8")
        code, statuses, rows = self._ledger(mutate)
        self.assertEqual((code, statuses), (0, ["ok"]), rows)

    def test_ledger_deferred_ac_is_excluded(self):
        def mutate(fx):
            fx.requirements_acs = ["AC-1", "AC-2"]
            fx.plan = ("| Stage ID | Covers AC | PR Boundary |\n|---|---|---|\n"
                       "| S-1 | AC-1 | current-pr |\n| S-2 | AC-2 | post-merge-verification |\n")
            fx.ledger = LEDGER_HEADER + ledger_row()
        code, statuses, rows = self._ledger(mutate)
        self.assertEqual((code, statuses), (0, ["ok"]), rows)

    def test_ledger_unreadable_row_goes_to_gate(self):
        # 欄の数が見出しと合わない行（逃がしていない `|`）を読み飛ばして前の verified を残さない
        bad = "| AC-1 | Task 1 | `pytest -q 2>&1 | tail -1` -> 1 failed | failed | gdd-completion-check @ 2026-10-21 | 回帰 |\n"
        self._assert_ledger_to_gate(LEDGER_HEADER + ledger_row() + bad)

    def test_ledger_decorated_ac_id_goes_to_gate(self):
        # AC ID の欄が素の ID でない行（`**AC-1**`）も読めない行として止める
        self._assert_ledger_to_gate(LEDGER_HEADER + ledger_row() + ledger_row(ac="**AC-1**", status="failed"))

    def test_ledger_ac_row_in_other_table_goes_to_gate(self):
        # ac-ledger.md の Ledger でない表に AC の行があれば、読めない行として止める
        self._assert_ledger_to_gate(LEDGER_HEADER + ledger_row() + "\n| AC | 結果 |\n|---|---|\n| AC-1 | failed |\n")

    def test_ledger_other_table_in_ledger_file_goes_to_gate(self):
        # ac-ledger.md に置けるのは Ledger の表だけ。AC を含まない別の表も gate に返す
        self._assert_ledger_to_gate(LEDGER_HEADER + ledger_row() + "\n| Round | 件数 |\n|---|---|\n| 1 | 7 |\n")

    def test_ledger_table_split_by_note_goes_to_gate(self):
        # `>` の注記（実データの退避の注記の形）も ac-ledger.md にあれば gate に返す
        self._assert_ledger_to_gate(LEDGER_HEADER + "> Round 1 の行は worklog.md へ退避\n\n" + ledger_row())

    def _assert_ledger_to_gate(self, ledger):
        code, statuses, rows = self._ledger(lambda fx: setattr(fx, "ledger", ledger))
        self.assertEqual((code, statuses), (1, []), rows)
        self.assertEqual({s for s, r, _g, _d in rows[:-1] if r == "ac-source"}, {"invalid"}, rows)
        self.assertIn("Ledger の行を読めない", rows[0][3])

    def test_ledger_unknown_ac_id_goes_to_gate(self):
        # requirements.md に無い綴りの AC ID（`AC-01`）の行を読み飛ばして前の verified を残さない
        self._assert_ledger_to_gate(LEDGER_HEADER + ledger_row() + ledger_row(ac="AC-01", status="failed"))

    def test_ledger_fullwidth_ac_id_goes_to_gate(self):
        self._assert_ledger_to_gate(LEDGER_HEADER + ledger_row() + ledger_row(ac="ＡＣ-1", status="failed"))

    def test_ledger_free_text_append_goes_to_gate(self):
        # 表でない追記（箇条書き・散文）も読み飛ばさない
        for line in ("- AC-1: REFACTOR-reverified -> failed\n", "AC-1 は再検証で落ちた\n", "- ac-1 failed\n"):
            with self.subTest(line=line):
                self._assert_ledger_to_gate(LEDGER_HEADER + ledger_row() + "\n" + line)

    def test_ledger_unreadable_row_then_verified_goes_to_gate(self):
        # 読めない行は後に verified の行を足しても gate に返す（どの AC の出来事かを機械で決めない）
        bad = "| AC-1 | Task 1 | `pytest -q 2>&1 | tail -1` -> 1 failed | failed | gdd-completion-check @ 2026-10-21 | 回帰 |\n"
        self._assert_ledger_to_gate(LEDGER_HEADER + ledger_row() + bad + ledger_row())

    def test_ledger_escaped_pipe_in_cell_is_read(self):
        # `\|` で逃がした欄は Ledger の行として読み、最後の行の status（failed）で判定する
        escaped = "| AC-1 | Task 1 | `pytest -q 2>&1 \\| tail -1` -> 1 failed | failed | gdd-completion-check @ 2026-10-21 | 回帰 |\n"
        code, statuses, rows = self._ledger(lambda fx: setattr(fx, "ledger", LEDGER_HEADER + ledger_row() + escaped))
        self.assertEqual((code, statuses), (1, ["invalid"]), rows)

    def test_ledger_other_heading_in_ledger_file_goes_to_gate(self):
        self._assert_ledger_to_gate(LEDGER_HEADER + "\n### Round 2\n\n" + ledger_row())

    def test_ledger_row_before_separator_goes_to_gate(self):
        # 区切り行の直前の行でも、Ledger の見出しでなければ別の表の見出しとして読み飛ばさない
        self._assert_ledger_to_gate(LEDGER_HEADER + ledger_row() + ledger_row(status="failed") + "|---|---|---|---|---|---|\n")

    def test_ledger_other_table_header_with_ac_is_not_skipped(self):
        ledger = LEDGER_HEADER + ledger_row() + "\n| Task | AC-1 |\n|---|---|\n| T-1 | failed |\n"
        code, _statuses_, rows = self._ledger(lambda fx: setattr(fx, "ledger", ledger))
        self.assertEqual(code, 1, rows)

    def test_ledger_note_or_heading_with_ac_goes_to_gate(self):
        # AC を含む `>` の注記と見出し（全角・小文字の綴りを含む）も gate に返す
        for line in ("> AC-1: REFACTOR-reverified -> failed\n", "### AC-1 再検証: 1 failed\n",
                     "> ａｃ-1 failed\n", "> ＡＣ-1 failed\n", "> AC-1は再検証で failed\n", "### AC-2a 再検証\n"):
            with self.subTest(line=line):
                self._assert_ledger_to_gate(LEDGER_HEADER + ledger_row() + "\n" + line)

    def test_ledger_other_table_row_with_ac_goes_to_gate(self):
        # Ledger でない表の行（小文字の綴り・日本語が続く ID を含む）も gate に返す
        for row in ("| ac-1 | failed |\n", "| AC-1は失敗 | x |\n"):
            with self.subTest(row=row):
                self._assert_ledger_to_gate(LEDGER_HEADER + ledger_row() + "\n| 項目 | 結果 |\n|---|---|\n" + row)

    def test_ledger_header_like_row_with_ac_is_not_skipped(self):
        bad = "| AC ID | Task 1 | 検証コマンド/結果 | status | AC-1 failed | なし |\n"
        self._assert_ledger_to_gate(LEDGER_HEADER + ledger_row() + bad)

    def test_ledger_header_with_ac_before_separator_goes_to_gate(self):
        # 欄がそろい区切りが続く見出しの形でも、欄に AC ID があれば Ledger の見出しとして受け付けない
        bad = "| AC ID | 対応タスク | 検証コマンド/結果 | status | AC-1 failed | 未解決リスク |\n|---|---|---|---|---|---|\n"
        self._assert_ledger_to_gate(LEDGER_HEADER + ledger_row() + "\n" + bad + ledger_row())

    def test_ledger_header_like_row_with_ac_ends_ledger_table(self):
        # AC を含む見出しの形の行の後の別の表の行を、前の Ledger の見出しで読まない
        other = ("\n| AC-1 の内訳 | 手順 | 結果 | 前回 | 今回 | メモ |\n|---|---|---|---|---|---|\n"
                 "| AC-1 | REFACTOR | 1 failed | verified | failed | 回帰 |\n")
        code, statuses, rows = self._ledger(lambda fx: setattr(fx, "ledger", LEDGER_HEADER + ledger_row() + other))
        self.assertEqual(code, 1, rows)
        self.assertNotIn("ok", statuses, rows)
        self.assertNotIn("error", {s for s, _r, _g, _d in rows[:-1]}, rows)

    def test_ledger_ac_after_symbol_goes_to_gate(self):
        # 記号・日本語に続く AC（`①AC-1`、`™AC-1`）を含む注記も gate に返す
        for line in ("> ①AC-1: 再検証で 1 failed\n", "> ™AC-1 failed\n", "> 再検証でAC-1が failed\n"):
            with self.subTest(line=line):
                self._assert_ledger_to_gate(LEDGER_HEADER + ledger_row() + "\n" + line)

    def test_ledger_ac_without_front_boundary_goes_to_gate(self):
        # 全角・記号の混じった AC、英数字に続く AC を含む注記も gate に返す
        for line in ("> ①AC-１ failed\n", "> ①ＡＣ-1 failed\n", "> ①AC－1 failed\n", "> TaskAC-1 failed\n"):
            with self.subTest(line=line):
                self._assert_ledger_to_gate(LEDGER_HEADER + ledger_row() + "\n" + line)

    def test_ledger_row_with_unnamed_ac_goes_to_gate(self):
        # 欄の数が合わず、AC_ID_RE で拾える AC と境界の無い AC が並ぶ行も gate に返す
        def mutate(fx):
            fx.requirements_acs = ["AC-1", "AC-2"]
            fx.ledger = (LEDGER_HEADER + ledger_row() + ledger_row(ac="AC-2")
                         + "| AC-1 と AC-2は再検証で failed | - |\n" + ledger_row())
        code, statuses, rows = self._ledger(mutate)
        self.assertEqual((code, statuses), (1, []), rows)
        self.assertEqual({s for s, r, _g, _d in rows[:-1] if r == "ac-source"}, {"invalid"}, rows)

    def test_ledger_note_without_ac_goes_to_gate(self):
        # AC を含まない注記と見出しも gate に返す
        self._assert_ledger_to_gate(LEDGER_HEADER + "> Round 1 の行は worklog.md へ退避\n\n### Round 2\n\n" + ledger_row())

    def test_ledger_other_ac_in_other_cell_goes_to_gate(self):
        # 読めた Ledger の行のほかの欄に別の AC の結果があれば、その AC の最後の行が verified でも gate に返す
        for cell in ("-> AC-2 1 failed", "-> AC-2は 1 failed", "再検証でAC-2が failed", "AC-12 failed", "TaskAC-2 failed"):
            with self.subTest(cell=cell):
                def mutate(fx, c=cell):
                    fx.requirements_acs = ["AC-1", "AC-2"]
                    fx.ledger = LEDGER_HEADER + ledger_row(ac="AC-2") + ledger_row(command=c)
                code, statuses, rows = self._ledger(mutate)
                self.assertEqual((code, statuses), (1, []), rows)
                self.assertEqual({s for s, r, _g, _d in rows[:-1] if r == "ac-source"}, {"invalid"}, rows)

    def test_ledger_own_ac_in_other_cell_is_read(self):
        code, statuses, rows = self._ledger(
            lambda fx: setattr(fx, "ledger", LEDGER_HEADER + ledger_row(command="`pytest -k AC-1` -> pass")))
        self.assertEqual((code, statuses), (0, ["ok"]), rows)

    def test_ledger_non_ascii_digit_goes_to_gate(self):
        # ASCII でない数字の AC（`AC-١`）は、注記でも AC ID の欄でも gate に返す
        for tail in ("> AC-١は再検証で failed\n", "> TaskAC-١ failed\n", ledger_row(ac="AC-١", status="failed")):
            with self.subTest(tail=tail):
                self._assert_ledger_to_gate(LEDGER_HEADER + ledger_row() + tail)

    def test_ledger_header_missing_field_rows_are_not_unreadable(self):
        # 欄が欠けた Ledger の見出しの下の行は、見出しの不備（errors）で止まるので読めない行に数えない
        header = LEDGER_HEADER.replace("| status ", "| state ")
        code, statuses, rows = self._ledger(lambda fx: setattr(fx, "ledger", header + ledger_row() + ledger_row()))
        self.assertEqual((code, set(statuses)), (1, {"invalid"}), rows)
        self.assertNotIn("ac-source", {r for _s, r, _g, _d in rows[:-1]}, rows)

    def test_ledger_malformed_lines_go_to_gate_without_error(self):
        # 壊れた形の行で例外を出して guard 全体を落とさない（L1+ 安全策 2）
        for tail in ("|\n", "| |\n", "||||||\n", "|\\|\n", "| AC-1\n", "|---|\n| AC-1 | failed |\n"):
            with self.subTest(tail=tail):
                self._assert_ledger_to_gate(LEDGER_HEADER + ledger_row() + tail)

    def test_ledger_row_without_ac_id_goes_to_gate(self):
        # どの AC の行か決まらない行（AC ID の欄が空）は通さない（L1+ 安全策 2）
        self._assert_ledger_to_gate(LEDGER_HEADER + ledger_row() + ledger_row(ac="", status="failed"))

    def test_ledger_fence_in_ledger_file_goes_to_gate(self):
        # ac-ledger.md の閉じた fence の行も、許可リストの外として gate に返す（中の failed を読まずに ok にしない）
        for fence in ("```text\nAC-1 REFACTOR-reverified: pytest t.py -> 1 failed\n```\n",
                      "```\n$ pytest t.py\n1 failed\n```\n",
                      "~~~\n" + ledger_row(status="failed") + "~~~\n"):
            with self.subTest(fence=fence):
                self._assert_ledger_to_gate(LEDGER_HEADER + ledger_row() + "\n" + fence)

    def test_ledger_fence_with_hash_line_goes_to_gate(self):
        # fence の中の `#` の行（シェルのコメント）を Ledger の題として読まず、fence の行ごと gate に返す
        fence = "```bash\n# run tests\npytest t.py\n```\n"
        self._assert_ledger_to_gate(LEDGER_HEADER + ledger_row() + "\n" + fence + ledger_row(status="failed"))

    def test_ledger_unclosed_fence_in_ledger_file_goes_to_gate(self):
        self._assert_ledger_to_gate(LEDGER_HEADER + ledger_row() + "\n```\nAC-1 1 failed\n")

    # --- ac-ledger.md の末尾に足した行（Ledger の表のほかの行の後ろ。ファイル全体を許可リストで読む）---

    def _assert_ledger_ok(self, ledger):
        code, statuses, rows = self._ledger(lambda fx: setattr(fx, "ledger", ledger))
        self.assertEqual((code, statuses), (0, ["ok"]), rows)

    def test_ledger_row_appended_after_other_content_goes_to_gate(self):
        # 注記・別の表・別の見出しの表・区切りが続く行・引用の後ろ（ファイルの末尾）に足した failed の行を、
        # 前の verified の行で ok にしない（L1+ 安全策 2）
        table = LEDGER_HEADER.split("\n\n", 1)[1]
        six = "| a | b | c | d | e | f |\n|---|---|---|---|---|---|\n"
        failed = ledger_row(status="failed")
        for tail in ("\n## Ledger Notes\n\n> Round 1 の行は退避\n\n" + failed,
                     "\n## Ledger Notes\n\n" + six + failed,
                     "\n" + six + failed,
                     "\n## Archived\n\n" + table + failed,
                     "\n" + failed + "|---|---|---|---|---|---|\n",
                     "\n| AC ID | 対応タスク | 検証コマンド/結果 | status | AC-1 failed | 未解決リスク |\n|---|---|---|---|---|---|\n" + failed,
                     "\n> " + failed,
                     "\n" + "".join("> " + ln + "\n" for ln in (table + failed).splitlines()),
                     ledger_row(ac="ac-1", status="failed")):
            with self.subTest(tail=tail):
                self._assert_ledger_to_gate(LEDGER_HEADER + ledger_row() + tail)

    def test_ledger_broken_rows_appended_go_to_gate_without_error(self):
        # 末尾の壊れた形の行で例外を出して guard 全体を落とさない
        self._assert_ledger_to_gate(LEDGER_HEADER + ledger_row() + "\n## Notes\n\n| AC-1\n|\n|---|\n")

    def test_ledger_file_heading_forms_are_ok(self):
        # 見出しの無いファイル、`#` の見出しのファイル、Ledger の表を 2 つ並べたファイルは読む
        table = LEDGER_HEADER.split("\n\n", 1)[1]
        for ledger in (table + ledger_row(), "# AC Trace Ledger\n\n" + table + ledger_row(),
                       LEDGER_HEADER + ledger_row(status="failed") + "\n" + table + ledger_row()):
            with self.subTest(ledger=ledger):
                self._assert_ledger_ok(ledger)

    def test_ledger_file_without_rows_is_not_ok(self):
        # 空のファイル・見出しだけのファイルで、行の無い AC を ok にしない（判定できないときに通さない）
        for text in ("", "## AC Trace Ledger\n", LEDGER_HEADER):
            with self.subTest(text=text):
                code, statuses, rows = self._ledger(lambda fx, t=text: setattr(fx, "ledger", t))
                self.assertEqual((code, statuses), (1, ["invalid"]), rows)

    def test_ledger_file_unreadable_is_error(self):
        # ac-ledger.md がディレクトリ・指す先の無い symlink・UTF-8 でないときに、例外で全体を落とさず
        # ok・missing にもしない（error）
        for kind in ("dir", "dangling", "bytes"):
            with self.subTest(kind=kind):
                def mutate(fx, kind=kind):
                    fx.write()
                    path = fx.steering / "ac-ledger.md"
                    if kind == "dir":
                        path.mkdir()
                    elif kind == "dangling":
                        path.symlink_to(fx.steering / "nowhere.md")
                    else:
                        path.write_bytes(b"## AC Trace Ledger\n\n\xff\xfe\n")
                    fx.write = lambda: None
                code, statuses, rows = self._ledger(mutate)
                self.assertEqual((code, statuses), (1, ["error"]), rows)

    def test_ledger_unreadable_requirements_is_error(self):
        def mutate(fx):
            fx.write()
            fx.steering.joinpath("requirements.md").unlink()
            fx.steering.joinpath("requirements.md").mkdir()
            fx.write = lambda: None
        code, statuses, rows = self._ledger(mutate)
        self.assertEqual((code, statuses), (1, ["error"]), rows)

    # --- fail-open 側（root CLAUDE.md L1+ 安全策 2）---

    def test_unreadable_tasklist_fails_closed(self):
        # 例外で全体が落ちて exit 0 にならない（tasklist.md がディレクトリ）
        def mutate(fx):
            fx.write()
            fx.steering.joinpath("tasklist.md").unlink()
            fx.steering.joinpath("tasklist.md").mkdir()
            fx.write = lambda: None
        _fx, code, rows, err = self._run(mutate)
        self.assertEqual(code, 1, (rows, err))
        # 例外で止まった部品が受け持つ要求は、どれも行を残して error になる（行が消えない。
        # 記録の不備〔invalid〕と分け、main も gate も差し戻さずに外部前提不足で止める）
        self.assertEqual(_statuses(rows, "reviewed-by"), ["error"], rows)
        self.assertEqual(_statuses(rows, "remaining-tasks"), ["error"], rows)

    def test_non_utf8_stdout_keeps_every_row_and_end_row(self):
        # stdout の符号化が UTF-8 でなくても、途中で落ちて後ろの行が消えない。最後は終わりの行
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        fx = Fixture(Path(tmp.name))
        fx.write()
        args = ["--steering", str(fx.steering), "--root", str(fx.repo), "--base", "main"]
        result = subprocess.run([sys.executable, str(SCRIPT), *args], cwd=fx.repo, capture_output=True,
                                env={**os.environ, "PYTHONIOENCODING": "ascii", "PYTHONUTF8": "0"}, check=False)
        rows = [tuple(ln.split("\t")) for ln in result.stdout.decode("utf-8").splitlines()]
        self.assertEqual(result.returncode, 0, (rows, result.stderr))
        for req in REQUIREMENTS:
            self.assertIn("ok", _statuses(rows, req), (req, rows))
        self.assertEqual(rows[-1][:3], ("ok", "end", "completion-check:0"), rows)

    def test_unresolvable_base_fails_closed(self):
        # 判定できない（base を解決できない）ときに codebase-health が ok にならない
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        fx = Fixture(Path(tmp.name))
        fx.write()
        args = ["--steering", str(fx.steering), "--root", str(fx.repo), "--base", "no-such-ref"]
        result = subprocess.run([sys.executable, str(SCRIPT), *args], cwd=fx.repo,
                                capture_output=True, text=True, check=False)
        rows = [tuple(ln.split("\t")) for ln in result.stdout.splitlines()]
        self.assertEqual(result.returncode, 1, (rows, result.stderr))
        self.assertEqual(_statuses(rows, "codebase-health"), ["error"], rows)

    def test_lint_ac_usage_error_is_error(self):
        # lint-ac.py が判定できない（requirements.md が無い。exit 2）ときは invalid ではなく error
        def mutate(fx):
            fx.write()
            fx.steering.joinpath("requirements.md").unlink()
            fx.write = lambda: None
        _fx, code, rows, err = self._run(mutate)
        self.assertEqual(code, 1, (rows, err))
        self.assertEqual(_statuses(rows, "ac-ids"), ["error"], rows)
        # requirements.md を読む新しい行も、判定できないので error（ok にしない）
        self.assertEqual(_statuses(rows, "ac-coverage"), ["error"], rows)
        self.assertEqual(_statuses(rows, "follow-up-stage"), ["error"], rows)

    def test_unreadable_requirements_fails_closed(self):
        # 例外（requirements.md がディレクトリ）で全体が落ちず、読む行がどれも error になる
        def mutate(fx):
            fx.write()
            fx.steering.joinpath("requirements.md").unlink()
            fx.steering.joinpath("requirements.md").mkdir()
            fx.write = lambda: None
        _fx, code, rows, err = self._run(mutate)
        self.assertEqual(code, 1, (rows, err))
        self.assertEqual(_statuses(rows, "ac-coverage"), ["error"], rows)
        self.assertEqual(_statuses(rows, "follow-up-stage"), ["error"], rows)
        self.assertEqual(rows[-1][:3], ("ok", "end", "completion-check:0"), rows)

    def test_missing_steering_is_usage_error(self):
        # 判定できない（steering が無い）ときに通らない
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        fx = Fixture(Path(tmp.name))
        code, _rows, err = fx.run(steering=fx.root / "nowhere")
        self.assertEqual(code, 2)
        self.assertIn("steering が無い", err)

    def test_unclosed_fence_hides_pending_task(self):
        # 閉じ忘れの fence の後ろの task を数え落として ok にしない（done guard と同じ組み立て）
        def mutate(fx):
            fx.pending = "```\n### Task 2: 二つ目"
        _fx, code, rows, err = self._run(mutate)
        self.assertEqual(code, 1, (rows, err))
        self.assertIn("invalid", _statuses(rows, "remaining-tasks"), rows)

    def test_line_separator_in_tasklist(self):
        # LF・CR 以外の行区切り文字（U+2028）で節の境界が崩れたまま ok にしない
        def mutate(fx):
            fx.pending = "- なし\u2028### Task 2: 二つ目"
        _fx, code, rows, err = self._run(mutate)
        self.assertEqual(code, 1, (rows, err))
        self.assertIn("invalid", _statuses(rows, "remaining-tasks"), rows)


if __name__ == "__main__":
    unittest.main()
