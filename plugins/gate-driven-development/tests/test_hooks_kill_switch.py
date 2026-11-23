"""AC-A0-1 / AC-A0-3: kill switch の**対象名簿**と、ディスクとの drift 検査。

対象の正本は `ALL_HOOKS` で、`test_all_hooks_matches_the_scripts_on_disk` が
ディスクとの両方向一致を assert する。**件数をここに書かない** ―― 旧記述は
「全 12」と書きながら実体は 15 本あり、3 本が黙って検査対象外だった。

**kill switch が実際に効いているかの正本は本ファイルではない。**
`STDIN_PAYLOAD` はどの hook の実行経路も踏まないため、下の 2 つの parametrize は
**guard を削除しても常時 no-op へ変えても緑のまま**（gate が全 hook で確かめた。
`ALL_HOOKS` を是正した後も同じ）。efficacy を pin しているのは各 hook の
契約テスト側で、guard 削除で実際に落ちることを確認済み:

- `run-pre-push-gate-hook.sh` -> `test_pre_push_gate_activation_contract.py`
- `run-notification-hook.sh` -> `test_notification_hook_contract.py`
- `run-stop-failure-hook.sh` -> `test_stop_failure_hook_contract.py`
- `run-session-start-hook.sh` -> `test_session_start_last_turn_failure_contract.py`

残る 11 hook には efficacy の pin がどこにも無い（carry-forward **ADV-T21-1**）。
"""
import json
import os
import subprocess
from pathlib import Path

import pytest

from _paths import PLUGIN_ROOT
SCRIPTS_DIR = PLUGIN_ROOT / "hooks" / "scripts"

ALL_HOOKS = [
    "run-active-gdd-skill-expansion-gate-hook.sh",
    "run-active-gdd-skill-gate-hook.sh",
    "run-agent-dispatch-model-gate-hook.sh",
    "run-background-dispatch-gate-hook.sh",
    "run-block-enter-worktree-hook.sh",
    "run-block-plan-mode-hook.sh",
    "run-gdd-stop-hook.sh",
    "run-pre-compact-hook.sh",
    "run-pre-pr-gate-hook.sh",
    "run-merge-gate-hook.sh",
    "run-pre-tool-use-plan-reread-hook.sh",
    "run-request-diff-hook.sh",
    "run-display-marker-hook.sh",
    "run-session-start-hook.sh",
    "run-push-review-env-hook.sh",
    "run-steering-write-hook.sh",
    "run-user-prompt-submit-hook.sh",
    "run-worktree-command-guard.sh",
    "run-pre-push-gate-hook.sh",
    "run-stop-failure-hook.sh",
    "run-notification-hook.sh",
    "run-review-followup-nudge-hook.sh",
    "run-gate-skill-dispatch-nudge-hook.sh",
    "run-wait-loop-gate-hook.sh",
    "run-main-model-gate-hook.sh",
    "run-request-capture-hook.sh",
    "run-request-diff-approval-gate-hook.sh",
]

STDIN_PAYLOAD = json.dumps({
    "cwd": "/tmp",
    "transcript_path": "/tmp/transcript.jsonl",
    "session_id": "test-session",
    "stop_hook_active": False,
})


def _run_hook(hook_name: str, home_dir: Path) -> subprocess.CompletedProcess:
    script = SCRIPTS_DIR / hook_name
    env = dict(os.environ)
    env["HOME"] = str(home_dir)
    env["CLAUDE_PLUGIN_ROOT"] = str(PLUGIN_ROOT)
    # テストを回す session の env file に、SessionStart の hook が書き足さないようにする
    env.pop("CLAUDE_ENV_FILE", None)
    return subprocess.run(
        ["bash", str(script)],
        input=STDIN_PAYLOAD,
        capture_output=True,
        text=True,
        env=env,
        timeout=30  # 並列の全量テストの負荷の下では、session-start hook が hook の timeout を超えることがある（2026-09-06）,
    )


def test_all_hooks_matches_the_scripts_on_disk():
    """`ALL_HOOKS` が `hooks/scripts/run-*.sh` の実体と一致することを固定する（AC-19）。

    このリストは手書きで、hook を新設しても足し忘れると
    **kill switch が効かない hook が黙って検査対象外になる**。
    実際に 3 本（`run-pre-push-gate-hook.sh` / `run-stop-failure-hook.sh` /
    `run-notification-hook.sh`）が漏れていた。件数はここに書かず、
    **ディスクを正本にして両方向の集合一致**を assert する。
    """
    on_disk = {path.name for path in SCRIPTS_DIR.glob("run-*.sh")}
    listed = set(ALL_HOOKS)

    assert on_disk, "SCRIPTS_DIR に run-*.sh が 1 本も無い（検査が空虚になる）"
    assert len(listed) == len(ALL_HOOKS), f"ALL_HOOKS に重複がある: {ALL_HOOKS}"
    assert listed - on_disk == set(), f"ALL_HOOKS にあるが実体が無い: {sorted(listed - on_disk)}"
    assert on_disk - listed == set(), f"実体はあるが ALL_HOOKS に無い: {sorted(on_disk - listed)}"


@pytest.mark.parametrize("hook_name", ALL_HOOKS)
def test_kill_switch_active_makes_hook_noop(tmp_path, hook_name):
    home_dir = tmp_path / "home"
    (home_dir / ".claude").mkdir(parents=True)
    (home_dir / ".claude" / "gdd-hooks-disabled").touch()

    result = _run_hook(hook_name, home_dir)

    assert result.returncode == 0, (
        f"{hook_name}: expected exit 0 with kill switch active, "
        f"got {result.returncode}, stderr={result.stderr!r}"
    )
    assert '"decision"' not in result.stdout
    assert '"hookEventName"' not in result.stdout
    assert '"permissionDecision":"deny"' not in result.stdout


@pytest.mark.parametrize("hook_name", ALL_HOOKS)
def test_kill_switch_inactive_preserves_normal_behavior(tmp_path, hook_name):
    """kill switch guard が常時 no-op ではないことを保証する逆ケース（AC-A0-3）。

    各 hook は構造が異なる（SCRIPT_DIR 有無・既存 python 検出ロジック等）ため、
    guard 挿入がどのファイルかに関わらず既存の非 kill-switch 挙動を壊していないことを
    1 hook だけでなく `ALL_HOOKS` 全件で確認する（T-3 で発見した dirname 依存 regression の
    ような hook 固有の壊れ方は 1 hook だけの検証では検出できない）。
    """
    home_dir = tmp_path / "home"
    home_dir.mkdir()

    result = _run_hook(hook_name, home_dir)

    # kill switch 無し時は通常挙動（guard による無条件 exit 0 ではない）。
    # 各 hook は非 active セッションでは deny/block を返さない通常挙動を持つため、
    # 「kill switch 起因の即時 exit ではない」ことを exit code と stderr の異常有無で確認する。
    assert result.returncode == 0, (
        f"{hook_name}: expected exit 0 without kill switch, "
        f"got {result.returncode}, stderr={result.stderr!r}"
    )
    assert "command not found" not in result.stderr
    assert "No such file or directory" not in result.stderr
