"""scripts/run-reviewer-recall-eval.py（reviewer の見逃しの評価）の runner を、偽の claude で入口から通す。

LLM は呼ばない。偽の claude は argv に `--agent` があれば reviewer、無ければ表への写し役として、
FAKE_SPEC の JSON の値を返し、呼ばれた argv を FAKE_LOG に 1 行ずつ足す。
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from _git_fixture import init_repo
from _paths import PLUGIN_ROOT, REPO_ROOT

sys.path.insert(0, str(PLUGIN_ROOT / "hooks" / "scripts"))
from lib import finding_dispositions as fd  # noqa: E402

SCRIPT = PLUGIN_ROOT / "scripts" / "run-reviewer-recall-eval.py"

FAKE_CLAUDE = """#!/usr/bin/env python3
import json, os, sys
spec = json.load(open(os.environ["FAKE_SPEC"]))
with open(os.environ["FAKE_LOG"], "a") as f:
    f.write(json.dumps({"argv": sys.argv[1:], "cwd": os.getcwd(), "stdin": sys.stdin.read()}) + "\\n")
part = spec["reviewer" if "--agent" in sys.argv else "transcriber"]
print(json.dumps({"type": "result", "is_error": part.get("is_error", False), "result": part["result"],
                  "total_cost_usd": part["cost"], "duration_ms": 1000}))
sys.exit(part.get("exit", 0))
"""


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=True).stdout.strip()


class RecallEvalFixture(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.repo = self.root / "repo"
        self.repo.mkdir()
        init_repo(self.repo)
        self.base = _git(self.repo, "rev-parse", "HEAD")
        (self.repo / "src").mkdir()
        (self.repo / "src" / "a.py").write_text("a = 1\n", encoding="utf-8")
        (self.repo / "src" / "b.py").write_text("b = 1\n", encoding="utf-8")
        (self.repo / "review-log").mkdir()
        (self.repo / "review-log" / "x.md").write_text("| r1-1 | 独立-1 | high | 答え |\n", encoding="utf-8")
        _git(self.repo, "add", "-A")
        _git(self.repo, "commit", "-q", "-m", "defect")
        self.tip = _git(self.repo, "rev-parse", "HEAD")
        (self.repo / "src" / "a.py").write_text("a = 2\n", encoding="utf-8")
        _git(self.repo, "commit", "-q", "-am", "fix")
        self.fix = _git(self.repo, "rev-parse", "HEAD")
        self.cases = self.root / "cases.json"
        self.write_cases([{"id": "found-1", "kind": "found", "source": {"review_log": "review-log/x.md", "round": "独立-1", "pr": 1},
                           "base": self.base, "tip": self.tip, "expected": [
                               {"id": "r1-1", "severity": "high", "harm": "yes", "paths": ["src/a.py"], "fix_commit": self.fix},
                               {"id": "r1-2", "severity": "high", "harm": "yes", "paths": ["src/a.py"], "fix_commit": self.fix},
                               {"id": "r1-3", "severity": "medium", "harm": "yes", "paths": ["src/b.py"], "fix_commit": self.fix}]}])
        self.fake = self.root / "claude"
        self.fake.write_text(FAKE_CLAUDE, encoding="utf-8")
        self.fake.chmod(0o755)
        self.spec = self.root / "spec.json"
        self.log = self.root / "calls.jsonl"
        self.out = self.root / "out"
        self.set_spec(reviewer_cost=0.5)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def write_cases(self, cases: list[dict]) -> None:
        self.cases.write_text(json.dumps({"description": "t", "cases": cases}, ensure_ascii=False), encoding="utf-8")

    def set_spec(self, reviewer_cost: float, rows: str = "| 1 | high | fail-open | src/a.py:1 |\n| 2 | medium | product | b.py:1 |",
                 reviewer_error: bool = False) -> None:
        self.spec.write_text(json.dumps({
            "reviewer": {"result": "### [High] a\n### [Medium] b", "cost": reviewer_cost, "is_error": reviewer_error},
            "transcriber": {"result": rows, "cost": 0.01}}), encoding="utf-8")

    def run_cli(self, *extra: str) -> subprocess.CompletedProcess:
        env = {**os.environ, "FAKE_SPEC": str(self.spec), "FAKE_LOG": str(self.log)}
        return subprocess.run([sys.executable, str(SCRIPT), "--cases", str(self.cases), "--out", str(self.out),
                               "--repo", str(self.repo), "--claude-bin", str(self.fake), "--jobs", "1", *extra],
                              capture_output=True, text=True, env=env, timeout=120)

    def calls(self) -> list[dict]:
        if not self.log.exists():
            return []
        return [json.loads(line) for line in self.log.read_text(encoding="utf-8").splitlines()]

    def results(self) -> list[dict]:
        return [json.loads(line) for line in (self.out / "results.jsonl").read_text(encoding="utf-8").splitlines()]


class RecallEvalTests(RecallEvalFixture):
    def test_dry_run_writes_materials_without_review_log_and_calls_nothing(self) -> None:
        proc = self.run_cli("--dry-run")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        case_dir = self.out / "found-1"
        self.assertTrue((case_dir / "wt" / "src" / "a.py").exists())
        self.assertEqual((case_dir / "wt" / "src" / "a.py").read_text(encoding="utf-8"), "a = 1\n")
        self.assertFalse((case_dir / "wt" / "review-log").exists())
        diff = (case_dir / "diff.txt").read_text(encoding="utf-8")
        self.assertIn("src/a.py", diff)
        self.assertNotIn("review-log", diff)
        self.assertIn(str(case_dir / "sheet.md"), (case_dir / "prompt.txt").read_text(encoding="utf-8"))
        self.assertEqual(self.calls(), [])

    def test_scores_hit_weak_miss_one_to_one(self) -> None:
        proc = self.run_cli("--runs", "1")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        [res] = self.results()
        # high の 1 件は a.py の 1 つ目にだけ当て、2 つ目は外れ。b.py は medium・非実害で weak（basename でも当てる）
        self.assertEqual(res["matches"], {"r1-1": "hit", "r1-2": "miss", "r1-3": "weak"})
        self.assertEqual(res["status"], "ok")
        self.assertAlmostEqual(res["cost_usd"], 0.51)
        reviewer, transcriber = self.calls()
        self.assertIn("--agent", reviewer["argv"])
        self.assertEqual(reviewer["argv"][reviewer["argv"].index("--tools") + 1], "Read,Grep,Glob")
        self.assertEqual(Path(reviewer["cwd"]).resolve(), (self.out / "found-1" / "wt").resolve())
        self.assertIn("### [High] a", transcriber["stdin"])
        self.assertIn("found-1", (self.out / "summary.md").read_text(encoding="utf-8"))

    def test_findings_file_is_the_review_findings_form(self) -> None:
        self.run_cli("--runs", "1")
        text = (self.out / "found-1" / "run-1.findings.md").read_text(encoding="utf-8")
        sections, errors = fd.parse(text)
        self.assertEqual(errors, [])
        [sec] = sections
        self.assertEqual(sec.count, 2)
        self.assertEqual([r.dest for r in sec.rows], ["blocking", "advisory"])

    def test_stops_before_a_run_that_could_cross_the_cost_cap(self) -> None:
        self.set_spec(reviewer_cost=3.0)
        proc = self.run_cli("--runs", "2", "--max-run-usd", "2", "--max-cost-usd", "4")
        self.assertEqual(proc.returncode, 3, proc.stderr)
        self.assertEqual([r["status"] for r in self.results()], ["ok", "budget"])
        self.assertEqual(len([c for c in self.calls() if "--agent" in c["argv"]]), 1)

    def test_resume_reuses_finished_runs(self) -> None:
        self.run_cli("--runs", "1")
        first = len(self.calls())
        proc = self.run_cli("--runs", "2")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(len([c for c in self.calls()[first:] if "--agent" in c["argv"]]), 1)
        self.assertEqual([r["run"] for r in self.results()], [1, 2])

    def test_reviewer_error_is_recorded_not_scored(self) -> None:
        self.set_spec(reviewer_cost=0.2, reviewer_error=True)
        proc = self.run_cli("--runs", "1")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        [res] = self.results()
        self.assertEqual(res["status"], "error")
        self.assertEqual(res["matches"], {})
        self.assertAlmostEqual(res["cost_usd"], 0.2)

    def test_check_rejects_a_path_missing_at_tip(self) -> None:
        doc = json.loads(self.cases.read_text(encoding="utf-8"))
        doc["cases"][0]["expected"][0]["paths"] = ["src/nope.py"]
        self.write_cases(doc["cases"])
        proc = self.run_cli("--check")
        self.assertEqual(proc.returncode, 2)
        self.assertIn("src/nope.py", proc.stderr)
        self.assertEqual(self.calls(), [])


if __name__ == "__main__":
    unittest.main()
