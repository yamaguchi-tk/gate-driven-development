"""hook は、プロセスの cwd ではなく payload の最上位の `cwd`（セッションの cwd）で判定する。

desktop の worktree のセッションでは、hook のプロセスの cwd は root checkout になり、payload の
`cwd` が worktree になる。root checkout に残った古い steering を読んで、worktree のセッションに
毎ターン `[gdd:blocked]` を注入していた（2026-11-20 に再現）。

1. hooks.json から起動する wrapper のうち、steering・marker を読む lib を source するものは、
   入口の関数 `gdd_enter_payload_cwd` を呼ぶ（payload の cwd を自分で扱う gate は除く）
2. プロセスの cwd が古い steering のある root、payload の cwd が worktree なら、UserPromptSubmit は
   何も注入しない
3. UserPromptSubmit は、このセッションの GDD の印（active で session_id が同じ marker）が無ければ、
   steering があっても毎ターンの注入をしない。印があれば今までどおり注入する
4. block gate は、payload の cwd の marker と、プロセスの cwd の marker のどちらかが
   このセッションの active な印なら止める
5. payload の cwd が使えないときは、プロセスの cwd のまま今までどおり判定し、stdin も後ろへ渡す
"""
from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path

import pytest

from _git_fixture import init_repo
from _paths import PLUGIN_ROOT
from test_hooks_toplevel_trailing_newline import HOOKS, _blocked

SCRIPTS = PLUGIN_ROOT / "hooks" / "scripts"
SESSION = "test-session"
UPS = "run-user-prompt-submit-hook.sh"
LIBS = re.compile(r"lib/(detect-steering|exact-path|gdd-active-check)\.sh")
# payload の cwd を自分で読んで cd する gate（hook_cwd.toplevel_cwd を使う）
EXEMPT = {"run-merge-gate-hook.sh", "run-pre-pr-gate-hook.sh"}


def _wrappers():
    hooks = json.loads((PLUGIN_ROOT / "hooks" / "hooks.json").read_text(encoding="utf-8"))["hooks"]
    names = set()
    for groups in hooks.values():
        for group in groups:
            for hook in group["hooks"]:
                m = re.search(r"hooks/scripts/([\w.-]+\.sh)", hook["command"])
                if m:
                    names.add(m.group(1))
    return sorted(names)


def test_wrappers_reading_steering_enter_the_payload_cwd():
    sourcing = [n for n in _wrappers() if LIBS.search((SCRIPTS / n).read_text(encoding="utf-8"))]
    assert len(sourcing) >= 11
    missing = [n for n in sourcing if n not in EXEMPT
               and "gdd_enter_payload_cwd" not in (SCRIPTS / n).read_text(encoding="utf-8")]
    assert missing == []


def _repo(path: Path, *, marker: str | None = None, steering: bool = False) -> Path:
    """marker: None（無し）・"ours"（active で同じ session）・"other"（active で別の session）・"inactive"・
    "noid"（active で session_id が空。session id の無いランタイムの setup が書く形）。"""
    path.mkdir(parents=True)
    init_repo(path)
    if marker is not None:
        active = "false" if marker == "inactive" else "true"
        sid = {"other": "other-session", "noid": ""}.get(marker, SESSION)
        (path / ".claude").mkdir()
        (path / ".claude" / "gdd-dev.local.md").write_text(
            f"---\nactive: {active}\nsession_id: {sid}\n---\n", encoding="utf-8")
    if steering:
        task = path / ".steering" / "20260619-stale"
        task.mkdir(parents=True)
        (task / "state.md").write_text("Resume From=implementation\nNext Action=implementation\n",
                                       encoding="utf-8")
    return path


def _run(script: str, payload: dict, cwd: Path, home: Path, session: str = SESSION):
    env = {**os.environ, "CLAUDE_PLUGIN_ROOT": str(PLUGIN_ROOT), "CLAUDE_CODE_SESSION_ID": session,
           "HOME": str(home)}
    for key in ("GDD_DISABLE", "GDD_STEERING_DIR", "CLAUDE_USER_PROMPT"):
        env.pop(key, None)
    r = subprocess.run(["bash", str(SCRIPTS / script)], cwd=cwd, input=json.dumps(payload),
                       capture_output=True, text=True, env=env, timeout=60, check=False)
    assert r.returncode == 0, r.stderr
    return r.stdout


@pytest.fixture
def home(tmp_path):
    h = tmp_path / "home"
    h.mkdir()
    return h


def _prompt(cwd, text="続けて"):
    return {"hook_event_name": "UserPromptSubmit", "prompt": text, "cwd": str(cwd)}


def test_stale_root_steering_is_not_injected_into_a_worktree_session(tmp_path, home):
    root = _repo(tmp_path / "root", steering=True)
    wt = _repo(tmp_path / "wt")
    assert _run(UPS, _prompt(wt), root, home) == ""


@pytest.mark.parametrize("marker", [None, "other", "inactive"])
def test_steering_without_this_sessions_marker_is_not_injected(tmp_path, home, marker):
    root = _repo(tmp_path / "root", marker=marker, steering=True)
    assert _run(UPS, _prompt(root), root, home) == ""


def test_steering_with_this_sessions_marker_is_still_injected(tmp_path, home):
    wt = _repo(tmp_path / "wt", marker="ours", steering=True)
    root = _repo(tmp_path / "root")
    assert _run(UPS, _prompt(wt), root, home) != ""


def test_payload_is_still_passed_on_after_entering_the_cwd(tmp_path, home):
    # 相対パスの continuation ファイルを payload の cwd で見つけ、prompt を stdin から読む
    wt = _repo(tmp_path / "wt")
    (wt / ".claude").mkdir()
    (wt / ".claude" / "gdd-post-merge-continuation.json").write_text("{}", encoding="utf-8")
    root = _repo(tmp_path / "root")
    assert "post-merge-continuation" in _run(UPS, _prompt(wt, "マージした"), root, home)


@pytest.mark.parametrize("script,payload,form", HOOKS)
def test_block_gate_reads_the_payload_cwd_marker(tmp_path, home, script, payload, form):
    wt = _repo(tmp_path / "wt", marker="ours")
    root = _repo(tmp_path / "root")
    assert _blocked(_run(script, {**payload, "cwd": str(wt)}, root, home), form)


@pytest.mark.parametrize("script,payload,form", HOOKS)
def test_block_gate_still_honours_this_sessions_marker_at_the_process_cwd(tmp_path, home, script,
                                                                          payload, form):
    root = _repo(tmp_path / "root", marker="ours")
    wt = _repo(tmp_path / "wt")
    assert _blocked(_run(script, {**payload, "cwd": str(wt)}, root, home), form)


@pytest.mark.parametrize("script,payload,form", HOOKS)
def test_block_gate_ignores_another_sessions_marker_at_the_process_cwd(tmp_path, home, script,
                                                                       payload, form):
    root = _repo(tmp_path / "root", marker="other")
    wt = _repo(tmp_path / "wt")
    assert not _blocked(_run(script, {**payload, "cwd": str(wt)}, root, home), form)


@pytest.mark.parametrize("cwd", ["/nonexistent-gdd-payload-cwd", "relative/dir", 3, "/tmp\nx"])
@pytest.mark.parametrize("script,payload,form", HOOKS[:1])
def test_unusable_payload_cwd_keeps_the_process_cwd(tmp_path, home, script, payload, form, cwd):
    root = _repo(tmp_path / "root", marker="ours")
    assert _blocked(_run(script, {**payload, "cwd": cwd}, root, home), form)


# --- 移す前の repo の marker を、gate 自身の判定で見る（fail-open の 3 つの形） ---

def _path_without_git(tmp_path: Path) -> str:
    """PATH の実行ファイルを git だけ除いて並べたディレクトリ。"""
    bin_dir = tmp_path / "bin-no-git"
    bin_dir.mkdir()
    for d in os.environ.get("PATH", "").split(os.pathsep):
        if not d or not os.path.isdir(d):
            continue
        for name in os.listdir(d):
            src = os.path.join(d, name)
            dst = bin_dir / name
            if name == "git" or dst.exists() or not os.access(src, os.X_OK) or os.path.isdir(src):
                continue
            dst.symlink_to(src)
    return str(bin_dir)


def _run_env(script, payload, cwd, home, **extra):
    env = {**os.environ, "CLAUDE_PLUGIN_ROOT": str(PLUGIN_ROOT), "HOME": str(home)}
    for key in ("GDD_DISABLE", "GDD_STEERING_DIR", "CLAUDE_USER_PROMPT", "CLAUDE_CODE_SESSION_ID"):
        env.pop(key, None)
    env.update(extra)
    r = subprocess.run(["bash", str(SCRIPTS / script)], cwd=cwd, input=json.dumps(payload),
                       capture_output=True, text=True, env=env, timeout=60, check=False)
    assert r.returncode == 0, r.stderr
    return r.stdout


@pytest.mark.parametrize("script,payload,form", HOOKS)
def test_block_gate_without_git_still_honours_the_process_cwd_marker(tmp_path, home, script, payload,
                                                                      form):
    root = _repo(tmp_path / "root", marker="ours")
    wt = _repo(tmp_path / "wt")
    out = _run_env(script, {**payload, "cwd": str(wt)}, root, home,
                   CLAUDE_CODE_SESSION_ID=SESSION, PATH=_path_without_git(tmp_path))
    assert _blocked(out, form)


@pytest.mark.parametrize("script,payload,form", HOOKS)
def test_block_gate_with_a_loosely_written_payload_marker_still_honours_the_process_cwd_marker(
        tmp_path, home, script, payload, form):
    root = _repo(tmp_path / "root", marker="ours")
    wt = _repo(tmp_path / "wt")
    (wt / ".claude").mkdir()
    (wt / ".claude" / "gdd-dev.local.md").write_text(
        f"---\nactive:true\nsession_id: {SESSION}\n---\n", encoding="utf-8")
    assert _blocked(_run(script, {**payload, "cwd": str(wt)}, root, home), form)


@pytest.mark.parametrize("script,payload,form", HOOKS)
def test_block_gate_without_a_session_id_still_honours_the_process_cwd_marker(tmp_path, home, script,
                                                                               payload, form):
    root = _repo(tmp_path / "root", marker="other")
    wt = _repo(tmp_path / "wt")
    assert _blocked(_run_env(script, {**payload, "cwd": str(wt)}, root, home), form)


@pytest.mark.parametrize("script,payload,form", HOOKS)
def test_block_gate_with_another_sessions_payload_marker_still_honours_this_sessions_origin_marker(
        tmp_path, home, script, payload, form):
    root = _repo(tmp_path / "root", marker="ours")
    wt = _repo(tmp_path / "wt", marker="other")
    assert _blocked(_run(script, {**payload, "cwd": str(wt)}, root, home), form)


# --- 入口が失敗しても hook 全体は落ちない ---

ENTRY_HOOKS = ("run-gdd-stop-hook.sh", UPS, "run-pre-compact-hook.sh", "run-block-plan-mode-hook.sh")


@pytest.mark.parametrize("script", ENTRY_HOOKS)
def test_hook_whose_process_cwd_was_removed_does_not_fail(tmp_path, home, script):
    wt = _repo(tmp_path / "wt", marker="ours")
    gone = tmp_path / "gone"
    gone.mkdir()
    env = {**os.environ, "CLAUDE_PLUGIN_ROOT": str(PLUGIN_ROOT), "CLAUDE_CODE_SESSION_ID": SESSION,
           "HOME": str(home)}
    env.pop("GDD_DISABLE", None)
    payload = json.dumps({"hook_event_name": "Stop", "prompt": "x", "tool_name": "EnterPlanMode",
                          "tool_input": {}, "cwd": str(wt)})
    r = subprocess.run(["bash", "-c", 'cd "$1" && rmdir "$1" && exec bash "$2"', "_", str(gone),
                        str(SCRIPTS / script)],
                       input=payload, capture_output=True, text=True, env=env, timeout=60, check=False)
    if "failed to make path absolute" in r.stderr:
        pytest.skip("python3 cannot start in a removed cwd on this platform")
    assert r.returncode == 0, r.stderr


def test_several_steerings_without_this_sessions_marker_are_not_announced(tmp_path, home):
    root = _repo(tmp_path / "root", steering=True)
    task = root / ".steering" / "20260620-stale"
    task.mkdir()
    (task / "state.md").write_text("Resume From=implementation\nNext Action=implementation\n",
                                   encoding="utf-8")
    assert _run(UPS, _prompt(root), root, home) == ""


# session id が env に無いランタイムでは、payload の session_id で比べる（Stop hook の
# `_session_guard` と同じ）。marker に id が無ければ active かだけを見る。
@pytest.mark.parametrize("marker,payload_sid,injected", [
    (None, None, False), ("inactive", None, False), ("noid", None, True), ("noid", "codex-1", True),
    ("other", "other-session", True), ("other", "codex-1", False), ("other", None, False),
])
def test_runtime_without_a_session_id_injects_only_with_this_sessions_active_marker(
        tmp_path, home, marker, payload_sid, injected):
    root = _repo(tmp_path / "root", marker=marker, steering=True)
    payload = _prompt(root)
    if payload_sid is not None:
        payload["session_id"] = payload_sid
    assert (_run_env(UPS, payload, root, home) != "") is injected


@pytest.mark.parametrize("script,payload,form", HOOKS)
def test_block_gate_whose_cwd_cannot_be_resolved_blocks(tmp_path, home, script, payload, form):
    # プロセスの cwd が消え、payload の cwd も使えないときは、marker で判定できないので止める側
    gone = tmp_path / "gone"
    gone.mkdir()
    env = {**os.environ, "CLAUDE_PLUGIN_ROOT": str(PLUGIN_ROOT), "CLAUDE_CODE_SESSION_ID": SESSION,
           "HOME": str(home)}
    env.pop("GDD_DISABLE", None)
    r = subprocess.run(["bash", "-c", 'cd "$1" && rmdir "$1" && exec bash "$2"', "_", str(gone),
                        str(SCRIPTS / script)],
                       input=json.dumps({**payload, "cwd": "/nonexistent-gdd-payload-cwd"}),
                       capture_output=True, text=True, env=env, timeout=60, check=False)
    if r.returncode != 0 and "failed to make path absolute" in r.stderr:
        pytest.skip("python3 cannot start in a removed cwd on this platform")
    assert r.returncode == 0, r.stderr
    assert _blocked(r.stdout, form)


# --- 判定できないときは止める側（通すのは、marker が無いと言い切れたときだけ） ---

@pytest.mark.skipif(os.geteuid() == 0, reason="root は読めない権限でも読める")
@pytest.mark.parametrize("script,payload,form", HOOKS)
def test_block_gate_with_an_unreadable_marker_blocks(tmp_path, home, script, payload, form):
    root = _repo(tmp_path / "root", marker="ours")
    marker = root / ".claude" / "gdd-dev.local.md"
    marker.chmod(0)
    try:
        assert _blocked(_run(script, {**payload, "cwd": str(root)}, root, home), form)
    finally:
        marker.chmod(0o644)


@pytest.mark.parametrize("marker,allowed", [("ours", False), ("other", True), ("inactive", True), (None, True)])
def test_marker_allows_compares_the_session_by_itself(tmp_path, marker, allowed):
    # exact-path.sh だけを source しても、marker の session_id を自分で読んで比べる
    root = _repo(tmp_path / "root", marker=marker)
    r = subprocess.run(["bash", "-c", 'source "$1"; GDD_ORIGIN_CWD="$PWD"; gdd_marker_allows', "_",
                        str(SCRIPTS / "lib" / "exact-path.sh")],
                       cwd=root, capture_output=True, text=True, timeout=30, check=False,
                       env={**os.environ, "CLAUDE_CODE_SESSION_ID": SESSION})
    assert (r.returncode == 0) is allowed, r.stderr


# --- 「無い」と読むのは正の証拠があるときだけ（既定は止める側） ---

def _marker_text(root: Path, text: str) -> Path:
    (root / ".claude").mkdir(exist_ok=True)
    (root / ".claude" / "gdd-dev.local.md").write_text(text, encoding="utf-8")
    return root


@pytest.mark.parametrize("text,blocked", [
    (f"---\n  active: true\nsession_id: {SESSION}\n---\n", True),
    (f"---\nactive : true\nsession_id: {SESSION}\n---\n", True),
    (f"---\nActive:TRUE\nsession_id: {SESSION}\n---\n", True),
    ("", True),
    ("---\nsession_id: x\n---\n", True),
    (f"---\nactive: maybe\nsession_id: {SESSION}\n---\n", True),
    (f"---\n  active: false\nsession_id: {SESSION}\n---\n", False),
])
@pytest.mark.parametrize("script,payload,form", HOOKS)
def test_block_gate_reads_active_as_the_stop_hook_does(tmp_path, home, script, payload, form, text, blocked):
    # Stop hook（state_io.py）と同じく key と値を strip・小文字で読む。値が読めなければ止める側
    root = _marker_text(_repo(tmp_path / "root"), text)
    assert _blocked(_run(script, {**payload, "cwd": str(root)}, root, home), form) is blocked


@pytest.mark.skipif(os.geteuid() == 0, reason="root は検索できない権限でも読める")
@pytest.mark.parametrize("script,payload,form", HOOKS)
def test_block_gate_with_an_unsearchable_claude_dir_blocks(tmp_path, home, script, payload, form):
    root = _repo(tmp_path / "root", marker="ours")
    (root / ".claude").chmod(0)
    try:
        assert _blocked(_run(script, {**payload, "cwd": str(root)}, root, home), form)
    finally:
        (root / ".claude").chmod(0o755)


@pytest.mark.parametrize("script,payload,form", HOOKS)
def test_block_gate_with_a_dangling_marker_symlink_blocks(tmp_path, home, script, payload, form):
    root = _repo(tmp_path / "root")
    (root / ".claude").mkdir()
    (root / ".claude" / "gdd-dev.local.md").symlink_to(tmp_path / "missing")
    assert _blocked(_run(script, {**payload, "cwd": str(root)}, root, home), form)


@pytest.mark.parametrize("script,payload,form", HOOKS)
def test_block_gate_whose_origin_cwd_is_unknown_blocks(tmp_path, home, script, payload, form):
    # 入口で移す前の cwd を取れない（プロセスの cwd が消えた）なら、移した先に marker が無くても止める側
    wt = _repo(tmp_path / "wt")
    gone = tmp_path / "gone"
    gone.mkdir()
    env = {**os.environ, "CLAUDE_PLUGIN_ROOT": str(PLUGIN_ROOT), "CLAUDE_CODE_SESSION_ID": SESSION,
           "HOME": str(home)}
    env.pop("GDD_DISABLE", None)
    r = subprocess.run(["bash", "-c", 'cd "$1" && rmdir "$1" && exec bash "$2"', "_", str(gone),
                        str(SCRIPTS / script)],
                       input=json.dumps({**payload, "cwd": str(wt)}),
                       capture_output=True, text=True, env=env, timeout=60, check=False)
    if "failed to make path absolute" in r.stderr:
        pytest.skip("python3 cannot start in a removed cwd on this platform")
    assert r.returncode == 0, r.stderr
    assert _blocked(r.stdout, form)


@pytest.mark.parametrize("text,blocked", [
    (f"---\nactive: true\n  session_id: {SESSION}\n---\n", True),
    (f"---\nactive: true\nsession_id : {SESSION}\n---\n", True),
    (f"---\nactive: true\nsession_id: other-session\nsession_id: {SESSION}\n---\n", True),
    (f"---\nactive: true\nsession_id: {SESSION}\n---\nsession_id: other-session\n", True),
    ("---\nactive: true\nsession_id: a b\n---\n", True),
    ("---\nactive: true\nsession_id: other-session\n---\n", False),
    ("---\nactive: true\nsession_id:\n---\n", False),
])
@pytest.mark.parametrize("script,payload,form", HOOKS)
def test_block_gate_reads_session_id_as_the_stop_hook_does(tmp_path, home, script, payload, form, text, blocked):
    # session_id も active と同じく frontmatter の中を strip して読み、後の行を採る（state_io.py と同じ）。
    # 別のセッションと言い切れる値（許す文字だけで、今の id と違う）か空のときだけ通す
    root = _marker_text(_repo(tmp_path / "root"), text)
    assert _blocked(_run(script, {**payload, "cwd": str(root)}, root, home), form) is blocked


@pytest.mark.parametrize("text", [
    f"---\nactive: true\nsession_id: {SESSION}\nsession_id: other-session\n---\n",
    f"---\nactive: true\nsession_id: {SESSION}\nsession_id:\n---\n",
    f"---\nactive: true\nactive: false\nsession_id: {SESSION}\n---\n",
    "---\nactive: false\nactive: false\nsession_id: other-session\n---\n",
])
@pytest.mark.parametrize("script,payload,form", HOOKS)
def test_block_gate_with_a_repeated_key_blocks(tmp_path, home, script, payload, form, text):
    # frontmatter に同じ key（active・session_id）が 2 行以上ある marker は、どちらの行を採るかで結論が
    # 割れる（Stop hook は後の行、注入と root-branch guard は前の行・どこかの行）。判定できないので止める側
    root = _marker_text(_repo(tmp_path / "root"), text)
    assert _blocked(_run(script, {**payload, "cwd": str(root)}, root, home), form)


@pytest.mark.parametrize("text", [
    f"---\nactive: true\nsession_id: other-session\nnote: x\rsession_id: {SESSION}\n---\n",
    f"---\nactive: false\nnote: x\ractive: true\nsession_id: {SESSION}\n---\n",
    f"---\nactive: true\nsession_id: other-session\nsession_id\x1f: {SESSION}\n---\n",
    f"---\nactive: true\nsession_id: other-session\n　session_id: {SESSION}\n---\n",
])
@pytest.mark.parametrize("script,payload,form", HOOKS)
def test_block_gate_blocks_frontmatter_lines_it_cannot_read_like_the_stop_hook(
        tmp_path, home, script, payload, form, text):
    # Stop hook（regular_file.py・state_io.py）は単独の `\r` も行の区切りにし、key の前後の Unicode の空白も
    # 落とす。block gate はそれと同じ行・key の集合を読める形（`\r` の無い行、ASCII の key）だけを読み、
    # ほかは判定できないとして止める
    root = _marker_text(_repo(tmp_path / "root"), text)
    assert _blocked(_run(script, {**payload, "cwd": str(root)}, root, home), form)


# --- marker の中身は Stop hook と同じ Python のコードで読む（読み手を 1 つにする） ---

@pytest.mark.parametrize("text", [
    f"---\nactive: false\nx\x00\ractive: true\nsession_id: {SESSION}\n---\n",
    f"---\nactive: false\n---\x00\nactive: true\nsession_id: {SESSION}\n---\n",
])
@pytest.mark.parametrize("script,payload,form", HOOKS)
def test_block_gate_reads_a_marker_with_nul_as_the_stop_hook_does(tmp_path, home, script, payload, form, text):
    # awk の実装によっては NUL で行を打ち切る。Stop hook と同じコードで読めば、active が 2 行の marker として止まる
    root = _marker_text(_repo(tmp_path / "root"), text)
    assert _blocked(_run(script, {**payload, "cwd": str(root)}, root, home), form)


def _path_without_python(tmp_path: Path) -> str:
    """PATH の実行ファイルを python の名前のものだけ除いて並べたディレクトリ。"""
    bin_dir = tmp_path / "bin-no-python"
    bin_dir.mkdir()
    for d in os.environ.get("PATH", "").split(os.pathsep):
        if not d or not os.path.isdir(d):
            continue
        for name in os.listdir(d):
            src = os.path.join(d, name)
            dst = bin_dir / name
            if name.startswith("python") or dst.exists() or not os.access(src, os.X_OK) or os.path.isdir(src):
                continue
            dst.symlink_to(src)
    return str(bin_dir)


@pytest.mark.parametrize("marker,blocked", [("other", True), ("inactive", True), (None, False)])
@pytest.mark.parametrize("script,payload,form", HOOKS)
def test_block_gate_without_python_blocks_only_when_a_marker_exists(
        tmp_path, home, script, payload, form, marker, blocked):
    # marker の中身は Python でしか読まない。python3 が無ければ、marker が在るときは判定できないので止め、
    # 無いときは bash だけで通す
    root = _repo(tmp_path / "root", marker=marker)
    out = _run_env(script, {**payload, "cwd": str(root)}, root, home,
                   CLAUDE_CODE_SESSION_ID=SESSION, PATH=_path_without_python(tmp_path))
    assert _blocked(out, form) is blocked


def _path_with_failing_python(tmp_path: Path) -> str:
    """起動はできるが必ず 1 で終わる python3 を、PATH の先頭に置く（shim・stub が壊れた形）。"""
    bin_dir = tmp_path / "bin-failing-python"
    bin_dir.mkdir()
    for name in ("python3", "python"):
        shim = bin_dir / name
        shim.write_text("#!/bin/sh\nexit 1\n")
        shim.chmod(0o755)
    return str(bin_dir) + os.pathsep + os.environ.get("PATH", "")


@pytest.mark.parametrize("marker,blocked", [("other", True), ("inactive", True), (None, False)])
@pytest.mark.parametrize("script,payload,form", HOOKS)
def test_block_gate_with_a_failing_python_blocks_only_when_a_marker_exists(
        tmp_path, home, script, payload, form, marker, blocked):
    # payload を読む python3 が落ちたら、通すと答えたことにならないので、marker が在れば止める
    root = _repo(tmp_path / "root", marker=marker)
    out = _run_env(script, {**payload, "cwd": str(root)}, root, home,
                   CLAUDE_CODE_SESSION_ID=SESSION, PATH=_path_with_failing_python(tmp_path))
    assert _blocked(out, form) is blocked
