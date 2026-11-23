"""root branch guard 契約テスト群が **横断で** 共有する fixture / helper。

`tests/test_root_branch_guard_contract.py`（旧・単一ファイル、1652 行）が
`gdd-codebase-health.py` の large_file（1652 > 1500）と python_function_count
（77 > 40）の両方で medium 判定されたため、関心事ごとに
`test_root_branch_guard_*.py` へ分割した。分割後の各ファイルが独自に
git repo 初期化・active state 書き込み・hook subprocess 起動を持つと、同じ fixture が
複数ファイルへコピーされて片方だけ直すドリフトが発生する。ここへ 1 本化することで
「hook 起動 fixture の正本はここだけ」という構造を保つ（`_merge_gate_support.py`
と同じ方針）。
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from _timing_budget import hang_guard_seconds, hook_timeout_seconds
from _git_fixture import init_repo

from _paths import PLUGIN_ROOT as ROOT

#: root branch guard の運用 timeout（`hooks/hooks.json` 由来。10 秒）。
#: #1/#2 の壁時計 backstop（`GUARD_HOOK_TIMEOUT_SEC / 2`）と、helper の打ち切り
#: （`GUARD_HANG_GUARD_SEC`）の両方がここと同じ `hooks.json` の値を導出元にする。
#: **モジュールレベルで 1 回だけ解決する**（design.md § hook_timeout_seconds）。
#: 関数本体で毎回呼ぶと `hooks.json` の read + `json.loads` が
#: `timing_budget()` の計測区間の内側に入り、親プロセスの `process_time` に
#: 計上される。import 時に解決するため hooks.json 不整合は collection error
#: として fail-loud に落ちる（静かな既定値フォールバックは持たない）。
GUARD_HOOK_TIMEOUT_SEC = hook_timeout_seconds("run-worktree-command-guard.sh")
#: hook を起動する helper の壁時計の打ち切り（止まったときの保険）。壁時計は負荷で運用 timeout に届くので、
#: 運用 timeout そのものは打ち切りに使わない（`_timing_budget.hang_guard_seconds`）。
GUARD_HANG_GUARD_SEC = hang_guard_seconds("run-worktree-command-guard.sh")


def init_git_repo(path: Path) -> None:
    """git init から main への初回 commit までのテスト用リポジトリ初期化。"""
    init_repo(path, branch="main")


def run_root_branch_guard(
    cwd: Path, command: str, *, timeout: float | None = None
) -> subprocess.CompletedProcess[str]:
    """plugin 同梱の validate-worktree-command.py を PreToolUse payload で実行する。

    `timeout` は既定でモジュール定数 `GUARD_HANG_GUARD_SEC`（`hooks.json`
    由来の運用 timeout の 6 倍）。ハングへ退行した場合に `subprocess.run` が永久に
    返らず回帰スイート全体を止めるのを防ぐ（`TimeoutExpired` は捕捉しない。
    ハング退行はテストの Error として現れることが検出経路そのもの）。
    mutation 実測時（AC-4/AC-8）のみ override する。
    """
    if timeout is None:
        timeout = GUARD_HANG_GUARD_SEC
    payload = {
        "tool_name": "Bash",
        "tool_input": {"command": command, "cwd": str(cwd)},
    }
    env = {"CLAUDE_PLUGIN_ROOT": str(ROOT)}
    return subprocess.run(
        ["python3", str(ROOT / "hooks" / "scripts" / "validate-worktree-command.py")],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env=env,
        check=False,
        timeout=timeout,
    )


def run_root_branch_guard_raw(
    stdin: bytes,
    *,
    extra_env: dict[str, str] | None = None,
    removed_cwd: Path | None = None,
    process_cwd: Path | None = None,
) -> subprocess.CompletedProcess[bytes]:
    """壊れた payload や解けない cwd を試すため、stdin の bytes をそのまま渡して実行する。

    `removed_cwd` を渡すと、そのディレクトリに入ってから消し、hook 自身の cwd が無い状態で起動する。
    `process_cwd` を渡すと、hook 自身の cwd をそこにして起動する（payload の cwd と食い違う場面を作る）。
    """
    hook = str(ROOT / "hooks" / "scripts" / "validate-worktree-command.py")
    argv = ["python3", hook]
    if removed_cwd is not None:
        # 本番は PATH から解いた python3 を exec する。PATH を渡さない env で bare の python3 を起動すると、
        # Linux の CPython は実行ファイルの場所を cwd から求めて起動に失敗するので、絶対パスで起動する。
        argv = ["sh", "-c", 'cd "$1" && rmdir "$1" && exec "$3" "$2"', "_", str(removed_cwd), hook, sys.executable]
    return subprocess.run(
        argv,
        input=stdin,
        capture_output=True,
        cwd=process_cwd,
        env={"CLAUDE_PLUGIN_ROOT": str(ROOT), **(extra_env or {})},
        check=False,
        timeout=GUARD_HANG_GUARD_SEC,
    )


class RootBranchGuardFixtureMixin:
    """`unittest.TestCase` と併用する fixture mixin。

    `unittest.TestCase` を継承しないため pytest / unittest のどちらからも
    テストクラスとして collect されない（分割で collect 対象が増えないことが
    「分割前後でテスト件数を変えない」不変条件の前提）。
    """

    def _init_repo(self, path: Path) -> None:
        init_git_repo(path)

    def _head(self, path: Path) -> str:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=path,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()

    def _write_active_state(self, path: Path) -> None:
        state_dir = path / ".claude"
        state_dir.mkdir()
        (state_dir / "gdd-dev.local.md").write_text(
            "---\nactive: true\nsession_id: test-session\n---\n",
            encoding="utf-8",
        )

    def _run_guard(self, cwd: Path, command: str) -> subprocess.CompletedProcess[str]:
        return run_root_branch_guard(cwd, command)

    def _repo_ignorecase(self, path: Path) -> bool:
        """`git init` がこのファイルシステム向けに自動設定した `core.ignorecase` を読む。

        macOS の既定 APFS（大文字小文字を区別しない設定が既定）や Windows の既定
        NTFS では `git init` 時にこの値が `true` になる。case-folding に依存する
        bypass の回帰テストは、この値で実行環境の対応可否を判定して skip する
        （case-sensitive な CI（Linux ext4 等）では再現しないため）。
        """
        result = subprocess.run(
            ["git", "config", "--get", "core.ignorecase"],
            cwd=path,
            capture_output=True,
            text=True,
            check=False,
        )
        return result.returncode == 0 and result.stdout.strip() == "true"
