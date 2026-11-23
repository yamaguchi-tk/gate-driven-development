"""main が gate の skill を Skill ツールで直接呼んだとき、runner への dispatch を促す hook の契約。

2026-09-28〜30 の実測で、GDD の自動継続が効いていない再開（自由文・compact・resume の後）では、
main が state.md の Next Action の名前の skill をそのまま呼び、gate を main で回していた
（reviewer の起動の一部）。runner の Template が書かせる handoff/ の記録が残らず、
impl-gate の round 2 を飛ばした例もあった。本 hook は block せず、Template の場所を伝える。
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
from pathlib import Path

import pytest

from _paths import PLUGIN_ROOT

HOOK = PLUGIN_ROOT / "hooks" / "scripts" / "run-gate-skill-dispatch-nudge-hook.sh"


def _run(payload: object, *, home: Path | None = None, raw: str | None = None) -> subprocess.CompletedProcess[str]:
    env = {
        "PATH": os.environ.get("PATH", ""),
        "CLAUDE_PLUGIN_ROOT": str(PLUGIN_ROOT),
        "HOME": str(home) if home else tempfile.mkdtemp(),
    }
    return subprocess.run(
        ["bash", str(HOOK)],
        input=raw if raw is not None else json.dumps(payload),
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )


def _context(proc: subprocess.CompletedProcess[str]) -> str:
    assert proc.returncode == 0, proc.stderr
    out = json.loads(proc.stdout)
    assert set(out) == {"hookSpecificOutput"}
    hso = out["hookSpecificOutput"]
    assert set(hso) == {"hookEventName", "additionalContext"}
    assert hso["hookEventName"] == "PreToolUse"
    return hso["additionalContext"]


@pytest.mark.parametrize(
    ("skill", "template"),
    [
        ("gate-driven-development:gdd-implementation-gating", "Implementation-Gating Template"),
        ("gdd-implementation-gating", "Implementation-Gating Template"),
        ("gate-driven-development:gdd-completion-check", "Completion-Check Template"),
        ("gdd-completion-check", "Completion-Check Template"),
    ],
)
def test_gate_skill_gets_runner_dispatch_context(skill: str, template: str) -> None:
    ctx = _context(_run({"tool_name": "Skill", "tool_input": {"skill": skill}}))
    assert template in ctx
    assert "gate-driven-development:gdd-formal-gate-runner" in ctx
    assert str(PLUGIN_ROOT / "references" / "subagent-dispatch.md") in ctx


@pytest.mark.parametrize("skill", ["gdd-implementation-gating", "gdd-completion-check"])
def test_pointed_template_exists_and_dispatches_to_the_named_runner(skill: str) -> None:
    ctx = _context(_run({"tool_name": "Skill", "tool_input": {"skill": skill}}))
    heading = re.search(r"`(### [^`]+)`", ctx).group(1)
    runner = re.search(r"`(gate-driven-development:[a-z-]+)` に dispatch", ctx).group(1)
    doc = (PLUGIN_ROOT / "references" / "subagent-dispatch.md").read_text(encoding="utf-8")
    lines = doc.splitlines()
    assert heading in lines
    start = lines.index(heading) + 1
    end = next((i for i in range(start, len(lines)) if lines[i].startswith("#")), len(lines))
    section = "\n".join(lines[start:end])
    assert f'subagent_type="{runner}"' in section


@pytest.mark.parametrize("key", ["skill", "name", "skill_name"])
def test_skill_name_keys_match_the_existing_skill_hook(key: str) -> None:
    ctx = _context(_run({"tool_name": "Skill", "tool_input": {key: "gdd-implementation-gating"}}))
    assert "Implementation-Gating Template" in ctx


@pytest.mark.parametrize(
    "skill",
    [
        "gate-driven-development:gdd-test-driven-development",
        "gate-driven-development:gdd-design-gating",
        "gdd-implementation-gating-extra",
        "superpowers:brainstorming",
        "",
    ],
)
def test_other_skills_get_no_output(skill: str) -> None:
    proc = _run({"tool_name": "Skill", "tool_input": {"skill": skill}})
    assert proc.returncode == 0
    assert proc.stdout == ""


@pytest.mark.parametrize("raw", ["", "not json", "[]", '{"tool_input": "x"}'])
def test_unreadable_payload_exits_quietly(raw: str) -> None:
    proc = _run(None, raw=raw)
    assert proc.returncode == 0
    assert proc.stdout == ""


def test_kill_switch_silences_the_hook(tmp_path: Path) -> None:
    (tmp_path / ".claude").mkdir()
    (tmp_path / ".claude" / "gdd-hooks-disabled").write_text("", encoding="utf-8")
    proc = _run({"tool_name": "Skill", "tool_input": {"skill": "gdd-completion-check"}}, home=tmp_path)
    assert proc.returncode == 0
    assert proc.stdout == ""


def _skill_commands() -> list[str]:
    hooks = json.loads((PLUGIN_ROOT / "hooks" / "hooks.json").read_text(encoding="utf-8"))["hooks"]
    return [
        h["command"]
        for entry in hooks["PreToolUse"]
        if re.fullmatch(entry.get("matcher", ""), "Skill")
        for h in entry["hooks"]
    ]


def test_hooks_json_runs_the_nudge_on_skill_calls() -> None:
    commands = [c for c in _skill_commands() if "run-gate-skill-dispatch-nudge-hook.sh" in c]
    assert len(commands) == 1
    env = {"PATH": os.environ.get("PATH", ""), "CLAUDE_PLUGIN_ROOT": str(PLUGIN_ROOT), "HOME": tempfile.mkdtemp()}
    proc = subprocess.run(
        ["bash", "-c", commands[0]],
        input=json.dumps({"tool_name": "Skill", "tool_input": {"skill": "gate-driven-development:gdd-implementation-gating"}}),
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    assert "Implementation-Gating Template" in _context(proc)
