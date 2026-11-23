#!/usr/bin/env bash
set -euo pipefail
: "${ROOT:?}" "${PYTHON_BIN:?}"

echo "BLOCK: workflow-loop"
"$PYTHON_BIN" - "$ROOT" <<'PY'
import json
import os
import pathlib
import shlex
import subprocess
import sys
import tempfile

root = pathlib.Path(sys.argv[1])

with tempfile.TemporaryDirectory(prefix="validate-grade-") as tmp_root_raw:
    tmp_root = pathlib.Path(tmp_root_raw)
    workspace = tmp_root / "sample-iteration"
    eval_id = 101
    category = "entry"
    priority = "high"
    outputs = workspace / f"eval-{eval_id}" / "with_skill" / "run-1" / "outputs"
    outputs.mkdir(parents=True)
    evals_path = tmp_root / "fixture-evals.json"

    final_response = """entry intent は `ambiguous` です。
fail-closed で停止します。
`参照した正本`: `references/state-machine.md`
`停止理由`: `/gdd-dev` の引数が空で、新規開始か再開かを決められません。
`次の1アクション`: `新規開始` か `再開` を指定してください。
"""
    (outputs / "final_response.md").write_text(final_response, encoding="utf-8")
    (workspace / f"eval-{eval_id}" / "with_skill" / "run-1" / "transcript.md").write_text(
        final_response,
        encoding="utf-8",
    )
    evals_path.write_text(
        json.dumps(
            {
                "skill_name": "gate-driven-development",
                "evals": [
                    {
                        "id": eval_id,
                        "category": category,
                        "priority": priority,
                        "required": True,
                        "prompt": "fixture",
                        "expected_output": "fixture",
                        "files": [],
                        "expectations": [
                            "entry_intent_ambiguous",
                            "mentions_fail_closed",
                            "confirm_new_vs_resume",
                            "next_single_action_guidance",
                        ],
                    }
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    env = os.environ.copy()
    env["GDD_EVALS_TRUSTED_ROOT"] = str(tmp_root)
    result = subprocess.run(
        [
            sys.executable,
            str(root / "scripts" / "grade_evals.py"),
            str(workspace),
            "--evals-file",
            str(evals_path),
            "--eval-id",
            str(eval_id),
            "--present-only",
        ],
        env=env,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr, file=sys.stderr)
        raise SystemExit("grade_evals.py returned a non-zero exit code")

    grading = json.loads(
        (workspace / f"eval-{eval_id}" / "with_skill" / "run-1" / "grading.json").read_text(
            encoding="utf-8"
        )
    )
    summary = json.loads((workspace / "grading-summary.json").read_text(encoding="utf-8"))

    for key in ["eval_id", "category", "priority", "required"]:
        if key not in grading["eval_metadata"]:
            raise SystemExit(f"grading.json missing eval_metadata key: {key}")
    if grading["eval_metadata"]["eval_id"] != eval_id:
        raise SystemExit("grading.json eval_metadata.eval_id mismatch")
    if grading["eval_metadata"]["category"] != category:
        raise SystemExit("grading.json eval_metadata.category mismatch")
    if grading["eval_metadata"]["priority"] != priority:
        raise SystemExit("grading.json eval_metadata.priority mismatch")
    if grading["eval_metadata"]["required"] is not True:
        raise SystemExit("grading.json eval_metadata.required mismatch")
    if grading["summary"].get("run_passed") is not True:
        raise SystemExit("grading.json summary.run_passed must be true for the fixture")
    if not all(item.get("passed") is True for item in grading["expectations"]):
        raise SystemExit("grading.json expectations must all pass for the fixture")
    if not all(isinstance(item.get("id"), str) for item in grading["expectations"]):
        raise SystemExit("grading.json expectations must include string ids")
    if not all(isinstance(item.get("label"), str) for item in grading["expectations"]):
        raise SystemExit("grading.json expectations must include labels")

    for key in ["workspace", "overall", "by_category", "by_priority", "required_evals"]:
        if key not in summary:
            raise SystemExit(f"grading-summary.json missing key: {key}")
    for key in ["runs", "passed_runs", "failed_runs", "run_pass_rate", "expectation_pass_rate"]:
        if key not in summary["overall"]:
            raise SystemExit(f"grading-summary.json overall missing key: {key}")
    if summary["overall"]["runs"] != 1:
        raise SystemExit("grading-summary.json overall.runs is unexpected")
    if summary["overall"]["passed_runs"] + summary["overall"]["failed_runs"] != summary["overall"]["runs"]:
        raise SystemExit("grading-summary.json overall run counts are inconsistent")
    for key in ["run_pass_rate", "expectation_pass_rate"]:
        value = summary["overall"][key]
        if not isinstance(value, (int, float)) or not 0 <= value <= 1:
            raise SystemExit(f"grading-summary.json overall.{key} must be a rate between 0 and 1")
    if category not in summary["by_category"]:
        raise SystemExit("grading-summary.json missing category summary")
    if summary["required_evals"]["runs"] != 1:
        raise SystemExit("grading-summary.json required_evals summary is unexpected")
    if summary["required_evals"]["passed_runs"] != 1 or summary["required_evals"]["failed_runs"] != 0:
        raise SystemExit("grading-summary.json required_evals pass/fail counts are unexpected")
PY

"$PYTHON_BIN" - "$ROOT" <<'PY'
import json
import os
import pathlib
import subprocess
import sys

root = pathlib.Path(sys.argv[1])
hooks_path = root / "hooks" / "hooks.json"
hook_runner = root / "hooks" / "scripts" / "run-steering-write-hook.sh"

hooks_data = json.loads(hooks_path.read_text(encoding="utf-8"))
if "hooks" not in hooks_data or not isinstance(hooks_data["hooks"], dict):
    raise SystemExit("hooks/hooks.json must use the plugin wrapper format")

pre_tool_use = hooks_data["hooks"].get("PreToolUse")
if not isinstance(pre_tool_use, list) or not pre_tool_use:
    raise SystemExit("hooks/hooks.json missing PreToolUse configuration")

stop_hooks = hooks_data["hooks"].get("Stop")
if not isinstance(stop_hooks, list) or not stop_hooks:
    raise SystemExit("hooks/hooks.json missing Stop configuration")

expected_pre_tool_use_hooks = [
    "run-steering-write-hook.sh",
    "run-pre-tool-use-plan-reread-hook.sh",
]
if len(pre_tool_use) < len(expected_pre_tool_use_hooks):
    raise SystemExit(
        f"hooks/hooks.json PreToolUse has {len(pre_tool_use)} entries, "
        f"expected at least {len(expected_pre_tool_use_hooks)}"
    )
for i, expected_script in enumerate(expected_pre_tool_use_hooks):
    hook_entry = pre_tool_use[i]
    if hook_entry.get("matcher") != "Write|Edit|MultiEdit|ApplyPatch":
        raise SystemExit(f"hooks/hooks.json PreToolUse[{i}] matcher is unexpected")
    command_hooks = hook_entry.get("hooks")
    if not isinstance(command_hooks, list) or not command_hooks:
        raise SystemExit(f"hooks/hooks.json PreToolUse[{i}] must contain command hooks")
    command = command_hooks[0]
    if command.get("type") != "command":
        raise SystemExit(f"hooks/hooks.json PreToolUse[{i}] must use a command hook")
    if expected_script not in command.get("command", ""):
        raise SystemExit(f"hooks/hooks.json PreToolUse[{i}] must reference {expected_script}")

stop_command_hooks = stop_hooks[0].get("hooks")
if not isinstance(stop_command_hooks, list) or not stop_command_hooks:
    raise SystemExit("hooks/hooks.json Stop must contain command hooks")
if stop_hooks[0].get("matcher") != "*":
    raise SystemExit('hooks/hooks.json Stop matcher must be "*"')
stop_command = stop_command_hooks[0]
if stop_command.get("type") != "command":
    raise SystemExit("hooks/hooks.json Stop must use a command hook")
if "run-gdd-stop-hook.sh" not in stop_command.get("command", ""):
    raise SystemExit("hooks/hooks.json must reference run-gdd-stop-hook.sh")

# Runtime hook smoke tests are intentionally omitted here; the hook scripts are
# covered by syntax checks and direct resolver tests above.
PY

echo "VERDICT: workflow-loop: OK"
