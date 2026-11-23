# test_root_branch_guard_session_owner.py
# validate-worktree-command.py の root-branch guard: root の `active: true` の marker で止めるのは、
# marker の持ち主の session だけにすること。今の session id は hook の payload の session_id から取り、
# 照合を緩めるのは、hook のプロセスの環境変数 CLAUDE_CODE_SESSION_ID が payload の id と一致するとき
# （Claude Code の hook）だけにする。環境変数を継いだ別の runtime では payload と合わないので止める。
# 照合できないとき（id が取れない・形が外れる・marker の session_id が空か frontmatter に無い・例外）は
# 今までどおり止め、marker が読めないとき（前は通していた）も止めること。
# 抜け方: 持ち主がもう動いていないことをユーザーに確かめてから、marker を active: false にする。
# 読めない marker は、通常のファイルに戻すか、`.claude/` と marker の権限を直す。
from __future__ import annotations

import importlib.util
import io
import json
import os
import subprocess
from pathlib import Path

import pytest

from _paths import PLUGIN_ROOT
from _root_branch_guard_support import init_git_repo, run_root_branch_guard_raw

HOOK = PLUGIN_ROOT / "hooks" / "scripts" / "validate-worktree-command.py"
COMMAND = "git checkout -b feature-x"


def _repo(tmp_path: Path) -> Path:
    root = tmp_path / "root"
    root.mkdir()
    init_git_repo(root)
    return root


def _marker(root: Path, text: str) -> None:
    state = root / ".claude"
    state.mkdir(exist_ok=True)
    (state / "gdd-dev.local.md").write_text(text, encoding="utf-8")


def _owned_by(sid: str) -> str:
    return f"---\nactive: true\nsession_id: {sid}\n---\nbody\n"


def _payload(cwd: Path, command: str = COMMAND, **extra) -> dict:
    return {"tool_name": "Bash", "tool_input": {"command": command, "cwd": str(cwd)}, **extra}


def _run(payload: dict, extra_env=None, env_from_payload: bool = True):
    """hook を起動する。既定では Claude Code の hook と同じく、環境変数 CLAUDE_CODE_SESSION_ID を
    payload の session_id（文字列のとき）にそろえる。そろえないと照合の前に「照合できない」で止まり、
    frontmatter の読み方や持ち主との一致を確かめられない。`extra_env` はこの既定より優先する。
    """
    env = {}
    sid = payload.get("session_id")
    if env_from_payload and isinstance(sid, str):
        env["CLAUDE_CODE_SESSION_ID"] = sid
    env.update(extra_env or {})
    return run_root_branch_guard_raw(json.dumps(payload).encode(), extra_env=env)


def _denied(r) -> bool:
    return r.returncode == 2 and b"Blocked GDD root branch creation" in r.stderr


def _allowed(r) -> bool:
    return r.returncode == 0 and b"deny" not in r.stdout + r.stderr


# --- 緩める側（別の session の marker では止めない） -------------------------


def test_other_sessions_marker_does_not_block(tmp_path):
    root = _repo(tmp_path)
    _marker(root, _owned_by("OWNER"))
    assert _allowed(_run(_payload(root, session_id="OTHER")))


def test_other_sessions_marker_does_not_block_via_git_c(tmp_path):
    root = _repo(tmp_path)
    _marker(root, _owned_by("OWNER"))
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    assert _allowed(_run(_payload(elsewhere, f"git -C {root} checkout -b feature-x", session_id="OTHER")))


# --- 止める側（持ち主・照合できないとき） -------------------------------------


def test_owner_session_is_still_blocked(tmp_path):
    root = _repo(tmp_path)
    _marker(root, _owned_by("OWNER"))
    assert _denied(_run(_payload(root, session_id="OWNER")))


def test_owner_session_is_still_blocked_via_git_c(tmp_path):
    root = _repo(tmp_path)
    _marker(root, _owned_by("OWNER"))
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    assert _denied(_run(_payload(elsewhere, f"git -C {root} checkout -b feature-x", session_id="OWNER")))


def test_payload_without_session_id_is_blocked(tmp_path):
    root = _repo(tmp_path)
    _marker(root, _owned_by("OWNER"))
    assert _denied(_run(_payload(root)))


def test_env_alone_without_payload_id_is_blocked(tmp_path):
    root = _repo(tmp_path)
    _marker(root, _owned_by("OWNER"))
    assert _denied(_run(_payload(root), extra_env={"CLAUDE_CODE_SESSION_ID": "OTHER"}))


@pytest.mark.parametrize("value", [None, "", "   ", 123, ["OTHER"], {"id": "OTHER"}])
def test_unusable_payload_session_id_is_blocked(tmp_path, value):
    root = _repo(tmp_path)
    _marker(root, _owned_by("OWNER"))
    assert _denied(_run(_payload(root, session_id=value)))


@pytest.mark.parametrize(
    "text",
    [
        "---\nactive: true\nsession_id:\n---\n",
        "---\nactive: true\nsession_id:   \n---\n",
        "---\nactive: true\n---\n",
        # frontmatter の外にだけある値は読まない
        "---\nactive: true\n---\nsession_id: OWNER\n",
        # frontmatter の区切りが無い
        "active: true\nsession_id: OWNER\n",
        # 閉じの区切りが無い
        "---\nactive: true\nsession_id: OWNER\n",
    ],
)
def test_marker_without_usable_session_id_is_blocked(tmp_path, text):
    root = _repo(tmp_path)
    _marker(root, text)
    assert _denied(_run(_payload(root, session_id="OTHER")))


def test_two_session_id_lines_in_frontmatter_are_blocked(tmp_path):
    # どちらの値で照合しても別の session になる payload でも、あいまいな marker では止める
    root = _repo(tmp_path)
    _marker(root, "---\nactive: true\nsession_id: OWNER\nsession_id: OTHER\n---\n")
    assert _denied(_run(_payload(root, session_id="THIRD")))


def test_body_session_id_does_not_override_frontmatter(tmp_path):
    # 本文の値を読むと持ち主が別の session に見えて通ってしまう
    root = _repo(tmp_path)
    _marker(root, "---\nactive: true\nsession_id: OWNER\n---\nUser intent:\nsession_id: OTHER\n")
    assert _denied(_run(_payload(root, session_id="OWNER")))


def test_gdd_named_branch_is_blocked_regardless_of_session(tmp_path):
    root = _repo(tmp_path)
    _marker(root, _owned_by("OWNER"))
    r = _run(_payload(root, "git checkout -b claude/20261014-task", session_id="OTHER"))
    assert _denied(r)


def test_inactive_marker_still_allows(tmp_path):
    root = _repo(tmp_path)
    _marker(root, "---\nactive: false\nsession_id: OWNER\n---\n")
    assert _allowed(_run(_payload(root, session_id="OTHER")))


# --- 例外で guard 全体が落ちない --------------------------------------------


def _load_hook():
    spec = importlib.util.spec_from_file_location("vwc_session_owner", HOOK)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_exception_while_matching_session_is_denied(tmp_path, monkeypatch, capsys):
    root = _repo(tmp_path)
    _marker(root, _owned_by("OWNER"))
    module = _load_hook()

    def boom(text):
        raise RuntimeError("boom")

    monkeypatch.setattr(module, "frontmatter_session_id", boom)
    monkeypatch.setenv("CLAUDE_CODE_SESSION_ID", "OTHER")
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(_payload(root, session_id="OTHER"))))
    assert module.main() == 2
    assert "Blocked GDD root branch creation" in capsys.readouterr().err


# --- id の形でない値は照合できないとして止める -------------------------------


@pytest.mark.parametrize(
    "owner_line",
    ['session_id: "OWNER"', "session_id: OWNER # note", "session_id: OWN ER"],
)
def test_owner_id_outside_allowed_shape_is_blocked(tmp_path, owner_line):
    root = _repo(tmp_path)
    _marker(root, f"---\nactive: true\n{owner_line}\n---\n")
    assert _denied(_run(_payload(root, session_id="OTHER")))


def test_trailing_cr_on_owner_line_is_stripped_like_parse_state(tmp_path):
    # parse_state は値を strip して OWNER と読むので、別の session は通し、持ち主は止める
    root = _repo(tmp_path)
    _marker(root, "---\nactive: true\nsession_id: OWNER\r\n---\n")
    assert _allowed(_run(_payload(root, session_id="OTHER")))
    assert _denied(_run(_payload(root, session_id="OWNER")))


def test_owner_id_with_undecodable_bytes_is_blocked(tmp_path):
    root = _repo(tmp_path)
    state = root / ".claude"
    state.mkdir()
    (state / "gdd-dev.local.md").write_bytes(b"---\nactive: true\nsession_id: OWN\xffER\n---\n")
    assert _denied(_run(_payload(root, session_id="OTHER")))


@pytest.mark.parametrize("value", ["served:OTHER", "served:unknown", "OTHER x", "OTHER\n", "ＯＴＨＥＲ"])
def test_payload_id_outside_allowed_shape_is_blocked(tmp_path, value):
    root = _repo(tmp_path)
    _marker(root, _owned_by("OWNER"))
    assert _denied(_run(_payload(root, session_id=value)))


# --- frontmatter の読み方を parse_state とそろえる ---------------------------


@pytest.mark.parametrize(
    "text",
    [
        # parse_state は行を strip して後勝ちで読むので、持ち主は OTHER になる
        "---\nactive: true\nsession_id: OWNER\n  session_id: OTHER\n---\n",
        "---\nactive: true\nsession_id: OWNER\nsession_id : OTHER\n---\n",
    ],
)
def test_frontmatter_read_like_parse_state_blocks_ambiguous_owner(tmp_path, text):
    root = _repo(tmp_path)
    _marker(root, text)
    assert _denied(_run(_payload(root, session_id="OTHER")))


def test_unicode_line_separator_does_not_split_frontmatter_lines(tmp_path):
    # U+2028 は行の区切りではない（parse_state は `\n` だけで分ける）。session_id の行は無いので止める
    root = _repo(tmp_path)
    _marker(root, "---\nactive: true\nnote: x\u2028session_id: OTHER\n---\n")
    assert _denied(_run(_payload(root, session_id="THIRD")))


def test_indented_single_session_id_line_is_read(tmp_path):
    # parse_state と同じく、行頭の空白は落として読む
    root = _repo(tmp_path)
    _marker(root, "---\nactive: true\n  session_id: OWNER\n---\n")
    assert _allowed(_run(_payload(root, session_id="OTHER")))
    assert _denied(_run(_payload(root, session_id="OWNER")))


# --- marker があるのに読めないときは止める -----------------------------------


def test_marker_that_is_a_directory_is_blocked(tmp_path):
    root = _repo(tmp_path)
    (root / ".claude" / "gdd-dev.local.md").mkdir(parents=True)
    assert _denied(_run(_payload(root, session_id="OTHER")))


def test_marker_that_is_a_broken_symlink_is_blocked(tmp_path):
    root = _repo(tmp_path)
    (root / ".claude").mkdir()
    (root / ".claude" / "gdd-dev.local.md").symlink_to(tmp_path / "missing")
    assert _denied(_run(_payload(root, session_id="OTHER")))


def test_marker_that_is_a_fifo_is_blocked_without_reading(tmp_path):
    root = _repo(tmp_path)
    (root / ".claude").mkdir()
    os.mkfifo(root / ".claude" / "gdd-dev.local.md")
    assert _denied(_run(_payload(root, session_id="OTHER")))


@pytest.mark.skipif(hasattr(os, "geteuid") and os.geteuid() == 0, reason="root は chmod 000 を読める")
def test_unreadable_marker_is_blocked(tmp_path):
    root = _repo(tmp_path)
    _marker(root, _owned_by("OWNER"))
    path = root / ".claude" / "gdd-dev.local.md"
    path.chmod(0)
    try:
        assert _denied(_run(_payload(root, session_id="OTHER")))
    finally:
        path.chmod(0o600)


def test_missing_marker_still_allows(tmp_path):
    root = _repo(tmp_path)
    assert _allowed(_run(_payload(root, session_id="OTHER")))


@pytest.mark.skipif(hasattr(os, "geteuid") and os.geteuid() == 0, reason="root は検索権が無くても読める")
def test_marker_under_unsearchable_state_dir_is_blocked(tmp_path):
    # `.claude/` に x が無いと、state を開くと EACCES になる。「無い」と読んで通さない
    root = _repo(tmp_path)
    _marker(root, _owned_by("OWNER"))
    state = root / ".claude"
    state.chmod(0o600)
    try:
        assert _denied(_run(_payload(root, session_id="OTHER")))
    finally:
        state.chmod(0o700)


# --- 環境変数と payload の id が一致するときだけ緩める ------------------------


def test_payload_without_matching_env_is_blocked(tmp_path):
    # 環境変数が無い runtime（Claude Code 以外）では、payload に id があっても緩めない
    root = _repo(tmp_path)
    _marker(root, _owned_by("OWNER"))
    assert _denied(_run(_payload(root, session_id="OTHER"), env_from_payload=False))


def test_inherited_env_of_owner_blocks_even_with_other_payload_id(tmp_path):
    # 持ち主の Claude Code から環境変数を継いだ別の runtime: payload の id は別でも、持ち主自身なので止める
    root = _repo(tmp_path)
    _marker(root, _owned_by("OWNER"))
    assert _denied(_run(_payload(root, session_id="OTHER"), extra_env={"CLAUDE_CODE_SESSION_ID": "OWNER"}))


def test_env_and_payload_disagreeing_is_blocked(tmp_path):
    root = _repo(tmp_path)
    _marker(root, _owned_by("OWNER"))
    assert _denied(_run(_payload(root, session_id="OTHER"), extra_env={"CLAUDE_CODE_SESSION_ID": "THIRD"}))


@pytest.mark.parametrize("env_value", ["", "   ", "OTHER ", "served:OTHER", "OTHER x"])
def test_env_outside_allowed_shape_is_blocked(tmp_path, env_value):
    root = _repo(tmp_path)
    _marker(root, _owned_by("OWNER"))
    assert _denied(_run(_payload(root, session_id="OTHER"), extra_env={"CLAUDE_CODE_SESSION_ID": env_value}))


def test_env_matching_payload_but_equal_to_owner_is_blocked(tmp_path):
    root = _repo(tmp_path)
    _marker(root, _owned_by("OWNER"))
    assert _denied(_run(_payload(root, session_id="OWNER")))


# --- deny の文と、setup-gdd-loop.sh が書いた marker -------------------------


def test_state_deny_says_how_to_release_the_state(tmp_path):
    # state で止めたときは、抜け方（持ち主が動いていなければ active: false）を文に出す
    root = _repo(tmp_path)
    _marker(root, "---\nactive: true\nsession_id: \n---\nbody\n")
    r = _run(_payload(root, session_id="OTHER"))
    assert _denied(r)
    message = json.loads(r.stderr)["systemMessage"]
    assert ".claude/gdd-dev.local.md" in message and "active: false" in message, message
    # 書き換える前に、持ち主がまだ動いているかをユーザーに聞く（setup-gdd-loop.sh のロックの文と同じ順）
    assert message.index("ask the user") < message.index("active: false"), message
    for reason in ("`session_id` is empty", "no `---` frontmatter", "`served:<id>`", "cannot be read"):
        assert reason in message, (reason, message)


@pytest.mark.skipif(hasattr(os, "geteuid") and os.geteuid() == 0, reason="root は読めない state も読める")
def test_unreadable_state_deny_says_how_to_restore_it(tmp_path):
    root = _repo(tmp_path)
    _marker(root, _owned_by("OWNER"))
    state = root / ".claude" / "gdd-dev.local.md"
    state.chmod(0)
    try:
        r = _run(_payload(root, session_id="OTHER"))
    finally:
        state.chmod(0o600)
    assert _denied(r)
    message = json.loads(r.stderr)["systemMessage"]
    assert "regular file" in message and "permissions" in message, message


def _setup_gdd_loop(root: Path, sid: str, tmp_path: Path) -> None:
    env = {**os.environ, "CLAUDE_CODE_SESSION_ID": sid, "CLAUDE_CONFIG_DIR": str(tmp_path / "no-claude-config")}
    r = subprocess.run(
        ["bash", str(PLUGIN_ROOT / "scripts" / "setup-gdd-loop.sh"), "test intent"],
        cwd=root, env=env, capture_output=True, text=True,
    )
    assert r.returncode == 0, r.stderr
    assert f"session_id: {sid}" in (root / ".claude" / "gdd-dev.local.md").read_text(encoding="utf-8")


def test_marker_written_by_setup_blocks_only_its_owner(tmp_path):
    # setup-gdd-loop.sh が環境変数から書いた session_id を、guard が payload の id と照合する
    root = _repo(tmp_path)
    _setup_gdd_loop(root, "OWNER-1", tmp_path)
    assert _denied(_run(_payload(root, session_id="OWNER-1")))
    assert _allowed(_run(_payload(root, session_id="OTHER-2")))
