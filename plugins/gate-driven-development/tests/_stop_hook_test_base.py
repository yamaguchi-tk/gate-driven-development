"""Integration tests for Stop hook logic.

Tests the core functions extracted from run-gdd-stop-hook.sh's inline Python:
- HANDOFF_PATTERN regex
- persist_handoff_summary() round-trip
- Phase transition detection + handoff missing warning
- parse_state / write_state
- last_assistant_text / last_tool_result_text (transcript scanning)
- ALLOWED_STOP_REASONS validation

Run from plugins/gate-driven-development/:
  python3 -m unittest discover -s tests
  or: python3 -m unittest tests.test_stop_hook_unit tests.test_stop_hook_state_unit tests.test_stop_hook_continuation_unit tests.test_stop_hook_stop_reason_unit tests.test_stop_hook_e2e tests.test_stop_hook_e2e_block_content tests.test_stop_hook_validate -v
"""
from __future__ import annotations

__all__ = [
    "ALLOWED_STOP_REASONS",
    "GOAL_COMPLETE_REASONS",
    "GOAL_INCOMPLETE_REASONS",
    "HANDOFF_PATTERN",
    "PHASE_MARKER",
    "Path",
    "SAMPLE_STATE",
    "STOP_PATTERN",
    "_CLEAN_STATE",
    "_CLEAN_TASKLIST",
    "_DONE_OUTPUT",
    "_HOOK_PATH",
    "_UNFINISHED_TASKLIST",
    "_bind",
    "_git",
    "_make_transcript_jsonl",
    "_make_two_worktree_fixture",
    "_run_hook",
    "_stop_done",
    "_subprocess",
    "_write_binding",
    "_write_state_file",
    "_write_steering",
    "detect_phase_transition",
    "goal_completion_allowed_for_stop",
    "goal_guard_message",
    "is_invalid_active_local_session",
    "json",
    "last_assistant_text",
    "last_tool_result_text",
    "looks_like_gdd_continuation",
    "os",
    "parse_state",
    "persist_handoff_summary_to_content",
    "re",
    "subagent_in_flight",
    "subprocess",
    "sys",
    "tempfile",
    "textwrap",
    "unittest",
    "write_state",
]

import json
import os
import re
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "hooks" / "scripts"))

from _git_fixture import init_repo
from lib.constants import (
    ALLOWED_STOP_REASONS,
    GOAL_COMPLETE_REASONS,
    GOAL_INCOMPLETE_REASONS,
    HANDOFF_PATTERN,
    STOP_PATTERN,
)
from lib.guards import goal_completion_allowed_for_stop, goal_guard_message, looks_like_gdd_continuation
from lib.state_io import parse_state, write_state
from lib.transcript import last_assistant_text, last_tool_result_text, subagent_in_flight

PHASE_MARKER = re.compile(r"<gdd-phase>([^<]+)</gdd-phase>")


def is_invalid_active_local_session(frontmatter: dict[str, str]) -> bool:
    return frontmatter.get("active", "").lower() == "true" and not frontmatter.get("session_id", "")


def persist_handoff_summary_to_content(text: str, content: str) -> str:
    """Simplified version of persist_handoff_summary that operates on string
    content instead of filesystem + git worktree. Returns updated content."""
    match = HANDOFF_PATTERN.search(text)
    if not match:
        return content
    summary = match.group(1).strip()
    if not summary:
        return content
    lines = summary.splitlines()[:10]
    summary = "\n".join(lines)
    encoded = summary.replace("\n", " | ")
    marker = "Last Handoff Summary="
    if marker in content:
        content = re.sub(
            r"Last Handoff Summary=.*",
            f"Last Handoff Summary={encoded}",
            content,
            count=1,
        )
    else:
        for anchor in ["Route In Progress=", "Approved Direction="]:
            if anchor in content:
                idx = content.index(anchor)
                eol = content.index("\n", idx)
                content = (
                    content[: eol + 1]
                    + f"Last Handoff Summary={encoded}\n"
                    + content[eol + 1 :]
                )
                break
    return content


def detect_phase_transition(
    last_output: str, previous_phase: str
) -> tuple[str, str]:
    """Detect current phase and handoff warning.
    Returns (current_phase, handoff_warning).
    """
    phase_match = PHASE_MARKER.search(last_output)
    if phase_match:
        current_phase = phase_match.group(1).strip()
    else:
        current_phase = previous_phase
        lower_output = last_output.lower()
        for candidate in [
            "gdd-completion-check",
            "gdd-implementation-gating",
            "gdd-subagent-driven-implementation",
            "gdd-test-driven-development",
            "gdd-task-breakdown",
            "gdd-design-gating",
            "gdd-requirements-gating",
            "gdd-systematic-debugging",
            "gdd-brainstorming",
            "gdd-pre-workflow-brainstorming",
        ]:
            if candidate in lower_output:
                current_phase = candidate
                break

    phase_transitioned = previous_phase and previous_phase != current_phase
    warning = ""
    if phase_transitioned:
        has_handoff = bool(HANDOFF_PATTERN.search(last_output))
        if not has_handoff:
            warning = (
                f"[context-budget] Phase transition detected "
                f"({previous_phase} -> {current_phase}) "
                "but no Context Handoff Summary found in output. "
                "Include <!-- Context Handoff --> block per references/output-format.md."
            )
    return current_phase, warning


# ===========================================================================
# Tests
# ===========================================================================

SAMPLE_STATE = textwrap.dedent("""\
---
## Gate Status
Requirements Review Status=approved | evidence: req-001
Human Check Status=approved | evidence: hc-001
Design Review Status=approved | evidence: des-001
Route In Progress=none
Approved Direction=REST API でページネーション
---
""")

import subprocess as _subprocess

_HOOK_PATH = (
    Path(__file__).parent.parent / "hooks" / "scripts" / "gdd_stop_hook.py"
).resolve()


def _make_transcript_jsonl(path: Path, assistant_text: str = "", user_text: str = "") -> None:
    """Create a minimal transcript jsonl file with given assistant/user text."""
    lines = []
    if user_text:
        lines.append(json.dumps({
            "type": "user",
            "message": {"content": [{"type": "text", "text": user_text}]},
        }))
    if assistant_text:
        lines.append(json.dumps({
            "type": "assistant",
            "message": {"content": [{"type": "text", "text": assistant_text}]},
        }))
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def _write_state_file(workspace: Path, frontmatter: dict[str, str], body: str = "body") -> Path:
    """Create .claude/gdd-dev.local.md in the workspace."""
    claude_dir = workspace / ".claude"
    claude_dir.mkdir(parents=True, exist_ok=True)
    state_file = claude_dir / "gdd-dev.local.md"
    lines = ["---"]
    for key, value in frontmatter.items():
        lines.append(f"{key}: {value}")
    lines.append("---")
    lines.append("")
    lines.append(body)
    lines.append("")
    state_file.write_text("\n".join(lines), encoding="utf-8")
    return state_file


def _write_binding(workspace: Path, dirname: str, *, branch: str = "") -> Path:
    """`.gdd/tasks/<dirname>/binding.json` を書く（この worktree に bind された状態）。

    bind 限定の変更以降、done guard の検査対象は **bind 済み steering だけ**。
    steering ディレクトリを作っただけでは検査されないので、
    「bind 済みの状態で guard がどう振る舞うか」を測るテストは必ずこれを呼ぶ。
    逆に、呼ばないテストは**意図的に unbound な状態**を測っていることになる。
    実運用では `gdd_task_binding.upsert_binding_from_state()` が書く。
    """
    binding_dir = workspace / ".gdd" / "tasks" / dirname
    binding_dir.mkdir(parents=True, exist_ok=True)
    path = binding_dir / "binding.json"
    path.write_text(
        json.dumps(
            {
                "task_id": dirname,
                "worktree_path": str(workspace.resolve()),
                "steering_path": str((workspace / ".steering" / dirname).resolve()),
                "branch": branch,
            }
        ),
        encoding="utf-8",
    )
    return path


def _write_steering(
    workspace: Path,
    dirname: str,
    tasklist_content: str,
    state_content: str | None = None,
) -> Path:
    """Create .steering/<dirname>/tasklist.md (and optional state.md)."""
    steering = workspace / ".steering" / dirname
    steering.mkdir(parents=True, exist_ok=True)
    (steering / "tasklist.md").write_text(tasklist_content, encoding="utf-8")
    if state_content is not None:
        (steering / "state.md").write_text(state_content, encoding="utf-8")
    return steering


def _run_hook(
    cwd: Path,
    transcript_path: Path | None = None,
    session_id: str = "test-session",
    claude_code_session_id: str | None = "__use_hook_session__",
    stop_hook_active: bool = False,
    env_overrides: dict[str, str] | None = None,
    timeout: float = 60,
) -> tuple[int, str, str]:
    """Run gdd_stop_hook.py as subprocess. Returns (exit_code, stdout, stderr).

    env_overrides: applied last, after the isolation env.pop() calls below —
    use it for tests that need e.g. GDD_PLUGIN_ROOT (script-path resolution)
    or GDD_SKIP_HITL_LINT set to a specific value.
    """
    hook_input: dict = {"cwd": str(cwd), "session_id": session_id}
    if transcript_path is not None:
        hook_input["transcript_path"] = str(transcript_path)
    if stop_hook_active:
        hook_input["stop_hook_active"] = True
    env = os.environ.copy()
    env["GDD_HOOK_INPUT"] = json.dumps(hook_input)
    # Prevent the hook from picking up the developer's real env config
    env.pop("CLAUDE_PLUGIN_ROOT", None)
    env.pop("GDD_PLUGIN_ROOT", None)
    env.pop("CLAUDE_CODE_SESSION_ID", None)
    env.pop("GDD_STOP_HOOK_MAX_CONSECUTIVE_BLOCKS", None)
    env.pop("GDD_SKIP_HITL_LINT", None)
    if env_overrides:
        env.update(env_overrides)
    if claude_code_session_id == "__use_hook_session__":
        claude_code_session_id = session_id
    if claude_code_session_id:
        env["CLAUDE_CODE_SESSION_ID"] = claude_code_session_id
    result = _subprocess.run(
        ["python3", str(_HOOK_PATH)],
        capture_output=True,
        text=True,
        env=env,
        cwd=str(cwd),
        timeout=timeout,
    )
    return result.returncode, result.stdout, result.stderr


# Standard tasklist with one completed task and clean Verification.
_CLEAN_TASKLIST = textwrap.dedent("""\
    # Tasklist

    ## Current Task
    - なし

    ## Pending Tasks
    - なし

    ## Completed Tasks
    - T1 | AC-01 | done

    ## Verification
    | method | status | evidence | notes |
    |---|---|---|---|
    | method=ac:AC-01 | pass | npm test 通過 | - |

    ## Status
    Next Action=done
""")

_CLEAN_STATE = textwrap.dedent("""\
    # State
    Route In Progress=none
""")

# Tasklist with one open task in `## Current Task` (done guard Check 1 が block する形)。
_UNFINISHED_TASKLIST = textwrap.dedent("""\
    # Tasklist

    ## Current Task
    - T1 | AC-01 | still open

    ## Pending Tasks
    - なし

    ## Completed Tasks
    - なし

    ## Verification
    - なし

    ## Status
    Next Action=done
""")

# `reason=done` を宣言する assistant 出力。
_DONE_OUTPUT = textwrap.dedent("""\
    全タスク完了しました。

    ## 👤 次にすること
    レビューを依頼してください。

    <gdd-stop reason="done">
""")


# ===========================================================================
# bind 限定の 2-worktree fixture（bind 解決スコープを測るテスト共通）
#
# `test_stop_hook_bind_resolution_contract.py`（bind スコープ + 見出し受理面）と、そこから
# 分けた `test_stop_hook_tasklist_fence_contract.py`（fence）・
# `test_stop_hook_progress_bind_scope_contract.py`（進捗・Resume From）、
# `test_stop_hook_done_guard_regression_contract.py`（AC-3 / CT-3 の Check 2 / Check 3）
# の 4 ファイルが使う。**複製せずここ 1 箇所に置く**（受理面を増やさない）。
# ===========================================================================


def _git(*args, cwd) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)


def _make_two_worktree_fixture(tmp: Path) -> tuple[Path, Path]:
    """wtA(foreign, unfinished) が `git worktree list` で wtB(target) より先に来る配置。

    現行実装の legacy fallback が誤検査した再現条件そのもの。
    wtA には未完了 tasklist、wtB には完了済み tasklist を置く。
    """
    main = tmp / "main"
    main.mkdir()
    init_repo(main)

    wtA = tmp / "wtA"
    wtB = tmp / "wtB"
    _git("worktree", "add", "-b", "foreign-branch", str(wtA), cwd=main)
    _git("worktree", "add", "-b", "target-branch", str(wtB), cwd=main)

    (wtA / ".steering" / "20260101-foreign").mkdir(parents=True)
    (wtA / ".steering" / "20260101-foreign" / "tasklist.md").write_text(
        _UNFINISHED_TASKLIST, encoding="utf-8"
    )
    (wtB / ".steering" / "20260822-target").mkdir(parents=True)
    (wtB / ".steering" / "20260822-target" / "tasklist.md").write_text(
        _CLEAN_TASKLIST, encoding="utf-8"
    )

    listing = subprocess.run(
        ["git", "worktree", "list", "--porcelain"],
        cwd=wtB,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    idx_a = listing.index(str(wtA))
    idx_b = listing.index(str(wtB))
    # `assert` は `python -O` で消える。順序が逆のまま通すと述語が最初から緑になり
    # RED の意味が失われるため、明示的に送出する。
    if idx_a >= idx_b:
        raise AssertionError("fixture invariant broken: wtA must list before wtB")
    return wtA, wtB


def _bind(worktree: Path, slug: str = "20260822-target") -> None:
    binding_dir = worktree / ".gdd" / "tasks" / slug
    binding_dir.mkdir(parents=True, exist_ok=True)
    (binding_dir / "binding.json").write_text(
        json.dumps(
            {
                "task_id": slug,
                "worktree_path": str(worktree.resolve()),
                "steering_path": str((worktree / ".steering" / slug).resolve()),
                "branch": "target-branch",
            }
        ),
        encoding="utf-8",
    )


def _stop_done(worktree: Path) -> tuple[int, str, str]:
    """`reason=done` で stop hook を実行する（アクティブセッション状態を作ってから）。"""
    _write_state_file(
        worktree, {"active": "true", "session_id": "test-session", "iteration": "1"}
    )
    transcript = worktree / "transcript.jsonl"
    _make_transcript_jsonl(transcript, assistant_text=_DONE_OUTPUT)
    return _run_hook(worktree, transcript, session_id="test-session")
