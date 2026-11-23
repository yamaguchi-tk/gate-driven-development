"""Contract tests for dedicated GDD scenario evaluation."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from _validate_plugin_reader import read_validate_plugin_and_checks


from _paths import PLUGIN_ROOT


def read(path: str) -> str:
    return (PLUGIN_ROOT / path).read_text(encoding="utf-8")


class GddScenarioEvalContractTests(unittest.TestCase):
    def test_scenario_eval_assets_define_p0_p1_gdd_dedicated_evaluation(self) -> None:
        reference = read("references/gdd-scenario-evals.md")
        fixture = json.loads(read("evals/gdd-scenario-fixtures.json"))
        script = read("scripts/run-gdd-scenario-evals.py")
        validate = read_validate_plugin_and_checks()

        for token in [
            "Scenario Corpus",
            "Scenario Layers",
            "P2: Release Gate",
            "GDD Flow Goal",
            "GDD 専用の回帰評価基盤",
            "deterministic replay を正本",
            "UX Regression Matrix",
            "期待チェックリスト",
            "Artifact Collector",
            "Deterministic Scorer",
            "LLM Judge Boundary",
            "GDD Scenario Review Support",
            "decisionability",
            "human_ux_rubric",
            "safety_rubric",
            "failure_modes",
            "category coverage",
            "Subagent Prompt Generation",
            "Iteration Report",
            "Empirical-style Presentation",
            "Minimal Next Fix",
            "Empirical-Style Operating Loop",
            "Final Evaluation",
            "Improvement Result",
            "Hold-out Regression Gate",
            "Release Gate Enforcement",
            "require-release-pass",
            "overall_status",
            "Actionable Failures",
            "GDD Scenario Review Signals",
            "baseline-summary",
            "GDDとして守りたいこと",
            "起きてはいけないこと",
            "現行契約の参照先",
            "新しい subagent",
            "自己再読で代替しない",
            "gdd scenario review skipped: dispatch unavailable",
            "同じ subagent の再利用は禁止",
            "Final Evaluation status=pass",
            "シナリオ別結果と不明瞭点を主役",
            "収束判定",
        ]:
            self.assertIn(token, reference)

        self.assertIn("gdd-scenario-fixtures.json", validate)
        self.assertIn("run-gdd-scenario-evals.py", validate)
        self.assertIn("--require-release-pass", validate)
        self.assertIn("emit-subagent-prompts", script)
        self.assertIn("require_release_pass", script)
        self.assertIn("release_decision", script)
        self.assertIn("Hold-out Regression Gate", script)
        self.assertIn("overall_status", script)
        self.assertIn("release_decision", script)
        self.assertIn("Final Evaluation", script)
        self.assertIn("Improvement Result", script)
        self.assertIn("| シナリオ | 成功/失敗 | 精度 | checks | unclear | retries |", script)
        self.assertIn("scenario_unclear_summary", script)
        self.assertIn("scenario_check_summary", script)
        self.assertIn("convergence_summary", script)
        self.assertIn("status_mark", script)
        self.assertIn("top_actionable_summaries", script)
        self.assertIn("Actionable Failures 詳細を参照", script)
        self.assertIn("Actionable Failures", script)
        self.assertIn("--review-dir", script)
        self.assertIn("--baseline-summary", script)
        self.assertIn("UX観点", script)
        self.assertIn("安全観点", script)
        self.assertIn("想定失敗", script)
        self.assertIn("## 評価モード", script)
        self.assertIn("pass: critical checklist", script)
        self.assertIn("warning: critical checklist", script)
        self.assertIn("## 期待される成果物の型", script)
        self.assertIn("DEFAULT_CONTRACT_REFS_BY_CATEGORY", script)
        self.assertIn("## GDD共通の形式要件", script)
        self.assertIn("## 契約スナップショット", script)
        self.assertIn("## 期待される結果", script)
        self.assertIn("fresh review evidence", script)
        self.assertIn("worktree path slug / state Task ID / branch slug / Active Branch", script)
        self.assertIn("Task ID / Active Worktree Path / Active Branch", script)
        self.assertGreaterEqual(len(fixture["scenarios"]), 10)
        scenario_ids = {scenario["scenario_id"] for scenario in fixture["scenarios"]}
        for scenario_id in [
            "codex_goal_continuation_superpowers_reboot_conflict",
            "fable_lightweight_hitl_primary_surface",
            "fable_reference_integrity_local_references",
            "fable_done_guard_fail_closed_on_validation_error",
            "fable_state_minimal_routing_appendix",
            "fable_hook_error_visibility_status",
            "fable_superpowers_concise_routing_injection",
            "fable_quick_standard_design_gate_optional",
            "fable_context_budget_runtime_read_limits",
            "fable_readme_time_estimates_are_conditioned",
            "fable_user_entrypoints_are_three",
            "fable_resume_ux_hides_three_layer_internals",
            "fable_express_and_hitl_templates_are_split",
            "fable_stop_hook_structured_marker_fail_closed",
            "fable_state_source_of_truth_map_prevents_state_audit_dump",
            "post_pr_followup_requires_adr_not_raw_steering",
            "terraform_ci_policy_architecture_options_conftest",
            "manual_merge_report_verifies_deploy_and_cleanup",
            "stale_stop_hook_missing_transcript_suppressed",
            "active_gdd_pr_followup_stays_gdd_primary",
            "external_review_loop_self_drives_via_schedulewakeup",
        ]:
            self.assertIn(scenario_id, scenario_ids)
        categories = {scenario["category"] for scenario in fixture["scenarios"]}
        for category in [
            "hitl",
            "route",
            "next-plan",
            "worktree",
            "pr",
            "verification",
            "debugging",
            "model-routing",
            "staged-implementation",
            "pre-workflow",
            "design",
            "build",
            "state",
        ]:
            self.assertIn(category, categories)
        flow_goal_scenarios = [
            scenario for scenario in fixture["scenarios"]
            if scenario.get("origin") == "gdd_flow_goal"
        ]
        self.assertGreaterEqual(len(flow_goal_scenarios), 7)
        expected_flow_stages = {
            "gdd-pre-workflow-brainstorming",
            "gdd-brainstorming formal entry",
            "human-check-waiting",
            "post-human-check progression",
            "gdd-design-gating",
            "build phase",
            "active session follow-up",
            "completion / post-merge follow-up",
        }
        self.assertTrue(expected_flow_stages.issubset({scenario["flow_stage"] for scenario in flow_goal_scenarios}))
        for scenario in fixture["scenarios"]:
            self.assertIn("scenario_id", scenario)
            self.assertIn("source_session", scenario)
            self.assertIn("human_ux_rubric", scenario)
            self.assertIn("safety_rubric", scenario)
            self.assertIn("failure_modes", scenario)
            self.assertTrue(scenario["human_ux_rubric"])
            self.assertTrue(scenario["safety_rubric"])
            self.assertTrue(scenario["failure_modes"])
            self.assertIn("checklist", scenario)
            self.assertTrue(any(item.get("critical") for item in scenario["checklist"]))
            if scenario.get("origin") == "gdd_flow_goal":
                for field in ["goal", "flow_stage", "current_contract_refs", "must_preserve", "must_not_happen"]:
                    self.assertIn(field, scenario)
                    self.assertTrue(scenario[field])
            for item in scenario["checklist"]:
                patterns = " ".join(item.get("patterns", []))
                self.assertFalse(
                    item.get("kind") == "not_contains" and "superpowers:" in patterns,
                    f"{scenario['scenario_id']} / {item['id']} should assert GDD primary positively instead of failing on forbidden skill names",
                )

        codex_goal = next(
            scenario for scenario in fixture["scenarios"]
            if scenario["scenario_id"] == "codex_goal_continuation_superpowers_reboot_conflict"
        )
        self.assertEqual(codex_goal["source_session"], "synthetic:session-09")
        for token in [
            "Codex goal continuation",
            "superpowers",
            "reboot task",
            "example-prod-eval",
            "workflow owner ではない",
            "Task Binding",
        ]:
            self.assertIn(token, json.dumps(codex_goal, ensure_ascii=False))

        terraform_policy = next(
            scenario for scenario in fixture["scenarios"]
            if scenario["scenario_id"] == "terraform_ci_policy_architecture_options_conftest"
        )
        self.assertEqual(terraform_policy["source_session"], "synthetic:session-10")
        for token in [
            "Architecture Option Matrix",
            "Terraform plan JSON",
            "OPA/Rego + Conftest",
            "Python 独自チェック",
            "terraform validate / tflint / Checkov",
            "DRY / KISS / YAGNI",
            "人間に確認",
        ]:
            self.assertIn(token, json.dumps(terraform_policy, ensure_ascii=False))

    def test_require_release_pass_fails_warning_and_fail_results(self) -> None:
        fixture = {
            "version": 1,
            "scenarios": [
                {
                    "scenario_id": "release_gate_warning",
                    "title": "warning should block release pass",
                    "source_session": "synthetic:release-gate",
                    "category": "hitl",
                    "artifacts": ["assistant"],
                    "human_ux_rubric": ["decisionability"],
                    "safety_rubric": ["no_unsafe_release"],
                    "failure_modes": ["non-critical warning is released"],
                    "checklist": [
                        {
                            "id": "RG-1",
                            "critical": True,
                            "description": "critical passes",
                            "target": "assistant",
                            "kind": "contains_all",
                            "patterns": ["critical-pass"],
                        },
                        {
                            "id": "RG-2",
                            "critical": False,
                            "description": "non-critical warning remains",
                            "target": "assistant",
                            "kind": "contains_all",
                            "patterns": ["non-critical-pass"],
                        },
                    ],
                }
            ],
        }
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            fixture_path = tmp_path / "fixture.json"
            input_dir = tmp_path / "artifacts"
            scenario_dir = input_dir / "release_gate_warning"
            fixture_path.write_text(json.dumps(fixture), encoding="utf-8")
            scenario_dir.mkdir(parents=True)
            (scenario_dir / "assistant.md").write_text("critical-pass\n", encoding="utf-8")

            critical_only = subprocess.run(
                [
                    sys.executable,
                    str(PLUGIN_ROOT / "scripts" / "run-gdd-scenario-evals.py"),
                    "--fixture",
                    str(fixture_path),
                    "--input-dir",
                    str(input_dir),
                    "--require-critical-pass",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(critical_only.returncode, 0)

            release_gate = subprocess.run(
                [
                    sys.executable,
                    str(PLUGIN_ROOT / "scripts" / "run-gdd-scenario-evals.py"),
                    "--fixture",
                    str(fixture_path),
                    "--input-dir",
                    str(input_dir),
                    "--require-release-pass",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(release_gate.returncode, 1)
            self.assertIn('"status": "warning"', release_gate.stdout)

    def test_scenario_eval_runner_scores_artifacts_and_generates_subagent_prompts(self) -> None:
        script = PLUGIN_ROOT / "scripts" / "run-gdd-scenario-evals.py"
        fixture = {
            "version": 1,
            "scenarios": [
                {
                    "scenario_id": "hitl_option_verification",
                    "title": "HITL option and verification plan",
                    "source_session": "synthetic:session-03",
                    "category": "hitl",
                    "prompt": "GDD planning HITLを出す",
                    "artifacts": ["assistant"],
                    "human_ux_rubric": ["decisionability", "non_engineer_readability"],
                    "safety_rubric": ["scope_boundary_is_explicit"],
                    "failure_modes": ["Option label is undefined", "Verification location is missing"],
                    "checklist": [
                        {
                            "id": "C1",
                            "critical": True,
                            "description": "Option B is defined",
                            "target": "assistant",
                            "kind": "contains_all",
                            "patterns": ["選択肢の説明", "Option B", "何をする案か"],
                        },
                        {
                            "id": "C2",
                            "critical": True,
                            "description": "Verification plan is actionable",
                            "target": "assistant",
                            "kind": "contains_all",
                            "patterns": ["検証計画", "どこで確認するか", "どう確認するか", "OK条件", "失敗時の扱い"],
                        },
                    ],
                }
            ],
        }

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            fixture_path = tmp_path / "fixtures.json"
            input_dir = tmp_path / "artifacts"
            review_dir = tmp_path / "reviews"
            prompt_dir = tmp_path / "prompts"
            report_path = tmp_path / "report.md"
            scenario_dir = input_dir / "hitl_option_verification"
            scenario_dir.mkdir(parents=True)
            review_scenario_dir = review_dir / "hitl_option_verification"
            review_scenario_dir.mkdir(parents=True)
            fixture_path.write_text(json.dumps(fixture), encoding="utf-8")
            (scenario_dir / "assistant.md").write_text(
                "\n".join(
                    [
                        "### 選択肢の説明",
                        "| Option B | 何をする案か |",
                        "### 検証計画",
                        "| どこで確認するか | どう確認するか | OK条件 | 失敗時の扱い |",
                    ]
                ),
                encoding="utf-8",
            )
            (review_scenario_dir / "review.md").write_text(
                "\n".join(
                    [
                        "- 成果物: HITL と検証計画を確認",
                        "- 要件達成: C1 ○ / C2 ○",
                        "- 不明瞭点: なし",
                        "- 裁量補完: なし",
                        "- 再試行: 0",
                    ]
                ),
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(script),
                    "--fixture",
                    str(fixture_path),
                    "--input-dir",
                    str(input_dir),
                    "--review-dir",
                    str(review_dir),
                    "--emit-subagent-prompts",
                    str(prompt_dir),
                    "--iteration-report",
                    str(report_path),
                    "--holdout",
                    "--require-critical-pass",
                ],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            summary = json.loads(result.stdout)
            self.assertEqual(summary["overall_status"], "pass")
            self.assertEqual(summary["release_decision"]["status"], "pass")
            self.assertEqual(summary["status_counts"]["pass"], 1)
            self.assertEqual(summary["category_coverage"]["hitl"], 1)
            self.assertEqual(summary["scenarios"][0]["status"], "pass")
            self.assertFalse(summary["scenarios"][0]["review_signals"]["has_unclear_points"])
            self.assertIn("Hold-out Regression Gate", report_path.read_text(encoding="utf-8"))
            self.assertIn("Final Evaluation", report_path.read_text(encoding="utf-8"))
            self.assertIn("### 実行結果（シナリオ別）", report_path.read_text(encoding="utf-8"))
            self.assertIn("| シナリオ | 成功/失敗 | 精度 | checks | unclear | retries |", report_path.read_text(encoding="utf-8"))
            self.assertIn("### 詳細", report_path.read_text(encoding="utf-8"))
            self.assertNotIn("### 結論", report_path.read_text(encoding="utf-8"))
            self.assertIn("（収束判定:", report_path.read_text(encoding="utf-8"))
            self.assertIn("Improvement Result", report_path.read_text(encoding="utf-8"))
            self.assertIn("Actionable Failures", report_path.read_text(encoding="utf-8"))
            self.assertIn("GDD Scenario Review Signals", report_path.read_text(encoding="utf-8"))
            prompt_text = (prompt_dir / "hitl_option_verification.md").read_text(encoding="utf-8")
            self.assertIn("あなたは GDD scenario fixture を白紙で読む実行者です", prompt_text)
            self.assertIn("要件チェックリスト", prompt_text)
            self.assertIn("評価モード", prompt_text)
            self.assertIn("期待される成果物の型", prompt_text)
            self.assertIn("契約スナップショット", prompt_text)
            self.assertIn("期待される結果", prompt_text)
            self.assertIn("GDD共通の形式要件", prompt_text)
            self.assertNotIn("## 現行契約の参照先\n- なし", prompt_text)
            self.assertIn("親セッションの会話履歴", prompt_text)
            self.assertIn("GDDとして守りたいこと", prompt_text)
            self.assertIn("起きてはいけないこと", prompt_text)
            self.assertIn("現行契約の参照先", prompt_text)
            self.assertIn("UX観点", prompt_text)
            self.assertIn("安全観点", prompt_text)
            self.assertIn("想定失敗", prompt_text)
            self.assertIn("不明瞭点", prompt_text)

    def test_scenario_eval_runner_reports_actionable_failures_and_baseline_compare(self) -> None:
        script = PLUGIN_ROOT / "scripts" / "run-gdd-scenario-evals.py"
        fixture = {
            "version": 1,
            "scenarios": [
                {
                    "scenario_id": "route_regression",
                    "title": "Route regression",
                    "source_session": "synthetic:route",
                    "category": "route",
                    "prompt": "GDD route should stay primary.",
                    "artifacts": ["assistant"],
                    "human_ux_rubric": ["next_human_action"],
                    "safety_rubric": ["gdd_primary"],
                    "failure_modes": ["superpowers が owner になる"],
                    "checklist": [
                        {
                            "id": "R1",
                            "critical": True,
                            "description": "GDD primary is explicit",
                            "target": "assistant",
                            "kind": "contains_all",
                            "patterns": ["GDD primary", "superpowers", "渡さない"],
                        }
                    ],
                }
            ],
        }
        baseline = {
            "scenarios": [
                {
                    "scenario_id": "route_regression",
                    "checks": [{"id": "R1", "status": "fail"}],
                }
            ]
        }

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            fixture_path = tmp_path / "fixtures.json"
            baseline_path = tmp_path / "baseline.json"
            input_dir = tmp_path / "artifacts"
            review_dir = tmp_path / "reviews"
            report_path = tmp_path / "report.md"
            scenario_dir = input_dir / "route_regression"
            review_scenario_dir = review_dir / "route_regression"
            scenario_dir.mkdir(parents=True)
            review_scenario_dir.mkdir(parents=True)
            fixture_path.write_text(json.dumps(fixture), encoding="utf-8")
            baseline_path.write_text(json.dumps(baseline), encoding="utf-8")
            (scenario_dir / "assistant.md").write_text(
                "GDD primary\nsuperpowers\n渡さない\n",
                encoding="utf-8",
            )
            (review_scenario_dir / "review.md").write_text(
                "- 不明瞭点: route owner の説明が短い\n- 裁量補完: GDD primary と解釈\n- 再試行: 1\n",
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(script),
                    "--fixture",
                    str(fixture_path),
                    "--input-dir",
                    str(input_dir),
                    "--review-dir",
                    str(review_dir),
                    "--baseline-summary",
                    str(baseline_path),
                    "--iteration-report",
                    str(report_path),
                    "--holdout",
                    "--require-critical-pass",
                ],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            summary = json.loads(result.stdout)
            self.assertEqual(summary["overall_status"], "warning")
            self.assertEqual(summary["release_decision"]["status"], "warning")
            self.assertEqual(summary["comparison"]["mode"], "baseline-compare")
            self.assertEqual(summary["comparison"]["improvement"], ["route_regression / R1"])
            self.assertTrue(summary["scenarios"][0]["review_signals"]["has_unclear_points"])
            self.assertEqual(summary["review_signal_counts"]["has_unclear_points"], 1)
            report = report_path.read_text(encoding="utf-8")
            self.assertIn("baseline-compare", report)
            self.assertIn("route_regression / R1", report)
            self.assertIn("- 判定: warning", report)
            self.assertIn("- 次アクション: iter 継続", report)
            self.assertIn("Final Evaluation", report)
            self.assertIn("Improvement Result", report)

    def test_fable_scenarios_score_positive_and_negative_artifacts(self) -> None:
        script = PLUGIN_ROOT / "scripts" / "run-gdd-scenario-evals.py"
        fixture_path = PLUGIN_ROOT / "evals" / "gdd-scenario-fixtures.json"

        def run_eval(input_dir: Path) -> dict[str, object]:
            result = subprocess.run(
                [
                    sys.executable,
                    str(script),
                    "--fixture",
                    str(fixture_path),
                    "--input-dir",
                    str(input_dir),
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            return json.loads(result.stdout)

        def scenario(summary: dict[str, object], scenario_id: str) -> dict[str, object]:
            for item in summary["scenarios"]:  # type: ignore[index]
                if item["scenario_id"] == scenario_id:
                    return item
            self.fail(f"scenario not found: {scenario_id}")

        with tempfile.TemporaryDirectory() as tmp:
            input_dir = Path(tmp) / "positive"
            for scenario_id in [
                "fable_lightweight_hitl_primary_surface",
                "fable_reference_integrity_local_references",
                "fable_done_guard_fail_closed_on_validation_error",
                "fable_state_minimal_routing_appendix",
                "fable_hook_error_visibility_status",
                "fable_superpowers_concise_routing_injection",
                "fable_quick_standard_design_gate_optional",
                "fable_context_budget_runtime_read_limits",
                "fable_readme_time_estimates_are_conditioned",
                "fable_user_entrypoints_are_three",
                "fable_resume_ux_hides_three_layer_internals",
                "fable_express_and_hitl_templates_are_split",
                "fable_stop_hook_structured_marker_fail_closed",
            ]:
                (input_dir / scenario_id).mkdir(parents=True)

            (input_dir / "fable_lightweight_hitl_primary_surface" / "assistant.md").write_text(
                "\n".join(
                    [
                        "なぜやるか: 既存の手動運用で漏れが発生しているため、自動チェックに置き換えます。",
                        "整理した要件: ユーザー入力を要件と完了条件に変換します。",
                        "実装する方法・内容: 既存実装を再利用し、主要ファイルだけを変更します。",
                        "変更予定ファイル: skills/gdd-example/SKILL.md を変更します。",
                        "検証する方法・内容: 検証計画でどこで確認するか、どう確認するか、OK条件、失敗時の扱いを示します。",
                        "どこまで自走するのか: PR 作成まで。",
                        "判断ポイント: 人間に決めてほしいこと、まだ確認できないこと、人間に戻す条件を示します。",
                        "段階実装: この PR の範囲と後続 Stage を示します。",
                        "OKでも許可されないこと: merge / deploy / apply。",
                        "詳細は requirements.md に残します。詳細は artifact を参照。",
                    ]
                ),
                encoding="utf-8",
            )
            (input_dir / "fable_reference_integrity_local_references" / "assistant.md").write_text(
                "root references と skill-local references を分けます。./references は skill-local references です。\n"
                "references/pr-lifecycle.md は存在しないため、実在する gdd-pr-review-followup へ参照を寄せます。\n",
                encoding="utf-8",
            )
            (input_dir / "fable_reference_integrity_local_references" / "commands.md").write_text(
                "validate-plugin checks root references and ./references separately.\n",
                encoding="utf-8",
            )
            (input_dir / "fable_done_guard_fail_closed_on_validation_error" / "assistant.md").write_text(
                '{"decision":"block","reason":"done guard の検証中にエラー。tasklist.md を修復し、検証行を確認して再出力してください。"}\n',
                encoding="utf-8",
            )
            (input_dir / "fable_state_minimal_routing_appendix" / "state.md").write_text(
                "Tier 1\nResume From: gdd-completion-check\nHuman Check Status: approved\n"
                "Route In Progress: none\nNext Action: done\n",
                encoding="utf-8",
            )
            (input_dir / "fable_state_minimal_routing_appendix" / "assistant.md").write_text(
                "Audit / Context の詳細は worklog.md と appendix に移し、routing source にはしない。\n",
                encoding="utf-8",
            )
            (input_dir / "fable_hook_error_visibility_status" / "assistant.md").write_text(
                "### Hook Errors\nhook error log を表示します。次の1アクション: 状態を変更せず確認。\n"
                "これは表示だけです。state を変更しないし、done / blocked に進めない。\n",
                encoding="utf-8",
            )
            (input_dir / "fable_superpowers_concise_routing_injection" / "assistant.md").write_text(
                "Routing reason: GDD active marker detected. GDD primary / superpowers advisory only. gdd-status で確認。\n",
                encoding="utf-8",
            )
            (input_dir / "fable_quick_standard_design_gate_optional" / "assistant.md").write_text(
                "設計 gate: light。なぜ light でよいか: 既存類似実装に沿う小変更です。\n"
                "codebase survey pack: 関連ファイル、類似実装、テスト、ドキュメントを確認。複雑性シグナルなし。\n",
                encoding="utf-8",
            )
            (input_dir / "fable_context_budget_runtime_read_limits" / "assistant.md").write_text(
                "Skill Runtime Read Limits: 実行時 reference は原則 3 ファイルまで。\n"
                "state.md / tasklist.md / requirements.md を優先し、長い reference はなぜ必要かを 1 行で説明してから読む。\n",
                encoding="utf-8",
            )
            (input_dir / "fable_readme_time_estimates_are_conditioned" / "assistant.md").write_text(
                "所要時間は検証・レビュー・差し戻し回数で大きく変わる。build phase だけなら短いが、"
                "standard は 45 分〜数時間で、必要なら段階 PR 化を推奨する。\n",
                encoding="utf-8",
            )
            (input_dir / "fable_user_entrypoints_are_three" / "assistant.md").write_text(
                "ユーザーが覚える入口は 3 つ: /gdd-dev, gdd-status, gdd-pr-review。"
                "その他の skill は state machine から自動で呼ばれるので覚える必要はない。\n",
                encoding="utf-8",
            )
            (input_dir / "fable_resume_ux_hides_three_layer_internals" / "assistant.md").write_text(
                "まず gdd-status で候補と次の1アクションを確認し、/gdd-dev resume <候補> で明示する。"
                "段階実装は /gdd-resume <continuation-id> で latest default branch から新しい worktree を作る。\n",
                encoding="utf-8",
            )
            (input_dir / "fable_express_and_hitl_templates_are_split" / "assistant.md").write_text(
                "quick (express) は requirements-template-express.md から始め、full template は複雑化したら昇格して使います。"
                "HITL は human-check-template-compact.md を一次表示にし、判断ポイントと OKでも許可されないことを先頭に出します。\n",
                encoding="utf-8",
            )
            (input_dir / "fable_stop_hook_structured_marker_fail_closed" / "assistant.md").write_text(
                "Primary Stop Signal は <gdd-stop reason=\"...\"> です。自然文だけで、停止の reason を推定しない。\n"
                "Markerless State Fallback は human-check surface がある時だけで、単に「承認をお願いします」だけでは許可しない。\n"
                "Fail-Closed Error Handling では state を削除せず block し、.gdd/hook-errors.log に記録する。\n",
                encoding="utf-8",
            )

            positive = run_eval(input_dir)
            for scenario_id in [
                "fable_lightweight_hitl_primary_surface",
                "fable_reference_integrity_local_references",
                "fable_done_guard_fail_closed_on_validation_error",
                "fable_state_minimal_routing_appendix",
                "fable_hook_error_visibility_status",
                "fable_superpowers_concise_routing_injection",
                "fable_quick_standard_design_gate_optional",
                "fable_context_budget_runtime_read_limits",
                "fable_readme_time_estimates_are_conditioned",
                "fable_user_entrypoints_are_three",
                "fable_resume_ux_hides_three_layer_internals",
                "fable_express_and_hitl_templates_are_split",
                "fable_stop_hook_structured_marker_fail_closed",
            ]:
                self.assertEqual(scenario(positive, scenario_id)["status"], "pass")

        with tempfile.TemporaryDirectory() as tmp:
            input_dir = Path(tmp) / "negative"
            scenario_dir = input_dir / "fable_lightweight_hitl_primary_surface"
            scenario_dir.mkdir(parents=True)
            (scenario_dir / "assistant.md").write_text(
                "\n".join(
                    [
                        "整理した要件: ユーザー入力を要件に変換します。",
                        "実装する方法・内容: 既存実装を再利用します。",
                        "どこまで自走するのか: PR 作成まで。",
                        "判断ポイント: 人間に決めてほしいことを示します。",
                        "段階実装: この PR の範囲を示します。",
                    ]
                ),
                encoding="utf-8",
            )

            negative = run_eval(input_dir)
            hitl = scenario(negative, "fable_lightweight_hitl_primary_surface")
            self.assertEqual(hitl["status"], "fail")
            failed = {check["id"]: check for check in hitl["checks"]}  # type: ignore[index]
            self.assertIn("検証する方法・内容", failed["FABLE-HITL-1"]["missing"])
            self.assertIn("OKでも許可されないこと", failed["FABLE-HITL-2"]["missing"])


if __name__ == "__main__":
    unittest.main()
