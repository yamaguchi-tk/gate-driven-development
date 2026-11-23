"""Contract tests for steering retention."""
from __future__ import annotations

import unittest
import subprocess
import sys
import tempfile
from pathlib import Path


from _paths import PLUGIN_ROOT


class SteeringRetentionContractTests(unittest.TestCase):

    def test_post_merge_steering_retention_scenario_passes(self) -> None:
        subprocess.run(
            [
                sys.executable,
                str(PLUGIN_ROOT / "scripts" / "run-gdd-scenario-evals.py"),
                "--fixture",
                str(PLUGIN_ROOT / "tests" / "fixtures" / "gdd-steering-retention-scenarios.json"),
                "--input-dir",
                str(PLUGIN_ROOT / "tests" / "fixtures" / "gdd-scenario-eval-inputs"),
                "--require-critical-pass",
            ],
            check=True,
            capture_output=True,
            text=True,
        )

    def test_raw_task_steering_ci_backstop_rejects_tracked_task_dirs(self) -> None:
        script = PLUGIN_ROOT / "scripts" / "check-no-raw-task-steering.py"
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True, text=True)
            steering = repo / ".steering" / "20260613-task"
            steering.mkdir(parents=True)
            (steering / "state.md").write_text("Next Action=done\n", encoding="utf-8")
            subprocess.run(["git", "add", ".steering/20260613-task/state.md"], cwd=repo, check=True)

            result = subprocess.run(
                [sys.executable, str(script), "--root", str(repo)],
                capture_output=True,
                text=True,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("raw task steering files are tracked", result.stderr)
        self.assertIn(".steering/20260613-task/state.md", result.stderr)

    def test_raw_task_steering_ci_backstop_rejects_root_steering_state_files(self) -> None:
        script = PLUGIN_ROOT / "scripts" / "check-no-raw-task-steering.py"
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True, text=True)
            steering = repo / ".steering"
            steering.mkdir()
            (steering / "state.md").write_text("Next Action=done\n", encoding="utf-8")
            subprocess.run(["git", "add", ".steering/state.md"], cwd=repo, check=True)

            result = subprocess.run(
                [sys.executable, str(script), "--root", str(repo)],
                capture_output=True,
                text=True,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("raw task steering files are tracked", result.stderr)
        self.assertIn(".steering/state.md", result.stderr)

    def test_raw_task_steering_ci_backstop_rejects_subdirectory_task_dirs(self) -> None:
        script = PLUGIN_ROOT / "scripts" / "check-no-raw-task-steering.py"
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True, text=True)
            steering = repo / "services" / "api" / ".steering" / "20260613-task"
            steering.mkdir(parents=True)
            (steering / "state.md").write_text("Next Action=done\n", encoding="utf-8")
            subprocess.run(
                ["git", "add", "services/api/.steering/20260613-task/state.md"],
                cwd=repo,
                check=True,
            )

            result = subprocess.run(
                [sys.executable, str(script), "--root", str(repo)],
                capture_output=True,
                text=True,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("services/api/.steering/20260613-task/state.md", result.stderr)

    def test_raw_task_steering_ci_backstop_rejects_steering_root_learned_patterns(self) -> None:
        # repo-level learned-patterns は docs/learned-patterns.md（.steering/ の外）へ移設済み。
        # .steering/ 直下の root-file 例外は撤去したため、誰かが誤って
        # `.steering/learned-patterns.md` を tracked にした場合も他の raw task
        # steering と同様に reject されることを固定する。
        script = PLUGIN_ROOT / "scripts" / "check-no-raw-task-steering.py"
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True, text=True)
            steering = repo / ".steering"
            steering.mkdir()
            (steering / "learned-patterns.md").write_text("# Learned Patterns\n", encoding="utf-8")
            subprocess.run(["git", "add", ".steering/learned-patterns.md"], cwd=repo, check=True)

            result = subprocess.run(
                [sys.executable, str(script), "--root", str(repo)],
                capture_output=True,
                text=True,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(".steering/learned-patterns.md", result.stderr)

    def test_raw_task_steering_ci_backstop_allows_repo_level_learned_patterns_in_docs(self) -> None:
        script = PLUGIN_ROOT / "scripts" / "check-no-raw-task-steering.py"
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True, text=True)
            docs = repo / "docs"
            docs.mkdir()
            (docs / "learned-patterns.md").write_text("# Learned Patterns\n", encoding="utf-8")
            subprocess.run(["git", "add", "docs/learned-patterns.md"], cwd=repo, check=True)

            result = subprocess.run(
                [sys.executable, str(script), "--root", str(repo)],
                capture_output=True,
                text=True,
            )

        self.assertEqual(result.returncode, 0, result.stderr)

    def test_raw_task_steering_local_guard_rejects_staged_task_dirs(self) -> None:
        script = PLUGIN_ROOT / "scripts" / "check-no-raw-task-steering.py"
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True, text=True)
            steering = repo / ".steering" / "20260613-staged"
            steering.mkdir(parents=True)
            (steering / "state.md").write_text("Next Action=done\n", encoding="utf-8")
            subprocess.run(["git", "add", ".steering/20260613-staged/state.md"], cwd=repo, check=True)

            result = subprocess.run(
                [sys.executable, str(script), "--root", str(repo), "--staged"],
                capture_output=True,
                text=True,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("raw task steering files are staged", result.stderr)
        self.assertIn(".steering/20260613-staged/state.md", result.stderr)

    def test_raw_task_steering_local_guard_rejects_staged_steering_root_learned_patterns(self) -> None:
        # .steering/ 直下の root-file 例外は撤去済み。staged チェックでも同様に reject する。
        script = PLUGIN_ROOT / "scripts" / "check-no-raw-task-steering.py"
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True, text=True)
            steering = repo / ".steering"
            steering.mkdir()
            (steering / "learned-patterns.md").write_text("# Learned Patterns\n", encoding="utf-8")
            subprocess.run(["git", "add", ".steering/learned-patterns.md"], cwd=repo, check=True)

            result = subprocess.run(
                [sys.executable, str(script), "--root", str(repo), "--staged"],
                capture_output=True,
                text=True,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(".steering/learned-patterns.md", result.stderr)

    def test_raw_task_steering_local_guard_allows_staged_repo_level_learned_patterns_in_docs(self) -> None:
        script = PLUGIN_ROOT / "scripts" / "check-no-raw-task-steering.py"
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True, text=True)
            docs = repo / "docs"
            docs.mkdir()
            (docs / "learned-patterns.md").write_text("# Learned Patterns\n", encoding="utf-8")
            subprocess.run(["git", "add", "docs/learned-patterns.md"], cwd=repo, check=True)

            result = subprocess.run(
                [sys.executable, str(script), "--root", str(repo), "--staged"],
                capture_output=True,
                text=True,
            )

        self.assertEqual(result.returncode, 0, result.stderr)

    def test_raw_task_steering_ci_backstop_checks_only_pr_diff_when_base_is_given(self) -> None:
        script = PLUGIN_ROOT / "scripts" / "check-no-raw-task-steering.py"
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True, text=True)
            subprocess.run(["git", "config", "user.email", "gdd@example.invalid"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.name", "GDD Test"], cwd=repo, check=True)
            historical = repo / ".steering" / "20260326-historical"
            historical.mkdir(parents=True)
            (historical / "state.md").write_text("Next Action=done\n", encoding="utf-8")
            subprocess.run(["git", "add", ".steering/20260326-historical/state.md"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-m", "historical steering"], cwd=repo, check=True, capture_output=True, text=True)
            base = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=repo,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()

            result = subprocess.run(
                [sys.executable, str(script), "--root", str(repo), "--against", base],
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)

            new = repo / ".steering" / "20260613-new-task"
            new.mkdir(parents=True)
            (new / "state.md").write_text("Next Action=gdd-completion-check\n", encoding="utf-8")
            subprocess.run(["git", "add", ".steering/20260613-new-task/state.md"], cwd=repo, check=True)
            subprocess.run(
                ["git", "commit", "-m", "add new task steering"],
                cwd=repo,
                check=True,
                capture_output=True,
                text=True,
            )

            result = subprocess.run(
                [sys.executable, str(script), "--root", str(repo), "--against", base],
                capture_output=True,
                text=True,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(".steering/20260613-new-task/state.md", result.stderr)
        self.assertNotIn(".steering/20260326-historical/state.md", result.stderr)


if __name__ == "__main__":
    unittest.main()
