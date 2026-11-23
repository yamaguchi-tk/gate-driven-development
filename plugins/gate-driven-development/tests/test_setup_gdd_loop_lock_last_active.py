# test_setup_gdd_loop_lock_last_active.py
# setup-gdd-loop.sh: 別の session の active な marker でロックするとき、持ち主の session の
# transcript（Claude Code の projects/*/<session_id>.jsonl）の最後の記録の時刻をメッセージに出すこと。
# 時刻を確かに読めないときは unknown と出し、どの場合もロックのまま（exit 1・marker を変えない）であること。
from __future__ import annotations

import datetime
import json
import os
import subprocess
from pathlib import Path

import pytest

from _paths import PLUGIN_ROOT

SCRIPT = PLUGIN_ROOT / "scripts" / "setup-gdd-loop.sh"
LOCK = "already active in another session"
LAST = "Existing session last active:"
MARKER = "---\nactive: true\nsession_id: {sid}\n---\nbody\n"


def _repo(base: Path) -> Path:
    root = base / "root"
    root.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    return root


def _write_marker(root: Path, sid: str) -> Path:
    path = root / ".claude" / "gdd-dev.local.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(MARKER.format(sid=sid), encoding="utf-8")
    return path


def _transcript(config: Path, project: str, sid: str, lines: list[str]) -> Path:
    path = config / "projects" / project / f"{sid}.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(line + "\n" for line in lines), encoding="utf-8")
    return path


def _rec(ts: str) -> str:
    return '{"type":"assistant","timestamp":"%s","message":{"content":[]}}' % ts


def _run(root: Path, home: Path, env_extra=None):
    env = {k: v for k, v in os.environ.items() if k != "CLAUDE_CONFIG_DIR"}
    env.update({"HOME": str(home), "CLAUDE_CODE_SESSION_ID": "NEW-SESSION", **(env_extra or {})})
    return subprocess.run(
        ["bash", str(SCRIPT), "test intent"], cwd=root, env=env,
        capture_output=True, text=True,
    )


def _assert_locked(r, marker: Path, sid: str):
    assert r.returncode == 1, r.stderr
    assert LOCK in r.stderr
    assert marker.read_text(encoding="utf-8") == MARKER.format(sid=sid)


def _last_line(stderr: str) -> str:
    lines = [l for l in stderr.splitlines() if l.startswith(LAST)]
    assert len(lines) == 1, stderr
    return lines[0]


def _hours_ago(hours: float) -> str:
    seen = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=hours)
    return seen.strftime("%Y-%m-%dT%H:%M:%S.000Z")


def test_lock_shows_owner_last_activity(tmp_path):
    root, home = _repo(tmp_path), tmp_path / "home"
    marker = _write_marker(root, "OLD-SESSION")
    ts = _hours_ago(5.5)
    # 新しい記録を先に置く（最後に当たった値ではなく、最大値を採ること）
    _transcript(home / ".claude", "-p", "OLD-SESSION", [_rec(ts), _rec(_hours_ago(30.5))])
    r = _run(root, home)
    _assert_locked(r, marker, "OLD-SESSION")
    assert _last_line(r.stderr).startswith(f"{LAST} {ts} (5h ago; local time ")


def test_lock_reads_json_with_spaces_and_only_top_level_timestamp(tmp_path):
    root, home = _repo(tmp_path), tmp_path / "home"
    marker = _write_marker(root, "OLD-SESSION")
    ts = _hours_ago(2.5)
    record = {"type": "user", "timestamp": ts, "message": {"timestamp": "2099-01-01T00:00:00Z"}}
    _transcript(home / ".claude", "-p", "OLD-SESSION", [json.dumps(record)])
    r = _run(root, home)
    _assert_locked(r, marker, "OLD-SESSION")
    assert _last_line(r.stderr).startswith(f"{LAST} {ts} (2h ago; local time ")


@pytest.mark.parametrize("newer", ["-a", "-z"])
def test_lock_uses_latest_across_project_dirs(tmp_path, newer):
    # 新しい方を名前の先・後の両方に置く（dir を読む順によらず最大値を採ること）
    root, home = _repo(tmp_path), tmp_path / "home"
    marker = _write_marker(root, "OLD-SESSION")
    older = "-z" if newer == "-a" else "-a"
    _transcript(home / ".claude", older, "OLD-SESSION", [_rec("2026-10-02T00:00:00Z")])
    _transcript(home / ".claude", newer, "OLD-SESSION", [_rec("2026-10-09T08:00:00Z")])
    _transcript(home / ".claude", "-m", "OLD-SESSION", [_rec("2026-10-05T00:00:00Z")])
    r = _run(root, home)
    _assert_locked(r, marker, "OLD-SESSION")
    assert "2026-10-09T08:00:00" in _last_line(r.stderr)


def test_lock_respects_claude_config_dir(tmp_path):
    root, home, config = _repo(tmp_path), tmp_path / "home", tmp_path / "cfg"
    marker = _write_marker(root, "OLD-SESSION")
    _transcript(home / ".claude", "-p", "OLD-SESSION", [_rec("2026-09-01T00:00:00Z")])
    _transcript(config, "-p", "OLD-SESSION", [_rec("2026-10-07T00:00:00Z")])
    r = _run(root, home, {"CLAUDE_CONFIG_DIR": str(config)})
    _assert_locked(r, marker, "OLD-SESSION")
    assert "2026-10-07T00:00:00" in _last_line(r.stderr)


def test_lock_ignores_home_when_claude_config_dir_is_set(tmp_path):
    # HOME の側が新しくても、CLAUDE_CONFIG_DIR があればそちらだけを読む
    root, home, config = _repo(tmp_path), tmp_path / "home", tmp_path / "cfg"
    marker = _write_marker(root, "OLD-SESSION")
    _transcript(home / ".claude", "-p", "OLD-SESSION", [_rec("2026-10-12T00:00:00Z")])
    _transcript(config, "-p", "OLD-SESSION", [_rec("2026-10-03T00:00:00Z")])
    r = _run(root, home, {"CLAUDE_CONFIG_DIR": str(config)})
    _assert_locked(r, marker, "OLD-SESSION")
    assert "2026-10-03T00:00:00" in _last_line(r.stderr)


def test_lock_reads_only_last_mib_of_large_transcript(tmp_path):
    # 先頭の新しい時刻は 1 MiB より前にあるので読まず、末尾の最大値を採る
    root, home = _repo(tmp_path), tmp_path / "home"
    marker = _write_marker(root, "OLD-SESSION")
    pad = json.dumps({"type": "user", "timestamp": "2026-10-01T00:00:00Z", "message": {"content": "x" * 1000}})
    lines = [_rec("2026-10-11T00:00:00Z")] + [pad] * 1200 + [_rec("2026-10-06T00:00:00Z"), pad]
    _transcript(home / ".claude", "-p", "OLD-SESSION", lines)
    r = _run(root, home)
    _assert_locked(r, marker, "OLD-SESSION")
    assert "2026-10-06T00:00:00" in _last_line(r.stderr)


def test_lock_ignores_nested_timestamp_placed_before_top_level(tmp_path):
    root, home = _repo(tmp_path), tmp_path / "home"
    marker = _write_marker(root, "OLD-SESSION")
    ts = _hours_ago(3.5)
    record = '{"message":{"timestamp":"2099-01-01T00:00:00Z"},"type":"user","timestamp":"%s"}' % ts
    _transcript(home / ".claude", "-p", "OLD-SESSION", [record])
    r = _run(root, home)
    _assert_locked(r, marker, "OLD-SESSION")
    assert _last_line(r.stderr).startswith(f"{LAST} {ts} (3h ago; local time ")


def test_lock_reads_record_containing_line_separator(tmp_path):
    # U+2028 は JSON の文字列の中に生のまま置ける。行の区切りは \n だけにすること
    root, home = _repo(tmp_path), tmp_path / "home"
    marker = _write_marker(root, "OLD-SESSION")
    record = json.dumps({"type": "user", "timestamp": "2026-10-10T00:00:00Z", "message": {"content": "a\u2028b"}}, ensure_ascii=False)
    assert "\u2028" in record
    _transcript(home / ".claude", "-p", "OLD-SESSION", [_rec("2026-10-02T00:00:00Z"), record])
    r = _run(root, home)
    _assert_locked(r, marker, "OLD-SESSION")
    assert "2026-10-10T00:00:00" in _last_line(r.stderr)


def test_lock_skips_invalid_dates_and_keeps_valid_ones(tmp_path):
    root, home = _repo(tmp_path), tmp_path / "home"
    marker = _write_marker(root, "OLD-SESSION")
    _transcript(home / ".claude", "-p", "OLD-SESSION", [
        _rec("2026-10-08T00:00:00Z"),
        _rec("2026-13-45T00:00:00Z"),
        _rec("\uff12\uff10\uff12\uff16-10-30T00:00:00Z"),
    ])
    r = _run(root, home)
    _assert_locked(r, marker, "OLD-SESSION")
    assert "2026-10-08T00:00:00" in _last_line(r.stderr)


def test_lock_compares_fraction_within_same_second(tmp_path):
    root, home = _repo(tmp_path), tmp_path / "home"
    marker = _write_marker(root, "OLD-SESSION")
    _transcript(home / ".claude", "-p", "OLD-SESSION", [
        # 小さい方を先に置く（秒で切って比べると、先に当たった .100 が残る）
        _rec("2026-10-08T00:00:00.100Z"),
        _rec("2026-10-08T00:00:00.9Z"),
    ])
    r = _run(root, home)
    _assert_locked(r, marker, "OLD-SESSION")
    assert _last_line(r.stderr).startswith(f"{LAST} 2026-10-08T00:00:00.9Z (")


def test_lock_future_timestamp_is_not_negative(tmp_path):
    root, home = _repo(tmp_path), tmp_path / "home"
    marker = _write_marker(root, "OLD-SESSION")
    ts = _hours_ago(-2.5)
    _transcript(home / ".claude", "-p", "OLD-SESSION", [_rec(ts)])
    r = _run(root, home)
    _assert_locked(r, marker, "OLD-SESSION")
    assert _last_line(r.stderr).startswith(f"{LAST} {ts} (in the future; local time "), r.stderr


def test_lock_under_one_hour_shows_minutes(tmp_path):
    root, home = _repo(tmp_path), tmp_path / "home"
    marker = _write_marker(root, "OLD-SESSION")
    ts = _hours_ago(25.5 / 60)
    _transcript(home / ".claude", "-p", "OLD-SESSION", [_rec(ts)])
    r = _run(root, home)
    _assert_locked(r, marker, "OLD-SESSION")
    assert _last_line(r.stderr).startswith(f"{LAST} {ts} (25m ago; local time "), r.stderr


def test_lock_shows_local_time(tmp_path):
    root, home = _repo(tmp_path), tmp_path / "home"
    marker = _write_marker(root, "OLD-SESSION")
    _transcript(home / ".claude", "-p", "OLD-SESSION", [_rec("2026-10-08T00:00:00Z")])
    r = _run(root, home, {"TZ": "Asia/Tokyo"})
    _assert_locked(r, marker, "OLD-SESSION")
    assert _last_line(r.stderr).endswith("; local time 2026-10-08 09:00 JST)"), r.stderr


def test_lock_without_transcript_adds_started_at_as_lower_bound(tmp_path):
    root, home = _repo(tmp_path), tmp_path / "home"
    path = root / ".claude" / "gdd-dev.local.md"
    path.parent.mkdir(parents=True)
    text = '---\nactive: true\nsession_id: OLD-SESSION\nstarted_at: "2026-10-01T00:00:00Z"\n---\nbody\n'
    path.write_text(text, encoding="utf-8")
    r = _run(root, home)
    assert r.returncode == 1 and LOCK in r.stderr
    assert path.read_text(encoding="utf-8") == text
    assert _last_line(r.stderr) == f"{LAST} unknown (state started_at: 2026-10-01T00:00:00Z; active at least since then)"


def test_lock_asks_to_show_last_active_line(tmp_path):
    root, home = _repo(tmp_path), tmp_path / "home"
    marker = _write_marker(root, "OLD-SESSION")
    r = _run(root, home)
    _assert_locked(r, marker, "OLD-SESSION")
    guide = [l for l in r.stderr.splitlines() if l.startswith("To continue:")]
    assert len(guide) == 1 and "'Existing session last active'" in guide[0], r.stderr


def test_lock_without_transcript_says_unknown(tmp_path):
    root, home = _repo(tmp_path), tmp_path / "home"
    marker = _write_marker(root, "OLD-SESSION")
    r = _run(root, home)
    _assert_locked(r, marker, "OLD-SESSION")
    assert "unknown" in _last_line(r.stderr)


def test_lock_with_transcript_without_timestamp_says_unknown(tmp_path):
    root, home = _repo(tmp_path), tmp_path / "home"
    marker = _write_marker(root, "OLD-SESSION")
    _transcript(home / ".claude", "-p", "OLD-SESSION", ['{"type":"summary"}', "not json"])
    r = _run(root, home)
    _assert_locked(r, marker, "OLD-SESSION")
    assert "unknown" in _last_line(r.stderr)


@pytest.mark.parametrize("sid", ["../-p/OLD-SESSION", "../OLD-SESSION", "OLD*", "OLD?SESSION", "[O]LD-SESSION"])
def test_session_id_with_path_or_glob_chars_does_not_match_other_transcript(tmp_path, sid):
    root, home = _repo(tmp_path), tmp_path / "home"
    marker = _write_marker(root, sid)
    # "../-p/OLD-SESSION" と "../OLD-SESSION" は、許可リストが無ければ辿った先に実在するファイルに当たる
    _transcript(home / ".claude", "-p", "OLD-SESSION", [_rec("2026-10-04T15:05:12Z")])
    (home / ".claude" / "projects" / "OLD-SESSION.jsonl").write_text(_rec("2026-10-04T15:05:12Z") + "\n", encoding="utf-8")
    r = _run(root, home)
    _assert_locked(r, marker, sid)
    assert "unknown" in _last_line(r.stderr)
    assert "2026-10-04T15:05:12" not in r.stderr


def test_transcript_path_that_is_a_directory_says_unknown(tmp_path):
    root, home = _repo(tmp_path), tmp_path / "home"
    marker = _write_marker(root, "OLD-SESSION")
    (home / ".claude" / "projects" / "-p" / "OLD-SESSION.jsonl").mkdir(parents=True)
    r = _run(root, home)
    _assert_locked(r, marker, "OLD-SESSION")
    assert "unknown" in _last_line(r.stderr)


@pytest.mark.skipif(hasattr(os, "geteuid") and os.geteuid() == 0, reason="root は chmod 000 を読める")
def test_unreadable_transcript_says_unknown(tmp_path):
    root, home = _repo(tmp_path), tmp_path / "home"
    marker = _write_marker(root, "OLD-SESSION")
    path = _transcript(home / ".claude", "-p", "OLD-SESSION", [_rec("2026-10-04T15:05:12Z")])
    path.chmod(0)
    try:
        r = _run(root, home)
    finally:
        path.chmod(0o600)
    _assert_locked(r, marker, "OLD-SESSION")
    assert "unknown" in _last_line(r.stderr)


def test_unset_home_still_locks(tmp_path):
    root = _repo(tmp_path)
    marker = _write_marker(root, "OLD-SESSION")
    env = {k: v for k, v in os.environ.items() if k not in ("HOME", "CLAUDE_CONFIG_DIR")}
    env["CLAUDE_CODE_SESSION_ID"] = "NEW-SESSION"
    r = subprocess.run(["bash", str(SCRIPT), "test intent"], cwd=root, env=env, capture_output=True, text=True)
    _assert_locked(r, marker, "OLD-SESSION")
    assert "unknown" in _last_line(r.stderr)
