#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


FLAGS = re.IGNORECASE | re.DOTALL


DEFAULT_CONTRACT_REFS_BY_CATEGORY = {
    "hitl": ["references/human-check-template.md", "references/requirements-template.md"],
    "route": ["references/phase-progression.md", "references/skill-responsibility-matrix.md"],
    "next-plan": ["skills/gdd-next-plan/SKILL.md", "references/phase-progression.md"],
    "worktree": ["references/contract-overview.md", "references/common-guardrails.md"],
    "pr": ["skills/gdd-pr-review-followup/SKILL.md", "references/phase-progression.md"],
    "verification": ["references/verification-before-completion.md", "references/phase-progression.md"],
    "debugging": ["skills/root-cause-investigation/SKILL.md", "references/phase-progression.md"],
    "model-routing": ["skills/gdd-model-routing/SKILL.md", "references/human-check-template.md"],
    "staged-implementation": ["references/human-check-template.md", "references/phase-progression.md"],
    "pre-workflow": ["skills/gdd-pre-workflow-brainstorming/SKILL.md"],
    "design": ["skills/gdd-design-gating/SKILL.md", "references/requirements-template.md"],
    "build": ["references/phase-progression.md", "references/verification-before-completion.md"],
    "state": ["references/state-machine.md", "references/common-guardrails.md"],
}


@dataclass(frozen=True)
class CheckResult:
    item_id: str
    critical: bool
    description: str
    status: str
    target: str
    missing: list[str]


@dataclass(frozen=True)
class ReviewSignals:
    unclear_points: str
    discretionary_fill: str
    retries: str


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_artifact(input_dir: Path | None, scenario_id: str, target: str) -> str:
    if input_dir is None:
        return ""
    scenario_dir = input_dir / scenario_id
    candidates = [
        scenario_dir / f"{target}.md",
        scenario_dir / f"{target}.txt",
        input_dir / f"{scenario_id}.{target}.md",
        input_dir / f"{scenario_id}.{target}.txt",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate.read_text(encoding="utf-8")
    return ""


def extract_report_field(text: str, label: str) -> str:
    if not text:
        return ""
    pattern = rf"^\s*[-*]\s*{re.escape(label)}\s*:\s*(.*)$"
    match = re.search(pattern, text, re.MULTILINE)
    if match:
        return match.group(1).strip()
    heading = re.search(rf"^#+\s*{re.escape(label)}\s*$", text, re.MULTILINE)
    if not heading:
        return ""
    tail = text[heading.end() :]
    next_heading = re.search(r"^#+\s+", tail, re.MULTILINE)
    body = tail[: next_heading.start()] if next_heading else tail
    return body.strip()


def parse_review_signals(text: str) -> ReviewSignals:
    return ReviewSignals(
        unclear_points=extract_report_field(text, "不明瞭点"),
        discretionary_fill=extract_report_field(text, "裁量補完"),
        retries=extract_report_field(text, "再試行"),
    )


def pattern_found(text: str, pattern: str, regex: bool) -> bool:
    if regex:
        return re.search(pattern, text, FLAGS) is not None
    return pattern.lower() in text.lower()


def evaluate_item(item: dict[str, Any], artifacts: dict[str, str]) -> CheckResult:
    target = item.get("target", "assistant")
    text = artifacts.get(target, "")
    kind = item.get("kind", "contains_all")
    patterns = list(item.get("patterns", []))
    regex = kind == "regex"

    if kind in {"contains_all", "regex"}:
        missing = [p for p in patterns if not pattern_found(text, p, regex)]
        status = "pass" if not missing else "fail"
    elif kind == "contains_any":
        found = [p for p in patterns if pattern_found(text, p, False)]
        missing = [] if found else patterns
        status = "pass" if found else "fail"
    elif kind == "not_contains":
        present = [p for p in patterns if pattern_found(text, p, False)]
        missing = present
        status = "pass" if not present else "fail"
    else:
        missing = [f"unsupported kind: {kind}"]
        status = "fail"

    return CheckResult(
        item_id=item["id"],
        critical=bool(item.get("critical", False)),
        description=item.get("description", ""),
        status=status,
        target=target,
        missing=missing,
    )


def evaluate_scenario(
    scenario: dict[str, Any],
    input_dir: Path | None,
    review_dir: Path | None = None,
) -> dict[str, Any]:
    scenario_id = scenario["scenario_id"]
    targets = set(scenario.get("artifacts", ["assistant"]))
    targets.update(item.get("target", "assistant") for item in scenario.get("checklist", []))
    artifacts = {target: read_artifact(input_dir, scenario_id, target) for target in targets}
    review_signals = parse_review_signals(read_artifact(review_dir, scenario_id, "review"))

    results = [evaluate_item(item, artifacts) for item in scenario.get("checklist", [])]
    critical_failed = [r for r in results if r.critical and r.status != "pass"]
    failed = [r for r in results if r.status != "pass"]
    if critical_failed:
        status = "fail"
    elif failed:
        status = "warning"
    else:
        status = "pass"

    total = len(results) or 1
    passed = sum(1 for r in results if r.status == "pass")
    return {
        "scenario_id": scenario_id,
        "title": scenario.get("title", scenario_id),
        "source_session": scenario.get("source_session", ""),
        "category": scenario.get("category", ""),
        "status": status,
        "accuracy": round(passed / total * 100, 2),
        "critical_failed": [r.item_id for r in critical_failed],
        "failed_checks": [r.item_id for r in failed],
        "judge_required": bool(scenario.get("judge_required", False)),
        "human_ux_rubric": list(scenario.get("human_ux_rubric", [])),
        "safety_rubric": list(scenario.get("safety_rubric", [])),
        "failure_modes": list(scenario.get("failure_modes", [])),
        "review_signals": {
            "unclear_points": review_signals.unclear_points,
            "discretionary_fill": review_signals.discretionary_fill,
            "retries": review_signals.retries,
            "has_unclear_points": bool(review_signals.unclear_points and review_signals.unclear_points != "なし"),
        },
        "next_actions": [
            {
                "check_id": r.item_id,
                "critical": r.critical,
                "description": r.description,
                "target": r.target,
                "missing": r.missing,
                "action": "GDD contract / artifact output を修正して missing pattern を満たす",
            }
            for r in failed
        ],
        "checks": [
            {
                "id": r.item_id,
                "critical": r.critical,
                "description": r.description,
                "status": r.status,
                "target": r.target,
                "missing": r.missing,
            }
            for r in results
        ],
    }


def overall_status(results: list[dict[str, Any]]) -> str:
    if any(r["status"] == "fail" for r in results):
        return "fail"
    if any(r["review_signals"]["has_unclear_points"] for r in results):
        return "warning"
    if any(r["status"] == "warning" for r in results):
        return "warning"
    return "pass"


def status_counts(results: list[dict[str, Any]]) -> dict[str, int]:
    counts = {"pass": 0, "warning": 0, "fail": 0}
    for result in results:
        counts[result["status"]] = counts.get(result["status"], 0) + 1
    return counts


def category_coverage(results: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for result in results:
        category = result.get("category") or "uncategorized"
        counts[category] = counts.get(category, 0) + 1
    return dict(sorted(counts.items()))


def flatten_check_status(summary: dict[str, Any]) -> dict[tuple[str, str], str]:
    statuses: dict[tuple[str, str], str] = {}
    for scenario in summary.get("scenarios", []):
        scenario_id = scenario.get("scenario_id", "")
        for check in scenario.get("checks", []):
            statuses[(scenario_id, check.get("id", ""))] = check.get("status", "")
    return statuses


def compare_with_baseline(current: dict[str, Any], baseline: dict[str, Any] | None) -> dict[str, Any]:
    if not baseline:
        return {
            "mode": "deterministic-only",
            "degrade": [],
            "improvement": [],
            "not_measured": True,
        }
    current_status = flatten_check_status(current)
    baseline_status = flatten_check_status(baseline)
    degrade: list[str] = []
    improvement: list[str] = []
    for key, before in baseline_status.items():
        after = current_status.get(key)
        if before == "pass" and after and after != "pass":
            degrade.append(f"{key[0]} / {key[1]}")
        if before != "pass" and after == "pass":
            improvement.append(f"{key[0]} / {key[1]}")
    return {
        "mode": "baseline-compare",
        "degrade": degrade,
        "improvement": improvement,
        "not_measured": False,
    }


def release_decision(summary: dict[str, Any]) -> dict[str, Any]:
    failed = [s for s in summary["scenarios"] if s["status"] == "fail"]
    warnings = [s for s in summary["scenarios"] if s["status"] == "warning"]
    review_unclear = [
        s for s in summary["scenarios"] if s["review_signals"]["has_unclear_points"]
    ]
    degrade = summary["comparison"]["degrade"]

    if failed or degrade:
        return {
            "status": "fail",
            "reason": "critical failure or baseline degrade remains",
            "next_action": "iter 継続",
        }
    if warnings or review_unclear:
        return {
            "status": "warning",
            "reason": "critical checks pass but review signals or non-critical failures remain",
            "next_action": "iter 継続",
        }
    return {
        "status": "pass",
        "reason": "all scenarios pass with no review ambiguity or degrade",
        "next_action": "release 推奨",
    }


def status_mark(status: str) -> str:
    return {"pass": "○", "warning": "△", "fail": "×"}.get(status, status)


def short_text(text: str, limit: int = 64) -> str:
    normalized = " ".join(text.split())
    if not normalized:
        return "なし"
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 1] + "…"


def readable_next_action(scenario: dict[str, Any]) -> str:
    actions = scenario.get("next_actions", [])
    if actions:
        check_ids = ", ".join(action["check_id"] for action in actions[:3])
        suffix = "" if len(actions) <= 3 else " ほか"
        return f"不足checkを修正: {check_ids}{suffix}"
    if scenario["review_signals"]["has_unclear_points"]:
        return "不明瞭点を解消"
    return "追加修正なし"


def scenario_result_mark(status: str) -> str:
    if status == "pass":
        return "○"
    if status == "warning":
        return "△"
    return "×"


def scenario_check_summary(scenario: dict[str, Any]) -> str:
    checks = scenario.get("checks", [])
    total = len(checks)
    passed = sum(1 for check in checks if check.get("status") == "pass")
    if total == 0:
        return "0/0"
    return f"{passed}/{total}"


def scenario_unclear_summary(scenario: dict[str, Any]) -> str:
    if scenario.get("critical_failed"):
        return "[critical] " + ", ".join(scenario["critical_failed"]) + " が ×"
    if scenario["review_signals"]["has_unclear_points"]:
        return short_text(scenario["review_signals"]["unclear_points"], 80)
    if scenario.get("failed_checks"):
        return ", ".join(scenario["failed_checks"]) + " が未達"
    return "新出なし"


def convergence_summary(summary: dict[str, Any]) -> str:
    decision = summary["release_decision"]
    if decision["status"] == "pass":
        return "1回クリア / 2回連続 pass で収束"
    return f"未クリア / status={decision['status']} のため iter 継続"


def top_actionable_summaries(summary: dict[str, Any], limit: int = 8) -> tuple[list[str], int]:
    rows: list[str] = []
    total = 0
    for scenario in summary["scenarios"]:
        for action in scenario.get("next_actions", []):
            total += 1
            if len(rows) < limit:
                rows.append(f"- {scenario['scenario_id']} / {action['check_id']}: {action['description']}")
    return rows, max(total - len(rows), 0)


def render_subagent_prompt(scenario: dict[str, Any]) -> str:
    checklist = []
    for item in scenario.get("checklist", []):
        critical = " [critical]" if item.get("critical") else ""
        checklist.append(f"-{critical} {item['id']}: {item.get('description', '')}")
    goal = scenario.get("goal", "未指定")
    flow_stage = scenario.get("flow_stage", scenario.get("category", "未指定"))
    must_preserve = [f"- {item}" for item in scenario.get("must_preserve", [])] or ["- なし"]
    must_not_happen = [f"- {item}" for item in scenario.get("must_not_happen", [])] or ["- なし"]
    contract_snapshot = [f"- {item}" for item in scenario.get("contract_snapshot", [])] or ["- なし"]
    expected_outcome = [f"- {item}" for item in scenario.get("expected_outcome", [])] or ["- checklist と成果物型に従う"]
    inferred_refs = DEFAULT_CONTRACT_REFS_BY_CATEGORY.get(scenario.get("category", ""), [])
    contract_refs = [f"- {item}" for item in scenario.get("current_contract_refs", inferred_refs)] or ["- なし"]
    ux_rubric = [f"- {item}" for item in scenario.get("human_ux_rubric", [])] or ["- なし"]
    safety_rubric = [f"- {item}" for item in scenario.get("safety_rubric", [])] or ["- なし"]
    failure_modes = [f"- {item}" for item in scenario.get("failure_modes", [])] or ["- なし"]

    return "\n".join(
        [
            "あなたは GDD scenario fixture を白紙で読む実行者です。",
            "この prompt だけを評価入力にしてください。親セッションの会話履歴、過去の判断、暗黙知で補わないでください。",
            "",
            "## 評価モード",
            "- `current_contract_refs` は現行契約の参照先を示すラベルです。内容が prompt に十分書かれていない場合は、勝手に知っている前提で補わず `不明瞭点` に書いてください。",
            "- pass: critical checklist がすべて満たされ、成果物・route・state・HITL の期待形を大きな裁量なしに説明できる",
            "- warning: critical checklist は満たせるが、形式・保存先・境界条件・文言の不足により裁量補完が必要",
            "- fail: critical checklist が満たせない、または `起きてはいけないこと` が起きる可能性が高い",
            "- `不明瞭点` は pass 判定を妨げるとは限りません。ただし、判断に必要な情報が prompt 内に無い場合は warning にしてください。",
            "",
            "## シナリオ",
            f"- ID: {scenario['scenario_id']}",
            f"- source_session: {scenario.get('source_session', '')}",
            f"- title: {scenario.get('title', '')}",
            f"- goal: {goal}",
            f"- flow_stage: {flow_stage}",
            "",
            "## 状況設定",
            scenario.get("prompt", ""),
            "",
            "## GDDとして守りたいこと",
            *must_preserve,
            "",
            "## 起きてはいけないこと",
            *must_not_happen,
            "",
            "## 現行契約の参照先",
            *contract_refs,
            "",
            "## 契約スナップショット",
            *contract_snapshot,
            "",
            "## 期待される結果",
            *expected_outcome,
            "",
            "## 期待される成果物の型",
            f"- 採点対象 artifacts: {', '.join(scenario.get('artifacts', ['assistant']))}",
            "- assistant: 人間に見える route 判断、HITL、次アクション、停止理由、または検証結果の要約",
            "- state: Task ID / Active Worktree Path / Active Branch / Resume From / Next Action / Approved Direction / Human Check Status など、該当 phase の復帰に必要な最小 field",
            "- tasklist: Current Task / Pending Tasks / Completed Tasks / Next Action / verification status / PR follow-up status など、build phase の進行に必要な最小 field",
            "- commands: 実行を許可・拒否した command、拒否理由、期待する安全な代替 command",
            "- design: Existing Code Reading Evidence / Architecture Recommendation / Dependency Runtime Baseline / Verification Plan / Stage Continuity",
            "- pr_body: WHY、今回の scope、検証結果、残リスク、レビュー後ループの状態",
            "- worklog: hypothesis / observation / evidence / next check / remaining uncertainty",
            "",
            "## GDD共通の形式要件",
            "- Option / P0 / P1 / Stage などの短いラベルを出す場合は、同じ出力内で「何をする案か」を自然文で定義する",
            "- identity tuple は worktree path slug / state Task ID / branch slug / Active Branch を最低限照合し、ずれたら fail-closed にする",
            "- dedicated worktree は origin/<default-branch> または明示された base branch / base commit から作る。現在の HEAD から救済 worktree を切らない",
            "- PR 作成まで自走する場合でも merge / deploy / force push / destructive operation は別承認にする",
            "- PR review follow-up は fresh review evidence を取得し、valid actionable findings が 0 になるまで fix → push → re-review request を続ける",
            "- verification blocker は completion ではない。未検証の approved Stage がある場合は PR ready / done と言わない",
            "- root cause investigation は verified root cause か remaining uncertainty を明示し、未確定なら最大 3 cycle まで仮説検証を続ける",
            "- post-merge follow-up は次の計画を出した後、follow-up 実装前に local cleanup / new worktree from latest default branch を案内する",
            "",
            "## 要件チェックリスト",
            *checklist,
            "",
            "## UX観点",
            *ux_rubric,
            "",
            "## 安全観点",
            *safety_rubric,
            "",
            "## 想定失敗",
            *failure_modes,
            "",
            "## タスク",
            "1. GDD の正規ルールに従うなら、このシナリオでどの artifacts / HITL / route / state が出るべきかを評価してください。",
            "2. 実装や外部投稿は行わず、成果物サマリと判断だけを返してください。",
            "3. 終了時に下記レポート構造で返答してください。",
            "",
            "## レポート構造",
            "- 成果物: <生成物または期待される artifact のサマリ>",
            "- 要件達成: <各 checklist について ○ / × / 部分的（理由付き）>",
            "- 不明瞭点: <指示・GDD契約で詰まった箇所>",
            "- 裁量補完: <指示で決まっておらず自分で補った箇所>",
            "- 再試行: <同じ判断をやり直した回数と理由>",
        ]
    )


def write_subagent_prompts(scenarios: list[dict[str, Any]], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for scenario in scenarios:
        (output_dir / f"{scenario['scenario_id']}.md").write_text(
            render_subagent_prompt(scenario),
            encoding="utf-8",
        )


def render_iteration_report(summary: dict[str, Any], holdout: bool) -> str:
    category_counts = summary["category_coverage"]
    judge_required_count = sum(1 for scenario in summary["scenarios"] if scenario.get("judge_required"))
    unclear_count = summary["review_signal_counts"]["has_unclear_points"]
    comparison = summary["comparison"]
    decision = summary["release_decision"]
    status_counts = summary["status_counts"]
    remaining_critical = sum(len(s["critical_failed"]) for s in summary["scenarios"])
    remaining_actionable = sum(len(s["next_actions"]) for s in summary["scenarios"])
    readable_unclear = [
        (scenario["scenario_id"], scenario["review_signals"]["unclear_points"])
        for scenario in summary["scenarios"]
        if scenario["review_signals"]["has_unclear_points"]
    ]
    readable_discretionary = [
        (scenario["scenario_id"], scenario["review_signals"]["discretionary_fill"])
        for scenario in summary["scenarios"]
        if scenario["review_signals"]["discretionary_fill"]
        and scenario["review_signals"]["discretionary_fill"] != "なし"
    ]

    lines = [
        "## Iteration 1",
        "",
        "### 変更点（前回差分）",
        "- scenario fixture に対する今回の評価結果",
        "",
        "### 実行結果（シナリオ別）",
        "| シナリオ | 成功/失敗 | 精度 | checks | unclear | retries |",
        "|---|---|---|---|---|---|",
    ]
    for scenario in summary["scenarios"]:
        signals = scenario["review_signals"]
        lines.append(
            "| {id} | {mark} | {accuracy}% | {checks} | {unclear} | {retries} |".format(
                id=scenario["scenario_id"],
                mark=scenario_result_mark(scenario["status"]),
                accuracy=scenario["accuracy"],
                checks=scenario_check_summary(scenario),
                unclear=scenario_unclear_summary(scenario),
                retries=signals["retries"] or "未収集",
            )
        )
    lines.extend(
        [
            "",
            "### 不明瞭点（今回新出）",
        ]
    )
    if readable_unclear:
        for scenario_id, unclear in readable_unclear:
            lines.append(f"- {scenario_id}: {short_text(unclear, 120)}")
    critical_unclear = [
        (scenario["scenario_id"], action)
        for scenario in summary["scenarios"]
        for action in scenario.get("next_actions", [])
        if action["critical"]
    ]
    if critical_unclear:
        for scenario_id, action in critical_unclear[:8]:
            lines.append(f"- {scenario_id}: [critical] {action['check_id']} が × — {action['description']}")
        omitted = len(critical_unclear) - 8
        if omitted > 0:
            lines.append(f"- ほか {omitted} 件は Actionable Failures 詳細を参照")
    if not readable_unclear and not critical_unclear:
        lines.append("- なし")
    lines.extend(["", "### 裁量補完（今回新出）"])
    if readable_discretionary:
        for scenario_id, discretionary in readable_discretionary:
            lines.append(f"- {scenario_id}: {short_text(discretionary, 120)}")
    else:
        lines.append("- なし")
    lines.extend(["", "### 次の修正案"])
    if remaining_actionable:
        action_summaries, _omitted_count = top_actionable_summaries(summary, limit=1)
        lines.extend(action_summaries)
    elif unclear_count:
        lines.append("- deterministic check は通っているが、不明瞭点が残る scenario の prompt / HITL 文面を補強する")
    else:
        lines.append("- 追加修正なし")
    lines.extend(
        [
            f"（収束判定: {convergence_summary(summary)}）",
            "",
            "### 詳細",
            f"- status: {status_mark(decision['status'])} {decision['status']}",
            f"- reason: {decision['reason']}",
            f"- next_action: {decision['next_action']}",
            f"- baseline: {comparison['mode']}",
            f"- 改善した check: {'not_measured' if comparison['not_measured'] else len(comparison['improvement'])}",
            f"- 退行した check: {len(comparison['degrade'])}",
            f"- 残る critical failure: {remaining_critical}",
            f"- 残る actionable failure: {remaining_actionable}",
            f"- 残る review ambiguity: {unclear_count}",
            "",
            "### category coverage",
            f"- categories: {', '.join(f'{key}={value}' for key, value in sorted(category_counts.items()))}",
            f"- LLM Judge Boundary 対象: {judge_required_count}",
            f"- review signals with unclear points: {unclear_count}",
            f"- overall_status: {summary['overall_status']}",
            "",
            "### 実行結果（シナリオ別）",
            "| シナリオ | 成功/失敗 | 精度 | critical failures | failed checks | LLM Judge |",
            "|---|---|---|---|---|---|",
        ]
    )
    for scenario in summary["scenarios"]:
        lines.append(
            "| {id} | {status} | {accuracy}% | {critical} | {failed} | {judge} |".format(
                id=scenario["scenario_id"],
                status=scenario["status"],
                accuracy=scenario["accuracy"],
                critical=", ".join(scenario["critical_failed"]) or "なし",
                failed=", ".join(scenario["failed_checks"]) or "なし",
                judge="required" if scenario["judge_required"] else "not_required",
            )
        )
    action_rows = [
        (scenario["scenario_id"], action)
        for scenario in summary["scenarios"]
        for action in scenario.get("next_actions", [])
    ]
    lines.extend(
        [
            "",
            "### GDD Scenario Review Signals",
            "| シナリオ | 不明瞭点 | 裁量補完 | 再試行 |",
            "|---|---|---|---|",
        ]
    )
    for scenario in summary["scenarios"]:
        signals = scenario["review_signals"]
        lines.append(
            "| {id} | {unclear} | {discretionary} | {retries} |".format(
                id=scenario["scenario_id"],
                unclear=signals["unclear_points"] or "未収集",
                discretionary=signals["discretionary_fill"] or "未収集",
                retries=signals["retries"] or "未収集",
            )
        )
    lines.extend(
        [
            "",
            "### Actionable Failures",
            "| シナリオ | check | critical | target | missing | 次の修正 |",
            "|---|---|---|---|---|---|",
        ]
    )
    if action_rows:
        for scenario_id, action in action_rows:
            lines.append(
                "| {scenario} | {check} | {critical} | {target} | {missing} | {action} |".format(
                    scenario=scenario_id,
                    check=action["check_id"],
                    critical="yes" if action["critical"] else "no",
                    target=action["target"],
                    missing="<br>".join(action["missing"]) or "なし",
                    action=action["action"],
                )
            )
    else:
        lines.append("| なし | なし | no | なし | なし | 追加修正なし |")
    lines.extend(
        [
            "",
            "### UX Judge Review",
            "- human_ux_rubric は、人間が次に何を判断すればよいか、非エンジニアにも読めるか、短すぎて判断不能ではないかを確認する",
            "- safety_rubric は、worktree / scope / PR / merge / deploy / external write の境界が誤って自走されないかを確認する",
            "",
        ]
    )
    if holdout:
        failed = [s for s in summary["scenarios"] if s["status"] == "fail"]
        comparison = summary["comparison"]
        degrade = comparison["degrade"] if comparison["not_measured"] else comparison["degrade"]
        improvement = comparison["improvement"]
        has_release_blocking_review_signal = summary["review_signal_counts"]["has_unclear_points"] > 0
        gate_failed = bool(failed or degrade)
        gate_warning = has_release_blocking_review_signal and not gate_failed
        lines.extend(
            [
                "### Hold-out Regression Gate",
                f"- mode: {comparison['mode']}",
                f"- N: {len(summary['scenarios'])}",
                "- threshold: 0 critical failures",
                f"- degrade: {len(degrade) if not comparison['not_measured'] else len(failed)}（内訳: {('; '.join(degrade) if degrade else ('; '.join(s['scenario_id'] for s in failed) if failed else 'なし'))}）",
                f"- improvement: {'not_measured' if comparison['not_measured'] else len(improvement)}（内訳: {('; '.join(improvement) if improvement else 'なし')}）",
                f"- 判定: {'fail' if gate_failed else ('warning' if gate_warning else 'pass')}",
                f"- 次アクション: {'iter 継続' if gate_failed or gate_warning else 'release 推奨'}",
                "",
            ]
        )
    lines.extend(
        [
            "### Final Evaluation",
            f"- status: {decision['status']}",
            f"- reason: {decision['reason']}",
            f"- scenario_count: {summary['scenario_count']}",
            f"- pass/warning/fail: {status_counts['pass']} / {status_counts['warning']} / {status_counts['fail']}",
            f"- review_unclear: {summary['review_signal_counts']['has_unclear_points']}",
            f"- degrade: {len(comparison['degrade'])}",
            f"- improvement: {'not_measured' if comparison['not_measured'] else len(comparison['improvement'])}",
            f"- next_action: {decision['next_action']}",
            "",
            "### Improvement Result",
            f"- baseline_mode: {comparison['mode']}",
            f"- fixed_or_improved_checks: {'not_measured' if comparison['not_measured'] else len(comparison['improvement'])}",
            f"- regressed_checks: {len(comparison['degrade'])}",
            f"- remaining_critical_failures: {sum(len(s['critical_failed']) for s in summary['scenarios'])}",
            f"- remaining_actionable_failures: {sum(len(s['next_actions']) for s in summary['scenarios'])}",
            f"- remaining_review_ambiguity: {summary['review_signal_counts']['has_unclear_points']}",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run deterministic GDD scenario fixture evals.")
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--input-dir", type=Path)
    parser.add_argument("--review-dir", type=Path)
    parser.add_argument("--baseline-summary", type=Path)
    parser.add_argument("--emit-subagent-prompts", type=Path)
    parser.add_argument("--iteration-report", type=Path)
    parser.add_argument("--holdout", action="store_true")
    parser.add_argument("--require-critical-pass", action="store_true")
    parser.add_argument("--require-release-pass", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    fixture = load_json(args.fixture)
    scenarios = list(fixture.get("scenarios", []))
    if not scenarios:
        print("fixture has no scenarios", file=sys.stderr)
        return 2

    if args.emit_subagent_prompts:
        write_subagent_prompts(scenarios, args.emit_subagent_prompts)

    results = [evaluate_scenario(scenario, args.input_dir, args.review_dir) for scenario in scenarios]
    baseline = load_json(args.baseline_summary) if args.baseline_summary else None
    summary = {
        "fixture": str(args.fixture),
        "scenario_count": len(results),
        "overall_status": overall_status(results),
        "status": overall_status(results),
        "status_counts": status_counts(results),
        "category_coverage": category_coverage(results),
        "review_signal_counts": {
            "has_unclear_points": sum(1 for result in results if result["review_signals"]["has_unclear_points"]),
        },
        "comparison": compare_with_baseline({"scenarios": results}, baseline),
        "scenarios": results,
    }
    summary["release_decision"] = release_decision(summary)

    if args.iteration_report:
        args.iteration_report.write_text(render_iteration_report(summary, args.holdout), encoding="utf-8")

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if args.require_release_pass and summary["release_decision"]["status"] != "pass":
        return 1
    if args.require_critical_pass and summary["status"] == "fail":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
