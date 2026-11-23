"""AC-A1 / AC-compose / AC-regression: run-gdd-stop-hook.sh の fail-open 4象限を検証する。"""
import json
import shutil
import subprocess
from pathlib import Path

from _paths import PLUGIN_ROOT
from _timing_budget import hang_guard_seconds
STOP_HOOK = PLUGIN_ROOT / "hooks" / "scripts" / "run-gdd-stop-hook.sh"

REQUIRED_COMMANDS = ["bash", "cat", "grep", "dirname", "pwd"]


OPTIONAL_COMMANDS = ["git", "python3"]


def _make_symlink_farm(tmp_path: Path, exclude: list[str]) -> Path:
    """REQUIRED_COMMANDS + OPTIONAL_COMMANDS（exclude されない限り含む）で fake PATH を作る。

    git-missing テストで python3 を意図せず欠落させ、実際には python-missing 経路を
    検証してしまう（AC-A1 の git 分岐が未検証になる）ことを避けるため、
    exclude で明示されないコマンドはデフォルトで含める。
    """
    fake_bin = tmp_path / "fake_bin"
    fake_bin.mkdir()
    commands = REQUIRED_COMMANDS + [c for c in OPTIONAL_COMMANDS if c not in exclude]
    for cmd in commands:
        real_path = shutil.which(cmd)
        assert real_path is not None, f"required command not found on host: {cmd}"
        (fake_bin / cmd).symlink_to(real_path)
    return fake_bin


def _make_local_state(repo_dir: Path, active: bool) -> None:
    claude_dir = repo_dir / ".claude"
    claude_dir.mkdir(parents=True, exist_ok=True)
    value = "true" if active else "false"
    (claude_dir / "gdd-dev.local.md").write_text(f"active: {value}\n")


def _run_stop_hook(cwd: Path, fake_bin: Path, stop_hook_active: bool = False):
    payload = json.dumps({
        "cwd": str(cwd),
        "transcript_path": str(cwd / "transcript.jsonl"),
        "session_id": "test-session",
        "stop_hook_active": stop_hook_active,
    })
    env = {"PATH": str(fake_bin), "HOME": str(cwd), "CLAUDE_PLUGIN_ROOT": str(PLUGIN_ROOT)}
    return subprocess.run(
        ["bash", str(STOP_HOOK)],
        input=payload,
        capture_output=True,
        text=True,
        cwd=str(cwd),
        env=env,
        timeout=hang_guard_seconds("run-gdd-stop-hook.sh"),
    )


def test_inactive_python_missing_does_not_block(tmp_path):
    fake_bin = _make_symlink_farm(tmp_path, exclude=["python3", "python"])
    _make_local_state(tmp_path, active=False)
    result = _run_stop_hook(tmp_path, fake_bin)
    assert result.returncode == 0
    assert '"decision":"block"' not in result.stdout


def test_active_python_missing_blocks(tmp_path):
    fake_bin = _make_symlink_farm(tmp_path, exclude=["python3", "python"])
    _make_local_state(tmp_path, active=True)
    result = _run_stop_hook(tmp_path, fake_bin)
    assert '"decision":"block"' in result.stdout


def test_active_stop_hook_already_active_does_not_double_block(tmp_path):
    fake_bin = _make_symlink_farm(tmp_path, exclude=["python3", "python"])
    _make_local_state(tmp_path, active=True)
    result = _run_stop_hook(tmp_path, fake_bin, stop_hook_active=True)
    assert result.returncode == 0
    assert '"decision":"block"' not in result.stdout


def test_inactive_git_missing_does_not_block(tmp_path):
    fake_bin = _make_symlink_farm(tmp_path, exclude=["git"])
    _make_local_state(tmp_path, active=False)
    result = _run_stop_hook(tmp_path, fake_bin)
    assert result.returncode == 0
    assert '"decision":"block"' not in result.stdout


def test_active_git_missing_blocks(tmp_path):
    fake_bin = _make_symlink_farm(tmp_path, exclude=["git"])
    _make_local_state(tmp_path, active=True)
    result = _run_stop_hook(tmp_path, fake_bin)
    assert '"decision":"block"' in result.stdout


def test_active_python_present_still_passes_hook_input_to_body(tmp_path):
    """stdin hoist の regression 回避: GDD_HOOK_INPUT が本体に正しく渡ることを確認する。"""
    fake_bin = _make_symlink_farm(tmp_path, exclude=[])
    _make_local_state(tmp_path, active=True)
    result = _run_stop_hook(tmp_path, fake_bin)
    # 本体が正常実行できていること（GDD_HOOK_INPUT が空でクラッシュしていないこと、
    # wrapper自体がsource path等の問題で早期失敗していないこと）を
    # returncodeとstderrのPythonのTraceback/KeyError有無で確認する
    assert result.returncode == 0, f"stderr={result.stderr!r}"
    assert "Traceback" not in result.stderr
    assert "KeyError" not in result.stderr
