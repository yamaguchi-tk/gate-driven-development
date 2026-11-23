# test_setup_gdd_loop_project_root.py
# setup-gdd-loop.sh: 別の checkout から写された marker（`project_root:` が今の git toplevel と違う）
# をロックにしないこと。値を確かに読めないとき・比べられないときは、今までどおりロックにすること。
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from _paths import PLUGIN_ROOT

sys.path.insert(0, str(PLUGIN_ROOT / "hooks" / "scripts"))
from lib.state_io import parse_state, write_state  # noqa: E402

SCRIPT = PLUGIN_ROOT / "scripts" / "setup-gdd-loop.sh"
LOCK = "already active in another session"
COPIED = "copied from another checkout"


def _git(cwd: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@example.com", *args],
        cwd=cwd, check=True, capture_output=True, text=True,
    ).stdout


def _repo(base: Path, name: str = "root") -> tuple[Path, Path]:
    """root の repo と、その下の linked worktree を作る（Claude desktop の配置と同じ形）"""
    root = base / name
    root.mkdir(parents=True)
    _git(root, "init", "-q")
    _git(root, "commit", "-q", "--allow-empty", "-m", "init")
    wt = root / ".claude" / "worktrees" / "wt"
    _git(root, "worktree", "add", "-q", "-b", "wt", str(wt))
    return root, wt


def _toplevel(cwd: Path) -> str:
    out = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"], cwd=cwd, check=True,
        capture_output=True, text=True,
    ).stdout
    return out[:-1]


def _run(cwd: Path, session_id: str, intent: str = "test intent", env_extra=None):
    # ロックの分岐は transcript を読むので、実際の ~/.claude/projects を走査しないよう空の場所を指す
    env = {**os.environ, "CLAUDE_CODE_SESSION_ID": session_id, "CLAUDE_CONFIG_DIR": str(cwd / "no-claude-config"), **(env_extra or {})}
    return subprocess.run(
        ["bash", str(SCRIPT), intent], cwd=cwd, env=env,
        capture_output=True, text=True,
    )


def _marker(checkout: Path) -> Path:
    return checkout / ".claude" / "gdd-dev.local.md"


def _write_marker(checkout: Path, text: str) -> Path:
    path = _marker(checkout)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _frontmatter(lines: str) -> str:
    return f"---\nactive: true\nsession_id: OLD-SESSION\n{lines}---\nbody\n"


def _copy_root_marker(root: Path, wt: Path) -> None:
    (wt / ".claude").mkdir(parents=True, exist_ok=True)
    shutil.copy2(_marker(root), _marker(wt))


# --- 書く側 ---------------------------------------------------------------


def test_marker_records_project_root_as_json(tmp_path):
    root, _ = _repo(tmp_path)
    r = _run(root, "SESSION-A")
    assert r.returncode == 0, r.stderr
    fm, _body = parse_state(_marker(root))
    assert json.loads(fm["project_root"]) == _toplevel(root)


def test_marker_without_git_has_no_project_root(tmp_path):
    r = _run(tmp_path, "SESSION-A")
    assert r.returncode == 0, r.stderr
    fm, _body = parse_state(_marker(tmp_path))
    assert "project_root" not in fm


# --- 写された marker はロックにしない（正当な操作）--------------------------


def test_marker_copied_from_root_does_not_lock_worktree(tmp_path):
    root, wt = _repo(tmp_path)
    assert _run(root, "SESSION-A").returncode == 0
    _copy_root_marker(root, wt)
    r = _run(wt, "SESSION-B")
    assert r.returncode == 0, r.stderr
    assert LOCK not in r.stderr
    assert COPIED in r.stderr
    assert "SESSION-A" in r.stderr
    fm, _body = parse_state(_marker(wt))
    assert fm["session_id"] == "SESSION-B"
    assert json.loads(fm["project_root"]) == _toplevel(wt)
    # 持ち主の marker は変わらない
    root_fm, _ = parse_state(_marker(root))
    assert root_fm["session_id"] == "SESSION-A"


def test_copied_marker_in_path_with_hash_space_and_non_ascii(tmp_path):
    root, wt = _repo(tmp_path, "r #1 日本")
    assert _run(root, "SESSION-A").returncode == 0
    _copy_root_marker(root, wt)
    r = _run(wt, "SESSION-B")
    assert r.returncode == 0, r.stderr
    assert COPIED in r.stderr


def test_copied_marker_survives_stop_hook_round_trip(tmp_path):
    """stop hook の write_state を通った後も project_root が同じ値で残り、写しを見分けられる"""
    root, wt = _repo(tmp_path)
    assert _run(root, "SESSION-A").returncode == 0
    fm, body = parse_state(_marker(root))
    write_state(_marker(root), fm, body)
    again, _ = parse_state(_marker(root))
    assert again["project_root"] == fm["project_root"]
    _copy_root_marker(root, wt)
    r = _run(wt, "SESSION-B")
    assert r.returncode == 0, r.stderr
    assert COPIED in r.stderr


# --- block すべき入力が allow にならない -------------------------------------


def test_same_project_root_other_session_locks(tmp_path):
    root, _ = _repo(tmp_path)
    assert _run(root, "SESSION-A").returncode == 0
    r = _run(root, "SESSION-B")
    assert r.returncode == 1
    assert LOCK in r.stderr
    assert COPIED not in r.stderr


def test_same_project_root_in_unusual_path_locks(tmp_path):
    root, _ = _repo(tmp_path, "r #1 日本 ")
    assert _run(root, "SESSION-A").returncode == 0
    r = _run(root, "SESSION-B")
    assert r.returncode == 1
    assert LOCK in r.stderr


def test_marker_without_project_root_still_locks(tmp_path):
    _, wt = _repo(tmp_path)
    _write_marker(wt, _frontmatter(""))
    r = _run(wt, "SESSION-B")
    assert r.returncode == 1
    assert LOCK in r.stderr


def test_project_root_only_in_body_still_locks(tmp_path):
    """本文（User intent など）に書かれた project_root: は読まない"""
    root, wt = _repo(tmp_path)
    _write_marker(wt, _frontmatter("") + f"project_root: {json.dumps(str(root))}\n")
    r = _run(wt, "SESSION-B")
    assert r.returncode == 1
    assert LOCK in r.stderr


def test_project_root_injected_through_multiline_intent_still_locks(tmp_path):
    """複数行の intent から本文に project_root: の行を置いても、写しとして扱わない"""
    root, wt = _repo(tmp_path)
    intent = f"task\nproject_root: {json.dumps(str(root))}"
    assert _run(wt, "SESSION-A", intent=intent).returncode == 0
    r = _run(wt, "SESSION-B")
    assert r.returncode == 1
    assert LOCK in r.stderr


def test_two_project_root_lines_still_lock(tmp_path):
    root, wt = _repo(tmp_path)
    lines = (
        f"project_root: {json.dumps(_toplevel(wt))}\n"
        f"project_root: {json.dumps(str(root))}\n"
    )
    _write_marker(wt, _frontmatter(lines))
    r = _run(wt, "SESSION-B")
    assert r.returncode == 1
    assert LOCK in r.stderr


def test_project_root_not_a_json_string_still_locks(tmp_path):
    root, wt = _repo(tmp_path)
    for value in [str(root), "123", '["/x"]', '"', '""', "null"]:
        _write_marker(wt, _frontmatter(f"project_root: {value}\n"))
        r = _run(wt, "SESSION-B")
        assert r.returncode == 1, value
        assert LOCK in r.stderr, value


def test_marker_without_frontmatter_delimiter_still_locks(tmp_path):
    root, wt = _repo(tmp_path)
    _write_marker(
        wt,
        f"active: true\nsession_id: OLD-SESSION\nproject_root: {json.dumps(str(root))}\n",
    )
    r = _run(wt, "SESSION-B")
    assert r.returncode == 1
    assert LOCK in r.stderr


def test_owner_moved_with_git_worktree_move_still_locks(tmp_path):
    """持ち主の checkout が git worktree move で動いた後は、記録値の旧パスが無い。写しとして扱わない"""
    root, wt = _repo(tmp_path)
    assert _run(wt, "SESSION-A").returncode == 0
    moved = root / ".claude" / "worktrees" / "wt2"
    _git(root, "worktree", "move", str(wt), str(moved))
    r = _run(moved, "SESSION-B")
    assert r.returncode == 1
    assert LOCK in r.stderr
    assert COPIED not in r.stderr


def test_recorded_value_not_an_existing_other_directory_still_locks(tmp_path):
    """記録値は、今の toplevel と別の実在するディレクトリを指す絶対パスのときだけ受け付ける"""
    root, wt = _repo(tmp_path / "repo")
    (tmp_path / "afile").write_text("x", encoding="utf-8")
    link = tmp_path / "link-to-wt"
    link.symlink_to(wt)
    for recorded in [
        str(tmp_path / "missing"),  # 存在しない
        str(tmp_path / "afile"),  # ディレクトリでない
        str(link),  # 今の checkout を別の文字列で指す
        ".",
        "sub",  # 相対パス
        "/x\u0000y",  # stat が ValueError を出す
    ]:
        path = _write_marker(wt, _frontmatter(f"project_root: {json.dumps(recorded)}\n"))
        before = path.read_bytes()
        r = _run(wt, "SESSION-B")
        assert r.returncode == 1, recorded
        assert LOCK in r.stderr, recorded
        assert path.read_bytes() == before, recorded


def test_hardlinked_marker_still_locks_and_owner_unchanged(tmp_path):
    root, wt = _repo(tmp_path)
    assert _run(root, "SESSION-A").returncode == 0
    before = _marker(root).read_bytes()
    (wt / ".claude").mkdir(parents=True, exist_ok=True)
    os.link(_marker(root), _marker(wt))
    r = _run(wt, "SESSION-B")
    assert r.returncode == 1
    assert LOCK in r.stderr
    assert _marker(root).read_bytes() == before


# --- 判定できないときに通らない -------------------------------------------


def test_outside_git_with_project_root_still_locks(tmp_path):
    _write_marker(tmp_path, _frontmatter('project_root: "/somewhere/else"\n'))
    r = _run(tmp_path, "SESSION-B")
    assert r.returncode == 1
    assert LOCK in r.stderr


def test_failing_git_still_locks(tmp_path):
    root, wt = _repo(tmp_path / "repo")
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    fake = bin_dir / "git"
    fake.write_text("#!/bin/sh\nexit 128\n", encoding="utf-8")
    fake.chmod(0o755)
    _write_marker(wt, _frontmatter(f"project_root: {json.dumps(str(root))}\n"))
    r = _run(wt, "SESSION-B", env_extra={"PATH": f"{bin_dir}:{os.environ['PATH']}"})
    assert r.returncode == 1
    assert LOCK in r.stderr


def test_toplevel_ending_with_newline_still_locks(tmp_path):
    """名前が改行で終わる checkout では、setup は改行を落としたパスの marker を読む。
    toplevel と比べられないので、写しとして扱わない"""
    root, _ = _repo(tmp_path, "r\n")
    assert _toplevel(root).endswith("\n")
    stripped = Path(str(root)[:-1])
    _write_marker(stripped, _frontmatter('project_root: "/somewhere/else"\n'))
    r = _run(root, "SESSION-B")
    assert r.returncode == 1
    assert LOCK in r.stderr
    assert COPIED not in r.stderr


def test_symlinked_marker_still_locks_and_owner_unchanged(tmp_path):
    root, wt = _repo(tmp_path)
    assert _run(root, "SESSION-A").returncode == 0
    before = _marker(root).read_text(encoding="utf-8")
    (wt / ".claude").mkdir(parents=True, exist_ok=True)
    _marker(wt).symlink_to(_marker(root))
    r = _run(wt, "SESSION-B")
    assert r.returncode == 1
    assert LOCK in r.stderr
    assert _marker(root).read_text(encoding="utf-8") == before


def test_symlinked_state_dir_still_locks_and_owner_unchanged(tmp_path):
    root, wt = _repo(tmp_path)
    assert _run(root, "SESSION-A").returncode == 0
    before = _marker(root).read_text(encoding="utf-8")
    shutil.rmtree(wt / ".claude", ignore_errors=True)
    (wt / ".claude").symlink_to(root / ".claude")
    r = _run(wt, "SESSION-B")
    assert r.returncode == 1
    assert LOCK in r.stderr
    assert _marker(root).read_text(encoding="utf-8") == before


# --- 例外で guard が落ちない（止める側に倒れる）------------------------------


def test_non_utf8_marker_stops_without_overwriting(tmp_path):
    root, wt = _repo(tmp_path)
    path = _marker(wt)
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = _frontmatter(f"project_root: {json.dumps(str(root))}\n").encode() + b"\xff\xfe\n"
    path.write_bytes(raw)
    r = _run(wt, "SESSION-B")
    assert r.returncode != 0
    assert path.read_bytes() == raw
