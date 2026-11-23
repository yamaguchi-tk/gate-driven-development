"""Tests for run-pre-compact-hook.sh.

Covers: the reminder systemMessage (the facts handed to the compaction summarizer) —
including its noop behavior when python is unavailable or fails at runtime.
The line forms, the role-agnostic wording and "state.md is not written" are in
test_compact_without_auto_resume.py.
"""
import json
import shutil
import subprocess
import os
from pathlib import Path

from _paths import PLUGIN_ROOT
SCRIPT = PLUGIN_ROOT / "hooks/scripts/run-pre-compact-hook.sh"


def _make_state(tmp: Path, extra: str = "") -> Path:
    state = tmp / "state.md"
    state.write_text("Resume From: gdd-task-breakdown\n" + extra)
    return state


def test_noop_when_no_state(tmp_path):
    env = {**os.environ, "GDD_STEERING_DIR": str(tmp_path)}
    r = subprocess.run(["bash", str(SCRIPT)], env=env, capture_output=True, text=True)
    assert r.returncode == 0  # コンパクションをブロックしない


def test_emits_reminder_system_message(tmp_path):
    """compact 直前に systemMessage で Resume From を要約器へ渡す。"""
    _make_state(tmp_path)  # Resume From: gdd-task-breakdown
    env = {**os.environ, "GDD_STEERING_DIR": str(tmp_path)}
    r = subprocess.run(["bash", str(SCRIPT)], env=env, capture_output=True, text=True)
    assert r.returncode == 0
    payload = json.loads(r.stdout)
    assert "gdd-task-breakdown" in payload["systemMessage"]


def test_no_reminder_when_resume_from_missing(tmp_path):
    state = tmp_path / "state.md"
    state.write_text("Status: in_progress\n")
    env = {**os.environ, "GDD_STEERING_DIR": str(tmp_path)}
    r = subprocess.run(["bash", str(SCRIPT)], env=env, capture_output=True, text=True)
    assert r.returncode == 0
    assert r.stdout.strip() == ""


def test_noop_reminder_when_python_unavailable(tmp_path):
    """python3/python が無い環境でもリマインダー出力をスキップし、
    compaction をブロックしない（noop 方針。Copilotレビュー #145 指摘）。"""
    _make_state(tmp_path)  # Resume From: gdd-task-breakdown
    # スクリプトが実際に使う外部コマンドだけを含み、python/python3 を含まない
    # PATH を組み立てる（macOS は /usr/bin/python3 スタブを常備しているため
    # PATH を素朴に絞るだけでは python 不在環境を再現できない）。
    fake_bin = tmp_path / "fake_bin"
    fake_bin.mkdir()
    for name in ("awk", "date", "dirname", "grep", "head", "rm", "sed", "tail", "tr"):
        real_path = shutil.which(name)
        assert real_path, f"{name} not found on test host"
        (fake_bin / name).symlink_to(real_path)
    env = {
        **{k: v for k, v in os.environ.items() if k != "PATH"},
        "PATH": str(fake_bin),
        "GDD_STEERING_DIR": str(tmp_path),
    }
    bash_path = shutil.which("bash")
    r = subprocess.run([bash_path, str(SCRIPT)], env=env, capture_output=True, text=True)
    assert r.returncode == 0
    assert r.stdout.strip() == ""


def test_noop_reminder_when_python_fails_at_runtime(tmp_path):
    """python3 が存在しても実行時エラー（非0終了）を起こす場合、
    compaction をブロックしない（noop 方針。Copilotレビュー #145 追加指摘）。"""
    _make_state(tmp_path)  # Resume From: gdd-task-breakdown
    fake_bin = tmp_path / "fake_bin"
    fake_bin.mkdir()
    for name in ("awk", "date", "dirname", "grep", "head", "rm", "sed", "tail", "tr"):
        real_path = shutil.which(name)
        assert real_path, f"{name} not found on test host"
        (fake_bin / name).symlink_to(real_path)
    fake_python = fake_bin / "python3"
    fake_python.write_text("#!/bin/sh\necho 'boom' >&2\nexit 1\n")
    fake_python.chmod(0o755)
    env = {
        **{k: v for k, v in os.environ.items() if k != "PATH"},
        "PATH": str(fake_bin),
        "GDD_STEERING_DIR": str(tmp_path),
    }
    bash_path = shutil.which("bash")
    r = subprocess.run([bash_path, str(SCRIPT)], env=env, capture_output=True, text=True)
    assert r.returncode == 0
    assert r.stdout.strip() == ""


def test_reminder_truncates_and_strips_control_chars_in_resume_from(tmp_path):
    """Resume From を systemMessage に注入する前に長さ制限・制御文字除去を行う
    （run-session-start-hook.sh と同様。Copilotレビュー #145 指摘）。"""
    long_value = "a" * 200 + "\x1b[31mDANGER\x07" + "b" * 50
    state = tmp_path / "state.md"
    state.write_text(f"Resume From: {long_value}\n")
    env = {**os.environ, "GDD_STEERING_DIR": str(tmp_path)}
    r = subprocess.run(["bash", str(SCRIPT)], env=env, capture_output=True, text=True)
    assert r.returncode == 0
    output = json.loads(r.stdout.strip())
    message = output["systemMessage"]
    assert "\x1b" not in message
    assert "\x07" not in message
    assert "b" * 50 not in message  # 128文字を超える末尾は切り捨てられる
