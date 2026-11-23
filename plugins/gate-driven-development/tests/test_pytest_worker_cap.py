"""pytest.ini が xdist の worker 数に上限を掛けていることを、実際の pytest の起動で確かめる。

`-n auto` は論理 CPU 数ぶんの worker を起動する。コア数の多い Mac でコア数ぶんの worker にすると、
8 worker とほぼ同じ時間で負荷平均だけが大きく上がった（全量のテストで測った）。
複数のセッションが同時に回すとマシンが詰まるので、pytest.ini で上限を掛ける。

子の pytest は、xdist が起動する worker の一覧（`config.option.tx`）が決まった後、worker を
起動する前に、その数を出して終わる。worker を実際に起動すると、子 1 回で interpreter を
8 本起動することになり、混んだマシンでは timeout で落ちていた（2026-10-14 に、全量の
並列実行の中で長くかかり、120 秒の timeout に当たった）。
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

from _paths import PLUGIN_ROOT

WORKER_CAP = 8

# xdist は pytest_cmdline_main（tryfirst）で worker の一覧を決め、pytest_sessionstart（trylast）で
# 起動する。その間で数を出して止める
CHILD_CONFTEST = """
import pytest


@pytest.hookimpl(tryfirst=True)
def pytest_sessionstart(session):
    pytest.exit(f"planned workers: {len(session.config.option.tx or [])}", returncode=0)
"""


def _planned_workers(tmp_path: Path, *args: str) -> int:
    (tmp_path / "conftest.py").write_text(CHILD_CONFTEST)
    (tmp_path / "test_child.py").write_text("def test_child():\n    pass\n")
    env = {k: v for k, v in os.environ.items() if not k.startswith(("PYTEST_", "PYTHONPATH"))}
    # xdist の既定の auto は、この環境変数を CPU 数より先に読む。32 コアの機械を模す
    env["PYTEST_XDIST_AUTO_NUM_WORKERS"] = "32"
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-c", str(PLUGIN_ROOT / "pytest.ini"),
         "--rootdir", str(tmp_path), "-q", "-p", "no:cacheprovider", *args,
         str(tmp_path / "test_child.py")],
        cwd=tmp_path, env=env, capture_output=True, text=True, timeout=120, check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    match = re.search(r"planned workers: (\d+)", result.stdout + result.stderr)
    assert match, result.stdout + result.stderr
    return int(match.group(1))


def test_ini_default_caps_auto_workers(tmp_path: Path) -> None:
    assert _planned_workers(tmp_path) == WORKER_CAP


def test_explicit_n_auto_is_capped_too(tmp_path: Path) -> None:
    # CI（plugin-lint.yml）と CLAUDE.md の手順は -n auto をコマンドラインで渡す
    assert _planned_workers(tmp_path, "-n", "auto") == WORKER_CAP


def test_explicit_worker_count_below_the_cap_is_kept(tmp_path: Path) -> None:
    # 数を出す仕組みが worker の一覧を実際に読んでいることの確かめ（定数を返す形を落とす）
    assert _planned_workers(tmp_path, "-n", "3") == 3
