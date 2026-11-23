"""`scripts/gdd-codebase-health.py` の baseline（current_lines / current_count / current_complexity）を、pre-PR ref（merge-base）の実測値で検査する契約テスト。

`test_engineering_baseline_architecture_contract.py` から分けた。helper の `git`・`load_codebase_health_module` は元のファイルから名前だけを import する。
"""
from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from test_engineering_baseline_architecture_contract import git, load_codebase_health_module


class TestCodebaseHealthPrePrRefMeasurement(unittest.TestCase):
    """baseline の current_lines / current_count / current_complexity は pre-PR ref
    (merge-base) の実測値を超えてはならない (GDD を使う別の repo の PR での
    レビュー bot の round-9 指摘の再発防止: baseline 値が PR のワーキングツリー（rebase 後）から
    採取されたことを reason 自身が認めていた)。3 セクション全てに同じ provenance
    保証を適用する（1 セクションだけ塞いでも他 2 セクションに同型の脆弱性が残るため）。"""

    def test_codebase_health_flags_large_file_baseline_inflated_beyond_pre_pr_ref(self) -> None:
        module = load_codebase_health_module()
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            git(repo, "init", "-b", "main")
            git(repo, "config", "user.email", "gdd-test@example.invalid")
            git(repo, "config", "user.name", "GDD Test")
            (repo / "legacy.py").write_text("\n".join("print('x')" for _ in range(20)), encoding="utf-8")
            git(repo, "add", "legacy.py")
            git(repo, "commit", "-m", "pre-PR state: legacy.py at 20 lines")

            git(repo, "switch", "-c", "feature")
            (repo / "legacy.py").write_text("\n".join("print('x')" for _ in range(25)), encoding="utf-8")
            (repo / "gdd-codebase-health-baseline.json").write_text(
                json.dumps(
                    {
                        "large_files": [
                            {
                                "path": "legacy.py",
                                "current_lines": 25,
                                "target_lines": 15,
                                "reduce_by": 5,
                                "reason": "captured from the working tree during this PR's repeated rebases",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            git(repo, "add", "legacy.py", "gdd-codebase-health-baseline.json")
            git(repo, "commit", "-m", "grow legacy.py and accept an inflated baseline")

            report = module.build_report(repo, "changed", "main", 10)

        matching = [
            finding
            for finding in report["findings"]
            if finding["category"] == "codebase_health_baseline"
            and finding["path"] == "legacy.py"
            and finding["severity"] == "high"
        ]
        self.assertTrue(
            matching and "pre-PR ref" in matching[0]["evidence"],
            f"expected a high codebase_health_baseline finding about the pre-PR ref, got: {report['findings']}",
        )

    def test_codebase_health_allows_large_file_baseline_matching_pre_pr_ref(self) -> None:
        module = load_codebase_health_module()
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            git(repo, "init", "-b", "main")
            git(repo, "config", "user.email", "gdd-test@example.invalid")
            git(repo, "config", "user.name", "GDD Test")
            (repo / "legacy.py").write_text("\n".join("print('x')" for _ in range(20)), encoding="utf-8")
            git(repo, "add", "legacy.py")
            git(repo, "commit", "-m", "pre-PR state: legacy.py at 20 lines")

            git(repo, "switch", "-c", "feature")
            (repo / "gdd-codebase-health-baseline.json").write_text(
                json.dumps(
                    {
                        "large_files": [
                            {
                                "path": "legacy.py",
                                "current_lines": 20,
                                "target_lines": 15,
                                "reduce_by": 5,
                                "reason": "true pre-PR debt measured at the merge-base with main",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            git(repo, "add", "gdd-codebase-health-baseline.json")
            git(repo, "commit", "-m", "accept legacy.py baseline matching the pre-PR state")

            report = module.build_report(repo, "changed", "main", 10)

        provenance_findings = [
            finding
            for finding in report["findings"]
            if finding["category"] == "codebase_health_baseline" and finding["path"] == "legacy.py"
        ]
        self.assertEqual(provenance_findings, [])

    def test_codebase_health_flags_function_count_baseline_inflated_beyond_pre_pr_ref(self) -> None:
        module = load_codebase_health_module()
        pre_pr_source = "\n".join(f"def f{i}():\n    pass\n" for i in range(85))
        pr_source = pre_pr_source + "\n".join(f"def g{i}():\n    pass\n" for i in range(5))
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            git(repo, "init", "-b", "main")
            git(repo, "config", "user.email", "gdd-test@example.invalid")
            git(repo, "config", "user.name", "GDD Test")
            (repo / "many_functions.py").write_text(pre_pr_source, encoding="utf-8")
            git(repo, "add", "many_functions.py")
            git(repo, "commit", "-m", "pre-PR state: 85 functions")

            git(repo, "switch", "-c", "feature")
            (repo / "many_functions.py").write_text(pr_source, encoding="utf-8")
            (repo / "gdd-codebase-health-baseline.json").write_text(
                json.dumps(
                    {
                        "python_function_count": [
                            {
                                "path": "many_functions.py",
                                "current_count": 90,
                                "target_count": 80,
                                "reduce_by": 5,
                                "reason": "captured from the working tree during this PR's repeated rebases",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            git(repo, "add", "many_functions.py", "gdd-codebase-health-baseline.json")
            git(repo, "commit", "-m", "grow many_functions.py and accept an inflated baseline")

            report = module.build_report(repo, "changed", "main", 1500)

        matching = [
            finding
            for finding in report["findings"]
            if finding["category"] == "codebase_health_baseline"
            and finding["path"] == "many_functions.py"
            and finding["severity"] == "high"
        ]
        self.assertTrue(
            matching and "pre-PR ref" in matching[0]["evidence"],
            f"expected a high codebase_health_baseline finding about the pre-PR ref, got: {report['findings']}",
        )

    def test_codebase_health_flags_complexity_baseline_inflated_beyond_pre_pr_ref(self) -> None:
        module = load_codebase_health_module()
        pre_pr_source = "def f():\n" + "".join(f"    if a{i}:\n        pass\n" for i in range(16))
        pr_source = pre_pr_source + "".join(f"    if b{i}:\n        pass\n" for i in range(4))
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            git(repo, "init", "-b", "main")
            git(repo, "config", "user.email", "gdd-test@example.invalid")
            git(repo, "config", "user.name", "GDD Test")
            (repo / "complex.py").write_text(pre_pr_source, encoding="utf-8")
            git(repo, "add", "complex.py")
            git(repo, "commit", "-m", "pre-PR state: f has complexity 17")

            git(repo, "switch", "-c", "feature")
            (repo / "complex.py").write_text(pr_source, encoding="utf-8")
            (repo / "gdd-codebase-health-baseline.json").write_text(
                json.dumps(
                    {
                        "python_complexity": [
                            {
                                "path": "complex.py",
                                "function": "f",
                                "current_complexity": 21,
                                "target_complexity": 15,
                                "reduce_by": 5,
                                "reason": "captured from the working tree during this PR's repeated rebases",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            git(repo, "add", "complex.py", "gdd-codebase-health-baseline.json")
            git(repo, "commit", "-m", "grow complex.py and accept an inflated baseline")

            report = module.build_report(repo, "changed", "main", 1500)

        matching = [
            finding
            for finding in report["findings"]
            if finding["category"] == "codebase_health_baseline"
            and finding["path"] == "complex.py"
            and finding["severity"] == "high"
        ]
        self.assertTrue(
            matching and "pre-PR ref" in matching[0]["evidence"],
            f"expected a high codebase_health_baseline finding about the pre-PR ref, got: {report['findings']}",
        )

    def test_codebase_health_skips_pre_pr_ref_check_for_a_brand_new_file(self) -> None:
        """merge-base に存在しない新規ファイルは pre-PR ref 検証の対象外（比較対象が無い）。"""
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
            (repo / "brand_new.py").write_text("\n".join("print('x')" for _ in range(20)), encoding="utf-8")
            (repo / "gdd-codebase-health-baseline.json").write_text(
                json.dumps(
                    {
                        "large_files": [
                            {
                                "path": "brand_new.py",
                                "current_lines": 20,
                                "target_lines": 15,
                                "reduce_by": 5,
                                "reason": "new module intentionally starts above the limit",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            git(repo, "add", "brand_new.py", "gdd-codebase-health-baseline.json")
            git(repo, "commit", "-m", "add brand new large module with a baseline exception")

            report = module.build_report(repo, "changed", "main", 10)

        provenance_findings = [
            finding
            for finding in report["findings"]
            if finding["category"] == "codebase_health_baseline" and finding["path"] == "brand_new.py"
        ]
        self.assertEqual(provenance_findings, [])

    def test_resolve_pre_pr_ref_returns_none_when_base_is_unresolvable(self) -> None:
        module = load_codebase_health_module()
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            git(repo, "init", "-b", "feature")
            git(repo, "config", "user.email", "gdd-test@example.invalid")
            git(repo, "config", "user.name", "GDD Test")
            (repo / "README.md").write_text("# test\n", encoding="utf-8")
            git(repo, "add", "README.md")
            git(repo, "commit", "-m", "initial")

            self.assertIsNone(module.resolve_pre_pr_ref(repo, "origin/main"))

    def test_resolve_pre_pr_ref_returns_merge_base_sha(self) -> None:
        module = load_codebase_health_module()
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            git(repo, "init", "-b", "main")
            git(repo, "config", "user.email", "gdd-test@example.invalid")
            git(repo, "config", "user.name", "GDD Test")
            (repo / "README.md").write_text("# test\n", encoding="utf-8")
            git(repo, "add", "README.md")
            git(repo, "commit", "-m", "initial")
            main_sha = subprocess.run(
                ["git", "rev-parse", "HEAD"], cwd=repo, check=True, text=True, stdout=subprocess.PIPE
            ).stdout.strip()

            git(repo, "switch", "-c", "feature")
            (repo / "feature.py").write_text("print('feature')\n", encoding="utf-8")
            git(repo, "add", "feature.py")
            git(repo, "commit", "-m", "feature work")

            self.assertEqual(module.resolve_pre_pr_ref(repo, "main"), main_sha)


if __name__ == "__main__":
    unittest.main()
