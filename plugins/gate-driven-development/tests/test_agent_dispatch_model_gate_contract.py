"""Judgment 1: Agent 起動時に工程に対して model が未指定/不適切なら warn する契約。

根拠: 過去の Agent 起動を調べると、model の未指定が多く、host 既定＝main セッションの
model に落ちていた。判定材料は
5 つの閉じた入力のみ（`tool_input.subagent_type` / `tool_input.model` / `tasklist.md`
の `Gate Rounds`（本判定は不使用）/ `.claude/gdd-dev.local.md` の `active` /
`state.md` の `Resume From`）+ ユーザー承認により追加した `tasklist.md` の
`Next Action`（build phase の routing 正本。`references/state-machine.md:199-208`
— `Resume From` は planning phase 専用で build phase の戻り先を持たない）。

`description` の自由文は判定材料に使わない（PR #83 の失敗: 自由文の機械判定は
7 巡しても収束しなかった）。
"""
from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

from _paths import PLUGIN_ROOT
from _git_fixture import init_repo
LIB_DIR = PLUGIN_ROOT / "hooks" / "scripts" / "lib"
HOOK_SCRIPT = PLUGIN_ROOT / "hooks" / "scripts" / "run-agent-dispatch-model-gate-hook.sh"
#: 相談役の agent（agents/ に置き、model と effort を定義で固定する）
ADVISORS = ("gdd-opus-advisor", "gdd-opus-advisor-max", "gdd-fable-advisor")

sys.path.insert(0, str(LIB_DIR))
import agent_dispatch_gate as gate  # noqa: E402


class ResolvePhaseTests(unittest.TestCase):
    def test_planning_resume_from_wins_over_next_action(self) -> None:
        # Resume From が正本の間（3 gate 未承認）は Next Action は draft 記載値でしか
        # ないので、Resume From が読める限りそちらを優先する。
        self.assertEqual(
            gate.resolve_phase("gdd-design-gating", "gdd-task-breakdown"),
            "gdd-design-gating",
        )

    def test_falls_back_to_next_action_when_resume_from_is_not_planning(self) -> None:
        # human-check-waiting は planning phase 固定語彙に含まれない → build 側を見る
        self.assertEqual(
            gate.resolve_phase("human-check-waiting", "gdd-implementation-gating"),
            "gdd-implementation-gating",
        )

    def test_unresolvable_phase_returns_empty(self) -> None:
        self.assertEqual(gate.resolve_phase("", ""), "")
        self.assertEqual(gate.resolve_phase("done", "done"), "")

    def test_next_action_decoration_is_stripped(self) -> None:
        # 既存 hook（gdd_check_3field_gate 等）と同じ `sed 's/[[:space:]|].*//'`
        # 正規化を揃える（独立レビュー Medium-5 指摘）。
        self.assertEqual(
            gate.resolve_phase("", "gdd-implementation-gating | reason: retry"),
            "gdd-implementation-gating",
        )
        self.assertEqual(
            gate.resolve_phase("", "gdd-implementation-gating|reason:retry"),
            "gdd-implementation-gating",
        )

    def test_newly_added_build_phases_resolve(self) -> None:
        # 独立レビュー High-2 指摘: 抜けていた 4 工程を BUILD_PHASES に追加した。
        for phase in (
            "gdd-subagent-driven-implementation",
            "gdd-pr-review",
            "gdd-requesting-code-review",
            "gdd-requirements-amendment",
        ):
            with self.subTest(phase=phase):
                self.assertEqual(gate.resolve_phase("human-check-waiting", phase), phase)


class JudgeModelTests(unittest.TestCase):
    def test_formal_gate_phase_with_unspecified_model_is_flagged(self) -> None:
        finding = gate.judge("gdd-requirements-gating", "")
        self.assertIsNotNone(finding)
        self.assertEqual(finding["reason"], "unspecified")
        self.assertEqual(finding["required"], "opus")

    def test_formal_gate_phase_with_opus_is_clean(self) -> None:
        self.assertIsNone(gate.judge("gdd-requirements-gating", "opus"))

    def test_formal_gate_phase_with_sonnet_is_not_allowed(self) -> None:
        finding = gate.judge("gdd-implementation-gating", "sonnet")
        self.assertIsNotNone(finding)
        self.assertEqual(finding["reason"], "not_allowed")

    def test_disallowed_light_model_is_always_flagged_even_for_light_task_phase(self) -> None:
        # 許容集合に無い軽量モデル（実測で費用が高く検出力が低いと分かった。
        # CHANGELOG.md:94-95）は tier を問わず不適切。値そのものは fixture データ
        # であり判定ロジックはリテラル名指しをしない（許容集合に無いことだけを見る）。
        finding = gate.judge("gdd-task-breakdown", "fable")
        self.assertIsNotNone(finding)
        self.assertEqual(finding["reason"], "not_allowed")

    def test_light_task_phase_with_sonnet_is_clean(self) -> None:
        self.assertIsNone(gate.judge("gdd-task-breakdown", "sonnet"))

    def test_light_task_phase_with_opus_is_not_flagged(self) -> None:
        # opus はコスト超過だが「不適切」ではない（false positive を避ける）。
        self.assertIsNone(gate.judge("gdd-task-breakdown", "opus"))

    def test_unknown_phase_returns_none(self) -> None:
        self.assertIsNone(gate.judge("not-a-real-phase", ""))

    def test_debug_phase_requires_opus(self) -> None:
        finding = gate.judge("gdd-systematic-debugging", "sonnet")
        self.assertIsNotNone(finding)
        self.assertEqual(finding["required"], "opus")

    def test_pr_review_phase_requires_opus(self) -> None:
        # gdd-pr-review は general_heavy_risk tier（独立レビュー High-2 で
        # BUILD_PHASES に追加した工程の tier も一致することを確認する）。
        finding = gate.judge("gdd-pr-review", "sonnet")
        self.assertIsNotNone(finding)
        self.assertEqual(finding["required"], "opus")

    def test_subagent_driven_implementation_phase_allows_sonnet(self) -> None:
        self.assertIsNone(gate.judge("gdd-subagent-driven-implementation", "sonnet"))


class ModelFixedSubagentTypeTests(unittest.TestCase):
    def test_known_reviewer_agents_are_model_fixed(self) -> None:
        for name in (
            "gate-driven-development:gdd-planning-reviewer",
            "gate-driven-development:gdd-implementation-reviewer",
            "gate-driven-development:gdd-completion-reviewer",
            "gate-driven-development:gdd-security-reviewer",
            "gate-driven-development:gdd-code-simplifier",
        ):
            self.assertIn(name, gate.MODEL_FIXED_SUBAGENT_TYPES)

    def test_general_purpose_is_not_model_fixed(self) -> None:
        self.assertNotIn("general-purpose", gate.MODEL_FIXED_SUBAGENT_TYPES)


class IsExemptFromPhaseModelCheckTests(unittest.TestCase):
    def test_prefixed_reviewer_name_is_exempt_when_model_unspecified(self) -> None:
        self.assertTrue(
            gate.is_exempt_from_phase_model_check(
                "gate-driven-development:gdd-planning-reviewer", ""
            )
        )

    def test_bare_reviewer_name_is_also_exempt_when_model_unspecified(self) -> None:
        # 独立レビュー Medium-6 指摘: `Agent(subagent_type=...)` には prefix 無しの
        # bare 名でも実測で渡ってくるため、prefix 有無で判定結果が変わってはならない。
        self.assertTrue(gate.is_exempt_from_phase_model_check("gdd-planning-reviewer", ""))

    def test_fixed_reviewer_with_explicit_model_is_not_exempt(self) -> None:
        # PR #91 人間レビュー指摘（High）: Claude Code の model 解決順は起動時
        # model → agent frontmatter → 環境変数 → main。起動時に model を明示指定
        # すると frontmatter の固定 model より優先されるため、model=sonnet 等で
        # 明示的にダウングレードされた固定 reviewer は判定 1 の対象外にしてはならない。
        self.assertFalse(
            gate.is_exempt_from_phase_model_check(
                "gate-driven-development:gdd-planning-reviewer", "sonnet"
            )
        )
        self.assertFalse(gate.is_exempt_from_phase_model_check("gdd-planning-reviewer", "sonnet"))

    def test_investigation_agents_are_exempt_regardless_of_model(self) -> None:
        # phase-tier 表は GDD worker 向けであり、下請けの読み取り専用調査 agent
        # まで model を強制すると誤検知になる（独立レビュー Medium-7 指摘）。
        # investigation agent には phase-tier の model 要件自体が無関係なので、
        # model が明示指定されていても免除は変わらない。
        self.assertTrue(gate.is_exempt_from_phase_model_check("Explore", ""))
        self.assertTrue(gate.is_exempt_from_phase_model_check("Plan", ""))
        self.assertTrue(gate.is_exempt_from_phase_model_check("Explore", "sonnet"))

    def test_advisor_agents_are_exempt_with_either_name(self) -> None:
        for name in ADVISORS:
            for subagent_type in (f"gate-driven-development:{name}", name):
                with self.subTest(subagent_type=subagent_type):
                    self.assertTrue(gate.is_exempt_from_phase_model_check(subagent_type, ""))

    def test_general_purpose_is_not_exempt(self) -> None:
        self.assertFalse(gate.is_exempt_from_phase_model_check("general-purpose", ""))

    def test_empty_subagent_type_is_not_exempt(self) -> None:
        self.assertFalse(gate.is_exempt_from_phase_model_check("", ""))


class NormalizeModelFamilyTests(unittest.TestCase):
    def test_full_model_id_normalizes_to_family(self) -> None:
        # PR #91 人間レビュー指摘（Medium）: full ID（例: claude-opus-5）は alias
        # だけの許容集合とは一致せず、opus 必須 phase でも誤って警告していた。
        self.assertIsNone(gate.judge("gdd-requirements-gating", "claude-opus-5"))
        # 小数の版（claude-opus-5-5）も family に正規化される。版が上がっても gate は変えない
        self.assertIsNone(gate.judge("gdd-requirements-gating", "claude-opus-5-5"))

    def test_full_sonnet_id_is_not_allowed_for_opus_required_phase(self) -> None:
        finding = gate.judge("gdd-requirements-gating", "claude-sonnet-5")
        self.assertIsNotNone(finding)
        self.assertEqual(finding["reason"], "not_allowed")

    def test_full_sonnet_id_is_allowed_for_sonnet_required_phase(self) -> None:
        self.assertIsNone(gate.judge("gdd-task-breakdown", "claude-sonnet-5"))

    def test_unrecognized_value_is_not_normalized(self) -> None:
        # `inherit` 等の family を認識できない値は、そのまま許容集合に一致せず
        # 不適切として扱われる（独立レビュー指摘どおり、この挙動自体は変えない）。
        finding = gate.judge("gdd-requirements-gating", "inherit")
        self.assertIsNotNone(finding)
        self.assertEqual(finding["reason"], "not_allowed")


class HookScriptContractTests(unittest.TestCase):
    """Bash hook 本体の統合テスト。stdin に PreToolUse payload を渡して振る舞いを見る。"""

    def _init_repo(self, path: Path) -> None:
        init_repo(path)

    def _write_active_state(self, path: Path, *, active: bool = True, session_id: str = "test-session") -> None:
        state_dir = path / ".claude"
        state_dir.mkdir(exist_ok=True)
        (state_dir / "gdd-dev.local.md").write_text(
            f"---\nactive: {str(active).lower()}\nsession_id: {session_id}\n---\n",
            encoding="utf-8",
        )

    def _write_steering(
        self,
        path: Path,
        *,
        task: str = "20260915-sample",
        resume_from: str = "",
        next_action: str = "",
        next_action_in_state: bool = False,
        canonical: bool = True,
    ) -> None:
        # `gdd_check_3field_gate` は 3 つの承認フィールドをすべて state.md（正確には
        # GDD_GATE_FILE。存在すれば state.md 優先）から読む。tasklist.md には無い
        # （tests/test_gate_delimiter_normalization_contract.py が同じ前提）。
        design_status = "approved" if canonical else "in_review"
        state_next_action_line = f"- Next Action: {next_action}\n" if next_action_in_state else ""
        steering_dir = path / ".steering" / task
        steering_dir.mkdir(parents=True, exist_ok=True)
        (steering_dir / "state.md").write_text(
            "---\n---\n"
            "## State\n\n"
            f"- Resume From: {resume_from}\n"
            "- Requirements Review Status: approved | evidence: x | updated_by: test | updated_at: 2026-09-15T00:00:00Z\n"
            f"- Design Review Status: {design_status} | evidence: x | updated_by: test | updated_at: 2026-09-15T00:00:00Z\n"
            "- Human Check Status: approved | evidence: x | updated_by: test | updated_at: 2026-09-15T00:00:00Z\n"
            "- Route In Progress: none\n"
            "- Started At: 2026-09-15T00:00:00Z\n"
            f"{state_next_action_line}",
            encoding="utf-8",
        )
        tasklist_next_action_line = "" if next_action_in_state else f"- Next Action: {next_action}\n"
        (steering_dir / "tasklist.md").write_text(
            "## Review Status\n\n"
            f"{tasklist_next_action_line}\n"
            "## Current Task\n\n"
            "- Task: T-1\n",
            encoding="utf-8",
        )

    def _run_hook(self, cwd: Path, subagent_type: str, model: str) -> subprocess.CompletedProcess[str]:
        tool_input: dict[str, str] = {}
        if subagent_type:
            tool_input["subagent_type"] = subagent_type
        if model:
            tool_input["model"] = model
        payload = {"tool_name": "Agent", "tool_input": tool_input}
        env = {
            "CLAUDE_PLUGIN_ROOT": str(PLUGIN_ROOT),
            "CLAUDE_CODE_SESSION_ID": "test-session",
            "PATH": "/usr/bin:/bin:/usr/local/bin",
        }
        return subprocess.run(
            ["bash", str(HOOK_SCRIPT)],
            cwd=cwd,
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            env=env,
            check=False,
        )

    def _run_hook_raw(self, cwd: Path, stdin: str) -> subprocess.CompletedProcess[str]:
        env = {
            "CLAUDE_PLUGIN_ROOT": str(PLUGIN_ROOT),
            "CLAUDE_CODE_SESSION_ID": "test-session",
            "PATH": "/usr/bin:/bin:/usr/local/bin",
        }
        return subprocess.run(
            ["bash", str(HOOK_SCRIPT)],
            cwd=cwd,
            input=stdin,
            capture_output=True,
            text=True,
            env=env,
            check=False,
        )

    def test_malformed_json_payload_does_not_crash_the_guard(self) -> None:
        # 独立レビュー指摘（fail-open 側テスト 3 類型の「例外で guard 全体が落ちる」）:
        # stdin が JSON として壊れていても、warn-only の hook は非0で落ちてはならない。
        # subagent_type / model の抽出自体は失敗して空文字列になるため、Resume From が
        # 読める formal gate phase では「model 未指定」と同じ扱いで安全側に warn する
        # （抽出失敗を「未指定でない」と誤認して沈黙するより安全）。
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            self._init_repo(path)
            self._write_active_state(path)
            self._write_steering(path, resume_from="gdd-requirements-gating")
            result = self._run_hook_raw(path, "{not valid json")
            self.assertEqual(result.returncode, 0)
            self.assertIn("additionalContext", result.stdout)

    def test_non_dict_tool_input_does_not_crash_the_guard(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            self._init_repo(path)
            self._write_active_state(path)
            self._write_steering(path, resume_from="gdd-requirements-gating")
            payload = json.dumps({"tool_name": "Agent", "tool_input": "not-a-dict"})
            result = self._run_hook_raw(path, payload)
            self.assertEqual(result.returncode, 0)
            self.assertIn("additionalContext", result.stdout)

    def test_non_string_model_is_treated_as_unspecified_not_a_crash(self) -> None:
        # `model` が文字列でない（例: 数値）場合、抽出側は無視して未指定として
        # 扱われる（＝formal gate では warn される）。crash して guard が落ちる
        # ことはない。
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            self._init_repo(path)
            self._write_active_state(path)
            self._write_steering(path, resume_from="gdd-requirements-gating")
            payload = json.dumps({"tool_name": "Agent", "tool_input": {"model": 12345}})
            result = self._run_hook_raw(path, payload)
            self.assertEqual(result.returncode, 0)
            self.assertIn("additionalContext", result.stdout)

    def test_hooks_json_registers_agent_matcher(self) -> None:
        hooks = json.loads((PLUGIN_ROOT / "hooks" / "hooks.json").read_text(encoding="utf-8"))
        pre_tool = hooks["hooks"]["PreToolUse"]
        commands = [
            hook["command"]
            for entry in pre_tool
            if entry.get("matcher") == "Agent"
            for hook in entry.get("hooks", [])
        ]
        self.assertTrue(commands, "PreToolUse must register an Agent matcher")
        self.assertTrue(
            any("run-agent-dispatch-model-gate-hook.sh" in command for command in commands),
            commands,
        )

    def test_no_active_gdd_session_is_noop(self, ) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            self._init_repo(path)
            # active state が存在しない
            result = self._run_hook(path, "", "")
            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stdout.strip(), "")

    def test_active_but_no_model_in_formal_gate_phase_warns(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            self._init_repo(path)
            self._write_active_state(path)
            self._write_steering(path, resume_from="gdd-requirements-gating")
            result = self._run_hook(path, "", "")
            self.assertEqual(result.returncode, 0)
            self.assertIn("additionalContext", result.stdout)
            self.assertIn("opus", result.stdout)

    def test_active_with_correct_opus_model_is_silent(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            self._init_repo(path)
            self._write_active_state(path)
            self._write_steering(path, resume_from="gdd-requirements-gating")
            result = self._run_hook(path, "", "opus")
            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stdout.strip(), "")

    def test_build_phase_uses_next_action_when_resume_from_is_human_check_waiting(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            self._init_repo(path)
            self._write_active_state(path)
            self._write_steering(
                path,
                resume_from="human-check-waiting",
                next_action="gdd-implementation-gating",
            )
            result = self._run_hook(path, "", "sonnet")
            self.assertEqual(result.returncode, 0)
            self.assertIn("additionalContext", result.stdout)
            self.assertIn("opus", result.stdout)

    def test_disallowed_light_model_is_flagged_even_in_light_task_phase(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            self._init_repo(path)
            self._write_active_state(path)
            self._write_steering(
                path,
                resume_from="human-check-waiting",
                next_action="gdd-task-breakdown",
            )
            result = self._run_hook(path, "", "fable")
            self.assertEqual(result.returncode, 0)
            self.assertIn("additionalContext", result.stdout)
            self.assertIn("sonnet", result.stdout.lower())

    def test_model_fixed_reviewer_subagent_is_not_flagged(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            self._init_repo(path)
            self._write_active_state(path)
            self._write_steering(path, resume_from="gdd-design-gating")
            result = self._run_hook(
                path, "gate-driven-development:gdd-planning-reviewer", ""
            )
            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stdout.strip(), "")

    def test_qa_runner_without_model_is_not_flagged(self) -> None:
        # マージ後の QA は agent 定義で opus・high に固定し、起動時に model を渡さない。
        # hook は QA の起動を QA として判定しないので、ここは表の登録だけを確かめる
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            self._init_repo(path)
            self._write_active_state(path)
            # QA は main が references/post-merge-qa.md 手順 4 から起動する。ここでは判定が走る phase を置く
            self._write_steering(path, next_action="gdd-completion-check")
            for name in ("gate-driven-development:gdd-qa-runner", "gdd-qa-runner"):
                with self.subTest(name=name):
                    result = self._run_hook(path, name, "")
                    self.assertEqual(result.returncode, 0)
                    self.assertEqual(result.stdout.strip(), "")

    def test_model_fixed_reviewer_with_explicit_downgrade_is_flagged(self) -> None:
        # PR #91 人間レビュー指摘（High）: 固定 reviewer でも起動時に model を
        # 明示指定すると frontmatter の固定 model より優先されるため、
        # model=sonnet で明示的にダウングレードされた場合は警告しなければならない。
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            self._init_repo(path)
            self._write_active_state(path)
            self._write_steering(path, resume_from="gdd-design-gating")
            result = self._run_hook(
                path, "gate-driven-development:gdd-planning-reviewer", "sonnet"
            )
            self.assertEqual(result.returncode, 0)
            self.assertIn("additionalContext", result.stdout)
            self.assertIn("opus", result.stdout)

    def test_full_model_id_for_formal_gate_phase_is_silent(self) -> None:
        # PR #91 人間レビュー指摘（Medium）: full ID（claude-opus-5 等）が alias
        # だけの許容集合と一致せず誤警告していた。
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            self._init_repo(path)
            self._write_active_state(path)
            self._write_steering(path, resume_from="gdd-requirements-gating")
            result = self._run_hook(path, "", "claude-opus-5")
            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stdout.strip(), "")

    def test_large_prompt_in_tool_input_does_not_break_extraction(self) -> None:
        # PR #91 人間レビュー指摘（Medium）: payload 全体を argv に渡すと大きな
        # prompt で ARG_MAX を超えて抽出が失敗しうる。stdin 経由の parse に切り
        # 替えたので、巨大な prompt が同居していても subagent_type / model の
        # 抽出とその後の判定は壊れない。
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            self._init_repo(path)
            self._write_active_state(path)
            self._write_steering(path, resume_from="gdd-requirements-gating")
            payload = {
                "tool_name": "Agent",
                "tool_input": {
                    "subagent_type": "general-purpose",
                    "model": "sonnet",
                    "prompt": "x" * 2_000_000,
                },
            }
            result = self._run_hook_raw(path, json.dumps(payload))
            self.assertEqual(result.returncode, 0)
            self.assertIn("additionalContext", result.stdout)
            self.assertIn("opus", result.stdout)

    def test_inactive_state_is_noop(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            self._init_repo(path)
            self._write_active_state(path, active=False)
            self._write_steering(path, resume_from="gdd-requirements-gating")
            result = self._run_hook(path, "", "")
            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stdout.strip(), "")

    def test_other_session_marker_is_noop(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            self._init_repo(path)
            self._write_active_state(path, session_id="another-session")
            self._write_steering(path, resume_from="gdd-requirements-gating")
            result = self._run_hook(path, "", "")
            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stdout.strip(), "")

    def test_next_action_falls_back_to_state_md_when_tasklist_is_empty(self) -> None:
        # 独立レビューの指摘: 実運用では Next Action が tasklist.md ではなく
        # state.md 側に書かれることが多い（実測）。tasklist.md 側が空でも
        # state.md 側の値で判定できることを確認する。
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            self._init_repo(path)
            self._write_active_state(path)
            self._write_steering(
                path,
                resume_from="human-check-waiting",
                next_action="gdd-implementation-gating",
                next_action_in_state=True,
            )
            result = self._run_hook(path, "", "sonnet")
            self.assertEqual(result.returncode, 0)
            self.assertIn("additionalContext", result.stdout)
            self.assertIn("opus", result.stdout)

    def test_next_action_is_ignored_when_tasklist_not_canonical(self) -> None:
        # 独立レビュー Medium-4 指摘: 3 gate 未承認（draft）の tasklist.md に書かれた
        # Next Action は仮置きの記載値でしかなく、routing source として使うと
        # 未承認段階の worker を誤って formal gate 扱いしてしまう。
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            self._init_repo(path)
            self._write_active_state(path)
            self._write_steering(
                path,
                resume_from="human-check-waiting",
                next_action="gdd-implementation-gating",
                canonical=False,
            )
            result = self._run_hook(path, "", "")
            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stdout.strip(), "")

    def test_explore_subagent_is_not_flagged_during_formal_gate_phase(self) -> None:
        # 独立レビュー Medium-7 指摘: 読み取り専用の汎用調査 agent は phase の
        # tier 要件と無関係なので、formal gate 中でも model 未指定を warn しない。
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            self._init_repo(path)
            self._write_active_state(path)
            self._write_steering(path, resume_from="gdd-requirements-gating")
            result = self._run_hook(path, "Explore", "")
            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stdout.strip(), "")

    def test_advisor_subagents_are_not_flagged_during_formal_gate_phase(self) -> None:
        # 相談役（references/autonomy.md 判断の手順）は工程の worker ではなく、model と effort を
        # agent 定義で固定する。fable の相談役も、工程の tier の警告を出さない
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            self._init_repo(path)
            self._write_active_state(path)
            self._write_steering(path, resume_from="gdd-requirements-gating")
            for name in ADVISORS:
                for subagent_type in (f"gate-driven-development:{name}", name):
                    with self.subTest(subagent_type=subagent_type):
                        result = self._run_hook(path, subagent_type, "")
                        self.assertEqual(result.returncode, 0)
                        self.assertEqual(result.stdout.strip(), "")

    def test_requirements_precheck_is_not_flagged_during_requirements_gating(self) -> None:
        # 提出前の照合（references/requirements-gating-steps.md Step 4a）は read-only で工程の worker
        # ではなく、Sonnet に固定する。opus 必須の requirements-gating から起動しても警告しない
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            self._init_repo(path)
            self._write_active_state(path)
            self._write_steering(path, resume_from="gdd-requirements-gating")
            for subagent_type in ("gate-driven-development:gdd-requirements-precheck", "gdd-requirements-precheck"):
                with self.subTest(subagent_type=subagent_type):
                    result = self._run_hook(path, subagent_type, "")
                    self.assertEqual(result.returncode, 0)
                    self.assertEqual(result.stdout.strip(), "")

    def test_general_purpose_with_fable_is_still_flagged_during_formal_gate_phase(self) -> None:
        # Fable の相談役は名前で免除し、Opus の相談役は model を省略したときだけ免除する。model の値では免除しない
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            self._init_repo(path)
            self._write_active_state(path)
            self._write_steering(path, resume_from="gdd-requirements-gating")
            result = self._run_hook(path, "general-purpose", "fable")
            self.assertEqual(result.returncode, 0)
            self.assertIn("additionalContext", result.stdout)
            self.assertIn('model=\\"fable\\"', result.stdout)

    def test_unresolvable_phase_is_noop(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            self._init_repo(path)
            self._write_active_state(path)
            # Resume From も Next Action も判定対象外の値
            self._write_steering(path, resume_from="human-check-waiting", next_action="")
            result = self._run_hook(path, "", "")
            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stdout.strip(), "")


if __name__ == "__main__":
    unittest.main()
