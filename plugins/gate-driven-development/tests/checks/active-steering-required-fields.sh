#!/usr/bin/env bash
set -euo pipefail
: "${ROOT:?}" "${PYTHON_BIN:?}"

echo "BLOCK: active-steering-required-fields"
"$PYTHON_BIN" - "$ROOT" <<'PY'
import json
import os
import pathlib
import subprocess
import sys
import tempfile

root = pathlib.Path(sys.argv[1])
session_start_hook = root / "hooks" / "scripts" / "run-session-start-hook.sh"
user_prompt_hook = root / "hooks" / "scripts" / "run-user-prompt-submit-hook.sh"
if "gdd-post-merge-continuation.json" not in user_prompt_hook.read_text(encoding="utf-8"):
    raise SystemExit("run-user-prompt-submit-hook.sh must inject manual merge continuation context")

with tempfile.TemporaryDirectory(prefix="validate-active-steering-fields-") as tmp_dir_raw:
    repo = pathlib.Path(tmp_dir_raw)
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)

    steering = repo / ".steering" / "20260506-active-steering"
    steering.mkdir(parents=True)

    # Test A: state.md missing Human Check Status -> session-start should fail-closed
    (steering / "state.md").write_text(
        "# State\n\n"
        "## Gate Status\n"
        "- Requirements Review Status=approved | evidence: req\n"
        "- Design Review Status=approved | evidence: des\n"
        "- Resume From=gdd-design-gating\n"
        "- Route In Progress=none\n",
        encoding="utf-8",
    )
    (steering / "tasklist.md").write_text(
        "# Task List\n\n"
        "## Current Task\n"
        "- なし\n\n"
        "## Pending Tasks\n"
        "- なし\n\n"
        "## Completed Tasks\n"
        "- なし\n",
        encoding="utf-8",
    )

    result_a = subprocess.run(
        ["bash", str(session_start_hook)],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    )
    payload_a = json.loads(result_a.stdout)
    additional_a = payload_a["hookSpecificOutput"]["additionalContext"]
    if "[gdd:blocked]" not in additional_a:
        raise SystemExit("session-start should emit [gdd:blocked] when Human Check Status is missing")
    if "Human Check Status" not in additional_a:
        raise SystemExit("session-start block reason should mention missing Human Check Status")
    if "state.md" not in additional_a:
        raise SystemExit("session-start block reason should mention state.md as canonical source")

    # Test B: canonical tasklist missing Next Action -> user-prompt should fail-closed
    (steering / "state.md").write_text(
        "# State\n\n"
        "## Gate Status\n"
        "- Requirements Review Status=approved | evidence: req\n"
        "- Design Review Status=approved | evidence: des\n"
        "- Human Check Status=approved | evidence: hc\n"
        "- Resume From=gdd-test-driven-development\n"
        "- Route In Progress=none\n",
        encoding="utf-8",
    )
    (steering / "tasklist.md").write_text(
        "# Task List\n\n"
        "## Current Task\n"
        "### Task: T-1 | AC-01 | add validator\n\n"
        "## Pending Tasks\n"
        "- なし\n\n"
        "## Completed Tasks\n"
        "- なし\n",
        encoding="utf-8",
    )

    (repo / ".claude").mkdir(exist_ok=True)
    (repo / ".claude" / "gdd-dev.local.md").write_text("---\nactive: true\n---\n", encoding="utf-8")
    result_b = subprocess.run(
        ["bash", str(user_prompt_hook)],
        cwd=repo,
        # 毎ターンの注入は GDD の印（active な marker）があるときだけになる。印は下で置き、
        # session id の無いランタイムとして回す（手元のセッションの id を引き継がない）
        env={k: v for k, v in os.environ.items() if k != "CLAUDE_CODE_SESSION_ID"},
        input=json.dumps({"prompt": "続けて"}),
        capture_output=True,
        text=True,
        check=True,
    )
    payload_b = json.loads(result_b.stdout)
    additional_b = payload_b["hookSpecificOutput"]["additionalContext"]
    if "[gdd:blocked]" not in additional_b:
        raise SystemExit("user-prompt should emit [gdd:blocked] when canonical tasklist misses Next Action")
    if "Next Action" not in additional_b:
        raise SystemExit("user-prompt block reason should mention missing Next Action")
    if "tasklist.md" not in additional_b:
        raise SystemExit("user-prompt block reason should mention tasklist.md as canonical source")

print("OK")
PY

echo "VERDICT: active-steering-required-fields: OK"
