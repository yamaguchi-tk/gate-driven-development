"""Contract tests for GDD autonomous model worker orchestration."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from _paths import PLUGIN_ROOT
WORKER = PLUGIN_ROOT / "scripts" / "run-gdd-worker.py"


class AutonomousModelWorkerContractTests(unittest.TestCase):
    def run_worker(self, *args: str) -> dict[str, object]:
        result = subprocess.run(
            [sys.executable, str(WORKER), *args],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_codex_worker_dry_run_builds_phase_model_effort_command(self) -> None:
        payload = self.run_worker(
            "--runtime",
            "codex",
            "--phase",
            "gdd-design-gating",
            "--text",
            "formal gate detailed design",
            "--dry-run",
        )

        self.assertEqual(payload["requested_model"], "gpt-5.6-sol")
        self.assertEqual(payload["requested_effort"], "medium")
        self.assertEqual(payload["applied_model"], "unknown")
        self.assertEqual(payload["applied_effort"], "unknown")
        self.assertEqual(payload["application_status"], "planned")
        self.assertIn("--model", payload["command"])
        self.assertIn("gpt-5.6-sol", payload["command"])
        self.assertIn("model_reasoning_effort=medium", payload["command"])

    def test_codex_formal_gate_with_risk_signal_escalates_to_high_effort(self) -> None:
        payload = self.run_worker(
            "--runtime",
            "codex",
            "--phase",
            "gdd-design-gating",
            "--text",
            "security-sensitive design review across many files before final review",
            "--dry-run",
        )

        self.assertEqual(payload["requested_model"], "gpt-5.6-sol")
        self.assertEqual(payload["requested_effort"], "high")
        self.assertIn("model_reasoning_effort=high", payload["command"])

    def test_worker_success_without_metadata_is_unverified_not_applied(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            runner = tmp_path / "fake-runner.py"
            runner.write_text(
                "#!/usr/bin/env python3\nimport sys\nprint('artifact generated without metadata')\n",
                encoding="utf-8",
            )
            runner.chmod(0o755)
            output_dir = tmp_path / "worker_runs"

            payload = self.run_worker(
                "--runtime",
                "codex",
                "--phase",
                "gdd-task-breakdown",
                "--text",
                "task breakdown",
                "--runner",
                str(runner),
                "--output-dir",
                str(output_dir),
            )

            self.assertEqual(payload["worker_exit_status"], "succeeded")
            self.assertEqual(payload["application_status"], "unverified")
            self.assertEqual(payload["applied_model"], "unknown")
            self.assertEqual(payload["integration_status"], "pending_main_review")
            result_files = list(output_dir.glob("*/result.json"))
            self.assertEqual(len(result_files), 1)
            saved = json.loads(result_files[0].read_text(encoding="utf-8"))
            self.assertEqual(saved["application_status"], "unverified")

    def test_formal_gate_runner_failure_does_not_silent_fallback_to_light_model(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            runner = tmp_path / "fail-runner.py"
            runner.write_text(
                "#!/usr/bin/env python3\nimport sys\nprint('model unavailable', file=sys.stderr)\nsys.exit(7)\n",
                encoding="utf-8",
            )
            runner.chmod(0o755)
            result = subprocess.run(
                [
                    sys.executable,
                    str(WORKER),
                    "--runtime",
                    "codex",
                    "--phase",
                    "gdd-requirements-gating",
                    "--text",
                    "formal requirements gate",
                    "--runner",
                    str(runner),
                ],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 7)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["requested_model"], "gpt-5.6-sol")
            self.assertEqual(payload["application_status"], "unavailable")
            self.assertEqual(payload["applied_model"], "unknown")
            self.assertEqual(payload["fallback_action"], "needs_human_acceptance_or_heavy_retry")

    def test_formal_gate_fallback_applies_to_case_and_whitespace_variant_phase(self) -> None:
        # 独立レビュー round 5 High/blocking 指摘（F-1）: `fallback_action()` は
        # `--phase` をそのまま `FORMAL_GATE_PHASES` と完全一致で比較するため、
        # `hooks/scripts/gdd_stop_hook.py::_detect_phase()` と `resolve-gdd-model.py`
        # `classify_tier()` に足した大文字小文字・空白ゆれの正規化（round 4 F2）が
        # ここには及ばず、表記ゆれの phase では formal gate の
        # 「unverified なら軽量 model へ黙って落とさない」契約
        # （`references/subagent-dispatch.md` の formal gate unverified 契約）を
        # 迂回できていた。同じ `--phase` 入力を読む別実装（`fallback_action`）にも
        # 同じ正規化を対称に適用してこの fail-open を塞ぐ。
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            runner = tmp_path / "fail-runner.py"
            runner.write_text(
                "#!/usr/bin/env python3\nimport sys\nprint('model unavailable', file=sys.stderr)\nsys.exit(7)\n",
                encoding="utf-8",
            )
            runner.chmod(0o755)
            for phase in ("GDD-Requirements-Gating", " gdd-requirements-gating "):
                with self.subTest(phase=phase):
                    result = subprocess.run(
                        [
                            sys.executable,
                            str(WORKER),
                            "--runtime",
                            "codex",
                            "--phase",
                            phase,
                            "--text",
                            "formal requirements gate",
                            "--runner",
                            str(runner),
                        ],
                        text=True,
                        capture_output=True,
                        check=False,
                    )
                    self.assertEqual(result.returncode, 7)
                    payload = json.loads(result.stdout)
                    self.assertEqual(payload["application_status"], "unavailable")
                    self.assertEqual(
                        payload["fallback_action"], "needs_human_acceptance_or_heavy_retry"
                    )
                    # 独立レビュー round 6 指摘（A-1）: fallback_action だけでなく、
                    # payload 記録（"phase"）と resolve_model() 経由の
                    # requested_model にも正規化が対称に効いていることを検査する。
                    self.assertEqual(payload["phase"], "gdd-requirements-gating")
                    self.assertEqual(payload["requested_model"], "gpt-5.6-sol")

if __name__ == "__main__":
    unittest.main()
