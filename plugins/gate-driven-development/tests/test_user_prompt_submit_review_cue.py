"""RED tests for review cue detection in run-user-prompt-submit-hook.sh (Task 4)"""
import subprocess, os

from _paths import PLUGIN_ROOT
SCRIPT = PLUGIN_ROOT / "hooks/scripts/run-user-prompt-submit-hook.sh"

def _make_state(tmp, resume_from="gdd-implementation-gating"):
    state = tmp / "state.md"
    state.write_text(
        f"Resume From: {resume_from}\n"
        "Human Check Status: approved\n"
        "Route In Progress: none\n"
        "Active Branch: gdd/test-branch\n"
    )
    return state

def test_review_cue_japanese_injects_prompt(tmp_path):
    _make_state(tmp_path)
    env = {**os.environ, "GDD_STEERING_DIR": str(tmp_path),
           "CLAUDE_USER_PROMPT": "レビューコメントが来ました"}
    r = subprocess.run(["bash", str(SCRIPT)], env=env, capture_output=True, text=True)
    assert r.returncode == 0
    assert "gdd:review-cue-detected" in r.stdout

def test_review_cue_english_injects_prompt(tmp_path):
    _make_state(tmp_path)
    env = {**os.environ, "GDD_STEERING_DIR": str(tmp_path),
           "CLAUDE_USER_PROMPT": "PR review comments added"}
    r = subprocess.run(["bash", str(SCRIPT)], env=env, capture_output=True, text=True)
    assert r.returncode == 0
    assert "gdd:review-cue-detected" in r.stdout

def test_no_active_steering_no_injection(tmp_path):
    """active steering がなければ注入しない"""
    env = {**os.environ, "GDD_STEERING_DIR": str(tmp_path),
           "CLAUDE_USER_PROMPT": "レビューコメントが来ました"}
    r = subprocess.run(["bash", str(SCRIPT)], env=env, capture_output=True, text=True)
    assert r.returncode == 0
    assert "gdd:review-cue-detected" not in r.stdout

def test_wrong_phase_no_injection(tmp_path):
    """Resume From が対象外 phase なら注入しない"""
    _make_state(tmp_path, resume_from="gdd-brainstorming")
    env = {**os.environ, "GDD_STEERING_DIR": str(tmp_path),
           "CLAUDE_USER_PROMPT": "レビューコメントが来ました"}
    r = subprocess.run(["bash", str(SCRIPT)], env=env, capture_output=True, text=True)
    assert r.returncode == 0
    assert "gdd:review-cue-detected" not in r.stdout

def test_unrelated_prompt_no_injection(tmp_path):
    """review と無関係なプロンプトには注入しない"""
    _make_state(tmp_path)
    env = {**os.environ, "GDD_STEERING_DIR": str(tmp_path),
           "CLAUDE_USER_PROMPT": "ファイルを読んで"}
    r = subprocess.run(["bash", str(SCRIPT)], env=env, capture_output=True, text=True)
    assert r.returncode == 0
    assert "gdd:review-cue-detected" not in r.stdout

def test_external_review_waiting_phase_injects_prompt(tmp_path):
    """external-review-waiting phase でも review cue を注入する"""
    _make_state(tmp_path, resume_from="external-review-waiting")
    env = {**os.environ, "GDD_STEERING_DIR": str(tmp_path),
           "CLAUDE_USER_PROMPT": "PRレビューコメントが来ました"}
    r = subprocess.run(["bash", str(SCRIPT)], env=env, capture_output=True, text=True)
    assert r.returncode == 0
    assert "gdd:review-cue-detected" in r.stdout
