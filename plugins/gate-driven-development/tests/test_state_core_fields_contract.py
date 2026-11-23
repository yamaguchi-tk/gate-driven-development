"""state.md の Tier 1 (Core) field 充足を write 側でも検査する契約テスト。

背景:
`detect-steering.sh:gdd_validate_active_state_fields` は
`Resume From` / `Human Check Status` / `Route In Progress` の 3 field すべてを
要求して fail-closed する。一方 `validate-steering-write.py` 側には充足検査が無く、
`STATE_REQUIRED_FIELDS` は `Started At` の transitive 判定にしか使われていなかった。

書き込み側が無検査・読み取り側が厳格という非対称のため、実運用の state.md で
3 field が揃っていたのは一部だけだった。write 時点で検査して非対称を解消する。

判定は「既存ファイル内容 + 書き込み chunk」に対して行う。
chunk だけを見ると、Edit で 1 field ずつ更新する通常運用で永久に検査されないため。
"""
from __future__ import annotations

import importlib.util
import io
import contextlib
import json
import sys
from pathlib import Path

import pytest

from _paths import PLUGIN_ROOT
SCRIPT = PLUGIN_ROOT / "hooks" / "scripts" / "validate-steering-write.py"

CORE_FIELDS = (
    "Resume From: gdd-test-driven-development\n"
    "Human Check Status: approved\n"
    "Route In Progress: none\n"
    "Started At: 2026-07-27T09:00:00Z\n"
)


@pytest.fixture()
def module(tmp_path, monkeypatch):
    """deny counter がユーザー環境を汚さないよう state dir を tmp に向けて読み込む"""
    monkeypatch.setenv("GDD_HOOK_STATE_DIR", str(tmp_path / "hook-state"))
    spec = importlib.util.spec_from_file_location("validate_steering_write_core", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["validate_steering_write_core"] = mod
    spec.loader.exec_module(mod)
    return mod


def _run(module, payload: dict) -> tuple[int, str]:
    """main() を stdin 差し替えで実行し (exit_code, stderr) を返す"""
    stderr = io.StringIO()
    with contextlib.redirect_stderr(stderr):
        with contextlib.redirect_stdout(io.StringIO()):
            monkey_stdin = io.StringIO(json.dumps(payload))
            original = sys.stdin
            sys.stdin = monkey_stdin
            try:
                code = module.main()
            finally:
                sys.stdin = original
    return code, stderr.getvalue()


def _state_path(tmp_path: Path) -> Path:
    p = tmp_path / ".steering" / "20260727-task" / "state.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def _write_payload(path: Path, content: str) -> dict:
    return {"tool_name": "Write", "tool_input": {"file_path": str(path), "content": content}}


def test_allows_write_with_all_core_fields(module, tmp_path):
    """3 field が揃った state.md の書き込みは通る"""
    path = _state_path(tmp_path)
    code, _ = _run(module, _write_payload(path, CORE_FIELDS))
    assert code == 0, "state.md with all core fields must be allowed"


def test_denies_write_missing_route_in_progress(module, tmp_path):
    """Route In Progress が欠落した state.md の書き込みは deny される"""
    path = _state_path(tmp_path)
    content = (
        "Resume From: gdd-test-driven-development\n"
        "Human Check Status: approved\n"
        "Started At: 2026-07-27T09:00:00Z\n"
    )
    code, stderr = _run(module, _write_payload(path, content))
    assert code == 2, f"missing Route In Progress must be denied, got exit={code}"
    assert "Route In Progress" in stderr, f"deny reason should name the missing field: {stderr}"


def test_denies_write_missing_two_core_fields(module, tmp_path):
    """複数欠落しているときは欠落 field をすべて挙げる"""
    path = _state_path(tmp_path)
    content = "Resume From: gdd-task-breakdown\nStarted At: 2026-07-27T09:00:00Z\n"
    code, stderr = _run(module, _write_payload(path, content))
    assert code == 2
    assert "Human Check Status" in stderr
    assert "Route In Progress" in stderr


def test_allows_partial_edit_when_existing_file_has_rest(module, tmp_path):
    """Edit で 1 field だけ更新しても、既存ファイルに残りが揃っていれば通る

    これが chunk 単位でなく「結果ファイル」で判定する必要がある理由。
    """
    path = _state_path(tmp_path)
    path.write_text(CORE_FIELDS, encoding="utf-8")
    payload = {
        "tool_name": "Edit",
        "tool_input": {
            "file_path": str(path),
            "old_string": "Resume From: gdd-test-driven-development",
            "new_string": "Resume From: gdd-implementation-gating",
        },
    }
    code, stderr = _run(module, payload)
    assert code == 0, f"partial edit on a complete state.md must be allowed: {stderr}"


def test_denies_partial_edit_when_existing_file_incomplete(module, tmp_path):
    """既存ファイルが不完全なまま routing field を触る書き込みは deny される"""
    path = _state_path(tmp_path)
    path.write_text("Resume From: gdd-task-breakdown\nStarted At: 2026-07-27T09:00:00Z\n", encoding="utf-8")
    payload = {
        "tool_name": "Edit",
        "tool_input": {
            "file_path": str(path),
            "old_string": "Resume From: gdd-task-breakdown",
            "new_string": "Resume From: gdd-design-gating",
        },
    }
    code, _ = _run(module, payload)
    assert code == 2, "incomplete state.md must be denied when routing fields are touched"


def test_ignores_non_state_steering_files(module, tmp_path):
    """state.md 以外の steering artifact は対象外"""
    path = tmp_path / ".steering" / "20260727-task" / "design.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    code, _ = _run(module, _write_payload(path, "# Design\n\n設計方針を書く。\n"))
    assert code == 0, "design.md must not be subject to state core field validation"


def test_ignores_files_outside_steering(module, tmp_path):
    """.steering 外のファイルは対象外"""
    path = tmp_path / "notes.md"
    code, _ = _run(module, _write_payload(path, "Resume From: something\n"))
    assert code == 0, "files outside .steering must not be validated"


# ---------------------------------------------------------------------------
# canonical tasklist phase 以降の `Next Action` を write 側でも必須にする
#
# 実データでは `Next Action` が state.md / tasklist.md の両方で欠落しているものが少なくなかった。
# gate 判定の区切りを揃えて read 側は fail-closed するようになったが、write 側は無検査のままだったため
# 「書けてしまってから止まる」構図が残っていた。
#
# 設計:
# - conditional field なので canonical（3 gate approved + tasklist.md あり）のときだけ必須
# - 保存先は state.md / tasklist.md のどちらでもよい（read 側で state.md / tasklist.md を切り離したのと整合）
# - 既存の `state_core_fields` カテゴリに統合する。別カテゴリにすると deny メッセージが
#   2 本に割れ、MAX_CONSECUTIVE_DENIES の counter も独立して ping-pong を招く
# ---------------------------------------------------------------------------

GATES_APPROVED = (
    "Requirements Review Status: approved | evidence: r\n"
    "Design Review Status: approved | evidence: d\n"
)


def _canonical_dir(tmp_path: Path, tasklist_body: str = "## Current Task\n### Task: T-1 x\n") -> Path:
    """3 gate approved + tasklist.md ありの steering を作る"""
    path = _state_path(tmp_path)
    (path.parent / "tasklist.md").write_text(tasklist_body, encoding="utf-8")
    return path


def test_denies_missing_next_action_when_canonical(module, tmp_path):
    """canonical なのに Next Action がどちらのファイルにも無ければ deny"""
    path = _canonical_dir(tmp_path)
    code, stderr = _run(module, _write_payload(path, CORE_FIELDS + GATES_APPROVED))
    assert code == 2, "canonical phase must require Next Action"
    assert "Next Action" in stderr, f"deny reason should name the field: {stderr}"


def test_allows_next_action_in_state_md(module, tmp_path):
    """Next Action が state.md にあれば通る"""
    path = _canonical_dir(tmp_path)
    content = CORE_FIELDS + GATES_APPROVED + "Next Action: gdd-implementation-gating\n"
    code, stderr = _run(module, _write_payload(path, content))
    assert code == 0, f"Next Action in state.md must be accepted: {stderr}"


def test_allows_next_action_in_tasklist(module, tmp_path):
    """Next Action が tasklist.md にあれば通る（従来の routing source）"""
    path = _canonical_dir(
        tmp_path,
        "## Current Task\n### Task: T-1 x\n\n## Review Status\nNext Action=gdd-implementation-gating\n",
    )
    code, stderr = _run(module, _write_payload(path, CORE_FIELDS + GATES_APPROVED))
    assert code == 0, f"Next Action in tasklist.md must be accepted: {stderr}"


def test_next_action_not_required_before_canonical(module, tmp_path):
    """planning phase（gate 未承認）では Next Action を要求しない（conditional）"""
    path = _state_path(tmp_path)
    (path.parent / "tasklist.md").write_text("## Current Task\n### Task: T-1 x\n", encoding="utf-8")
    content = CORE_FIELDS + "Requirements Review Status: in_review\nDesign Review Status: pending\n"
    code, stderr = _run(module, _write_payload(path, content))
    assert code == 0, f"Next Action must stay conditional before canonical: {stderr}"


def test_next_action_not_required_without_tasklist(module, tmp_path):
    """tasklist.md が無ければ canonical ではないので要求しない"""
    path = _state_path(tmp_path)
    code, _ = _run(module, _write_payload(path, CORE_FIELDS + GATES_APPROVED))
    assert code == 0, "no tasklist.md means not canonical"


def test_missing_fields_reported_in_one_message(module, tmp_path):
    """Next Action と他の Core field が同時に欠けても deny は 1 本にまとまる

    2 本に割れるとエージェントが 1 回の書き込みで直せず、
    MAX_CONSECUTIVE_DENIES の escape hatch を無駄に消費する。
    """
    path = _canonical_dir(tmp_path)
    content = (
        "Resume From: gdd-test-driven-development\n"
        "Human Check Status: approved\n"
        "Started At: 2026-07-28T09:00:00Z\n"
    ) + GATES_APPROVED
    code, stderr = _run(module, _write_payload(path, content))
    assert code == 2
    assert "Route In Progress" in stderr and "Next Action" in stderr, \
        f"both missing fields must appear in one message: {stderr}"
    assert stderr.count("state.md without canonical") == 1, \
        f"deny message must not be split into two: {stderr}"
