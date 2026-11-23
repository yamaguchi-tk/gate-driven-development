#!/usr/bin/env bash
set -euo pipefail
: "${ROOT:?}" "${PYTHON_BIN:?}"

echo "BLOCK: hooks"
"$PYTHON_BIN" - "$ROOT" <<'PY'
import json
import os
import pathlib
import re
import subprocess
import sys
import tempfile
from typing import Optional

root = pathlib.Path(sys.argv[1])
frontmatter_files = [root / "commands" / "gdd-dev.md"]
frontmatter_files.extend((root / "agents").glob("*.md"))
frontmatter_files.extend((root / "skills").glob("*/SKILL.md"))


def parse_frontmatter(path: pathlib.Path) -> dict[str, str]:
    content = path.read_text(encoding="utf-8")
    if not content.startswith("---\n"):
        raise SystemExit(f"frontmatter start missing: {path}")
    if "\n---\n" not in content[4:]:
        raise SystemExit(f"frontmatter end missing: {path}")
    _, rest = content.split("---\n", 1)
    block, _ = rest.split("\n---\n", 1)
    data: dict[str, str] = {}
    for raw_line in block.splitlines():
        line = raw_line.strip()
        if not line or ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip()
    return data


for path in frontmatter_files:
    content = path.read_text(encoding="utf-8")
    frontmatter = parse_frontmatter(path)
    required_keys = ["description", "name"]
    if path.parent.name == "agents":
        required_keys.extend(["alwaysApply", "model", "color"])
    for key in required_keys:
        if not frontmatter.get(key):
            raise SystemExit(f"{path.name} missing frontmatter key: {key}")
    if path.name == "gdd-dev.md" and frontmatter["name"] != "gdd-dev":
        raise SystemExit("gdd-dev.md name must be gdd-dev")
    if path.name == "SKILL.md" and frontmatter["name"] != path.parent.name:
        raise SystemExit(f"{path.parent.name} skill name must match directory name")
    if path.name == "SKILL.md" and "\n---\nname:" in content.split("\n---\n", 1)[1]:
        raise SystemExit(f"{path.parent.name}/SKILL.md contains duplicate frontmatter block")
    if path.parent.name == "agents":
        if frontmatter["name"] != path.stem:
            raise SystemExit(f"{path.name} agent name must match filename")
        if frontmatter["alwaysApply"] not in {"true", "false"}:
            raise SystemExit(f"{path.name} alwaysApply must be true or false")
        if frontmatter["color"] not in {"blue", "cyan", "green", "yellow", "magenta", "red"}:
            raise SystemExit(f"{path.name} has invalid color: {frontmatter['color']}")
        if "<example>" not in content:
            raise SystemExit(f"{path.name} missing <example> block in description")

expected_agent_models = {
    "gdd-planning-reviewer.md": "opus",
    "gdd-implementation-reviewer.md": "opus",
    "gdd-security-reviewer.md": "opus",
    "gdd-completion-reviewer.md": "opus",
}

for filename, expected_model in expected_agent_models.items():
    frontmatter = parse_frontmatter(root / "agents" / filename)
    if frontmatter["model"] != expected_model:
        raise SystemExit(f"{filename} expected model {expected_model} but got {frontmatter['model']}")


def isolated_hook_env(claude_code_session_id: Optional[str] = None) -> dict[str, str]:
    env = dict(os.environ)
    env["CLAUDE_PLUGIN_ROOT"] = str(root)
    env.pop("CLAUDE_CODE_SESSION_ID", None)
    if claude_code_session_id:
        env["CLAUDE_CODE_SESSION_ID"] = claude_code_session_id
    return env


def run_plan_mode_hook(
    project_dir: pathlib.Path,
    payload: dict[str, object],
    *,
    claude_code_session_id: Optional[str] = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(root / "hooks" / "scripts" / "run-block-plan-mode-hook.sh")],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        cwd=project_dir,
        env=isolated_hook_env(claude_code_session_id),
        check=False,
    )


with tempfile.TemporaryDirectory(prefix="gdd-plan-mode-hook-") as tmp:
    project_dir = pathlib.Path(tmp)
    state_dir = project_dir / ".claude"
    state_dir.mkdir()
    state_file = state_dir / "gdd-dev.local.md"
    state_file.write_text("---\nactive: true\nsession_id: test\n---\n", encoding="utf-8")

    cases = [
        (
            {"tool_name": "EnterPlanMode", "tool_input": {}},
            True,
            "EnterPlanMode should be blocked while GDD is active",
            "test",
        ),
        (
            {"tool_name": "SwitchMode", "tool_input": {"target_mode_id": "plan"}},
            True,
            "Cursor SwitchMode(plan) should be blocked while GDD is active",
            None,
        ),
        (
            {"tool_name": "SwitchMode", "tool_input": {"target_mode_id": "agent"}},
            False,
            "SwitchMode(agent) should be allowed so recovery from Plan mode is possible",
            None,
        ),
    ]
    for payload, should_block, label, claude_code_session_id in cases:
        result = run_plan_mode_hook(
            project_dir,
            payload,
            claude_code_session_id=claude_code_session_id,
        )
        blocked = '"decision":"block"' in result.stdout
        if result.returncode != 0:
            raise SystemExit(f"{label}: unexpected return code {result.returncode}: {result.stderr}")
        if blocked != should_block:
            raise SystemExit(f"{label}: blocked={blocked}, stdout={result.stdout!r}")

    state_file.write_text("---\nactive: false\n---\n", encoding="utf-8")
    inactive_result = run_plan_mode_hook(
        project_dir,
        {"tool_name": "SwitchMode", "tool_input": {"target_mode_id": "plan"}},
        claude_code_session_id="test",
    )
    if inactive_result.stdout.strip():
        raise SystemExit(
            f"inactive GDD session should not block plan mode: {inactive_result.stdout!r}"
        )


resolver = root / "scripts" / "resolve-gdd-model.py"
_resolver_tmpdir = tempfile.TemporaryDirectory(prefix="gdd-resolver-state-")
state_dir = pathlib.Path(_resolver_tmpdir.name)
state_file = state_dir / "state.md"
state_file.write_text(
    "---\nrecommended_model: grok-4.6\ndetected_phase: gdd-requirements-gating\n---\n",
    encoding="utf-8",
)
long_light_text = " ".join(["context"] * 150)
resolver_cases = [
    (
        ["--runtime", "claude_code", "--phase", "gdd-brainstorming", "--text", "requirements cleanup"],
        "formal_gate",
        "opus",
        ["phase_default:formal_gate:gdd-brainstorming"],
    ),
    (
        ["--runtime", "claude_code", "--text", "complex gdd-implementation-gating security review"],
        "general_heavy_risk",
        "opus",
        ["general_heavy_risk:final_review"],
    ),
    (
        ["--runtime", "claude_code", "--phase", "gdd-requirements-gating", "--text", "requirements review"],
        "formal_gate",
        "opus",
        ["phase_default:formal_gate:gdd-requirements-gating"],
    ),
    (
        ["--runtime", "cursor", "--text", "final review of gdd-design-gating"],
        "general_heavy_risk",
        "grok-4.6",
        ["general_heavy_risk:final_review"],
    ),
    (
        ["--runtime", "cursor", "--text", "classify routing candidates final review"],
        "general_heavy_risk",
        "grok-4.6",
        ["general_heavy_risk:final_review"],
    ),
    (
        ["--runtime", "cursor", "--phase", "gdd-design-gating", "--text", "detailed design"],
        "formal_gate",
        "grok-4.6",
        ["phase_default:formal_gate:gdd-design-gating"],
    ),
    (
        ["--runtime", "cursor", "--phase", "gdd-completion-check", "--text", "final gate"],
        "formal_gate",
        "grok-4.6",
        ["phase_default:formal_gate:gdd-completion-check"],
    ),
    (
        ["--runtime", "cursor", "--phase", "gdd-implementation-gating", "--text", "impl gate review"],
        "formal_gate",
        "grok-4.6",
        ["phase_default:formal_gate:gdd-implementation-gating"],
    ),
    (
        ["--runtime", "codex", "--phase", "gdd-design-gating", "--text", "detailed design"],
        "formal_gate",
        "gpt-5.6-sol",
        ["phase_default:formal_gate:gdd-design-gating"],
    ),
    (
        ["--runtime", "codex", "--phase", "gdd-brainstorming", "--text", "requirements cleanup"],
        "formal_gate",
        "gpt-5.6-sol",
        ["phase_default:formal_gate:gdd-brainstorming"],
    ),
    (
        ["--runtime", "codex", "--phase", "gdd-refactor-planning", "--text", "refactor planning"],
        "general_heavy",
        "gpt-5.6-sol",
        ["phase_default:general_heavy:gdd-refactor-planning"],
    ),
    (
        ["--runtime", "codex", "--phase", "gdd-task-breakdown", "--text", "break approved design into tasks"],
        "light_task",
        "gpt-5.6-terra",
        ["phase_default:light_task:gdd-task-breakdown"],
    ),
    (
        ["--runtime", "claude_code", "--text", "unclear re-entry after review with multiple files"],
        "general_heavy_risk",
        "opus",
        ["general_heavy_risk:cross_scope_with_branching"],
    ),
    (
        ["--runtime", "claude_code", "--text", "undocumented step after re-entry"],
        "general_heavy_risk",
        "opus",
        ["general_heavy_risk:undocumented_step"],
    ),
    (
        ["--runtime", "claude_code", "--text", long_light_text],
        "light_task",
        "sonnet",
        ["default:light_task"],
    ),
    (
        ["--runtime", "cursor", "--text", "classify routing candidates"],
        "leaf_task",
        "grok-4.5",
        ["leaf_task:bounded_leaf_task"],
    ),
    (
        # 独立レビュー round 3 High/blocking 指摘（PR #89）: formal gate phase は
        # LEAF_HINTS のテキスト一致だけでは leaf_task へ降格しない（fail-open修正）。
        ["--runtime", "cursor", "--phase", "gdd-requirements-gating", "--text", "classify routing candidates"],
        "formal_gate",
        "grok-4.6",
        ["phase_default:formal_gate:gdd-requirements-gating"],
    ),
    (
        ["--runtime", "cursor", "--phase", "gdd-pre-workflow-brainstorming", "--text", "idea comparison and scope narrowing"],
        "light_task",
        "grok-4.5",
        ["phase_default:light_task:gdd-pre-workflow-brainstorming"],
    ),
    (
        ["--runtime", "cursor", "--phase", "gdd-requirements-gating", "--text", "requirements summary cleanup"],
        "formal_gate",
        "grok-4.6",
        ["phase_default:formal_gate:gdd-requirements-gating"],
    ),
    (
        ["--runtime", "cursor", "--phase", "gdd-brainstorming", "--text", "requirements cleanup"],
        "formal_gate",
        "grok-4.6",
        ["phase_default:formal_gate:gdd-brainstorming"],
    ),
    (
        ["--runtime", "cursor", "--phase", "gdd-task-breakdown", "--text", "break approved design into tasks"],
        "light_task",
        "grok-4.5",
        ["phase_default:light_task:gdd-task-breakdown"],
    ),
    (
        # 独立レビュー round 3 High/blocking 指摘（PR #89）: formal gate phase は
        # LEAF_HINTS のテキスト一致だけでは leaf_task へ降格しない（fail-open修正）。
        [
            "--runtime",
            "cursor",
            "--state-file",
            str(state_file),
            "--phase",
            "gdd-requirements-gating",
            "--text",
            "classify routing candidates",
        ],
        "formal_gate",
        "grok-4.6",
        ["phase_default:formal_gate:gdd-requirements-gating"],
    ),
    (
        [
            "--runtime",
            "cursor",
            "--state-file",
            str(state_file),
            "--phase",
            "gdd-requirements-gating",
            "--text",
            "requirements summary cleanup",
        ],
        "formal_gate",
        "grok-4.6",
        ["phase_default:formal_gate:gdd-requirements-gating"],
    ),
    (
        ["--runtime", "cursor", "--text", "unclear re-entry after review with multiple files"],
        "general_heavy_risk",
        "grok-4.6",
        ["general_heavy_risk:cross_scope_with_branching"],
    ),
    (
        ["--runtime", "cursor", "--text", "undocumented step after re-entry"],
        "general_heavy_risk",
        "grok-4.6",
        ["general_heavy_risk:undocumented_step"],
    ),
    (
        ["--runtime", "cursor", "--phase", "gdd-requirements-gating", "--text", "undocumented step after requirements review"],
        "general_heavy_risk",
        "grok-4.6",
        ["general_heavy_risk:undocumented_step"],
    ),
]

def arg_value(args: list[str], flag: str) -> str:
    if flag not in args:
        return ""
    index = args.index(flag)
    if index + 1 >= len(args):
        return ""
    return args[index + 1]


def expected_effort_for_case(args: list[str], tier: str):
    runtime = arg_value(args, "--runtime")
    phase = arg_value(args, "--phase")
    text = arg_value(args, "--text")
    formal_gate_phases = {
        "gdd-brainstorming",
        "gdd-requirements-gating",
        "gdd-design-gating",
        "gdd-implementation-gating",
        "gdd-completion-check",
        "gdd-requirements-amendment",
    }
    if runtime == "claude_code":
        return {
            "leaf_task": "low",
            "light_task": "medium",
            "implementation": "medium",
            "formal_gate": "high",
            "general_heavy": "high",
            "general_heavy_risk": "high",
        }[tier]
    if runtime in {"cursor", "codex"}:
        if tier == "leaf_task":
            return "low"
        if tier == "light_task":
            return "medium"
        if tier == "implementation":
            return "n/a" if runtime == "cursor" else "low"
        if tier == "formal_gate":
            return "medium"
        if tier == "general_heavy_risk":
            return "high"
        if "undocumented step" in text or "security" in text or "final review" in text:
            return "high"
        return "low"
    return None


for args, expected_tier, expected_model, expected_reasons in resolver_cases:
    result = subprocess.run(
        [sys.executable, str(resolver), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    if result.stdout.strip() != expected_model:
        raise SystemExit(
            f"resolve-gdd-model.py {args!r} expected {expected_model} but got {result.stdout.strip()}"
        )

    json_result = subprocess.run(
        [sys.executable, str(resolver), *args, "--json"],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(json_result.stdout)
    if payload.get("tier") != expected_tier:
        raise SystemExit(
            f"resolve-gdd-model.py {args!r} expected tier {expected_tier} but got {payload.get('tier')}"
        )
    if payload.get("model") != expected_model:
        raise SystemExit(
            f"resolve-gdd-model.py {args!r} expected model {expected_model} in json but got {payload.get('model')}"
        )
    expected_effort = expected_effort_for_case(args, expected_tier)
    if payload.get("effort") != expected_effort:
        raise SystemExit(
            f"resolve-gdd-model.py {args!r} expected effort {expected_effort} in json but got {payload.get('effort')}"
        )
    reasons = payload.get("reasons", [])
    if not isinstance(reasons, list):
        raise SystemExit(f"resolver json reasons must be a list: {args!r}")
    for expected_reason in expected_reasons:
        if expected_reason not in reasons:
            raise SystemExit(
                f"resolve-gdd-model.py {args!r} expected reason {expected_reason} but got {reasons}"
            )
    signals = payload.get("signals")
    if not isinstance(signals, dict):
        raise SystemExit(f"resolver json signals must be an object: {args!r}")
    if "matches" not in signals and "explicit_complexity" not in signals:
        raise SystemExit(f"resolver json signals missing matches payload: {args!r}")

benchmark = root / "scripts" / "benchmark-model-routing.py"
benchmark_result = subprocess.run(
    [sys.executable, str(benchmark)],
    check=True,
    capture_output=True,
    text=True,
)
benchmark_payload = json.loads(benchmark_result.stdout)
if benchmark_payload.get("accuracy") != 1.0:
    raise SystemExit(f"benchmark-model-routing.py expected accuracy 1.0 but got {benchmark_payload}")


def require_tokens(path: pathlib.Path, tokens: list[str]) -> None:
    content = path.read_text(encoding="utf-8")
    for token in tokens:
        if token not in content:
            raise SystemExit(f"{path.relative_to(root)} missing token: {token}")


def forbid_tokens(path: pathlib.Path, tokens: list[str]) -> None:
    content = path.read_text(encoding="utf-8")
    for token in tokens:
        if token in content:
            raise SystemExit(f"{path.relative_to(root)} must not contain token: {token}")


forbid_tokens(
    root / "skills" / "gdd-model-routing" / "references" / "cursor.md",
    [
        "reasoning.effort=xhigh",
        "reasoning.effort=none",
        "GPT-5.4",
        "GPT-5.5",
    ],
)

for path in [
    root / "skills" / "gdd-model-routing" / "SKILL.md",
    root / "references" / "cursor.md",
    root / "references" / "codex.md",
    root / "references" / "fixed-models.md",
]:
    require_tokens(
        path,
        [
            "cheap/read-only lane",
            "state 更新なし",
            "routing 判断なし",
        ],
    )

for path in [
    root / "skills" / "gdd-model-routing" / "SKILL.md",
    root / "references" / "fixed-models.md",
]:
    require_tokens(path, ["Grok 4.6", "gpt-5.6-sol"])

require_tokens(root / "references" / "cursor.md", ["Grok 4.6", "Grok 4.5", "Composer 2.5"])
require_tokens(
    root / "references" / "codex.md",
    ["gpt-5.6-sol", "gpt-5.6-terra", "gpt-5.6-luna"],
)

# Claude Code 側は alias で書く（版は CLI が解決する）。Cursor の Opus は一覧の最新を選ぶので、版を書かずに `Opus` と書く
for path in [
    root / "skills" / "gdd-model-routing" / "SKILL.md",
    root / "references" / "fixed-models.md",
]:
    require_tokens(path, ["`opus`"])
require_tokens(root / "references" / "cursor.md", ["`Opus`"])


require_tokens(
    root / "README.md",
    [
        "/gdd-dev",
        ".claude-plugin/plugin.json",
        ".cursor-plugin/plugin.json",
        ".codex-plugin/plugin.json",
        "hooks/hooks.json",
        "PreToolUse",
        "self-contained-contract.md",
        "gdd-pre-workflow-brainstorming",
        "gdd-brainstorming",
        "gdd-requirements-gating",
        "gdd-design-gating",
        "gdd-task-breakdown",
        "gdd-using-git-worktrees",
        "gdd-test-driven-development",
        "gdd-subagent-driven-implementation",
        "gdd-implementation-gating",
        "gdd-completion-check",
        "gdd-planning-reviewer",
        "gdd-implementation-reviewer",
        "gdd-completion-reviewer",
        "gdd-requesting-code-review",
        "gdd-receiving-code-review",
        "gdd-test-failure-debug-pack",
        "gdd-security-reviewer",
        "workflow artifact",
        "gdd-dev.local.md",
        "Stop hook",
        "gdd-model-routing",
        "resolve-gdd-model.py",
        "run-with-plugin.sh",
        "Plan mode",
        "ops-blocking medium",
        "Summary Brief",
        "対象",
        "確定事項",
        "未確定事項",
        "やらないこと",
        "外部依存の確認結果",
        "lightweight `design.md` skeleton",
        "Design Policy Discussion",
        "legacy migration",
        "tech-docs-searcher",
        "references/reviewer-selection.md",
        "Implementation Reviewer Selection",
        "参照した正本",
        "停止理由",
        "次の1アクション",
        "references/onboarding.md",
        "references/faq.md",
        "CHANGELOG.md",
        "grading-summary.json",
        "references/operation-levels.md",
        "docs/references-archive/team-onboarding.md",
        "Approved Direction",
        "E2E Discovery Loop",
        "Problem Discovery",
        "Smart Session Recovery",
        "Parallel Execution",
        "Hook-enforced",
        "Implementation Guidance",
        "Direct Intent",
        "Cross-Task Learning",
        "Reviewer Calibration",
        "Reviewer Learning Loop",
        "Progress Visibility",
        "gdd-metrics",
        "CI / Issue 連携",
        "Workflow Metrics",
    ],
)

command = (root / "commands" / "gdd-dev.md").read_text(encoding="utf-8")
for token in [
    "references/self-contained-contract.md",
    "gdd-pre-workflow-brainstorming",
    "gdd-requirements-gating",
    "gdd-planning-reviewer",
    "`.cursor/plans/*.plan.md`",
    "workflow artifact",
    "Plan mode",
    "ops-blocking medium",
    "gdd-using-git-worktrees",
    "tech-docs-searcher",
    "references/reviewer-selection.md",
    "Implementation Reviewer Selection",
    "gdd-dev.local.md",
    "gdd-model-routing",
    "gdd-refactor-planning",
    "gdd-stop",
    "Stop hook",
    "参照した正本",
    "停止理由",
    "次の1アクション",
    "README.md",
    "references/onboarding.md",
    "references/faq.md",
    "Approved Direction",
    "Build Loop Orchestration",
    "実装漏れ防止 guard",
    "ディスクから re-read",
    "gdd-completion-check",
    "gdd-pr-review",
]:
    if token not in command:
        raise SystemExit(f"gdd-dev command missing token: {token}")
for token in ["plan-reviewer", "plan-reviewer-feasibility-strict"]:
    if token in command:
        raise SystemExit(f"gdd-dev command still references legacy reviewer: {token}")

design_gating = (root / "skills" / "gdd-design-gating" / "SKILL.md").read_text(encoding="utf-8")
for token in [
    "gdd-planning-reviewer",
    "gdd-security-reviewer",
    "Planning Reviewer Selection",
    "references/reviewer-selection.md",
    "Requirements Review Status=approved",
    "Human Check Status=approved",
    "Resume From=gdd-design-gating",
    "Resume From=gdd-task-breakdown",
    "Next Action=gdd-task-breakdown",
    "planning_rework_required",
    "human_recheck_required",
    "design_detail_only",
    "lightweight `design.md` skeleton",
    "tech-docs-searcher",
    "E2E Discovery Loop",
    "Approved Direction",
]:
    if token not in design_gating:
        raise SystemExit(f"gdd-design-gating missing token: {token}")
for token in ["plan-reviewer", "plan-reviewer-feasibility-strict", "`approved` または `waived`", "AI reviewer 4 人", "設計 reviewer 4 人"]:
    if token in design_gating:
        raise SystemExit(f"gdd-design-gating still references legacy reviewer/waiver behavior: {token}")

checks = {
    root / "skills" / "gdd-pre-workflow-brainstorming" / "SKILL.md": [
        "/gdd-dev",
        ".steering/.../requirements.md",
        ".cursor/plans/*.plan.md",
        "artifact",
        "state machine",
        "host の skill discovery",
        "Next Action",
        "gdd-brainstorming",
        "曖昧",
        "Summary Brief",
        "対象",
        "確定事項",
        "未確定事項",
        "やらないこと",
        "外部依存の確認結果",
    ],
    root / "skills" / "gdd-brainstorming" / "SKILL.md": [
        "references/self-contained-contract.md",
        "gdd-pre-workflow-brainstorming",
        "Requirements Review Status=pending",
        "gdd-requirements-gating",
        "gdd-using-git-worktrees",
        "Design Review Status=pending",
        "Human Check Status=pending",
        "Resume From=gdd-brainstorming",
        "Resume From=gdd-requirements-gating",
        "Resume From=human-check-waiting",
        ".cursor/plans/*.plan.md",
        "workflow artifact",
        "Plan mode",
        "Summary Brief",
        "対象",
        "確定事項",
        "未確定事項",
        "やらないこと",
        "外部依存の確認結果",
        "lightweight `design.md` skeleton",
        "Design Policy Discussion",
        "legacy migration",
        "fail-closed",
        "tech-docs-searcher",
        "Open Questions",
        "候補一覧",
        "次の1アクション",
        "条件",
        "見る入力",
        "出力または次アクション",
        "不足時の扱い",
        "unknown -> needs_input",
    ],
    root / "skills" / "gdd-using-git-worktrees" / "SKILL.md": [
        "helper",
        "branch / worktree",
        "canonical artifact",
        "legacy",
        "fail-closed",
        "復旧手順",
    ],
    root / "skills" / "gdd-requirements-gating" / "SKILL.md": [
        "gdd-planning-reviewer",
        "Requirements Review Status",
        "Planning Reviewer Selection",
        "references/reviewer-selection.md",
        "Summary Brief",
        "対象",
        "確定事項",
        "未確定事項",
        "やらないこと",
        "外部依存の確認結果",
        "Design Policy Discussion",
        "Resume From=gdd-requirements-gating",
        "Resume From=human-check-waiting",
    ],
    root / "skills" / "gdd-task-breakdown" / "SKILL.md": [
        "Resume From=gdd-brainstorming",
        "Resume From=human-check-waiting",
        "Resume From=gdd-design-gating",
        "Next Action=human-check-waiting",
        "gdd-implementation-reviewer",
        "gdd-security-reviewer",
        "Implementation Reviewer Selection",
        "Current Task",
        "Pending Tasks",
        "Completed Tasks",
        "Next Action=gdd-test-driven-development",
    ],
    root / "skills" / "gdd-implementation-gating" / "SKILL.md": [
        "Next Action=gdd-systematic-debugging",
        "Next Action=gdd-completion-check",
        "Next Action=done",
        "gdd-implementation-reviewer",
        "gdd-security-reviewer",
        "gdd-requesting-code-review",
        "Implementation Reviewer Selection",
        "references/reviewer-selection.md",
        "Current Task",
        "Pending Tasks",
        "Completed Tasks",
        "ops-blocking medium",
        "ユーザー確認待ち",
        "tasklist re-read",
        "実装漏れ防止",
        "stub detection",
    ],
    root / "skills" / "gdd-test-driven-development" / "SKILL.md": [
        "gdd-subagent-driven-implementation",
        "failing test",
        "RED",
        "gdd-brainstorming",
        "gdd-design-gating",
        "Next Action=gdd-subagent-driven-implementation",
    ],
    root / "skills" / "gdd-subagent-driven-implementation" / "SKILL.md": [
        "references/self-contained-contract.md",
        "gdd-implementation-gating",
        "gdd-brainstorming",
        "gdd-design-gating",
        "Next Action=gdd-implementation-gating",
        "fail-closed",
        "gdd-requesting-code-review",
        "明示実行",
        "active worktree",
        "ops-blocking medium",
    ],
    root / "skills" / "gdd-requesting-code-review" / "SKILL.md": [
        "gdd-implementation-reviewer",
        "gdd-security-reviewer",
        "gdd-implementation-gating",
        "external security evidence",
        "Next Action",
        "明示実行",
        "auto-trigger",
    ],
    root / "skills" / "gdd-receiving-code-review" / "SKILL.md": [
        "gdd-requesting-code-review",
        "gdd-security-reviewer",
        "gdd-systematic-debugging",
        "gdd-brainstorming",
        "gdd-design-gating",
        "Next Action",
        "gdd-implementation-gating",
    ],
    root / "skills" / "gdd-test-failure-debug-pack" / "SKILL.md": [
        "gdd-systematic-debugging",
        "gdd-test-driven-development",
        "gdd-subagent-driven-implementation",
        "Current Task",
        "Failure Command",
        "Expected",
        "Actual",
        "Root Cause Hypothesis",
        "Worklog Decision",
        "Next Action",
    ],
    root / "skills" / "gdd-systematic-debugging" / "SKILL.md": [
        "gdd-test-driven-development",
        "gdd-subagent-driven-implementation",
        "gdd-implementation-gating",
        "gdd-brainstorming",
        "gdd-design-gating",
        "gdd-receiving-code-review",
        "ops-blocking medium",
        "ops impact",
        "gdd-test-failure-debug-pack",
        "Approved Direction",
        "E2E Discovery Loop",
        "GDDのsystematic debug",
        "デバッグ中の設計判断",
    ],
    root / "skills" / "gdd-completion-check" / "SKILL.md": [
        "Next Action=done",
        "Next Action=cancelled",
        "Next Action=gdd-systematic-debugging",
        "Next Action=gdd-test-driven-development",
        "Verification",
        "evidence",
        "Reviewer Selection",
        "gdd-completion-reviewer",
        "Current Task",
        "Pending Tasks",
        "gdd-requesting-code-review",
        "security_evidence:<kind>",
        "`Next Action=gdd-completion-check` のまま",
        "外部前提不足",
        "ディスクから re-read",
        "Manual Merge Continuation",
    ],
    root / "skills" / "gdd-refactor-planning" / "SKILL.md": [
        "behavior-preserving",
        "Behavior Preservation Invariants",
        "Refactor Scope / Non-Scope",
        "Verification Focus",
        "Next Action=gdd-test-driven-development",
        "gdd-systematic-debugging",
    ],
    root / "skills" / "gdd-model-routing" / "SKILL.md": [
        "resolve-gdd-model.py",
        "run-with-plugin.sh",
        "setup-gdd-loop.sh",
        "Sonnet",
        "Opus",
        "detected_phase",
    ],
    root / "references" / "reviewer-selection.md": [
        "gdd-planning-reviewer",
        "gdd-implementation-reviewer",
        "gdd-security-reviewer",
        "gdd-completion-reviewer",
        "Planning Reviewer Selection",
        "Implementation Reviewer Selection",
        "selection_change_reason",
    ],
    root / "hooks" / "hooks.json": [
        "PreToolUse",
        "Stop",
        "Write|Edit|MultiEdit|ApplyPatch",
        "run-gdd-stop-hook.sh",
        "run-steering-write-hook.sh",
        ".steering/**",
    ],
    root / "hooks" / "scripts" / "run-gdd-stop-hook.sh": [
        "python3",
        "python",
        "GDD_PLUGIN_ROOT",
        "gdd_stop_hook.py",
    ],
    root / "hooks" / "scripts" / "gdd_stop_hook.py": [
        "gdd-dev.local.md",
        "gdd-post-merge-continuation.json",
        "Manual merge continuation",
        "gdd-stop",
        "decision",
        "systemMessage",
        "validate_done_preconditions",
        "Pending Tasks",
        "Current Task",
        "Verification",
        "実装漏れ防止",
        "hook-enforced",
        "verification_section_found",
        "verification_data_rows",
        "unexpected_content",
        "Route In Progress",
        "human-check-waiting",
    ],
    root / "hooks" / "scripts" / "run-steering-write-hook.sh": [
        "python3",
        "python",
        "CLAUDE_PLUGIN_ROOT",
        "permissionDecision",
    ],
    root / "scripts" / "setup-gdd-loop.sh": [
        "gdd-dev.local.md",
        "gdd-stop",
        "session_id",
        "iteration",
    ],
    root / "hooks" / "scripts" / "validate-steering-write.py": [
        ".steering",
        "permissionDecision",
    ],
    root / "hooks" / "scripts" / "lib" / "secret_scanning.py": [
        "Active Worktree Path",
    ],
    root / "references" / "self-contained-contract.md": [
        "External Security Evidence Contract",
        "security_evidence:<kind>",
        "gdd-pre-workflow-brainstorming",
        "gdd-requirements-gating",
        "human_recheck_required",
        "gdd-completion-reviewer",
        "same-name ambient asset",
        "Acceptance Criteria",
        ".steering/**",
        "mode switch 契約",
        "Plan mode",
        "ops-blocking medium",
        "references/reviewer-selection.md",
        "Implementation Reviewer Selection",
        "legacy root steering",
        "findings.md",
        "formal auto-trigger",
        "最新技術情報の検索",
        "参照した正本",
        "停止理由",
        "次の1アクション",
    ],
    root / "references" / "contract-overview.md": [
        "self-contained-contract.md",
        "Fail-Closed",
        "Blocked Response",
        "参照した正本",
        "停止理由",
        "次の1アクション",
        "findings.md",
    ],
    root / "references" / "state-machine.md": [
        "references/self-contained-contract.md",
        "gdd-pre-workflow-brainstorming",
        "gdd-requirements-gating",
        "active steering の決定規則",
        "build candidate",
        "planning candidate",
        "legacy root candidate",
        "Requirements Review Status",
        "Planning Reviewer Selection",
        "Human Check Status",
        "draft / stale tasklist",
        "Implementation Reviewer Selection",
        "Current Task",
        "Pending Tasks",
        "Completed Tasks",
        "human_recheck_required",
        "planning_rework_required",
        "gdd-completion-reviewer",
        "fail-closed",
        "参照した正本",
        "次の1アクション",
        "現在 phase の `Next Action` を維持する",
    ],
    root / "CHANGELOG.md": [
        "Breaking Contract Changes",
        "User Action Required",
        "Validation / Eval Impact",
        "changelog.d/<YYYYMMDD>-<slug>.md",
        "「最終ツリーで」のような時点依存の実測値は書かない",
    ],
    root / "references" / "faq.md": [
        "same-name ambient asset",
        "security_evidence:<kind>",
        "git worktree",
        "次の1アクション",
        "gdd-pre-workflow-brainstorming",
    ],
    root / "references" / "onboarding.md": [
        "gdd-pre-workflow-brainstorming",
        "/gdd-dev",
        "gdd-brainstorming",
        "human-check-waiting",
        "Resume From",
        "Next Action",
        "findings.md",
        "worklog.md",
    ],
    root / "references" / "operation-levels.md": [
        "light",
        "standard",
        "strict",
        ".gdd-config.md",
    ],
    root / "docs" / "references-archive" / "team-onboarding.md": [
        "operation-levels",
        "requirements.md",
        "design.md",
    ],
    root / "agents" / "gdd-completion-reviewer.md": [
        "gate-driven-development",
        "gdd-completion-check",
        "advisory",
    ],
    root / "agents" / "gdd-security-reviewer.md": [
        "gate-driven-development",
        "external security evidence",
        "advisory",
        "gdd-requesting-code-review",
    ],
}

for path, tokens in checks.items():
    require_tokens(path, tokens)

completion_check = (root / "skills" / "gdd-completion-check" / "SKILL.md").read_text(encoding="utf-8")
if "`Verification` の status は `pending` / `pass` / `fail` に固定する。" not in completion_check:
    raise SystemExit("gdd-completion-check must declare pending/pass/fail Verification schema")
if re.search(r"`pass`\s*(?:と|または)\s*`waived`", completion_check):
    raise SystemExit("gdd-completion-check must not allow waived in Verification")

state_machine = (root / "references" / "state-machine.md").read_text(encoding="utf-8")
if "approved/waived" in state_machine:
    raise SystemExit("state-machine must not allow waived for Design Review Status")
if "gdd-using-git-worktrees 完了" in state_machine:
    raise SystemExit("state-machine should not treat gdd-using-git-worktrees as a formal phase")
if "Next Action=gdd-using-git-worktrees" in state_machine:
    raise SystemExit("state-machine should not route gdd-task-breakdown to gdd-using-git-worktrees")

line_level_allow_phrases = ["前提にしない", "依存を持たない", "依存しない", "使わない"]
root_dependency_targets = [
    root / "README.md",
    *sorted((root / "commands").glob("*.md")),
    *sorted((root / "skills").glob("*/SKILL.md")),
    *sorted((root / "agents").glob("*.md")),
    *sorted((root / "scripts").glob("*.sh")),
]
for path in root_dependency_targets:
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if "CLAUDE.md" in line:
            raise SystemExit(f"{path.relative_to(root)}:{lineno} should not reference root CLAUDE.md")
        if "~/.claude/skills/" in line:
            raise SystemExit(f"{path.relative_to(root)}:{lineno} should not reference root ~/.claude/skills")
        if "~/.claude/agents" in line and not any(phrase in line for phrase in line_level_allow_phrases):
            raise SystemExit(f"{path.relative_to(root)}:{lineno} should not depend on root ~/.claude/agents")
        if "root 側資産は移行期間だけ残す" in line:
            raise SystemExit(f"{path.relative_to(root)}:{lineno} still contains migration-era root fallback wording")

evals_text = (root / "evals" / "evals.json").read_text(encoding="utf-8")
for token in [
    "gdd-using-git-worktrees",
    "human-check-waiting",
    "gdd-requirements-gating",
    "human_recheck_required",
    "planning_rework_required",
    "design_detail_only",
    "fail-closed",
    "gdd-pre-workflow-brainstorming",
    "gdd-requesting-code-review",
    "gdd-test-failure-debug-pack",
    "gdd-completion-reviewer",
    "security_evidence:code",
    "tech-docs-searcher",
    "gdd-stop",
    "gdd-dev.local.md",
    "references/reviewer-selection.md",
    "Implementation Reviewer Selection",
    "次の1アクション",
    "外部前提不足",
    "\"category\"",
    "\"priority\"",
    "\"required\"",
    "external-prereq",
]:
    if token not in evals_text:
        raise SystemExit(f"evals/evals.json missing coverage token: {token}")

evals_data = json.loads(evals_text)
allowed_categories = {
    "entry",
    "resume",
    "planning",
    "build",
    "completion",
    "external-prereq",
    "model",
    "review",
    "refactor",
    "status",
}
allowed_priorities = {"critical", "high", "normal", "medium"}

if not evals_data.get("evals"):
    raise SystemExit("evals/evals.json must contain evals")

if not any(ev.get("required") is True for ev in evals_data["evals"]):
    raise SystemExit("evals/evals.json must contain at least one required eval")

for ev in evals_data["evals"]:
    for key in ["category", "priority", "required"]:
        if key not in ev:
            raise SystemExit(f"eval {ev.get('id')} missing metadata field: {key}")
    if ev["category"] not in allowed_categories:
        raise SystemExit(f"eval {ev['id']} has invalid category: {ev['category']}")
    if ev["priority"] not in allowed_priorities:
        raise SystemExit(f"eval {ev['id']} has invalid priority: {ev['priority']}")
    if not isinstance(ev["required"], bool):
        raise SystemExit(f"eval {ev['id']} required must be boolean")
    expectations = ev.get("expectations")
    if not isinstance(expectations, list) or not expectations:
        raise SystemExit(f"eval {ev['id']} expectations must be a non-empty list")
    for expectation in expectations:
        if not isinstance(expectation, str):
            raise SystemExit(f"eval {ev['id']} expectation ids must be strings")
        if not re.fullmatch(r"[a-z0-9_]+", expectation):
            raise SystemExit(
                f"eval {ev['id']} expectation must use snake_case id: {expectation}"
            )

print("OK")
PY

echo "VERDICT: hooks: OK"
