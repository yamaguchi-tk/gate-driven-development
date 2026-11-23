"""Contract tests for P0/P1 GDD operational hardening.

These tests cover issues seen in recent Codex runs: telemetry under-counting,
stale resume context, and HITL readability.
"""
from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


from _paths import PLUGIN_ROOT


def read(path: str) -> str:
    return (PLUGIN_ROOT / path).read_text(encoding="utf-8")


def build_precheck_passes(schema: dict, task_size: str, statuses: dict[str, str]) -> bool:
    """`references/phase-gate-prechecks.md` Template A/B の唯一の実行可能な表現。

    独立-25 finding 2: 4 テストがそれぞれ別の簡略版（KeyError のみ／default のみ／
    LookupError なし）を局所定義しており、"唯一の実行可能な表現" という主張と
    食い違っていた。1 本に集約し、全テストで共有する。
    """
    if task_size in schema["prechecks"]["build_phase_unreachable"]:
        raise LookupError(f"Task Size {task_size!r} does not reach build phase precheck")
    build_phase = schema["prechecks"]["build_phase"]
    required = build_phase.get(task_size, schema["prechecks"]["build_phase_default"])
    return all(statuses[item["field"]] == item["status"] for item in required)


def load_telemetry_module():
    script = PLUGIN_ROOT / "scripts" / "collect-gdd-telemetry.py"
    spec = importlib.util.spec_from_file_location("collect_gdd_telemetry", script)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class P0P1OperationalHardeningContractTests(unittest.TestCase):
    def test_telemetry_normalizes_status_with_evidence_and_skips_orphaned_steering(self) -> None:
        telemetry = load_telemetry_module()

        with tempfile.TemporaryDirectory(prefix="gdd-telemetry-contract-") as tmp_raw:
            root = Path(tmp_raw)
            valid = root / ".steering" / "20260606-valid-task"
            valid.mkdir(parents=True)
            valid.joinpath("state.md").write_text(
                "\n".join(
                    [
                        "Resume From: done",
                        "Requirements Review Status: approved | evidence: req-review",
                        "Design Review Status: approved | evidence: design-review",
                        "Human Check Status: approved | evidence: human-ok",
                        "Route In Progress: none",
                    ]
                ),
                encoding="utf-8",
            )
            valid.joinpath("tasklist.md").write_text("Next Action: done\n", encoding="utf-8")
            valid.joinpath("requirements.md").write_text("Task Size: standard\n", encoding="utf-8")
            valid.joinpath("worklog.md").write_text(
                "## Workflow Incident Review\n\n"
                "| field | value |\n"
                "|---|---|\n"
                "| incident_type | hitl_readability |\n"
                "| 検出 lint / fixture | scripts/lint-hitl-decision-quality.py / tests/fixtures/e2e-replay/hitl-marker-present-but-undecidable |\n",
                encoding="utf-8",
            )

            orphan = root / ".steering" / "20260326-orphaned-copy"
            orphan.mkdir()
            orphan.joinpath("requirements.md").write_text("Task Size: unknown\n", encoding="utf-8")

            pairs = telemetry.find_steering_dirs([root])
            tasks = [telemetry.parse_task_metrics(path, wt) for path, wt in pairs]
            summary = telemetry.aggregate(tasks)

        self.assertEqual([task.steering_id for task in tasks], ["20260606-valid-task"])
        self.assertEqual(summary["total_tasks"], 1)
        self.assertEqual(summary["gate_pass_counts"]["requirements_approved"], 1)
        self.assertEqual(summary["gate_pass_counts"]["design_approved"], 1)
        self.assertEqual(summary["gate_pass_counts"]["human_check_approved"], 1)
        self.assertEqual(summary["by_kind"], {"done": 1})
        self.assertEqual(summary["workflow_guardrails"]["workflow_incident_entries"], 1)
        self.assertGreaterEqual(summary["workflow_guardrails"]["guardrail_detection_entries"], 2)
        self.assertEqual(summary["workflow_guardrails"]["by_incident_type"], {"hitl_readability": 1})

    def test_telemetry_counts_ac_trace_ledger_in_its_own_file(self) -> None:
        # AC Trace Ledger は専用ファイル ac-ledger.md に置く。そこにある Ledger も件数に数える
        telemetry = load_telemetry_module()
        with tempfile.TemporaryDirectory() as tmp:
            steering = Path(tmp) / ".steering" / "20261022-ledger"
            steering.mkdir(parents=True)
            steering.joinpath("state.md").write_text("Resume From: done\n", encoding="utf-8")
            steering.joinpath("ac-ledger.md").write_text("## AC Trace Ledger\n", encoding="utf-8")
            task = telemetry.parse_task_metrics(steering, "wt")
        self.assertEqual(task.guardrail_detection_entries, 1)

    def test_session_start_missing_current_session_id_keeps_same_worktree_resume_available(self) -> None:
        hook = PLUGIN_ROOT / "hooks" / "scripts" / "run-session-start-hook.sh"

        with tempfile.TemporaryDirectory(prefix="gdd-same-worktree-resume-") as tmp_raw:
            repo = Path(tmp_raw)
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            steering = repo / ".steering" / "20260606-human-check-pending"
            steering.mkdir(parents=True)
            steering.joinpath("state.md").write_text(
                "Resume From: human-check-waiting\n"
                "Human Check Status: pending\n"
                "Route In Progress: none\n",
                encoding="utf-8",
            )
            local = repo / ".claude"
            local.mkdir()
            local.joinpath("gdd-dev.local.md").write_text(
                "---\nactive: true\nsession_id: old-session\n---\n",
                encoding="utf-8",
            )

            env = dict(os.environ)
            env.pop("CLAUDE_CODE_SESSION_ID", None)
            for leaked in ("GDD_STEERING_DIR", "GDD_MAX_AUTO_CYCLES",
                           "GDD_WORKTREES_ROOT"):
                env.pop(leaked, None)
            # hook が開発者の実 HOME・~/.claude/.gdd-hook-state を読み・消費しないよう隔離する
            env["HOME"] = str(repo / ".home")
            env["GDD_HOOK_STATE_DIR"] = str(repo / ".hook-state")
            result = subprocess.run(
                ["bash", str(hook)],
                cwd=repo,
                env=env,
                capture_output=True,
                text=True,
                check=True,
            )

        additional = json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"]
        self.assertIn("[gdd:reboot]", additional)
        self.assertIn("20260606-human-check-pending", additional)
        self.assertIn("Session continuity: current session id unavailable", additional)
        self.assertIn("single active steering in the current git worktree", additional)
        self.assertIn("do not advance GDD", additional)
        self.assertNotIn("[gdd:paused]", additional)
        self.assertNotIn("Safe Resume Candidate Mode", additional)

    def test_session_start_mismatched_session_id_still_points_to_safe_resume_candidate_list(self) -> None:
        hook = PLUGIN_ROOT / "hooks" / "scripts" / "run-session-start-hook.sh"

        with tempfile.TemporaryDirectory(prefix="gdd-paused-resume-") as tmp_raw:
            repo = Path(tmp_raw)
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            steering = repo / ".steering" / "20260601-old-task"
            steering.mkdir(parents=True)
            steering.joinpath("state.md").write_text(
                "Resume From: gdd-test-driven-development\n"
                "Human Check Status: approved\n"
                "Route In Progress: none\n",
                encoding="utf-8",
            )
            local = repo / ".claude"
            local.mkdir()
            local.joinpath("gdd-dev.local.md").write_text(
                "---\nactive: true\nsession_id: old-session\n---\n",
                encoding="utf-8",
            )

            env = dict(os.environ)
            env["CLAUDE_CODE_SESSION_ID"] = "new-session"
            for leaked in ("GDD_STEERING_DIR", "GDD_MAX_AUTO_CYCLES",
                           "GDD_WORKTREES_ROOT"):
                env.pop(leaked, None)
            # hook が開発者の実 HOME・~/.claude/.gdd-hook-state を読み・消費しないよう隔離する
            env["HOME"] = str(repo / ".home")
            env["GDD_HOOK_STATE_DIR"] = str(repo / ".hook-state")
            result = subprocess.run(
                ["bash", str(hook)],
                cwd=repo,
                env=env,
                capture_output=True,
                text=True,
                check=True,
            )

        additional = json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"]
        self.assertIn("[gdd:paused]", additional)
        self.assertIn("Safe Resume Candidate Mode", additional)
        self.assertIn("gdd-status", additional)
        self.assertIn("/gdd-dev resume <target>", additional)
        self.assertNotIn("20260601-old-task", additional)
        self.assertNotIn("Current Task:", additional)
        self.assertNotIn("resume the active task with `/gdd-dev`", additional)

    def test_session_start_default_branch_with_nonterminal_steering_is_safe_resume_even_without_session_id(self) -> None:
        # 開発者の実 HOME・env に触れないよう、隔離済みの共通ヘルパーを使う（独立-14 F1）
        additional = self._session_start_additional_context_on_branch("main")
        self.assertIn("[gdd:paused]", additional)
        self.assertIn("Safe Resume Candidate Mode", additional)
        self.assertIn("default branch (main)", additional)
        self.assertNotIn("20260601-example-review-task", additional)

    def _session_start_additional_context_on_branch(self, branch: str) -> str:
        """`branch` の worktree（commit あり）に非終端 steering がある状態で SessionStart を起動する。
        開発者の実 HOME・env に触れないよう、HOME を tmp にして env を落とす。"""
        hook = PLUGIN_ROOT / "hooks" / "scripts" / "run-session-start-hook.sh"
        with tempfile.TemporaryDirectory(prefix="gdd-default-branch-set-") as tmp_raw:
            repo = Path(os.path.realpath(tmp_raw))
            git = ["git", "-c", "user.name=GDD Test", "-c", "user.email=gdd-test@example.invalid"]
            subprocess.run(["git", "init", "-q", "-b", branch], cwd=repo, check=True)
            subprocess.run([*git, "commit", "-q", "--allow-empty", "-m", "fixture"], cwd=repo, check=True)
            steering = repo / ".steering" / "20260601-example-review-task"
            steering.mkdir(parents=True)
            steering.joinpath("state.md").write_text(
                "Resume From: human-check-waiting\n"
                "Human Check Status: pending\n"
                "Route In Progress: none\n",
                encoding="utf-8",
            )
            local = repo / ".claude"
            local.mkdir()
            local.joinpath("gdd-dev.local.md").write_text(
                "---\nactive: true\nsession_id: old-session\n---\n", encoding="utf-8"
            )
            env = dict(os.environ)
            for leaked in ("GDD_STEERING_DIR", "GDD_MAX_AUTO_CYCLES",
                           "CLAUDE_CODE_SESSION_ID", "GDD_WORKTREES_ROOT"):
                env.pop(leaked, None)
            env["HOME"] = str(repo / ".home")
            env["GDD_HOOK_STATE_DIR"] = str(repo / ".hook-state")
            result = subprocess.run(
                ["bash", str(hook)], cwd=repo, env=env, input="", capture_output=True, text=True,
                check=True, timeout=120,
            )
        return json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"]

    def test_session_start_develop_branches_with_nonterminal_steering_are_safe_resume(self) -> None:
        # 既定ブランチの集合（gdd_is_default_branch）は master / trunk / develop /
        # development も含む。main だけを通すテストでは、集合を狭める変異が生き残る（独立-12 F2）
        for branch in ("master", "trunk", "develop", "development"):
            with self.subTest(branch=branch):
                additional = self._session_start_additional_context_on_branch(branch)
                self.assertIn("Safe Resume Candidate Mode", additional)
                self.assertIn(f"default branch ({branch})", additional)
                self.assertNotIn("20260601-example-review-task", additional)

    def test_session_start_task_branch_with_commit_is_not_treated_as_default_branch(self) -> None:
        # HEAD があって既定ブランチでもない worktree は、既定ブランチ扱いにしない。述語の連言を落として
        # HEAD があれば全ブランチを既定ブランチ扱いにする変異を落とす（独立-13 F3）
        additional = self._session_start_additional_context_on_branch("20260601-example-review-task")
        self.assertIn("[gdd:reboot]", additional)
        self.assertNotIn("default branch (", additional)

    def test_human_check_status_uses_machine_readable_state_schema(self) -> None:
        schema = json.loads(read("references/state-schema.json"))
        gate_schema = read("references/gate-status-schema.md")
        prechecks = read("references/phase-gate-prechecks.md")
        state_machine = read("references/state-machine.md")

        human_status = schema["phase_status"]["Human Check Status"]
        self.assertEqual(human_status["allowed"], ["pending", "changes_requested", "approved"])
        # 2026-10-30 に express の Auto-Confirm モードを撤去した。human check を省く経路は schema に無い
        self.assertNotIn("auto_confirm", schema)
        self.assertNotIn("auto_confirmed", human_status["allowed"])

        for text in [gate_schema, prechecks, state_machine]:
            self.assertIn("references/state-schema.json", text)
            self.assertIn("Human Check Status=approved", text)
            self.assertNotIn("Human Check Status: auto_confirmed", text)

    def test_user_prompt_hook_injects_covers_ac_and_ac_miss_health(self) -> None:
        hook = PLUGIN_ROOT / "hooks" / "scripts" / "run-user-prompt-submit-hook.sh"

        with tempfile.TemporaryDirectory(prefix="gdd-ac-miss-hook-") as tmp_raw:
            repo = Path(tmp_raw)
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            steering = repo / ".steering" / "20260607-ac-miss"
            steering.mkdir(parents=True)
            steering.joinpath("state.md").write_text(
                "Started At: 2026-06-07T00:00:00+09:00\n"
                "Resume From: gdd-test-driven-development\n"
                "Requirements Review Status=approved | evidence: req\n"
                "Design Review Status=approved | evidence: design\n"
                "Human Check Status=approved | evidence: human\n"
                "Route In Progress=none\n",
                encoding="utf-8",
            )
            steering.joinpath("requirements.md").write_text(
                "### 一言\n"
                "AC miss hook fixture\n\n"
                "## 受入条件\n"
                "- AC-1: first requirement\n"
                "- AC-2: second requirement\n",
                encoding="utf-8",
            )
            steering.joinpath("tasklist.md").write_text(
                "## Current Task\n"
                "### Task: T-1 | implement both ACs\n"
                "- Covers AC: AC-1, AC-2\n"
                "#### RED Evidence\n"
                "- test: pending\n"
                "- AC: AC-1\n\n"
                "## Pending Tasks\n"
                "- なし\n\n"
                "## Review Status\n"
                "Next Action=gdd-test-driven-development\n",
                encoding="utf-8",
            )

            (repo / ".claude").mkdir(exist_ok=True)
            (repo / ".claude" / "gdd-dev.local.md").write_text("---\nactive: true\n---\n", encoding="utf-8")
            result = subprocess.run(
                ["bash", str(hook)],
                cwd=repo,
                # 毎ターンの注入は GDD の印（active な marker）があるときだけになる。印は下で置き、
                # session id の無いランタイムとして回す（手元のセッションの id を引き継がない）
                env={k: v for k, v in os.environ.items() if k != "CLAUDE_CODE_SESSION_ID"},
                input=json.dumps({"prompt": "続けて"}),
                capture_output=True,
                text=True,
                check=True,
            )

        additional = json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"]
        self.assertIn("AC: AC-1, AC-2", additional)
        self.assertIn("AC Coverage Health", additional)
        self.assertIn("expected 2", additional)
        self.assertIn("injected 2", additional)

    def test_user_prompt_hook_detects_pr_review_feedback_and_routes_to_followup(self) -> None:
        """OT-F3 Change B1: a PR-review-feedback prompt during active GDD injects a
        hint routing to gdd-pr-review-followup."""
        hook = PLUGIN_ROOT / "hooks" / "scripts" / "run-user-prompt-submit-hook.sh"

        with tempfile.TemporaryDirectory(prefix="gdd-f3-b1-") as tmp_raw:
            repo = Path(tmp_raw)
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            steering = repo / ".steering" / "20260621-f3-followup"
            steering.mkdir(parents=True)
            steering.joinpath("state.md").write_text(
                "Started At: 2026-06-21T00:00:00+09:00\n"
                "Resume From: gdd-implementation-gating\n"
                "Requirements Review Status=approved | evidence: req\n"
                "Design Review Status=approved | evidence: design\n"
                "Human Check Status=approved | evidence: human\n"
                "Route In Progress=none\n",
                encoding="utf-8",
            )
            steering.joinpath("requirements.md").write_text(
                "### 一言\nF3 followup fixture\n\n## 受入条件\n- AC-1: x\n",
                encoding="utf-8",
            )
            steering.joinpath("tasklist.md").write_text(
                "## Current Task\n### Task: T-1 | implement\n- Covers AC: AC-1\n\n"
                "## Pending Tasks\n- なし\n\n"
                "## Review Status\nNext Action=gdd-implementation-gating\n",
                encoding="utf-8",
            )

            (repo / ".claude").mkdir(exist_ok=True)
            (repo / ".claude" / "gdd-dev.local.md").write_text("---\nactive: true\n---\n", encoding="utf-8")
            result = subprocess.run(
                ["bash", str(hook)],
                cwd=repo,
                # 毎ターンの注入は GDD の印（active な marker）があるときだけになる。印は下で置き、
                # session id の無いランタイムとして回す（手元のセッションの id を引き継がない）
                env={k: v for k, v in os.environ.items() if k != "CLAUDE_CODE_SESSION_ID"},
                input=json.dumps({
                    "prompt": "https://github.com/example-org/example-repo/pull/651 のレビュー指摘に対応して"
                }),
                capture_output=True,
                text=True,
                check=True,
            )

        additional = json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"]
        self.assertIn("gdd-pr-review-followup", additional)

    def test_user_prompt_hook_resumes_into_followup_when_pushed_waiting_re_review(self) -> None:
        """OT-F3 Change B2: a generic resume during active GDD whose state.md has
        PR Review Follow-up Status=pushed_waiting_re_review routes into followup,
        not planning."""
        hook = PLUGIN_ROOT / "hooks" / "scripts" / "run-user-prompt-submit-hook.sh"

        with tempfile.TemporaryDirectory(prefix="gdd-f3-b2-") as tmp_raw:
            repo = Path(tmp_raw)
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            steering = repo / ".steering" / "20260621-f3-b2"
            steering.mkdir(parents=True)
            steering.joinpath("state.md").write_text(
                "Started At: 2026-06-21T00:00:00+09:00\n"
                "Resume From: gdd-pr-review-followup\n"
                "Requirements Review Status=approved | evidence: req\n"
                "Design Review Status=approved | evidence: design\n"
                "Human Check Status=approved | evidence: human\n"
                "Route In Progress=none\n"
                # Real state.md uses the "colon + space" format (followup skill State Contract).
                "PR Review Follow-up Status: pushed_waiting_re_review\n",
                encoding="utf-8",
            )
            steering.joinpath("requirements.md").write_text(
                "### 一言\nF3 B2 fixture\n\n## 受入条件\n- AC-1: x\n",
                encoding="utf-8",
            )
            steering.joinpath("tasklist.md").write_text(
                "## Current Task\n### Task: T-1 | implement\n- Covers AC: AC-1\n\n"
                "## Pending Tasks\n- なし\n\n"
                "## Review Status\nNext Action=gdd-pr-review-followup\n",
                encoding="utf-8",
            )

            (repo / ".claude").mkdir(exist_ok=True)
            (repo / ".claude" / "gdd-dev.local.md").write_text("---\nactive: true\n---\n", encoding="utf-8")
            result = subprocess.run(
                ["bash", str(hook)],
                cwd=repo,
                # 毎ターンの注入は GDD の印（active な marker）があるときだけになる。印は下で置き、
                # session id の無いランタイムとして回す（手元のセッションの id を引き継がない）
                env={k: v for k, v in os.environ.items() if k != "CLAUDE_CODE_SESSION_ID"},
                input=json.dumps({"prompt": "続けて"}),
                capture_output=True,
                text=True,
                check=True,
            )

        additional = json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"]
        self.assertIn("gdd-pr-review-followup", additional)
        self.assertIn("pushed_waiting_re_review", additional)

    def test_minimal_state_machine_scenarios_cover_express_and_human_recheck(self) -> None:
        schema = json.loads(read("references/state-schema.json"))

        express_state = {
            "Requirements Review Status": "approved",
            "Design Review Status": "approved",
            "Human Check Status": "approved",
        }
        self.assertTrue(build_precheck_passes(schema, "quick (express)", express_state))

        human_recheck_state = {
            "Requirements Review Status": "approved",
            "Design Review Status": "approved",
            "Human Check Status": "pending",
        }
        self.assertFalse(build_precheck_passes(schema, "standard", human_recheck_state))

        # 独立-26 finding 1: 上の 2 assert は `build_phase_default`（3-gate 必須）と
        # 偶然一致する状態しか使っておらず、`quick (express)` 行を schema から削除しても
        # module-level helper の default フォールバックにより通ったままになる。
        # 2026-10-29 から express も requirements-gating を通るので、Human Check だけ
        # 承認の状態では express も standard も build に進めないことを確かめる。
        express_only_state = {
            "Requirements Review Status": "pending",
            "Design Review Status": "pending",
            "Human Check Status": "approved",
        }
        self.assertFalse(build_precheck_passes(schema, "quick (express)", express_only_state))
        self.assertFalse(build_precheck_passes(schema, "standard", express_only_state))

    def test_build_precheck_passes_treats_promoted_express_task_size_as_quick_standard(self) -> None:
        # 独立-21 finding 1: `prechecks.build_phase` に `quick (express → standard)`
        # （Express 昇格後の正規値。`references/phase-progression.md:155` は「昇格後は
        # 通常の quick (standard) フローに従う」と明記）のキーが無く、この lookup が
        # KeyError になっていた。`references/phase-gate-prechecks.md:11` の「文書を
        # 更新したら schema と contract test も更新する」規定に従い、Template A/B の
        # 修正と同時に schema 側にもキーを足す。
        schema = json.loads(read("references/state-schema.json"))

        promoted_state = {
            "Requirements Review Status": "approved",
            "Design Review Status": "approved",
            "Human Check Status": "approved",
        }
        self.assertTrue(build_precheck_passes(schema, "quick (express → standard)", promoted_state))
        self.assertEqual(
            schema["prechecks"]["build_phase"]["quick (express → standard)"],
            schema["prechecks"]["build_phase"]["quick (standard)"],
        )

    def test_build_precheck_falls_back_to_default_for_unenumerated_task_size(self) -> None:
        # 独立-22 finding 2: `prechecks.build_phase` の列挙に無い Task Size 表記
        # （将来の新設値・列挙漏れを含む）は、hooks/scripts/run-pre-push-gate-hook.sh 等が
        # 既に standard へフォールバックしているのに、precheck 側には default が無く
        # KeyError になっていた。`prechecks.build_phase_default` を足し、未列挙値は
        # これにフォールバックする（独立-21 finding 1 のように新しい列挙を都度足すのではなく、
        # 既存 hook の実際の挙動を precheck 側にも明示するのが対応方針）。
        schema = json.loads(read("references/state-schema.json"))

        standard_state = {
            "Requirements Review Status": "approved",
            "Design Review Status": "approved",
            "Human Check Status": "approved",
        }
        self.assertTrue(
            build_precheck_passes(schema, "standard (upgraded from quick)", standard_state)
        )
        self.assertEqual(
            schema["prechecks"]["build_phase_default"],
            schema["prechecks"]["build_phase"]["standard"],
        )

    def test_build_precheck_default_fallback_excludes_trivial(self) -> None:
        # 独立-23 finding 3: `build_phase_default` の note は「列挙に無い Task Size 値は
        # standard にフォールバックする」とだけ書いており、`trivial`（`phase-gate-prechecks.md`
        # の Template A/B が「この skill に到達しないはず（routing 誤り）」と定める値）も
        # 字面どおりに読むと standard にフォールバックしてしまい、markdown 側の定義と
        # 食い違っていた（`:11` の「文書を更新したら schema も更新する」規定に反する）。
        # `build_phase_unreachable` に `trivial` を列挙し、default フォールバックの対象外
        # であることを明示した。独立-24 finding 2: この 2 行だけでは
        # `build_phase.get(task_size, build_phase_default)`（precheck の唯一の
        # 実行可能な表現。runtime の読み手は無い）に `"trivial"` を渡すと default が
        # 返ってしまう食い違いを検出できない。独立-25 finding 2: このヘルパーを本テスト
        # 内だけに局所定義すると、自分で定義した式を自分で検査するだけになり
        # （`self.assertIn`/`assertNotIn` が通れば assertRaises は必ず通る）、他 3 テストの
        # 局所版（`build_phase_unreachable` を参照しない版）は直っていなかった。
        # module-level の `build_precheck_passes()` に集約し、4 テストで共有する。
        schema = json.loads(read("references/state-schema.json"))
        self.assertIn("trivial", schema["prechecks"]["build_phase_unreachable"])
        self.assertNotIn("trivial", schema["prechecks"]["build_phase"])

        with self.assertRaises(LookupError):
            build_precheck_passes(
                schema,
                "trivial",
                {
                    "Requirements Review Status": "approved",
                    "Design Review Status": "approved",
                    "Human Check Status": "approved",
                },
            )

    def test_ac_machine_readable_yaml_frontmatter_is_removed_and_strict_accepts_markdown_only(
        self,
    ) -> None:
        """実使用が無いこと（.steering/ と transcript を横断して実測）を確認のうえ、
        YAML frontmatter による機械可読AC機能を撤去した。schema定義（唯一の情報源だった
        docs/references-archive/ac-machine-readable-schema.md）と、requirements-template.md /
        operation-levels.md の案内、lint-ac.py の YAML 抽出・strict時YAML必須分岐を削除
        している。--strict は他の意味（WARN→ERROR昇格）を保持したまま、markdown bullet
        のみの requirements.md でも ERROR にならないことを固定する。lint-ac.py 自体は
        未移行の YAML frontmatter を検出して ERROR にする移行メッセージ
        （requirements_has_yaml_ac_frontmatter）を持つため、"YAML frontmatter" という
        文言自体は禁止せず、撤去済みの実装（抽出関数・yaml.safe_load・strict必須文言）
        の不在に絞って検査する（PR #96 レビュー指摘 MEDIUM）。"""
        operation_levels = read("references/operation-levels.md")
        requirements_template = read("references/requirements-template.md")
        lint_ac = read("scripts/lint-ac.py")

        for text, label in [
            (operation_levels, "operation-levels.md"),
            (requirements_template, "requirements-template.md"),
        ]:
            with self.subTest(label):
                self.assertNotIn("YAML frontmatter", text)
                self.assertNotIn("machine-readable AC", text)
                self.assertNotIn("docs/references-archive/ac-machine-readable-schema.md", text)

        self.assertNotIn("extract_ac_ids_from_yaml_frontmatter", lint_ac)
        self.assertNotIn("yaml.safe_load", lint_ac)
        self.assertNotIn("import yaml", lint_ac)
        self.assertNotIn("machine-readable AC required", lint_ac)
        self.assertNotIn("docs/references-archive/ac-machine-readable-schema.md", lint_ac)

        self.assertFalse(
            (PLUGIN_ROOT / "docs" / "references-archive" / "ac-machine-readable-schema.md").exists()
        )

        with tempfile.TemporaryDirectory(prefix="gdd-lint-ac-strict-") as tmp_raw:
            root = Path(tmp_raw)
            markdown_only = root / "requirements-markdown.md"
            markdown_only.write_text(
                "## 受入条件\n- AC-1: markdown only\n",
                encoding="utf-8",
            )

            strict_markdown = subprocess.run(
                ["python3", str(PLUGIN_ROOT / "scripts" / "lint-ac.py"), "--strict", str(markdown_only)],
                capture_output=True,
                text=True,
            )

        self.assertEqual(
            strict_markdown.returncode,
            0,
            msg=f"stdout={strict_markdown.stdout!r} stderr={strict_markdown.stderr!r}",
        )
        self.assertNotIn("machine-readable AC required", strict_markdown.stdout)

    def test_hitl_decision_linter_requires_post_pr_validation_followup_path(self) -> None:
        script = PLUGIN_ROOT / "scripts" / "lint-hitl-decision-quality.py"
        base_lines = [
            "## 🔍 確認",
            "### 30秒判断",
            "どこまで自走するのか？",
            "**整理した要件**: PR 後の導線を分かるようにします。",
            "**実装する方法・内容**: HITL template と lint を更新します。",
            "**検証する方法・内容**: contract test と lint smoke を実行します。",
            "**どこまで自走するのか**: PR 作成まで。merge と deploy は別承認です。",
            "**判断ポイント**: PR 境界後の導線を表示するか。",
            "**段階実装サマリー**: 単一段階: 今回の PR で完結。",
            "",
            "### OKで進む範囲",
            "このPRではここまで進め、PR 作成まで AI に任せます。",
            "",
            "### OKでも許可されないこと",
            "merge と deploy は承認しません。",
            "",
            "### 現在地",
            "| 項目 | 内容 |",
            "|---|---|",
            "| 人間が今やること | OK か変更点を返す |",
            "| OK 後に残る作業 | 実装、検証、PR 作成まで |",
            "",
            "### やらないこと",
            "本番操作はしません。",
            "",
            "### 人間に戻す条件",
            "完了条件や外部公開範囲が変わる場合。",
        ]
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "missing-pr-followup.md"
            bad.write_text("\n".join(base_lines), encoding="utf-8")
            bad_result = subprocess.run(
                [sys.executable, str(script), str(bad)],
                text=True,
                capture_output=True,
                check=False,
            )

            good = Path(tmp) / "with-pr-followup.md"
            good.write_text(
                "\n".join(
                    base_lines
                    + [
                        "",
                        "### PR検証後の次の導線",
                        "| PR検証後の状態 | 次にやること | 同じチャットで続けるか / 新しいチャットか |",
                        "|---|---|---|",
                        "| PR の検証・レビューが通った | merge は人間判断。後続実装があれば次の GDD タスクにする | 新しいチャット推奨: 別 scope になるため |",
                        "| レビュー指摘や CI 失敗が出た | PRレビュー後の修正ループで直す | 同じチャット推奨: PR URL と指摘が同じ文脈にあるため |",
                    ]
                ),
                encoding="utf-8",
            )
            good_result = subprocess.run(
                [sys.executable, str(script), str(good)],
                text=True,
                capture_output=True,
                check=False,
            )

        self.assertEqual(bad_result.returncode, 1, bad_result.stdout + bad_result.stderr)
        self.assertIn("missing PR follow-up path", bad_result.stdout)
        self.assertEqual(good_result.returncode, 0, good_result.stdout + good_result.stderr)

    def test_hitl_decision_linter_rejects_unexplained_priority_labels_and_redundant_summaries(self) -> None:
        script = PLUGIN_ROOT / "scripts" / "lint-hitl-decision-quality.py"
        base_lines = [
            "## 🔍 確認",
            "### 30秒判断",
            "どこまで自走するのか？",
            "**整理した要件**: 調査品質の底上げを進めます。",
            "**実装する方法・内容**: HITL template と lint を更新します。",
            "**検証する方法・内容**: contract test と lint smoke を実行します。",
            "**どこまで自走するのか**: 実装まで。merge と deploy は別承認です。",
            "**判断ポイント**: 優先度ラベルの表示方法です。",
            "**段階実装サマリー**: 単一段階: 今回の PR で完結。",
            "",
            "### OKで進む範囲",
            "調査品質の底上げを進めます。",
            "",
            "### OKでも許可されないこと",
            "merge と deploy は承認しません。",
            "",
            "### 現在地",
            "| 項目 | 内容 |",
            "|---|---|",
            "| 人間が今やること | OK か変更点を返す |",
            "| OK 後に残る作業 | 設計、テスト、実装 |",
            "",
            "### やらないこと",
            "本番操作はしません。",
            "",
            "### 人間に戻す条件",
            "完了条件や外部公開範囲が変わる場合。",
        ]
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "bad.md"
            bad.write_text(
                "\n".join(
                    base_lines
                    + [
                        "",
                        "### 承認サマリ",
                        "P0 から始めるか、P1/P2 も含めるかを判断してください。",
                        "",
                        "### まず確認",
                        "P0 は trajectory、P1 は knowledge、P2 は feedback sink です。",
                    ]
                ),
                encoding="utf-8",
            )
            bad_result = subprocess.run(
                [sys.executable, str(script), str(bad)],
                text=True,
                capture_output=True,
                check=False,
            )

            good = Path(tmp) / "good.md"
            good.write_text(
                "\n".join(
                    base_lines
                    + [
                        "",
                        "### まず見るところ",
                        "- まずやること（P0）: 証拠の流れを残す",
                        "- 次にやること（P1）: 知見化する",
                        "- 今回は後回し（P2）: feedback sink を作る",
                    ]
                ),
                encoding="utf-8",
            )
            good_result = subprocess.run(
                [sys.executable, str(script), str(good)],
                text=True,
                capture_output=True,
                check=False,
            )

        self.assertEqual(bad_result.returncode, 1, bad_result.stdout + bad_result.stderr)
        self.assertIn("missing priority content for P0", bad_result.stdout)
        self.assertIn("missing priority content for P1", bad_result.stdout)
        self.assertIn("missing priority content for P2", bad_result.stdout)
        self.assertIn("too many overlapping summary sections", bad_result.stdout)
        self.assertIn("unnecessary HITL section remains: ### まず確認", bad_result.stdout)
        self.assertEqual(good_result.returncode, 0, good_result.stdout + good_result.stderr)

    def test_hitl_decision_linter_requires_content_for_each_visible_priority_label(self) -> None:
        script = PLUGIN_ROOT / "scripts" / "lint-hitl-decision-quality.py"
        base_lines = [
            "## 🔍 確認",
            "### 30秒判断",
            "どこまで自走するのか？",
            "**整理した要件**: 調査品質の底上げ対象を優先度ごとに見せます。",
            "**実装する方法・内容**: HITL template と lint を更新します。",
            "**検証する方法・内容**: contract test と lint smoke を実行します。",
            "**どこまで自走するのか**: 実装まで。merge と deploy は別承認です。",
            "**判断ポイント**: P0/P1/P2 の中身が表示されているか。",
            "**段階実装サマリー**: 単一段階: 今回の PR で完結。",
            "",
            "### OKで進む範囲",
            "調査機能の底上げを進めます。",
            "",
            "### OKでも許可されないこと",
            "merge と deploy は承認しません。",
            "",
            "### 現在地",
            "| 項目 | 内容 |",
            "|---|---|",
            "| 人間が今やること | OK か変更点を返す |",
            "| OK 後に残る作業 | 設計、テスト、実装 |",
            "",
            "### やらないこと",
            "本番操作はしません。",
            "",
            "### 人間に戻す条件",
            "完了条件や外部公開範囲が変わる場合。",
        ]
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "priority-missing-content.md"
            bad.write_text(
                "\n".join(
                    base_lines
                    + [
                        "",
                        "### まず見るところ",
                        "- まずやること（P0）: trajectory trace と contradiction matrix",
                        "",
                        "### 承認ポイント",
                        "1. 初回実装は P0 の 2 件に絞ってよいですか？",
                        "2. wiki の履歴の構造化再利用、alert type 別 checklist、step-level eval、human feedback learning sink は P1/P2 として後回しでよいですか？",
                    ]
                ),
                encoding="utf-8",
            )
            bad_result = subprocess.run(
                [sys.executable, str(script), str(bad)],
                text=True,
                capture_output=True,
                check=False,
            )

            good = Path(tmp) / "priority-with-content.md"
            good.write_text(
                "\n".join(
                    base_lines
                    + [
                        "",
                        "### まず見るところ",
                        "- まずやること（P0）: trajectory trace と contradiction matrix",
                        "- 次にやること（P1）: wiki の履歴の構造化再利用、alert type 別 checklist、step-level eval",
                        "- 今回は後回し（P2）: human feedback learning sink",
                        "",
                        "### 承認ポイント",
                        "1. 初回実装は P0 の 2 件に絞ってよいですか？",
                        "2. P1/P2 は今回 scope 外として残してよいですか？",
                    ]
                ),
                encoding="utf-8",
            )
            good_result = subprocess.run(
                [sys.executable, str(script), str(good)],
                text=True,
                capture_output=True,
                check=False,
            )

        self.assertEqual(bad_result.returncode, 1, bad_result.stdout + bad_result.stderr)
        self.assertIn("missing priority content for P1", bad_result.stdout)
        self.assertIn("missing priority content for P2", bad_result.stdout)
        self.assertEqual(good_result.returncode, 0, good_result.stdout + good_result.stderr)

    # --- Task 5 追加テスト ---

    def test_pre_compact_large_state_noop(self) -> None:
        """state.md が 512 文字超でも run-pre-compact-hook.sh は exit 0 で終了する"""
        hook = PLUGIN_ROOT / "hooks/scripts/run-pre-compact-hook.sh"
        with tempfile.TemporaryDirectory(prefix="gdd-large-state-") as tmp_raw:
            steering = Path(tmp_raw)
            steering.joinpath("state.md").write_text(
                "Resume From: gdd-task-breakdown\n" + "X" * 600,
                encoding="utf-8",
            )
            env = {**os.environ, "GDD_STEERING_DIR": str(steering)}
            r = subprocess.run(["bash", str(hook)], env=env, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, f"Expected exit 0. stderr: {r.stderr}")


if __name__ == "__main__":
    unittest.main()
