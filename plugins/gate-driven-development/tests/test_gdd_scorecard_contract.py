"""`scripts/gdd-scorecard.py` の契約テスト。

スコアカードは「GDD の skill / prompt 改訂を採用してよいか」を、自己申告ではなく
`.steering/` 由来の行動メトリクスで判定する。ここで固定する契約は次の 4 つ。

1. 指標レジストリが単一の正本であること（`--list-metrics` が全指標と方向を出す）
2. キャリーオーバー除外 — baseline に既にある task は candidate 集合から除く
3. 母数不足を improved と誤って言わないこと（`insufficient_data` / `inconclusive`）
4. gate 一発通過率の母数が「その gate に到達した task」であること
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


from _paths import PLUGIN_ROOT as ROOT
SCRIPT_PATH = ROOT / "scripts" / "gdd-scorecard.py"


def load_module():
    spec = importlib.util.spec_from_file_location("gdd_scorecard", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    # dataclass の解決は sys.modules 経由で行われるため、exec_module の前に登録する
    # （Python 3.14 では未登録だと `_is_type` が None を引いて AttributeError になる）
    sys.modules["gdd_scorecard"] = module
    spec.loader.exec_module(module)
    return module


def make_task(steering_id: str, **overrides) -> dict:
    """`collect-gdd-telemetry.py --format=json` の tasks[] 1 件分を組み立てる。"""
    task = {
        "steering_id": steering_id,
        "worktree": "/tmp/repo",
        "task_size": "standard",
        "entry_intent": "unknown",
        "requirements_status": "approved",
        "design_status": "approved",
        "human_check_status": "approved",
        "resume_from": "done",
        "next_action": "done",
        "route_in_progress": "none",
        "fix_attempts": 0,
        "completed_tasks": 1,
        "pending_tasks": 0,
        "error_log_entries": 0,
        "learned_patterns_entries": 0,
        "reviewer_lineage_smi_added": 0,
        "reviewer_lineage_impact_added": 0,
        "workflow_incident_entries": 0,
        "guardrail_detection_entries": 0,
        "incident_types": "",
        "state_is_terminal": True,
        "state_kind": "done",
    }
    task.update(overrides)
    return task


def make_snapshot(tasks: list[dict]) -> dict:
    return {"tasks": tasks, "summary": {"total_tasks": len(tasks)}}


class ScorecardTestBase(unittest.TestCase):
    def setUp(self) -> None:
        self.mod = load_module()
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def write_snapshot(self, name: str, tasks: list[dict]) -> Path:
        path = self.tmp / name
        path.write_text(json.dumps(make_snapshot(tasks), ensure_ascii=False), encoding="utf-8")
        return path

    def run_cli(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(SCRIPT_PATH), *args],
            capture_output=True,
            text=True,
        )

    def run_json(self, baseline: Path, candidate: Path, *extra: str) -> tuple[dict, int]:
        proc = self.run_cli(
            "--baseline", str(baseline),
            "--candidate", str(candidate),
            "--format", "json",
            *extra,
        )
        self.assertIn(proc.returncode, (0, 3), msg=f"unexpected exit: {proc.returncode}\n{proc.stderr}")
        return json.loads(proc.stdout), proc.returncode

    def find_metric(self, payload: dict, key: str) -> dict:
        for row in payload["metrics"]:
            if row["key"] == key:
                return row
        self.fail(f"metric not found in payload: {key}")


class TestMetricRegistry(ScorecardTestBase):
    """指標定義はコード内のレジストリが単一の正本。SKILL.md には複製しない。"""

    def test_list_metrics_emits_every_registered_metric(self) -> None:
        proc = self.run_cli("--list-metrics", "--format", "json")
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        payload = json.loads(proc.stdout)
        keys = {row["key"] for row in payload["metrics"]}
        self.assertEqual(keys, {m.key for m in self.mod.METRICS})

    def test_every_metric_declares_direction_label_and_proxy(self) -> None:
        for metric in self.mod.METRICS:
            with self.subTest(metric=metric.key):
                self.assertIn(metric.direction, ("lower_is_better", "higher_is_better"))
                self.assertTrue(metric.label.strip(), "label は空にできない")
                self.assertTrue(metric.proxy.strip(), "proxy 説明は空にできない")

    def test_registry_is_not_empty(self) -> None:
        self.assertGreaterEqual(len(self.mod.METRICS), 4)


class TestCarryOverExclusion(ScorecardTestBase):
    """同一 repo の時系列比較では baseline の task が candidate にも残る。"""

    def test_baseline_tasks_are_excluded_from_candidate_set(self) -> None:
        baseline_tasks = [make_task(f"old-{i}", fix_attempts=3) for i in range(4)]
        # candidate snapshot は baseline を内包し、改訂後の task を 4 件足したもの
        candidate_tasks = baseline_tasks + [make_task(f"new-{i}", fix_attempts=0) for i in range(4)]

        baseline = self.write_snapshot("baseline.json", baseline_tasks)
        candidate = self.write_snapshot("candidate.json", candidate_tasks)
        payload, _ = self.run_json(baseline, candidate)

        self.assertEqual(payload["sample"]["baseline_tasks"], 4)
        self.assertEqual(payload["sample"]["candidate_tasks"], 4, "carry-over を除外していない")
        self.assertEqual(payload["sample"]["carried_over_excluded"], 4)

        row = self.find_metric(payload, "avg_fix_attempts")
        self.assertEqual(row["candidate"], 0.0, "希釈された平均になっている")
        self.assertEqual(row["verdict"], "improved")

    def test_disjoint_snapshots_exclude_nothing(self) -> None:
        baseline = self.write_snapshot("baseline.json", [make_task(f"a-{i}") for i in range(3)])
        candidate = self.write_snapshot("candidate.json", [make_task(f"b-{i}") for i in range(3)])
        payload, _ = self.run_json(baseline, candidate)

        self.assertEqual(payload["sample"]["carried_over_excluded"], 0)
        self.assertEqual(payload["sample"]["candidate_tasks"], 3)


class TestVerdictPerMetric(ScorecardTestBase):
    def test_lower_is_better_metric_improves_when_value_drops(self) -> None:
        baseline = self.write_snapshot("b.json", [make_task(f"b-{i}", fix_attempts=2) for i in range(3)])
        candidate = self.write_snapshot("c.json", [make_task(f"c-{i}", fix_attempts=0) for i in range(3)])
        payload, _ = self.run_json(baseline, candidate)

        row = self.find_metric(payload, "avg_fix_attempts")
        self.assertEqual(row["direction"], "lower_is_better")
        self.assertEqual(row["baseline"], 2.0)
        self.assertEqual(row["candidate"], 0.0)
        self.assertEqual(row["verdict"], "improved")

    def test_lower_is_better_metric_regresses_when_value_rises(self) -> None:
        baseline = self.write_snapshot("b.json", [make_task(f"b-{i}", error_log_entries=0) for i in range(3)])
        candidate = self.write_snapshot("c.json", [make_task(f"c-{i}", error_log_entries=5) for i in range(3)])
        payload, _ = self.run_json(baseline, candidate)

        row = self.find_metric(payload, "error_log_per_task")
        self.assertEqual(row["verdict"], "regressed")

    def test_change_within_noise_floor_is_flat(self) -> None:
        # 完了率 100% -> 100%: 変化なし
        baseline = self.write_snapshot("b.json", [make_task(f"b-{i}") for i in range(4)])
        candidate = self.write_snapshot("c.json", [make_task(f"c-{i}") for i in range(4)])
        payload, _ = self.run_json(baseline, candidate)

        row = self.find_metric(payload, "completion_rate")
        self.assertEqual(row["verdict"], "flat")

    def test_metric_below_min_samples_is_insufficient_data(self) -> None:
        baseline = self.write_snapshot("b.json", [make_task("b-0", fix_attempts=3)])
        candidate = self.write_snapshot("c.json", [make_task("c-0", fix_attempts=0)])
        payload, _ = self.run_json(baseline, candidate, "--min-samples", "3")

        row = self.find_metric(payload, "avg_fix_attempts")
        self.assertEqual(row["verdict"], "insufficient_data")
        self.assertNotEqual(row["verdict"], "improved", "母数 1 件で改善と言ってはいけない")


class TestSingleTaskEffectGuard(ScorecardTestBase):
    """1 task 分の振れ幅で説明できる差を improved と言わせない。

    小サンプルでは相対変化の noise-floor が効かない。n=4 の完走率は task 1 件で
    25 ポイント動くため、25 ポイントの改善は「1 件たまたま done になった」と
    区別がつかない。指標ごとの単位（rate=100pt / count=1）を母数で割った
    「1 task が動かせる量」を超えない変化は flat に落とす。
    """

    def test_rate_change_explainable_by_one_task_is_flat(self) -> None:
        # baseline 完走率 0% (n=4) -> candidate 25% (n=4): done が 1 件増えただけ
        baseline = self.write_snapshot(
            "b.json", [make_task(f"b-{i}", state_kind="in-progress", next_action="gdd-task-breakdown") for i in range(4)]
        )
        candidate_tasks = [
            make_task("c-0", state_kind="done"),
            *[make_task(f"c-{i}", state_kind="in-progress", next_action="gdd-task-breakdown") for i in range(1, 4)],
        ]
        candidate = self.write_snapshot("c.json", candidate_tasks)
        payload, _ = self.run_json(baseline, candidate)

        row = self.find_metric(payload, "completion_rate")
        self.assertEqual(row["candidate"], 25.0)
        self.assertEqual(row["verdict"], "flat", "task 1 件分の差を improved と判定している")

    def test_rate_change_beyond_one_task_is_improved(self) -> None:
        # 0% -> 75%: 3 件分動いており 1 task では説明できない
        baseline = self.write_snapshot(
            "b.json", [make_task(f"b-{i}", state_kind="in-progress", next_action="gdd-task-breakdown") for i in range(4)]
        )
        candidate_tasks = [
            *[make_task(f"c-{i}", state_kind="done") for i in range(3)],
            make_task("c-3", state_kind="in-progress", next_action="gdd-task-breakdown"),
        ]
        candidate = self.write_snapshot("c.json", candidate_tasks)
        payload, _ = self.run_json(baseline, candidate)

        row = self.find_metric(payload, "completion_rate")
        self.assertEqual(row["verdict"], "improved")

    def test_count_metric_change_of_one_task_is_flat(self) -> None:
        # 平均 Fix Attempts 0 -> 0.25 (n=4): 1 件が 1 回だけ差し戻された分
        baseline = self.write_snapshot("b.json", [make_task(f"b-{i}", fix_attempts=0) for i in range(4)])
        candidate_tasks = [make_task("c-0", fix_attempts=1)] + [
            make_task(f"c-{i}", fix_attempts=0) for i in range(1, 4)
        ]
        candidate = self.write_snapshot("c.json", candidate_tasks)
        payload, _ = self.run_json(baseline, candidate)

        row = self.find_metric(payload, "avg_fix_attempts")
        self.assertEqual(row["candidate"], 0.25)
        self.assertEqual(row["verdict"], "flat")

    def test_every_metric_declares_a_single_task_unit(self) -> None:
        for metric in self.mod.METRICS:
            with self.subTest(metric=metric.key):
                self.assertGreater(metric.unit, 0, "1 task が動かせる量の単位が必要")

    def test_guard_is_reported_in_output(self) -> None:
        baseline = self.write_snapshot(
            "b.json", [make_task(f"b-{i}", state_kind="in-progress", next_action="gdd-task-breakdown") for i in range(4)]
        )
        candidate_tasks = [
            make_task("c-0", state_kind="done"),
            *[make_task(f"c-{i}", state_kind="in-progress", next_action="gdd-task-breakdown") for i in range(1, 4)],
        ]
        candidate = self.write_snapshot("c.json", candidate_tasks)
        payload, _ = self.run_json(baseline, candidate)

        row = self.find_metric(payload, "completion_rate")
        self.assertIn("single_task_effect", row)
        self.assertEqual(row["single_task_effect"], 25.0)


class TestGateDenominator(ScorecardTestBase):
    """gate 一発通過率の母数は「その gate に到達した task」に限る。"""

    def test_tasks_that_never_reached_the_gate_are_excluded_from_denominator(self) -> None:
        reached = [make_task(f"b-{i}", design_status="approved") for i in range(3)]
        not_reached = [make_task(f"b-x-{i}", design_status="unknown", state_kind="in-progress") for i in range(7)]
        baseline = self.write_snapshot("b.json", reached + not_reached)
        candidate = self.write_snapshot("c.json", [make_task(f"c-{i}", design_status="approved") for i in range(3)])
        payload, _ = self.run_json(baseline, candidate)

        row = self.find_metric(payload, "design_first_pass_rate")
        self.assertEqual(row["baseline"], 100.0, "未到達 task を分母に入れて通過率を下げている")
        self.assertEqual(row["baseline_sample"], 3)


class TestOverallVerdict(ScorecardTestBase):
    def test_small_dataset_forces_inconclusive(self) -> None:
        baseline = self.write_snapshot("b.json", [make_task("b-0", fix_attempts=5)])
        candidate = self.write_snapshot("c.json", [make_task("c-0", fix_attempts=0)])
        payload, _ = self.run_json(baseline, candidate, "--min-samples", "3")

        self.assertEqual(payload["overall"]["verdict"], "inconclusive")
        self.assertIn("データ不足", payload["overall"]["reason"])

    def test_all_improved_yields_adopt(self) -> None:
        baseline = self.write_snapshot(
            "b.json", [make_task(f"b-{i}", fix_attempts=3, error_log_entries=2) for i in range(4)]
        )
        candidate = self.write_snapshot(
            "c.json", [make_task(f"c-{i}", fix_attempts=0, error_log_entries=0) for i in range(4)]
        )
        payload, _ = self.run_json(baseline, candidate)

        self.assertEqual(payload["overall"]["verdict"], "adopt")

    def test_regression_only_yields_reject(self) -> None:
        baseline = self.write_snapshot("b.json", [make_task(f"b-{i}", fix_attempts=0) for i in range(4)])
        candidate = self.write_snapshot("c.json", [make_task(f"c-{i}", fix_attempts=4) for i in range(4)])
        payload, _ = self.run_json(baseline, candidate)

        self.assertEqual(payload["overall"]["verdict"], "reject")

    def test_mixed_signals_yield_mixed(self) -> None:
        baseline = self.write_snapshot(
            "b.json", [make_task(f"b-{i}", fix_attempts=3, error_log_entries=0) for i in range(4)]
        )
        candidate = self.write_snapshot(
            "c.json", [make_task(f"c-{i}", fix_attempts=0, error_log_entries=4) for i in range(4)]
        )
        payload, _ = self.run_json(baseline, candidate)

        self.assertEqual(payload["overall"]["verdict"], "mixed")


class TestCliContract(ScorecardTestBase):
    def test_fail_on_regress_exits_3(self) -> None:
        baseline = self.write_snapshot("b.json", [make_task(f"b-{i}", fix_attempts=0) for i in range(4)])
        candidate = self.write_snapshot("c.json", [make_task(f"c-{i}", fix_attempts=4) for i in range(4)])
        _, code = self.run_json(baseline, candidate, "--fail-on-regress")
        self.assertEqual(code, 3)

    def test_adopt_exits_0_even_with_fail_on_regress(self) -> None:
        baseline = self.write_snapshot("b.json", [make_task(f"b-{i}", fix_attempts=3) for i in range(4)])
        candidate = self.write_snapshot("c.json", [make_task(f"c-{i}", fix_attempts=0) for i in range(4)])
        _, code = self.run_json(baseline, candidate, "--fail-on-regress")
        self.assertEqual(code, 0)

    def test_missing_input_exits_1(self) -> None:
        candidate = self.write_snapshot("c.json", [make_task("c-0")])
        proc = self.run_cli("--baseline", str(self.tmp / "nope.json"), "--candidate", str(candidate))
        self.assertEqual(proc.returncode, 1)

    def test_text_output_shows_sample_counts_and_verdict(self) -> None:
        baseline = self.write_snapshot("b.json", [make_task(f"b-{i}", fix_attempts=3) for i in range(4)])
        candidate = self.write_snapshot("c.json", [make_task(f"c-{i}", fix_attempts=0) for i in range(4)])
        proc = self.run_cli("--baseline", str(baseline), "--candidate", str(candidate))

        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        self.assertIn("GDD Scorecard", proc.stdout)
        self.assertIn("avg_fix_attempts", proc.stdout)
        self.assertIn("adopt", proc.stdout)
        self.assertIn("n=", proc.stdout, "母数を出さないと過剰主張になる")

    def test_empty_candidate_is_inconclusive_not_crash(self) -> None:
        baseline_tasks = [make_task(f"b-{i}") for i in range(4)]
        baseline = self.write_snapshot("b.json", baseline_tasks)
        candidate = self.write_snapshot("c.json", baseline_tasks)  # 新規 task ゼロ
        payload, _ = self.run_json(baseline, candidate)

        self.assertEqual(payload["sample"]["candidate_tasks"], 0)
        self.assertEqual(payload["overall"]["verdict"], "inconclusive")


if __name__ == "__main__":
    unittest.main()
