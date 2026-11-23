# test_setup_gdd_loop_session_lock.py
# setup-gdd-loop.sh: stale state file (active: false) が別セッションからの起動をブロックしないことを検証する
import os
import subprocess
from pathlib import Path

from _paths import PLUGIN_ROOT
SCRIPT = PLUGIN_ROOT / "scripts" / "setup-gdd-loop.sh"


def _run(tmp_path: Path, session_id: str) -> subprocess.CompletedProcess:
    # ロックの分岐は transcript を読むので、実際の ~/.claude/projects を走査しないよう空の場所を指す
    env = {**os.environ, "CLAUDE_CODE_SESSION_ID": session_id, "CLAUDE_CONFIG_DIR": str(tmp_path / "no-claude-config")}
    return subprocess.run(
        ["bash", str(SCRIPT), "test intent"],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
    )


def _write_state(tmp_path: Path, active: str, session_id: str) -> None:
    state_dir = tmp_path / ".claude"
    state_dir.mkdir(parents=True, exist_ok=True)
    (state_dir / "gdd-dev.local.md").write_text(
        f"---\nactive: {active}\nsession_id: {session_id}\n---\nbody\n",
        encoding="utf-8",
    )


def test_active_true_mismatched_session_blocks(tmp_path):
    """active: true かつ session_id 不一致なら従来通りブロックする"""
    _write_state(tmp_path, active="true", session_id="OLD-SESSION")
    r = _run(tmp_path, session_id="NEW-SESSION")
    assert r.returncode == 1
    assert "already active in another session" in r.stderr


def test_active_false_mismatched_session_does_not_block(tmp_path):
    """active: false（手動 disable 済みの stale marker）は session_id が不一致でもブロックしない"""
    _write_state(tmp_path, active="false", session_id="OLD-SESSION")
    r = _run(tmp_path, session_id="NEW-SESSION")
    assert "already active in another session" not in r.stderr
    assert r.returncode == 0


def test_no_state_file_does_not_block(tmp_path):
    """state file が存在しない初回起動はブロックされない"""
    r = _run(tmp_path, session_id="NEW-SESSION")
    assert "already active in another session" not in r.stderr
    assert r.returncode == 0


def test_active_true_same_session_does_not_block(tmp_path):
    """active: true でも session_id が一致していれば同一セッションの再実行としてブロックしない"""
    _write_state(tmp_path, active="true", session_id="SAME-SESSION")
    r = _run(tmp_path, session_id="SAME-SESSION")
    assert "already active in another session" not in r.stderr
    assert r.returncode == 0


def test_active_true_case_insensitive_mismatched_session_blocks(tmp_path):
    """active: True / TRUE 等の表記揺れも gdd-active-check.sh 同様に大文字小文字を無視してブロックする"""
    _write_state(tmp_path, active="True", session_id="OLD-SESSION")
    r = _run(tmp_path, session_id="NEW-SESSION")
    assert r.returncode == 1
    assert "already active in another session" in r.stderr


def test_active_true_no_frontmatter_delimiter_mismatched_session_blocks(tmp_path):
    """gdd-dev.md のフォールバック手順で作られる、`---` 区切りなしの state file も検知する"""
    state_dir = tmp_path / ".claude"
    state_dir.mkdir(parents=True, exist_ok=True)
    (state_dir / "gdd-dev.local.md").write_text(
        "active: true\nsession_id: OLD-SESSION\n",
        encoding="utf-8",
    )
    r = _run(tmp_path, session_id="NEW-SESSION")
    assert r.returncode == 1
    assert "already active in another session" in r.stderr


def test_active_true_inline_comment_mismatched_session_blocks(tmp_path):
    """`active: true  # メモ` のような行末コメント付きでも値を正しく判定する"""
    state_dir = tmp_path / ".claude"
    state_dir.mkdir(parents=True, exist_ok=True)
    (state_dir / "gdd-dev.local.md").write_text(
        "---\nactive: true  # 手動再開時にメモを残した\nsession_id: OLD-SESSION\n---\nbody\n",
        encoding="utf-8",
    )
    r = _run(tmp_path, session_id="NEW-SESSION")
    assert r.returncode == 1
    assert "already active in another session" in r.stderr


def test_active_false_frontmatter_not_overridden_by_later_body_line(tmp_path):
    """frontmatter が active: false でも、本文中に active: true 行があると最後の出現で上書きされ誤ブロックする懸念に対する回帰テスト"""
    state_dir = tmp_path / ".claude"
    state_dir.mkdir(parents=True, exist_ok=True)
    (state_dir / "gdd-dev.local.md").write_text(
        "---\nactive: false\nsession_id: OLD-SESSION\n---\n"
        "active: true\n",
        encoding="utf-8",
    )
    r = _run(tmp_path, session_id="NEW-SESSION")
    assert "already active in another session" not in r.stderr
    assert r.returncode == 0


def test_lock_message_names_the_way_out(tmp_path):
    """ロックで止めたとき、抜け方（ユーザーに確かめて active: false にする。session_id は書き換えない）を出す"""
    _write_state(tmp_path, active="true", session_id="OLD-SESSION")
    r = _run(tmp_path, session_id="NEW-SESSION")
    assert r.returncode == 1
    assert "ask the user whether the existing session is still running" in r.stderr
    assert r.stderr.index("ask the user") < r.stderr.index("'active:' line in the state file to false")
    assert "Do not rewrite session_id." in r.stderr
    # 抜け方の後も、state file は書き換えていない（判定は変えない）
    text = (tmp_path / ".claude" / "gdd-dev.local.md").read_text(encoding="utf-8")
    assert "active: true" in text and "OLD-SESSION" in text
