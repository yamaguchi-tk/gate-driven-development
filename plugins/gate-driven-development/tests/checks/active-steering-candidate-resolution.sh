#!/usr/bin/env bash
set -euo pipefail
: "${ROOT:?}" "${PYTHON_BIN:?}"

echo "BLOCK: active-steering-candidate-resolution"
"$PYTHON_BIN" - "$ROOT" <<'PY'
import json
import os
import pathlib
import subprocess
import sys
import tempfile

root = pathlib.Path(sys.argv[1])
session_start_hook = root / "hooks" / "scripts" / "run-session-start-hook.sh"

with tempfile.TemporaryDirectory(prefix="validate-active-steering-resolution-") as tmp_dir_raw:
    repo = pathlib.Path(tmp_dir_raw)
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)

    def write_state(dirname: str, started_at: str) -> None:
        steering = repo / ".steering" / dirname
        steering.mkdir(parents=True, exist_ok=True)
        (steering / "state.md").write_text(
            "# State\n\n"
            "## Metadata\n"
            f"- Started At: {started_at}\n\n"
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
            "### Task: T-1 | AC-01 | continue\n\n"
            "## Pending Tasks\n"
            "- なし\n\n"
            "## Completed Tasks\n"
            "- なし\n\n"
            "## Review Status\n"
            "- `Next Action=gdd-test-driven-development`\n",
            encoding="utf-8",
        )

    write_state("20260501-older-active", "2026-05-01T00:00:00Z")
    write_state("20260506-newer-active", "2026-05-06T00:00:00Z")

    stale = repo / ".steering" / "20200101-abandoned-brainstorming"
    stale.mkdir(parents=True, exist_ok=True)
    (stale / "state.md").write_text(
        "# State\n\n"
        "## Metadata\n"
        "- Started At: 2020-01-01T00:00:00Z\n\n"
        "## Gate Status\n"
        "- Requirements Review Status=pending | evidence: none\n"
        "- Design Review Status=pending | evidence: none\n"
        "- Human Check Status=pending | evidence: none\n"
        "- Resume From=gdd-brainstorming\n"
        "- Route In Progress=none\n",
        encoding="utf-8",
    )

    legacy = repo / ".steering" / "20260401-design-only"
    legacy.mkdir(parents=True, exist_ok=True)
    (legacy / "design.md").write_text("# legacy only\n", encoding="utf-8")

    (repo / ".claude").mkdir(exist_ok=True)
    (repo / ".claude" / "gdd-dev.local.md").write_text(
        "---\nactive: true\nsession_id: same-session\n---\n",
        encoding="utf-8",
    )
    result = subprocess.run(
        ["bash", str(session_start_hook)],
        cwd=repo,
        env={**os.environ, "CLAUDE_CODE_SESSION_ID": "same-session"},
        capture_output=True,
        text=True,
        check=True,
    )
    payload = json.loads(result.stdout)
    additional = payload["hookSpecificOutput"]["additionalContext"]
    if "[gdd:warning]" not in additional:
        raise SystemExit("session-start should warn about multiple steering candidates (A-3: tie-break removed, always fail-closed to multiple)")
    if "20260506-newer-active" not in additional:
        raise SystemExit("session-start should list every non-terminal candidate in the multiple warning, including the newer one")
    if "20260501-older-active" not in additional:
        raise SystemExit("session-start should list every non-terminal candidate in the multiple warning, including the older one")
    if "20260401-design-only" in additional:
        raise SystemExit("design-only legacy artifact should not be considered an active steering candidate")
    if "20200101-abandoned-brainstorming" in additional:
        raise SystemExit("stale brainstorming candidate should be excluded from active steering resolution")

    # Test C: stale brainstorming candidate must not hijack selection when the
    # only live candidate lacks Started At metadata.
    repo2 = pathlib.Path(tmp_dir_raw) / "stale-precedence"
    repo2.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-q"], cwd=repo2, check=True)
    active2 = repo2 / ".steering" / "20260506-live-without-started-at"
    active2.mkdir(parents=True, exist_ok=True)
    (active2 / "state.md").write_text(
        "# State\n\n"
        "## Gate Status\n"
        "- Requirements Review Status=approved | evidence: req\n"
        "- Design Review Status=approved | evidence: des\n"
        "- Human Check Status=approved | evidence: hc\n"
        "- Resume From=gdd-test-driven-development\n"
        "- Route In Progress=none\n",
        encoding="utf-8",
    )
    (active2 / "tasklist.md").write_text(
        "# Task List\n\n"
        "## Current Task\n"
        "### Task: T-1 | AC-01 | continue\n\n"
        "## Pending Tasks\n"
        "- なし\n\n"
        "## Completed Tasks\n"
        "- なし\n\n"
        "## Review Status\n"
        "- `Next Action=gdd-test-driven-development`\n",
        encoding="utf-8",
    )
    stale2 = repo2 / ".steering" / "20200101-old-brainstorming"
    stale2.mkdir(parents=True, exist_ok=True)
    (stale2 / "state.md").write_text(
        "# State\n\n"
        "## Metadata\n"
        "- Started At: 2020-01-01T00:00:00Z\n\n"
        "## Gate Status\n"
        "- Requirements Review Status=pending | evidence: none\n"
        "- Design Review Status=pending | evidence: none\n"
        "- Human Check Status=pending | evidence: none\n"
        "- Resume From=gdd-brainstorming\n"
        "- Route In Progress=none\n",
        encoding="utf-8",
    )
    (repo2 / ".claude").mkdir(exist_ok=True)
    (repo2 / ".claude" / "gdd-dev.local.md").write_text(
        "---\nactive: true\nsession_id: same-session\n---\n",
        encoding="utf-8",
    )
    result_c = subprocess.run(
        ["bash", str(session_start_hook)],
        cwd=repo2,
        env={**os.environ, "CLAUDE_CODE_SESSION_ID": "same-session"},
        capture_output=True,
        text=True,
        check=True,
    )
    payload_c = json.loads(result_c.stdout)
    additional_c = payload_c["hookSpecificOutput"]["additionalContext"]
    if "20200101-old-brainstorming" in additional_c:
        raise SystemExit("stale brainstorming candidate should not win over a live candidate without Started At")
    if "20260506-live-without-started-at" not in additional_c:
        raise SystemExit("live candidate without Started At should remain selectable after stale exclusion")

print("OK")
PY

"$PYTHON_BIN" - "$ROOT" <<'PY'
import json
import os
import pathlib
import shlex
import sys
import tempfile

root = pathlib.Path(sys.argv[1])
setup_script = root / "scripts" / "setup-gdd-loop.sh"
stop_hook = root / "hooks" / "scripts" / "run-gdd-stop-hook.sh"

with tempfile.TemporaryDirectory(prefix="validate-workflow-loop-") as tmp_dir_raw:
    tmp_dir = pathlib.Path(tmp_dir_raw)
    state_file = tmp_dir / ".claude" / "gdd-dev.local.md"
    transcript_path = tmp_dir / "transcript.jsonl"
    setup_stdout = tmp_dir / "setup.stdout"
    stop_stdout = tmp_dir / "stop.stdout"
    hook_input_path = tmp_dir / "hook-input.json"
    session_id = "test-session-123"

    setup_command = " ".join(
        [
            "cd",
            shlex.quote(str(tmp_dir)),
            "&&",
            "CLAUDE_CODE_SESSION_ID=" + shlex.quote(session_id),
            "bash",
            shlex.quote(str(setup_script)),
            "Fix",
            "the",
            "workflow",
            "loop",
            ">",
            shlex.quote(str(setup_stdout)),
            "2>&1",
        ]
    )
    if os.system(setup_command) != 0:
        raise SystemExit("setup-gdd-loop.sh failed")
    if "gdd-dev.local.md" not in setup_stdout.read_text(encoding="utf-8"):
        raise SystemExit("setup-gdd-loop.sh should mention the state file")
    if not state_file.exists():
        raise SystemExit("setup-gdd-loop.sh did not create the state file")

    state_text = state_file.read_text(encoding="utf-8")
    for token in [
        "active: true",
        "iteration: 1",
        f"session_id: {session_id}",
        "gdd-stop",
        "human-check-waiting",
        "User intent:",
    ]:
        if token not in state_text:
            raise SystemExit(f"setup-gdd-loop.sh state file missing token: {token}")

    # Include a user turn with explicit GDD intent so looks_like_gdd_continuation()
    # recognises the workflow is in progress and injects a continuation block.
    transcript_path.write_text(
        json.dumps(
            {
                "type": "user",
                "message": {
                    "content": [
                        {
                            "type": "text",
                            "text": "/gdd-dev Fix the workflow loop",
                        }
                    ]
                },
            },
            ensure_ascii=False,
        )
        + "\n"
        + json.dumps(
            {
                "type": "assistant",
                "message": {
                    "content": [
                        {
                            "type": "text",
                            "text": "現在 state を要約します。まだ stop marker は出していません。",
                        }
                    ]
                },
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    hook_input = json.dumps(
        {
            "session_id": session_id,
            "transcript_path": str(transcript_path),
        }
    )
    hook_input_path.write_text(hook_input, encoding="utf-8")
    stop_command = " ".join(
        [
            "cd",
            shlex.quote(str(tmp_dir)),
            "&&",
            "CLAUDE_CODE_SESSION_ID=" + shlex.quote(session_id),
            "bash",
            shlex.quote(str(stop_hook)),
            "<",
            shlex.quote(str(hook_input_path)),
            ">",
            shlex.quote(str(stop_stdout)),
            "2>&1",
        ]
    )
    if os.system(stop_command) != 0:
        raise SystemExit("run-gdd-stop-hook.sh failed")
    payload = json.loads(stop_stdout.read_text(encoding="utf-8"))
    if payload.get("decision") != "block":
        raise SystemExit("GDD Stop hook should block when no stop marker is present")
    if "Continue the active `/gdd-dev` run." not in payload.get("reason", ""):
        raise SystemExit("GDD Stop hook should feed the continuation prompt back")
    if "[GDD #2]" not in payload.get("systemMessage", ""):
        raise SystemExit("GDD Stop hook should update the iteration count")
    if "iteration: 2" not in state_file.read_text(encoding="utf-8"):
        raise SystemExit("GDD Stop hook should persist the incremented iteration")

    transcript_path.write_text(
        json.dumps(
            {
                "type": "assistant",
                "message": {
                    "content": [
                        {
                            "type": "text",
                            "text": '<gdd-stop reason="human-check-waiting">human approval required</gdd-stop>',
                        }
                    ]
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )

    hook_input_path.write_text(hook_input, encoding="utf-8")
    if os.system(stop_command) != 0:
        raise SystemExit("run-gdd-stop-hook.sh failed")
    # human-check-waiting is a pause point, not a terminal state.
    # state.md should be PRESERVED so the session can resume.
    if not state_file.exists():
        raise SystemExit("GDD Stop hook should PRESERVE state file on human-check-waiting (pause point)")

    # Clean up state file for subsequent done-guard tests
    state_file.unlink(missing_ok=True)

    # --- Done guard tests: structural guarantee against incomplete done ---

    # Test A: done with remaining tasks -> BLOCK
    state_file.parent.mkdir(parents=True, exist_ok=True)
    state_file.write_text(
        f"---\nactive: true\niteration: 1\nsession_id: {session_id}\n---\n\n"
        "Continue the active `/gdd-dev` run.\n",
        encoding="utf-8",
    )

    steering = tmp_dir / ".steering" / "20260414-test"
    steering.mkdir(parents=True, exist_ok=True)
    # Route In Progress は Tier 1 必須。行が無い state.md は done guard Check 3 が block する（Issue #119）
    (steering / "state.md").write_text(
        "---\nResume From: gdd-completion-check\nRoute In Progress=none\n---\n",
        encoding="utf-8",
    )
    # bind 限定の変更以降、done guard の検査対象は **この worktree に bind された steering だけ**。
    # binding.json が無いと unbound 扱いになり、block ではなく warn へ降格する
    # （旧実装は他 worktree を漁って誤 block していた）。
    # done guard の検査ロジックそのものを測る以降のテストは bind 済みを前提にする。
    binding_dir = tmp_dir / ".gdd" / "tasks" / "20260414-test"
    binding_dir.mkdir(parents=True, exist_ok=True)
    (binding_dir / "binding.json").write_text(
        json.dumps(
            {
                "task_id": "20260414-test",
                "worktree_path": str(tmp_dir.resolve()),
                "steering_path": str(steering.resolve()),
                "branch": "",
            }
        ),
        encoding="utf-8",
    )
    (steering / "tasklist.md").write_text(
        "## Current Task\n\n- なし\n\n"
        "## Pending Tasks\n\n### Task: T-2 | AC-02 | remaining work\n\nDo something\n\n"
        "## Completed Tasks\n\n### Task: T-1 | AC-01 | done work\n\nDone\n\n"
        "## Verification\n\n"
        "| method | status | evidence | notes |\n"
        "|---|---|---|---|\n"
        "| method=ac:AC-01 | pass | evidence | notes |\n\n"
        "## Status\n\n`Next Action=done`\n",
        encoding="utf-8",
    )

    transcript_path.write_text(
        json.dumps(
            {
                "type": "assistant",
                "message": {
                    "content": [
                        {
                            "type": "text",
                            "text": '<gdd-stop reason="done">all done</gdd-stop>\n\n## 👤 次にすること\n完了（追加対応なし）',
                        }
                    ]
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )

    hook_input_path.write_text(
        json.dumps({"session_id": session_id, "transcript_path": str(transcript_path)}),
        encoding="utf-8",
    )
    if os.system(stop_command) != 0:
        raise SystemExit("done-guard test A: stop hook failed")
    payload_a = json.loads(stop_stdout.read_text(encoding="utf-8"))
    if payload_a.get("decision") != "block":
        raise SystemExit("done-guard test A: should BLOCK when Pending Tasks remain")
    if "未完了タスク" not in payload_a.get("reason", ""):
        raise SystemExit("done-guard test A: block reason should mention remaining tasks")

    # Test B: done with all tasks completed and verification pass -> ALLOW
    state_file.write_text(
        f"---\nactive: true\niteration: 1\nsession_id: {session_id}\n---\n\n"
        "Continue the active `/gdd-dev` run.\n",
        encoding="utf-8",
    )
    (steering / "tasklist.md").write_text(
        "## Current Task\n\n- なし\n\n"
        "## Pending Tasks\n\n- なし\n\n"
        "## Completed Tasks\n\n### Task: T-1 | AC-01 | done work\n\nDone\n\n"
        "## Verification\n\n"
        "| method | status | evidence | notes |\n"
        "|---|---|---|---|\n"
        "| method=ac:AC-01 | pass | evidence | notes |\n\n"
        "## Status\n\n`Next Action=done`\n",
        encoding="utf-8",
    )

    hook_input_path.write_text(
        json.dumps({"session_id": session_id, "transcript_path": str(transcript_path)}),
        encoding="utf-8",
    )
    if os.system(stop_command) != 0:
        raise SystemExit("done-guard test B: stop hook failed")
    stdout_b = stop_stdout.read_text(encoding="utf-8").strip()
    if stdout_b:
        try:
            payload_b = json.loads(stdout_b)
            if payload_b.get("decision") == "block":
                raise SystemExit(
                    "done-guard test B: should ALLOW when all tasks complete, got block: "
                    + payload_b.get("reason", "")[:200]
                )
        except json.JSONDecodeError:
            pass
    if state_file.exists():
        raise SystemExit("done-guard test B: state file should be removed on allowed done")

    # Test C: done with Verification fail -> BLOCK
    state_file.write_text(
        f"---\nactive: true\niteration: 1\nsession_id: {session_id}\n---\n\n"
        "Continue the active `/gdd-dev` run.\n",
        encoding="utf-8",
    )
    (steering / "tasklist.md").write_text(
        "## Current Task\n\n- なし\n\n"
        "## Pending Tasks\n\n- なし\n\n"
        "## Completed Tasks\n\n### Task: T-1 | AC-01 | done work\n\nDone\n\n"
        "## Verification\n\n"
        "| method | status | evidence | notes |\n"
        "|---|---|---|---|\n"
        "| method=ac:AC-01 | fail | test failed | needs fix |\n\n"
        "## Status\n\n`Next Action=done`\n",
        encoding="utf-8",
    )

    hook_input_path.write_text(
        json.dumps({"session_id": session_id, "transcript_path": str(transcript_path)}),
        encoding="utf-8",
    )
    if os.system(stop_command) != 0:
        raise SystemExit("done-guard test C: stop hook failed")
    payload_c = json.loads(stop_stdout.read_text(encoding="utf-8"))
    if payload_c.get("decision") != "block":
        raise SystemExit("done-guard test C: should BLOCK when Verification has fail")
    if "未完了/失敗" not in payload_c.get("reason", ""):
        raise SystemExit("done-guard test C: block reason should mention verification failure")

    # Test D: done with Verification pending in table format -> BLOCK
    state_file.write_text(
        f"---\nactive: true\niteration: 1\nsession_id: {session_id}\n---\n\n"
        "Continue the active `/gdd-dev` run.\n",
        encoding="utf-8",
    )
    (steering / "tasklist.md").write_text(
        "## Current Task\n\n- なし\n\n"
        "## Pending Tasks\n\n- なし\n\n"
        "## Completed Tasks\n\n### Task: T-1 | AC-01 | done work\n\nDone\n\n"
        "## Verification\n\n"
        "| method | status | evidence | notes |\n"
        "|---|---|---|---|\n"
        "| method=ac:AC-01 | pending | not yet | needs run |\n\n"
        "## Status\n\n`Next Action=done`\n",
        encoding="utf-8",
    )

    hook_input_path.write_text(
        json.dumps({"session_id": session_id, "transcript_path": str(transcript_path)}),
        encoding="utf-8",
    )
    if os.system(stop_command) != 0:
        raise SystemExit("done-guard test D: stop hook failed")
    payload_d = json.loads(stop_stdout.read_text(encoding="utf-8"))
    if payload_d.get("decision") != "block":
        raise SystemExit("done-guard test D: should BLOCK when Verification table has pending")
    if "未完了/失敗" not in payload_d.get("reason", ""):
        raise SystemExit("done-guard test D: block reason should mention verification failure")

    # Test E: done with missing Verification section -> BLOCK
    state_file.write_text(
        f"---\nactive: true\niteration: 1\nsession_id: {session_id}\n---\n\n"
        "Continue the active `/gdd-dev` run.\n",
        encoding="utf-8",
    )
    (steering / "state.md").write_text(
        "---\nResume From: gdd-completion-check\n---\n",
        encoding="utf-8",
    )
    (steering / "tasklist.md").write_text(
        "## Current Task\n\n- なし\n\n"
        "## Pending Tasks\n\n- なし\n\n"
        "## Completed Tasks\n\n### Task: T-1 | AC-01 | done work\n\nDone\n\n"
        "---\n\n`Next Action=done`\n",
        encoding="utf-8",
    )

    hook_input_path.write_text(
        json.dumps({"session_id": session_id, "transcript_path": str(transcript_path)}),
        encoding="utf-8",
    )
    if os.system(stop_command) != 0:
        raise SystemExit("done-guard test E: stop hook failed")
    payload_e = json.loads(stop_stdout.read_text(encoding="utf-8"))
    if payload_e.get("decision") != "block":
        raise SystemExit("done-guard test E: should BLOCK when Verification section is missing")
    if "Verification セクションが存在しません" not in payload_e.get("reason", ""):
        raise SystemExit("done-guard test E: block reason should mention missing Verification")

    # Test F: done with empty Verification section (only header + schema) -> BLOCK
    state_file.write_text(
        f"---\nactive: true\niteration: 1\nsession_id: {session_id}\n---\n\n"
        "Continue the active `/gdd-dev` run.\n",
        encoding="utf-8",
    )
    (steering / "tasklist.md").write_text(
        "## Current Task\n\n- なし\n\n"
        "## Pending Tasks\n\n- なし\n\n"
        "## Completed Tasks\n\n### Task: T-1 | AC-01 | done work\n\nDone\n\n"
        "## Verification\n\n"
        "| method | status | evidence | notes |\n"
        "|---|---|---|---|\n\n"
        "## Status\n\n`Next Action=done`\n",
        encoding="utf-8",
    )

    hook_input_path.write_text(
        json.dumps({"session_id": session_id, "transcript_path": str(transcript_path)}),
        encoding="utf-8",
    )
    if os.system(stop_command) != 0:
        raise SystemExit("done-guard test F: stop hook failed")
    payload_f = json.loads(stop_stdout.read_text(encoding="utf-8"))
    if payload_f.get("decision") != "block":
        raise SystemExit("done-guard test F: should BLOCK when Verification has no data rows")
    if "検証行がありません" not in payload_f.get("reason", ""):
        raise SystemExit("done-guard test F: block reason should mention empty verification")

    # Test G: done with non-standard content in Current Task -> BLOCK
    state_file.write_text(
        f"---\nactive: true\niteration: 1\nsession_id: {session_id}\n---\n\n"
        "Continue the active `/gdd-dev` run.\n",
        encoding="utf-8",
    )
    (steering / "tasklist.md").write_text(
        "## Current Task\n\n- 作業中のタスクあり\n\n"
        "## Pending Tasks\n\n- なし\n\n"
        "## Completed Tasks\n\n### Task: T-1 | AC-01 | done work\n\nDone\n\n"
        "## Verification\n\n"
        "| method | status | evidence | notes |\n"
        "|---|---|---|---|\n"
        "| method=ac:AC-01 | pass | evidence | notes |\n\n"
        "## Status\n\n`Next Action=done`\n",
        encoding="utf-8",
    )

    hook_input_path.write_text(
        json.dumps({"session_id": session_id, "transcript_path": str(transcript_path)}),
        encoding="utf-8",
    )
    if os.system(stop_command) != 0:
        raise SystemExit("done-guard test G: stop hook failed")
    payload_g = json.loads(stop_stdout.read_text(encoding="utf-8"))
    if payload_g.get("decision") != "block":
        raise SystemExit("done-guard test G: should BLOCK when Current Task has non-standard content")
    if "非標準の内容" not in payload_g.get("reason", ""):
        raise SystemExit("done-guard test G: block reason should mention non-standard content")

    # Test H: done with Route In Progress != none -> BLOCK
    state_file.write_text(
        f"---\nactive: true\niteration: 1\nsession_id: {session_id}\n---\n\n"
        "Continue the active `/gdd-dev` run.\n",
        encoding="utf-8",
    )
    (steering / "state.md").write_text(
        "---\nResume From: gdd-completion-check\nRoute In Progress=design_detail_only\n---\n",
        encoding="utf-8",
    )
    (steering / "tasklist.md").write_text(
        "## Current Task\n\n- なし\n\n"
        "## Pending Tasks\n\n- なし\n\n"
        "## Completed Tasks\n\n### Task: T-1 | AC-01 | done work\n\nDone\n\n"
        "## Verification\n\n"
        "| method | status | evidence | notes |\n"
        "|---|---|---|---|\n"
        "| method=ac:AC-01 | pass | evidence | notes |\n\n"
        "## Status\n\n`Next Action=done`\n",
        encoding="utf-8",
    )

    hook_input_path.write_text(
        json.dumps({"session_id": session_id, "transcript_path": str(transcript_path)}),
        encoding="utf-8",
    )
    if os.system(stop_command) != 0:
        raise SystemExit("done-guard test H: stop hook failed")
    payload_h = json.loads(stop_stdout.read_text(encoding="utf-8"))
    if payload_h.get("decision") != "block":
        raise SystemExit("done-guard test H: should BLOCK when Route In Progress is not none")
    if "Route In Progress" not in payload_h.get("reason", ""):
        raise SystemExit("done-guard test H: block reason should mention Route In Progress")

    # Test H2: done guard validation error -> BLOCK (fail-closed)
    state_file.write_text(
        f"---\nactive: true\niteration: 1\nsession_id: {session_id}\n---\n\n"
        "Continue the active `/gdd-dev` run.\n",
        encoding="utf-8",
    )
    (steering / "state.md").write_text(
        "---\nResume From: gdd-completion-check\nRoute In Progress=none\n---\n",
        encoding="utf-8",
    )
    # Invalid UTF-8 forces tasklist.md read_text() to raise. This must not
    # allow done, because verification evidence could not be inspected.
    (steering / "tasklist.md").write_bytes(b"\xff\xfe\x00\x00")
    transcript_path.write_text(
        json.dumps(
            {
                "type": "assistant",
                "message": {
                    "content": [
                        {
                            "type": "text",
                            "text": '<gdd-stop reason="done">all done</gdd-stop>\n\n## 👤 次にすること\n完了（追加対応なし）',
                        }
                    ]
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )
    hook_input_path.write_text(
        json.dumps({"session_id": session_id, "transcript_path": str(transcript_path)}),
        encoding="utf-8",
    )
    if os.system(stop_command) != 0:
        raise SystemExit("done-guard test H2: stop hook failed")
    payload_h2 = json.loads(stop_stdout.read_text(encoding="utf-8"))
    if payload_h2.get("decision") != "block":
        raise SystemExit("done-guard test H2: should BLOCK when done guard validation errors")
    if "done guard の検証中にエラー" not in payload_h2.get("reason", ""):
        raise SystemExit("done-guard test H2: block reason should mention validation error")
    if not state_file.exists():
        raise SystemExit("done-guard test H2: state file should be preserved on validation error")

    # Test I: human-check-waiting should preserve state.md (not delete it)
    state_file.write_text(
        f"---\nactive: true\niteration: 3\nsession_id: {session_id}\n---\n\n"
        "Continue the active `/gdd-dev` run.\n",
        encoding="utf-8",
    )
    transcript_path.write_text(
        json.dumps(
            {
                "type": "assistant",
                "message": {
                    "content": [
                        {
                            "type": "text",
                            "text": '<gdd-stop reason="human-check-waiting">waiting for approval</gdd-stop>',
                        }
                    ]
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )
    hook_input_path.write_text(
        json.dumps({"session_id": session_id, "transcript_path": str(transcript_path)}),
        encoding="utf-8",
    )
    if os.system(stop_command) != 0:
        raise SystemExit("done-guard test I: stop hook failed")
    if not state_file.exists():
        raise SystemExit("done-guard test I: state file should be PRESERVED on human-check-waiting")
    # Verify iteration counter is intact
    preserved = state_file.read_text(encoding="utf-8")
    if "iteration: 3" not in preserved:
        raise SystemExit("done-guard test I: iteration counter should be preserved in state.md")

    # Test J: task body text in Completed Tasks should NOT trigger false positive
    # Regression: ensure body text under ### Task: in Completed Tasks doesn't leak
    # into unexpected_content detection (only Current/Pending are checked).
    # Also tests that Completed Tasks' task body doesn't cause issues.
    state_file.write_text(
        f"---\nactive: true\niteration: 1\nsession_id: {session_id}\n---\n\n"
        "Continue the active `/gdd-dev` run.\n",
        encoding="utf-8",
    )
    (steering / "state.md").write_text(
        "---\nResume From: gdd-completion-check\nRoute In Progress=none\n---\n",
        encoding="utf-8",
    )
    (steering / "tasklist.md").write_text(
        "## Current Task\n\n- なし\n\n"
        "## Pending Tasks\n\n- なし\n\n"
        "## Completed Tasks\n\n"
        "### Task: T-1 | AC-01 | implement feature\n\n"
        "Write code to implement X.\n"
        "Use the following approach:\n"
        "- Step 1: do something\n"
        "- Step 2: do something else\n\n"
        "### Task: T-2 | AC-02 | add tests\n\n"
        "Write tests for the feature.\n\n"
        "## Verification\n\n"
        "| method | status | evidence | notes |\n"
        "|---|---|---|---|\n"
        "| method=ac:AC-01 | pass | all tests green | verified |\n"
        "| method=ac:AC-02 | pass | coverage ok | verified |\n\n"
        "## Status\n\n`Next Action=done`\n",
        encoding="utf-8",
    )

    hook_input_path.write_text(
        json.dumps({"session_id": session_id, "transcript_path": str(transcript_path)}),
        encoding="utf-8",
    )
    # Restore done transcript
    transcript_path.write_text(
        json.dumps(
            {
                "type": "assistant",
                "message": {
                    "content": [
                        {
                            "type": "text",
                            "text": '<gdd-stop reason="done">all done</gdd-stop>\n\n## 👤 次にすること\n完了（追加対応なし）',
                        }
                    ]
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )
    if os.system(stop_command) != 0:
        raise SystemExit("done-guard test J: stop hook failed")
    stdout_j = stop_stdout.read_text(encoding="utf-8").strip()
    if stdout_j:
        try:
            payload_j = json.loads(stdout_j)
            if payload_j.get("decision") == "block":
                raise SystemExit(
                    "done-guard test J: should ALLOW (task body in Completed shouldn't trigger), got block: "
                    + payload_j.get("reason", "")[:200]
                )
        except json.JSONDecodeError:
            pass

    print("OK: done-guard tests passed (A=block-remaining, B=allow-complete, C=block-verification-list, D=block-verification-table, E=block-no-verification, F=block-empty-verification, G=block-nonstandard-task, H=block-route-in-progress, H2=block-validation-error, I=preserve-state-human-check, J=allow-body-text-no-false-positive)")
PY

for script in \
  "$ROOT/hooks/scripts/run-gdd-stop-hook.sh" \
  "$ROOT/hooks/scripts/run-steering-write-hook.sh" \
  "$ROOT/scripts/setup-gdd-loop.sh" \
  "$ROOT/scripts/install-cursor-links.sh" \
  "$ROOT/scripts/uninstall-cursor-links.sh"
do
  bash -n "$script"
done

TMP_DIR="$(mktemp -d)"
# assertion 失敗時（set -e で即終了する）にも temp を残さない。
# 後段で作る temp も含めて最初の mktemp 直後に登録する（未定義の間は空に展開される）。
trap 'rm -rf "${TMP_DIR:-}"' EXIT

TEST_CURSOR_HOME="$TMP_DIR/cursor-home"
CONFLICT_CURSOR_HOME="$TMP_DIR/conflict-home"
STATE_FILE="$TEST_CURSOR_HOME/plugins/gate-driven-development/cursor-links.tsv"

CURSOR_HOME="$TEST_CURSOR_HOME" bash "$ROOT/scripts/install-cursor-links.sh" >/dev/null

if [[ ! -L "$TEST_CURSOR_HOME/commands/gdd-dev.md" ]]; then
  echo "install script did not create command symlink"
  exit 1
fi

if [[ ! -L "$TEST_CURSOR_HOME/agents/gdd-planning-reviewer.md" ]]; then
  echo "install script did not create planning reviewer symlink"
  exit 1
fi

if [[ ! -L "$TEST_CURSOR_HOME/agents/gdd-implementation-reviewer.md" ]]; then
  echo "install script did not create implementation reviewer symlink"
  exit 1
fi

if [[ ! -L "$TEST_CURSOR_HOME/agents/gdd-security-reviewer.md" ]]; then
  echo "install script did not create security reviewer symlink"
  exit 1
fi

if [[ ! -L "$TEST_CURSOR_HOME/agents/gdd-completion-reviewer.md" ]]; then
  echo "install script did not create completion reviewer symlink"
  exit 1
fi

if [[ ! -L "$TEST_CURSOR_HOME/skills/gdd-requesting-code-review" ]]; then
  echo "install script did not create workflow requesting code review symlink"
  exit 1
fi

if [[ ! -L "$TEST_CURSOR_HOME/skills/gdd-receiving-code-review" ]]; then
  echo "install script did not create workflow receiving code review symlink"
  exit 1
fi

if [[ ! -L "$TEST_CURSOR_HOME/skills/gdd-pre-workflow-brainstorming" ]]; then
  echo "install script did not create pre-workflow brainstorming symlink"
  exit 1
fi

if [[ ! -L "$TEST_CURSOR_HOME/skills/gdd-requirements-gating" ]]; then
  echo "install script did not create requirements gating symlink"
  exit 1
fi

for source_path in "$ROOT"/skills/*; do
  [[ -f "$source_path/SKILL.md" ]] || continue
  skill_name="$(basename "$source_path")"
  target_path="$TEST_CURSOR_HOME/skills/$skill_name"
  if [[ ! -L "$target_path" ]]; then
    echo "install script did not create skill symlink: $skill_name"
    exit 1
  fi
  if [[ "$(readlink "$target_path")" != "$source_path" ]]; then
    echo "install script created wrong skill symlink: $skill_name"
    exit 1
  fi
done

if [[ -e "$TEST_CURSOR_HOME/agents/plan-reviewer.md" ]]; then
  echo "install script should not create legacy design reviewer symlink"
  exit 1
fi

if [[ ! -f "$STATE_FILE" ]]; then
  echo "install script did not write state file"
  exit 1
fi

mkdir -p "$CONFLICT_CURSOR_HOME/agents"
touch "$CONFLICT_CURSOR_HOME/agents/gdd-planning-reviewer.md"

if CURSOR_HOME="$CONFLICT_CURSOR_HOME" bash "$ROOT/scripts/install-cursor-links.sh" >/dev/null 2>&1; then
  echo "install script should fail on target conflict"
  exit 1
fi

if [[ -e "$CONFLICT_CURSOR_HOME/commands/gdd-dev.md" ]]; then
  echo "install script partially applied links on conflict"
  exit 1
fi

UPGRADE_CURSOR_HOME="$TMP_DIR/upgrade-home"
UPGRADE_PLUGIN_ROOT="$TMP_DIR/upgrade-plugin"

cp -R "$ROOT" "$UPGRADE_PLUGIN_ROOT"
mv "$UPGRADE_PLUGIN_ROOT/agents/gdd-planning-reviewer.md" "$UPGRADE_PLUGIN_ROOT/agents/plan-reviewer.md"
mv "$UPGRADE_PLUGIN_ROOT/agents/gdd-implementation-reviewer.md" "$UPGRADE_PLUGIN_ROOT/agents/plan-reviewer-feasibility-strict.md"

CURSOR_HOME="$UPGRADE_CURSOR_HOME" bash "$UPGRADE_PLUGIN_ROOT/scripts/install-cursor-links.sh" >/dev/null

if [[ ! -L "$UPGRADE_CURSOR_HOME/agents/plan-reviewer.md" ]]; then
  echo "upgrade fixture did not create legacy design reviewer symlink"
  exit 1
fi

if CURSOR_HOME="$UPGRADE_CURSOR_HOME" bash "$ROOT/scripts/install-cursor-links.sh" >/dev/null 2>&1; then
  echo "install script should fail when a previously managed target disappears"
  exit 1
fi

if [[ ! -L "$UPGRADE_CURSOR_HOME/agents/plan-reviewer.md" ]]; then
  echo "rename reinstall should fail closed without removing legacy symlink"
  exit 1
fi

if [[ -e "$UPGRADE_CURSOR_HOME/agents/gdd-planning-reviewer.md" ]]; then
  echo "rename reinstall should not partially apply new planning reviewer symlink"
  exit 1
fi

MISSING_STATE_CURSOR_HOME="$TMP_DIR/missing-state-home"
mkdir -p "$MISSING_STATE_CURSOR_HOME/commands"
ln -s "$ROOT/commands/gdd-dev.md" "$MISSING_STATE_CURSOR_HOME/commands/gdd-dev.md"

if CURSOR_HOME="$MISSING_STATE_CURSOR_HOME" bash "$ROOT/scripts/uninstall-cursor-links.sh" >/dev/null 2>&1; then
  echo "uninstall script should fail closed when state file is missing"
  exit 1
fi

if [[ ! -L "$MISSING_STATE_CURSOR_HOME/commands/gdd-dev.md" ]]; then
  echo "uninstall script removed links even though state file was missing"
  exit 1
fi

mkdir -p "$TMP_DIR/moved-plugin/scripts"
cp "$ROOT/scripts/uninstall-cursor-links.sh" "$TMP_DIR/moved-plugin/scripts/uninstall-cursor-links.sh"

CURSOR_HOME="$TEST_CURSOR_HOME" bash "$TMP_DIR/moved-plugin/scripts/uninstall-cursor-links.sh" >/dev/null

if [[ -e "$TEST_CURSOR_HOME/commands/gdd-dev.md" ]]; then
  echo "uninstall script did not remove command symlink"
  exit 1
fi

if [[ -e "$TEST_CURSOR_HOME/agents/gdd-planning-reviewer.md" ]]; then
  echo "uninstall script did not remove planning reviewer symlink"
  exit 1
fi

if [[ -e "$TEST_CURSOR_HOME/agents/gdd-implementation-reviewer.md" ]]; then
  echo "uninstall script did not remove implementation reviewer symlink"
  exit 1
fi

if [[ -e "$TEST_CURSOR_HOME/agents/gdd-security-reviewer.md" ]]; then
  echo "uninstall script did not remove security reviewer symlink"
  exit 1
fi

if [[ -e "$TEST_CURSOR_HOME/agents/gdd-completion-reviewer.md" ]]; then
  echo "uninstall script did not remove completion reviewer symlink"
  exit 1
fi

if [[ -e "$TEST_CURSOR_HOME/skills/gdd-requesting-code-review" ]]; then
  echo "uninstall script did not remove workflow requesting code review symlink"
  exit 1
fi

if [[ -e "$TEST_CURSOR_HOME/skills/gdd-receiving-code-review" ]]; then
  echo "uninstall script did not remove workflow receiving code review symlink"
  exit 1
fi

if [[ -e "$TEST_CURSOR_HOME/skills/gdd-pre-workflow-brainstorming" ]]; then
  echo "uninstall script did not remove pre-workflow brainstorming symlink"
  exit 1
fi

if [[ -e "$TEST_CURSOR_HOME/skills/gdd-requirements-gating" ]]; then
  echo "uninstall script did not remove requirements gating symlink"
  exit 1
fi

if [[ -f "$STATE_FILE" ]]; then
  echo "uninstall script did not remove state file"
  exit 1
fi

echo "VERDICT: active-steering-candidate-resolution: OK"
