#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESOLVER = ROOT / "scripts" / "resolve-gdd-model.py"
FORMAL_GATE_PHASES = {
    "gdd-brainstorming",
    "gdd-requirements-gating",
    "gdd-design-gating",
    "gdd-implementation-gating",
    "gdd-completion-check",
    "gdd-requirements-amendment",
}


def resolve_model(
    runtime: str, phase: str, text: str, state_file: str | None, complexity: str | None = None
) -> dict[str, object]:
    cmd = [
        sys.executable,
        str(RESOLVER),
        "--runtime",
        runtime,
        "--phase",
        phase,
        "--text",
        text,
        "--json",
    ]
    if state_file:
        cmd.extend(["--state-file", state_file])
    if complexity:
        cmd.extend(["--complexity", complexity])
    result = subprocess.run(cmd, text=True, capture_output=True, check=False)
    if result.returncode != 0:
        raise SystemExit(result.stderr or result.stdout)
    return json.loads(result.stdout)


def build_command(runtime: str, model: str, effort: str, prompt: str, cwd: str | None) -> list[str]:
    if runtime == "codex":
        cmd = [
            "codex",
            "exec",
            "--model",
            model,
            "-c",
            f"model_reasoning_effort={effort}",
        ]
        if cwd:
            cmd.extend(["--cd", cwd])
        cmd.append(prompt)
        return cmd
    if runtime == "claude_code":
        cmd = ["claude", "--model", model]
        if cwd:
            cmd.extend(["--cwd", cwd])
        cmd.append(prompt)
        return cmd
    if runtime == "cursor":
        cmd = [
            "codex",
            "exec",
            "--model",
            model,
            "-c",
            f"model_reasoning_effort={effort}",
        ]
        if cwd:
            cmd.extend(["--cd", cwd])
        cmd.append(prompt)
        return cmd
    raise ValueError(f"unsupported runtime: {runtime}")


def parse_observed_metadata(stdout: str) -> dict[str, str]:
    """Best-effort parse of model metadata from JSON lines emitted by a fake/real runner."""
    observed: dict[str, str] = {}
    for line in stdout.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        model = payload.get("applied_model") or payload.get("model")
        effort = payload.get("applied_effort") or payload.get("model_reasoning_effort") or payload.get("effort")
        if model:
            observed["applied_model"] = str(model)
        if effort:
            observed["applied_effort"] = str(effort)
    return observed


def fallback_action(phase: str, application_status: str) -> str:
    if phase in FORMAL_GATE_PHASES and application_status in {"unavailable", "failed", "unverified"}:
        return "needs_human_acceptance_or_heavy_retry"
    if application_status in {"unavailable", "failed"}:
        return "warn_and_halt_before_next_phase"
    return "none"


def write_result(output_dir: Path | None, run_id: str, payload: dict[str, object]) -> None:
    if not output_dir:
        return
    run_dir = output_dir / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "result.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a GDD worker with model/effort routing")
    parser.add_argument("--runtime", choices=("codex", "cursor", "claude_code"), default="codex")
    parser.add_argument("--phase", required=True)
    parser.add_argument("--text", default="")
    parser.add_argument("--prompt", default="")
    parser.add_argument("--state-file", default="")
    parser.add_argument("--cwd", default="")
    parser.add_argument("--output-dir", default="")
    parser.add_argument("--runner", default="")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--complexity", choices=("remediation_loop",), default="",
        help="往復発生時は remediation_loop を明示指定する（references/fixed-models.md）。"
        "他の値は formal gate phase を黙って降格させる fail-open だったため受理しない（PR #89）",
    )
    args = parser.parse_args()
    # 独立レビュー round 5 High/blocking 指摘（F-1）: `fallback_action()` は
    # `--phase` をそのまま `FORMAL_GATE_PHASES` と完全一致で比較しており、
    # `hooks/scripts/gdd_stop_hook.py::_detect_phase()` /
    # `resolve-gdd-model.py::classify_tier()` に足した大文字小文字・空白ゆれの
    # 正規化（round 4 F2）が及んでいなかった。同じ `--phase` 入力を読む本モジュール
    # 内の全経路（resolve_model 呼び出し・fallback_action・payload 記録）に対して
    # 対称に正規化する。
    args.phase = args.phase.strip().lower()

    prompt = args.prompt or args.text or f"Run GDD worker phase: {args.phase}"
    resolved = resolve_model(
        args.runtime, args.phase, args.text or prompt, args.state_file or None, args.complexity or None
    )
    requested_model = str(resolved["model"])
    requested_effort = str(resolved["effort"])
    command = build_command(args.runtime, requested_model, requested_effort, prompt, args.cwd or None)
    run_id = f"{time.strftime('%Y%m%d-%H%M%S')}-{args.phase}"

    payload: dict[str, object] = {
        "run_id": run_id,
        "phase": args.phase,
        "runtime": args.runtime,
        "tier": resolved.get("tier", ""),
        "requested_model": requested_model,
        "requested_effort": requested_effort,
        "applied_model": "unknown",
        "applied_effort": "unknown",
        "application_status": "planned" if args.dry_run else "unverified",
        "worker_exit_status": "not_run" if args.dry_run else "unknown",
        "integration_status": "pending_main_review",
        "command": command,
        "command_display": " ".join(shlex.quote(part) for part in command),
        "artifacts": [],
        "warnings": [],
        "fallback_action": "none",
    }

    if args.dry_run:
        payload["fallback_action"] = fallback_action(args.phase, str(payload["application_status"]))
        write_result(Path(args.output_dir) if args.output_dir else None, run_id, payload)
        print(json.dumps(payload, ensure_ascii=False))
        return 0

    run_command = command
    if args.runner:
        run_command = [args.runner, json.dumps(command, ensure_ascii=False)]

    result = subprocess.run(run_command, text=True, capture_output=True, check=False, cwd=args.cwd or None)
    payload["worker_exit_status"] = "succeeded" if result.returncode == 0 else "failed"
    payload["runner_returncode"] = result.returncode
    payload["stdout_tail"] = result.stdout[-2000:]
    payload["stderr_tail"] = result.stderr[-2000:]

    if result.returncode != 0:
        payload["application_status"] = "unavailable"
        payload["warnings"] = ["worker command failed; requested model/effort was not proven applied"]
    else:
        observed = parse_observed_metadata(result.stdout)
        if observed:
            payload["applied_model"] = observed.get("applied_model", "unknown")
            payload["applied_effort"] = observed.get("applied_effort", "unknown")
            payload["application_status"] = "verified"
        else:
            payload["application_status"] = "unverified"
            payload["warnings"] = ["worker succeeded but applied model/effort metadata was not observed"]

    payload["fallback_action"] = fallback_action(args.phase, str(payload["application_status"]))
    write_result(Path(args.output_dir) if args.output_dir else None, run_id, payload)
    print(json.dumps(payload, ensure_ascii=False))
    return 0 if result.returncode == 0 else result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
