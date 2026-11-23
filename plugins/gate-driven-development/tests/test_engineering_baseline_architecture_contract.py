"""Contract tests for engineering baseline and architecture posture in GDD."""
from __future__ import annotations

import ast
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


from _paths import PLUGIN_ROOT


def load_codebase_health_module():
    script = PLUGIN_ROOT / "scripts" / "gdd-codebase-health.py"
    spec = importlib.util.spec_from_file_location("gdd_codebase_health", script)
    if spec is None or spec.loader is None:
        raise AssertionError(f"failed to load {script}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


class EngineeringBaselineArchitectureContractTests(unittest.TestCase):
    def test_codebase_health_changed_mode_falls_back_when_origin_main_is_missing(self) -> None:
        module = load_codebase_health_module()
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            git(repo, "init", "-b", "main")
            git(repo, "config", "user.email", "gdd-test@example.invalid")
            git(repo, "config", "user.name", "GDD Test")
            (repo / "README.md").write_text("# test\n", encoding="utf-8")
            git(repo, "add", "README.md")
            git(repo, "commit", "-m", "initial")
            git(repo, "switch", "-c", "feature")
            (repo / "large.py").write_text("\n".join("print('x')" for _ in range(12)), encoding="utf-8")
            git(repo, "add", "large.py")
            git(repo, "commit", "-m", "add large file")

            report = module.build_report(repo, "changed", "origin/main", 10)

        self.assertEqual(report["summary"]["files_scanned"], 1)
        self.assertEqual(report["findings"][0]["category"], "large_file")
        self.assertEqual(report["findings"][0]["path"], "large.py")

    def test_codebase_health_changed_mode_does_not_scan_legacy_files_when_base_resolves_to_head(self) -> None:
        module = load_codebase_health_module()
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            git(repo, "init", "-b", "main")
            git(repo, "config", "user.email", "gdd-test@example.invalid")
            git(repo, "config", "user.name", "GDD Test")
            (repo / "README.md").write_text("# test\n", encoding="utf-8")
            git(repo, "add", "README.md")
            git(repo, "commit", "-m", "initial")
            (repo / "large.py").write_text("\n".join("print('x')" for _ in range(12)), encoding="utf-8")
            git(repo, "add", "large.py")
            git(repo, "commit", "-m", "add large file")

            report = module.build_report(repo, "changed", "origin/main", 10)

        paths = {finding["path"] for finding in report["findings"]}
        self.assertNotIn("large.py", paths)

    def test_codebase_health_changed_mode_does_not_fall_back_past_head_base(self) -> None:
        module = load_codebase_health_module()
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            git(repo, "init", "-b", "master")
            git(repo, "config", "user.email", "gdd-test@example.invalid")
            git(repo, "config", "user.name", "GDD Test")
            (repo / "README.md").write_text("# test\n", encoding="utf-8")
            git(repo, "add", "README.md")
            git(repo, "commit", "-m", "initial")
            git(repo, "switch", "-c", "main")
            (repo / "legacy_large.py").write_text("\n".join("print('x')" for _ in range(12)), encoding="utf-8")
            git(repo, "add", "legacy_large.py")
            git(repo, "commit", "-m", "add legacy large file")

            report = module.build_report(repo, "changed", "main", 10)

        paths = {finding["path"] for finding in report["findings"]}
        self.assertNotIn("legacy_large.py", paths)

    def test_codebase_health_changed_mode_scans_worktree_when_base_is_missing(self) -> None:
        module = load_codebase_health_module()
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            git(repo, "init", "-b", "main")
            git(repo, "config", "user.email", "gdd-test@example.invalid")
            git(repo, "config", "user.name", "GDD Test")
            (repo / "README.md").write_text("# test\n", encoding="utf-8")
            git(repo, "add", "README.md")
            git(repo, "commit", "-m", "initial")
            git(repo, "switch", "-c", "feature")
            (repo / "large.py").write_text("\n".join("print('x')" for _ in range(12)), encoding="utf-8")
            git(repo, "add", "large.py")
            git(repo, "commit", "-m", "add large file")
            (repo / "untracked.py").write_text("print('x')\n", encoding="utf-8")

            report = module.build_report(repo, "changed", "origin/main", 10)

        paths = {finding["path"] for finding in report["findings"]}
        self.assertIn("large.py", paths)

    def test_codebase_health_changed_mode_scans_earlier_commits_when_base_is_missing(self) -> None:
        module = load_codebase_health_module()
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            git(repo, "init", "-b", "main")
            git(repo, "config", "user.email", "gdd-test@example.invalid")
            git(repo, "config", "user.name", "GDD Test")
            (repo / "README.md").write_text("# test\n", encoding="utf-8")
            git(repo, "add", "README.md")
            git(repo, "commit", "-m", "initial")
            git(repo, "switch", "-c", "feature")
            (repo / "earlier_large.py").write_text(
                "\n".join("print('x')" for _ in range(12)),
                encoding="utf-8",
            )
            git(repo, "add", "earlier_large.py")
            git(repo, "commit", "-m", "add earlier large file")
            (repo / "later.py").write_text("print('later')\n", encoding="utf-8")
            git(repo, "add", "later.py")
            git(repo, "commit", "-m", "add later file")

            report = module.build_report(repo, "changed", "origin/main", 10)

        paths = {finding["path"] for finding in report["findings"]}
        self.assertIn("earlier_large.py", paths)

    def test_codebase_health_changed_mode_fails_closed_when_base_is_missing_with_dirty_files(self) -> None:
        module = load_codebase_health_module()
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            git(repo, "init", "-b", "feature")
            git(repo, "config", "user.email", "gdd-test@example.invalid")
            git(repo, "config", "user.name", "GDD Test")
            (repo / "README.md").write_text("# test\n", encoding="utf-8")
            git(repo, "add", "README.md")
            git(repo, "commit", "-m", "initial")
            (repo / "committed_large.py").write_text("\n".join("print('x')" for _ in range(12)), encoding="utf-8")
            git(repo, "add", "committed_large.py")
            git(repo, "commit", "-m", "add committed large file")
            (repo / "dirty.py").write_text("print('dirty')\n", encoding="utf-8")

            with self.assertRaises(ValueError):
                module.build_report(repo, "changed", "origin/main", 10)

    def test_codebase_health_changed_mode_scans_initial_commit_when_base_is_missing(self) -> None:
        module = load_codebase_health_module()
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            git(repo, "init", "-b", "main")
            git(repo, "config", "user.email", "gdd-test@example.invalid")
            git(repo, "config", "user.name", "GDD Test")
            (repo / "large.py").write_text("\n".join("print('x')" for _ in range(12)), encoding="utf-8")
            git(repo, "add", "large.py")
            git(repo, "commit", "-m", "initial")

            report = module.build_report(repo, "changed", "origin/main", 10)

        paths = {finding["path"] for finding in report["findings"]}
        self.assertIn("large.py", paths)

    def test_codebase_health_baseline_allows_legacy_file_that_meets_reduction(self) -> None:
        module = load_codebase_health_module()
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            git(repo, "init", "-b", "main")
            git(repo, "config", "user.email", "gdd-test@example.invalid")
            git(repo, "config", "user.name", "GDD Test")
            (repo / "legacy.py").write_text("\n".join("print('x')" for _ in range(11)), encoding="utf-8")
            (repo / "gdd-codebase-health-baseline.json").write_text(
                json.dumps(
                    {
                        "large_files": [
                            {
                                "path": "legacy.py",
                                "current_lines": 12,
                                "target_lines": 10,
                                "reduce_by": 1,
                                "expires_on": "2099-12-31",
                                "reason": "accepted legacy module",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            git(repo, "add", "legacy.py", "gdd-codebase-health-baseline.json")
            git(repo, "commit", "-m", "baseline legacy")

            report = module.build_report(repo, "survey", "origin/main", 10)

        high_paths = {
            finding["path"]
            for finding in report["findings"]
            if finding["severity"] == "high"
        }
        self.assertNotIn("legacy.py", high_paths)

    def test_codebase_health_baseline_blocks_legacy_file_growth(self) -> None:
        module = load_codebase_health_module()
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            git(repo, "init", "-b", "main")
            git(repo, "config", "user.email", "gdd-test@example.invalid")
            git(repo, "config", "user.name", "GDD Test")
            (repo / "legacy.py").write_text("\n".join("print('x')" for _ in range(13)), encoding="utf-8")
            (repo / "gdd-codebase-health-baseline.json").write_text(
                json.dumps(
                    {
                        "large_files": [
                            {
                                "path": "legacy.py",
                                "current_lines": 12,
                                "target_lines": 10,
                                "reduce_by": 1,
                                "expires_on": "2099-12-31",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            git(repo, "add", "legacy.py", "gdd-codebase-health-baseline.json")
            git(repo, "commit", "-m", "baseline legacy growth")

            report = module.build_report(repo, "survey", "origin/main", 10)

        findings = [finding for finding in report["findings"] if finding["path"] == "legacy.py"]
        self.assertTrue(any(finding["category"] == "large_file" and finding["severity"] == "high" for finding in findings))
        self.assertTrue(any("baseline current" in finding["evidence"] for finding in findings))

    def test_codebase_health_baseline_warns_when_reduction_is_not_met(self) -> None:
        module = load_codebase_health_module()
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            git(repo, "init", "-b", "main")
            git(repo, "config", "user.email", "gdd-test@example.invalid")
            git(repo, "config", "user.name", "GDD Test")
            (repo / "legacy.py").write_text("\n".join("print('x')" for _ in range(12)), encoding="utf-8")
            (repo / "gdd-codebase-health-baseline.json").write_text(
                json.dumps(
                    {
                        "large_files": [
                            {
                                "path": "legacy.py",
                                "current_lines": 12,
                                "target_lines": 10,
                                "reduce_by": 1,
                                "expires_on": "2099-12-31",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            git(repo, "add", "legacy.py", "gdd-codebase-health-baseline.json")
            git(repo, "commit", "-m", "baseline legacy no reduction")

            report = module.build_report(repo, "survey", "origin/main", 10)

        findings = [finding for finding in report["findings"] if finding["path"] == "legacy.py"]
        self.assertTrue(any(finding["category"] == "large_file_baseline_reduction" and finding["severity"] == "medium" for finding in findings))
        self.assertFalse(any(finding["severity"] == "high" for finding in findings))

    def test_codebase_health_baseline_rejects_expired_exception(self) -> None:
        module = load_codebase_health_module()
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            git(repo, "init", "-b", "main")
            git(repo, "config", "user.email", "gdd-test@example.invalid")
            git(repo, "config", "user.name", "GDD Test")
            (repo / "legacy.py").write_text("\n".join("print('x')" for _ in range(12)), encoding="utf-8")
            (repo / "gdd-codebase-health-baseline.json").write_text(
                json.dumps(
                    {
                        "large_files": [
                            {
                                "path": "legacy.py",
                                "current_lines": 12,
                                "target_lines": 10,
                                "reduce_by": 1,
                                "expires_on": "2000-01-01",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            git(repo, "add", "legacy.py", "gdd-codebase-health-baseline.json")
            git(repo, "commit", "-m", "expired baseline")

            report = module.build_report(repo, "survey", "origin/main", 10)

        self.assertTrue(
            any(
                finding["category"] == "codebase_health_baseline"
                and finding["severity"] == "high"
                and finding["path"] == "legacy.py"
                for finding in report["findings"]
            )
        )

    def _write_complexity_fixture(self, repo: Path, branch_count: int) -> None:
        branches = "\n".join(
            f"    if value == {index}:\n        total += {index}" for index in range(branch_count)
        )
        (repo / "inventory.py").write_text(
            "def classify(value):\n"
            "    total = 0\n"
            f"{branches}\n"
            "    return total\n",
            encoding="utf-8",
        )

    def test_codebase_health_complexity_baseline_allows_legacy_function_that_meets_reduction(self) -> None:
        module = load_codebase_health_module()
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            git(repo, "init", "-b", "main")
            git(repo, "config", "user.email", "gdd-test@example.invalid")
            git(repo, "config", "user.name", "GDD Test")
            self._write_complexity_fixture(repo, 15)  # complexity 16
            (repo / "gdd-codebase-health-baseline.json").write_text(
                json.dumps(
                    {
                        "python_complexity": [
                            {
                                "path": "inventory.py",
                                "function": "classify",
                                "current_complexity": 17,
                                "target_complexity": 15,
                                "reduce_by": 1,
                                "expires_on": "2099-12-31",
                                "reason": "accepted legacy function",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            git(repo, "add", "inventory.py", "gdd-codebase-health-baseline.json")
            git(repo, "commit", "-m", "baseline legacy complexity")

            report = module.build_report(repo, "survey", "origin/main", 1500)

        findings = [finding for finding in report["findings"] if finding["path"] == "inventory.py"]
        self.assertFalse(findings)

    def test_codebase_health_complexity_baseline_blocks_legacy_function_growth(self) -> None:
        module = load_codebase_health_module()
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            git(repo, "init", "-b", "main")
            git(repo, "config", "user.email", "gdd-test@example.invalid")
            git(repo, "config", "user.name", "GDD Test")
            self._write_complexity_fixture(repo, 16)  # complexity 17
            (repo / "gdd-codebase-health-baseline.json").write_text(
                json.dumps(
                    {
                        "python_complexity": [
                            {
                                "path": "inventory.py",
                                "function": "classify",
                                "current_complexity": 16,
                                "target_complexity": 15,
                                "reduce_by": 1,
                                "expires_on": "2099-12-31",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            git(repo, "add", "inventory.py", "gdd-codebase-health-baseline.json")
            git(repo, "commit", "-m", "baseline legacy complexity growth")

            report = module.build_report(repo, "survey", "origin/main", 1500)

        findings = [finding for finding in report["findings"] if finding["path"] == "inventory.py"]
        self.assertTrue(any(finding["category"] == "python_cyclomatic_complexity" and finding["severity"] == "high" for finding in findings))
        self.assertTrue(any("baseline current" in finding["evidence"] for finding in findings))

    def test_codebase_health_complexity_baseline_warns_when_reduction_is_not_met(self) -> None:
        module = load_codebase_health_module()
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            git(repo, "init", "-b", "main")
            git(repo, "config", "user.email", "gdd-test@example.invalid")
            git(repo, "config", "user.name", "GDD Test")
            self._write_complexity_fixture(repo, 16)  # complexity 17
            (repo / "gdd-codebase-health-baseline.json").write_text(
                json.dumps(
                    {
                        "python_complexity": [
                            {
                                "path": "inventory.py",
                                "function": "classify",
                                "current_complexity": 17,
                                "target_complexity": 15,
                                "reduce_by": 1,
                                "expires_on": "2099-12-31",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            git(repo, "add", "inventory.py", "gdd-codebase-health-baseline.json")
            git(repo, "commit", "-m", "baseline legacy complexity no reduction")

            report = module.build_report(repo, "survey", "origin/main", 1500)

        findings = [finding for finding in report["findings"] if finding["path"] == "inventory.py"]
        self.assertTrue(any(finding["category"] == "python_cyclomatic_complexity_baseline_reduction" and finding["severity"] == "medium" for finding in findings))
        self.assertFalse(any(finding["severity"] == "high" for finding in findings))

    def test_codebase_health_complexity_baseline_rejects_expired_exception(self) -> None:
        module = load_codebase_health_module()
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            git(repo, "init", "-b", "main")
            git(repo, "config", "user.email", "gdd-test@example.invalid")
            git(repo, "config", "user.name", "GDD Test")
            self._write_complexity_fixture(repo, 16)  # complexity 17
            (repo / "gdd-codebase-health-baseline.json").write_text(
                json.dumps(
                    {
                        "python_complexity": [
                            {
                                "path": "inventory.py",
                                "function": "classify",
                                "current_complexity": 17,
                                "target_complexity": 15,
                                "reduce_by": 1,
                                "expires_on": "2000-01-01",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            git(repo, "add", "inventory.py", "gdd-codebase-health-baseline.json")
            git(repo, "commit", "-m", "expired complexity baseline")

            report = module.build_report(repo, "survey", "origin/main", 1500)

        self.assertTrue(
            any(
                finding["category"] == "codebase_health_baseline"
                and finding["severity"] == "high"
                and finding["path"] == "inventory.py"
                for finding in report["findings"]
            )
        )

    def test_codebase_health_complexity_baseline_only_covers_matching_function(self) -> None:
        module = load_codebase_health_module()
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            branches_a = "\n".join(f"    if value == {index}:\n        total += {index}" for index in range(16))
            branches_b = "\n".join(f"    if value == {index}:\n        total += {index}" for index in range(16))
            (repo / "inventory.py").write_text(
                "def classify(value):\n"
                "    total = 0\n"
                f"{branches_a}\n"
                "    return total\n\n\n"
                "def other(value):\n"
                "    total = 0\n"
                f"{branches_b}\n"
                "    return total\n",
                encoding="utf-8",
            )
            baselines = {
                ("inventory.py", "classify"): module.PythonComplexityBaseline(
                    path="inventory.py",
                    function="classify",
                    current_complexity=18,
                    target_complexity=15,
                    reduce_by=1,
                )
            }

            findings = module.collect_python_structure_findings(
                repo, [repo / "inventory.py"], complexity_baselines=baselines
            )

        self.assertFalse(any(finding.evidence.startswith("classify ") for finding in findings))
        self.assertTrue(any(finding.evidence.startswith("other ") and finding.severity == "high" for finding in findings))

    def _write_function_count_fixture(self, repo: Path, function_count: int) -> None:
        (repo / "inventory.py").write_text(
            "\n\n".join(f"def func_{index}():\n    return {index}" for index in range(function_count)),
            encoding="utf-8",
        )

    def test_codebase_health_function_count_baseline_allows_legacy_file_that_meets_reduction(self) -> None:
        module = load_codebase_health_module()
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            git(repo, "init", "-b", "main")
            git(repo, "config", "user.email", "gdd-test@example.invalid")
            git(repo, "config", "user.name", "GDD Test")
            self._write_function_count_fixture(repo, 81)
            (repo / "gdd-codebase-health-baseline.json").write_text(
                json.dumps(
                    {
                        "python_function_count": [
                            {
                                "path": "inventory.py",
                                "current_count": 82,
                                "target_count": 80,
                                "reduce_by": 1,
                                "expires_on": "2099-12-31",
                                "reason": "accepted legacy module",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            git(repo, "add", "inventory.py", "gdd-codebase-health-baseline.json")
            git(repo, "commit", "-m", "baseline legacy function count")

            report = module.build_report(repo, "survey", "origin/main", 1500)

        findings = [finding for finding in report["findings"] if finding["path"] == "inventory.py"]
        self.assertFalse(findings)

    def test_codebase_health_function_count_baseline_blocks_legacy_file_growth(self) -> None:
        module = load_codebase_health_module()
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            git(repo, "init", "-b", "main")
            git(repo, "config", "user.email", "gdd-test@example.invalid")
            git(repo, "config", "user.name", "GDD Test")
            self._write_function_count_fixture(repo, 82)
            (repo / "gdd-codebase-health-baseline.json").write_text(
                json.dumps(
                    {
                        "python_function_count": [
                            {
                                "path": "inventory.py",
                                "current_count": 81,
                                "target_count": 80,
                                "reduce_by": 1,
                                "expires_on": "2099-12-31",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            git(repo, "add", "inventory.py", "gdd-codebase-health-baseline.json")
            git(repo, "commit", "-m", "baseline legacy function count growth")

            report = module.build_report(repo, "survey", "origin/main", 1500)

        findings = [finding for finding in report["findings"] if finding["path"] == "inventory.py"]
        self.assertTrue(any(finding["category"] == "python_function_count" and finding["severity"] == "high" for finding in findings))
        self.assertTrue(any("baseline current" in finding["evidence"] for finding in findings))

    def test_codebase_health_function_count_baseline_warns_when_reduction_is_not_met(self) -> None:
        module = load_codebase_health_module()
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            git(repo, "init", "-b", "main")
            git(repo, "config", "user.email", "gdd-test@example.invalid")
            git(repo, "config", "user.name", "GDD Test")
            self._write_function_count_fixture(repo, 82)
            (repo / "gdd-codebase-health-baseline.json").write_text(
                json.dumps(
                    {
                        "python_function_count": [
                            {
                                "path": "inventory.py",
                                "current_count": 82,
                                "target_count": 80,
                                "reduce_by": 1,
                                "expires_on": "2099-12-31",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            git(repo, "add", "inventory.py", "gdd-codebase-health-baseline.json")
            git(repo, "commit", "-m", "baseline legacy function count no reduction")

            report = module.build_report(repo, "survey", "origin/main", 1500)

        findings = [finding for finding in report["findings"] if finding["path"] == "inventory.py"]
        self.assertTrue(any(finding["category"] == "python_function_count_baseline_reduction" and finding["severity"] == "medium" for finding in findings))
        self.assertFalse(any(finding["severity"] == "high" for finding in findings))

    def test_codebase_health_function_count_baseline_rejects_expired_exception(self) -> None:
        module = load_codebase_health_module()
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            git(repo, "init", "-b", "main")
            git(repo, "config", "user.email", "gdd-test@example.invalid")
            git(repo, "config", "user.name", "GDD Test")
            self._write_function_count_fixture(repo, 82)
            (repo / "gdd-codebase-health-baseline.json").write_text(
                json.dumps(
                    {
                        "python_function_count": [
                            {
                                "path": "inventory.py",
                                "current_count": 82,
                                "target_count": 80,
                                "reduce_by": 1,
                                "expires_on": "2000-01-01",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            git(repo, "add", "inventory.py", "gdd-codebase-health-baseline.json")
            git(repo, "commit", "-m", "expired function count baseline")

            report = module.build_report(repo, "survey", "origin/main", 1500)

        self.assertTrue(
            any(
                finding["category"] == "codebase_health_baseline"
                and finding["severity"] == "high"
                and finding["path"] == "inventory.py"
                for finding in report["findings"]
            )
        )

    def test_codebase_health_changed_mode_decodes_non_ascii_git_paths(self) -> None:
        module = load_codebase_health_module()
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            git(repo, "init", "-b", "main")
            git(repo, "config", "user.email", "gdd-test@example.invalid")
            git(repo, "config", "user.name", "GDD Test")
            (repo / "日本語.py").write_text("\n".join("print('x')" for _ in range(12)), encoding="utf-8")
            git(repo, "add", "日本語.py")
            git(repo, "commit", "-m", "initial")

            report = module.build_report(repo, "changed", "origin/main", 10)

        paths = {finding["path"] for finding in report["findings"]}
        self.assertIn("日本語.py", paths)

    def test_codebase_health_changed_mode_includes_untracked_files(self) -> None:
        module = load_codebase_health_module()
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            git(repo, "init", "-b", "main")
            git(repo, "config", "user.email", "gdd-test@example.invalid")
            git(repo, "config", "user.name", "GDD Test")
            (repo / "README.md").write_text("# test\n", encoding="utf-8")
            git(repo, "add", "README.md")
            git(repo, "commit", "-m", "initial")
            git(repo, "switch", "-c", "feature")
            (repo / "untracked_large.py").write_text(
                "\n".join("print('x')" for _ in range(12)),
                encoding="utf-8",
            )

            report = module.build_report(repo, "changed", "main", 10)

        paths = {finding["path"] for finding in report["findings"]}
        self.assertIn("untracked_large.py", paths)

    def test_codebase_health_changed_mode_checks_added_dependency_manifests(self) -> None:
        module = load_codebase_health_module()
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            git(repo, "init", "-b", "main")
            git(repo, "config", "user.email", "gdd-test@example.invalid")
            git(repo, "config", "user.name", "GDD Test")
            (repo / "README.md").write_text("# test\n", encoding="utf-8")
            git(repo, "add", "README.md")
            git(repo, "commit", "-m", "initial")
            git(repo, "switch", "-c", "feature")
            (repo / "pyproject.toml").write_text("[project]\nname = 'demo'\n", encoding="utf-8")
            git(repo, "add", "pyproject.toml")
            git(repo, "commit", "-m", "add manifest")

            report = module.build_report(repo, "changed", "main", 1500)

        categories = {finding["category"] for finding in report["findings"]}
        paths = {finding["path"] for finding in report["findings"]}
        self.assertIn("missing_lockfile", categories)
        self.assertIn("pyproject.toml", paths)

    def test_codebase_health_changed_mode_checks_nested_dependency_manifests(self) -> None:
        module = load_codebase_health_module()
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            git(repo, "init", "-b", "main")
            git(repo, "config", "user.email", "gdd-test@example.invalid")
            git(repo, "config", "user.name", "GDD Test")
            (repo / "README.md").write_text("# test\n", encoding="utf-8")
            git(repo, "add", "README.md")
            git(repo, "commit", "-m", "initial")
            git(repo, "switch", "-c", "feature")
            (repo / "apps" / "web").mkdir(parents=True)
            (repo / "apps" / "web" / "package.json").write_text('{"scripts":{}}\n', encoding="utf-8")
            git(repo, "add", "apps/web/package.json")
            git(repo, "commit", "-m", "add nested manifest")

            report = module.build_report(repo, "changed", "main", 1500)

        categories = {finding["category"] for finding in report["findings"]}
        paths = {finding["path"] for finding in report["findings"]}
        self.assertIn("missing_lockfile", categories)
        self.assertIn("apps/web/package.json", paths)

    def test_codebase_health_changed_mode_detects_lockfile_deletion(self) -> None:
        module = load_codebase_health_module()
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            git(repo, "init", "-b", "main")
            git(repo, "config", "user.email", "gdd-test@example.invalid")
            git(repo, "config", "user.name", "GDD Test")
            (repo / "package.json").write_text('{"scripts":{}}\n', encoding="utf-8")
            (repo / "package-lock.json").write_text("{}\n", encoding="utf-8")
            git(repo, "add", "package.json", "package-lock.json")
            git(repo, "commit", "-m", "initial")
            git(repo, "switch", "-c", "feature")
            (repo / "package-lock.json").unlink()
            git(repo, "add", "package-lock.json")
            git(repo, "commit", "-m", "remove lockfile")

            report = module.build_report(repo, "changed", "main", 1500)

        categories = {finding["category"] for finding in report["findings"]}
        paths = {finding["path"] for finding in report["findings"]}
        self.assertIn("missing_lockfile", categories)
        self.assertIn("package.json", paths)

    def test_codebase_health_changed_mode_skips_deleted_manifest(self) -> None:
        module = load_codebase_health_module()
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            git(repo, "init", "-b", "main")
            git(repo, "config", "user.email", "gdd-test@example.invalid")
            git(repo, "config", "user.name", "GDD Test")
            (repo / "package.json").write_text('{"scripts":{}}\n', encoding="utf-8")
            (repo / "package-lock.json").write_text("{}\n", encoding="utf-8")
            git(repo, "add", "package.json", "package-lock.json")
            git(repo, "commit", "-m", "initial")
            git(repo, "switch", "-c", "feature")
            (repo / "package.json").unlink()
            git(repo, "add", "package.json")
            git(repo, "commit", "-m", "remove manifest")

            report = module.build_report(repo, "changed", "main", 1500)

        findings = [
            finding
            for finding in report["findings"]
            if finding["category"] == "missing_lockfile" and finding["path"] == "package.json"
        ]
        self.assertEqual(findings, [])

    def test_codebase_health_accepts_bun_text_lockfile(self) -> None:
        module = load_codebase_health_module()
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            git(repo, "init", "-b", "main")
            (repo / "package.json").write_text('{"scripts":{}}\n', encoding="utf-8")
            (repo / "bun.lock").write_text("# bun lock\n", encoding="utf-8")

            report = module.build_report(repo, "survey", "origin/main", 1500)

        findings = [
            finding
            for finding in report["findings"]
            if finding["category"] == "missing_lockfile" and finding["path"] == "package.json"
        ]
        self.assertEqual(findings, [])

    def test_codebase_health_large_go_test_file_is_medium(self) -> None:
        module = load_codebase_health_module()
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "pkg").mkdir()
            path = repo / "pkg" / "foo_test.go"
            path.write_text("\n".join("func TestX() {}" for _ in range(12)), encoding="utf-8")

            findings = module.collect_large_file_findings(repo, [path], 10)

        self.assertEqual(findings[0].severity, "medium")

    def test_codebase_health_large_jest_tests_file_is_medium(self) -> None:
        module = load_codebase_health_module()
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            path = repo / "src" / "__tests__" / "fixture-helper.ts"
            path.parent.mkdir(parents=True)
            path.write_text("\n".join("export const value = 1;" for _ in range(12)), encoding="utf-8")

            findings = module.collect_large_file_findings(repo, [path], 10)

        self.assertEqual(findings[0].severity, "medium")

    def test_codebase_health_test_classification_uses_repo_relative_path(self) -> None:
        module = load_codebase_health_module()
        with tempfile.TemporaryDirectory() as tmp:
            parent = Path(tmp) / "tests-parent"
            repo = parent / "repo"
            (repo / "src").mkdir(parents=True)
            path = repo / "src" / "large.py"
            path.write_text("\n".join("print('x')" for _ in range(12)), encoding="utf-8")

            findings = module.collect_large_file_findings(repo, [path], 10)

        self.assertEqual(findings[0].severity, "high")

    def test_codebase_health_flags_python_function_count_accretion(self) -> None:
        module = load_codebase_health_module()
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            path = repo / "inventory.py"
            path.write_text(
                "\n\n".join(f"def func_{index}():\n    return {index}" for index in range(81)),
                encoding="utf-8",
            )

            findings = module.collect_python_structure_findings(repo, [path])

        self.assertEqual(findings[0].category, "python_function_count")
        self.assertEqual(findings[0].severity, "high")
        self.assertIn("81 functions > fail limit 80", findings[0].evidence)

    def test_codebase_health_warns_on_python_function_count_before_fail_limit(self) -> None:
        module = load_codebase_health_module()
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            path = repo / "inventory.py"
            path.write_text(
                "\n\n".join(f"def func_{index}():\n    return {index}" for index in range(41)),
                encoding="utf-8",
            )

            findings = module.collect_python_structure_findings(repo, [path])

        self.assertEqual(findings[0].category, "python_function_count")
        self.assertEqual(findings[0].severity, "medium")
        self.assertIn("41 functions > warn limit 40", findings[0].evidence)

    def test_codebase_health_flags_python_cyclomatic_complexity(self) -> None:
        module = load_codebase_health_module()
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            path = repo / "inventory.py"
            branches = "\n".join(
                f"    if value == {index}:\n        total += {index}" for index in range(16)
            )
            path.write_text(
                "def classify(value):\n"
                "    total = 0\n"
                f"{branches}\n"
                "    return total\n",
                encoding="utf-8",
            )

            findings = module.collect_python_structure_findings(repo, [path])

        self.assertEqual(findings[0].category, "python_cyclomatic_complexity")
        self.assertEqual(findings[0].severity, "high")
        self.assertIn("classify complexity 17 > limit 15", findings[0].evidence)

    @unittest.skipUnless(hasattr(ast, "Match"), "requires Python 3.10+ match AST")
    def test_codebase_health_counts_python_match_cases_as_complexity(self) -> None:
        module = load_codebase_health_module()
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            path = repo / "inventory.py"
            cases = "\n".join(
                f"        case {index}:\n            return {index}" for index in range(16)
            )
            path.write_text(
                "def classify(value):\n"
                "    match value:\n"
                f"{cases}\n"
                "        case _:\n"
                "            return -1\n",
                encoding="utf-8",
            )

            findings = module.collect_python_structure_findings(repo, [path])

        self.assertEqual(findings[0].category, "python_cyclomatic_complexity")
        self.assertIn("classify complexity 18 > limit 15", findings[0].evidence)

    def test_codebase_health_does_not_count_nested_function_branches_against_outer_function(self) -> None:
        module = load_codebase_health_module()
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            path = repo / "inventory.py"
            branches = "\n".join(
                f"        if value == {index}:\n            total += {index}" for index in range(16)
            )
            path.write_text(
                "def outer(value):\n"
                "    def inner():\n"
                "        total = 0\n"
                f"{branches}\n"
                "        return total\n"
                "    return inner()\n",
                encoding="utf-8",
            )

            findings = module.collect_python_structure_findings(repo, [path])

        evidence = [finding.evidence for finding in findings]
        self.assertIn("inner complexity 17 > limit 15", evidence)
        self.assertNotIn("outer complexity 17 > limit 15", evidence)

    def test_codebase_health_report_includes_python_structure_findings(self) -> None:
        module = load_codebase_health_module()
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            git(repo, "init", "-b", "main")
            git(repo, "config", "user.email", "gdd-test@example.invalid")
            git(repo, "config", "user.name", "GDD Test")
            (repo / "README.md").write_text("# test\n", encoding="utf-8")
            git(repo, "add", "README.md")
            git(repo, "commit", "-m", "initial")
            git(repo, "switch", "-c", "feature")
            (repo / "inventory.py").write_text(
                "\n\n".join(f"def func_{index}():\n    return {index}" for index in range(81)),
                encoding="utf-8",
            )
            git(repo, "add", "inventory.py")
            git(repo, "commit", "-m", "add inventory module")

            report = module.build_report(repo, "changed", "origin/main", 1500)

        categories = {finding["category"] for finding in report["findings"]}
        self.assertIn("python_function_count", categories)

    def test_codebase_health_accepts_workspace_root_lockfile_for_nested_manifest(self) -> None:
        module = load_codebase_health_module()
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            git(repo, "init", "-b", "main")
            (repo / "package.json").write_text('{"workspaces":["apps/*"]}\n', encoding="utf-8")
            (repo / "package-lock.json").write_text("{}\n", encoding="utf-8")
            (repo / "apps" / "web").mkdir(parents=True)
            (repo / "apps" / "web" / "package.json").write_text('{"scripts":{}}\n', encoding="utf-8")

            report = module.build_report(repo, "survey", "origin/main", 1500)

        findings = [
            finding
            for finding in report["findings"]
            if finding["category"] == "missing_lockfile" and finding["path"] == "apps/web/package.json"
        ]
        self.assertEqual(findings, [])

    def test_codebase_health_does_not_overmatch_workspace_glob_segments(self) -> None:
        module = load_codebase_health_module()
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            git(repo, "init", "-b", "main")
            (repo / "package.json").write_text('{"workspaces":["apps/*"]}\n', encoding="utf-8")
            (repo / "package-lock.json").write_text("{}\n", encoding="utf-8")
            nested = repo / "apps" / "web" / "examples" / "demo"
            nested.mkdir(parents=True)
            (nested / "package.json").write_text('{"scripts":{}}\n', encoding="utf-8")

            report = module.build_report(repo, "survey", "origin/main", 1500)

        findings = [
            finding
            for finding in report["findings"]
            if finding["category"] == "missing_lockfile" and finding["path"] == "apps/web/examples/demo/package.json"
        ]
        self.assertEqual(len(findings), 1)

    def test_codebase_health_rejects_unrelated_parent_lockfile_for_nested_manifest(self) -> None:
        module = load_codebase_health_module()
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            git(repo, "init", "-b", "main")
            (repo / "package.json").write_text('{"scripts":{}}\n', encoding="utf-8")
            (repo / "package-lock.json").write_text("{}\n", encoding="utf-8")
            (repo / "examples" / "web").mkdir(parents=True)
            (repo / "examples" / "web" / "package.json").write_text('{"scripts":{}}\n', encoding="utf-8")

            report = module.build_report(repo, "survey", "origin/main", 1500)

        findings = [
            finding
            for finding in report["findings"]
            if finding["category"] == "missing_lockfile" and finding["path"] == "examples/web/package.json"
        ]
        self.assertEqual(len(findings), 1)

    def test_codebase_health_accepts_pnpm_workspace_root_lockfile_for_nested_manifest(self) -> None:
        module = load_codebase_health_module()
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            git(repo, "init", "-b", "main")
            (repo / "pnpm-workspace.yaml").write_text("packages:\n  - 'apps/*'\n", encoding="utf-8")
            (repo / "pnpm-lock.yaml").write_text("lockfileVersion: '9.0'\n", encoding="utf-8")
            (repo / "apps" / "web").mkdir(parents=True)
            (repo / "apps" / "web" / "package.json").write_text('{"scripts":{}}\n', encoding="utf-8")

            report = module.build_report(repo, "survey", "origin/main", 1500)

        findings = [
            finding
            for finding in report["findings"]
            if finding["category"] == "missing_lockfile" and finding["path"] == "apps/web/package.json"
        ]
        self.assertEqual(findings, [])

    def test_codebase_health_allows_dependency_free_go_module_without_sum(self) -> None:
        module = load_codebase_health_module()
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            git(repo, "init", "-b", "main")
            (repo / "go.mod").write_text("module example.com/demo\n\ngo 1.22\n", encoding="utf-8")

            report = module.build_report(repo, "survey", "origin/main", 1500)

        findings = [
            finding
            for finding in report["findings"]
            if finding["category"] == "missing_lockfile" and finding["path"] == "go.mod"
        ]
        self.assertEqual(findings, [])

    def test_codebase_health_allows_local_replaced_go_module_without_sum(self) -> None:
        module = load_codebase_health_module()
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            git(repo, "init", "-b", "main")
            (repo / "go.mod").write_text(
                "\n".join(
                    [
                        "module example.com/demo",
                        "",
                        "go 1.22",
                        "",
                        "require example.com/local v0.0.0",
                        "replace example.com/local => ./local",
                    ]
                ),
                encoding="utf-8",
            )

            report = module.build_report(repo, "survey", "origin/main", 1500)

        findings = [
            finding
            for finding in report["findings"]
            if finding["category"] == "missing_lockfile" and finding["path"] == "go.mod"
        ]
        self.assertEqual(findings, [])

    def test_codebase_health_requires_local_lockfile_for_nested_go_module(self) -> None:
        module = load_codebase_health_module()
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            git(repo, "init", "-b", "main")
            (repo / "go.mod").write_text("module example.com/root\n", encoding="utf-8")
            (repo / "go.sum").write_text("example.com/root v0.0.0 h1:abc\n", encoding="utf-8")
            (repo / "tools").mkdir()
            (repo / "tools" / "go.mod").write_text(
                "module example.com/root/tools\n\ngo 1.22\n\nrequire golang.org/x/sync v0.7.0\n",
                encoding="utf-8",
            )

            report = module.build_report(repo, "survey", "origin/main", 1500)

        findings = [
            finding
            for finding in report["findings"]
            if finding["category"] == "missing_lockfile" and finding["path"] == "tools/go.mod"
        ]
        self.assertEqual(len(findings), 1)

    def test_codebase_health_survey_recognizes_colocated_test_files(self) -> None:
        module = load_codebase_health_module()
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            git(repo, "init", "-b", "main")
            (repo / "foo_test.go").write_text("package main\n", encoding="utf-8")
            (repo / ".github" / "workflows").mkdir(parents=True)
            (repo / ".github" / "workflows" / "ci.yml").write_text("name: ci\n", encoding="utf-8")

            report = module.build_report(repo, "survey", "origin/main", 1500)

        categories = {finding["category"] for finding in report["findings"]}
        self.assertNotIn("missing_tests_directory", categories)

    def test_codebase_health_survey_mode_includes_untracked_scaffold_files(self) -> None:
        module = load_codebase_health_module()
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            git(repo, "init", "-b", "main")
            (repo / "pyproject.toml").write_text("[project]\nname = 'demo'\n", encoding="utf-8")
            (repo / "large.py").write_text("\n".join("print('x')" for _ in range(12)), encoding="utf-8")

            report = module.build_report(repo, "survey", "origin/main", 10)

        categories = {finding["category"] for finding in report["findings"]}
        paths = {finding["path"] for finding in report["findings"]}
        self.assertGreaterEqual(report["summary"]["files_scanned"], 2)
        self.assertIn("large_file", categories)
        self.assertIn("missing_lockfile", categories)
        self.assertIn("large.py", paths)
        self.assertIn("pyproject.toml", paths)

    def test_codebase_health_survey_recognizes_nested_tests_and_non_github_ci(self) -> None:
        module = load_codebase_health_module()
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            git(repo, "init", "-b", "main")
            (repo / "src" / "service" / "tests").mkdir(parents=True)
            (repo / "src" / "service" / "tests" / "test_app.py").write_text(
                "def test_app():\n    assert True\n",
                encoding="utf-8",
            )
            (repo / ".gitlab-ci.yml").write_text("test:\n  script: pytest\n", encoding="utf-8")

            report = module.build_report(repo, "survey", "origin/main", 1500)

        categories = {finding["category"] for finding in report["findings"]}
        self.assertNotIn("missing_tests_directory", categories)
        self.assertNotIn("missing_ci_workflow", categories)


if __name__ == "__main__":
    unittest.main()
