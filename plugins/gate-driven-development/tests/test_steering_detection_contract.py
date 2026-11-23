import json
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

MULTIPLE_STATUS_CHECK_RE = re.compile(r'GDD_STEERING_STATUS"\s*==\s*"multiple"')


from _paths import PLUGIN_ROOT as ROOT
from _git_fixture import init_repo
DETECT_STEERING_LIB = ROOT / "hooks" / "scripts" / "lib" / "detect-steering.sh"

# Caller scripts that invoke gdd_detect_active_steering() and must not inject
# a different-slug Current Task when GDD_STEERING_STATUS=multiple (AC-6).
CALLER_SCRIPTS_WITH_EXPLICIT_MULTIPLE_BRANCH = [
    "run-pre-pr-gate-hook.sh",
    "run-session-start-hook.sh",
    "run-user-prompt-submit-hook.sh",
]
CALLER_SCRIPTS_WITH_EARLY_EXIT_ON_NON_FOUND = [
    "run-pre-compact-hook.sh",
    "run-pre-tool-use-plan-reread-hook.sh",
]


def _init_repo(path: Path) -> None:
    init_repo(path, branch="main")
    subprocess.run(
        ["git", "switch", "-c", "codex/20260708-detect-steering-fixture", "-q"],
        cwd=path,
        check=True,
    )


def _write_state(
    steering_root: Path,
    slug: str,
    resume_from: str = "implementation",
    next_action: str = "implementation",
    started_at: str = "",
) -> Path:
    task_dir = steering_root / slug
    task_dir.mkdir(parents=True)
    lines = [
        f"Resume From={resume_from}",
        f"Next Action={next_action}",
    ]
    if started_at:
        lines.append(f"Started At={started_at}")
    state_file = task_dir / "state.md"
    state_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return state_file


def _run_detect(repo: Path) -> subprocess.CompletedProcess[str]:
    # Source the lib, call gdd_detect_active_steering(), and print the
    # resulting contract variables as JSON so the Python test can assert
    # on them without re-implementing bash-side parsing.
    script = f"""
set -euo pipefail
source "{DETECT_STEERING_LIB}"
gdd_detect_active_steering >/dev/null 2>&1 || true
python3 -c '
import json
print(json.dumps({{
    "status": "'"$GDD_STEERING_STATUS"'",
    "dir": "'"$GDD_STEERING_DIR"'",
    "candidate_count": '"${{#GDD_STEERING_CANDIDATES[@]}}"',
}}))
'
"""
    env = {
        "GDD_PLUGIN_ROOT": str(ROOT),
        "PATH": "/usr/bin:/bin:/usr/local/bin",
        "HOME": str(repo),
    }
    return subprocess.run(
        ["bash", "-c", script],
        cwd=repo,
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )


class SteeringDetectionContractTests(unittest.TestCase):
    def test_multiple_candidates_with_distinct_slugs_report_multiple_unselected(self):
        """AC-4/AC-5: 2+ candidates (distinct slugs, distinct valid Started At
        timestamps) must resolve to "multiple" — no tie-break auto-selection.

        Regression note: the current implementation (pre-fix) tie-breaks on
        the latest "Started At" and returns "found" with a single winner when
        exactly one candidate has the max timestamp. This test fixture uses
        two distinct, valid timestamps so a unique max exists — this is the
        one fixture shape that actually discriminates old vs. new behavior:
        equal or absent/invalid timestamps already yield "multiple" under the
        old code (latest_count != 1), so RED would be a false RED.
        """
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _init_repo(repo)
            steering_root = repo / ".steering"
            _write_state(
                steering_root,
                "20260701-older-task",
                started_at="2026-07-01T10:00:00Z",
            )
            _write_state(
                steering_root,
                "20260702-newer-task",
                started_at="2026-07-02T10:00:00Z",
            )

            result = _run_detect(repo)
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            payload = json.loads(result.stdout.strip().splitlines()[-1])

            self.assertEqual(payload["status"], "multiple")
            self.assertEqual(payload["dir"], "")
            self.assertEqual(payload["candidate_count"], 2)

    def test_single_candidate_reports_found(self):
        """AC-5 regression: unchanged single-candidate path (177-181行) still
        returns "found"."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _init_repo(repo)
            steering_root = repo / ".steering"
            _write_state(
                steering_root,
                "20260701-only-task",
                started_at="2026-07-01T10:00:00Z",
            )

            result = _run_detect(repo)
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            payload = json.loads(result.stdout.strip().splitlines()[-1])

            self.assertEqual(payload["status"], "found")
            self.assertIn("20260701-only-task", payload["dir"])

    def test_no_candidates_reports_none(self):
        """AC-5 regression: no .steering directory at all still returns
        "none"."""
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            _init_repo(repo)

            result = _run_detect(repo)
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            payload = json.loads(result.stdout.strip().splitlines()[-1])

            self.assertEqual(payload["status"], "none")
            self.assertEqual(payload["dir"], "")


class SteeringDetectionMultipleCallerRegressionTests(unittest.TestCase):
    """AC-6: callers of gdd_detect_active_steering() must not inject a
    different-slug Current Task when GDD_STEERING_STATUS=multiple.

    Two distinct achievement paths exist among the 5 callers:
      - explicit "multiple" branch (warns / reports candidate count only):
        run-pre-pr-gate-hook.sh, run-session-start-hook.sh,
        run-user-prompt-submit-hook.sh
      - early exit whenever status != "found" (no explicit "multiple"
        handling needed): run-pre-compact-hook.sh,
        run-pre-tool-use-plan-reread-hook.sh
    This test only verifies static contract shape (source inspection), since
    reproducing full hook stdin/stdout wiring is out of scope per
    requirements.md Honest Limitations; behavior-level verification happens
    in Planned Verification Step 4 during implementation phase.
    """

    def _read(self, relative_path: str) -> str:
        return (ROOT / relative_path).read_text(encoding="utf-8")

    def test_explicit_multiple_branch_callers_check_status_multiple(self):
        for script in CALLER_SCRIPTS_WITH_EXPLICIT_MULTIPLE_BRANCH:
            with self.subTest(script=script):
                content = self._read(f"hooks/scripts/{script}")
                self.assertIn("gdd_detect_active_steering", content)
                self.assertRegex(content, MULTIPLE_STATUS_CHECK_RE)

    def test_early_exit_callers_do_not_special_case_multiple(self):
        for script in CALLER_SCRIPTS_WITH_EARLY_EXIT_ON_NON_FOUND:
            with self.subTest(script=script):
                content = self._read(f"hooks/scripts/{script}")
                self.assertIn("gdd_detect_active_steering", content)
                # These scripts rely on gdd_detect_active_steering() returning
                # non-zero (exit 1) for any non-"found" status, including
                # "multiple" — so they early-exit without an explicit
                # "multiple" string check.
                self.assertNotRegex(content, MULTIPLE_STATUS_CHECK_RE)


if __name__ == "__main__":
    unittest.main()
