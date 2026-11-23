"""review-followup nudge hook の契約テストが共有する fixture（一時 repo・hook 起動・`gh` の stub）。

`test_review_followup_nudge_hook.py` が 1,500 行を超えたので、テストを関心ごとのファイルに
分けた。各ファイルは `ReviewFollowupNudgeFixtureMixin` を `unittest.TestCase` と一緒に継承する。
mixin は TestCase ではないので、どのファイルから import しても test は二重に収集されない。

`gh` はネットワーク呼び出しになるため、テストでは `GDD_REVIEW_FOLLOWUP_GH_BIN` で
stub スクリプト（`_write_stub_gh`）に差し替える。stub は呼び出しごとに counter file へ
1 行追記するので、cache 命中時に再呼び出しされないことも検証できる。
"""
from __future__ import annotations

import hashlib
import json
import os
import stat
import subprocess
import unittest
from pathlib import Path

from _paths import PLUGIN_ROOT
from _git_fixture import init_repo
from _timing_budget import hang_guard_seconds


def _hash8(value: str) -> str:
    """hook 側の `_hash8`（shasum -a 1 | cut -c1-8）と同じアルゴリズム。"""
    return hashlib.sha1(value.encode("utf-8")).hexdigest()[:8]


HOOK = PLUGIN_ROOT / "hooks" / "scripts" / "run-review-followup-nudge-hook.sh"
HOOKS_JSON = PLUGIN_ROOT / "hooks" / "hooks.json"
# hook を起動するテストの壁時計の打ち切り（止まったときの保険）
HANG_GUARD = hang_guard_seconds("run-review-followup-nudge-hook.sh")


def _write_stub_gh(
    path: Path,
    *,
    behavior: str,
    counter_file: Path | None = None,
    sleep_seconds: float = 0,
    args_file: Path | None = None,
) -> None:
    """behavior: 'has-pr' | 'has-pr-merged' | 'no-pr' | 'error' | 'hang' |
    'exit0-unexpected-state'"""
    lines = ["#!/usr/bin/env bash", "set -eu"]
    if counter_file is not None:
        lines.append(f'printf "call\\n" >> "{counter_file}"')
    if args_file is not None:
        # stub 自体が `gh` を置き換えるため、呼び出し形
        # `"$GH_RESOLVED" pr view --json state --jq '.state' -- "$BRANCH"`
        # （PR #88 人間レビュー round 5 指摘 High-1 是正: `$BRANCH` は常に `--`
        # の後の最後の引数になる。`$3` 固定だと flag 位置が変わるたびに壊れる
        # ため、末尾引数を取る形にしておく）。
        lines.append(f'printf "%s\\n" "${{@: -1}}" >> "{args_file}"')
    if sleep_seconds:
        lines.append(f"sleep {sleep_seconds}")
    if behavior == "has-pr":
        # 実 `gh ... --json state --jq '.state'` は state の値だけを平文で
        # 出力する（JSON 構造も引用符も付かない）。PR #88 人間レビュー指摘
        # Medium の是正で hook 側がこの形を読むようになったため、stub も
        # 同じ形にする。
        lines.append('echo "OPEN"')
        lines.append("exit 0")
    elif behavior == "has-pr-merged":
        # MERGED / CLOSED でも `gh pr view` は exit 0 する（独立レビュー指摘
        # Medium: state を見ずに exit code だけで注入すると、マージ済み/
        # クローズ済み PR にまで誤注入する）。
        lines.append('echo "MERGED"')
        lines.append("exit 0")
    elif behavior == "exit0-unexpected-state":
        # exit 0 だが state が OPEN/MERGED/CLOSED のいずれでもない（空文字列。
        # `--jq` の出力が壊れた・API 応答が想定外だった等を模す）。PR #88
        # 人間レビュー round 6 指摘 Medium: この場合を「OPEN ではない」＝
        # no-pr と断定すると、判定不能な出力を PR なしとしてキャッシュする。
        lines.append("exit 0")
    elif behavior == "no-pr":
        lines.append('echo "no pull requests found for branch \\"x\\"" >&2')
        lines.append("exit 1")
    elif behavior == "error":
        lines.append('echo "error connecting to api.github.com" >&2')
        lines.append("exit 1")
    elif behavior == "hang":
        lines.append("sleep 30")
        lines.append("exit 0")
    else:
        raise ValueError(behavior)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)


class ReviewFollowupNudgeFixtureMixin:
    @classmethod
    def setUpClass(cls) -> None:
        # 独立レビューで指摘: このクラスの大半のテストは `HOME` を上書きせず
        # 実行環境の `HOME` をそのまま継承する。`gdd_kill_switch_active`
        # （kill-switch.sh）は `${HOME}/.claude/gdd-hooks-disabled` の存在だけで
        # hook 全体を即 no-op にするため、この実行環境でそのファイルが
        # 存在すると（開発中に一時的に GDD hook を止めた等）、本クラスの
        # fail-safe 系テスト（gh を呼んでいないこと・注入されていないこと
        # を assert するもの）が「本当に対象コードが正しく除外/是正した」
        # のではなく「kill switch で hook 自体が即抜けた」だけで軒並み
        # vacuous green になりうる（`test_kill_switch_suppresses_injection`
        # 自身は明示的に別の `HOME` を使うため対象外）。この状態のまま
        # テストを走らせて誤った安心感を持たないよう、事前に検出して
        # スキップする。
        killswitch_file = Path.home() / ".claude" / "gdd-hooks-disabled"
        if killswitch_file.exists():
            raise unittest.SkipTest(
                f"kill switch file exists at {killswitch_file}; "
                "most tests in this module would pass vacuously (hook "
                "short-circuits before the code under test runs). "
                "Remove it before running this test module."
            )

    def _init_repo(self, path: Path, *, branch: str = "feature-x") -> None:
        init_repo(path, branch=branch)

    def _run_hook(
        self,
        cwd: Path,
        command: str,
        *,
        extra_env: dict[str, str] | None = None,
        timeout: float = HANG_GUARD,
    ) -> subprocess.CompletedProcess[str]:
        payload = {"tool_name": "Bash", "tool_input": {"command": command}}
        env = os.environ.copy()
        # テストを実行するシェル自身の環境に `GDD_SKIP_PRE_PUSH_GATE=1` 等が
        # 残っていると、`os.environ.copy()` 経由でそれが hook プロセスへ
        # 継承され、step 3 の opt-out 判定（または gh 呼び出し先/timeout 等）
        # がテストの意図と無関係に変わりうる（PR #88 人間レビュー round 5
        # 指摘 Medium: 除外系テストが「対象コードで正しく除外された」のか
        # 「環境の opt-out で早期に抜けただけ」なのか区別できなくなる）。
        # 各テストが `extra_env` で明示しない限り、これらの seam は毎回
        # クリーンな既定値から始める。
        for _leaky_var in (
            "GDD_SKIP_PRE_PUSH_GATE",
            "GDD_HOOK_STATE_DIR",
            "GDD_REVIEW_FOLLOWUP_GH_BIN",
            "GDD_REVIEW_FOLLOWUP_GH_TIMEOUT",
            "GDD_REVIEW_FOLLOWUP_PR_CACHE_TTL",
            "GDD_REVIEW_FOLLOWUP_PR_UNKNOWN_TTL",
        ):
            env.pop(_leaky_var, None)
        env.update({"CLAUDE_PLUGIN_ROOT": str(PLUGIN_ROOT)})
        if extra_env:
            env.update(extra_env)
        return subprocess.run(
            ["bash", str(HOOK)],
            cwd=cwd,
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            env=env,
            check=False,
            timeout=timeout,
        )
