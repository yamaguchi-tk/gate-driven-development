#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


LEAF_HINTS = (
    "classify",
    "extract",
    "ranking",
    "route",
    "routing",
    "normalize",
    "dedupe",
    "parse",
    "token",
    "lookup",
    "分類",
    "抽出",
    "ランキング",
    "ルーティング",
    "正規化",
    "重複除去",
    "パース",
)

LIGHT_HINTS = (
    "summary",
    "onboarding",
    "faq",
    "lightweight",
    "simple",
    "draft",
    "resume",
    "continue",
    "summary brief",
    "faq",
    "onboarding",
    "壁打ち",
    "要約",
    "初稿",
    "再開",
    "継続",
    "軽量",
)

# phase 未確定の entry で formal gate（brainstorming が最初のフェーズ）を
# light に落とさないための hint。phase が判明している場合は PHASE_TO_TIER が優先される。
GATE_ENTRY_HINTS = (
    "brainstorming",
    "gdd-brainstorming",
    "requirements",
    "要件整理",
    "要件定義",
)

AMBIGUITY_HINTS = (
    "uncertain",
    "unclear",
    "ambiguous",
    "ambiguity",
    "not sure",
    "unknown",
    "曖昧",
    "不明",
    "わからない",
    "確信がない",
)

CROSS_SCOPE_HINTS = (
    "cross-phase",
    "cross phase",
    "cross-cutting",
    "cross module",
    "cross-module",
    "multiple files",
    "multi-file",
    "multi file",
    "multiple modules",
    "repo-wide",
    "repository-wide",
    "複数ファイル",
    "複数モジュール",
    "横断",
    "リポジトリ全体",
)

LONG_HORIZON_HINTS = (
    "re-entry",
    "rework",
    "recheck",
    "re-check",
    "revisit",
    "rerun",
    "retry",
    "compare",
    "tradeoff",
    "investigate",
    "debug",
    "implementation",
    "gdd-task-breakdown",
    "gdd-implementation-gating",
    "gdd-completion-check",
    "gdd-design-gating",
    "design",
    "complex",
    "root cause",
    "multi-step",
    "end-to-end",
    "handoff",
    "phase transition",
    "review feedback",
    "deep debug",
    "深いデバッグ",
    "根本原因",
    "多段",
    "段階的",
    "トレードオフ",
    "比較検討",
    "設計",
    "実装",
)

TOOL_HEAVY_HINTS = (
    "tool-heavy",
    "tool heavy",
    "subagent",
    "subagents",
    "shell",
    "terminal",
    "git",
    "terraform",
    "applypatch",
    "readfile",
    "computer use",
    "mcp",
    "サブエージェント",
    "シェル",
    "ターミナル",
    "git worktree",
)

FINAL_REVIEW_HINTS = (
    "final review",
    "final confirmation",
    "final check",
    "pr-ready",
    "pr ready",
    "pre-pr",
    "before merge",
    "code review",
    "design review",
    "security review",
    "gdd-completion-check",
    "gdd-implementation-gating",
    "gdd-design-gating",
    "最終レビュー",
    "最終確認",
    "PR作成前",
    "PR 作成前",
    "マージ前",
    "コードレビュー",
    "設計レビュー",
    "セキュリティレビュー",
    "完了確認",
    "review feedback",
)

UNDOCUMENTED_STEP_HINTS = (
    "undocumented step",
    "insufficient investigation",
    "insufficient evidence",
    "evidence missing",
    "no runbook",
    "without runbook",
    "手順がない",
    "調査不足",
    "証跡不足",
    "evidence 不足",
    "runbook がない",
    "未文書化",
)

LARGE_WORKING_SET_HINTS = (
    "large context",
    "wide scope",
    "broad refactor",
    "many files",
    "many modules",
    "whole repo",
    "whole repository",
    "large codebase",
    "広範囲",
    "大量ファイル",
    "広いスコープ",
    "大きいコードベース",
    "全体改修",
)

SECURITY_SENSITIVE_HINTS = (
    "security-sensitive",
    "permission",
    "secret",
    "iam",
    "snyk",
    "認可",
    "権限",
    "秘密情報",
)

PHASE_TO_TIER = {
    "gdd-brainstorming": "formal_gate",
    "gdd-pre-workflow-brainstorming": "light_task",
    "gdd-requirements-gating": "formal_gate",
    "gdd-requirements-amendment": "formal_gate",
    "gdd-design-gating": "formal_gate",
    "gdd-task-breakdown": "light_task",
    "gdd-test-driven-development": "light_task",
    "gdd-subagent-driven-implementation": "implementation",
    "gdd-implementation-gating": "formal_gate",
    "gdd-systematic-debugging": "general_heavy",
    "gdd-completion-check": "formal_gate",
    "gdd-refactor-planning": "general_heavy",
    "gdd-requesting-code-review": "general_heavy",
    "gdd-receiving-code-review": "light_task",
    # 最終 diff review。2026-08-22 実測（gate 通過後に残った実害級欠陥を Opus+high の
    # 最終レビューだけが検出）に基づき light_task から昇格（2026-08-25）
    "gdd-pr-review": "general_heavy_risk",
    "gdd-test-failure-debug-pack": "light_task",
    "gdd-status": "leaf_task",
    "gdd-metrics": "leaf_task",
    "gdd-using-git-worktrees": "leaf_task",
}

TIER_TO_MODEL = {
    "claude_code": {
        "leaf_task": "sonnet",
        "light_task": "sonnet",
        "implementation": "sonnet",
        "formal_gate": "opus",
        "general_heavy": "opus",
        "general_heavy_risk": "opus",
        # 往復発生時（references/fixed-models.md § remediation_loop。Opus + xhigh）
        "remediation_loop": "opus",
        # 独立レビュー（references/fixed-models.md § independent_review）。worker runner
        # 経由では起動しないため --complexity からは届かない。表との同期のためのキー
        "independent_review": "opus",
    },
    "cursor": {
        # 2026-08-25 最新化: Grok + Composer 主体（GPT-5.4/5.5 系は routing から除外。
        # GPT-5.4 は 2026-08-31 廃止予定）。詳細は references/cursor.md
        # leaf / light: Grok 4.5（state / routing source を読むため cheap lane に落とさない）
        "leaf_task": "grok-4.5",
        "light_task": "grok-4.5",
        # Cursor の実装は Composer 2.5 に固定する。composer-2-fast は使わない
        "implementation": "composer-2.5",
        # heavy 既定は Grok 4.6（effort は per-phase: formal gate=medium / 一般=low / risk=high）
        "formal_gate": "grok-4.6",
        "general_heavy": "grok-4.6",
        "general_heavy_risk": "grok-4.6",
        # 往復発生時（references/fixed-models.md）。general_heavy_risk と同じ写像
        "remediation_loop": "grok-4.6",
        # 独立レビュー（references/fixed-models.md § independent_review）。worker runner
        # 経由では起動しないため --complexity からは届かない。表との同期のためのキー
        "independent_review": "grok-4.6",
    },
    "codex": {
        # 2026-08-25 最新化: GPT-5.6 系（Sol/Terra/Luna）へ移行。GPT-5.4 は使わない
        # （2026-08-31 廃止予定）。GPT-5.5 も一世代前のため Terra（5.5 相当・低コスト）へ。
        # 詳細は references/codex.md
        "leaf_task": "gpt-5.6-terra",
        "light_task": "gpt-5.6-terra",
        "implementation": "gpt-5.6-terra",
        "formal_gate": "gpt-5.6-sol",
        "general_heavy": "gpt-5.6-sol",
        "general_heavy_risk": "gpt-5.6-sol",
        "remediation_loop": "gpt-5.6-sol",
        # 独立レビュー（references/fixed-models.md § independent_review）。worker runner
        # 経由では起動しないため --complexity からは届かない。表との同期のためのキー
        "independent_review": "gpt-5.6-sol",
    },
}

# Phase-specific overrides — 現状は使用しない（tier 既定＝host 既定モデルで足りるため）。
# effort の differentiation は references/cursor.md / references/codex.md /
# references/fixed-models.md で per-phase に文書化する。
# 将来 phase ごとに別 model を割り当てる必要が出たら復活させる。
PHASE_MODEL_OVERRIDE: dict[str, dict[str, str]] = {}

FORMAL_GATE_PHASES = {
    "gdd-brainstorming",
    "gdd-requirements-gating",
    "gdd-design-gating",
    "gdd-implementation-gating",
    "gdd-completion-check",
    "gdd-requirements-amendment",
}

# formal gate 相当以上（general_heavy / general_heavy_risk を含む）の tier 集合。
# 独立レビュー round 4 指摘（F9）: 同じ集合が classify_tier() 内に複数リテラルで
# 存在すると片方だけ更新される退行の芽になるため、1 箇所にまとめて共有する。
HEAVY_OR_ABOVE_TIERS = frozenset({"formal_gate", "general_heavy", "general_heavy_risk"})

RISK_ESCALATION_SIGNALS = {
    "undocumented_step",
    "large_working_set",
    "security_sensitive",
    "final_review",
}


def _split_frontmatter(text: str) -> tuple[str, str] | None:
    # 独立レビュー round 10 High/blocking 指摘（H-1）: 従来この関数と
    # `read_text_from_state()` は個別に `text.split("---\n", 2)`（部分文字列一致）
    # で frontmatter 終端を判定していた。`hooks/scripts/lib/state_io.py
    # ::parse_state()` が round 9 H-1 で修正したのと同じ入口（frontmatter の値が
    # ちょうど `"---"` になる行、例: `resume_from_baseline: ---`）で、同種の
    # fail-open（それより後ろの `detected_phase` が丸ごと読み落とされ、formal
    # gate phase が `light_task` へ黙って降格する）を踏んでいた。`state_io.py
    # ::parse_state()` と対称に「内容が厳密に `---` である行」でのみ終端を判定し、
    # 両関数で共通化することで対になる片方だけを直す再発を防ぐ。
    if not text.startswith("---\n"):
        return None
    lines = text.split("\n")
    try:
        end_index = lines.index("---", 1)
    except ValueError:
        return None
    frontmatter_raw = "\n".join(lines[1:end_index])
    body = "\n".join(lines[end_index + 1 :])
    return frontmatter_raw, body


def extract_frontmatter_value(text: str, key: str) -> str | None:
    split = _split_frontmatter(text)
    if split is None:
        return None
    frontmatter_raw, _ = split
    for raw_line in frontmatter_raw.splitlines():
        if ":" not in raw_line:
            continue
        current_key, value = raw_line.split(":", 1)
        if current_key.strip() == key:
            return value.strip()
    return None


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower())


def matched_hints(text: str, hints: tuple[str, ...]) -> list[str]:
    return [hint for hint in hints if hint in text]


def analyze_signals(text: str) -> dict[str, object]:
    lowered = normalize_text(text)
    word_count = len(lowered.split()) if lowered else 0

    leaf_matches = matched_hints(lowered, LEAF_HINTS)
    light_matches = matched_hints(lowered, LIGHT_HINTS)
    ambiguity_matches = matched_hints(lowered, AMBIGUITY_HINTS)
    cross_scope_matches = matched_hints(lowered, CROSS_SCOPE_HINTS)
    long_horizon_matches = matched_hints(lowered, LONG_HORIZON_HINTS)
    tool_heavy_matches = matched_hints(lowered, TOOL_HEAVY_HINTS)
    final_review_matches = matched_hints(lowered, FINAL_REVIEW_HINTS)
    undocumented_matches = matched_hints(lowered, UNDOCUMENTED_STEP_HINTS)
    large_working_set_matches = matched_hints(lowered, LARGE_WORKING_SET_HINTS)
    security_matches = matched_hints(lowered, SECURITY_SENSITIVE_HINTS)

    return {
        "leaf_task": bool(leaf_matches),
        "light_task": bool(light_matches),
        "ambiguous": bool(ambiguity_matches),
        "cross_scope": bool(cross_scope_matches),
        "long_horizon": bool(long_horizon_matches),
        "tool_heavy": bool(tool_heavy_matches),
        "final_review": bool(final_review_matches),
        "undocumented_step": bool(undocumented_matches),
        "large_working_set": bool(large_working_set_matches),
        "security_sensitive": bool(security_matches),
        "word_count": word_count,
        "matches": {
            "leaf_task": leaf_matches,
            "light_task": light_matches,
            "ambiguous": ambiguity_matches,
            "cross_scope": cross_scope_matches,
            "long_horizon": long_horizon_matches,
            "tool_heavy": tool_heavy_matches,
            "final_review": final_review_matches,
            "undocumented_step": undocumented_matches,
            "large_working_set": large_working_set_matches,
            "security_sensitive": security_matches,
        },
    }


def classify_tier(
    text: str,
    phase: str | None,
    complexity: str | None,
) -> tuple[str, list[str], dict[str, object]]:
    # tier の明示指定は remediation_loop のみ受理する（正本:
    # references/subagent-dispatch.md § Codex / Cursor Worker Dispatch）。
    # leaf/light/heavy はかつて存在したが、phase 判定より無条件に優先されるため
    # formal gate phase（`PHASE_TO_TIER` で tier="formal_gate" の phase 集合。
    # `FORMAL_GATE_PHASES` はこのモジュールでは未使用で、`run-gdd-worker.py`
    # 側との一致 pin 用にのみ残している。独立レビュー round 7 指摘: 本コメントが
    # あたかも `classify_tier()` がこの定数を参照しているかのように誤読させて
    # いたため訂正）を黙って軽い tier へ降格できる fail-open だった（PR #89
    # self-review HIGH。実際にこれらを渡す呼び出し元は 0 件だったため、
    # argparse の choices ごと削除して機械的に閉じた。CHANGELOG-archive-3.md
    # の同型再発）。
    phase_tier = PHASE_TO_TIER.get(phase or "", "light_task")

    if complexity == "remediation_loop":
        # 往復発生時に controller が明示指定する（phase 由来では判定しない）
        return "remediation_loop", [
            "explicit_complexity:remediation_loop",
            "tier_alias:remediation_loop",
        ], {"explicit_complexity": complexity}

    signals = analyze_signals(text)
    rules: list[str] = []

    # phase は既定 tier。だが heavy への昇格条件は phase より優先する。
    if signals["undocumented_step"]:
        rules.append("general_heavy_risk:undocumented_step")
        return "general_heavy_risk", rules, signals

    if signals["large_working_set"]:
        rules.append("general_heavy_risk:large_working_set")
        return "general_heavy_risk", rules, signals

    if signals["final_review"]:
        rules.append("general_heavy_risk:final_review")
        return "general_heavy_risk", rules, signals

    if signals["security_sensitive"] and phase_tier in {"implementation", "general_heavy"}:
        rules.append("general_heavy_risk:security_sensitive")
        return "general_heavy_risk", rules, signals

    if signals["tool_heavy"] and (
        signals["long_horizon"] or signals["cross_scope"] or signals["security_sensitive"]
    ):
        rules.append("general_heavy_risk:tool_heavy_with_branching")
        return "general_heavy_risk", rules, signals

    if signals["cross_scope"] and (
        signals["ambiguous"] or signals["long_horizon"] or signals["security_sensitive"]
    ):
        rules.append("general_heavy_risk:cross_scope_with_branching")
        return "general_heavy_risk", rules, signals

    if signals["ambiguous"] and (
        signals["long_horizon"]
        or signals["security_sensitive"]
        or phase_tier in HEAVY_OR_ABOVE_TIERS
    ):
        rules.append("general_heavy_risk:ambiguity_with_branching")
        return "general_heavy_risk", rules, signals

    if not phase and matched_hints(normalize_text(text), GATE_ENTRY_HINTS):
        rules.append("formal_gate:entry_hint")
        return "formal_gate", rules, signals

    if (
        signals["leaf_task"]
        and phase_tier not in HEAVY_OR_ABOVE_TIERS
        # 独立レビュー round 4 High/blocking 指摘（F2）: `phase` が非空だが
        # `PHASE_TO_TIER` に無い値（未知・表記ゆれ・タイポ）は phase_tier が
        # permissive な既定（light_task）へ倒れ floor が効かなかった。閉じた
        # 部分集合として、未知 phase は leaf_task 分岐を素通りさせない
        # （ユーザー確認のうえ本 PR で修正。完全に開いた自由文字列の正規化は
        # hooks/scripts/gdd_stop_hook.py 側の marker 抽出の正規化で別途対処）。
        and (not phase or phase in PHASE_TO_TIER)
        and not any(
            (
                signals["ambiguous"],
                signals["cross_scope"],
                signals["long_horizon"],
                signals["tool_heavy"],
                signals["final_review"],
                signals["undocumented_step"],
                signals["large_working_set"],
                signals["security_sensitive"],
            )
        )
    ):
        rules.append("leaf_task:bounded_leaf_task")
        return "leaf_task", rules, signals

    if phase:
        rules.append(f"phase_default:{phase_tier}:{phase}")
        return phase_tier, rules, signals

    if signals["light_task"]:
        rules.append("light_task:bounded_first_pass")
        return "light_task", rules, signals

    rules.append("default:light_task")
    return "light_task", rules, signals


def resolve_effort(
    runtime: str,
    tier: str,
    phase: str | None,
    signals: dict[str, object],
) -> str:
    """Return the runtime-specific reasoning effort for the resolved tier."""
    if runtime == "claude_code":
        return {
            "leaf_task": "low",
            "light_task": "medium",
            "implementation": "medium",
            "formal_gate": "high",
            "general_heavy": "high",
            "general_heavy_risk": "high",
            "remediation_loop": "xhigh",
            "independent_review": "xhigh",
        }[tier]

    if tier == "leaf_task":
        return "low"
    if tier == "light_task":
        return "medium"
    if tier == "implementation":
        return "n/a" if runtime == "cursor" else "low"
    if tier == "formal_gate":
        return "medium"
    if tier in {"general_heavy_risk", "remediation_loop", "independent_review"}:
        return "high"

    if any(bool(signals.get(signal_name)) for signal_name in RISK_ESCALATION_SIGNALS):
        return "high"

    return "low"


def read_text_from_state(state_file: Path) -> str:
    if not state_file.exists():
        return ""
    text = state_file.read_text(encoding="utf-8")
    split = _split_frontmatter(text)
    if split is not None:
        _, body = split
        return body
    return text


def main() -> int:
    parser = argparse.ArgumentParser(description="Resolve the GDD model")
    parser.add_argument("--runtime", choices=("claude_code", "cursor", "codex"), default="claude_code")
    parser.add_argument("--text", default="")
    parser.add_argument("--phase", default="")
    parser.add_argument("--complexity", choices=("remediation_loop",), default="")
    parser.add_argument("--state-file", default="")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    state_path = Path(args.state_file).expanduser() if args.state_file else None
    state_text = ""
    if state_path and state_path.exists():
        state_text = state_path.read_text(encoding="utf-8")

    text = args.text
    if not text and state_path:
        text = read_text_from_state(state_path)
    if state_text and not text:
        text = read_text_from_state(state_path)

    phase = args.phase or (
        extract_frontmatter_value(state_text, "detected_phase")
        or extract_frontmatter_value(state_text, "workflow_phase")  # legacy fallback
        if state_text else None
    )
    # 独立レビュー round 6 High/blocking 指摘（H-1）: `hooks/scripts/gdd_stop_hook.py
    # ::_detect_phase()` と `run-gdd-worker.py::main()` には `.strip().lower()`
    # 正規化を足した（round 4/5）が、この関数自身（`--phase` 引数・state file の
    # `detected_phase`/`workflow_phase` の両方が集約されるこの 1 点）には及んで
    # いなかった。`PHASE_TO_TIER` は完全一致 lookup のため、表記ゆれのまま渡すと
    # `phase in PHASE_TO_TIER` の floor も `phase_tier` の解決も外れ、formal gate
    # phase が `light_task` へ黙って降格していた。ここで正規化することで、
    # `--phase` 直接指定・state file 経由の両チャネルを一括で閉じる。
    if phase:
        phase = phase.strip().lower()
    tier, reasons, signals = classify_tier(text, phase, args.complexity or None)

    model = TIER_TO_MODEL[args.runtime][tier]
    # Phase-specific override (e.g., host ごとに特定 phase だけ別 model へ逃がす場合)
    phase_override = PHASE_MODEL_OVERRIDE.get(args.runtime, {}).get(phase or "")
    if phase_override and tier in HEAVY_OR_ABOVE_TIERS:
        model = phase_override
        reasons.append(f"phase_override:{phase}:{phase_override}")
    model_source = "resolver"
    effort = resolve_effort(args.runtime, tier, phase, signals)

    payload = {
        "runtime": args.runtime,
        "phase": phase or "",
        "tier": tier,
        "model": model,
        "effort": effort,
        "model_source": model_source,
        "reasons": reasons,
        "signals": signals,
    }

    if args.json:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(model)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
